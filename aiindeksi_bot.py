#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
════════════════════════════════════════════════════════════════════════════
 AI Labs klubi — Telegram ro'yxatdan o'tish boti   (@aiindeksi_bot)   v2.1
 «Sun'iy intellekt monitoringi va raqamli o'lchov» klubi (ADRL / AAI-UZ)
 Toshkent davlat iqtisodiyot universiteti
════════════════════════════════════════════════════════════════════════════

 v2.1: DOIMIY BAZA — yopiq GitHub ombori (AILABS_DB_REPO/AILABS_DB_TOKEN), Render restarti
   endi ma'lumotni o'chirmaydi; /export → uslubli XLSX (har ustun alohida, Toshkent vaqti),
   /export csv → vergulli CSV; /royxat → telefonda matnli ro'yxat; admin xabarida yo'nalish
   va @username.

 v2.0 YANGILIKLARI:
   • CSV endi HAR BIR YOZUV alohida qatorda (va qo'shimcha XLSX — Excel'da
     kafolatli ochiladi, chunki ba'zi telefon viewer'lari CSV ni buzadi).
   • Fakultetlar klaviaturasi TDIU'ning RASMIY 14 ta fakulteti (tsue.uz) +
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

import base64
import csv
import hashlib
import hmac
import io
import json
import os
import re
import sys
import threading
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

# Doimiy baza: yopiq GitHub ombori (Render free diski har restartda o'chadi)
GH_REPO = "" if (DEMO or TEST) else _read_secret("ghrepo.txt", "AILABS_DB_REPO")
GH_TOKEN = "" if (DEMO or TEST) else _read_secret("ghtoken.txt", "AILABS_DB_TOKEN")
GH_FILE = "db.json"
TZ_SOAT = 5   # Toshkent = UTC+5

def kanal_url():
    return ("https://t.me/" + CHANNEL.lstrip("@")) if CHANNEL.startswith("@") else ""

