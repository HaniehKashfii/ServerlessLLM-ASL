# ============================================
# ServerlessLLM image (GPU) — PyPI install
# Base: CUDA 12.1 + Ubuntu 22.04 (Python 3.10)
# ============================================
FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

LABEL maintainer="Hanieh Kashfi <kashfi.hanieh.ca@gmail.com>"
LABEL org.opencontainers.image.source="https://github.com/haniehkashfi/ServerlessLLM-ASL"
LABEL description="ServerlessLLM + Store, ready for Runpod (CUDA), installed from PyPI."

# Non-interactive apt + sane defaults
ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=America/Los_Angeles \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH="/root/.local/bin:${PATH}" \
    CUDA_VISIBLE_DEVICES=0 \
    SLLM_STORE_PATH=/app/models \
    RAY_DISABLE_DASHBOARD=1

# --- System deps & Python 3.10 (default on 22.04) ---
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
        tzdata ca-certificates curl git \
        build-essential pkg-config \
        python3 python3-dev python3-venv python3-distutils python3-pip && \
    update-ca-certificates && \
    ln -sf /usr/bin/python3 /usr/bin/python && \
    python3 --version && python3 -m pip --version && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# --- Install ServerlessLLM from PyPI (no source build) ---
RUN python3 -m pip install --upgrade pip setuptools wheel && \
    python3 -m pip install \
        serverless-llm \
        "serverless-llm[worker]" \
        serverless-llm-store && \
    pip cache purge

# --- App workspace & model dir ---
WORKDIR /app
RUN mkdir -p /app/models

# --- Expose ports ---
# 8343 = ServerlessLLM (OpenAI-compatible API)
# 8073 = sllm-store gRPC
# 6379 = Ray head (optional to expose)
EXPOSE 8343 8073 6379

# --- Default startup ---
# Starts:
# 1) sllm-store (model checkpoint store)
# 2) Ray head
# 3) ServerlessLLM service
CMD ["/bin/bash", "-lc", "\
  set -euo pipefail; \
  echo 'Starting sllm-store...'; \
  sllm-store start --host 0.0.0.0 --port 8073 & \
  sleep 3; \
  echo 'Starting Ray head...'; \
  ray start --head --port=6379 --num-cpus=4 --num-gpus=1 --resources='{\"control_node\": 1, \"worker_node\": 1, \"worker_id_0\": 1}' --block & \
  sleep 5; \
  echo 'Starting ServerlessLLM service...'; \
  sllm start --host 0.0.0.0 --port 8343; \
"]
