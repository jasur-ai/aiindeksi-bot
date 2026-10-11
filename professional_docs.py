# -*- coding: utf-8 -*-
"""
RT Monitor — Professional Documentation
Xalqaro standartlar va hamkorlik hujjatlari.
"""
import json
from datetime import datetime, timezone, timedelta

TASHKENT = timezone(timedelta(hours=5))

# ─── Company Profile ───
COMPANY_PROFILE = {
    "name": "Raqamli Tadqiqot",
    "legal_name": "Raqamli o'lchov va sun'iy intellekt monitoringi",
    "brand": "RT Monitor",
    "type": "Ilmiy-tadqiqot klubi",
    "university": "Toshkent davlat iqtisodiyot universiteti (TDIU)",
    "founded": "2026",
    "founder": "Abduvayitov Jasurjon",
    "academic_advisor": "Salimova Husniya (AT kafedrasi)",
    "mission": "Tashkilotlarda sun'iy intellektni dalil bilan o'lchash va ochiq e'lon qilish",
    "vision": "O'zbekistonda AI monitoring bo'yicha yetakchi mustaqil tashkilot bo'lish",
    "values": [
        "Oshkoralik — barcha natijalar ochiq",
        "Dalil — har ball manbaga bog'langan",
        "Mustaqillik — hech qanday tashkilot ta'sirida emas",
        "Sifat — xalqaro standartlar",
        "Hamkorlik — korxonalar bilan birga"
    ]
}

# ─── Services ───
SERVICES = [
    {
        "id": "ai_monitoring",
        "name": "AI Monitoring",
        "description": "Tashkilotlarda AI joriy etish holatini xalqaro standartlar bo'yicha baholash",
        "duration": "1-3 oy",
        "deliverables": [
            "Batafsil hisobot (PDF + interaktiv dashboard)",
            "Tavsiyalar va yo'l xaritasi",
            "Benchmark — xalqaro tashkilotlar bilan taqqoslash"
        ],
        "price": "Kelishilgan",
        "target": "Banklar, sug'urta, davlat tashkilotlari"
    },
    {
        "id": "pilot_project",
        "name": "Pilot loyiha",
        "description": "Bitta tashkilotda 1 oylik to'liq monitoring",
        "duration": "1 oy",
        "deliverables": [
            "Hisobot + demo",
            "AI joriy etish bo'yicha tavsiyalar",
            "Keyingi qadamlar rejasi"
        ],
        "price": "Bepul (birinchi tashkilot uchun)",
        "target": "Yangi hamkorlar"
    },
    {
        "id": "training",
        "name": "Trening va seminar",
        "description": "AI va raqamli transformatsiya bo'yicha trening",
        "duration": "1-5 kun",
        "deliverables": [
            "Sertifikat",
            "O'quv materiallari",
            "Amaliy mashg'ulotlar"
        ],
        "price": "Kelishilgan",
        "target": "Korxona xodimlari"
    },
    {
        "id": "consultation",
        "name": "Konsultatsiya",
        "description": "AI strategiya va joriy etish bo'yicha maslahat",
        "duration": "1-2 hafta",
        "deliverables": [
            "Strategiya hujjati",
            "Yo'l xaritasi",
            "Budget hisob-kitobi"
        ],
        "price": "Kelishilgan",
        "target": "Rahbarlar"
    }
]