# ─────────────────────────── MATNLAR ───────────────────────────
START_MATN = (
    "Assalomu alaykum! 👋\n\n"
    "Bu — «AI Labs» klubi (TDIU) rasmiy ro'yxatdan o'tish boti.\n"
    "Klub sun'iy intellektning O'zbekistonda qayerda ISHLAYOTGANINI va "
    "qayerda ISHLAMAYOTGANINI ochiq ma'lumotlar asosida o'lchaydi.\n\n"
    "📣 Kanal: t.me/Raqamli_tadqiqot — barcha e'lonlar va tadbir "
    "chaqiruvlari shu yerda.\n"
    "🌐 Sayt: ailabs.tdiu.workers.dev — pilot natijasi, kalkulyator, test.\n\n"
    "Nega a'zo bo'lish kerak? /foyda — xabardorlik, jamoa, o'sish "
    "va fanga hissa.\n\n"
    "Ro'yxatdan o'tish 4 savoldan iborat (≈40 soniya):\n"
    "  1) ism-familiya\n  2) fakultet\n  3) kurs\n  4) ta'lim yo'nalishi\n\n"
    "Boshlaymizmi? Ism-familiyangizni yozing ✍️\n\n"
    "⚖️ Maxfiylik: saqlanadigani faqat ism, fakultet, kurs, yo'nalish va "
    "Telegram ID/username — klub reyestri uchun (Nizom, 8-bo'lim). Ro'yxatdan o'tish "
    "orqali rozilik bildirasiz. Ko'rish: /holat · O'chirish: /bekor · "
    "Batafsil: /maxfiylik"
)
SAVOLAR = [
    ("ism",      "1/4  ·  Ism-familiyangizni yozing:\nMasalan: Aliyeva Malika Rashidovna"),
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
    "1️⃣ XABARDORLIK: O'zbekistonda sun'iy intellektning real manzarasini birinchilardan "
    "bo'lib ko'rasiz: ochiq ma'lumotlar, haftalik digest va choraklik hisobot.\n"
    "2️⃣ JAMOA: turli fakultetlardan fikrdoshlar, mentor va o'zaro tekshiruv (peer-review) "
    "madaniyati. Birinchi kurs talabasi ham o'z o'rnini topadi: kuzatuvchidan muallifgacha.\n"
    "3️⃣ RIVOJLANISH: darsdagi bilimni real loyihada mustahkamlaysiz — manba qidirish va "
    "tekshirish, indeks qurish, Excel/Python, ilmiy yozish va himoya.\n"
    "4️⃣ HISSA: bo'sh katakni to'ldirsangiz, indeksga yangi tekshirilgan dalil qo'shiladi. "
    "Real hissa hisobotda nom bilan ko'rsatiladi.\n"
    "5️⃣ E'TIROF: bajarilgan ish tasdiqlovchi hujjatda aniq yoziladi — kim, nima qilgani; "
    "4 ta ichki daraja va kurator tavsiyanomasi.\n"
    "6️⃣ KELAJAK UCHUN BAZA (va'dasiz): ilmiy tezis va maqola uchun tayyor material. "
    "Baholash qarorlarini tegishli komissiyalar qabul qiladi.\n\n"
    "Biz va'da bermaymiz — natijani ko'rsatamiz. Ro'yxatdan o'tish: /start"
)
MAXFIYLIK_MATN = (
    "⚖️ MA'LUMOTLAR SIYOSATI (qisqa)\n\n"
    "1. Saqlanadi: ism, fakultet, kurs, yo'nalish, Telegram ID va username, sana. Boshqa "
    "hech narsa (telefon, pasport, joylashuv SO'RALMAYDI).\n"
    "2. Maqsad: klub reyestri, davomat va faoliyat hujjatlari "
    "(Nizom, 8-bo'lim). Uchinchi shaxsga berilmaydi.\n"
    "3. Huquqlaringiz: /holat (ko'rish), /bekor (o'chirish) — istalgan payt, "
    "savolsiz.\n"
    "4. Server: bot vaqtincha xorijiy hostingda (Render), reyestr nusxasi — yopiq "
    "(private) omborda. Chorak yakunida "
    "reyestr universitetdagi rasmiy saqlovga topshiriladi va bot bazasi "
    "tozalanadi (ZRU-547, 27-1-modda talabiga intilamiz).\n"
    "5. Hodisa bo'lsa (token/database ochilsa): 24 soat ichida kanalda ochiq "
    "e'lon qilinadi va barcha kalitlar almashtiriladi."
)
HELP_MATN = (
    "📘 Buyruqlar:\n"
    "/start — ro'yxatdan o'tishni boshlash\n"
    "/foyda — klub nima beradi? (6 ta halol javob)\n"
    "/holat — mening yozuvim\n"
    "/maxfiylik — ma'lumotlar siyosati\n"
    "/bekor — jarayonni bekor qilish / yozuvni o'chirish\n"
    "/help  — shu ro'yxat\n\n"
    "Admin uchun: /statlar, /royxat (matnli ro'yxat), /export (Excel), /elon (kanalga e'lon)\n\n"
    "Klub faqat OCHIQ manbalar bilan ishlaydi. A'zolik BEPUL.\n"
    "📣 Kanal: t.me/Raqamli_tadqiqot\n"
    "🌐 Sayt: ailabs.tdiu.workers.dev"
)

# ─────────────────────────── DB ───────────────────────────
# Ishchi nusxa xotirada + lokal fayl; doimiy nusxa — yopiq GitHub ombori (GH_REPO/db.json).
# Qoidalar: (1) GitHub'dan o'qilmaguncha unga HECH QACHON yozilmaydi (bo'sh baza bilan
# ustiga yozib yuborish xavfi yo'q); (2) sha to'qnashuvi bo'lsa — birlashtirib qayta yoziladi;
# (3) /bekor bilan o'chirilganlar "deleted" ro'yxatida turadi, birlashtirishda tirilmaydi.
PERSIST = ("users", "state", "counter", "deleted")
GH = {"sha": None, "synced": False, "last_ok": None, "err": "", "last_body": None}
DB_LOCK = threading.RLock()
_DB_REF = {"db": None}
_DIRTY = threading.Event()

def _bo_sh_db():
    return {"users": {}, "state": {}, "counter": 0, "deleted": {}}

def _norm(db):
    for k, v in _bo_sh_db().items():
        db.setdefault(k, v)
    return db

