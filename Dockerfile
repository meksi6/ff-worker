# FaceFusion serverless işçisi — RunPod GPU (kanıtlanmış reçete 2026-08-18):
# ubuntu24.04 = python3.12 + ffmpeg 6.1 · ORT 1.22 = CUDA 12 eşleşmesi ·
# modeller imaja gömülü (çalışma anında hiçbir indirme yok → cold start hızlı).
FROM nvidia/cuda:12.6.3-cudnn-runtime-ubuntu24.04

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
      python3 python3-venv git ffmpeg curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /venv
ENV PATH=/venv/bin:$PATH

RUN git clone --depth 1 https://github.com/facefusion/facefusion.git /facefusion

RUN pip install --no-cache-dir -r /facefusion/requirements.txt \
 && pip uninstall -y onnxruntime \
 && pip install --no-cache-dir onnxruntime-gpu==1.22.0 nvidia-cublas-cu12 nvidia-cudnn-cu12 runpod

# Doğrulanmış model paketi (fal storage'daki hash'i tutan set) imaja gömülür
ARG MODELS_URL
RUN curl -sL "$MODELS_URL" -o /tmp/models.tar \
 && tar -xf /tmp/models.tar -C /facefusion/ \
 && rm /tmp/models.tar

ENV LD_LIBRARY_PATH=/venv/lib/python3.12/site-packages/nvidia/cublas/lib:/venv/lib/python3.12/site-packages/nvidia/cudnn/lib

COPY handler.py /handler.py
CMD ["python3", "-u", "/handler.py"]
