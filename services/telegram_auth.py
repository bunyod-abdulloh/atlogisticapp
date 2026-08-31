"""Telegram WebApp initData'ni tekshirish.

Hujjat: https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app

Algoritm:
1. secret_key = HMAC-SHA256("WebAppData", bot_token)
2. data_check_string — "hash" dan tashqari barcha juftliklar, alifbo tartibida, "\n" bilan
3. bizning hash = HMAC-SHA256(secret_key, data_check_string)
4. shu hash Telegram yuborgan hash bilan bir xil bo'lishi SHART
"""

import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl

from django.conf import settings

INIT_DATA_MAX_AGE_SECONDS = 24 * 60 * 60  # 24 soat — replay hujumidan himoya


class InvalidInitData(Exception):
    """initData yaroqsiz yoki muddati o'tgan bo'lsa ko'tariladi."""


def parse_and_validate_init_data(init_data: str) -> dict:
    if not init_data:
        raise InvalidInitData("initData bo'sh")

    try:
        pairs = dict(parse_qsl(init_data, keep_blank_values=True, strict_parsing=True))
    except ValueError as exc:
        raise InvalidInitData("initData formati noto'g'ri") from exc

    received_hash = pairs.pop("hash", None)
    if not received_hash:
        raise InvalidInitData("hash maydoni topilmadi")

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))

    secret_key = hmac.new(
        b"WebAppData", settings.TELEGRAM_BOT_TOKEN.encode(), hashlib.sha256
    ).digest()

    computed_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(computed_hash, received_hash):
        raise InvalidInitData("hash mos kelmadi — soxta yoki o'zgartirilgan initData")

    try:
        auth_date = int(pairs.get("auth_date", 0))
    except ValueError as exc:
        raise InvalidInitData("auth_date formati noto'g'ri") from exc

    if time.time() - auth_date > INIT_DATA_MAX_AGE_SECONDS:
        raise InvalidInitData("initData muddati o'tgan, ilovani qayta oching")

    user_raw = pairs.get("user")
    if not user_raw:
        raise InvalidInitData("user maydoni topilmadi")

    try:
        return json.loads(user_raw)
    except json.JSONDecodeError as exc:
        raise InvalidInitData("user maydoni JSON emas") from exc
