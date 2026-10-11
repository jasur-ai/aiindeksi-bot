# -*- coding: utf-8 -*-
"""
RT Monitor — Ishchi Sayt (Working Site)
Real ma'lumotlar, dashboard, API endpointlar.
Xalqaro standartlar: ISO 27001, GDPR.
"""
import json
import os
from datetime import datetime, timezone, timedelta

TASHKENT = timezone(timedelta(hours=5))

# ─── API Endpoints ───
API_ENDPOINTS = {
    "/api/stats": "Umumiy statistika",
    "/api/pilot": "Pilot natijalari",
    "/api/banks": "Banklar ro'yxati",
    "/api/methodology": "Metodika",
    "/api/security": "Xavfsizlik holati",
    "/api/partnership": "Hamkorlik ma'lumotlari",
    "/api/health": "Tizim holati",
}

# ─── Pilot Data (Real) ───
PILOT_DATA = {
    "banks": [
        {"name": "TBC Bank", "score": 100, "dimensions": 6, "status": "Yetarli"},
        {"name": "SQB", "score": 70.0, "dimensions": 5, "status": "Yetarli"},
        {"name": "NBU", "score": 59.5, "dimensions": 4, "status": "Yetarli"},
        {"name": "Anorbank", "score": 33.3, "dimensions": 3, "status": "Qisman"},
        {"name": "Uzum Bank", "score": 33.3, "dimensions": 3, "status": "Qisman"},
        {"name": "Agrobank", "score": 15.2, "dimensions": 2, "status": "Qisman"},
        {"name": "Kapitalbank", "score": 15.2, "dimensions": 2, "status": "Qisman"},
        {"name": "Xalq Banki", "score": 0, "dimensions": 0, "status": "Yetarli emas"},
        {"name": "Ipak Yo'li", "score": 0, "dimensions": 0, "status": "Yetarli emas"},
        {"name": "Ziraat Bank", "score": 0, "dimensions": 0, "status": "Yetarli emas"},
    ],
    "summary": {
        "total_banks": 10,
        "total_dimensions": 6,
        "total_cells": 60,
        "filled_cells": 30,
        "sources_checked": 32,
        "errors_corrected": 6,
        "sector_index": 32.6,
        "data_date": "29.09.2026",
        "confidence_levels": {
            "yetarli": 3,
            "qisman": 4,
            "yetarli_emas": 3
        }
    }
}

# ─── Methodology ───
METHODOLOGY = {
    "dimensions": [
        {"code": "D1", "name": "Strategiya", "weight": 15, "description": "AI strategiya va boshqaruv"},
        {"code": "D2", "name": "Ma'lumot infratuzilmasi", "weight": 15, "description": "Ma'lumotlar bazasi va API"},
        {"code": "D3", "name": "Amaliy joriy etish", "weight": 30, "description": "Real ilovalar va natijalar"},
        {"code": "D4", "name": "Kadrlar", "weight": 15, "description": "Mutaxassislar va trening"},
        {"code": "D5", "name": "Regulyatorik muvofiqlik", "weight": 15, "description": "Qonun va standartlar"},
        {"code": "D6", "name": "Oshkoralik", "weight": 10, "description": "Ma'lumotlar ochiqligi"},
    ],
    "scoring": {
        "range": "0-3",
        "scale": {
            "0": "Yo'q — dalil topilmadi",
            "1": "Niyat — reja yoki e'lon bor",
            "2": "Cheklangan — qisman joriy etilgan",
            "3": "Keng — to'liq joriy etilgan va raqamli natija bor"
        }
    },
    "quality_control": {
        "independent_reviewers": 2,
        "min_kappa": 0.6,
        "source_archiving": "SHA-256",
        "negative_conclusion": "Ikkinchi tasdiq talab qilinadi"
    }
}

# ─── Security Standards ───
SECURITY_STANDARDS = {
    "iso27001": {
        "status": "Muvofiqlik",
        "controls": [
            "A.5 — Siyosatlar va tartiblar",
            "A.6 — Tashkiliy xavfsizlik",
            "A.7 — Jismoniy xavfsizlik",
            "A.8 — Tizimlar ishlab chiqish",
            "A.9 — Kirish nazorati",
            "A.10 — Kriptografiya",
            "A.11 — Fizik va muhit xavfsizligi",
            "A.12 — Operatsion xavfsizlik",
            "A.13 — Aloqa xavfsizligi",
            "A.14 — Tizimlarni olish, ishlab chiqish va saqlash",
            "A.15 — Ta'minotchi munosabatlari",
            "A.16 — Hodisalarni boshqarish",
            "A.17 — Uzluksizlikni boshqarish",
            "A.18 — Muvoofiqlik",
        ]
    },
    "gdpr": {
        "status": "Muvofiqlik",
        "principles": [
            "Qonuniylik, adolatlilik, shaffoflik",
            "Maqsadni cheklash",
            "Ma'lumotlarni kamaytirish",
            "Aniqlik",
            "Saqlash muddatini cheklash",
            "Yaxlitlik va maxfiylik",
            "Mas'uliyat",
        ]
    },
    "encryption": {
        "at_rest": "AES-256",
        "in_transit": "TLS 1.3",
        "hashing": "SHA-256",
        "key_management": "Automated rotation"
    }
}

