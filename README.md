# Raqamli Tadqiqot klubi boti (@aiindeksi_bot)

TDIU talabalarining ochiq manbalar asosidagi tadqiqot loyihasi uchun Telegram bot, Mini App va interaktiv sayt.

**Talab:** Python 3.8+ standart kutubxonasi. `pip` paketi talab qilinmaydi.

## Ishga tushirish

```bash
export AIINDEKSI_TOKEN="..."        # yoki token.txt
export AIINDEKSI_ADMIN="telegram_id" # yoki admin.txt; ID lar vergul bilan ajratilishi mumkin
export AIINDEKSI_CHANNEL="@kanal"    # ixtiyoriy
export AILABS_DB_REPO="owner/private-repo" # ixtiyoriy: doimiy JSON baza
export AILABS_DB_TOKEN="..."         # faqat hosting sirlarida saqlang
export RT_SITE_SESSION_SECRET="..."  # kamida 32 tasodifiy belgi, bot tokenidan alohida
python3 aiindeksi_bot.py
```

`RT_SITE_SESSION_SECRET` ni lokal xavfsiz terminalda `python -c 'import secrets; print(secrets.token_urlsafe(48))'` bilan yarating. Qiymatni chatga, ommaviy repo'ga yoki hujjatlarga kiritmang. U sozlanmasa, sessiyalar servis restartidan keyin bekor bo'lishi mumkin.

Sinov: `python3 aiindeksi_bot.py --demo` · Bot regressiya testi: `python3 aiindeksi_bot.py --test` · Auth/CORS integratsion testlari: `python3 -m unittest test_site_auth.py`.

## Bot funksiyalari

- `/start` — a'zolik ma'lumotlarini kiritish · `/foyda` · `/help` · `/holat` · `/bekor`.
- Admin: `/statlar`, `/royxat`, `/export`, `/export csv`, `/elon <matn>`.
- Tadbirlar va rollar — faqat ruxsat etilgan tashkilotchilar uchun.
- Sayt hisoblari — faqat `AIINDEKSI_ADMIN` ro'yxatidagi administratorning **shaxsiy chatida**:
  - `/sayt_admin login` — web-admin hisobini yaratish yoki yangilash;
  - `/qosh login` — a'zo hisobi yaratish;
  - `/loginlar` — loginlar va huquqlarni ko'rish;
  - `/parol login` — parolni tiklash;
  - `/ochir login` — a'zo hisobini o'chirish;
  - `/sayt_audit` — hisob amallarining oxirgi yozuvlari.

Parolni Telegramga yubormang: parol argumentli buyruqlar rad etiladi. Vakolatli adminning shaxsiy chatdagi buyrug'i 30 daqiqalik bir martalik aktivatsiya havolasini beradi. Havola faqat hisob egasiga shaxsiy yetkaziladi; parol HTTPS sahifada o'rnatiladi. DB'da havola tokenining faqat SHA-256 digesti, parolning esa saltli PBKDF2-HMAC-SHA256 xeshi saqlanadi. Guruhga adashib yuborilgan parolli buyruqni o'chirishga urinish bor, ammo Telegram bunga ruxsat bermasligi mumkin.

## Sayt va sessiyalar

- `site/` — Cloudflare Pages statik sayt (`https://raqamlitadqiqot.pages.dev`). Public saytda ilova yuklab olish tugmasi yo'q; a'zolik Telegram bot orqali.
- `site/admin.html` — autentifikatsiyadan so'ng hisoblar, hujjatlar va audit bo'limlarini ko'rsatadi. Admin amallari backendda rol bo'yicha tekshiriladi.
- Chiqish serverdagi hisob sessiyalarini bekor qiladi; eski bearer bilan API qayta ochilmaydi.
- Auth sessiyasi 12 soatgacha amal qiladi; token URL query stringga qo'yilmaydi. Frontend `sessionStorage` va `Authorization: Bearer` ishlatadi.
- CORS ruxsat ro'yxati `SITE_ORIGINS` da. Yangi/custom production domen ishlatilsa, aniq HTTPS originni backend ro'yxatiga qo'shib deploy qilish kerak; wildcard ishlatmang.
- Himoyalangan hujjatlar `RT_PRIVATE_DOCS_DIR` bilan ko'rsatilgan yoki Render muhitidagi `private_docs/` katalogidan beriladi. Bu katalog `site/` tashqarisida bo'lishi shart; omborda hozir real hujjat fayllari yo'q. Render persistent diskiga mount qilib, yo'lni `RT_PRIVATE_DOCS_DIR` ga sozlash kerak; doimiy saqlash alohida tekshirilsin.

## Mahalliy tekshiruv va joylashtirish

- Syntax/regressiya: `python3 aiindeksi_bot.py --test`.
- Render web service uchun `PORT` hosting tomonidan beriladi; backend `/healthz` yo'lini taqdim etadi.
- Cloudflare/Render deploy faqat tegishli loyiha egasi ruxsat berganda bajariladi. Joriy chiqarish holatini provider deployment ID va `/healthz` orqali tekshiring; kod nusxasining o‘zi deploy tasdig‘i emas.

## Ma'lumotlar va da'volar

Baza JSON ko'rinishida saqlanadi; `AILABS_DB_REPO` va `AILABS_DB_TOKEN` to'g'ri sozlangandagina GitHub API orqali sinxronlanadi. Saqlash chastotasi va tiklash SLA'si alohida tekshirilishi kerak.

Saytdagi pilot raqamlari loyiha ichki hisobotida keltirilgan qiymatlardir; mustaqil audit/tekshiruv deb talqin qilinmaydi. ISO 27001, GDPR, OWASP yoki WCAG sertifikatlari va muvofiqligi tasdiqlanmagan. `FINAL_STATUS.md`, `COMPREHENSIVE_PROJECT_SUMMARY.md` va `DEPLOYMENT_SUMMARY.md` shu cheklovlarni qayd etadi.

## Release 2026-10-14.1

Backend `/healthz` javobida `release: 2026-10-14.1`, `auth_api: 2` qaytaradi. Frontendni shu API bilan birga tekshiring. Qo‘shimcha xavfsizlik sinovlari: `python -m unittest test_release_security.py`. Aktivatsiya admin hisobini avtomatik yaratmaydi: vakolatli bot admini `/sayt_admin login` orqali boshlaydi.
