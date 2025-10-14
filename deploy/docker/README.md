# Docker Images

Two lightweight Dockerfiles are provided for the Ray head and worker nodes. They
extend the upstream `rayproject/ray-ml` images so that the project dependencies
are installed consistently during development.

Build the images locally with:

```bash
docker build -f deploy/docker/ray-head.Dockerfile -t serverless-llm/ray-head .
docker build -f deploy/docker/ray-worker.Dockerfile -t serverless-llm/ray-worker .
```

The resulting images can be used directly with `docker compose` or referenced by
the Kubernetes manifests.
