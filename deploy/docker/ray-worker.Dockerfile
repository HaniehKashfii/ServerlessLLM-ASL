FROM rayproject/ray-ml:2.10.0-py310

WORKDIR /opt/serverless-llm
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

ENTRYPOINT ["ray", "start", "--address=ray-head:6379", "--num-cpus=8", "--num-gpus=1"]