def _gh_req(method, url, data=None):
    req = urllib.request.Request(url, method=method,
        data=json.dumps(data).encode("utf-8") if data is not None else None,
        headers={"Authorization": "Bearer " + GH_TOKEN, "User-Agent": "ailabs-bot",
                 "Accept": "application/vnd.github+json", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read().decode("utf-8"))

def gh_fetch():
    """(dict|None, sha|None). 404 → (None, None). Tarmoq xatosi → exception."""
    url = "https://api.github.com/repos/%s/contents/%s" % (GH_REPO, GH_FILE)
    try:
        d = _gh_req("GET", url)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None, None
        raise
    raw = d.get("content") or ""
    if not raw:   # >1 MB bo'lsa contents API kontentni bermaydi → blob
        raw = _gh_req("GET", "https://api.github.com/repos/%s/git/blobs/%s"
                      % (GH_REPO, d["sha"]))["content"]
    return json.loads(base64.b64decode(raw).decode("utf-8")), d["sha"]

def _ts(u):
    return float(u.get("ts") or 0)

def db_merge(local, remote):
    """local ustun; ikkalasidagi a'zolar birlashadi; o'chirilganlar tirilmaydi."""
    remote = _norm(dict(remote or {}))
    dl = dict(remote.get("deleted", {}))
    for k, v in local.get("deleted", {}).items():
        dl[k] = max(float(v), float(dl.get(k, 0)))
    users = dict(remote.get("users", {}))
    for k, u in local.get("users", {}).items():
        if k not in users or _ts(u) >= _ts(users[k]):
            users[k] = u
    for k, t in dl.items():
        if k in users and _ts(users[k]) <= float(t):
            del users[k]
    local["users"] = users
    local["deleted"] = dl
    local["counter"] = max([int(local.get("counter", 0)), int(remote.get("counter", 0))] +
                           [int(u.get("nomer", 0)) for u in users.values()])
    st = dict(remote.get("state", {})); st.update(local.get("state", {}))
    local["state"] = {k: v for k, v in st.items() if k not in users}
    return local

def _local_load():
    if os.path.exists(DB_PATH):
        try:
            with open(DB_PATH, encoding="utf-8") as f:
                return _norm(json.load(f))
        except (ValueError, OSError):
            log.warning("Lokal DB buzilgan: %s", DB_PATH)
    return _bo_sh_db()

def _gh_sync_in(db):
    """GitHub'dagi nusxani o'qib, xotiradagiga birlashtiradi. True = muvaffaqiyat."""
    try:
        remote, sha = gh_fetch()
    except Exception as e:                          # noqa: BLE001
        GH["err"] = "o'qish: %s" % e
        return False
    with DB_LOCK:
        if remote is not None:
            db_merge(db, remote)
        GH["sha"], GH["synced"], GH["err"] = sha, True, ""
    return True

def db_load():
    db = _local_load()
    _DB_REF["db"] = db
    if GH_REPO and GH_TOKEN:
        for urinish in range(6):
            if _gh_sync_in(db):
                log.info("DB GitHub'dan yuklandi: %d a'zo (%s)", len(db["users"]), GH_REPO)
                break
            log.warning("GitHub o'qilmadi (%s), %d-urinish", GH["err"], urinish + 1)
            time.sleep(2 + urinish * 3)
        threading.Thread(target=_gh_writer, daemon=True).start()
    return db

def _snapshot(db):
    with DB_LOCK:
        return json.dumps({k: db.get(k) for k in PERSIST}, ensure_ascii=False,
                          indent=1, sort_keys=True)

def db_save(db):
    _DB_REF["db"] = db
    body = _snapshot(db)
    tmp = DB_PATH + ".tmp"
    with DB_LOCK:
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(body)
        os.replace(tmp, DB_PATH)
    if GH_REPO and GH_TOKEN and body != GH["last_body"]:
        _DIRTY.set()

def _gh_writer():
    url = "https://api.github.com/repos/%s/contents/%s" % (GH_REPO, GH_FILE)
    kutish = 2
    while True:
        _DIRTY.wait()
        time.sleep(1.5)                              # debounce: ketma-ket o'zgarishlar bitta commit
        db = _DB_REF["db"]
        if not GH["synced"] and not _gh_sync_in(db):
            time.sleep(min(kutish, 60)); kutish *= 2
            continue                                  # o'qilmaguncha yozmaymiz
        _DIRTY.clear()
        body = _snapshot(db)
        if body == GH["last_body"]:
            continue
        data = {"message": "db: %d a'zo" % len(db["users"]),
                "content": base64.b64encode(body.encode("utf-8")).decode()}
        if GH["sha"]:
            data["sha"] = GH["sha"]
        try:
            r = _gh_req("PUT", url, data)
            GH["sha"] = r["content"]["sha"]; GH["last_body"] = body
            GH["last_ok"], GH["err"], kutish = time.time(), "", 2
        except urllib.error.HTTPError as e:
            GH["err"] = "yozish HTTP %s" % e.code
            if e.code in (409, 422):                  # sha eskirgan → birlashtirib qayta
                GH["synced"] = False
            _DIRTY.set(); time.sleep(min(kutish, 60)); kutish *= 2
        except Exception as e:                        # noqa: BLE001
            GH["err"] = "yozish: %s" % e
            _DIRTY.set(); time.sleep(min(kutish, 60)); kutish *= 2

def baza_holati():
    if not (GH_REPO and GH_TOKEN):
        return "💾 Baza: faqat lokal fayl (⚠️ restartda o'chadi)"
    if GH["err"]:
        return "💾 Baza: ⚠️ GitHub xatosi — %s (lokal nusxa ishlayapti)" % GH["err"]
    t = GH["last_ok"]
    return "💾 Baza: yopiq GitHub ombori ✅" + (
        " · oxirgi saqlash %s" % time.strftime("%H:%M", time.gmtime(t + TZ_SOAT * 3600)) if t else "")

def mahalliy(sana_utc):
    """'YYYY-MM-DD HH:MM' (UTC) → Toshkent vaqti."""
    try:
        import calendar
        t = calendar.timegm(time.strptime(sana_utc, "%Y-%m-%d %H:%M"))
        return time.strftime("%d.%m.%Y %H:%M", time.gmtime(t + TZ_SOAT * 3600))
    except Exception:                                 # noqa: BLE001
        return sana_utc

def yangi_nomer(db, ism):
    """Tiklangan (qisman) yozuv shu ism bilan bo'lsa — o'rniga o'tadi va raqamini saqlaydi."""
    for k, u in list(db["users"].items()):
        if u.get("manba") == "tiklangan" and u.get("ism", "").lower() == ism.strip().lower():
            del db["users"][k]
            return u["nomer"]
    db["counter"] = int(db.get("counter", 0)) + 1
    return db["counter"]

def admin_xabar(y, uname, kanal=""):
    q = ["🔔 Yangi a'zo%s: #%d" % (kanal, y["nomer"]), "👤 " + y["ism"],
         "🏛 %s · %s-kurs" % (y["fakultet"], y["kurs"]), "📚 " + y["yonalish"]]
    if uname:
        q.append("💬 @" + uname)
    return "\n".join(q)

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

def write_xlsx(path, header, rows, widths=None):
    """XLSX (Office Open XML) — stdlib zipfile bilan: qalin sarlavha, ustun kengligi,
    muzlatilgan 1-qator, avtofiltr. Excel, Google Sheets, WPS, telefon viewer'larida ochiladi."""
    data = [header] + rows
    widths = widths or [max(8, min(45, max(len(str(r[i])) for r in data) + 2))
                        for i in range(len(header))]
    last = "%s%d" % (_col(len(header) - 1), len(data))
    out = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
           '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
           '<sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" '
           'activePane="bottomLeft" state="frozen"/></sheetView></sheetViews><cols>']
    out += ['<col min="%d" max="%d" width="%s" customWidth="1"/>' % (i + 1, i + 1, w)
            for i, w in enumerate(widths)]
    out.append('</cols><sheetData>')
    for ri, row in enumerate(data, 1):
        out.append('<row r="%d">' % ri)
        for ci, val in enumerate(row):
            ref = "%s%d" % (_col(ci), ri)
            st = ' s="1"' if ri == 1 else ' s="2"'
            if ri > 1 and isinstance(val, int):
                out.append('<c r="%s"%s><v>%s</v></c>' % (ref, st, val))
            else:
                out.append('<c r="%s"%s t="inlineStr"><is><t xml:space="preserve">%s</t>'
                           '</is></c>' % (ref, st, _xml(val)))
        out.append('</row>')
    out.append('</sheetData><autoFilter ref="A1:%s"/></worksheet>' % last)
    sheet = "".join(out)
    styles = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
              '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
              '<fonts count="2"><font><sz val="11"/><name val="Calibri"/></font>'
              '<font><b/><sz val="11"/><color rgb="FFFFFFFF"/><name val="Calibri"/></font></fonts>'
              '<fills count="3"><fill><patternFill patternType="none"/></fill>'
              '<fill><patternFill patternType="gray125"/></fill>'
              '<fill><patternFill patternType="solid"><fgColor rgb="FF1F3864"/></patternFill></fill></fills>'
              '<borders count="2"><border/><border><left style="thin"><color rgb="FFD0D7E2"/></left>'
              '<right style="thin"><color rgb="FFD0D7E2"/></right><top style="thin"><color rgb="FFD0D7E2"/></top>'
              '<bottom style="thin"><color rgb="FFD0D7E2"/></bottom></border></borders>'
              '<cellStyleXfs count="1"><xf/></cellStyleXfs><cellXfs count="3"><xf/>'
              '<xf fontId="1" fillId="2" borderId="1" applyFont="1" applyFill="1" applyBorder="1">'
              '<alignment vertical="center"/></xf>'
              '<xf borderId="1" applyBorder="1"><alignment vertical="center"/></xf></cellXfs>'
              '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>'
              '</styleSheet>')
    ct = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
          '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
          '<Default Extension="xml" ContentType="application/xml"/>'
          '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
          '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
          '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
          '</Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
            '</Relationships>')
    wb = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
          '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
          'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
          '<sheets><sheet name="Royxat" sheetId="1" r:id="rId1"/></sheets>'
          '<definedNames><definedName name="_xlnm._FilterDatabase" localSheetId="0" hidden="1">'
          'Royxat!$A$1:$%s$%d</definedName></definedNames></workbook>' % (_col(len(header) - 1), len(data)))
    wbrels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
              '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
              '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
              '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
              '</Relationships>')
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", ct)
        z.writestr("_rels/.rels", rels)
        z.writestr("xl/workbook.xml", wb)
        z.writestr("xl/_rels/workbook.xml.rels", wbrels)
        z.writestr("xl/styles.xml", styles)
        z.writestr("xl/worksheets/sheet1.xml", sheet)
    return path

