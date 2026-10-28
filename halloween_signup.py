"""Halloween event sign-up flow, kept separate from ordinary club membership."""
from __future__ import annotations

import html
import re
import time

HALLOWEEN_DEEP_LINK = "halloween"
EVENT_DAY = "2026-10-31"
DELETE_AFTER = "2026-11-30"  # Toshkent sanasi; faol ro'yxatdan tozalash kuni

KB_CONSENT = {"inline_keyboard": [
    [{"text": "✅ Roziman va davom etaman", "callback_data": "halloween:consent"}],
    [{"text": "Bekor qiliş", "callback_data": "halloween:cancel"}],
]}
KB_CONTACT = {"keyboard": [
    [{"text": "📱 Telefon raqamimni ulashiş", "request_contact": True}],
    [{"text": "Bekor qiliş"}],
], "resize_keyboard": True, "one_time_keyboard": True}
KB_COURSE = {"keyboard": [[{"text": c} for c in row]
                           for row in [["1", "2", "3", "4"], ["Magistratura"]]],
             "resize_keyboard": True, "one_time_keyboard": True}
KB_CONFIRM = {"inline_keyboard": [
    [{"text": "✅ Ishtirokni tasdiqlayman", "callback_data": "halloween:confirm"}],
    [{"text": "Bekor qiliş", "callback_data": "halloween:cancel"}],
]}
KB_REMOVE = {"remove_keyboard": True}


def _today_tashkent(now=None):
    now = time.time() if now is None else now
    return time.strftime("%Y-%m-%d", time.gmtime(now + 5 * 3600))


def prune(db, now=None, today=None):
    """Incomplete forms expire in a day; confirmed rows expire after the event retention date."""
    now = time.time() if now is None else now
    states = db.setdefault("halloween_state", {})
    for uid, state in list(states.items()):
        if now - float(state.get("updated_at", state.get("started_at", now))) > 86400:
            states.pop(uid, None)
    if (today or _today_tashkent(now)) > DELETE_AFTER:
        registrations = db.setdefault("halloween_registrations", {})
        deleted = db.setdefault("halloween_deleted", {})
        for uid, record in list(registrations.items()):
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
        return "🎃 Halloween kvestiga röyxatdan ötiş yopilgan.", None
    db.setdefault("halloween_state", {}).pop(str(chat_id), None)
    return (
        "🎃 Halloween sirli kvestiga röyxatdan ötiş\n\n"
        "Bot telefon raqamingizni Telegram kontaktini ulashiş orqali, şuningdek ism-familiya, "
        "kurs va guruhingizni söraydi. Ma’lumotlarni faqat administratorlar ko‘ra oladi va ular tadbir röyxati uchun ishlatiladi.\n\n"
        "Faol röyxatdagi ma’lumotlar 2026-yil 30-noyabrda öçiriladi. Baza zaxirasining "
        "versiya tarixida eski nusxalar qolishi mumkin. Rozilik bersangiz, davom eting.",
        KB_CONSENT,
    )


def callback(uid, data, db, now=None, courses=None):
    now = time.time() if now is None else now
    uid_s = str(uid)
    states = db.setdefault("halloween_state", {})
    registrations = db.setdefault("halloween_registrations", {})
    prune(db, now=now)
    if data == "halloween:cancel":
        states.pop(uid_s, None)
        return "Röyxatdan ötiş bekor qilindi.", KB_REMOVE
    if data == "halloween:consent":
        if _today_tashkent(now) > EVENT_DAY:
            states.pop(uid_s, None)
            return "Halloween kvestiga röyxatdan ötiş yopilgan.", KB_REMOVE
        states[uid_s] = {
            "step": "phone", "consent_at": time.strftime("%Y-%m-%d %H:%M", time.gmtime(now)),
            "started_at": now, "updated_at": now,
        }
        return (
            "📱 Telefon raqamingizni yuborish uchun «Telefon raqamimni ulashiş» tugmasini bosing. "
            "Faqat özingizning Telegram kontaktingiz qabul qilinadi.", KB_CONTACT,
        )
    if data == "halloween:confirm":
        state = states.get(uid_s)
        if not state or state.get("step") != "confirm":
            return "Röyxat qadami topilmadi. Botdagi yozilish tugmasidan qayta boshlang.", KB_REMOVE
        user = state.get("telegram_user", {})
        record = {
            "ism": state.get("ism", ""), "telefon": state.get("telefon", ""),
            "kurs": state.get("kurs", ""), "guruh": state.get("guruh", ""),
            "username": _clean(user.get("username", ""), 64), "telegram_id": uid_s,
            "confirmed_at": time.strftime("%Y-%m-%d %H:%M", time.gmtime(now)),
            "confirmed_ts": now, "consent_at": state.get("consent_at", ""),
        }
        registrations[uid_s] = record
        db.setdefault("halloween_deleted", {}).pop(uid_s, None)
        states.pop(uid_s, None)
        return "✅ Ishtirokingiz tasdiqlandi! Ma’lumotni öçirish uchun /bekor_hallowen buyrug‘ini yuboring.", KB_REMOVE
    return "Tugma eskirgan. Röyxatdan ötişni qayta boshlang.", KB_REMOVE


