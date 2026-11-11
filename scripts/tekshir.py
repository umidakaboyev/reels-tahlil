#!/usr/bin/env python3
"""O'rnatish to'g'ri bo'lganini tekshiradi. Har bir qator 'ok', 'ixtiyoriy' yoki 'XATO' bo'ladi."""
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _umumiy import env  # noqa: E402

xato = False


def q(nom, holat, izoh=""):
    global xato
    if holat == "XATO":
        xato = True
    print(f"{holat:<10} {nom}{'  — ' + izoh if izoh else ''}")


v = sys.version_info
q("Python 3.10+", "ok" if v >= (3, 10) else "XATO", f"{v.major}.{v.minor}")

try:
    from _umumiy import ffmpeg_tayyorla
    ffmpeg_tayyorla()
    q("ffmpeg", "ok" if shutil.which("ffmpeg") else "XATO")
except SystemExit as e:
    q("ffmpeg", "XATO", str(e))

for modul, nom in (("yt_dlp", "yt-dlp (yuklab olish)"), ("PIL", "Pillow (kadr varaqlari)"),
                   ("faster_whisper", "faster-whisper (transkript)"), ("requests", "requests")):
    try:
        __import__(modul)
        q(nom, "ok")
    except ImportError:
        q(nom, "XATO", "INSTALL.md, 3-qadam")

if env("ELEVENLABS_API_KEY"):
    try:
        import requests
        r = requests.get("https://api.elevenlabs.io/v1/user", headers={"xi-api-key": env("ELEVENLABS_API_KEY")}, timeout=20)
        q("ElevenLabs kaliti", "ok" if r.status_code == 200 else "XATO",
          "" if r.status_code == 200 else f"kalit qabul qilinmadi ({r.status_code})")
    except Exception as e:  # noqa: BLE001
        q("ElevenLabs kaliti", "XATO", str(e)[:120])
else:
    q("ElevenLabs kaliti", "ixtiyoriy", "yo'q — transkript Whisper bilan qilinadi")

out = Path.home() / "Documents" / "Reels tahlillari"
out.mkdir(parents=True, exist_ok=True)
q("Tahlillar papkasi", "ok", str(out))

sys.exit(1 if xato else 0)