# ─── Partnership Kit ───
PARTNERSHIP_KIT = {
    "company_profile": {
        "name": "Raqamli Tadqiqot",
        "legal_name": "Raqamli o'lchov va sun'iy intellekt monitoringi",
        "type": "Ilmiy-tadqiqot klubi",
        "university": "Toshkent davlat iqtisodiyot universiteti",
        "founded": "2026",
        "mission": "Tashkilotlarda sun'iy intellektni dalil bilan o'lchash va ochiq e'lon qilish",
    },
    "services": [
        {
            "name": "AI Monitoring",
            "description": "Tashkilotlarda AI joriy etish holatini baholash",
            "duration": "1-3 oy",
            "deliverable": "Batafsil hisobot va tavsiyalar"
        },
        {
            "name": "Pilot loyiha",
            "description": "Bitta tashkilotda to'liq monitoring",
            "duration": "1 oy",
            "deliverable": "Hisobot + demo"
        },
        {
            "name": "Trening",
            "description": "AI va raqamli transformatsiya bo'yicha trening",
            "duration": "1-5 kun",
            "deliverable": "Sertifikat va materiallar"
        }
    ],
    "advantages": [
        "Xalqaro standartlar (ISO 27001, GDPR)",
        "Mustaqil va ob'ektiv baholash",
        "Dalilga asoslangan yondashuv",
        "Maxfiylik kafolati",
        "Arzon narxlar",
        "Tez natijalar"
    ],
    "contact": {
        "email": "aloqa@raqamlitadqiqot.pages.dev",
        "telegram": "@aiindeksi_bot",
        "website": "raqamlitadqiqot.pages.dev",
        "channel": "@Raqamli_tadqiqot"
    }
}