def royxat_qatorlari(db):
    hdr = ["№", "Ism-familiya", "Fakultet", "Kurs", "Yo'nalish", "Telegram",
           "Telegram ID", "Manba", "Sana (Toshkent)"]
    rows = []
    for cid, u in sorted(db["users"].items(), key=lambda kv: int(kv[1].get("nomer", 0))):
        rows.append([int(u.get("nomer", 0)), u.get("ism", ""), u.get("fakultet", ""),
                     u.get("kurs", ""), u.get("yonalish", ""),
                     ("@" + u["username"]) if u.get("username") else "",
                     int(cid) if str(cid).isdigit() else cid, u.get("manba", "bot"),
                     mahalliy(u.get("sana", ""))])
    return hdr, rows

def export_files(db, csv_ham=False):
    hdr, rows = royxat_qatorlari(db)
    xlsx_path = os.path.join(HERE, "AI_Labs_royxat.xlsx")
    write_xlsx(xlsx_path, hdr, rows, widths=[6, 32, 26, 8, 34, 18, 14, 10, 17])
    csv_path = None
    if csv_ham:                       # vergul bilan — Google Sheets / LibreOffice uchun
        csv_path = os.path.join(HERE, "AI_Labs_royxat.csv")
        with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f, lineterminator="\n")
            w.writerow(hdr)
            w.writerows(rows)
    return csv_path, xlsx_path

