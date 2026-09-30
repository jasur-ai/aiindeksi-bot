# AI INDEKSI klubi boti (@aiindeksi_bot)

Toshkent davlat iqtisodiyot universiteti · «Sun'iy intellekt monitoringi va raqamli
o'lchov» klubi (ADRL / AAI-UZ) rasmiy ro'yxatdan o'tish va kanal boshqaruvi boti.

**Talab:** faqat Python 3.8+ standart kutubxonasi. Hech qanday pip-paket kerak emas.

## Ishga tushirish
```bash
export AIINDEKSI_TOKEN="***"      # yoki token.txt
export AIINDEKSI_ADMIN="chat_id"          # yoki admin.txt (@userinfobot dan)
export AIINDEKSI_CHANNEL="@kanal"         # yoki channel.txt (ixtiyoriy)
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

## Render'da doimiy ishlatish
1. GitHub repo'ni Render'ga ulang → **Background Worker** (yoki Web Service):
   start command `python3 aiindeksi_bot.py`, env: yuqoridagi 3 o'zgaruvchi.
2. `miniapp/` papkasi uchun **Static Site**: build `echo ok`, publish dir `miniapp`.

## Maxfiylik
Bot faqat ism, fakultet, kurs, yo'nalish va Telegram ID saqlaydi; ma'lumotlar
klub Nizomi 8-bo'limi bo'yicha faqat klub ichida ishlatiladi. `token.txt`,
`admin.txt`, DB fayllari `.gitignore` da — repo'ga tushmaydi.
