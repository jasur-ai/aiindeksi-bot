#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
════════════════════════════════════════════════════════════════════════════
 Raqamli Tadqiqot klubi — Telegram ro'yxatdan o'tish boti   (@aiindeksi_bot)   v3.0
 «Raqamli o'lchov va sun'iy intellekt monitoringi» klubi (ADRL / AAI-UZ)
 Toshkent davlat iqtisodiyot universiteti
════════════════════════════════════════════════════════════════════════════

 v3.0: TADBIRLAR VA ROLLAR —
   • kanalda #tadbir heshtegli post → barcha a'zolarga «✅ Boraman» tugmali xabar (taxminiy son);
   • /tadbir_boshlash N → admin QR ekrani (/qr/N): QR har 30 soniyada yangilanadi, ≤90 soniya amal qiladi;
     skanerlagan — davomatda; shu chatda tadbir suratlarini yuboradi → yopiq arxiv guruhi (har tadbir —
     alohida mavzu, havola hech kimga berilmaydi, qabul yakundan 1 soat o'tib yopiladi);
   • rollar — faqat ichki boshqaruv (admin): /rollar, /rol N rol, /jamoa. Ommaga ko'rsatilmaydi (v3.1).
 v2.2: MANBA O'LCHOVI — «/start KOD» (deep-link) kodi «Manba» ustuniga «bot:KOD» bo'lib yoziladi;
   /statlar manbalar kesimini ko'rsatadi (27-hujjat, 5-bo'lim).
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
import html
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
    "Bu — «Raqamli Tadqiqot» klubi (TDIU) rasmiy ro'yxatdan o'tish boti.\n"
    "Klub sun'iy intellektning O'zbekistonda qayerda ISHLAYOTGANINI va "
    "qayerda ISHLAMAYOTGANINI ochiq ma'lumotlar asosida o'lchaydi.\n\n"
    "📣 Kanal: t.me/Raqamli_tadqiqot — barcha e'lonlar va tadbir "
    "chaqiruvlari shu yerda.\n"
    "🌐 Sayt: raqamlitadqiqot.pages.dev — pilot natijasi, kalkulyator, test.\n\n"
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
    "Har bir tadbir e'lon qilinganda shu bot orqali xabar beramiz — «✅ Boraman» "
    "tugmasi bilan. Klubga xush kelibsiz! 🎉\n\n"
    "Ma'lumotlaringizni ko'rish: /holat   ·   O'chirish: /bekor"
)
FOYDA_MATN = (
    "🌱 Klub nima beradi? — 6 ta halol javob\n\n"
    "1️⃣ XABARDORLIK: O'zbekistonda sun'iy intellektning real manzarasini birinchilardan "
    "bo'lib ko'rasiz: ochiq ma'lumotlar, haftalik digest va sikl hisobotlari.\n"
    "2️⃣ JAMOA: turli fakultetlardan fikrdoshlar, mentor va o'zaro tekshiruv (peer-review) "
    "madaniyati. Birinchi kurs talabasi ham o'z o'rnini topadi.\n"
    "3️⃣ RIVOJLANISH: darsdagi bilimni real loyihada mustahkamlaysiz — manba qidirish va "
    "tekshirish, indeks qurish, Excel/Python, ilmiy yozish va himoya.\n"
    "4️⃣ HISSA: bo'sh katakni to'ldirsangiz, indeksga yangi tekshirilgan dalil qo'shiladi. "
    "Real hissa hisobotda nom bilan ko'rsatiladi.\n"
    "5️⃣ E'TIROF: bajarilgan ish tasdiqlovchi hujjatda aniq yoziladi — kim, nima qilgani; "
    "hujjat har bir ishtirokchiga beriladi.\n"
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
    "5. Tadbirlar: QR davomatda faqat qatnashganingiz qayd etiladi; yuborgan suratlaringiz yopiq "
    "arxivga tushadi va faqat klub foto-hisobotida ishlatilishi mumkin. Suratingiz ishlatilmasin desangiz — "
    "botga yozing, olib tashlanadi.\n"
    "6. Hodisa bo'lsa (token/database ochilsa): 24 soat ichida kanalda ochiq "
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
    "\n"
    "Klub faqat OCHIQ manbalar bilan ishlaydi. A'zolik BEPUL.\n"
    "📣 Kanal: t.me/Raqamli_tadqiqot\n"
    "🌐 Sayt: raqamlitadqiqot.pages.dev"
)

# ─────────────────────────── DB ───────────────────────────
# Ishchi nusxa xotirada + lokal fayl; doimiy nusxa — yopiq GitHub ombori (GH_REPO/db.json).
# Qoidalar: (1) GitHub'dan o'qilmaguncha unga HECH QACHON yozilmaydi (bo'sh baza bilan
# ustiga yozib yuborish xavfi yo'q); (2) sha to'qnashuvi bo'lsa — birlashtirib qayta yoziladi;
# (3) /bekor bilan o'chirilganlar "deleted" ro'yxatida turadi, birlashtirishda tirilmaydi.
PERSIST = ("users", "state", "counter", "deleted", "events", "ev_counter", "roles", "rol_ariza", "cfg")
REF = {}   # chat_id → (deep-link kodi, vaqt): «/start afisha» → manba «bot:afisha» (faqat xotirada, 24 soat)

def ref_qoy(chat_id, kod):
    kod = re.sub(r"[^a-z0-9_]", "", (kod or "").lower())[:24]
    if kod:
        if len(REF) > 5000:
            REF.clear()
        REF[str(chat_id)] = (kod, time.time())

def ref_ol(chat_id, asos):
    kod, ts = REF.pop(str(chat_id), ("", 0))
    return asos + ":" + kod if kod and time.time() - ts < 86400 else asos
GH = {"sha": None, "synced": False, "last_ok": None, "err": "", "last_body": None}
DB_LOCK = threading.RLock()
_DB_REF = {"db": None}
_DIRTY = threading.Event()

def _bo_sh_db():
    return {"users": {}, "state": {}, "counter": 0, "deleted": {},
            "events": {}, "ev_counter": 0, "roles": {}, "rol_ariza": {}, "cfg": {}}

def _norm(db):
    for k, v in _bo_sh_db().items():
        db.setdefault(k, v)
    return db

