"""YÖQOLGAN XARITA tadbiri uçun röyxatdan ötiş oqimi."""
from __future__ import annotations

import html
import re
import time

EVENT_DEEP_LINK = "yoqolganxarita"
EVENT_DAY = "2026-11-07"
DELETE_AFTER = "2026-12-07"  # Tadbirdan 30 kun ötgaç faol yozuvlarni tozalaş
EVENT_TITLE = "YÖQOLGAN XARITA"
EVENT_TIME = "14:30"
EVENT_VENUE = "TDIU piknik maydoni"

KB_CONSENT = {"inline_keyboard": [
    [{"text": "✅ Roziman va davom etaman", "callback_data": "yoqolganxarita:consent"}],
    [{"text": "Bekor qiliş", "callback_data": "yoqolganxarita:cancel"}],
]}
KB_CONTACT = {"keyboard": [
    [{"text": "📱 Telefon raqamimni ulaşiş", "request_contact": True}],
    [{"text": "Bekor qiliş"}],
], "resize_keyboard": True, "one_time_keyboard": True}
KB_COURSE = {"keyboard": [[{"text": c} for c in row]
                           for row in [["1", "2", "3", "4"], ["Magistratura"]]],
             "resize_keyboard": True, "one_time_keyboard": True}
KB_CONFIRM = {"inline_keyboard": [
    [{"text": "✅ Iştirokni tasdiqlayman", "callback_data": "yoqolganxarita:confirm"}],
    [{"text": "Bekor qiliş", "callback_data": "yoqolganxarita:cancel"}],
]}
KB_REMOVE = {"remove_keyboard": True}


def _today_tashkent(now=None):
    now = time.time() if now is None else now
    return time.strftime("%Y-%m-%d", time.gmtime(now + 5 * 3600))


def prune(db, now=None, today=None):
    """Tugallanmagan şakllar 24 soatda, faol tadbir yozuvlari 30 kundan keyin tozalanadi."""
    now = time.time() if now is None else now
    states = db.setdefault("event_state", {})
    for uid, state in list(states.items()):
        if now - float(state.get("updated_at", state.get("started_at", now))) > 86400:
            states.pop(uid, None)
    if (today or _today_tashkent(now)) >= DELETE_AFTER:
        registrations = db.setdefault("event_registrations", {})
        deleted = db.setdefault("event_deleted", {})
        for uid in list(registrations):
            deleted[uid] = max(float(deleted.get(uid, 0)), now)
            registrations.pop(uid, None)
        states.clear()


def _clean(value, limit=100):
    value = re.sub(r"[\x00-\x1f\x7f]", " ", str(value or ""))
    value = re.sub(r"\s+", " ", value).strip()
    return value.replace("<", "").replace(">", "")[:limit]


def start(chat_id, db, now=None):
    now = time.time() if now is None else now
    prune(db, now=now)
    if _today_tashkent(now) > EVENT_DAY:
        return "📚 YÖQOLGAN XARITA tadbiriga röyxatdan ötiş yopilgan.", None
    uid = str(chat_id)
    if uid in db.setdefault("event_registrations", {}):
        return ("✅ Siz bu tadbirga allaqaçon röyxatdan ötgansiz. "
                "Yozuvni bekor qiliş uçun /bekor_xarita buyruğini yuboring."), KB_REMOVE
    db.setdefault("event_state", {}).pop(uid, None)
    return (
        "🧭 <b>YÖQOLGAN XARITA — tadbirga röyxatdan ötiş</b>\n\n"
        "📅 7-noyabr 2026 · 14:30\n"
        "📍 TDIU piknik maydoni\n\n"
        "Röyxatdan ötiş uçun telefon raqamingizni Telegram kontaktingiz orqali, "
        "şuningdek ism-familiya, kurs va guruhingizni söraymiz. Ma’lumotlarni faqat "
        "administratorlar köradi; ular faqat uşbu tadbir röyxati uçun işlatiladi.\n\n"
        "Faol yozuvlar tadbirdan 30 kun ötgaç tozalanadi; yopiq zaxira tarixida "
        "avvalgi nusxalar qolişi mumkin. Rozilik bersangiz, davom eting.",
        KB_CONSENT,
    )


def callback(uid, data, db, now=None, courses=None):
    now = time.time() if now is None else now
    uid_s = str(uid)
    states = db.setdefault("event_state", {})
    registrations = db.setdefault("event_registrations", {})
    prune(db, now=now)
    if data == "yoqolganxarita:cancel":
        states.pop(uid_s, None)
        return "Röyxatdan ötiş bekor qilindi.", KB_REMOVE
    if data == "yoqolganxarita:consent":
        if _today_tashkent(now) > EVENT_DAY:
            states.pop(uid_s, None)
            return "YÖQOLGAN XARITA tadbiriga röyxatdan ötiş yopilgan.", KB_REMOVE
        if uid_s in registrations:
            states.pop(uid_s, None)
            return "Siz bu tadbirga allaqaçon röyxatdan ötgansiz.", KB_REMOVE
        states[uid_s] = {
            "step": "phone", "consent_at": time.strftime("%Y-%m-%d %H:%M", time.gmtime(now)),
            "started_at": now, "updated_at": now,
        }
        return (
            "📱 Telefon raqamingizni yuboriş uçun «Telefon raqamimni ulaşiş» tugmasini bosing. "
            "Faqat öz Telegram kontaktingiz qabul qilinadi.", KB_CONTACT,
        )
    if data == "yoqolganxarita:confirm":
        state = states.get(uid_s)
        if not state or state.get("step") != "confirm":
            return "Röyxatdan ötiş qadami topilmadi. Botdagi havoladan qayta boşlang.", KB_REMOVE
        user = state.get("telegram_user", {})
        record = {
            "ism": state.get("ism", ""), "telefon": state.get("telefon", ""),
            "kurs": state.get("kurs", ""), "guruh": state.get("guruh", ""),
            "username": _clean(user.get("username", ""), 64), "telegram_id": uid_s,
            "confirmed_at": time.strftime("%Y-%m-%d %H:%M", time.gmtime(now)),
            "confirmed_ts": now, "consent_at": state.get("consent_at", ""),
        }
        registrations[uid_s] = record
        db.setdefault("event_deleted", {}).pop(uid_s, None)
        states.pop(uid_s, None)
        return ("✅ Iştirokingiz tasdiqlandi! Yozuvni bekor qiliş uçun "
                "/bekor_xarita buyruğini yuboring."), KB_REMOVE
    return "Tugma eskirgan. Röyxatdan ötişni qayta boşlang.", KB_REMOVE


