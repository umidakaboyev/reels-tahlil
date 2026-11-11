#!/usr/bin/env python3
"""Instagram reels yoki TikTok videoni havola orqali yuklab oladi va raqamlarini yozadi.

Ishlatish:
  python yukla.py <havola> --out PAPKA [--brauzer chrome]

PAPKA/<id>/video.mp4 va PAPKA/<id>/info.json yoziladi, oxirida JSON chiqariladi.
--brauzer: Instagram login so'rasa, shu brauzerdagi sessiyadan foydalanadi
(chrome, safari, firefox, edge). Parol hech qayerga yozilmaydi.

TikTok uchun muallifning oxirgi videolarini ham o'qib, shu video odatdagidan necha barobar
ko'p ko'rilganini (koeffitsient) hisoblashga harakat qiladi. Instagram'da bu ko'pincha
ishlamaydi; unda koeffitsient.py bilan qo'lda hisoblanadi.
"""
import argparse
import json
import statistics
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _umumiy import ffmpeg_tayyorla  # noqa: E402

ffmpeg_tayyorla()

try:
    import yt_dlp
except ImportError:
    sys.exit("yt-dlp o'rnatilmagan. INSTALL.md, 3-qadamga qarang.")

SOLISHTIRISH_SONI = 12  # muallifning nechta boshqa videosi bilan solishtiriladi


class _JimLog:
    def debug(self, m): pass
    def info(self, m): pass
    def warning(self, m): pass
    def error(self, m): pass


def _sana(s):
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y%m%d").strftime("%Y-%m-%d")
    except ValueError:
        return s


def _opts(out_dir, brauzer, **qoshimcha):
    o = {"quiet": True, "no_warnings": True, "logger": _JimLog(), "noplaylist": True,
         "outtmpl": str(out_dir / "%(id)s" / "video.%(ext)s"),
         "format": "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/bv*+ba/b",
         "merge_output_format": "mp4", "retries": 3}
    if brauzer:
        o["cookiesfrombrowser"] = (brauzer,)
    o.update(qoshimcha)
    return o


def _muallif_korishlari(info, brauzer):
    """TikTok: muallifning oxirgi videolari ko'rishlari (shu videodan tashqari)."""
    if "tiktok" not in (info.get("extractor") or "").lower():
        return None
    handle = info.get("uploader") or info.get("uploader_id")
    if not handle:
        return None
    url = f"https://www.tiktok.com/@{handle}"
    try:
        with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True, "logger": _JimLog(),
                               "extract_flat": True, "playlistend": 40,
                               **({"cookiesfrombrowser": (brauzer,)} if brauzer else {})}) as y:
            p = y.extract_info(url, download=False)
    except Exception:  # noqa: BLE001
        return None
    entries = [e for e in (p or {}).get("entries") or [] if e]
    ids = [e.get("id") for e in entries]
    if info.get("id") in ids:
        # shu videoning atrofidagi videolar: yoshiga yaqinlari adolatliroq solishtiriladi
        i = ids.index(info["id"])
        yaqin = entries[max(0, i - SOLISHTIRISH_SONI // 2): i] + entries[i + 1: i + 1 + SOLISHTIRISH_SONI // 2]
    else:
        yaqin = entries[:SOLISHTIRISH_SONI]
    sonlar = [e.get("view_count") for e in yaqin if isinstance(e.get("view_count"), int)]
    return sonlar or None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("havola")
    ap.add_argument("--out", required=True)
    ap.add_argument("--brauzer", help="chrome / safari / firefox / edge")
    a = ap.parse_args()
    out_dir = Path(a.out).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)

    xatolar = []
    try:
        with yt_dlp.YoutubeDL(_opts(out_dir, a.brauzer)) as y:
            info = y.extract_info(a.havola, download=True)
    except Exception as e:  # noqa: BLE001
        matn = str(e)
        if any(k in matn.lower() for k in ("login", "cookies", "rate-limit", "private")):
            xatolar.append("login kerak: --brauzer chrome bilan qayta urinib ko'ring yoki faylni qo'lda yuklang")
        xatolar.append(f"yuklab bo'lmadi: {matn[:300]}")
        print(json.dumps({"ok": False, "xatolar": xatolar}, ensure_ascii=False, indent=1))
        sys.exit(1)

    if info.get("_type") == "playlist" or info.get("entries"):
        xatolar.append("karusel: bu post bir nechta fayldan iborat, video tahlili uchun emas")
        print(json.dumps({"ok": False, "xatolar": xatolar}, ensure_ascii=False, indent=1))
        sys.exit(1)

    vdir = out_dir / str(info["id"])
    video = next(iter(sorted(vdir.glob("video.*"))), None)
    if not video or video.suffix.lower() not in (".mp4", ".mov", ".webm", ".mkv"):
        xatolar.append("rasm yoki video fayli topilmadi")
    elif video.name != "video.mp4":
        video.rename(vdir / "video.mp4")
        video = vdir / "video.mp4"

    korish = info.get("view_count") if isinstance(info.get("view_count"), int) else None
    if korish is None:
        korish = info.get("play_count") if isinstance(info.get("play_count"), int) else None
    if korish is None:
        xatolar.append("ko'rishlar soni berilmadi: foydalanuvchidan so'rang")

    boshqalar = _muallif_korishlari(info, a.brauzer)
    koef = None
    if korish and boshqalar and len(boshqalar) >= 3:
        med = statistics.median(boshqalar)
        if med > 0:
            koef = round(korish / med, 1)
    elif korish:
        xatolar.append("muallifning boshqa videolari o'qilmadi: koeffitsientni koeffitsient.py bilan hisoblang")

    natija = {
        "id": str(info["id"]),
        "platforma": "tiktok" if "tiktok" in (info.get("extractor") or "").lower() else "instagram",
        "havola": info.get("webpage_url") or a.havola,
        "muallif": info.get("uploader") or info.get("channel") or info.get("uploader_id"),
        "sana": _sana(info.get("upload_date")),
        "davomiylik_s": info.get("duration"),
        "korishlar": korish,
        "layklar": info.get("like_count"),
        "kommentlar": info.get("comment_count"),
        "ulashishlar": info.get("repost_count"),
        "obunachilar": info.get("channel_follower_count"),
        "caption": info.get("description"),
        "musiqa_trek": info.get("track") or info.get("artist"),
        "muallif_videolari": boshqalar,
        "median": statistics.median(boshqalar) if boshqalar else None,
        "koeffitsient": koef,
        "video": str(video) if video else None,
        "xatolar": xatolar,
    }
    (vdir / "info.json").write_text(json.dumps(natija, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"ok": not any(x.startswith(("rasm", "yuklab")) for x in xatolar),
                      **{k: natija[k] for k in ("id", "muallif", "korishlar", "koeffitsient",
                                                "davomiylik_s", "video", "xatolar")},
                      "info": str(vdir / "info.json")}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
