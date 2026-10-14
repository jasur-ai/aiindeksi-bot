# Raqamli Tadqiqot / RT Monitor — kod ko'rigi holati

> **Maqom: mahalliy kod ko'rigi va tuzatishlar.** Bu hujjat jonli saytga o'zgarish kiritilganini bildirmaydi. Push, deploy va production login sinovi bajarilmagan.

## O'zgartirilgan yo'nalishlar

- Ommaviy saytdan “Ilovani yuklab olish” tugmasi olib tashlandi; haqiqiy a'zolik oqimi Telegram botga yo'naltiriladi.
- Kirish oqimi CORS preflightni qo'llaydi, tokenni URLga qo'ymaydi va qisqa muddatli imzolangan sessiyadan foydalanadi.
- Sayt hisoblari PBKDF2-HMAC-SHA256 (salt bilan) orqali saqlanadi; admin roli barcha himoyalangan API amallarida tekshiriladi.
- Botdagi hisob boshqaruvi buyruqlari vakolatli adminning shaxsiy chatida ishlaydi. Parol yozilgan xabarni o'chirishga uriniladi; parol matni javob, xesh audit yozuvi yoki ilova logiga kiritilmaydi.
- Hisob yaratish, tiklash, o'zgartirish va o'chirish audit qilinadi; eski sessiyalar parol o'zgarganda bekor qilinadi.
- Rasmiy hujjatlar ommaviy HTML sahifasida katalog qilinmaydi. Backend katalogi hozirda haqiqiy hujjat fayllarisiz bo'sh.
- Pilot ko'rsatkichlarining izohlari 10 banklik pilot namunasini 35 banklik umumiy loyiha reyestridan ajratadi va qiymatlarni mustaqil audit qilingan deb ko'rsatmaydi.
- ISO 27001, GDPR, OWASP yoki WCAG sertifikat/tekshiruvlari bor degan tasdiqlanmagan da'volar olib tashlanmoqda yoki aniq ogohlantirish bilan almashtirilmoqda.

## Hali bajariladigan tekshiruvlar

- Mahalliy Python sintaksis va mavjud bot regressiya testlari.
- Auth/CORS/API rollari bo'yicha lokal integratsion testlar.
- HTML/JavaScript tuzilmasi va end-user oqimi bo'yicha statik tekshiruv.
- `RT_SITE_SESSION_SECRET` ni Render muhitida sozlash va productionda tasdiqlash (faqat deploy egasi amalga oshiradi).
- Haqiqiy hujjat fayllari bo'lsa, ularni public `site/` tashqarisidagi himoyalangan saqlashga joylashtirish.

## Tasdiqlanmaganlar

Live site/Render deployment va production sessiyasi sinovdan o'tkazilmagan. Pilot ko'rsatkichlari loyiha ichki qiymatlaridir; mustaqil dalil-arxiv ko'rilmagan. ISO/GDPR/OWASP/WCAG muvofiqligi va “0 zaiflik” da'vosi tasdiqlanmagan.
