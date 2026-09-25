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

# Sürüm SABİT: 3.8.2 = 20 Ağu 2026 derlemesinde çalışan sürüm (o günkü HEAD
# 4b1dedb). Sabitsiz clone her push'ta yeni FaceFusion'ı çeker; CLI değişirse
# canlı hat kırılır. Yükseltme bilinçli yapılmalı (tool/gpu_swap.py ile test).
RUN git clone --depth 1 --branch 3.8.2 https://github.com/facefusion/facefusion.git /facefusion

# cudnn-runtime taban imajı cuDNN 9 + cuBLAS'ı zaten içeriyor → pip nvidia
# paketleri GEREKSİZ (~1.2GB tasarruf, cold start'ta daha hızlı imaj çekimi)
RUN pip install --no-cache-dir -r /facefusion/requirements.txt \
 && pip uninstall -y onnxruntime \
 && pip install --no-cache-dir onnxruntime-gpu==1.22.0 runpod

# Doğrulanmış model paketi (fal storage'daki hash'i tutan set) imaja gömülür
ARG MODELS_URL
RUN curl -sL "$MODELS_URL" -o /tmp/models.tar \
 && tar -xf /tmp/models.tar -C /facefusion/ \
 && rm /tmp/models.tar

# Yüz iyileştirici (ops., handler 'enhancer' girdisiyle açılır) — model imaja
# gömülür, çalışma anında indirme yok. FaceFusion'ın kendi varlık adresi.
RUN mkdir -p /facefusion/.assets/models \
 && for f in gfpgan_1.4.hash gfpgan_1.4.onnx; do \
      curl -fsSL "https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/$f" \
        -o "/facefusion/.assets/models/$f"; \
    done

COPY handler.py /handler.py
CMD ["python3", "-u", "/handler.py"]
