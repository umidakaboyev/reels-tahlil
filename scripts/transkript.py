#!/usr/bin/env python3
"""Videodagi nutqni vaqt belgilari bilan matnga o'giradi va fonda musiqa bor-yo'qligini baholaydi.

Ishlatish:
  python transkript.py <video.mp4> [--til uz] [--model small]

.env da ELEVENLABS_API_KEY bo'lsa ElevenLabs Scribe ishlatiladi (o'zbek tilida eng aniq).
Bo'lmasa kompyuterning o'zida faster-whisper ishlaydi (bepul, internet faqat birinchi
marta model yuklash uchun kerak).

Natija <video papkasi>/transkript.json ga yoziladi va qisqacha chiqariladi.
"""
import argparse
import json
import math
import subprocess
import sys
from array import array
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _umumiy import env, ffmpeg_tayyorla  # noqa: E402

ffmpeg_tayyorla()

SR = 16000


def audio_ol(video):
    """Mono 16 kHz float32 namunalar."""
    r = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(video), "-vn", "-ac", "1",
                        "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True)
    a = array("f")
    a.frombytes(r.stdout)
    return a


def elevenlabs(video, til, kalit):
    import requests
    wav = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(video), "-vn", "-ac", "1",
                          "-ar", str(SR), "-f", "wav", "-"], capture_output=True, check=True).stdout
    r = None
    for model in ("scribe_v2", "scribe_v1"):  # eng yangisi, eskirgan bo'lsa oldingisi
        data = {"model_id": model, "timestamps_granularity": "word", "tag_audio_events": "false"}
        if til:
            data["language_code"] = til
        r = requests.post("https://api.elevenlabs.io/v1/speech-to-text",
                          headers={"xi-api-key": kalit}, data=data,
                          files={"file": ("audio.wav", wav, "audio/wav")}, timeout=300)
        if r.status_code not in (400, 422) or "model" not in r.text.lower():
            break
    matn = r.text.lower()
    if r.status_code == 401:
        raise RuntimeError("ElevenLabs kalitni qabul qilmadi. Kalit noto'g'ri nusxalangan bo'lishi mumkin.")
    if r.status_code == 403 or "permission" in matn:
        raise RuntimeError("Kalitda Speech to Text ruxsati yo'q. ElevenLabs'da kalit sozlamasida "
                           "Speech to Text'ni yoqish kerak.")
    if r.status_code in (402, 429) or "quota" in matn or "credit" in matn or "payment" in matn:
        raise RuntimeError("ElevenLabs hisobida transkript uchun balans yoki limit tugagan.")
    r.raise_for_status()
    j = r.json()
    sozlar = [w for w in j.get("words", []) if w.get("type", "word") == "word"]
    # so'zlarni gap bo'laklariga yig'ish: tinish belgisi yoki 0.6 s dan uzun pauza bo'linish nuqtasi
    bolaklar, joriy = [], []
    for i, w in enumerate(sozlar):
        joriy.append(w)
        keyingi = sozlar[i + 1] if i + 1 < len(sozlar) else None
        tugadi = w["text"].rstrip().endswith((".", "!", "?", "…"))
        pauza = keyingi and keyingi["start"] - w["end"] > 0.6
        if tugadi or pauza or not keyingi:
            bolaklar.append({"start": round(joriy[0]["start"], 2), "end": round(joriy[-1]["end"], 2),
                             "matn": " ".join(x["text"].strip() for x in joriy).strip()})
            joriy = []
    return {"vosita": f"elevenlabs {model}", "til": j.get("language_code"),
            "matn": (j.get("text") or "").strip(), "bolaklar": bolaklar,
            "_sozlar": [(w["start"], w["end"]) for w in sozlar]}


def whisper(audio, til, model_nomi):
    try:
        import numpy as np
        from faster_whisper import WhisperModel
    except ImportError:
        sys.exit("faster-whisper o'rnatilmagan. INSTALL.md, 3-qadamga qarang.")
    a = np.frombuffer(audio.tobytes(), dtype=np.float32)
    if model_nomi == "auto":
        # Tilni kichik model bilan aniqlaymiz. Ingliz va rus tilida small yetarli,
        # o'zbek va boshqa tillarda esa katta model ancha yaxshi eshitadi.
        if not til:
            kichik = WhisperModel("small", device="cpu", compute_type="int8")
            til, ehtimol, _ = kichik.detect_language(a[: 30 * SR])
        model_nomi = "small" if til in ("en", "ru") else "large-v3-turbo"
    # O'zbekcha uchun lotin yozuvidagi namunaviy gap modelni to'g'ri imloga yo'naltiradi
    boshlov = ("Assalomu alaykum. Bugun sizlarga reels, Instagram va SMM haqida gapirib "
               "beraman. Ko'rishlar, obunachilar, kontent.") if til == "uz" else None
    m = WhisperModel(model_nomi, device="cpu", compute_type="int8")
    seg, inf = m.transcribe(a, language=til, initial_prompt=boshlov,
                            vad_filter=True, beam_size=5, word_timestamps=True)
    seg = list(seg)
    bolaklar = [{"start": round(s.start, 2), "end": round(s.end, 2), "matn": s.text.strip()} for s in seg]
    sozlar = [(w.start, w.end) for s in seg for w in (s.words or [])]
    return {"vosita": f"faster-whisper {model_nomi}", "til": inf.language,
            "matn": " ".join(b["matn"] for b in bolaklar), "bolaklar": bolaklar, "_sozlar": sozlar}


