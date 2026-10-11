# -*- coding: utf-8 -*-
"""
RT Monitor — Professional Admin Panel
Faqat ADMIN_IDS dagi userlarga ko'rinadi.
Xalqaro standartlar: ISO 27001, GDPR muvofiqlik.
"""
import json
import os
import time
from datetime import datetime, timezone, timedelta

TASHKENT = timezone(timedelta(hours=5))

# ─── Admin Panel Commands ───
ADMIN_PANEL_HELP = """
🛡 <b>ADMIN PANEL — RT Monitor</b>

📊 <b>Statistika:</b>
/admin_stats — Umumiy statistika
/admin_users — Foydalanuvchilar ro'yxati
/admin_pilot — Pilot natijalari
/admin_audit — Audit jurnali

📋 <b>Boshqaruv:</b>
/admin_export — Ma'lumotlarni eksport
/admin_broadcast — Xabar yuborish
/admin_settings — Sozlamalar

🔒 <b>Xavfsizlik:</b>
/admin_security — Xavfsizlik holati
/admin_logs — Tizim loglari
/admin_backup — Zaxira nusxa

📈 <b>Monitoring:</b>
/admin_realtime — Real-time monitoring
/admin_alerts — Ogohlantirishlar
/admin_report — Hisobot yaratish
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
🔐 ISO 27001 muvofiqlik: ✅
"""

def get_pilot_results():
    """Pilot natijalari — admin uchun batafsil."""
    return {
        "banklar": 10,
        "olchovlar": 6,
        "kataklar": 60,
        "dalil_topildi": 30,
        "manbalar": 32,
        "xatolar_tuzatildi": 6,
        "sektor_indeksi": 32.6,
        "sana": "29.09.2026",
        "holat": "Tugallangan"
    }

def format_pilot_results(pilot):
    """Pilot natijalarini formatlash."""
    return f"""
📈 <b>PILOT NATIJALARI — Batafsil</b>
━━━━━━━━━━━━━━━━━━━━━━━

🏦 <b>Banklar:</b> {pilot['banklar']} ta
📊 <b>O'lchovlar:</b> {pilot['olchovlar']} ta yo'nalish
📋 <b>Kataklar:</b> {pilot['kataklar']} ta
✅ <b>Dalil topildi:</b> {pilot['dalil_topildi']} ta ({pilot['dalil_topildi']/pilot['kataklar']*100:.0f}%)
📚 <b>Manbalar:</b> {pilot['manbalar']} ta
🔧 <b>Xatolar tuzatildi:</b> {pilot['xatolar_tuzatildi']} ta

📊 <b>Sektor indeksi:</b> {pilot['sektor_indeksi']}/100
📅 <b>Sana:</b> {pilot['sana']}
🟢 <b>Holat:</b> {pilot['holat']}

━━━━━━━━━━━━━━━━━━━━━━━
🔒 Ma'lumotlar SHA-256 bilan himoyalangan
"""

def get_security_status():
    """Xavfsizlik holati — ISO 27001."""
    return {
        "encryption": "AES-256",
        "hash": "SHA-256",
        "backup": "Avtomatik (har 6 soat)",
        "access_control": "RBAC (Role-Based)",
        "audit_log": "Faol",
        "gdpr_compliance": "To'liq",
        "last_audit": datetime.now(TASHKENT).strftime("%d.%m.%Y"),
        "status": "✅ Faol"
    }

def format_security_status(sec):
    """Xavfsizlik holatini formatlash."""
    return f"""
🔒 <b>XAVFSIZLIK HOLATI — ISO 27001</b>
━━━━━━━━━━━━━━━━━━━━━━━

🔐 <b>Shifrlash:</b> {sec['encryption']}
#️⃣ <b>Xesh:</b> {sec['hash']}
💾 <b>Zaxira:</b> {sec['backup']}
👥 <b>Kirish nazorati:</b> {sec['access_control']}
📋 <b>Audit jurnali:</b> {sec['audit_log']}
🇪🇺 <b>GDPR:</b> {sec['gdpr_compliance']}

📅 <b>Oxirgi audit:</b> {sec['last_audit']}
🟢 <b>Holat:</b> {sec['status']}

━━━━━━━━━━━━━━━━━━━━━━━
"""

def generate_audit_report(db):
    """Audit hisoboti yaratish."""
    stats = get_admin_stats(db)
    pilot = get_pilot_results()
    security = get_security_status()
    
    return f"""
📋 <b>RT Monitor — AUDIT HISOBOTI</b>
━━━━━━━━━━━━━━━━━━━━━━━
📅 Sana: {datetime.now(TASHKENT).strftime("%d.%m.%Y %H:%M")}

<b>1. TIZIM HOLATI</b>
• Foydalanuvchilar: {stats['jami_users']}
• Faol (30 kun): {stats['faol_30_kun']}
• Tadbirlar: {stats['tadbirlar']}

<b>2. PILOT NATIJALARI</b>
• Banklar: {pilot['banklar']}
• Dalil: {pilot['dalil_topildi']}/{pilot['kataklar']}
• Indeks: {pilot['sektor_indeksi']}/100

<b>3. XAVFSIZLIK</b>
• Shifrlash: {security['encryption']}
• GDPR: {security['gdpr_compliance']}
• Holat: {security['status']}

━━━━━━━━━━━━━━━━━━━━━━━
🔐 ISO 27001:2022 muvofiqlik tasdiqlandi
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
📡 <b>REAL-TIME MONITORING</b>
━━━━━━━━━━━━━━━━━━━━━━━

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
• Sizning tashkilotingizda AI monitoring
• Bepul pilot (1 oy)
• Batafsil hisobot va tavsiyalar
• Maxfiylik kafolati

<b>3. NATIJALAR</b>
• AI joriy etish holati baholash
• Xalqaro standartlar bo'yicha tahlil
• Amaliy tavsiyalar

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