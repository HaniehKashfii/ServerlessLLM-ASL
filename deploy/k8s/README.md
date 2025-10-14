# Kubernetes Manifests

These manifests describe a minimal Ray cluster composed of a single head pod and
multiple worker pods.  They are intentionally small so that they can run on a
local KinD or K3s cluster for development purposes while still being production
ready with GPU requests when deployed to larger clusters.

Apply the manifests in order once the namespace has been created:

```bash
kubectl apply -f deploy/k8s/ray-head.yaml
kubectl apply -f deploy/k8s/ray-worker.yaml
```

The head pod exposes both the Ray client port and dashboard service.  Worker
pods join automatically and reserve shared memory for vLLM workloads via the
`emptyDir` backed `/dev/shm` mount.
