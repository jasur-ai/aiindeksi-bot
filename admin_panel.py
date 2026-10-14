# -*- coding: utf-8 -*-
"""
RT Monitor — legacy admin-panel moduli
Faqat vakolatli admin uchun mo'ljallangan; bu fayl jonli tizim holatini isbotlamaydi.
ISO/GDPR/WCAG/OWASP bo'yicha sertifikat yoki audit tasdiqlanmagan.
"""
import json
import os
import time
from datetime import datetime, timezone, timedelta

TASHKENT = timezone(timedelta(hours=5))

# ─── Admin Panel Commands ───
ADMIN_PANEL_HELP = """
⚠️ <b>Legacy admin-panel moduli</b>

Ushbu modul joriy bot routeriga ulanmagan va undagi buyruqlar ishlab turgan deb hisoblanmasin.
Standartlar yoki production monitoring holatini tasdiqlamaydi.

Sayt hisoblarini boshqarish uchun vakolatli adminning shaxsiy chatida:
/loginlar · /qosh login parol · /sayt_admin login parol · /parol login yangi_parol · /ochir login · /sayt_audit
"""

def get_admin_stats(db):
    """Umumiy statistika — admin uchun."""
    users = db.get("users", {})
    events = db.get("events", [])
    
    now = datetime.now(TASHKENT)
    
    # Faol foydalanuvchilar (so'nggi 30 kun)
    active_30 = sum(1 for u in users.values() 
                   if u.get("vaqt") and 
                   (now - datetime.fromisoformat(u["vaqt"])).days <= 30)
    
    # Bugungi ro'yxatdan o'tganlar
    today_users = sum(1 for u in users.values()
                     if u.get("sana") and u["sana"] == now.strftime("%d.%m.%Y"))
    
    return {
        "jami_users": len(users),
        "faol_30_kun": active_30,
        "bugun": today_users,
        "tadbirlar": len(events),
        "vaqt": now.strftime("%d.%m.%Y %H:%M")
    }

def format_admin_stats(stats):
    """Statistikani chiroyli formatlash."""
    return f"""
📊 <b>RT Monitor — Admin Statistika</b>
━━━━━━━━━━━━━━━━━━━━━━━

👥 <b>Foydalanuvchilar:</b>
   • Jami: {stats['jami_users']}
   • Faol (30 kun): {stats['faol_30_kun']}
   • Bugun: {stats['bugun']}

📅 <b>Tadbirlar:</b>
   • Jami: {stats['tadbirlar']}

⏰ <b>Vaqt:</b> {stats['vaqt']}

━━━━━━━━━━━━━━━━━━━━━━━
⚠️ Ushbu modul mustaqil xavfsizlik auditi yoki sertifikat xulosasi emas.
"""

def get_pilot_results():
    """Pilot natijalari — admin uchun batafsil."""
    return {
        "banklar": 10,
        "olchovlar": 6,
        "kataklar": 60,
        "dalil_topildi": 30,
        "manbalar": 32,
        "xatolar_tuzatildi": None,
        "sektor_indeksi": "Manba bilan tasdiqlanmagan",
        "sana": "29.09.2026",
        "holat": "Loyiha ichki hisoboti; mustaqil tasdiqlanmagan"
    }

def format_pilot_results(pilot):
    """Loyiha ichki ko'rsatkichlarini tasdiqlanmagan deb aniq belgilab chiqarish."""
    return f"""
📈 <b>PILOT — LOYIHA BILDIRGAN QIYMATLAR</b>
━━━━━━━━━━━━━━━━━━━━━━━

🏦 <b>Namuna:</b> {pilot['banklar']} bank
📊 <b>O'lchovlar:</b> {pilot['olchovlar']} yo'nalish
📋 <b>Kataklar:</b> {pilot['kataklar']}
📌 <b>Loyiha bildirgan dalil:</b> {pilot['dalil_topildi']}/{pilot['kataklar']}
📚 <b>Loyiha bildirgan manba:</b> {pilot['manbalar']}
📅 <b>Hisobot sanasi:</b> {pilot['sana']}

⚠️ <b>Holat:</b> {pilot['holat']}
Sektor indeksi va banklar kesimidagi reyting mustaqil manba-arxiv bilan tasdiqlanmagan.

━━━━━━━━━━━━━━━━━━━━━━━
"""