# ─── Partnership Proposal ───
PARTNERSHIP_PROPOSAL = """
═══════════════════════════════════════════════════════════════
                    HAMKORLIK TAKLIFI
                         RT Monitor
═══════════════════════════════════════════════════════════════

Tashkilot: {company_name}
Sana: {date}

═══════════════════════════════════════════════════════════════
1. BIZ KIMMIZ?
═══════════════════════════════════════════════════════════════

Raqamli Tadqiqot — TDIU talabalarining ilmiy-tadqiqot klubi.
Biz tashkilotlarda sun'iy intellektni dalil bilan o'lchaymiz.

✅ 10 ta bankda pilot o'tkazildi
✅ 60 ta savoldan 30 tasiga dalil topildi
✅ Xalqaro standartlar (ISO 27001, GDPR)
✅ Mustaqil va ob'ektiv baholash

═══════════════════════════════════════════════════════════════
2. NIMA TAKLIF QILAMIZ?
═══════════════════════════════════════════════════════════════

🎯 BIRINCHI QADAM: BEPUL PILOT (1 OY)

Sizning tashkilotingizda:
• AI joriy etish holati baholash
• 6 ta yo'nalish bo'yicha tahlil
• Batafsil hisobot va tavsiyalar
• Maxfiylik kafolati

📊 NATIJALAR:
• AI qayerda ishlayotganini bilasiz
• Qayerda kamchilik borligini ko'rasiz
• Qanday yaxshilash mumkinligini o'rganasiz
• Xalqaro standartlar bo'yicha holatni bilasiz

═══════════════════════════════════════════════════════════════
3. NIMA UCHUN BIZNI TANLASHINGIZ KERAK?
═══════════════════════════════════════════════════════════════

✅ MUSTAQIL — hech qanday tashkilot ta'sirida emasmiz
✅ DALIL — har ball manbaga bog'langan, SHA-256 bilan arxivlangan
✅ XALQARO — ISO 27001, GDPR muvofiqlik
✅ ARZON — birinchi pilot bepul
✅ TEZ — 1 oyda natija
✅ MAXFIY — ma'lumotlar himoyalangan

═══════════════════════════════════════════════════════════════
4. KEYINGI QADAMLAR
═══════════════════════════════════════════════════════════════

1️⃣ Niyat xati imzolash (1 kun)
2️⃣ Ma'lumotlar yig'ish (2 hafta)
3️⃣ Tahlil va baholash (1 hafta)
4️⃣ Hisobot taqdim etish (1 hafta)
5️⃣ Tavsiyalar va yo'l xaritasi

JAMI: 1 OY

═══════════════════════════════════════════════════════════════
5. ALOQA
═══════════════════════════════════════════════════════════════

📧 Email: aloqa@raqamlitadqiqot.pages.dev
🤖 Telegram: @aiindeksi_bot
🌐 Veb-sayt: raqamlitadqiqot.pages.dev
📣 Kanal: @Raqamli_tadqiqot

═══════════════════════════════════════════════════════════════
                     RAD ETIB BO'LMAYDIGAN TAKLIF
═══════════════════════════════════════════════════════════════

BEPUL pilot — hech qanday xarajat yo'q
MAXFIYLIK — ma'lumotlar himoyalangan
NATIJA — 1 oyda batafsil hisobot
XALQARO — ISO 27001, GDPR standartlar

Siz faqat vaqt ajrating — qolgan hamma narsa bizdan.

═══════════════════════════════════════════════════════════════
"""

# ─── Letter of Intent Template ───
LETTER_OF_INTENT = """
═══════════════════════════════════════════════════════════════
                     NIYAT XATI
═══════════════════════════════════════════════════════════════

Sana: {date}

Kimga: Raqamli Tadqiqot jamoasi
Kimdan: {company_name}
Mavzu: AI monitoring bo'yicha hamkorlik

═══════════════════════════════════════════════════════════════

Hurmatli Raqamli Tadqiqot jamoasi,

Biz, {company_name}, sizlarning AI monitoring xizmatingizga 
qiziqish bildiramiz va quyidagilarni ma'lum qilamiz:

1. Biz sizlarning bepul pilot dasturingizda ishtirok etishga tayyormiz.

2. Biz quyidagi ma'lumotlarni taqdim etishga rozimiz:
   • Tashkilot nomi va tavsifi
   • AI joriy etish holati haqida umumiy ma'lumot
   • Kerakli hujjatlar (maxfiylik doirasida)

3. Biz quyidagilarni kafolatlaymiz:
   • Ma'lumotlar maxfiyligi
   • Hamkorlik uchun mas'ul shaxs tayinlash
   • Kerakli vaqt va resurslar ajratish

4. Natijalar va tavsiyalar faqat bizning roziligimiz bilan 
   e'lon qilinadi.

═══════════════════════════════════════════════════════════════

Imzo: ____________________
Ism: ____________________
Lavozim: ____________________
Sana: ____________________

M.O'.: ____________________

═══════════════════════════════════════════════════════════════
"""