def step(msg, db, now=None, courses=None):
    now = time.time() if now is None else now
    chat_id = msg["chat"]["id"]
    uid = str(chat_id)
    states = db.setdefault("event_state", {})
    prune(db, now=now)
    state = states.get(uid)
    if not state:
        return None, None
    text = (msg.get("text") or "").strip()
    if text in ("Bekor qiliş", "/bekor_xarita"):
        states.pop(uid, None)
        return "Röyxatdan ötiş bekor qilindi.", KB_REMOVE
    current = state.get("step")
    if current == "phone":
        contact = msg.get("contact") or {}
        if not contact:
            return "Telefon raqamini matn qilib emas, kontakt tugmasi orqali yuboring.", KB_CONTACT
        if str(contact.get("user_id", "")) != uid:
            return "Faqat öz telefon kontaktingizni ulaşing.", KB_CONTACT
        digits = re.sub(r"\D", "", str(contact.get("phone_number", "")))
        if not 7 <= len(digits) <= 15:
            return "Telefon raqami töğri körinmayapti. Kontaktni qayta ulaşing.", KB_CONTACT
        state.update({"telefon": "+" + digits, "step": "ism", "updated_at": now,
                      "telegram_user": msg.get("from", {})})
        return "✍️ Ism-familiyangizni töliq yozing:", KB_REMOVE
    if not text:
        return "Iltimos, söralgan ma’lumotni yuboring.", None
    if current == "ism":
        name = _clean(text, 100)
        if len(name) < 3:
            return "Ism-familiyani töliq yozing.", None
        state.update({"ism": name, "step": "kurs", "updated_at": now})
        return "🎓 Kursingizni tanlang:", KB_COURSE
    if current == "kurs":
        allowed = list(courses or ["1", "2", "3", "4", "Magistratura"])
        if text not in allowed:
            return "Kursni tugmadan tanlang.", KB_COURSE
        state.update({"kurs": text, "step": "guruh", "updated_at": now})
        return "👥 Guruhingizni yozing:", KB_REMOVE
    if current == "guruh":
        group = _clean(text, 40)
        if len(group) < 1:
            return "Guruhingizni kiriting.", None
        state.update({"guruh": group, "step": "confirm", "updated_at": now})
        tail = state.get("telefon", "")[-4:]
        phone_mask = ("•••• " + tail) if tail else "yaşirilgan"
        summary = (
            "🧾 Ma’lumotlaringizni tekşiring:\n"
            "👤 %s\n🎓 %s-kurs\n👥 %s-guruh\n📱 %s\n\n"
            "Hammasi töğri bölsa, iştirokni tasdiqlang."
            % (html.escape(state.get("ism", "")),
               html.escape(state.get("kurs", "")), html.escape(state.get("guruh", "")), phone_mask)
        )
        return summary, KB_CONFIRM
    if current == "confirm":
        return "Ma’lumotlarni tekşirib, «Iştirokni tasdiqlayman» tugmasini bosing.", KB_CONFIRM
    return "Röyxatdan ötiş qadami topilmadi. Qayta boşlaş uçun botdagi havolani bosing.", KB_REMOVE


def cancel(chat_id, db, now=None):
    now = time.time() if now is None else now
    uid = str(chat_id)
    db.setdefault("event_state", {}).pop(uid, None)
    existed = db.setdefault("event_registrations", {}).pop(uid, None)
    if existed:
        db.setdefault("event_deleted", {})[uid] = now
        return "YÖQOLGAN XARITA röyxatidagi ma’lumotlaringiz öçirildi.", KB_REMOVE
    return "Faol röyxatdan ötgan yozuv topilmadi.", KB_REMOVE


def rows(db, local_time):
    regs = db.get("event_registrations", {})
    ordered = sorted(regs.items(), key=lambda kv: (kv[1].get("confirmed_at", ""), kv[1].get("ism", "").casefold()))
    header = ["№", "Ism-familiya", "Telefon", "Kurs", "Guruh", "Telegram username", "Telegram ID", "Tasdiqlangan vaqt (Toşkent)"]
    result = []
    for i, (uid, record) in enumerate(ordered, 1):
        ts = record.get("confirmed_at", "")
        result.append([i, record.get("ism", ""), record.get("telefon", ""), record.get("kurs", ""),
                       record.get("guruh", ""), ("@" + record["username"]) if record.get("username") else "",
                       int(uid) if str(uid).isdigit() else uid, local_time(ts)])
    return header, result
