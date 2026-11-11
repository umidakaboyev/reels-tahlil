#!/usr/bin/env python3
"""Videoni Claude o'qiy oladigan kadrlarga aylantiradi.

Ishlatish:
  python kor.py <video.mp4> [--fps N]

Video uzunligiga qarab kadr oladi (30 s gacha soniyasiga 2 ta, 90 s gacha 1 ta, undan uzun
bo'lsa siyrakroq), ularni har birida 10 ta kadr bo'lgan varaqlarga joylaydi va har bir kadr
ustiga vaqtini yozadi. Montaj kesimlarini ffmpeg orqali sanaydi.

Natija: <video papkasi>/kadrlar/, <video papkasi>/varaqlar/ va JSON (varaqlar, kadr vaqtlari,
kesimlar).
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _umumiy import ffmpeg_tayyorla  # noqa: E402

ffmpeg_tayyorla()

from PIL import Image, ImageDraw, ImageFont  # noqa: E402

USTUN, QATOR = 5, 2
KATAK_EN = 360


def davomiylik(video):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(video)], capture_output=True, text=True, check=True)
    return float(r.stdout.strip() or 0)


def fps_tanla(s):
    if s <= 30:
        return 2.0
    if s <= 90:
        return 1.0
    return max(0.25, round(90 / s, 2))


def kesimlar(video, chegara):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(video), "-vf",
                        f"select='gt(scene,{chegara})',showinfo", "-an", "-f", "null", "-"],
                       capture_output=True, text=True)
    return [round(float(t), 2) for t in re.findall(r"pts_time:([\d.]+)", r.stderr)]


def vaqt(t):
    return f"{int(t // 60)}:{t % 60:04.1f}"


def shrift(o):
    for f in ("/System/Library/Fonts/Supplemental/Arial Bold.ttf", "C:/Windows/Fonts/arialbd.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(f, o)
        except OSError:
            continue
    return ImageFont.load_default()


def varaq_yasash(kadrlar, vaqtlar, yol):
    birinchi = Image.open(kadrlar[0])
    bal = round(KATAK_EN * birinchi.height / birinchi.width)
    var = Image.new("RGB", (USTUN * KATAK_EN + (USTUN + 1) * 6, QATOR * bal + (QATOR + 1) * 6), "white")
    f = shrift(26)
    for i, (k, t) in enumerate(zip(kadrlar, vaqtlar)):
        im = Image.open(k).convert("RGB").resize((KATAK_EN, bal))
        d = ImageDraw.Draw(im)
        yozuv = vaqt(t)
        x0, y0, x1, y1 = d.textbbox((0, 0), yozuv, font=f)
        d.rectangle((0, 0, x1 - x0 + 16, y1 - y0 + 14), fill=(220, 20, 60))
        d.text((8 - x0, 6 - y0), yozuv, font=f, fill="white")
        var.paste(im, (6 + (i % USTUN) * (KATAK_EN + 6), 6 + (i // USTUN) * (bal + 6)))
    var.save(yol, quality=88)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--fps", type=float)
    a = ap.parse_args()
    video = Path(a.video).expanduser().resolve()
    asos = video.parent
    kdir, vdir = asos / "kadrlar", asos / "varaqlar"
    for d in (kdir, vdir):
        d.mkdir(exist_ok=True)
        for f in d.glob("*.jpg"):
            f.unlink()

    s = davomiylik(video)
    fps = a.fps or fps_tanla(s)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(video), "-vf",
                    f"fps={fps},scale=1080:-2", "-q:v", "3", str(kdir / "kadr_%04d.jpg")], check=True)
    kadrlar = sorted(kdir.glob("kadr_*.jpg"))
    # fps filtri har bir kadrni o'z oralig'ining o'rtasidan oladi
    vaqtlar = [round((i + 0.5) / fps, 2) for i in range(len(kadrlar))]

    varaqlar = []
    bir = USTUN * QATOR
    for n in range(0, len(kadrlar), bir):
        yol = vdir / f"varaq_{n // bir + 1:02d}.jpg"
        varaq_yasash(kadrlar[n:n + bir], vaqtlar[n:n + bir], yol)
        varaqlar.append(str(yol))

    kes = kesimlar(video, 0.3)
    if len(kes) < 2:  # bir joyda turgan kamera: jump-cut'lar kichik farq beradi
        kes = kesimlar(video, 0.05)

    print(json.dumps({
        "davomiylik_s": round(s, 2), "fps": fps,
        "varaqlar": varaqlar,
        "varaq_tartibi": "har varaqda 10 kadr, chapdan o'ngga, yuqoridan pastga; vaqti har kadrning chap-yuqori burchagida",
        "kadrlar": [{"kadr": k.name, "t": t} for k, t in zip(kadrlar, vaqtlar)],
        "kesimlar": kes,
        "kesim_oraligi_s": round(s / (len(kes) + 1), 2),
    }, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