# ─── ROI Calculator ───
def calculate_roi(bank_count, avg_transactions, cost_per_transaction):
    """ROI hisoblash — AI monitoring natijalari."""
    
    # AI chatbot narxi (AQSh banki misoli)
    ai_cost = 0.03  # $0.03 per transaction
    human_cost = cost_per_transaction  # $0.35 per transaction (o'rtacha)
    
    # Tejamkorlik
    savings_per_transaction = human_cost - ai_cost
    daily_savings = bank_count * avg_transactions * savings_per_transaction
    monthly_savings = daily_savings * 30
    yearly_savings = monthly_savings * 12
    
    # ROI
    implementation_cost = 50000  # $50,000 (taxminiy)
    roi_percentage = ((yearly_savings - implementation_cost) / implementation_cost) * 100
    
    return {
        "savings_per_transaction": savings_per_transaction,
        "daily_savings": daily_savings,
        "monthly_savings": monthly_savings,
        "yearly_savings": yearly_savings,
        "implementation_cost": implementation_cost,
        "roi_percentage": roi_percentage,
        "payback_months": implementation_cost / monthly_savings
    }

def format_roi_report(roi_data):
    """ROI hisobotini formatlash."""
    return f"""
💰 <b>ROI HISOB-KITOBI — AI MONITORING</b>
━━━━━━━━━━━━━━━━━━━━━━━

📊 <b>Tejamkorlik:</b>
• Har bir tranzaksiya: ${roi_data['savings_per_transaction']:.2f}
• Kunlik: ${roi_data['daily_savings']:,.0f}
• Oylik: ${roi_data['monthly_savings']:,.0f}
• Yillik: ${roi_data['yearly_savings']:,.0f}

💵 <b>Investitsiya:</b>
• Joriy etish: ${roi_data['implementation_cost']:,.0f}
• ROI: {roi_data['roi_percentage']:.0f}%
• Qaytish muddati: {roi_data['payback_months']:.1f} oy

━━━━━━━━━━━━━━━━━━━━━━━
"""

# ─── Main Functions ───
def get_company_profile():
    return COMPANY_PROFILE

def get_services():
    return SERVICES

def get_partnership_proposal(company_name):
    return PARTNERSHIP_PROPOSAL.format(
        company_name=company_name,
        date=datetime.now(TASHKENT).strftime("%d.%m.%Y")
    )

def get_letter_of_intent(company_name):
    return LETTER_OF_INTENT.format(
        company_name=company_name,
        date=datetime.now(TASHKENT).strftime("%d.%m.%Y")
    )

def get_roi_report(bank_count=10, avg_transactions=1000, cost_per_transaction=0.35):
    roi = calculate_roi(bank_count, avg_transactions, cost_per_transaction)
    return format_roi_report(roi)

if __name__ == "__main__":
    print("=" * 60)
    print("RT Monitor — Professional Documentation")
    print("=" * 60)
    
    print("\n📋 Kompaniya profili:")
    print(f"  Nomi: {COMPANY_PROFILE['name']}")
    print(f"  Turi: {COMPANY_PROFILE['type']}")
    print(f"  Universitet: {COMPANY_PROFILE['university']}")
    
    print(f"\n📊 Xizmatlar: {len(SERVICES)} ta")
    for s in SERVICES:
        print(f"  • {s['name']}: {s['description'][:50]}...")
    
    print("\n🤝 Hamkorlik taklifi:")
    print(get_partnership_proposal("Namuna Bank")[:200] + "...")
    
    print("\n💰 ROI hisoboti:")
    print(get_roi_report())
    
    print("\n✅ Barcha hujjatlar tayyor!")