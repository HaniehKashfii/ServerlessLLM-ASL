"""Core abstractions for the Ray-powered serverless LLM system.

This module provides a minimal set of primitives that are shared across the
Ray actors that compose the serverless inference platform.  The goal is to make
it easy to build actors with consistent placement, logging and error handling
behaviour while keeping the rest of the codebase agnostic to the execution
back-end.
"""

from __future__ import annotations

import dataclasses
import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, Mapping, MutableMapping, Optional, Sequence, Type, TypeVar

try:
    import ray
    from ray.util.placement_group import PlacementGroup, placement_group, remove_placement_group
except ImportError:  # pragma: no cover - exercised in tests via monkeypatch
    ray = None  # type: ignore[assignment]
    PlacementGroup = Any  # type: ignore[assignment]


__all__ = [
    "ActorOptions",
    "ActorInitializationError",
    "BaseActor",
    "GPUId",
    "ModelId",
    "ModelNotLoaded",
    "PlacementFailure",
    "PlacementGroupSpec",
    "RayDependencyError",
    "TenantId",
    "create_placement_group",
    "remove_placement_group_safe",
]


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------
ModelId = str
TenantId = str
GPUId = str
PlacementStrategy = str
ResourceBundle = Mapping[str, float]


# ---------------------------------------------------------------------------
# Exception hierarchy
# ---------------------------------------------------------------------------
class CoreError(RuntimeError):
    """Base error type for core abstractions."""


class RayDependencyError(CoreError):
    """Raised when a Ray specific action is attempted without Ray installed."""


class PlacementFailure(CoreError):
    """Raised when a placement group cannot be created or is not ready."""


class ActorInitializationError(CoreError):
    """Raised when an actor fails during initialisation."""


class ModelNotLoaded(CoreError):
    """Raised when an inference request targets an unloaded model."""


# ---------------------------------------------------------------------------
# Placement group helpers
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class PlacementGroupSpec:
    """Configuration describing how an actor should be placed."""

    bundles: Sequence[ResourceBundle]
    strategy: PlacementStrategy = "PACK"
    timeout_s: float = 30.0

    def to_kwargs(self) -> Dict[str, Any]:
        """Convert the specification into keyword arguments for Ray."""

        return {"bundles": list(self.bundles), "strategy": self.strategy}


def _require_ray() -> Any:
    """Return the :mod:`ray` module or raise a helpful error."""

    if ray is None:  # pragma: no cover - guard validated via unit test
        raise RayDependencyError(
            "Ray is not installed. Install ray>=2.10.0 to use the core actors."
        )
    return ray


def create_placement_group(spec: PlacementGroupSpec) -> PlacementGroup:
    """Create and wait for a Ray placement group.

    Args:
        spec: Description of the placement group to create.

    Returns:
        The created placement group once it is ready.

    Raises:
        PlacementFailure: if the placement group cannot be created in time.
    """

    _ray = _require_ray()
    pg = placement_group(**spec.to_kwargs())
    ready, _ = _ray.wait([pg.ready()], timeout=spec.timeout_s)
    if not ready:
        remove_placement_group(pg)
        raise PlacementFailure(
            f"Placement group timed out after {spec.timeout_s} seconds"
        )
    logger.debug("Created placement group %s using spec %s", pg, spec)
    return pg


def remove_placement_group_safe(pg: Optional[PlacementGroup]) -> None:
    """Remove a placement group, swallowing errors if it is already gone."""

    if pg is None:
        return

    try:
        remove_placement_group(pg)
        logger.debug("Removed placement group %s", pg)
    except Exception:  # pragma: no cover - defensive logging
        logger.warning("Failed to remove placement group %s", pg, exc_info=True)


# ---------------------------------------------------------------------------
# Actor utilities
# ---------------------------------------------------------------------------
ActorType = TypeVar("ActorType", bound="BaseActor")


@dataclass
class ActorOptions:
    """Options used to configure a Ray actor."""

    num_cpus: float = 0.0
    num_gpus: float = 0.0
    resources: Optional[MutableMapping[str, float]] = None
    max_concurrency: Optional[int] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    lifetime: Optional[str] = None
    placement_group: Optional[PlacementGroup] = None

    def to_kwargs(self) -> Dict[str, Any]:
        """Convert the options into Ray ``.options`` keyword arguments."""

        kwargs: Dict[str, Any] = {
            "num_cpus": self.num_cpus,
            "num_gpus": self.num_gpus,
        }
        if self.resources:
            kwargs["resources"] = dict(self.resources)
        if self.max_concurrency is not None:
            kwargs["max_concurrency"] = self.max_concurrency
        if self.name is not None:
            kwargs["name"] = self.name
        if self.namespace is not None:
            kwargs["namespace"] = self.namespace
        if self.lifetime is not None:
            kwargs["lifetime"] = self.lifetime
        if self.placement_group is not None:
            kwargs["placement_group"] = self.placement_group
        return kwargs


class BaseActor:
    """Base class that wraps ``ray.remote`` with sensible defaults."""

    default_options = ActorOptions(num_cpus=0.5)
    placement_group_spec: Optional[PlacementGroupSpec] = None

    @classmethod
    def options(cls, **overrides: Any) -> ActorOptions:
        """Return actor options combining defaults with overrides."""

        options_dict = dataclasses.asdict(cls.default_options)
        options_dict.update(overrides)
        options = ActorOptions(**options_dict)
        if options.placement_group is None and cls.placement_group_spec is not None:
            options.placement_group = create_placement_group(cls.placement_group_spec)
        return options

    @classmethod
    def as_remote(cls: Type[ActorType], **overrides: Any) -> Any:
        """Return a ``ray.remote`` wrapped class using the provided options."""

        _ray = _require_ray()
        options = cls.options(**overrides)
        remote_cls = _ray.remote(**options.to_kwargs())(cls)
        return remote_cls

    async def ping(self) -> float:
        """Simple liveness probe returning the current timestamp."""

        return time.time()

    async def warmup(self) -> None:
        """Hook executed after actor construction to allocate resources."""

        return None

