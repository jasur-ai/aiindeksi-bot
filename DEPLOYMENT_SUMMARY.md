# Joylashtirish holati va tekshiruv yo'riqnomasi

> **Bu deploy tasdig'i emas.** Mahalliy koddagi o'zgarishlar hech qayerga push yoki deploy qilinmagan. Jonli Cloudflare Pages yoki Render servisi ushbu nusxa bilan bir xil ekani tekshirilmagan.

## Joriy koddagi asosiy yo'nalishlar

- Ommaviy sahifada noto'g'ri “Ilovani yuklab olish” amali olib tashlangan; a'zolik havolasi Telegram botga olib boradi.
- Kirish JSON API orqali amalga oshadi. Sessiya tokeni URL query stringga qo'yilmaydi; brauzer `sessionStorage` va `Authorization: Bearer` sarlavhasidan foydalanadi.
- API faqat oldindan belgilangan sayt originlariga CORS ruxsat beradi va `OPTIONS` preflight so'rovlariga javob beradi.
- Web hisoblari PBKDF2-HMAC-SHA256 bilan salt qo'shib xeshlanadi. Administrator va a'zo huquqlari API darajasida ajratilgan.
- Hisob amallari audit qilinadi; parol matni log yoki audit jurnaliga kiritilmaydi.
- Hujjatlar `private_docs/` katalogidan faqat sessiyali API orqali beriladi. Omborda hozir yuklab olinadigan hujjat fayllari yo'q.

## Render servisida talab qilinadigan sozlamalar

Mavjud loyiha sozlamalarini saqlagan holda quyidagilarni tekshiring:

- `AIINDEKSI_TOKEN` — Telegram bot tokeni.
- `AIINDEKSI_ADMIN` — Telegram administrator ID(lar)i; vergul bilan ajratilgan qiymatlar qabul qilinadi.
- `AILABS_DB_REPO` va `AILABS_DB_TOKEN` — amaldagi baza sinxronlash sozlamalari (maxfiy qiymatlarni faqat hosting sozlamalarida kiriting).
- `RT_SITE_SESSION_SECRET` — kamida 32 tasodifiy belgili, bot tokenidan alohida sir. Uni, masalan, lokal xavfsiz terminalda `python -c 'import secrets; print(secrets.token_urlsafe(48))'` bilan yarating va faqat Render Environment sahifasida saqlang. Chatga yoki repoga yubormang.
- `PORT` Render tomonidan beriladi.

`RT_SITE_SESSION_SECRET` sozlanmasa, servis ishga tushganda tasodifiy kalit yaratadi; bu holatda restart yoki ko'p nusxali servis sessiyani bekor qilishi mumkin. Doimiy production ishlashi uchun barqaror sirni hostingda sozlang.

## Cloudflare Pages / CORS

API ruxsat ro'yxatidagi production origin:

- `https://raqamlitadqiqot.pages.dev`

Custom domain ishlatilsa, uning aniq HTTPS originini backenddagi `SITE_ORIGINS` ro'yxatiga qo'shib, backendni qayta chiqarish kerak. Har qanday originni `*` bilan ochmang. Local ishlab chiqish uchun `http://localhost:5500` va `http://127.0.0.1:5500` ruxsat etilgan.

## Hujjat fayllari

Hujjatlarni `site/` ichiga qo'ymang: u Cloudflare Pages orqali ommaga chiqishi mumkin. Hujjatlarni Render persistent diskiga joylashtiring va `RT_PRIVATE_DOCS_DIR` bilan katalogni ko'rsating yoki shifrlangan, autentifikatsiyalangan saqlash tizimini sozlang. Hozirgi API faqat PDF, DOCX, XLSX, PPTX, TXT va Markdown fayllarni ro'yxatlaydi va sessiya bilan beradi. Render fayl tizimi vaqtinchalik bo'lishi mumkin; doimiy saqlashni alohida hal qiling.

## Deploydan keyingi sinovlar

1. `GET /healthz` — servis javob berishini tekshiring.
2. `https://raqamlitadqiqot.pages.dev` sahifasidan kirish oynasini ochib, faqat test hisobi bilan auth sinovi o'tkazing.
3. Brauzer Network panelida `OPTIONS /api/auth` va `OPTIONS /api/admin/users` javobida ruxsat etilgan origin hamda `Authorization, Content-Type` sarlavhalari borligini tekshiring.
4. A'zo hisobi `/api/admin/users` ga kira olmasligini (`403`), web-admin kira olishini (`200`) sinang.
5. Test parolini tiklab, avvalgi sessiya bekor bo'lishini; audit jurnalida hodisa qayd etilib, parolning o'zi yo'qligini tekshiring.
6. Hujjat fayli bo'lmasa, katalog bo'sh ko'rinishi kerak. Haqiqiy hujjatlar berilmaguncha test fayllarni official material sifatida chiqarmang.

## Nimalar tasdiqlanmagan

Jonli deploy, loginning production muhitida ishlashi, GitHub bazasiga haqiqiy yozilish, zaxira chastotasi, ISO 27001/GDPR/OWASP/WCAG muvofiqligi va mustaqil pentest ushbu ishda tasdiqlanmagan. Koddagi xavfsizlik choralarini sertifikat yoki to'liq audit deb talqin qilmang.