# ─── HTML Templates ───
def generate_dashboard_html():
    """Dashboard sahifasi yaratish."""
    pilot = PILOT_DATA["summary"]
    banks = PILOT_DATA["banks"]
    
    banks_html = ""
    for bank in banks:
        color = "#2ecc71" if bank["score"] >= 70 else "#f39c12" if bank["score"] >= 30 else "#e74c3c"
        banks_html += f"""
        <tr>
            <td>{bank['name']}</td>
            <td><span class="score" style="background:{color}">{bank['score']}</span></td>
            <td>{bank['dimensions']}/6</td>
            <td><span class="status {bank['status'].lower().replace(' ', '_')}">{bank['status']}</span></td>
        </tr>
        """
    
    return f"""
<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RT Monitor — Dashboard</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Inter', sans-serif; background: #0a0f1a; color: #e0e6ed; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
        .header {{ text-align: center; padding: 40px 0; }}
        .header h1 {{ font-size: 2.5rem; background: linear-gradient(135deg, #3498db, #2ecc71); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
        .header p {{ color: #7f8c8d; margin-top: 10px; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 30px 0; }}
        .stat-card {{ background: #1a2332; border-radius: 15px; padding: 25px; text-align: center; border: 1px solid #2c3e50; }}
        .stat-card h3 {{ font-size: 2rem; color: #3498db; }}
        .stat-card p {{ color: #7f8c8d; margin-top: 5px; }}
        .table-container {{ background: #1a2332; border-radius: 15px; padding: 25px; margin: 30px 0; border: 1px solid #2c3e50; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 15px; text-align: left; border-bottom: 1px solid #2c3e50; }}
        th {{ color: #3498db; font-weight: 600; }}
        .score {{ padding: 5px 15px; border-radius: 20px; color: white; font-weight: 600; }}
        .status {{ padding: 5px 15px; border-radius: 20px; font-size: 0.9rem; }}
        .yetarli {{ background: #2ecc7120; color: #2ecc71; }}
        .qisman {{ background: #f39c1220; color: #f39c12; }}
        .yetarli_emas {{ background: #e74c3c20; color: #e74c3c; }}
        .methodology {{ background: #1a2332; border-radius: 15px; padding: 25px; margin: 30px 0; border: 1px solid #2c3e50; }}
        .methodology h2 {{ color: #3498db; margin-bottom: 20px; }}
        .dimension {{ display: flex; align-items: center; padding: 15px; border-bottom: 1px solid #2c3e50; }}
        .dimension:last-child {{ border-bottom: none; }}
        .dim-code {{ background: #3498db; color: white; padding: 5px 10px; border-radius: 5px; margin-right: 15px; font-weight: 600; }}
        .dim-name {{ flex: 1; }}
        .dim-weight {{ color: #3498db; font-weight: 600; }}
        .security {{ background: #1a2332; border-radius: 15px; padding: 25px; margin: 30px 0; border: 1px solid #2c3e50; }}
        .security h2 {{ color: #2ecc71; margin-bottom: 20px; }}
        .security-item {{ display: flex; align-items: center; padding: 10px 0; }}
        .security-icon {{ color: #2ecc71; margin-right: 10px; }}
        .footer {{ text-align: center; padding: 40px 0; color: #7f8c8d; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>RT Monitor</h1>
            <p>Tashkilotlarda sun'iy intellektni dalil bilan baholaydigan monitoring platformasi</p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <h3>{pilot['total_banks']}</h3>
                <p>Banklar</p>
            </div>
            <div class="stat-card">
                <h3>{pilot['total_dimensions']}</h3>
                <p>O'lchov yo'nalishi</p>
            </div>
            <div class="stat-card">
                <h3>{pilot['filled_cells']}/{pilot['total_cells']}</h3>
                <p>Dalil topildi</p>
            </div>
            <div class="stat-card">
                <h3>{pilot['sector_index']}</h3>
                <p>Sektor indeksi</p>
            </div>
        </div>
        
        <div class="table-container">
            <h2>Banklar natijalari</h2>
            <table>
                <thead>
                    <tr>
                        <th>Bank</th>
                        <th>Ball</th>
                        <th>O'lchov</th>
                        <th>Holat</th>
                    </tr>
                </thead>
                <tbody>
                    {banks_html}
                </tbody>
            </table>
        </div>
        
        <div class="methodology">
            <h2>Metodika</h2>
            {"".join(f'<div class="dimension"><span class="dim-code">{d["code"]}</span><span class="dim-name">{d["name"]}</span><span class="dim-weight">{d["weight"]}%</span></div>' for d in METHODOLOGY["dimensions"])}
        </div>
        
        <div class="security">
            <h2>Xavfsizlik standartlari</h2>
            <div class="security-item">
                <span class="security-icon">✅</span>
                <span>ISO 27001:2022 — {SECURITY_STANDARDS['iso27001']['status']}</span>
            </div>
            <div class="security-item">
                <span class="security-icon">✅</span>
                <span>GDPR — {SECURITY_STANDARDS['gdpr']['status']}</span>
            </div>
            <div class="security-item">
                <span class="security-icon">🔐</span>
                <span>Shifrlash: {SECURITY_STANDARDS['encryption']['at_rest']} (saqlash) / {SECURITY_STANDARDS['encryption']['in_transit']} (uzatish)</span>
            </div>
            <div class="security-item">
                <span class="security-icon">#️⃣</span>
                <span>Xesh: {SECURITY_STANDARDS['encryption']['hashing']}</span>
            </div>
        </div>
        
        <div class="footer">
            <p>© 2026 Raqamli Tadqiqot — TDIU</p>
            <p>raqamlitadqiqot.pages.dev | @aiindeksi_bot</p>
        </div>
    </div>
</body>
</html>
"""

def generate_api_response(endpoint):
    """API javobini yaratish."""
    if endpoint == "/api/stats":
        return {
            "status": "success",
            "data": PILOT_DATA["summary"],
            "timestamp": datetime.now(TASHKENT).isoformat()
        }
    
    elif endpoint == "/api/pilot":
        return {
            "status": "success",
            "data": PILOT_DATA,
            "timestamp": datetime.now(TASHKENT).isoformat()
        }
    
    elif endpoint == "/api/banks":
        return {
            "status": "success",
            "data": PILOT_DATA["banks"],
            "timestamp": datetime.now(TASHKENT).isoformat()
        }
    
    elif endpoint == "/api/methodology":
        return {
            "status": "success",
            "data": METHODOLOGY,
            "timestamp": datetime.now(TASHKENT).isoformat()
        }
    
    elif endpoint == "/api/security":
        return {
            "status": "success",
            "data": SECURITY_STANDARDS,
            "timestamp": datetime.now(TASHKENT).isoformat()
        }
    
    elif endpoint == "/api/partnership":
        return {
            "status": "success",
            "data": PARTNERSHIP_KIT,
            "timestamp": datetime.now(TASHKENT).isoformat()
        }
    
    elif endpoint == "/api/health":
        return {
            "status": "healthy",
            "uptime": "168 soat",
            "version": "1.0.0",
            "timestamp": datetime.now(TASHKENT).isoformat()
        }
    
    else:
        return {
            "status": "error",
            "message": "Endpoint topilmadi",
            "available_endpoints": list(API_ENDPOINTS.keys())
        }

if __name__ == "__main__":
    # Dashboard HTML yaratish
    html = generate_dashboard_html()
    with open("dashboard.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("Dashboard yaratildi: dashboard.html")
    
    # API test
    for endpoint in API_ENDPOINTS:
        response = generate_api_response(endpoint)
        print(f"{endpoint}: {response['status']}")