#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
════════════════════════════════════════════════════════════════════════════
 AI INDEKSI klubi — Telegram ro'yxatdan o'tish boti   (@aiindeksi_bot)   v2.0
 «Sun'iy intellekt monitoringi va raqamli o'lchov» klubi (ADRL / AAI-UZ)
 Toshkent davlat iqtisodiyot universiteti
════════════════════════════════════════════════════════════════════════════

 v2.0 YANGILIKLARI:
   • CSV endi HAR BIR YOZUV alohida qatorda (va qo'shimcha XLSX — Excel'da
     kafolatli ochiladi, chunki ba'zi telefon viewer'lari CSV ni buzadi).
   • Fakultetlar klaviaturasi TDIU ning RASMIY 14 ta fakulteti (tsue.uz) +
     «Boshqa» → erkin matn qadami.
   • Kurslar: 1–4 + Magistratura.
   • KANAL integratsiyasi (channel.txt / AIINDEKSI_CHANNEL):
       – /start da kanalga a'zolik tekshiruvi (force-subscribe, adminlardan tashqari);
       – ro'yxatdan o'tganda «Kanalga a'zo bo'ling» tugmasi;
       – /elon <matn> → admin e'lonni kanalga yuboradi (tadbirga chaqiruv);
       – /statlar kanal a'zolari sonini ham ko'rsatadi.
     Kanal sozlanmaganda bu funksiyalar shunchaki o'chib turadi.
   • Admin salomi: /start da admin avtomatik taniladi.

 BUYRUQLAR:
   /start · /foyda · /help · /holat · /bekor · admin: /statlar · /export · /elon

 TEXNIK: faqat Python 3 standart kutubxonasi (urllib, json, csv, zipfile...).
 ISHGA TUSHIRISH: token.txt (yoki AIINDEKSI_TOKEN) → python3 aiindeksi_bot.py
 DEMO: python3 aiindeksi_bot.py --demo   ·   TEST: python3 aiindeksi_bot.py --test

 SOZLASH FAYLLARI (shu papkada): token.txt · admin.txt · channel.txt (ixtiyoriy)
 XAVFSIZLIK: uchala faylni Git'ga qo'shmang; token ochiq qolsa BotFather /revoke.
