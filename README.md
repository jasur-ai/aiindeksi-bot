# Raqamlab klubi boti (@aiindeksi_bot)

Toshkent davlat iqtisodiyot universiteti · «Raqamli o'lchov va sun'iy intellekt
monitoringi» klubi (ADRL / AAI-UZ) rasmiy ro'yxatdan o'tish va kanal boshqaruvi boti.

**Talab:** faqat Python 3.8+ standart kutubxonasi. Hech qanday pip-paket kerak emas.

## Ishga tushirish
```bash
export AIINDEKSI_TOKEN="***"      # yoki token.txt
export AIINDEKSI_ADMIN="chat_id"          # yoki admin.txt (@userinfobot dan)
export AIINDEKSI_CHANNEL="@kanal"         # yoki channel.txt (ixtiyoriy)
export AILABS_DB_REPO="owner/private-repo" # doimiy baza (db.json) — YOPIQ GitHub ombori
export AILABS_DB_TOKEN="***"               # shu omborga yozish huquqli token
python3 aiindeksi_bot.py
```
Sinov: `python3 aiindeksi_bot.py --demo` · Avto-test: `python3 aiindeksi_bot.py --test`

## Imkoniyatlar
- `/start` 4 savollik ro'yxat (ism → fakultet [TDIU rasmiy 14] → kurs → yo'nalish)
- `/foyda` 6 ta huquqiy asosli foyda · `/help` · `/holat` · `/bekor`
- Admin: `/statlar` (fakultet/kurs/kanal), `/export` (CSV **+ XLSX**, stdlib zipfile),
  `/elon <matn>` (kanalga e'lon)
- Kanal: force-subscribe, «Kanalga a'zo bo'ling» tugmasi
- `miniapp/` — Telegram Mini App (Render static site uchun tayyor)
- `site/` — rasmiy sayt (https://raqamlab.pages.dev, Cloudflare Pages): `cd cloudflare && wrangler pages deploy ../site --project-name raqamlab --branch main`
- `cloudflare/redirect/` — eski workers.dev manzillaridan saytga 301 yo'naltirish (ailabs, raqamli, raqamlab)

## Render'da doimiy ishlatish
1. GitHub repo'ni Render'ga ulang → **Background Worker** (yoki Web Service):
   start command `python3 aiindeksi_bot.py`, env: yuqoridagi 3 o'zgaruvchi.
2. `miniapp/` papkasi uchun **Static Site**: build `echo ok`, publish dir `miniapp`.

## Baza qayerda saqlanadi
Render bepul tarifida disk vaqtinchalik — har deploy/restartda lokal fayl o'chadi.
Shuning uchun ishchi nusxa xotirada, doimiy nusxa **yopiq GitHub omborida** (`db.json`,
har o'zgarish = alohida commit → to'liq tarix va zaxira). Qoidalar: ombor o'qilmaguncha
unga yozilmaydi; ikki nusxa to'qnashsa — birlashtiriladi; `/bekor` bilan o'chirilganlar
qayta tirilmaydi. Holat: `/statlar` dagi «💾 Baza» qatori.

Admin: `/statlar` · `/royxat` (telefonda matnli ro'yxat) · `/export` (Excel, har ustun alohida) ·
`/export csv` (vergulli CSV) · `/elon <matn>`.

## Maxfiylik
Bot faqat ism, fakultet, kurs, yo'nalish va Telegram ID saqlaydi; ma'lumotlar
klub Nizomi 8-bo'limi bo'yicha faqat klub ichida ishlatiladi. `token.txt`,
`admin.txt`, DB fayllari `.gitignore` da — repo'ga tushmaydi.
