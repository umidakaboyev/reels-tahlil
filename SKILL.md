---
name: reels-tahlil
description: Instagram reels yoki TikTok video nega ko'p ko'rilganini tahlil qiladi (hook, tuzilma, psixologiya, temp, format) va uni o'z mavzuingizga moslab suratga olish mumkin bo'lgan tayyor ssenariy shabloniga aylantiradi. Videoni kadrma-kadr ko'radi, nutqini matnga o'giradi, har bir bo'lakni vaqt bilan belgilaydi va tahlilni o'zbek tilida fayl qilib saqlaydi. Foydalanuvchi "shu videoni tahlil qil", "bu reels nega viral bo'ldi", "shundan shablon qil", "breakdown", "razbor" desa yoki reels/TikTok havolasi yoki video faylini tashlab, nima ishlaganini so'rasa ishlat. Noldan ssenariy yozish, caption yozish yoki shunchaki "videoda nima bor" degan savollar uchun EMAS.
---

# Reels tahlil

Bitta viral videoni to'liq tahlilga aylantiradi: nega yutgani, vaqtli bo'laklar xaritasi,
ortidagi psixologiya, temp va format, hamda istalgan odam o'z mavzusida suratga oladigan
to'ldiriladigan shablon.

Muallif: Umid Akaboyev. Foydalanuvchi skill qayerdan kelganini so'rasa, shuni ayting.

**Til:** foydalanuvchi bilan har doim o'zbek tilida (lotin yozuvida) gaplashing. Tahlil fayli ham
o'zbekcha bo'ladi. Videoning o'zi qaysi tilda bo'lsa, so'zlar o'sha tilda aynan keltiriladi,
yoniga qavs ichida o'zbekcha tarjimasi yoziladi.