def royxat_matn(db):
    """Telefonda tez ko'rish uchun matnli ro'yxat (bo'laklarga bo'lingan)."""
    hdr, rows = royxat_qatorlari(db)
    if not rows:
        return ["Ro'yxat hozircha bo'sh."]
    qator = ["%d. %s — %s, %s-kurs%s" % (r[0], r[1], r[2], r[3],
             (" · " + r[5]) if r[5] else "") for r in rows]
    bolak, joriy = [], "👥 A'ZOLAR: %d ta\n\n" % len(rows)
    for q in qator:
        if len(joriy) + len(q) > 3800:
            bolak.append(joriy); joriy = ""
        joriy += q + "\n"
    bolak.append(joriy)
    return bolak

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
        db.setdefault("deleted", {})[str(chat_id)] = time.time()
        db_save(db)
        return ("🗑 Yozuvingiz o'chirildi.\nQayta ro'yxatdan o'tish: /start", KB_YOQ)
    return "Bekor qilinadigan yozuv yo'q.\nBoshlash: /start", None

def statlar(db):
    n = len(db["users"])
    fak, kurs = {}, {}
    for u in db["users"].values():
        fak[u.get("fakultet", "?")] = fak.get(u.get("fakultet", "?"), 0) + 1
        kurs[u.get("kurs", "?")] = kurs.get(u.get("kurs", "?"), 0) + 1
    q = ["📊 STATISTIKA", "Jami a'zo: %d" % n, "Jarayonda (yarim): %d" % len(db["state"]),
         baza_holati()]
    if CHANNEL:
        cnt = tg("getChatMemberCount", chat_id=CHANNEL)
        q.append("Kanal a'zolari: %s" % (cnt if cnt is not None else "noma'lum"))
    q.append("\nFakultetlar bo'yicha:")
    q += ["  • %s — %d" % (k, v) for k, v in sorted(fak.items(), key=lambda kv: -kv[1])]
    q.append("Kurslar bo'yicha:")
    q += ["  • %s — %d" % (k, v) for k, v in sorted(kurs.items(), key=lambda kv: str(kv[0]))]
    return "\n".join(q), None

