# Ray Deployment Configurations

This directory contains example Ray cluster configuration files used during the
first phase of the project.  The goal is to support a quick local development
loop while keeping the configuration extensible to a multi-node GPU cluster.

- `single-node.yaml` targets a single machine and is ideal for running the MVP
  locally.  It keeps the layout close to how the production cluster will behave
  so that actors defined in `core/` can be validated early.
- `cluster.yaml` provides an opinionated AWS based configuration that can scale
  Ray workers elastically.  It uses the Ray provided Docker images to minimise
  setup time and ensures GPU availability for inference actors.

Both configurations assume that project dependencies are installed via
`pip install -r requirements.txt` before actors start.
