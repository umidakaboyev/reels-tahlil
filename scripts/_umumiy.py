"""Skriptlar uchun umumiy yordamchilar: ffmpeg'ni topish va .env faylini o'qish."""
import os
import shutil
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = SKILL_DIR / ".env"


def ffmpeg_tayyorla():
    """ffmpeg va ffprobe PATH'da bo'lishini ta'minlaydi (kerak bo'lsa static-ffmpeg orqali)."""
    if shutil.which("ffmpeg") and shutil.which("ffprobe"):
        return
    try:
        import static_ffmpeg
        static_ffmpeg.add_paths()  # birinchi marta ~70 MB yuklab oladi
    except Exception as e:  # noqa: BLE001
        raise SystemExit(f"ffmpeg topilmadi va o'rnatib bo'lmadi: {e}. INSTALL.md, 4-qadamga qarang.")


def env(nom):
    """Avval muhit o'zgaruvchisidan, keyin skill papkasidagi .env dan qiymat oladi."""
    if os.environ.get(nom):
        return os.environ[nom]
    if ENV_FILE.exists():
        for qator in ENV_FILE.read_text(encoding="utf-8").splitlines():
            qator = qator.strip()
            if qator.startswith(nom + "="):
                return qator.split("=", 1)[1].strip().strip('"').strip("'") or None
    return None