def flood_guard(chat_id, db):
    if TEST or DEMO:
        return False, False
    """60 soniyada 6+ xabar → 10 daqiqalik tanaffus (spam/flood himoyasi)."""
    now = time.time()
    fl = db.setdefault("flood", {})
    cool = fl.get("cool", {})
    if cool.get(str(chat_id), 0) > now:
        return False, True          # sovutish davri: jim o'tkazamiz
    arr = [t for t in fl.setdefault(str(chat_id), []) if now - t < 60]
    arr.append(now)
    fl[str(chat_id)] = arr[-8:]
    if len(arr) >= 6:
        cool[str(chat_id)] = now + 600
        return True, False
    return False, False

def handle(msg, db):
    chat_id = msg["chat"]["id"]
    matn = (msg.get("text") or "").strip()
    if matn.startswith("/"):
        # «/start site», «/start miniapp» (deep-link) va «/buyruq@aiindeksi_bot» → toza buyruq
        bosh, _, qolgan = matn.partition(" ")
        bosh = bosh.split("@")[0]
        matn = bosh if bosh == "/start" else (bosh + (" " + qolgan if qolgan else ""))
    blok, jim = flood_guard(chat_id, db)
    if blok:
        return ("⏳ Juda tez yozyapsiz. Iltimos, 10 daqiqadan keyin "
                "qayta urinib ko'ring.", None)
    if jim:
        return None, None
    st = db["state"].get(str(chat_id))

    if matn == "/start":
        pref = ("🛡 Siz ADMIN sifatida tanildingiz: /statlar, /royxat, /export, /elon faol.\n\n"
                if chat_id in ADMIN_IDS else "")
        if chat_id not in ADMIN_IDS and not kanal_azosi(chat_id):
            return ("Avval klub kanaliga a'zo bo'ling — e'lonlar va tadbir "
                    "chaqiruvlari shu yerda:\n\n" + (kanal_url() or CHANNEL) +
                    "\n\nQo'shilib, /start ni qayta yuboring.",
                    {"inline_keyboard": [[{"text": "📣 Kanalga qo'shilish",
                                           "url": kanal_url() or "https://t.me/"}]]})
        if str(chat_id) in db["users"] and not st:
            return (pref + "Siz allaqachon ro'yxatdan o'tgansiz ✅\n"
                    "Ma'lumotlaringiz: /holat\nQayta kiritish uchun avval /bekor bilan o'chiring.", None)
        m_, k_ = (START_MATN + "\n\n" + SAVOLAR[0][1], None)
        db["state"][str(chat_id)] = {"bosqich": 0, "javoblar": {}}
        return pref + m_, k_
    if matn == "/help":
        return HELP_MATN, None
    if matn in ("/foyda", "/benefit", "/foida"):
        return FOYDA_MATN, None
    if matn in ("/maxfiylik", "/privacy"):
        return MAXFIYLIK_MATN, None
    if matn == "/holat":
        return holat(chat_id, db)
    if matn in ("/bekor", "/cancel"):
        return bekor(chat_id, db)
    if matn in ("/statlar", "/stats", "/export", "/export csv", "/royxat", "/list"):
        if chat_id not in ADMIN_IDS:
            return "⛭ Bu buyruq faqat klub administratori uchun.", None
        if matn in ("/royxat", "/list"):
            bolaklar = royxat_matn(db)
            if TOKEN:
                for b in bolaklar[:-1]:
                    send(chat_id, b)
            return bolaklar[-1], None
        if matn.startswith("/export"):
            c, x = export_files(db, csv_ham=(matn == "/export csv"))
            if TOKEN:
                send_doc(chat_id, x,
                         "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                if c:
                    send_doc(chat_id, c, "text/csv")
            return ("📎 Ro'yxat yuborildi: %d ta a'zo.\n"
                    "Excel jadvali — har bir ma'lumot alohida ustunda.\n"
                    "Telefonda tez ko'rish: /royxat · CSV kerak bo'lsa: /export csv\n%s"
                    % (len(db["users"]), baza_holati()), None)
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
        return "Ism-familiyani to'liq yozing (kamida 3 belgi).", None
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

    uname = (msg.get("from") or {}).get("username", "")
    yozuv = {"nomer": yangi_nomer(db, javoblar["ism"]), "ism": javoblar["ism"],
             "fakultet": javoblar["fakultet"], "kurs": javoblar["kurs"],
             "yonalish": javoblar["yonalish"], "username": uname, "manba": "bot",
             "sana": time.strftime("%Y-%m-%d %H:%M", time.gmtime()), "ts": time.time()}
    db["users"][str(chat_id)] = yozuv
    db.get("deleted", {}).pop(str(chat_id), None)
    del db["state"][str(chat_id)]
    db_save(db)
    for aid in ADMIN_IDS:
        send(aid, admin_xabar(yozuv, uname) + "\n📊 Jami: %d" % len(db["users"]))
    return YAKUN.format(**yozuv), kanal_kb()


# ─────────────── MINI APP RO'YXAT (WebApp initData HMAC tekshiruvi) ───────────────
def _toza(s, limit=120):
    s = re.sub(r"\s+", " ", str(s or "")).strip()
    return s.replace("<", "").replace(">", "").replace("&", "")[:limit]

def webapp_auth(init_data):
    """Telegram WebApp initData imzosini tekshiradi; haqiqiy bo'lsa user dict."""
    if not init_data or not TOKEN:
        return None
    try:
        pairs = urllib.parse.parse_qsl(init_data, keep_blank_values=True)
        d = dict(pairs)
        check = "\n".join("%s=%s" % (k, v) for k, v in sorted(pairs) if k != "hash")
        secret = hmac.new(b"WebAppData", TOKEN.encode(), hashlib.sha256).digest()
        calc = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(calc, d.get("hash", "")):
            return None
        if int(time.time()) - int(d.get("auth_date", "0")) > 3600:
            return None
        return json.loads(d.get("user", "{}"))
    except Exception:
        return None

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

        def _json(self, code, obj):
            self._send(code, json.dumps(obj, ensure_ascii=False),
                       "application/json; charset=utf-8")

        def do_POST(self):
            if self.path.split("?")[0] != "/register":
                return self._send(404, "not found", "text/plain")
            try:
                n = int(self.headers.get("Content-Length", "0"))
                if not 0 < n <= 8192:
                    raise ValueError("uzunlik")
                body = json.loads(self.rfile.read(n).decode("utf-8"))
            except Exception:
                return self._json(400, {"ok": False, "xato": "So'rov formati xato."})
            init = str(body.get("initData", ""))
            user = webapp_auth(init)
            if user is None and DEMO and init.startswith("demo:"):
                try:
                    user = {"id": int(init.split(":", 1)[1])}
                except Exception:
                    user = None
            if not user or not user.get("id"):
                return self._json(403, {"ok": False,
                    "xato": "Ro'yxatdan o'tish faqat Telegram ichida ishlaydi. Botda /start bosing."})
            uid = str(user["id"])
            ism = _toza(body.get("ism"))
            fak = _toza(body.get("fakultet"))
            boshqa = bool(body.get("boshqa"))
            kurs = _toza(body.get("kurs"), 20)
            yon = _toza(body.get("yonalish"))
            if len(ism) < 3:
                return self._json(400, {"ok": False, "xato": "Ism-familiyani to'liq yozing (kamida 3 belgi)."})
            if boshqa:
                if len(fak) < 3:
                    return self._json(400, {"ok": False, "xato": "Fakultet nomini yozing."})
            elif fak not in FAKULTETLAR:
                return self._json(400, {"ok": False, "xato": "Fakultetni ro'yxatdan tanlang."})
            if kurs not in KURSLAR:
                return self._json(400, {"ok": False, "xato": "Kursni tanlang: 1, 2, 3, 4 yoki Magistratura."})
            if len(yon) < 3:
                return self._json(400, {"ok": False, "xato": "Ta'lim yo'nalishini yozing."})
            if not body.get("rozilik"):
                return self._json(400, {"ok": False, "xato": "Rozilik belgisi kerak (Nizom, 8-bo'lim)."})
            db = get_db()
            with DB_LOCK:
                if uid in db["users"]:
                    return self._json(200, {"ok": False,
                        "xato": "Siz allaqachon ro'yxatdan o'tgansiz (№ %s). Botda /holat bilan ko'rasiz."
                                % db["users"][uid].get("nomer", "?")})
                uname = _toza(user.get("username", ""), 40)
                yozuv = {"nomer": yangi_nomer(db, ism), "ism": ism, "fakultet": fak,
                         "kurs": kurs, "yonalish": yon, "username": uname,
                         "sana": time.strftime("%Y-%m-%d %H:%M", time.gmtime()),
                         "ts": time.time(), "manba": "miniapp"}
                db["users"][uid] = yozuv
                db.get("deleted", {}).pop(uid, None)
                db["state"].pop(uid, None)
                db_save(db)
            javob = {"ok": True, "nomer": yozuv["nomer"], "xabar": YAKUN.format(**yozuv)}
            self._json(200, javob)          # avval javob — keyin bildirishnomalar
            for aid in ADMIN_IDS:
                send(aid, admin_xabar(yozuv, uname, " (mini app)") +
                     "\n📊 Jami: %d" % len(db["users"]))
            send(uid, YAKUN.format(**yozuv), kanal_kb())

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
    db = _bo_sh_db()
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
    _, x = export_files(db)
    assert os.path.exists(x), "XLSX yaratilmadi!"
    with zipfile.ZipFile(x) as z:
        sh = z.read("xl/worksheets/sheet1.xml").decode()
        assert "xl/styles.xml" in z.namelist() and sh.count("<row ") == 2, "XLSX buzilgan"
    c, _ = export_files(db, csv_ham=True)
    lines = open(c, encoding="utf-8-sig").read().strip().split("\n")
    assert len(lines) == 2 and lines[0].count(",") == 8, "CSV xato"
    # birlashtirish: o'chirilgan yozuv tirilmasin, yangi yozuv yo'qolmasin
    a = {"users": {"1": {"nomer": 1, "ts": 10}}, "deleted": {"2": 50}, "counter": 1, "state": {}}
    b = {"users": {"2": {"nomer": 2, "ts": 20}, "3": {"nomer": 3, "ts": 30}}, "counter": 3}
    m = db_merge(a, b)
    assert set(m["users"]) == {"1", "3"} and m["counter"] == 3, m
    print("\n✅ TEST O'TDI: ro'yxat (Boshqa→erkin matn) → saqlash → holat → "
          "statistika → XLSX (uslubli) + CSV (vergul) → birlashtirish.")

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