def step(msg, db, now=None, courses=None):
    now = time.time() if now is None else now
    chat_id = msg["chat"]["id"]
    uid = str(chat_id)
    states = db.setdefault("halloween_state", {})
    prune(db, now=now)
    state = states.get(uid)
    if not state:
        return None, None
    text = (msg.get("text") or "").strip()
    if text in ("Bekor qiliş", "/bekor_hallowen"):
        states.pop(uid, None)
        return "Röyxatdan ötiş bekor qilindi.", KB_REMOVE
    current = state.get("step")
    if current == "phone":
        contact = msg.get("contact") or {}
        if not contact:
            return "Telefon raqamini matn qilib emas, kontakt tugmasi orqali yuboring.", KB_CONTACT
        if str(contact.get("user_id", "")) != uid:
            return "Faqat özingizning telefon kontaktingizni ulashiş.", KB_CONTACT
        digits = re.sub(r"\D", "", str(contact.get("phone_number", "")))
        if not 7 <= len(digits) <= 15:
            return "Telefon raqami töğri körinmayapti. Kontaktni qayta ulashiş.", KB_CONTACT
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
        phone_mask = ("•••• " + tail) if tail else "yashirilgan"
        summary = (
            "🧾 Ma’lumotlaringizni tekşiring:\n"
            "👤 %s\n🎓 %s-kurs\n👥 %s-guruh\n📱 %s\n\n"
            "Hammasi töğri bölsa, ishtirokni tasdiqlang."
            % (html.escape(state.get("ism", "")),
               html.escape(state.get("kurs", "")), html.escape(state.get("guruh", "")), phone_mask)
        )
        return summary, KB_CONFIRM
    if current == "confirm":
        return "Ma’lumotlarni tekşirib, «Ishtirokni tasdiqlayman» tugmasini bosing.", KB_CONFIRM
    return "Röyxat qadami topilmadi. Qayta boshlash uchun botdagi tugmani bosing.", KB_REMOVE


def cancel(chat_id, db, now=None):
    now = time.time() if now is None else now
    uid = str(chat_id)
    db.setdefault("halloween_state", {}).pop(uid, None)
    existed = db.setdefault("halloween_registrations", {}).pop(uid, None)
    if existed:
        db.setdefault("halloween_deleted", {})[uid] = now
        return "Halloween kvesti röyxatidagi ma’lumotlaringiz öçirildi.", KB_REMOVE
    return "Faol röyxatdan ö’tgan yozuv topilmadi.", KB_REMOVE


def rows(db, local_time):
    regs = db.get("halloween_registrations", {})
    ordered = sorted(regs.items(), key=lambda kv: (kv[1].get("confirmed_at", ""), kv[1].get("ism", "").casefold()))
    header = ["№", "Ism-familiya", "Telefon", "Kurs", "Guruh", "Telegram username", "Telegram ID", "Tasdiqlangan vaqt (Toshkent)"]
    result = []
    for i, (uid, record) in enumerate(ordered, 1):
        ts = record.get("confirmed_at", "")
        result.append([i, record.get("ism", ""), record.get("telefon", ""), record.get("kurs", ""),
                       record.get("guruh", ""), ("@" + record["username"]) if record.get("username") else "",
                       int(uid) if str(uid).isdigit() else uid, local_time(ts)])
    return header, result
