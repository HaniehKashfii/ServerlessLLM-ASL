"""Unit tests for the Ray core abstractions used by the MVP."""

import pytest

import core.base as base


class ExampleActor(base.BaseActor):
    """Simple actor used to verify option merging."""

    default_options = base.ActorOptions(num_cpus=1, num_gpus=0.25)


class ExampleActorWithPlacement(base.BaseActor):
    """Actor that declares a placement group requirement."""

    default_options = base.ActorOptions(num_cpus=1, num_gpus=1)
    placement_group_spec = base.PlacementGroupSpec(bundles=({"GPU": 1},))


def test_actor_options_merges_defaults():
    """Overriding options should keep defaults for unspecified values."""

    opts = ExampleActor.options(num_cpus=2)
    assert opts.num_cpus == 2
    assert opts.num_gpus == 0.25
    assert opts.resources is None


def test_actor_options_creates_placement_group(monkeypatch):
    """Actors with a placement spec should ask Ray for a placement group."""

    sentinel = object()
    monkeypatch.setattr(base, "create_placement_group", lambda spec: sentinel)

    opts = ExampleActorWithPlacement.options()
    assert opts.placement_group is sentinel


def test_missing_ray_dependency_error(monkeypatch):
    """Calling ``as_remote`` without Ray should raise a helpful error."""

    monkeypatch.setattr(base, "ray", None, raising=False)

    class DummyActor(base.BaseActor):
        """Actor used purely for dependency resolution tests."""

        pass

    with pytest.raises(base.RayDependencyError):
        DummyActor.as_remote()
