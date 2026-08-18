"""RunPod serverless handler — yüz takası işçisi.

Girdi (job.input):
  selfie_url        kullanıcı yüzü (URL)
  template_url      şablon videosu (URL, CFR 24fps beklenir)
  reference_frame   şablonda kahramanın net frontal karesi (24fps bazlı)
  output_put_url    sonucun PUT edileceği imzalı URL
  swapper_model / swapper_weight / fps  (ops.) — varsayılanlar üretim ayarı

Dönüş: {ok, seconds, bytes} veya {ok: False, error}
Not: bu işçi HİÇBİR şeyi dışarıdan indirmez (modeller imajda) — tek ağ
trafiği girdi indirme + çıktı yükleme.
"""
import os
import subprocess
import time
import urllib.request

import runpod


def _retry(fn, tries=3, wait=3):
    """Geçici ağ hatalarında iş ÖLMEZ — 3 deneme, aralarında bekleme."""
    last = None
    for i in range(tries):
        try:
            return fn()
        except Exception as e:  # noqa: BLE001 — ağ katmanı, her tür hata denenir
            last = e
            if i < tries - 1:
                time.sleep(wait * (i + 1))
    raise last


def _dl(url, path):
    _retry(lambda: urllib.request.urlretrieve(url, path))


def handler(job):
    i = job["input"]
    t0 = time.time()
    src, tpl, out = "/tmp/src.png", "/tmp/tpl.mp4", "/tmp/out.mp4"
    for p in (src, tpl, out):
        if os.path.exists(p):
            os.remove(p)
    _dl(i["selfie_url"], src)
    _dl(i["template_url"], tpl)

    cmd = [
        "python3", "facefusion.py", "headless-run",
        "-s", src, "-t", tpl, "-o", out,
        "--processors", "face_swapper", "expression_restorer",
        "--face-swapper-model", i.get("swapper_model", "hyperswap_1c_256"),
        "--face-swapper-weight", str(i.get("swapper_weight", 0.5)),
        "--face-swapper-pixel-boost", "512x512",
        "--face-selector-mode", "reference",
        "--reference-frame-number", str(i.get("reference_frame", 1)),
        "--execution-providers", "cuda",
        "--output-video-fps", str(i.get("fps", 24)),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd="/facefusion")

    if not os.path.exists(out):
        tail = ((proc.stdout or "")[-800:]) + ((proc.stderr or "")[-800:])
        return {"ok": False, "error": tail}

    with open(out, "rb") as f:
        data = f.read()

    def _put():
        req = urllib.request.Request(
            i["output_put_url"], data=data, method="PUT",
            headers={"Content-Type": "video/mp4"},
        )
        urllib.request.urlopen(req, timeout=300)

    _retry(_put)
    return {"ok": True, "seconds": round(time.time() - t0, 1), "bytes": len(data)}


runpod.serverless.start({"handler": handler})