def get_security_status():
    """Kod darajasidagi ko'rinadigan choralar; mustaqil audit holati emas."""
    return {
        "password_hashing": "PBKDF2-HMAC-SHA256, salt bilan (sayt hisoblari)",
        "session": "HMAC imzoli, 12 soatgacha",
        "access_control": "Himoyalangan admin API da rol tekshiruvi",
        "audit_log": "Sayt hisoblariga oid amallar qayd etiladi; parollar yozilmaydi",
        "at_rest": "Ilova darajasida shifrlash tasdiqlanmagan",
        "certifications": "ISO 27001/GDPR/OWASP/WCAG sertifikat yoki audit tasdiqlanmagan",
        "status": "Mustaqil tekshiruv talab etiladi"
    }

def format_security_status(sec):
    """Tekshirilgan kod xususiyatlari va noma'lum jihatlarni ajratish."""
    return f"""
🔒 <b>XAVFSIZLIK — KODDA KO'RINGAN CHORALAR</b>
━━━━━━━━━━━━━━━━━━━━━━━

🔑 <b>Sayt parollari:</b> {sec['password_hashing']}
🪪 <b>Sessiya:</b> {sec['session']}
👥 <b>Ruxsat:</b> {sec['access_control']}
📋 <b>Hisob auditi:</b> {sec['audit_log']}
💾 <b>Ma'lumotlar bazasini shifrlash:</b> {sec['at_rest']}

⚠️ <b>Tasdiqlanmagan:</b> {sec['certifications']}
Holat: {sec['status']}. Bu ma'lumot mustaqil audit xulosasi emas.

━━━━━━━━━━━━━━━━━━━━━━━
"""

def generate_audit_report(db):
    """Faqat mavjud hisob/audit sonlarini chiqaradi; sertifikat xulosasi bermaydi."""
    stats = get_admin_stats(db)
    events = db.get("site_audit", [])
    return f"""
📋 <b>RT Monitor — ICHKI HISOBOT</b>
━━━━━━━━━━━━━━━━━━━━━━━
📅 Sana: {datetime.now(TASHKENT).strftime("%d.%m.%Y %H:%M")}

👥 Bot foydalanuvchilari: {stats['jami_users']}
🔑 Sayt hisoblari: {len(db.get('site_users', {}))}
🧾 Hisob audit yozuvlari: {len(events)}

⚠️ ISO 27001, GDPR, OWASP yoki WCAG muvofiqligi tasdiqlanmagan.
Mustaqil audit va sertifikat mavjudligi ushbu hisobot bilan isbotlanmaydi.

━━━━━━━━━━━━━━━━━━━━━━━
"""

# ─── Real-time Monitoring ───
class RealTimeMonitor:
    """Real-time tizim monitoringi."""
    
    def __init__(self):
        self.metrics = {
            "cpu": 0,
            "memory": 0,
            "requests": 0,
            "errors": 0,
            "uptime": 0
        }
        self.alerts = []
    
    def update(self, metric, value):
        """Metrikani yangilash."""
        self.metrics[metric] = value
        self.check_alerts()
    
    def check_alerts(self):
        """Ogohlantirishlarni tekshirish."""
        if self.metrics["cpu"] > 80:
            self.alerts.append({
                "type": "warning",
                "message": f"CPU yuki: {self.metrics['cpu']}%",
                "time": datetime.now(TASHKENT).strftime("%H:%M")
            })
        if self.metrics["memory"] > 90:
            self.alerts.append({
                "type": "critical",
                "message": f"Xotira: {self.metrics['memory']}%",
                "time": datetime.now(TASHKENT).strftime("%H:%M")
            })
    
    def get_status(self):
        """Monitoring holatini qaytaradi."""
        return {
            "metrics": self.metrics,
            "alerts": self.alerts[-10:],  # Oxirgi 10 ta
            "status": "normal" if not self.alerts else "warning"
        }