def db(namunalar):
    if not namunalar:
        return -120.0
    rms = math.sqrt(sum(x * x for x in namunalar) / len(namunalar))
    return round(20 * math.log10(rms), 1) if rms > 0 else -120.0


def musiqa_baho(audio, sozlar):
    """So'zlar orasidagi pauzalardagi ovoz balandligiga qarab fonda musiqa bor-yo'qligini baholaydi."""
    dur = len(audio) / SR
    gaplar = sorted(sozlar)
    boshliqlar, oldin = [], 0.0
    for s, e in gaplar:
        if s - oldin >= 0.25:
            boshliqlar.append((oldin + 0.05, s - 0.05))
        oldin = max(oldin, e)
    if dur - oldin >= 0.25:
        boshliqlar.append((oldin + 0.05, dur))
    jami = sum(e - s for s, e in boshliqlar)
    nutq_db = db([x for s, e in gaplar for x in audio[int(s * SR):int(e * SR)]][::4])
    if jami < 0.8:
        return {"xulosa": "aniqlab bo'lmadi (nutq orasida deyarli bo'sh joy yo'q)",
                "nutqsiz_qism_s": round(jami, 1), "nutq_db": nutq_db, "fon_db": None}
    fon = [x for s, e in boshliqlar for x in audio[int(s * SR):int(e * SR)]]
    fon_db = db(fon)
    if not gaplar:
        xulosa = "nutq yo'q; tovush bor (musiqa yoki trend tovush)" if fon_db > -40 else "nutq ham, musiqa ham deyarli yo'q"
    elif fon_db < -50:
        xulosa = "musiqa yo'q (pauzalarda jimlik)"
    elif fon_db < -38:
        xulosa = "fonda past tovush bor (xona shovqini yoki juda past musiqa), aniq emas"
    else:
        xulosa = "fonda musiqa yoki tovush bor (pauzalarda ham eshitiladi)"
    return {"xulosa": xulosa, "nutqsiz_qism_s": round(jami, 1), "nutq_db": nutq_db, "fon_db": fon_db}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--til", help="masalan uz, ru, en; berilmasa avtomatik aniqlanadi")
    ap.add_argument("--model", default="auto", help="auto (tavsiya), small, medium, large-v3-turbo")
    a = ap.parse_args()
    video = Path(a.video).expanduser().resolve()
    audio = audio_ol(video)

    kalit = env("ELEVENLABS_API_KEY")
    natija, ogohlantirish = None, None
    if kalit:
        try:
            natija = elevenlabs(video, a.til, kalit)
        except Exception as e:  # noqa: BLE001
            ogohlantirish = f"ElevenLabs ishlamadi, Whisper'ga o'tildi: {str(e)[:200]}"
    if natija is None:
        natija = whisper(audio, a.til, a.model)

    dur = len(audio) / SR
    soz_soni = len(natija["matn"].split())
    natija.update({
        "davomiylik_s": round(dur, 2),
        "soz_soni": soz_soni,
        "soz_sekundiga": round(soz_soni / dur, 1) if dur else None,
        "musiqa": musiqa_baho(audio, natija.pop("_sozlar")),
    })
    if ogohlantirish:
        natija["ogohlantirish"] = ogohlantirish
    if natija["vosita"].startswith("faster-whisper") and natija.get("til") == "uz":
        natija["elevenlabs_kerak"] = ("O'zbekcha nutq bepul model bilan yozildi, xatolar ko'p bo'lishi "
                                      "mumkin. SKILL.md: 'ElevenLabs'ni ulash' bo'limiga qarang.")
    if not natija["bolaklar"]:
        natija["izoh"] = "nutq topilmadi: ekrandagi matnlarga tayaning"

    (video.parent / "transkript.json").write_text(json.dumps(natija, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(natija, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