"""

import csv
import io
import json
import os
import re
import sys
import time
import logging
import zipfile
import urllib.request
import urllib.error
import urllib.parse

# ─────────────────────────── SOZLAMALAR ───────────────────────────
HERE = os.path.dirname(os.path.abspath(__file__))
API = "https://api.telegram.org"
POLL_TIMEOUT = 45
DEMO = "--demo" in sys.argv
TEST = "--test" in sys.argv

log = logging.getLogger("aiindeksi")
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-7s | %(message)s")

def _read_secret(fname, env):
    v = os.environ.get(env, "").strip()
    if v:
        return v
    p = os.path.join(HERE, fname)
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            return f.read().strip()
    return ""

TOKEN = "" if (DEMO or TEST) else _read_secret("token.txt", "AIINDEKSI_TOKEN")
ADMIN_RAW = "" if TEST else _read_secret("admin.txt", "AIINDEKSI_ADMIN")
ADMIN_IDS = set(int(x) for x in re.findall(r"\d+", ADMIN_RAW))
CHANNEL = "" if TEST else _read_secret("channel.txt", "AIINDEKSI_CHANNEL")
DB_PATH = os.path.join(HERE, "demo_db.json" if DEMO else
                       ("test_db.json" if TEST else "aiindeksi_jazmalar.json"))

def kanal_url():
    return ("https://t.me/" + CHANNEL.lstrip("@")) if CHANNEL.startswith("@") else ""

# ─────────────────────────── MATNLAR ───────────────────────────
START_MATN = (
    "Assalomu alaykum! 👋\n\n"
    "Bu — «AI INDEKSI» klubi (TDIU) rasmiy ro'yxatdan o'tish boti.\n"
    "Klub sun'iy intellektning O'zbekistonda qayerda ISHLAYOTGANINI va "
    "qayerda ISHLAMAYOTGANINI ochiq ma'lumotlar asosida o'lchaydi.\n\n"
    "📣 Kanal: t.me/Raqamli_tadqiqot — barcha e'lonlar va tadbir "
    "chaqiruvlari shu yerda.\n\n"
    "Nega a'zo bo'lish kerak? /foyda — xabardorlik, jamoa, o'sish "
    "va fanga hissa.\n\n"
    "Ro'yxatdan o'tish 4 savoldan iborat (≈40 soniya):\n"
    "  1) ism-familiya\n  2) fakultet\n  3) kurs\n  4) ta'lim yo'nalishi\n\n"
    "Boshlaymizmi? Ism-familiangizni yozing ✍️"
)
SAVOLAR = [
    ("ism",      "1/4  ·  Ism-familiangizni yozing:\nMasalan: Aliyeva Malika Rashidovna"),
    ("fakultet", "2/4  ·  Fakultetingizni tanlang yoki yozing:"),
    ("kurs",     "3/4  ·  Kursingizni tanlang:"),
    ("yonalish", "4/4  ·  Ta'lim yo'nalishingizni yozing:\nMasalan: Buxgalteriya hisobi va audit"),
]
# TDIU rasmiy fakultetlari (tsue.uz, 30.09.2026 holatiga)
FAKULTETLAR = ["Iqtisodiyot", "Turizm", "Raqamli iqtisodiyot va AT",
               "Moliya", "Buxgalteriya hisobi", "Bank ishi",
               "Menejment", "Soliqlar va byudjet hisobi",
               "Qo'shma ta'lim dasturlari", "Kechki ta'lim va magistratura",
               "Sirtqi ta'lim", "Masofaviy va 2-oliy ta'lim",
               "To'rtko'l", "Andijon", "Boshqa"]
KURSLAR = ["1", "2", "3", "4", "Magistratura"]
YAKUN = (
    "✅ Ro'yxatdan o'tdingiz!\n\n"
    "№ {nomer}\n"
    "👤 {ism}\n"
    "🏛 {fakultet}\n"
    "🎓 {kurs}-kurs\n"
    "📚 {yonalish}\n\n"
    "Birinchi ochiq uchrashuv sanasi e'lon qilinganda shu bot orqali "
    "xabar beramiz. Klubga xush kelibsiz! 🎉\n\n"
    "Ma'lumotlaringizni ko'rish: /holat   ·   O'chirish: /bekor"
)
FOYDA_MATN = (
    "🌱 Klub nima beradi? — 6 ta halol javob\n\n"
    "1️⃣ XABARDORLIK: O'zbekistonda AI ning real manzarasini birinchi bo'lib "
    "bilasan. Ochiq ma'lumot, haftalik digest, choraklik milliy hisobot — "
    "hech kimda yo'q manzara.\n"
    "2️⃣ JAMOA: 6+ fakultetdan fikrdoshlar, mentor va peer-review madaniyati. "
    "Birinchi kurs ham joy topadi: kuzatuvchidan muallifgacha.\n"
    "3️⃣ RIVOJLANISH: ma'ruzada berilmaydigan ko'nikmalar — manba qidirish va "
    "tekshirish, indeks qurish, Excel/Python amaliyotda, yozish va himoya qilish.\n"
    "4️⃣ HISSA: bitta bo'sh katakchani to'ldirsang — mamlakatda bitta yangi "
    "bilim paydo bo'ladi. Isming milliy AAI-UZ hisoboti mualliflari qatorida.\n"
    "5️⃣ TAN OLINISH: sertifikatda aniq yoziladi kim nima qilgani; 4 ta ichki "
    "daraja, mualliflik, kurator tavsiyanomasi.\n"
    "6️⃣ YON TA'SIR (va'dasiz): klub faoliyati ayni paytda ijtimoiy faollik "
    "indeksi (tif.tsue.uz) va nashr yo'li uchun hujjat bo'ladi. Qaror "
    "komissiyada, hujjat bizda.\n\n"
    "Bizda halollik qoida: va'da bermaymiz — ko'rsatamiz. Ro'yxatdan o'tish: /start"
)
HELP_MATN = (
    "📘 Buyruqlar:\n"
    "/start — ro'yxatdan o'tishni boshlash\n"
    "/foyda — menga nima beradi? (6 ta aniq foyda)\n"
    "/holat — mening yozuvim\n"
    "/bekor — jarayonni bekor qilish / yozuvni o'chirish\n"
    "/help  — shu ro'yxat\n\n"
    "Admin uchun: /statlar, /export (CSV+XLSX), /elon (kanalga e'lon)\n\n"
    "Klub faqat OCHIQ manbalar bilan ishlaydi. A'zolik BEPUL.\n"
    "📣 Kanal: t.me/Raqamli_tadqiqot"
)

# ─────────────────────────── DB ───────────────────────────
def db_load():
    if os.path.exists(DB_PATH):
        try:
            with open(DB_PATH, encoding="utf-8") as f:
                return json.load(f)
        except (ValueError, OSError):
            log.warning("DB buzilgan, yangi boshlanmoqda: %s", DB_PATH)
    return {"users": {}, "state": {}, "counter": 0}

def db_save(db):
    tmp = DB_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=1)
    os.replace(tmp, DB_PATH)

# ─────────────────────────── TELEGRAM API ───────────────────────────
def tg(method, **kw):
    if not TOKEN:
        return None
    url = "%s/bot%s/%s" % (API, TOKEN, method)
    data = urllib.parse.urlencode(kw, doseq=True).encode("utf-8")
    req = urllib.request.Request(url, data=data)
    for urinish in range(3):
        try:
            with urllib.request.urlopen(req, timeout=POLL_TIMEOUT + 15) as r:
                return json.loads(r.read().decode("utf-8")).get("result")
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")[:300]
            log.error("HTTP %s (%s): %s", e.code, method, body)
            if e.code in (401, 404):
                raise SystemExit("TOKEN xato yoki bot o'chirilgan. BotFather'dan tekshiring.")
            time.sleep(2 + urinish * 3)
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            log.warning("Tarmoq xatosi (%s), qayta urinaman...", e)
            time.sleep(2 + urinish * 3)
    return None

def send(chat_id, matn, kb=None):
    kw = {"chat_id": chat_id, "text": matn, "parse_mode": "HTML",
          "disable_web_page_preview": True}
    if kb:
        kw["reply_markup"] = json.dumps(kb, ensure_ascii=False)
    return tg("sendMessage", **kw)

def send_doc(chat_id, path, mime):
    """Faylni multipart/form-data bilan yuborish (faqat stdlib)."""
    boundary = "----aiindeksi%012x" % int(time.time() * 1000)
    with open(path, "rb") as f:
        fayl = f.read()
    body = io.BytesIO()
    body.write(("--%s\r\nContent-Disposition: form-data; name=\"chat_id\"\r\n\r\n%s\r\n"
                % (boundary, chat_id)).encode())
    body.write(("--%s\r\nContent-Disposition: form-data; name=\"document\"; "
                "filename=\"%s\"\r\nContent-Type: %s\r\n\r\n"
                % (boundary, os.path.basename(path), mime)).encode())
    body.write(fayl)
    body.write(("\r\n--%s--\r\n" % boundary).encode())
    req = urllib.request.Request("%s/bot%s/sendDocument" % (API, TOKEN),
                                 data=body.getvalue(),
                                 headers={"Content-Type":
                                          "multipart/form-data; boundary=%s" % boundary})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode("utf-8")).get("ok")
    except (urllib.error.URLError, OSError) as e:
        log.error("Fayl yuborilmadi: %s", e)
        return False

def _kb_qatorlar(items, per_row):
    return [[{"text": t} for t in items[i:i + per_row]] for i in range(0, len(items), per_row)]

KB_FAK = {"keyboard": _kb_qatorlar(FAKULTETLAR, 2),
          "resize_keyboard": True, "one_time_keyboard": True}
KB_KURS = {"keyboard": [[{"text": k} for k in KURSLAR]],
           "resize_keyboard": True, "one_time_keyboard": True}
KB_YOQ = {"remove_keyboard": True}

def kanal_kb():
    if kanal_url():
        return {"inline_keyboard": [[{"text": "📣 Kanalga a'zo bo'ling", "url": kanal_url()}]]}
    return KB_YOQ

def kanal_azosi(uid):
    if not CHANNEL or not TOKEN:
        return True
    r = tg("getChatMember", chat_id=CHANNEL, user_id=uid)
    if r is None:   # bot kanal a'zosi/admin emas yoki tarmoq xatosi -> to'siqni ochiq qoldiramiz
        return True
    return r.get("status") in ("member", "administrator", "creator", "restricted")

# ─────────────────────────── EXPORT (CSV + XLSX) ───────────────────────────
def _xml(t):
    return (str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))

def _col(i):
    s = ""
    i += 1
    while i:
        i, r = divmod(i - 1, 26)
        s = chr(65 + r) + s
    return s

def write_xlsx(path, header, rows):
    """Minimal XLSX (Office Open XML) — faqat stdlib zipfile bilan."""
    data = [header] + rows
    out = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
           '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
           '><sheetData>']
    for ri, row in enumerate(data, 1):
        out.append('<row r="%d">' % ri)
        for ci, val in enumerate(row):
            ref = "%s%d" % (_col(ci), ri)
            if isinstance(val, int) or (isinstance(val, str) and val.isdigit()):
                out.append('<c r="%s"><v>%s</v></c>' % (ref, val))
            else:
                out.append('<c r="%s" t="inlineStr"><is><t xml:space="preserve">%s</t>'
                           '</is></c>' % (ref, _xml(val)))
        out.append('</row>')
    out.append('</sheetData></worksheet>')
    sheet = "".join(out)
    ct = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
          '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
          '<Default Extension="xml" ContentType="application/xml"/>'
          '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
          '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
          '</Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
            '</Relationships>')
    wb = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
          '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
          'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
          '<sheets><sheet name="Royxat" sheetId="1" r:id="rId1"/></sheets></workbook>')
    wbrels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
              '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
              '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
              '</Relationships>')
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", ct)
        z.writestr("_rels/.rels", rels)
        z.writestr("xl/workbook.xml", wb)
        z.writestr("xl/_rels/workbook.xml.rels", wbrels)
        z.writestr("xl/worksheets/sheet1.xml", sheet)
    return path

def royxat_qatorlari(db):
    hdr = ["№", "Telegram ID", "Ism-familiya", "Fakultet", "Kurs", "Yo'nalish", "Sana (UTC)"]
    rows = []
    for i, (cid, u) in enumerate(sorted(db["users"].items(),
                                        key=lambda kv: kv[1].get("nomer", 0)), 1):
        rows.append([i, int(cid) if str(cid).isdigit() else cid, u.get("ism", ""),
                     u.get("fakultet", ""), u.get("kurs", ""), u.get("yonalish", ""),
                     u.get("sana", "")])
    return hdr, rows

def export_files(db):
    hdr, rows = royxat_qatorlari(db)
    csv_path = os.path.join(HERE, "aiindeksi_royxat.csv")
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";", lineterminator="\n")
        w.writerow(hdr)
        w.writerows(rows)
    xlsx_path = os.path.join(HERE, "aiindeksi_royxat.xlsx")
    write_xlsx(xlsx_path, hdr, rows)
    return csv_path, xlsx_path

# ─────────────────────────── HANDLER ───────────────────────────
def holat(chat_id, db):
    u = db["users"].get(str(chat_id))
    if not u:
        return "Siz hali ro'yxatdan o'tmagansiz.\nBoshlash: /start", None
    return YAKUN.format(**u) + "\n\n(holat: ro'yxatdan o'tgan)", None

def bekor(chat_id, db):
    if str(chat_id) in db["state"]:
        del db["state"][str(chat_id)]
        return "🚫 Ro'yxatdan o'tish bekor qilindi.\nQayta boshlash: /start", KB_YOQ
    if str(chat_id) in db["users"]:
        del db["users"][str(chat_id)]
        db_save(db)
        return ("🗑 Yozuvingiz o'chirildi.\nQayta ro'yxatdan o'tish: /start", KB_YOQ)
    return "Bekor qilinadigan yozuv yo'q.\nBoshlash: /start", None

def statlar(db):
    n = len(db["users"])
    fak, kurs = {}, {}
    for u in db["users"].values():
        fak[u.get("fakultet", "?")] = fak.get(u.get("fakultet", "?"), 0) + 1
        kurs[u.get("kurs", "?")] = kurs.get(u.get("kurs", "?"), 0) + 1
    q = ["📊 STATISTIKA", "Jami a'zo: %d" % n, "Jarayonda (yarim): %d" % len(db["state"])]
    if CHANNEL:
        cnt = tg("getChatMemberCount", chat_id=CHANNEL)
        q.append("Kanal a'zolari: %s" % (cnt if cnt is not None else "noma'lum"))
    q.append("\nFakultetlar bo'yicha:")
    q += ["  • %s — %d" % (k, v) for k, v in sorted(fak.items(), key=lambda kv: -kv[1])]
    q.append("Kurslar bo'yicha:")
    q += ["  • %s — %d" % (k, v) for k, v in sorted(kurs.items(), key=lambda kv: str(kv[0]))]
    return "\n".join(q), None

def handle(msg, db):
    chat_id = msg["chat"]["id"]
    matn = (msg.get("text") or "").strip()
    st = db["state"].get(str(chat_id))

    if matn == "/start":
        pref = ("🛡 Siz ADMIN sifatida tanildingiz: /statlar, /export, /elon faol.\n\n"
                if chat_id in ADMIN_IDS else "")
        if chat_id not in ADMIN_IDS and not kanal_azosi(chat_id):
            return ("Avval klub kanaliga a'zo bo'ling — e'lonlar va tadbir "
                    "chaqiruvlari shu yerda:\n\n" + (kanal_url() or CHANNEL) +
                    "\n\nQo'shilib, /start ni qayta yuboring.",
                    {"inline_keyboard": [[{"text": "📣 Kanalga qo'shilish",
                                           "url": kanal_url() or "https://t.me/"}]]})
        if str(chat_id) in db["users"] and not st:
            return (pref + "Siz allaqachon ro'yxatdan o'tgansiz ✅\n"
                    "Ma'lumotlaringiz: /holat\nYangi a'zo qo'shish uchun avval /bekor", None)
        m_, k_ = (START_MATN + "\n\n" + SAVOLAR[0][1], None)
        db["state"][str(chat_id)] = {"bosqich": 0, "javoblar": {}}
        return pref + m_, k_
    if matn == "/help":
        return HELP_MATN, None
    if matn in ("/foyda", "/benefit", "/foida"):
        return FOYDA_MATN, None
    if matn == "/holat":
        return holat(chat_id, db)
    if matn in ("/bekor", "/cancel"):
        return bekor(chat_id, db)
    if matn in ("/statlar", "/stats", "/export"):
        if chat_id not in ADMIN_IDS:
            return "⛭ Bu buyruq faqat klub administratori uchun.", None
        if matn == "/export":
            c, x = export_files(db)
            if TOKEN:
                send_doc(chat_id, c, "text/csv")
                send_doc(chat_id, x,
                         "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                return ("📎 CSV va XLSX yuborildi (%d ta yozuv). XLSX — Excel/Google Sheets'da "
                        "kafolatli ochiladi." % len(db["users"]), None)
            return ("📎 Fayllar tayyor: %s va %s (%d ta yozuv). Token yo'q — "
                    "yuborilmadi." % (os.path.basename(c), os.path.basename(x),
                                      len(db["users"])), None)
        return statlar(db)
    if matn.startswith("/elon"):
        if chat_id not in ADMIN_IDS:
            return "⛭ Bu buyruq faqat klub administratori uchun.", None
        if not CHANNEL:
            return ("Kanal sozlanmagan. channel.txt fayliga kanal username'ini "
                    "yozing (masalan: @aiindeksi_tdiu) va botni kanalga admin "
                    "qilib qo'shing.", None)
        t = matn[5:].strip()
        if not t:
            return "Foydalanish: /elon E'lon matni", None
        ok = tg("sendMessage", chat_id=CHANNEL, text=t, parse_mode="HTML",
                disable_web_page_preview=True)
        return ("📣 E'lon kanalga yuborildi." if ok else
                "⚠️ Yuborilmadi: bot kanalga ADMIN qilib qo'shilganmi va post "
                "huquqi bormi?"), None
    if matn.startswith("/"):
        return "Bunday buyruq yo'q.\nBuyruqlar: /help", None

    # — ro'yxatdan o'tish oqimi —
    if not st:
        return "Avval /start buyrug'ini yuboring 🙂", None
    bosqich, javoblar = st["bosqich"], st["javoblar"]
    kalit, _ = SAVOLAR[bosqich]

    if kalit == "ism" and len(matn) < 3:
        return "Ism-familiya to'liq yozilsin (kamida 3 belgi).", None
    if kalit == "fakultet" and matn == "Boshqa" and not st.get("boshqa"):
        st["boshqa"] = True
        return ("Fakultetingiz nomini to'liq yozing "
                "(masalan: Raqamli iqtisodiyot va axborot texnologiyalari):"), None
    if kalit == "kurs" and matn not in KURSLAR:
        return "Kursni tugmadan tanlang: 1, 2, 3, 4 yoki Magistratura.", KB_KURS
    javoblar[kalit] = matn
    st.pop("boshqa", None)
    st["bosqich"] += 1

    if st["bosqich"] < len(SAVOLAR):
        keyt = KB_FAK if SAVOLAR[st["bosqich"]][0] == "fakultet" else (
               KB_KURS if SAVOLAR[st["bosqich"]][0] == "kurs" else KB_YOQ)
        return SAVOLAR[st["bosqich"]][1], keyt

    db["counter"] += 1
    yozuv = {"nomer": db["counter"], "ism": javoblar["ism"],
             "fakultet": javoblar["fakultet"], "kurs": javoblar["kurs"],
             "yonalish": javoblar["yonalish"],
             "sana": time.strftime("%Y-%m-%d %H:%M", time.gmtime())}
    db["users"][str(chat_id)] = yozuv
    del db["state"][str(chat_id)]
    db_save(db)
    for aid in ADMIN_IDS:
        send(aid, "🔔 Yangi a'zo: #%d %s (%s, %s-kurs)" % (
            yozuv["nomer"], yozuv["ism"], yozuv["fakultet"], yozuv["kurs"]))
    return YAKUN.format(**yozuv), kanal_kb()


# ─────────────────── WEB QATLAM (Render free uchun) ───────────────────
def make_server(get_db):
    """Mini app (/), health check (/healthz) va jonli statistika (/stats.json)."""
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    MINI = os.path.join(HERE, "miniapp", "index.html")

    class H(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"
        def log_message(self, *a):
            pass
        def _send(self, code, body, ctype):
            b = body.encode("utf-8") if isinstance(body, str) else body
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(b)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(b)
        def do_GET(self):
            p = self.path.split("?")[0]
            if p in ("/", "/index.html"):
                try:
                    with open(MINI, encoding="utf-8") as f:
                        self._send(200, f.read(), "text/html; charset=utf-8")
                except OSError:
                    self._send(404, "miniapp topilmadi", "text/plain")
            elif p == "/healthz":
                self._send(200, '{"ok":true}', "application/json")
            elif p == "/stats.json":
                db = get_db()
                fak, kurs = {}, {}
                for u in db["users"].values():
                    fak[u.get("fakultet", "?")] = fak.get(u.get("fakultet", "?"), 0) + 1
                    kurs[u.get("kurs", "?")] = kurs.get(u.get("kurs", "?"), 0) + 1
                self._send(200, json.dumps(
                    {"members": len(db["users"]), "fakultet": fak, "kurs": kurs,
                     "updated": time.strftime("%Y-%m-%d %H:%M", time.gmtime())},
                    ensure_ascii=False), "application/json; charset=utf-8")
            else:
                self._send(404, "not found", "text/plain")

    port = int(os.environ.get("PORT", "8000"))
    return ThreadingHTTPServer(("0.0.0.0", port), H)

def keep_alive(url):
    """Render free web service uyquga ketmasligi uchun o'z-o'zini pinglab turadi."""
    while True:
        time.sleep(240)
        try:
            urllib.request.urlopen(url + "/healthz", timeout=15).read()
        except Exception:
            pass

# ─────────────────────────── LONG-POLLING / DEMO / TEST ───────────────────────────
def poll(db=None):
    db = db or db_load()
    if not TOKEN:
        raise SystemExit("TOKEN topilmadi! Qarang: fayl boshidagi yo'riqnoma "
                         "(yoki --demo bilan sinab ko'ring).")
    log.info("Bot ishga tushdi (long-polling). DB: %s | kanal: %s | adminlar: %s",
             DB_PATH, CHANNEL or "(sozlanmagan)", sorted(ADMIN_IDS))
    offset = 0
    while True:
        nat = tg("getUpdates", timeout=POLL_TIMEOUT, offset=offset,
                 allowed_updates='["message"]')
        if nat is None:
            continue
        for up in nat:
            offset = up["update_id"] + 1
            msg = up.get("message")
            if not msg or "text" not in msg:
                continue
            try:
                javob, kb = handle(msg, db)
                db_save(db)
            except Exception as e:                      # noqa: BLE001
                log.exception("Handler xatosi: %s", e)
                javob, kb = "⚠️ Ichki xato. Keyinroq qayta urinib ko'ring.", None
            if javob:
                send(msg["chat"]["id"], javob, kb)

def suhbat(kiritmalar, db, chat_id=100001, admin_id=None):
    chiqish = []
    global ADMIN_IDS
    if admin_id is not None:
        ADMIN_IDS = {admin_id}
    for m in kiritmalar:
        chiqish.append(("👤 foydalanuvchi", m))
        javob, kb = handle({"chat": {"id": chat_id}, "text": m}, db)
        db_save(db)
        chiqish.append(("🤖 bot", javob or "(javob yo'q)"))
        if kb and kb.get("keyboard"):
            chiqish.append(("   [klaviatura]", " | ".join(
                t["text"] for row in kb["keyboard"] for t in row)))
    return chiqish

def demo():
    print("═" * 72)
    print(" DEMO REJIM — Telegram'siz sinov. Chiqish: /exit")
    print("═" * 72)
    db = db_load()
    chat = 100001
    print("\n🤖 bot: /start yozing yoki /help ko'ring\n")
    while True:
        try:
            m = input("👤 siz  > ").strip()
        except EOFError:
            break
        if m in ("/exit", "/quit"):
            break
        if not m:
            continue
        javob, kb = handle({"chat": {"id": chat}, "text": m}, db)
        db_save(db)
        print("\n🤖 bot  > %s" % (javob or "(javob yo'q)"))
        if kb and kb.get("keyboard"):
            print("   [tugmalar] " + " | ".join(t["text"] for r in kb["keyboard"] for t in r))
        print()
    print("\nDemo yakunlandi. Bazada %d ta yozuv (%s)." % (len(db["users"]), DB_PATH))

def test():
    db = {"users": {}, "state": {}, "counter": 0}
    ketma = ["/start", "Aliyeva Malika Rashidovna", "Boshqa",
             "Statistika fakulteti", "2", "Statistika va ma'lumotlar tahlili",
             "/holat", "/statlar", "/export"]
    ch = suhbat(ketma, db, chat_id=100001, admin_id=100001)
    for kim, m in ch:
        print("%-16s %s" % (kim, m.replace("\n", "\n" + " " * 17)))
    assert len(db["users"]) == 1, "yozuv saqlanmadi!"
    u = list(db["users"].values())[0]
    assert u["ism"] == "Aliyeva Malika Rashidovna" and u["kurs"] == "2"
    assert u["fakultet"] == "Statistika fakulteti", "Boshqa→erkin matn ishlamadi"
    assert db["state"] == {}, "state tozalanmadi!"
    c, x = os.path.join(HERE, "aiindeksi_royxat.csv"), os.path.join(HERE, "aiindeksi_royxat.xlsx")
    assert os.path.exists(c) and os.path.exists(x), "CSV/XLSX yaratilmadi!"
    lines = open(c, encoding="utf-8-sig").read().strip().split("\n")
    assert len(lines) == 2, "CSV qatorlari xato: %d" % len(lines)
    with zipfile.ZipFile(x) as z:
        assert "xl/worksheets/sheet1.xml" in z.namelist(), "XLSX buzilgan"
    print("\n✅ TEST O'TDI: ro'yxat (Boshqa→erkin matn) → saqlash → holat → "
          "statistika → CSV (qatorma-qator) + XLSX.")

if __name__ == "__main__":
    if TEST:
        test()
    elif DEMO:
        demo()
    elif os.environ.get("PORT"):
        import threading
        db = db_load()
        threading.Thread(target=poll, kwargs={"db": db}, daemon=True).start()
        su = os.environ.get("SELF_URL", "").strip().rstrip("/")
        if su:
            threading.Thread(target=keep_alive, args=(su,), daemon=True).start()
            log.info("Keep-alive yoqildi: %s", su)
        log.info("Web rejim: mini app / , /healthz , /stats.json (port %s)",
                 os.environ.get("PORT"))
        make_server(lambda: db).serve_forever()
    else:
        poll()