def format_realtime_status(monitor):
    """Real-time holatni formatlash."""
    status = monitor.get_status()
    metrics = status["metrics"]
    
    alerts_text = ""
    if status["alerts"]:
        alerts_text = "\n⚠️ <b>Ogohlantirishlar:</b>\n"
        for alert in status["alerts"][-5:]:
            alerts_text += f"  • {alert['time']}: {alert['message']}\n"
    
    return f"""
📡 <b>DEMO MONITORING KO'RSATKICHLARI</b>
━━━━━━━━━━━━━━━━━━━━━━━

⚠️ Bu moduldagi qiymatlar production telemetry emas; namuna/sinov ma'lumoti bo'lishi mumkin.

💻 <b>Tizim:</b>
  • CPU: {metrics['cpu']}%
  • Xotira: {metrics['memory']}%
  • So'rovlar: {metrics['requests']}
  • Xatolar: {metrics['errors']}
  • Uptime: {metrics['uptime']} soat

🟢 <b>Holat:</b> {status['status'].upper()}
{alerts_text}
━━━━━━━━━━━━━━━━━━━━━━━
"""

# ─── Partnership Kit ───
PARTNERSHIP_TEMPLATE = """
🤝 <b>HAMKORLIK TAKLIFI — RT Monitor</b>
━━━━━━━━━━━━━━━━━━━━━━━

<b>Tashkilot:</b> ____________________
<b>Manzil:</b> ____________________
<b>Aloqa:</b> ____________________

<b>1. LOYIHA HAQIDA</b>
RT Monitor — tashkilotlarda sun'iy intellekt va raqamli 
xizmatlarni dalil bilan baholaydigan monitoring platformasi.

<b>2. TAKLIF</b>
• Tashkilot bilan kelishilgan qamrovda AI bo'yicha ochiq manbalarni tahlil qilish
• Pilot narxi, muddati va hisobot tarkibi oldindan kelishiladi
• Amaliy tavsiyalar — ma'lumotlar yetarli bo'lsa
• Ma'lumotlarni qayta ishlash shartlari yozma ravishda kelishiladi

<b>3. NATIJALAR</b>
• Ochiq dalillarni kelishilgan mezonlar asosida ko'rib chiqish
• Standartlar haqida ma'lumot berish mumkin; muvofiqlik/sertifikat tasdiqlanmaydi
• Xulosalar va cheklovlar aniq ajratiladi

<b>4. KEYINGI QADAMLAR</b>
1. Niyat xati imzolash
2. Pilot boshlash (1 oy)
3. Hisobot taqdim etish
4. Hamkorlik davomi

━━━━━━━━━━━━━━━━━━━━━━━
📧 aloqa@raqamlitadqiqot.pages.dev
🌐 raqamlitadqiqot.pages.dev
"""

def get_partnership_kit():
    """Hamkorlik to'plami."""
    return PARTNERSHIP_TEMPLATE

# ─── Main Admin Handler ───
def handle_admin_command(command, db, chat_id):
    """Admin buyruqlarini boshqarish."""
    
    if command == "/admin_stats":
        stats = get_admin_stats(db)
        return format_admin_stats(stats)
    
    elif command == "/admin_pilot":
        pilot = get_pilot_results()
        return format_pilot_results(pilot)
    
    elif command == "/admin_security":
        security = get_security_status()
        return format_security_status(security)
    
    elif command == "/admin_audit":
        return generate_audit_report(db)
    
    elif command == "/admin_partnership":
        return get_partnership_kit()
    
    elif command == "/admin_panel":
        return ADMIN_PANEL_HELP
    
    else:
        return "❌ Noma'lum buyruq. /admin_panel — yordam"

if __name__ == "__main__":
    # Test
    print("Admin Panel moduli yuklandi ✅")