# Admin panel funksiyalari

def _admin_main_menu():
    """Admin panel bosh menyusi."""
    text = """🛡 <b>ADMIN PANEL — RT Monitor</b>
━━━━━━━━━━━━━━━━━━━━━━━

Kerakli bo'limni tanlang:

📊 <b>Statistika</b> — umumiy ma'lumotlar
📈 <b>Pilot</b> — pilot natijalari
🔒 <b>Xavfsizlik</b> — joriy holat
👥 <b>Foydalanuvchilar</b> — ro'yxat
📋 <b>Audit</b> — hisobot
🤝 <b>Hamkorlik</b> — taklif
📤 <b>Export</b> — ma'lumot yuklash

━━━━━━━━━━━━━━━━━━━━━━━"""
    kb = {"inline_keyboard": [
        [{"text": "📊 Statistika", "callback_data": "admin:stats"},
         {"text": "📈 Pilot", "callback_data": "admin:pilot"}],
        [{"text": "🔒 Xavfsizlik", "callback_data": "admin:security"},
         {"text": "👥 Users", "callback_data": "admin:users"}],
        [{"text": "📋 Audit", "callback_data": "admin:audit"},
         {"text": "🤝 Hamkorlik", "callback_data": "admin:partnership"}],
        [{"text": "📤 Export", "callback_data": "admin:export"},
         {"text": "🏠 Bosh menyu", "callback_data": "admin:main"}]
    ]}
    return text, kb

def _admin_panel_callback(uid, action, db):
    """Admin panel inline tugmalari."""
    import datetime
    if action == "main":
        return _admin_main_menu()
    elif action == "stats":
        users = db.get("users", {})
        events = db.get("events", [])
        text = f"""📊 <b>STATISTIKA</b>
━━━━━━━━━━━━━━━━━━━━━━━

👥 Jami foydalanuvchilar: {len(users)}
📅 Tadbirlar: {len(events)}
⏰ Vaqt: {datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=5))).strftime('%d.%m.%Y %H:%M')}

━━━━━━━━━━━━━━━━━━━━━━━"""
        kb = {"inline_keyboard": [
            [{"text": "🔙 Orqaga", "callback_data": "admin:main"}]
        ]}
        return text, kb
    elif action == "pilot":
        text = """📈 <b>PILOT NATIJALARI</b>
━━━━━━━━━━━━━━━━━━━━━━━

🏦 Banklar: 10 ta
📊 O'lchov: 6 ta yo'nalish
📋 Kataklar: 60 ta
📌 Loyiha bildirgan dalil: 30 ta (50%)
📚 Loyiha bildirgan ochiq manba: 32 ta
📅 Sana: 29.09.2026

⚠️ Bu qiymatlar loyihaning ichki ma'lumoti; mustaqil tekshiruv dalillari bilan tasdiqlanmagan.

━━━━━━━━━━━━━━━━━━━━━━━"""
        kb = {"inline_keyboard": [
            [{"text": "🔙 Orqaga", "callback_data": "admin:main"}]
        ]}
        return text, kb
    elif action == "security":
        text = """🔒 <b>XAVFSIZLIK — TEKSHIRILGAN HOLAT</b>
━━━━━━━━━━━━━━━━━━━━━━━

🔑 Sayt parollari: alohida salt bilan PBKDF2-HMAC-SHA256
🪪 Sessiya: imzolangan, 12 soatlik; admin API rol bo'yicha tekshiriladi
📋 Hisob o'zgarishlari: audit jurnalida; parol qiymatlari yozilmaydi
🌐 CORS: ruxsat etilgan sayt manzili bilan cheklangan

⚠️ ISO 27001 sertifikati, GDPR bo'yicha huquqiy baholash,
OWASP pentest yoki WCAG auditi mavjudligi tasdiqlanmagan.
Ilova darajasida ma'lumotlar bazasining AES shifrlanishi ham
tekshirilmagan. Bu ro'yxat mustaqil audit o'rnini bosmaydi.

━━━━━━━━━━━━━━━━━━━━━━━"""
        kb = {"inline_keyboard": [
            [{"text": "🔙 Orqaga", "callback_data": "admin:main"}]
        ]}
        return text, kb
    elif action == "users":
        users = db.get("users", {})
        text = f"""👥 <b>FOYDALANUVCHILAR</b>
━━━━━━━━━━━━━━━━━━━━━━━

Jami: {len(users)} ta

Ro'yxat: /royxat
Export: /export

━━━━━━━━━━━━━━━━━━━━━━━"""
        kb = {"inline_keyboard": [
            [{"text": "📋 Ro'yxat", "callback_data": "admin:export"},
             {"text": "🔙 Orqaga", "callback_data": "admin:main"}]
        ]}
        return text, kb
    elif action == "audit":
        accounts = db.get("site_users", {})
        events = db.get("site_audit", [])
        text = f"""📋 <b>HISOBLAR AUDITI</b>
━━━━━━━━━━━━━━━━━━━━━━━

🔑 Sayt hisoblari: {len(accounts)}
🧾 Qayd etilgan amallar: {len(events)}
🔒 Parol qiymatlari auditga kiritilmaydi.

Mustaqil ISO/GDPR/OWASP/WCAG sertifikati yoki auditi
mavjudligi bu bot orqali tasdiqlanmagan.

━━━━━━━━━━━━━━━━━━━━━━━"""
        kb = {"inline_keyboard": [
            [{"text": "🔙 Orqaga", "callback_data": "admin:main"}]
        ]}
        return text, kb
    elif action == "partnership":
        text = """🤝 <b>HAMKORLIK TAKLIFI</b>
━━━━━━━━━━━━━━━━━━━━━━━

PILOT — qamrov va muddat hamkor bilan kelishiladi
MANBALAR — ochiq ma'lumotlar asosida tahlil
HISOBOT — metodika va cheklovlari ko'rsatiladi
STANDARTLAR — talablar o'rganilmoqda; sertifikat tasdiqlanmagan

Aloqa: @aiindeksi_bot

━━━━━━━━━━━━━━━━━━━━━━━"""
        kb = {"inline_keyboard": [
            [{"text": "🔙 Orqaga", "callback_data": "admin:main"}]
        ]}
        return text, kb
    elif action == "export":
        text = """📤 <b>EXPORT</b>
━━━━━━━━━━━━━━━━━━━━━━━

Excel: /export
CSV: /export csv
Ro'yxat: /royxat

━━━━━━━━━━━━━━━━━━━━━━━"""
        kb = {"inline_keyboard": [
            [{"text": "🔙 Orqaga", "callback_data": "admin:main"}]
        ]}
        return text, kb
    else:
        return "Noma'lum buyruq", None
# admin panel v2 - Sun Oct 11 16:08:12 UTC 2026
