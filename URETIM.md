# Üretim sürümü — kalite kilidi

Canlı RunPod endpoint'i `ff-worker` (`sbg0jwe2hxnw1r`, şablon `cgae0g7s0a`)
imajı **digest ile** çalıştırır — etiketle değil:

```
ghcr.io/meksi6/ff-worker@sha256:02fd4e4fe3ec974036eef223e73ffa8c694ee8afaa511a6e3cb20a6ecb5d6621
```

`:latest` yalnız "son derleme" demektir, canlıya **çıkmaz**. Bu depoya push =
yeni *aday* imaj (`:sha-<commit>` etiketiyle); üretim değişmez.

## Kilitli bileşenler

| Bileşen | Sürüm |
|---|---|
| FaceFusion | 3.8.2 (commit `4b1dedb`) |
| onnxruntime-gpu | 1.22.0 |
| numpy · onnx · opencv-headless · scipy | 2.4.6 · 1.22.0 · 5.0.0.93 · 1.18.0 (FaceFusion 3.8.2 requirements) |
| runpod | 1.12.0 |
| ffmpeg · x264 | 6.1.1-3ubuntu5 · 0.164.3108 (Ubuntu 24.04) |
| Taban | `nvidia/cuda:12.6.3-cudnn-runtime-ubuntu24.04` (cuDNN 9.5.1) |
| Modeller | imaja gömülü (`MODELS_URL` tar) + `gfpgan_1.4` (ops., varsayılan kapalı) |

Doğrulama (2026-09-26): bu imaj (25 Eyl) ile 20 Ağu imajı (`57b985a3…`)
katman katman karşılaştırıldı — FaceFusion kodu 243 dosyada birebir aynı;
yapay zekâ kütüphaneleri, ffmpeg/x264, CUDA tabanı aynı. Fark yalnız yan
paketlerde (boto3, huggingface_hub vb.) ve ops. gfpgan modelinde.

## Altın ayarlar

Varsayılan komut (`handler.py`): `face_swapper` + `expression_restorer` ·
`hyperswap_1c_256` · ağırlık 0.5 · pixel boost 512x512 · kutu maske ·
reference modu, mesafe 0.6 · 24 fps · **yüz iyileştirici KAPALI**.

Şablon bazlı değerler (referans kare, ağırlık, mesafe, maske) sultansnap
deposunda `backend/animate-v2.js` → `SWAP_TEMPLATES` içinde, git'te sabit.

## Referans testi

`sultansnap/tool/golden_test.py` — sentetik yüz A + canlı Güverte Dövüşü
şablonu (kare 232, 1.0 / 0.9 / kutu) → çıktıyı `tool/golden/` referans
kareleriyle **yüz bölgesinde** PSNR ile karşılaştırır.

| Kalibrasyon (2026-09-26) | Yüz PSNR |
|---|---|
| Canlı hat, tekrar çalıştırma | 38.1 – 39.3 dB |
| Takassız şablon (yanlış sonuç) | 25.1 – 31.5 dB |

Eşik: ≥ 35 aynı kalite · 33–35 gözle kontrol · < 33 farklı.

## Yükseltme prosedürü

1. Değişikliği push et → CI `:sha-<commit>` aday imajını üretir.
2. Adayı canlıya dokunmadan dene: geçici ikinci endpoint (aynı ayarlar,
   aday digest) → `FF_ENDPOINT=<id> python3 tool/golden_test.py`.
   Ayrıca 2–3 şablonda gözle karşılaştırma.
3. Founder onayı.
4. RunPod şablonu `cgae0g7s0a` → Container Image = yeni digest. Bu dosyadaki
   digest'i güncelle. Geçici endpoint'i sil.

Geri dönüş: şablonu önceki digest'e çevir. ghcr'daki eski (etiketsiz)
sürümleri **silme** — geri dönüş noktalarıdır.

## Bilinen riskler

- `MODELS_URL` bir fal.media dosyası; silinirse yeni derleme **başarısız**
  olur (canlı etkilenmez — digest'teki imaj modelleri içerir). Kalıcı bir
  depoya taşınmalı.
- Depo herkese açık; sır içermez. İmaj da açık (RunPod şifresiz çekiyor).
