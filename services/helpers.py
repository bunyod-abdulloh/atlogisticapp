import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl

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