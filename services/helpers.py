import hashlib
import hmac
import json
import logging
import time
from urllib.parse import parse_qsl

import requests
from django.conf import settings

TELEGRAM_INIT_DATA_MAX_AGE = 24 * 60 * 60  # 1 kun — replay hujumini cheklash uchun


def get_telegram_user(init_data: str | None) -> dict | None:
    if not init_data:
        return None

    try:
        parsed = dict(parse_qsl(init_data, strict_parsing=True))
    except ValueError:
        return None

    received_hash = parsed.pop("hash", None)
    if not received_hash:
        return None

    # Telegram talabi: qolgan fieldlar alifbo bo'yicha saralanadi
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))

    secret_key = hmac.new(
        b"WebAppData", settings.TELEGRAM_BOT_TOKEN.encode(), hashlib.sha256
    ).digest()
    computed_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    # compare_digest — timing attack'dan himoya qiladi, oddiy == emas
    if not hmac.compare_digest(computed_hash, received_hash):
        return None

    auth_date = parsed.get("auth_date")
    if not auth_date or (time.time() - int(auth_date)) > TELEGRAM_INIT_DATA_MAX_AGE:
        return None

    user_json = parsed.get("user")
    if not user_json:
        return None

    try:
        return json.loads(user_json)
    except json.JSONDecodeError:
        return None


logger = logging.getLogger(__name__)

TELEGRAM_SEND_MESSAGE_URL = "https://api.telegram.org/bot{token}/sendMessage"
TELEGRAM_REQUEST_TIMEOUT = 5  # soniya — Telegram javob bermasa cheksiz kutmasin


def send_telegram_message(chat_id: int, text: str) -> bool:
    """
    Telegram foydalanuvchisiga xabar yuboradi.

    Xatolik yuz bersa (foydalanuvchi botni bloklagan, tarmoq muammosi va h.k.)
    False qaytaradi va logga yozadi — bu funksiya hech qachon exception
    tashlamaydi, shuning uchun admin panel saqlashini to'xtatib qo'ymaydi.
    """
    url = TELEGRAM_SEND_MESSAGE_URL.format(token=settings.TELEGRAM_BOT_TOKEN)

    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    try:
        response = requests.post(url, json=payload, timeout=TELEGRAM_REQUEST_TIMEOUT)
        response.raise_for_status()
        return True
    except requests.RequestException:
        # Tokenni logga chiqarmaslik uchun url emas, faqat chat_id yoziladi
        logger.warning("Telegram xabar yuborilmadi: chat_id=%s", chat_id, exc_info=True)
        return False
