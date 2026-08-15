from rest_framework.permissions import BasePermission

from services.helpers import get_telegram_user


class IsTelegramWebAppUser(BasePermission):
    message = "Telegram foydalanuvchisi aniqlanmadi."

    def has_permission(self, request, view):
        init_data = request.headers.get("X-Telegram-Init-Data")
        telegram_user = get_telegram_user(init_data)

        if not telegram_user:
            return False

        # View ichida qayta HMAC hisoblamaslik uchun natijani request'ga yozib qo'yamiz
        request.telegram_user = telegram_user
        return True
