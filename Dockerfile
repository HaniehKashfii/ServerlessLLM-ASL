# -------------------------------
# Base image with CUDA + Ubuntu 20.04
# -------------------------------
FROM nvidia/cuda:12.1.0-base-ubuntu20.04

# Metadata
LABEL maintainer="haniehkashfi <haniehkashfi@gmail.com>"
LABEL description="ServerlessLLM build compatible with RunPod GPUs"

# -------------------------------
# Environment setup
# -------------------------------
ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=America/Los_Angeles \
    PYTHONUNBUFFERED=1 \
    PATH="/root/.local/bin:${PATH}"

# -------------------------------
# System dependencies
# -------------------------------
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
        tzdata ca-certificates curl git sudo build-essential \
        python3 python3-dev python3-venv python3-distutils python3-pip && \
    ln -sf /usr/bin/python3 /usr/bin/python && \
    python3 --version && python3 -m pip --version && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# -------------------------------
# Install ServerlessLLM and its store
# -------------------------------
WORKDIR /app
COPY . /app

# Install Python dependencies (pip >= 23)
RUN pip install --upgrade pip setuptools wheel && \
    pip install -e ./sllm_store && \
    pip install -e . && \
    pip install ".[worker]" && \
    pip cache purge

# -------------------------------
# Runtime environment variables
# -------------------------------
ENV CUDA_VISIBLE_DEVICES=0
ENV SLLM_STORE_PATH=/app/models
ENV RAY_DISABLE_DASHBOARD=1

# -------------------------------
# Expose relevant ports
# -------------------------------
EXPOSE 8343 8073 6379 8265

# -------------------------------
# Default command
# -------------------------------
CMD ["bash", "-c", "\
sllm-store start --host 0.0.0.0 --port 8073 & \
ray start --head --port=6379 --num-cpus=4 --num-gpus=1 --resources='{\"control_node\": 1, \"worker_node\": 1, \"worker_id_0\": 1}' --block & \
sleep 5 && \
sllm start --host 0.0.0.0 --port 8343 \
"]