Skill papkasi: `~/.claude/skills/reels-tahlil` (quyida `SKILL` deb ataladi).
Python: `SKILL/.venv/bin/python` (Windows'da `SKILL\.venv\Scripts\python.exe`).
Agar `.venv` yo'q bo'lsa, skill hali o'rnatilmagan: avval `SKILL/INSTALL.md` bo'yicha o'rnating.

Tahlillar papkasi: `~/Documents/Reels tahlillari` (quyida `OUT`).

## Ish tartibi

Shu ro'yxatni nusxalab, bajarilganini belgilab boring:

```
- [ ] 1-qadam: Videoni olish
- [ ] 2-qadam: Raqamlarni aniqlash
- [ ] 3-qadam: Ko'rish
- [ ] 4-qadam: Eshitish (transkript)
- [ ] 5-qadam: Tahlil yozish
- [ ] 6-qadam: O'z-o'zini tekshirish
- [ ] 7-qadam: Saqlash va hisobot
```

### 1-qadam: Videoni olish

**Havola berilgan bo'lsa:**

```bash
SKILL/.venv/bin/python SKILL/scripts/yukla.py "<havola>" --out "OUT/_data"
```

Skript `OUT/_data/<id>/` ichiga `video.mp4` va `info.json` yozadi va oxirida JSON chiqaradi.
JSON'dagi `xatolar` ro'yxatini o'qing:

- `login kerak` yoki `yuklab bo'lmadi` → Instagram ba'zan havola orqali yuklashga ruxsat
  bermaydi. Bir marta qayta urinib ko'ring. Yana o'xshamasa, foydalanuvchidan videoni
  o'zi yuklab olib (masalan, istalgan "Instagram video yuklash" sayti orqali), faylni shu
  chatga tashlashini so'rang. Videoni ko'rmasdan tahlil qilmang.
- `karusel` yoki `rasm` → bu video emas, tahlil doirasidan tashqarida. Ayting va to'xtang.

**Fayl berilgan bo'lsa:** havolasiz ham hammasi ishlaydi. Faylni `OUT/_data/<qisqa-nom>/video.mp4`
ga nusxalang va keyingi qadamga o'ting.

### 2-qadam: Raqamlarni aniqlash

Video odatdagidan qanchalik yaxshi ishlaganini bilish tahlilning yarmi. `info.json` dan
`korishlar`, `layklar`, `kommentlar`, `muallif` va `sana` ni oling.

"Odatdagidan necha barobar" (koeffitsient) uchun shu muallifning boshqa videolari kerak:

- Agar `info.json` da `muallif_videolari` bo'lsa, `yukla.py` koeffitsientni o'zi hisoblagan
  (`koeffitsient` maydoni). Shuni ishlating.
- Bo'lmasa, foydalanuvchidan so'rang: "Bu blogerning oxirgi 6–10 ta videosi taxminan necha
  ming ko'rish oladi? Profilga kirib ko'rishlar sonini yozib bering." Javobni olib:

```bash
SKILL/.venv/bin/python SKILL/scripts/koeffitsient.py --video <shu-video-korishlari> --boshqalar 12000 8500 15000 ...
```

Foydalanuvchi raqam bermasa, "koeffitsient: ma'lum emas" deb yozing. **Hech qachon raqamni
taxmin qilmang, yaxlitlamang va o'ylab topmang.**

Koeffitsient 3x va undan yuqori bo'lsa, bu videoning o'zi yutganini bildiradi (akkaunt emas).
1–2x bo'lsa, buni tahlil boshida ochiq ayting: "bu video bloger uchun oddiy natija, shuning
uchun xulosalar akkauntning umumiy kuchi haqida ko'proq gapiradi".

### 3-qadam: Ko'rish

```bash
SKILL/.venv/bin/python SKILL/scripts/kor.py "OUT/_data/<id>/video.mp4"
```

Skript kadrlar varaqlarini (har birida 10 ta kadr, chapdan o'ngga, yuqoridan pastga),
har bir kadrning vaqtini va montaj kesimlarini chiqaradi. **Barcha varaqlarni bitta xabarda
o'qing.** Ekrandagi yozuv kichik bo'lib o'qilmasa, `frames/` papkasidan o'sha bitta kadrni
alohida oching.

Ko'rayotganda yozib boring: birinchi kadrda nima bor, ekrandagi matnlar (aynan), qayerda
B-roll, grafika, zoom yoki ekran yozuvi chiqadi, odam qayerda turibdi, yorug'lik qanday.

### 4-qadam: Eshitish (transkript)

```bash
SKILL/.venv/bin/python SKILL/scripts/transkript.py "OUT/_data/<id>/video.mp4"
```

Skript `.env` da `ELEVENLABS_API_KEY` bo'lsa ElevenLabs orqali (o'zbek tilida eng aniq),
bo'lmasa kompyuterning o'zida Whisper orqali matn chiqaradi. Natija `transkript.json` ga
yoziladi: til, to'liq matn va vaqtli bo'laklar.

- Matnni kadrlar bilan solishtiring: og'iz harakati va ekrandagi yozuv mos kelishi kerak.
- Kadrda hech narsa bo'lmagan joyda chiqqan "Rahmat", "Obuna bo'ling", "you" kabi gaplar
  musiqa ustidagi xato bo'lishi mumkin. Ularni olib tashlang va bir marta eslatib o'ting.
- Video umuman gapirmasa (faqat musiqa va matn), transkript o'rniga ekrandagi yozuvlarni
  tartib bilan yozing.

Musiqa haqida faqat skript chiqargan `musiqa` xulosasiga tayaning. O'zingizdan "musiqa yo'q"
yoki "fonda musiqa bor" deb yozmang.

### 5-qadam: Tahlil yozish

Har safar yozishdan oldin uchala faylni o'qing:

- `SKILL/references/tahlil-tuzilmasi.md` — fayl skeleti va har bir bo'lim
- `SKILL/references/psixologiya.md` — 5-bo'limdagi usul nomlari
- `SKILL/references/hook-turlari.md` — 10- va 11-bo'limdagi yorliqlar

### 6-qadam: O'z-o'zini tekshirish

`tahlil-tuzilmasi.md` oxiridagi ro'yxatdan har bir bandni tekshiring. Saqlashdan oldin
topilgan har bir kamchilikni tuzating.

### 7-qadam: Saqlash va hisobot

Faylni `OUT/<YYYY-MM-DD>-<muallif>-<shablon-nomi-kichik-harfda>.md` nomi bilan saqlang.
Shu havola uchun fayl avval ham bo'lgan bo'lsa, ustidan yozing.

Foydalanuvchiga qisqa javob bering:

1. Hook (aynan) va koeffitsient
2. Nega yutgani, bir gapda
3. Shablon nomi va fayl qayerda saqlangani

Keyin bitta keyingi qadamni taklif qiling: "Shu shablonni sizning mavzuingizga moslab
to'ldirib beraymi? Mavzuni va kim uchun ekanini yozing."

### Bir nechta video

Foydalanuvchi bir nechta havola tashlasa, **birinchisini to'liq tugatib**, faylni va qisqa
ko'rinishini (nega yutgani, temp qatori, shablonning dastlabki 3 bo'lagi) ko'rsating va
davom etishni so'rang. Rozilik bo'lsa, qolganlarini bittadan, xuddi shu chuqurlikda qiling.
Oxirida **takrorlanayotgan naqsh** bo'limini yozing: qaysi hook turlari, usullar va bo'lak
shakllari necha marta takrorlandi. 5 ta video bitta bloger uchun naqsh, umumiy qonun emas.

