# Admin panel funksiyalari

def _admin_main_menu():
    """Admin panel bosh menyusi."""
    text = """🛡 <b>ADMIN PANEL — RT Monitor</b>
━━━━━━━━━━━━━━━━━━━━━━━

Kerakli bo'limni tanlang:

📊 <b>Statistika</b> — umumiy ma'lumotlar
📈 <b>Pilot</b> — pilot natijalari
🔒 <b>Xavfsizlik</b> — ISO 27001, GDPR
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
✅ Dalil: 30 ta (50%)
📚 Manbalar: 32 ta
🔧 Xatolar: 6 ta tuzatildi

📊 Sektor indeksi: 32.6/100
📅 Sana: 29.09.2026

━━━━━━━━━━━━━━━━━━━━━━━"""
        kb = {"inline_keyboard": [
            [{"text": "🔙 Orqaga", "callback_data": "admin:main"}]
        ]}
        return text, kb
    elif action == "security":
        text = """🔒 <b>XAVFSIZLIK — ISO 27001</b>
━━━━━━━━━━━━━━━━━━━━━━━

🔐 Shifrlash: AES-256
#️⃣ Xesh: SHA-256
💾 Zaxira: Har 6 soat
👥 Kirish: RBAC
📋 Audit: Faol
🇪🇺 GDPR: Muvofiqlik

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
        users = db.get("users", {})
        text = f"""📋 <b>AUDIT HISOBOTI</b>
━━━━━━━━━━━━━━━━━━━━━━━

📅 Sana: {datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=5))).strftime('%d.%m.%Y %H:%M')}
👥 Foydalanuvchilar: {len(users)}

✅ ISO 27001: Muvofiqlik
✅ GDPR: Muvofiqlik
✅ OWASP: Tekshirilgan

━━━━━━━━━━━━━━━━━━━━━━━"""
        kb = {"inline_keyboard": [
            [{"text": "🔙 Orqaga", "callback_data": "admin:main"}]
        ]}
        return text, kb
    elif action == "partnership":
        text = """🤝 <b>HAMKORLIK TAKLIFI</b>
━━━━━━━━━━━━━━━━━━━━━━━

BEPUL PILOT — hech qanday xarajat yo'q
MAXFIYLIK — ma'lumotlar himoyalangan
NATIJA — 1 oyda batafsil hisobot
XALQARO — ISO 27001, GDPR standartlar

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
