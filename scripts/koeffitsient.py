#!/usr/bin/env python3
"""Video muallifning odatdagi natijasidan necha barobar ko'p ko'rilganini hisoblaydi.

Ishlatish:
  python koeffitsient.py --video 250000 --boshqalar 12000 8500 15000 9900 ...
  python koeffitsient.py --video 250000 --boshqalar 12k 8.5k 1.2m ...   (k / m ham bo'ladi)
  python koeffitsient.py ... --info PAPKA/<id>/info.json   (natijani info.json ga ham yozadi)

Median ishlatiladi (o'rtacha emas): bitta tasodifan portlagan video o'lchovni buzmasligi uchun.
"""
import argparse
import json
import statistics
from pathlib import Path


def son(s):
    s = str(s).strip().lower().replace(",", "").replace(" ", "")
    kop = 1
    if s.endswith(("k", "ming")):
        kop, s = 1_000, s.rstrip("ming").rstrip("k")
    elif s.endswith(("m", "mln")):
        kop, s = 1_000_000, s.rstrip("mln").rstrip("m")
    return int(float(s) * kop)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--boshqalar", nargs="+", required=True)
    ap.add_argument("--info")
    a = ap.parse_args()
    v = son(a.video)
    b = [son(x) for x in a.boshqalar]
    if len(b) < 3:
        raise SystemExit("Kamida 3 ta boshqa video ko'rishlari kerak.")
    med = statistics.median(b)
    koef = round(v / med, 1) if med else None
    natija = {"korishlar": v, "muallif_videolari": b, "median": med, "koeffitsient": koef,
              "izoh": ("video o'zi yutgan (3x va undan ko'p)" if koef and koef >= 3 else
                       "bloger uchun odatiy yoki biroz yaxshi natija")}
    if a.info:
        p = Path(a.info).expanduser()
        d = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
        d.update({k: natija[k] for k in ("korishlar", "muallif_videolari", "median", "koeffitsient")})
        p.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(natija, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