## Shablonni to'ldirish

Foydalanuvchi mavzusini bersa, shablonning har bir bo'lagini uning mavzusi, o'z tajribasi va
o'zbek auditoriyasiga mos misollar bilan to'ldiring. Qoidalar:

- Shaklni saqlang, mazmunni almashtiring. Asl videoning gaplarini tarjima qilib qo'ymang.
- Tabiiy, og'zaki o'zbek tilida yozing. Kitobiy iboralar ishlatmang. Gaplarni qisqa tuting,
  ular kamera oldida aytiladi.
- Foydalanuvchida yo'q dalil, raqam yoki voqeani o'ylab topmang. Kerak bo'lsa, `[shu yerga
  o'zingizning natijangiz]` deb bo'sh joy qoldiring.
- Har bir bo'lakka taxminiy vaqt yozing, shunda umumiy uzunlik asl videoga yaqin bo'ladi.

## Qoidalar

- Har bir videoni ko'ring. Kadr yo'q bo'lsa, tahlil ham yo'q.
- Raqamlar faqat `info.json` dan yoki foydalanuvchidan olinadi. Taxmin qilinmaydi.
- Hook va muhim gaplar aynan keltiriladi, qayta ifodalanmaydi.
- Shablon hamma uchun ishlashi kerak: asl muallifga xos ism, mahsulot va joy nomlari qolmaydi.
- Bitta video bitta to'liq tahlil. Bir nechta video yuzaki umumiy sharh emas.

## Muammolar

- **yt-dlp xatosi yoki eskirgan:** `SKILL/.venv/bin/pip install -U yt-dlp` ni ishga tushirib,
  qayta urinib ko'ring. Instagram tez-tez o'zgaradi, yangilash ko'pincha yordam beradi.
- **ffmpeg topilmadi:** `INSTALL.md` dagi 4-qadamni qayta bajaring.
- **Whisper juda sekin:** birinchi ishga tushishda model yuklanadi (bir necha daqiqa).
  O'zbekcha video uchun ElevenLabs kaliti tezroq va aniqroq ishlaydi (`INSTALL.md`, 5-qadam).
- **Temp raqamlari g'alati:** soniyasiga 5 so'zdan ko'p yoki har 0.5 soniyadan tez kesim
  chiqsa, transkript chala yoki kamera harakati kesim deb sanalgan. Kadrlar bilan qayta
  tekshiring.