def _gh_req(method, url, data=None):
    req = urllib.request.Request(url, method=method,
        data=json.dumps(data).encode("utf-8") if data is not None else None,
        headers={"Authorization": "Bearer " + GH_TOKEN, "User-Agent": "raqamlitadqiqot-bot",
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
    local["events"] = _merge_events(local.get("events", {}), remote.get("events", {}))
    local["ev_counter"] = max([int(local.get("ev_counter", 0)), int(remote.get("ev_counter", 0))] +
                              [int(k) for k in local["events"] if str(k).isdigit()])
    for k in ("roles", "rol_ariza", "cfg"):
        d = dict(remote.get(k, {})); d.update(local.get(k, {})); local[k] = d
    return local

def _merge_events(L, R):
    """Tadbirlar: holat faqat oldinga (e'lon→faol→yakun); yozilish/davomat/suratlar birlashadi."""
    out = dict(R or {})
    for k, e in (L or {}).items():
        r = out.get(k)
        if not r:
            out[k] = e
            continue
        m = dict(e if float(e.get("upd", 0)) >= float(r.get("upd", 0)) else r)
        m["holat"] = max(e.get("holat", "e'lon"), r.get("holat", "e'lon"), key=lambda h: {"e'lon": 0, "faol": 1, "yakun": 2}.get(h, 0))
        for f in ("boshlandi", "yakunlandi", "upd"):
            m[f] = max(float(e.get(f) or 0), float(r.get(f) or 0))
        rs = dict(r.get("rsvp", {}))
        for u, v in e.get("rsvp", {}).items():
            if u not in rs or abs(float(v)) >= abs(float(rs[u])):
                rs[u] = v
        m["rsvp"] = rs
        kd = dict(r.get("keldi", {})); kd.update(e.get("keldi", {})); m["keldi"] = kd
        sd = dict(r.get("suratlar", {}))
        for u, v in e.get("suratlar", {}).items():
            sd[u] = max(int(v), int(sd.get(u, 0)))
        m["suratlar"] = sd
        out[k] = m
    return out

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
    xlsx_path = os.path.join(HERE, "Raqamli_Tadqiqot_royxat.xlsx")
    write_xlsx(xlsx_path, hdr, rows, widths=[6, 32, 26, 8, 34, 18, 14, 16, 17])
    csv_path = None
    if csv_ham:                       # vergul bilan — Google Sheets / LibreOffice uchun
        csv_path = os.path.join(HERE, "Raqamli_Tadqiqot_royxat.csv")
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
    rl = [ROL[k]["nom"] for k in db.get("roles", {}).get(str(chat_id), []) if k in ROL]
    return YAKUN.format(**u) + "\n\n(holat: ro'yxatdan o'tgan%s)" % (
        "; rol: " + ", ".join(rl) if rl else ""), None

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
    fak, kurs, manba = {}, {}, {}
    for u in db["users"].values():
        manba[u.get("manba", "bot")] = manba.get(u.get("manba", "bot"), 0) + 1
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
    q.append("Manba bo'yicha (deep-link kodi):")
    q += ["  • %s — %d" % (k, v) for k, v in sorted(manba.items(), key=lambda kv: -kv[1])]
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
        deep = qolgan.strip() if bosh == "/start" else ""
        if deep and not deep.startswith(("ev", "rsvp", "rollar")):
            ref_qoy(chat_id, deep)
        matn = bosh if bosh == "/start" else (bosh + (" " + qolgan if qolgan else ""))
    else:
        deep = ""
    blok, jim = flood_guard(chat_id, db)
    if blok:
        return ("⏳ Juda tez yozyapsiz. Iltimos, 10 daqiqadan keyin "
                "qayta urinib ko'ring.", None)
    if jim:
        return None, None
    st = db["state"].get(str(chat_id))

    if matn == "/start" and deep.startswith("ev"):          # tadbir QR davomati (kanal to'sig'isiz)
        return tadbir_checkin(chat_id, deep, msg, db)
    if matn == "/start" and deep.startswith("rsvp"):        # kanaldagi «Boraman» tugmasi
        ev = db["events"].get(deep[4:])
        if not ev or ev["holat"] == "yakun":
            return "Bu tadbir yakunlangan yoki topilmadi. Yangi tadbirlar: " + (kanal_url() or CHANNEL), None
        rsvp_qoy(db, ev, chat_id, True)
        return ("✅ «%s» ga yozildingiz (jami %d kishi). Tadbir kuni kirishda QR orqali davomat olinadi.%s"
                % (esc(ev["nom"]), rsvp_soni(ev), "" if str(chat_id) in db["users"] else
                   "\n\nKlub a'zosi bo'lish uchun: /start"), rsvp_kb(ev, chat_id))
    if matn == "/rollar" and tadbir_ruxsat(chat_id, db):      # rollar — faqat ichki boshqaruv
        return rollar_matn(), rollar_kb()
    if matn.startswith(("/tadbirlar", "/tadbir_yangi", "/tadbir_boshlash", "/tadbir_yakun")) or \
            matn == "/tadbir" or matn.startswith("/tadbir "):
        return tadbir_buyruq(chat_id, matn, db)
    if matn == "/jamoa" or matn.startswith("/rol "):
        if not tadbir_ruxsat(chat_id, db) or (matn.startswith("/rol ") and chat_id not in ADMIN_IDS
                                               and "koordinator" not in db.get("roles", {}).get(str(chat_id), [])):
            return "⛭ Bu buyruq faqat administrator uchun.", None
        return (jamoa_matn(db), None) if matn == "/jamoa" else rol_tayinla(matn, db)

    if matn == "/start":
        pref = ("🛡 Siz ADMIN sifatida tanildingiz: /statlar, /royxat, /export, /elon, /tadbirlar, /jamoa faol.\n\n"
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
             "yonalish": javoblar["yonalish"], "username": uname, "manba": ref_ol(chat_id, "bot"),
             "sana": time.strftime("%Y-%m-%d %H:%M", time.gmtime()), "ts": time.time()}
    db["users"][str(chat_id)] = yozuv
    db.get("deleted", {}).pop(str(chat_id), None)
    del db["state"][str(chat_id)]
    db_save(db)
    for aid in ADMIN_IDS:
        send(aid, admin_xabar(yozuv, uname) + "\n📊 Jami: %d" % len(db["users"]))
    return YAKUN.format(**yozuv), kanal_kb()


# ─────────────────────────── TADBIRLAR (v3.0) ───────────────────────────
# Oqim: kanalda #tadbir heshtegli post → bot tadbirni yaratadi → barcha a'zolarga «✅ Boraman» tugmasi bilan
# xabar (taxminiy son). Tadbir kuni: /tadbir_boshlash N → admin ekranida har 30 soniyada yangilanadigan QR
# (≤90 soniya amal qiladi, skrinshot keyin ishlamaydi) → skanerlagan odam davomatdan o'tadi va SHU CHATDA
# tadbir suratlarini yuboradi. Suratlar yopiq arxiv guruhiga (har tadbir — alohida mavzu) nusxalanadi; hech
# kimga havola berilmaydi; qabul tadbir yakunidan 1 soat o'tib yopiladi — keyin qayta kirib bo'lmaydi.
BOT_USERNAME = os.environ.get("AIINDEKSI_BOT_USERNAME", "aiindeksi_bot").lstrip("@")
SELF_URL = os.environ.get("SELF_URL", "").strip().rstrip("/") or "https://aiindeksi-bot.onrender.com"
QR_OYNA = 30            # QR har 30 soniyada yangilanadi
QR_AMAL = 3             # joriy + oldingi 2 oyna → ≤90 soniya amal qiladi
SURAT_KECH = 3600       # tadbir yakunidan keyin 1 soat ichida surat qabul qilinadi
SURAT_LIMIT = 30        # bir kishidan bir tadbirga
AUTO_YAKUN = 8 * 3600   # yakunlash unutilsa — boshlanganidan 8 soat o'tib avtomatik yopiladi
TADBIR_TAG = "#tadbir"
TADBIR_ROLLAR = ("koordinator", "orinbosar", "kotib", "tashkiliy")   # tadbir buyruqlari ruxsati
HOLATLAR = {"e'lon": 0, "faol": 1, "yakun": 2}
_MEDIA_GURUH = {}       # media_group_id → vaqt (albomga bitta javob)

def esc(s):
    return html.escape(str(s or ""), quote=False)

def _hm(*parts):
    return hmac.new((TOKEN or "sinov-kaliti").encode(), "|".join(str(p) for p in parts).encode(),
                    hashlib.sha256).hexdigest()

def qr_token(ev, w=None):
    w = int(time.time() // QR_OYNA) if w is None else w
    return _hm("qr", ev["id"], ev.get("sir", ""), w)[:10]

def qr_tekshir(ev, tok):
    w = int(time.time() // QR_OYNA)
    return any(hmac.compare_digest(qr_token(ev, w - i), tok) for i in range(QR_AMAL))

def qr_admin_kalit(eid):
    return _hm("qr-admin", eid)[:20]

def qr_link(ev):
    return "https://t.me/%s?start=ev%s_%s" % (BOT_USERNAME, ev["id"], qr_token(ev))

def qr_sahifa_url(ev):
    return "%s/qr/%s?k=%s" % (SELF_URL, ev["id"], qr_admin_kalit(ev["id"]))

def rsvp_soni(ev):
    return sum(1 for v in ev.get("rsvp", {}).values() if float(v) > 0)

def tadbir_ruxsat(uid, db):
    if uid in ADMIN_IDS:
        return True
    return any(r in TADBIR_ROLLAR for r in db.get("roles", {}).get(str(uid), []))

def _avto_yakun(db):
    now = time.time()
    for ev in db["events"].values():
        if ev["holat"] == "faol" and ev.get("boshlandi") and now - ev["boshlandi"] > AUTO_YAKUN:
            ev["holat"], ev["yakunlandi"], ev["upd"] = "yakun", now, now

def _tg1(method, **kw):
    """Bitta urinish (ommaviy xabar uchun): (natija, http_kod, retry_after). Bloklagan a'zoda qayta urinmaydi."""
    if not TOKEN:
        return None, 0, None
    req = urllib.request.Request("%s/bot%s/%s" % (API, TOKEN, method),
                                 data=urllib.parse.urlencode(kw).encode("utf-8"))
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode("utf-8")).get("result"), 200, None
    except urllib.error.HTTPError as e:
        try:
            ra = json.loads(e.read().decode("utf-8")).get("parameters", {}).get("retry_after")
        except Exception:                                # noqa: BLE001
            ra = None
        return None, e.code, ra
    except (urllib.error.URLError, OSError) as e:
        return None, 0, None

def tadbir_yarat(db, nom, matn="", post=None):
    with DB_LOCK:
        db["ev_counter"] = int(db.get("ev_counter", 0)) + 1
        eid = str(db["ev_counter"])
        now = time.time()
        ev = {"id": eid, "nom": re.sub(r"\s+", " ", nom).strip()[:120] or ("Tadbir #" + eid),
              "matn": (matn or "")[:1500], "post": post, "holat": "e'lon", "yaratildi": now,
              "boshlandi": 0, "yakunlandi": 0, "rsvp": {}, "keldi": {}, "suratlar": {},
              "sir": os.urandom(8).hex(), "mavzu": None, "upd": now}
        db["events"][eid] = ev
    arx = arxiv_chat(db)
    if arx and TOKEN:                                    # yopiq arxivda shu tadbir uchun alohida mavzu
        r = tg("createForumTopic", chat_id=arx, name=("#%s · %s" % (eid, ev["nom"]))[:120])
        if r and r.get("message_thread_id"):
            ev["mavzu"] = r["message_thread_id"]
    db_save(db)
    return ev

def arxiv_chat(db):
    return os.environ.get("AIINDEKSI_ARXIV", "").strip() or db.get("cfg", {}).get("arxiv")

def rsvp_kb(ev, uid=None):
    n = rsvp_soni(ev)
    meniki = uid is not None and float(ev.get("rsvp", {}).get(str(uid), 0)) > 0
    t = ("✔️ Yozildingiz · %d  (bekor qilish)" % n) if meniki else ("✅ Boraman · %d" % n)
    rows = [[{"text": t, "callback_data": "rsvp:%s" % ev["id"]}]]
    if ev.get("post") and kanal_url():
        rows.append([{"text": "📣 Kanaldagi e'lon", "url": "%s/%s" % (kanal_url(), ev["post"])}])
    return {"inline_keyboard": rows}

def tadbir_xabar_matn(ev):
    tana = "\n".join(ev.get("matn", "").replace(TADBIR_TAG, "").strip().split("\n")[1:]).strip()
    if len(tana) > 700:
        tana = tana[:700].rsplit(" ", 1)[0] + " …"
    return ("📅 <b>Yangi tadbir</b>\n\n<b>%s</b>\n\n%s%s"
            "Borasizmi? Tugmani bosing — joy va tarqatma soni shunga qarab tayyorlanadi. "
            "Tadbir kuni kirishda ekrandagi QR orqali davomat olinadi.") % (
        esc(ev["nom"]), esc(tana), "\n\n" if tana else "")

def tadbir_tarqat(db, ev):
    """Barcha a'zolarga e'lon (≈20 xabar/soniya, 429 da kutadi). TEST'da sinxron."""
    def ish():
        with DB_LOCK:
            ids = list(db["users"].keys())
        ok = xato = 0
        matn, kb = tadbir_xabar_matn(ev), json.dumps(rsvp_kb(ev), ensure_ascii=False)
        for uid in ids:
            r = None
            for _ in range(3):
                r, kod, ra = _tg1("sendMessage", chat_id=uid, text=matn, parse_mode="HTML",
                                  disable_web_page_preview="true", reply_markup=kb)
                if kod == 429 and ra:
                    time.sleep(int(ra) + 1)
                    continue
                break
            ok, xato = (ok + 1, xato) if r else (ok, xato + 1)
            time.sleep(0.05)
        with DB_LOCK:
            ev["tarqatildi"] = {"ok": ok, "xato": xato, "ts": time.time()}
            ev["upd"] = time.time()
        db_save(db)
        for aid in ADMIN_IDS:
            send(aid, "📨 Tadbir #%s e'loni %d ta a'zoga yuborildi%s.\nKuzatish: /tadbir %s" % (
                ev["id"], ok, (" (%d tasiga yetmadi — botni to'xtatgan)" % xato) if xato else "", ev["id"]))
    if TEST or DEMO or not TOKEN:
        ish()
    else:
        threading.Thread(target=ish, daemon=True).start()

def kanal_post(post, db):
    """Kanaldagi #tadbir post → tadbir + tarqatish + postga «Boraman» tugmasi."""
    chat = post.get("chat") or {}
    if CHANNEL.startswith("@"):
        if (chat.get("username") or "").lower() != CHANNEL.lstrip("@").lower():
            return None
    elif CHANNEL and str(chat.get("id")) != CHANNEL:
        return None
    matn = post.get("text") or post.get("caption") or ""
    if TADBIR_TAG not in matn.lower():
        return None
    if any(e.get("post") == post.get("message_id") for e in db["events"].values()):
        return None
    qator = [q for q in matn.split("\n") if q.strip()]
    nom = re.sub(r"#\w+", "", qator[0] if qator else "").strip(" -—:·") if qator else ""
    ev = tadbir_yarat(db, nom, matn, post.get("message_id"))
    if TOKEN and chat.get("id"):
        tg("editMessageReplyMarkup", chat_id=chat["id"], message_id=post["message_id"],
           reply_markup=json.dumps({"inline_keyboard": [[{
               "text": "✅ Boraman — botda yozilish",
               "url": "https://t.me/%s?start=rsvp%s" % (BOT_USERNAME, ev["id"])}]]}, ensure_ascii=False))
    tadbir_tarqat(db, ev)
    return ev

def rsvp_qoy(db, ev, uid, yoq=None):
    """yoq=None — almashlash; True — yozish; False — bekor. Bekor qilish manfiy vaqt bilan saqlanadi (birlashtirishda tirilmaydi)."""
    with DB_LOCK:
        hozir = float(ev["rsvp"].get(str(uid), 0)) > 0
        yangi = (not hozir) if yoq is None else yoq
        ev["rsvp"][str(uid)] = time.time() if yangi else -time.time()
        ev["upd"] = time.time()
    db_save(db)
    return yangi

def tadbir_checkin(chat_id, arg, msg, db):
    m_ = re.match(r"ev(\d+)_([0-9a-f]{10})$", arg)
    ev = db["events"].get(m_.group(1)) if m_ else None
    if not ev:
        return "QR kod tanilmadi. Tadbirdagi ekranda ko'rsatilgan QR ni skanerlang.", None
    _avto_yakun(db)
    if ev["holat"] != "faol":
        return "«%s» hozir faol emas — davomat faqat tadbir paytida olinadi." % esc(ev["nom"]), None
    if not qr_tekshir(ev, m_.group(2)):
        return ("⏱ Bu QR eskirgan — u har 30 soniyada yangilanadi. Ekrandagi QR ni qayta skanerlang."), None
    uid = str(chat_id)
    u = db["users"].get(uid)
    with DB_LOCK:
        yangi = uid not in ev["keldi"]
        if yangi:
            ev["keldi"][uid] = {"ts": time.time(), "azo": bool(u),
                                "ism": (u or {}).get("ism") or _toza((msg.get("from") or {}).get("first_name", ""), 60)}
            if float(ev["rsvp"].get(uid, 0)) <= 0:
                ev["rsvp"][uid] = time.time()
        ev["upd"] = time.time()
    db_save(db)
    q = [("✅ Davomat qayd etildi: <b>%s</b>" if yangi else "Siz allaqachon qayd etilgansiz: <b>%s</b>") % esc(ev["nom"]),
         "📸 Tadbir suratlarini SHU CHATGA yuboring — ular faqat shu tadbirning yopiq arxiviga tushadi "
         "(ko'pi bilan %d ta). Qabul tadbir yakunidan 1 soat o'tib yopiladi." % SURAT_LIMIT]
    if not u:
        q.append("Siz hali klub a'zosi emassiz — 40 soniyada ro'yxatdan o'ting: /start")
    return "\n\n".join(q), None

def surat_qabul(msg, db):
    """Davomatdan o'tgan qatnashchining surat/videosini shu tadbir arxiviga nusxalaydi. Javob matni yoki None."""
    uid = str(msg["chat"]["id"])
    now = time.time()
    _avto_yakun(db)
    evs = [e for e in db["events"].values() if uid in e.get("keldi", {}) and
           (e["holat"] == "faol" or (e["holat"] == "yakun" and now - float(e.get("yakunlandi") or 0) < SURAT_KECH))]
    mg = msg.get("media_group_id")
    birinchi = True
    if mg:
        birinchi = mg not in _MEDIA_GURUH
        _MEDIA_GURUH[mg] = now
        if len(_MEDIA_GURUH) > 500:
            for k in [k for k, t in _MEDIA_GURUH.items() if now - t > 600]:
                _MEDIA_GURUH.pop(k, None)
    if not evs:
        return ("📷 Surat qabul qilinmadi: suratlar faqat tadbirda QR orqali davomatdan o'tganlardan va "
                "faqat tadbir davomida (yakunidan 1 soatgacha) qabul qilinadi.") if birinchi else None
    ev = max(evs, key=lambda e: e["keldi"][uid]["ts"])
    n = int(ev["suratlar"].get(uid, 0))
    if n >= SURAT_LIMIT:
        return ("Bir tadbirga ko'pi bilan %d ta surat qabul qilinadi." % SURAT_LIMIT) if birinchi else None
    arx = arxiv_chat(db) or (sorted(ADMIN_IDS)[0] if ADMIN_IDS else None)
    u = db["users"].get(uid) or {}
    imzo = "#tadbir%s · %s\n👤 %s%s" % (ev["id"], ev["nom"][:60], u.get("ism") or ev["keldi"][uid].get("ism", ""),
                                        (" · №%s" % u["nomer"]) if u.get("nomer") else " · mehmon")
    kw = {"chat_id": arx, "from_chat_id": uid, "message_id": msg["message_id"], "caption": imzo}
    if ev.get("mavzu"):
        kw["message_thread_id"] = ev["mavzu"]
    r = tg("copyMessage", **kw) if (arx and TOKEN) else None
    if not r:
        return "⚠️ Saqlanmadi. Birozdan keyin qayta yuboring." if birinchi else None
    with DB_LOCK:
        ev["suratlar"][uid] = n + 1
        ev["upd"] = now
    db_save(db)
    return ("✅ Qabul qilindi — «%s» arxivi. Yana yuborishingiz mumkin." % esc(ev["nom"])) if birinchi else None

def tadbir_tavsif(ev, toliq=False):
    keldi = ev.get("keldi", {})
    azo = sum(1 for v in keldi.values() if v.get("azo"))
    r = rsvp_soni(ev)
    q = ["<b>#%s · %s</b>" % (ev["id"], esc(ev["nom"])),
         "Holat: %s · ✅ yozilgan: %d · 🎟 kelgan: %d (a'zo %d, mehmon %d)%s · 📸 surat: %d" % (
             ev["holat"], r, len(keldi), azo, len(keldi) - azo,
             (" · kelish %d%%" % round(100 * len(keldi) / r)) if r else "", sum(int(x) for x in ev.get("suratlar", {}).values()))]
    if toliq and keldi:
        q.append("\nKelganlar (F-05 davomat uchun):")
        q += ["%d. %s" % (i, esc(v.get("ism", "?"))) for i, v in
              enumerate(sorted(keldi.values(), key=lambda v: v.get("ts", 0)), 1)]
    return "\n".join(q)

def tadbir_buyruq(chat_id, matn, db):
    """/tadbirlar · /tadbir N · /tadbir_yangi NOM · /tadbir_boshlash N · /tadbir_yakun N"""
    if not tadbir_ruxsat(chat_id, db):
        return "⛭ Bu buyruq faqat administrator uchun.", None
    _avto_yakun(db)
    bosh, _, arg = matn.partition(" ")
    arg = arg.strip()
    if bosh == "/tadbirlar":
        if not db["events"]:
            return ("Hali tadbir yo'q. Kanalga #tadbir heshtegi bilan post joylang yoki /tadbir_yangi Nomi.", None)
        evs = sorted(db["events"].values(), key=lambda e: -int(e["id"]))[:10]
        return "📅 TADBIRLAR (oxirgi 10)\n\n" + "\n\n".join(tadbir_tavsif(e) for e in evs) + \
               "\n\nBatafsil: /tadbir N · Boshlash: /tadbir_boshlash N · Yakun: /tadbir_yakun N", None
    if bosh == "/tadbir_yangi":
        if len(arg) < 3:
            return "Foydalanish: /tadbir_yangi Tadbir nomi (sana, joy)", None
        ev = tadbir_yarat(db, arg.split("\n")[0], arg)
        tadbir_tarqat(db, ev)
        return "✅ Tadbir #%s yaratildi va a'zolarga yuborilmoqda.\nTadbir kuni: /tadbir_boshlash %s" % (ev["id"], ev["id"]), None
    ev = db["events"].get(re.sub(r"\D", "", arg))
    if not ev:
        return "Tadbir raqamini yozing, masalan: %s 1 (ro'yxat: /tadbirlar)" % bosh, None
    if bosh == "/tadbir":
        return tadbir_tavsif(ev, toliq=True), None
    if bosh == "/tadbir_boshlash":
        with DB_LOCK:
            if ev["holat"] != "faol":
                ev["holat"], ev["boshlandi"], ev["upd"] = "faol", time.time(), time.time()
        db_save(db)
        return ("🟢 «%s» boshlandi. QR ekranini oching (proyektor yoki planshet) — QR har 30 soniyada "
                "yangilanadi, skrinshot 90 soniyadan keyin ishlamaydi. Havolani hech kimga bermang.\n\n"
                "Yakunlash: /tadbir_yakun %s" % (esc(ev["nom"]), ev["id"]),
                {"inline_keyboard": [[{"text": "📱 QR ekranini ochish", "url": qr_sahifa_url(ev)}]]})
    if bosh == "/tadbir_yakun":
        with DB_LOCK:
            if ev["holat"] != "yakun":
                ev["holat"], ev["yakunlandi"], ev["upd"] = "yakun", time.time(), time.time()
        db_save(db)
        return "🏁 Yakunlandi. Suratlar yana 1 soat qabul qilinadi, keyin yopiladi.\n\n" + tadbir_tavsif(ev, True), None
    return "Bunday buyruq yo'q. /tadbirlar", None

# ─────────────────────────── ROLLAR (rollar.json — yagona manba) ───────────────────────────
def _rollar_yukla():
    try:
        with open(os.path.join(HERE, "rollar.json"), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        log.warning("rollar.json o'qilmadi")
        return {"rollar": [], "guruhlar": [], "komissiya": {}}
ROLLAR = _rollar_yukla()
ROL = {r["key"]: r for r in ROLLAR.get("rollar", [])}

def _soni(r):
    return str(r["min"]) if r["min"] == r["max"] else "%d–%d" % (r["min"], r["max"])

def rollar_matn():
    q = ["🧭 <b>KLUBDAGI ROLLAR</b> — %d ta" % len(ROL), ""]
    for g in ROLLAR.get("guruhlar", []):
        q.append("<b>%s</b> — %s" % (esc(g["nom"]).upper(), esc(g["izoh"])))
        for r in ROLLAR["rollar"]:
            if r["guruh"] == g["key"]:
                q.append("%s %s — %s kishi · %s" % ("⭐" if r.get("ovoz") else "•", esc(r["nom"]), _soni(r), esc(r["qisqa"])))
        q.append("")
    k = ROLLAR.get("komissiya", {})
    if k:
        q.append("⭐ <b>%s</b>: %s" % (esc(k.get("nom", "")), esc(k.get("qoida", ""))))
    q.append("\nRolni tanlang — talablar va nima berishimizni ko'rasiz, ariza bir tugma bilan:")
    return "\n".join(q)

def rollar_kb():
    t = [r for r in ROLLAR.get("rollar", []) if r.get("ariza")]
    rows = [[{"text": ("⭐ " if r.get("ovoz") else "") + r["nom"], "callback_data": "rol:" + r["key"]}
             for r in t[i:i + 2]] for i in range(0, len(t), 2)]
    return {"inline_keyboard": rows}

def rol_karta(r):
    q = ["%s<b>%s</b> — %s kishi%s" % ("⭐ " if r.get("ovoz") else "", esc(r["nom"]), _soni(r),
                                       " · startdan majburiy" if r.get("start") else " · keyin saylanadi"),
         esc(r["qisqa"]), "",
         "<b>Vazifalar:</b>"] + ["• " + esc(v) for v in r["vazifalar"]] + [
         "", "<b>Minimal talab:</b> " + esc(r["talab_min"]),
         "<b>Ideal nomzod:</b> " + esc(r["talab_max"]),
         "<b>Vaqt:</b> " + esc(r["vaqt"]) + " · <b>Daraja:</b> " + esc(r["daraja"]),
         "", "<b>Nima beramiz:</b>"] + ["• " + esc(b) for b in r["beramiz"]]
    if r.get("ovoz"):
        q += ["", "⭐ Metodologiya komissiyasi a'zosi — hisobot nashri uchun ovoz beradi (Nizom 4.7)."]
    return "\n".join(q)

def rol_callback(uid, data, db):
    """(javob_toast, yangi_xabar_matn, kb)"""
    tur, _, key = data.partition(":")
    r = ROL.get(key)
    if not r:
        return "Rol topilmadi.", None, None
    if tur == "rol":
        kb = {"inline_keyboard": [[{"text": "📝 Ariza berish", "callback_data": "ariza:" + key}],
                                  [{"text": "⬅️ Barcha rollar", "callback_data": "rollar:"}]]} if r.get("ariza") else None
        return "", rol_karta(r), kb
    if str(uid) not in db["users"]:
        return "Avval ro'yxatdan o'ting: /start", "Rolga ariza berish uchun avval ro'yxatdan o'ting: /start", None
    u = db["users"][str(uid)]
    with DB_LOCK:
        db.setdefault("rol_ariza", {})[str(uid)] = {"rol": key, "ts": time.time(), "holat": "kutilmoqda"}
    db_save(db)
    for aid in ADMIN_IDS:
        send(aid, "🎯 Rol arizasi: №%s %s (%s · %s-kurs) → <b>%s</b>\nTayinlash: /rol %s %s\nJamoa: /jamoa" % (
            u["nomer"], esc(u["ism"]), esc(u["fakultet"]), esc(u["kurs"]), esc(r["nom"]), u["nomer"], key))
    return "Ariza yuborildi ✅", ("📝 «%s» roliga arizangiz Koordinatorga yuborildi. 3 ish kuni ichida javob "
                                 "beriladi (startda suhbat yoki kalibrovka sinovi bo'lishi mumkin)." % esc(r["nom"])), None

def rol_tayinla(matn, db):
    """/rol <nomer> <rol_key|->"""
    p = matn.split()
    if len(p) != 3:
        return ("Foydalanish: /rol <a'zo raqami> <rol>\nMasalan: /rol 12 tahlilchi · Olib tashlash: /rol 12 -\n"
                "Rollar: " + ", ".join(ROL)), None
    uid = next((k for k, u in db["users"].items() if str(u.get("nomer")) == p[1].lstrip("№#")), None)
    if not uid:
        return "№%s a'zo topilmadi." % p[1], None
    roles = db.setdefault("roles", {})
    if p[2] == "-":
        roles[uid] = []
        db_save(db)
        return "№%s ning rollari olib tashlandi." % p[1], None
    r = ROL.get(p[2])
    if not r:
        return "Bunday rol yo'q. Rollar: " + ", ".join(ROL), None
    band = sum(1 for v in roles.values() if p[2] in v)
    if p[2] not in roles.get(uid, []) and band >= r["max"]:
        return "«%s» to'lgan (%d/%d). Avval birini bo'shating: /rol N -" % (r["nom"], band, r["max"]), None
    roles[uid] = sorted(set(roles.get(uid, []) + [p[2]]))
    ar = db.setdefault("rol_ariza", {}).get(uid)
    if ar:
        ar["holat"] = "hal"
    db_save(db)
    send(int(uid), "🎉 Sizga <b>%s</b> roli berildi!\n\n%s" % (esc(r["nom"]), rol_karta(r)))
    return "✅ №%s %s → %s" % (p[1], db["users"][uid]["ism"], r["nom"]), None

def jamoa_matn(db):
    roles = db.get("roles", {})
    q = ["👥 <b>JAMOA</b> (band / kerak)"]
    for g in ROLLAR.get("guruhlar", []):
        q.append("\n<b>%s</b>" % esc(g["nom"]))
        for r in ROLLAR["rollar"]:
            if r["guruh"] != g["key"]:
                continue
            kim = [db["users"][u]["ism"] for u, v in roles.items() if r["key"] in v and u in db["users"]]
            bel = "✅" if len(kim) >= r["min"] else ("🟡" if kim else "⬜")
            q.append("%s %s — %d/%s%s" % (bel, esc(r["nom"]), len(kim), _soni(r),
                                          (": " + esc(", ".join(kim))) if kim else ""))
    kut = [(u, a) for u, a in db.get("rol_ariza", {}).items() if a.get("holat") == "kutilmoqda" and u in db["users"]]
    if kut:
        q.append("\n<b>Kutilayotgan arizalar:</b>")
        q += ["• №%s %s → %s  (/rol %s %s)" % (db["users"][u]["nomer"], esc(db["users"][u]["ism"]),
                                             esc(ROL.get(a["rol"], {}).get("nom", a["rol"])), db["users"][u]["nomer"], a["rol"])
              for u, a in kut]
    st = [r for r in ROLLAR.get("rollar", []) if r.get("start")]
    band = sum(min(r["min"], sum(1 for v in roles.values() if r["key"] in v)) for r in st)
    q.append("\nStart jamoa: %d/%d o'rin band (Ilmiy rahbar bilan)" % (band, sum(r["min"] for r in st)))
    return "\n".join(q)

def callback(cq, db):
    """Inline tugmalar: rsvp:N · rol:key · ariza:key · rollar:"""
    data = cq.get("data") or ""
    uid = (cq.get("from") or {}).get("id")
    m = cq.get("message") or {}
    toast, yangi, kb = "", None, None
    if data.startswith("rsvp:"):
        ev = db["events"].get(data[5:])
        if not ev or ev["holat"] == "yakun":
            toast = "Bu tadbir yakunlangan."
        else:
            toast = ("✅ Yozildingiz! Tadbir kuni kirishda QR orqali davomat olinadi."
                     if rsvp_qoy(db, ev, uid) else "Yozilish bekor qilindi.")
            if m and TOKEN:
                tg("editMessageReplyMarkup", chat_id=m["chat"]["id"], message_id=m["message_id"],
                   reply_markup=json.dumps(rsvp_kb(ev, uid), ensure_ascii=False))
    elif data.startswith(("rol:", "ariza:", "rollar:")) and not tadbir_ruxsat(uid, db):
        toast = "Bu tugma faol emas."                       # rollar — faqat ichki boshqaruv (v3.1)
    elif data.startswith(("rol:", "ariza:")):
        toast, yangi, kb = rol_callback(uid, data, db)
    elif data.startswith("rollar:"):
        yangi, kb = rollar_matn(), rollar_kb()
    if TOKEN and cq.get("id"):
        tg("answerCallbackQuery", callback_query_id=cq["id"], text=toast[:190])
    if yangi and TOKEN and uid:
        send(uid, yangi, kb)
    return toast, yangi, kb


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
            elif p.startswith("/qr/"):
                q = urllib.parse.parse_qs(self.path.partition("?")[2])
                qism = p.strip("/").split("/")
                eid = qism[1] if len(qism) > 1 else ""
                k = (q.get("k") or [""])[0]
                db = get_db()
                ev = db["events"].get(eid)
                if not ev or not hmac.compare_digest(qr_admin_kalit(eid), k):
                    return self._send(403, "ruxsat yo'q", "text/plain; charset=utf-8")
                if len(qism) > 2 and qism[2] == "t":
                    _avto_yakun(db)
                    return self._send(200, json.dumps({
                        "link": qr_link(ev) if ev["holat"] == "faol" else "", "holat": ev["holat"],
                        "nom": ev["nom"], "keldi": len(ev.get("keldi", {})), "rsvp": rsvp_soni(ev),
                        "qoldi": QR_OYNA - int(time.time()) % QR_OYNA}, ensure_ascii=False),
                        "application/json; charset=utf-8")
                self._send(200, qr_html(ev, k), "text/html; charset=utf-8")
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
                         "ts": time.time(), "manba": ref_ol(uid, "miniapp")}
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

def qr_html(ev, k):
    try:
        with open(os.path.join(HERE, "miniapp", "qrcode.js"), encoding="utf-8") as f:
            lib = f.read()
    except OSError:
        lib = ""
    return QR_SAHIFA.replace("__LIB__", lib).replace("__NOM__", esc(ev["nom"])).replace(
        "__URL__", "/qr/%s/t?k=%s" % (ev["id"], k)).replace("__ID__", ev["id"])

QR_SAHIFA = """<!doctype html><html lang="uz"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex">
<title>Davomat QR · __NOM__</title><style>
*{box-sizing:border-box}body{margin:0;min-height:100vh;font-family:Inter,system-ui,-apple-system,Segoe UI,Roboto,sans-serif;
background:radial-gradient(1200px 700px at 20% 0%,#2F6CD2 0%,#173A73 55%,#0F1622 100%);color:#fff;display:flex;
align-items:center;justify-content:center;padding:3vh 3vw}
.w{display:grid;grid-template-columns:minmax(280px,62vh) minmax(260px,1fr);gap:5vw;align-items:center;max-width:1300px;width:100%}
.q{background:#fff;border-radius:28px;padding:22px;box-shadow:0 30px 80px rgba(0,0,0,.35)}
.q svg{display:block;width:100%;height:auto}.bar{height:8px;border-radius:8px;background:rgba(255,255,255,.18);overflow:hidden;margin-top:18px}
.bar i{display:block;height:100%;background:linear-gradient(90deg,#9FD0FF,#4DA3FF);width:100%;transition:width 1s linear}
.b{font-size:14px;letter-spacing:.18em;text-transform:uppercase;color:#AFC3E0;font-weight:700}
h1{font-size:clamp(28px,4.4vw,56px);line-height:1.08;margin:.35em 0 .4em;font-weight:800}
.s{font-size:clamp(17px,1.7vw,24px);color:#D8E9FF;line-height:1.45}
.n{display:flex;gap:18px;margin-top:4vh}.n div{background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.18);
border-radius:18px;padding:16px 22px;min-width:150px}.n b{display:block;font-size:clamp(34px,4vw,60px);font-weight:800}
.n span{color:#AFC3E0;font-size:15px}.x{font-size:28px;color:#fff;text-align:center;padding:30px}
@media(max-width:800px){.w{grid-template-columns:1fr}}</style></head><body><div class="w">
<div><div class="q" id="q"><div class="x">…</div></div><div class="bar"><i id="t"></i></div></div>
<div><div class="b">Raqamli Tadqiqot · davomat</div><h1>__NOM__</h1>
<div class="s">Telefon kamerasi bilan skanerlang → botda <b>Start</b> bosing.<br>Davomatdan so'ng tadbir suratlarini
shu chatga yuborasiz. QR har 30 soniyada yangilanadi — skrinshot ishlamaydi.</div>
<div class="n"><div><b id="k">0</b><span>keldi</span></div><div><b id="r">0</b><span>yozilgan</span></div></div></div>
</div><script>__LIB__</script><script>
var last="",U="__URL__";
function draw(l){var qr=qrcode(0,"M");qr.addData(l);qr.make();document.getElementById("q").innerHTML=qr.createSvgTag({cellSize:8,margin:0,scalable:true});}
function tick(){fetch(U,{cache:"no-store"}).then(function(r){return r.json()}).then(function(d){
document.getElementById("k").textContent=d.keldi;document.getElementById("r").textContent=d.rsvp;
var t=document.getElementById("t");t.style.transition="none";t.style.width=(d.qoldi/30*100)+"%";
setTimeout(function(){t.style.transition="width "+d.qoldi+"s linear";t.style.width="0%"},50);
if(!d.link){document.getElementById("q").innerHTML='<div class="x" style="color:#173A73">Tadbir faol emas ('+d.holat+')</div>';last="";return}
if(d.link!==last){last=d.link;draw(d.link)}}).catch(function(){})}
tick();setInterval(tick,5000);</script></body></html>"""

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
                 allowed_updates='["message","channel_post","callback_query"]')
        if nat is None:
            continue
        for up in nat:
            offset = up["update_id"] + 1
            try:
                update_ishla(up, db)
            except Exception as e:                      # noqa: BLE001
                log.exception("Update xatosi: %s", e)

def update_ishla(up, db):
    """Bitta update: kanal posti, inline tugma, guruh buyrug'i, surat yoki shaxsiy xabar."""
    if up.get("channel_post"):
        kanal_post(up["channel_post"], db)
        return
    if up.get("callback_query"):
        callback(up["callback_query"], db)
        db_save(db)
        return
    msg = up.get("message")
    if not msg:
        return
    tur = (msg.get("chat") or {}).get("type", "private")
    uid = (msg.get("from") or {}).get("id")
    if tur != "private":                                # guruhlarda faqat /arxiv_shu (admin)
        if (msg.get("text") or "").split("@")[0].strip() == "/arxiv_shu" and uid in ADMIN_IDS:
            db.setdefault("cfg", {})["arxiv"] = msg["chat"]["id"]
            db_save(db)
            send(msg["chat"]["id"], "✅ Bu guruh tadbir suratlari arxivi qilib belgilandi. Guruh yopiq qolsin "
                 "va havolasi hech kimga berilmasin. «Mavzular» (Topics) yoqilgan bo'lsa, har tadbir alohida "
                 "mavzuga tushadi.")
        return
    if any(k in msg for k in ("photo", "video", "document")) and "text" not in msg:
        javob = surat_qabul(msg, db)
        if javob:
            send(msg["chat"]["id"], javob)
        return
    if "text" not in msg:
        return
    try:
        javob, kb = handle(msg, db)
        db_save(db)
    except Exception as e:                              # noqa: BLE001
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
    test_v3(db)
    print("\n✅ TEST O'TDI: ro'yxat (Boshqa→erkin matn) → saqlash → holat → "
          "statistika → XLSX (uslubli) + CSV (vergul) → birlashtirish → tadbir (kanal posti, "
          "Boraman, QR davomat, eskirgan QR, surat oynasi) → rollar (ariza, tayinlash, jamoa).")

def test_v3(db):
    global ADMIN_IDS, CHANNEL
    ADMIN_IDS, CHANNEL = {100001}, "@Raqamli_tadqiqot"
    # 1) kanal posti #tadbir → tadbir yaratiladi; boshqa kanal yoki heshtegsiz post — e'tiborsiz
    assert kanal_post({"chat": {"id": -1, "username": "boshqa"}, "message_id": 5, "text": "X #tadbir"}, db) is None
    assert kanal_post({"chat": {"id": -1, "username": "Raqamli_tadqiqot"}, "message_id": 6, "text": "Oddiy post"}, db) is None
    ev = kanal_post({"chat": {"id": -100, "username": "Raqamli_tadqiqot"}, "message_id": 7,
                     "text": "🤝 Tanishuv teambuilding #tadbir\n12-oktabr, 15:00"}, db)
    assert ev and ev["id"] == "1" and "Tanishuv teambuilding" in ev["nom"], ev
    assert kanal_post({"chat": {"id": -100, "username": "Raqamli_tadqiqot"}, "message_id": 7, "text": "#tadbir"}, db) is None
    # 2) Boraman (callback) — almashlash; deep-link rsvp
    callback({"data": "rsvp:1", "from": {"id": 100001}}, db)
    callback({"data": "rsvp:1", "from": {"id": 200002}}, db)
    callback({"data": "rsvp:1", "from": {"id": 200002}}, db)            # bekor
    assert rsvp_soni(ev) == 1, ev["rsvp"]
    j, _ = handle({"chat": {"id": 300003}, "text": "/start rsvp1"}, db)
    assert "yozildingiz" in j and rsvp_soni(ev) == 2
    # 3) QR: faol emas → rad; boshlash → yaroqli token qabul; eskirgan token rad
    j, _ = handle({"chat": {"id": 300003}, "text": "/start ev1_" + qr_token(ev)}, db)
    assert "faol emas" in j
    j, kb = handle({"chat": {"id": 100001}, "text": "/tadbir_boshlash 1"}, db)
    assert ev["holat"] == "faol" and "/qr/1?k=" in kb["inline_keyboard"][0][0]["url"]
    eski = qr_token(ev, int(time.time() // QR_OYNA) - QR_AMAL)
    j, _ = handle({"chat": {"id": 300003}, "text": "/start ev1_" + eski}, db)
    assert "eskirgan" in j and "300003" not in ev["keldi"]
    j, _ = handle({"chat": {"id": 300003}, "text": "/start ev1_" + qr_token(ev), "from": {"first_name": "Mehmon"}}, db)
    assert "Davomat qayd etildi" in j and ev["keldi"]["300003"]["azo"] is False
    # 4) surat: davomatsiz — rad; davomatli — qabul oynasida (TOKEN yo'q → «Saqlanmadi»)
    assert "qabul qilinmadi" in surat_qabul({"chat": {"id": 400004}, "message_id": 1, "photo": [{}]}, db)
    assert "Saqlanmadi" in surat_qabul({"chat": {"id": 300003}, "message_id": 2, "photo": [{}]}, db)
    handle({"chat": {"id": 100001}, "text": "/tadbir_yakun 1"}, db)
    ev["yakunlandi"] -= SURAT_KECH + 1                                  # 1 soat o'tdi → yopiq
    assert "qabul qilinmadi" in surat_qabul({"chat": {"id": 300003}, "message_id": 3, "photo": [{}]}, db)
    j, _ = handle({"chat": {"id": 100001}, "text": "/tadbirlar"}, db)
    assert "kelgan: 1" in j, j
    # 5) ruxsat: oddiy a'zo tadbir buyrug'ini ishlata olmaydi
    j, _ = handle({"chat": {"id": 300003}, "text": "/tadbir_boshlash 1"}, db)
    assert "⛭" in j
    # 6) rollar: 16 ta, komissiya — 3 ovoz; ariza → tayinlash → jamoa → holat
    assert len(ROL) == 16 and sum(1 for r in ROL.values() if r.get("ovoz")) == 3, len(ROL)
    j, kb = handle({"chat": {"id": 100001}, "text": "/rollar"}, db)
    assert "Metodologiya komissiyasi" in j and kb["inline_keyboard"]
    j, _ = handle({"chat": {"id": 300003}, "text": "/rollar"}, db)      # ommaga rollar ko'rinmaydi
    assert "komissiya" not in (j or "") and "rol" not in (j or "").lower(), j
    t, y, _ = callback({"data": "ariza:tahlilchi", "from": {"id": 300003}}, db)
    assert t == "Bu tugma faol emas." and not y and "300003" not in db.get("rol_ariza", {})
    t, y, _ = callback({"data": "rollar:", "from": {"id": 300003}}, db)
    assert not y
    t, _, _ = callback({"data": "ariza:tahlilchi", "from": {"id": 100001}}, db)
    assert db["rol_ariza"]["100001"]["rol"] == "tahlilchi"
    nomer = db["users"]["100001"]["nomer"]
    j, _ = handle({"chat": {"id": 100001}, "text": "/rol %s tahlilchi" % nomer}, db)
    assert "✅" in j and db["roles"]["100001"] == ["tahlilchi"]
    j, _ = handle({"chat": {"id": 100001}, "text": "/jamoa"}, db)
    assert "Tahlilchi — 1/4–6" in j, j
    j, _ = handle({"chat": {"id": 100001}, "text": "/holat"}, db)
    assert "rol: Tahlilchi" in j
    # 7) birlashtirish: holat orqaga qaytmaydi, davomat yo'qolmaydi, bekor qilingan yozilish tirilmaydi
    a = {"events": {"1": {"id": "1", "holat": "yakun", "upd": 5, "rsvp": {"9": -20}, "keldi": {"7": {}}, "suratlar": {"7": 2}}}}
    b = {"events": {"1": {"id": "1", "holat": "faol", "upd": 9, "rsvp": {"9": 10, "8": 3}, "keldi": {"6": {}}, "suratlar": {"7": 1}}}}
    m = _merge_events(a["events"], b["events"])["1"]
    assert m["holat"] == "yakun" and set(m["keldi"]) == {"6", "7"} and m["rsvp"]["9"] < 0 and m["suratlar"]["7"] == 2, m
    print("✅ v3: tadbir + QR + surat oynasi + rollar testlari o'tdi")

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
