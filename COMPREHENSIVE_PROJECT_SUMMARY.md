# Raqamli Tadqiqot / RT Monitor — loyiha xulosasi

> **Dalil va maqom eslatmasi.** Ushbu matn kod omboridagi holatni tavsiflaydi; u jonli servis joylashtirilgani, rasmiy ro'yxatdan o'tish, sertifikat yoki mustaqil audit dalili emas. Pilot raqamlari loyiha ichki hisobotida keltirilgan va ushbu omborda ularni mustaqil tasdiqlovchi manba-arxiv mavjud emas.

## 1. Loyiha

**Raqamli Tadqiqot** — ochiq manbalar asosida tashkilotlarda sun'iy intellektdan foydalanish bo'yicha dalillarni to'plash va tahlil qilishga mo'ljallangan talabalar tadqiqot loyihasi. Platforma Telegram boti, Mini App va interaktiv ommaviy sayt qismlaridan iborat.

## 2. Ombordagi funksiyalar

- Telegram orqali a'zolik ma'lumotlarini yig'ish va boshqarish.
- Ochiq manbalar bo'yicha pilot ko'rsatkichlarini va interaktiv indeks kalkulyatorini ko'rsatuvchi sayt.
- A'zolik o'z-o'zini ro'yxatdan o'tkazish orqali emas; saytdagi hisoblarni vakolatli administrator taqdim etadi.
- Himoyalangan ish maydoni: mavjud bo'lsa, a'zo hujjatlarni ko'rishi mumkin; web-admin hisoblar va audit yozuvlarini boshqaradi.
- Sayt parollari PBKDF2-HMAC-SHA256 bilan alohida salt qo'shib xeshlanadi. Sessiyalar imzolangan, 12 soatgacha amal qiladi; parol tiklanganda eski sessiyalar bekor qilinadi.
- Hisob yaratish, parol tiklash/o'zgartirish va o'chirish hodisalari audit jurnaliga yoziladi; parol matni jurnalga kiritilmaydi.
- Brauzer API so'rovlari uchun CORS kelib chiqish manzillari ro'yxat bilan cheklanadi.

Ushbu mexanizmlar kod darajasidagi amaliy joriy etilishni ifodalaydi, lekin mustaqil xavfsizlik tekshiruvi yoki sertifikatni anglatmaydi. Ilova darajasida ma'lumotlar bazasini AES bilan shifrlash tasdiqlanmagan.

## 3. Pilot raqamlari — loyiha bildirgan qiymatlar

Sayt kodi va loyiha materiallarida 29.09.2026 sanasiga quyidagi ko'rsatkichlar keltiriladi:

| Ko'rsatkich | Loyiha bildirgan qiymat | Izoh |
|---|---:|---|
| Pilot namunasi | 10 bank | Umumiy reyestrdagi son bilan bir xil ko'rsatkich emas |
| O'lchov yo'nalishlari | 6 | Pilot metodikasida |
| Baholash kataklari | 60 | 10 × 6 |
| Dalil topilgan kataklar | 30 | Loyiha bildirgan, mustaqil audit qilinmagan |
| Ochiq manbalar | 32 | Loyiha bildirgan, manba-arxiv omborga kiritilmagan |
| Umumiy loyiha reyestri | 35 bank | Pilot namunasi 10 bank; qolgan reyestr birliklari pilotda o'lchangan deb talqin qilinmaydi |

Ushbu qiymatlar tasdiqlangan tashqi statistika yoki auditorlik xulosasi sifatida keltirilmasin. Manbalar va qayta hisoblash izlari taqdim etilgandagina mustaqil tekshirilgan natija deb belgilash mumkin. Dalil yo'qligi sababli ushbu xulosada banklar kesimidagi reyting/ballar berilmaydi.

## 4. Standartlar va muvofiqlik

- ISO/IEC 27001 sertifikati yoki muvofiqlik auditi tasdiqlanmagan.
- GDPR bo'yicha mustaqil huquqiy baholash tasdiqlanmagan.
- OWASP bo'yicha pentest yoki to'liq zaiflik tekshiruvi o'tkazilgani tasdiqlanmagan; zaifliklar soni bo'yicha “0” da'vosi berilmaydi.
- WCAG 2.1 AA auditi yoki muvofiqlik tasdiqlanmagan.
- Shu yo'nalishlar kelajakdagi baholash mezonlari bo'lishi mumkin, amaldagi sertifikat yoki tasdiq sifatida emas.

## 5. Hujjatlar va joylashtirish

- Omborda pilot hisobotining, nizomning yoki boshqa rasmiy hujjatlarning yuklab olinadigan fayllari mavjud emas. Himoyalangan katalog bo'sh bo'lsa, ish maydoni buni aniq ko'rsatadi; fayl nomlari yoki soxta yuklab olish havolalari yaratilmaydi.
- Sayt frontendining manzili `https://raqamlitadqiqot.pages.dev`; API manzili Render servisiga yo'naltirilgan. Ushbu mahalliy ish nusxasi jonli saytga chiqarilmagan va jonli login sinovi o'tkazilmagan.
- Ishlab turgan muhitda `RT_SITE_SESSION_SECRET` ni mustaqil, tasodifiy qiymat qilib sozlash tavsiya etiladi. Qiymatni ochiq kodga yoki chatga joylamang.

## 6. Cheklovlar

Ushbu xulosa kod omboridagi ma'lumotlar bilan chegaralangan. Tashkilot nomi, rasmiy maqom, rahbarlik, hamkorlik, byudjet, natijalar va joylashtirish haqidagi ma'lumotlarni tashqi hujjat yoki jonli tizim orqali alohida tasdiqlash talab etiladi.
