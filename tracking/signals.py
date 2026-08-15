import html
import logging

from django.contrib import messages
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from services.helpers import send_telegram_message
from .models import CargoStatusUpdate

logger = logging.getLogger(__name__)


@receiver(post_save, sender=CargoStatusUpdate)
def notify_client_on_status_update(sender, instance, created, **kwargs):
    # Faqat yangi status yaratilganda
    if not created:
        return

    client = instance.cargo.client

    request = getattr(instance, "_admin_request", None)

    # Telegram ulanmagan
    if not client.telegram_id:
        if request:
            transaction.on_commit(
                lambda: messages.warning(
                    request,
                    f"⚠️ «{client.name}» Telegram botga ulanmagan. "
                    f"Xabar yuborilmadi."
                )
            )

        return

    # DB commit'dan keyin Telegram xabarini yuboramiz
    transaction.on_commit(
        lambda: _send_status_notification(
            instance,
            client,
            request,
        )
    )


def _send_status_notification(status_update, client, request=None):
    cargo = status_update.cargo

    local_time = timezone.localtime(status_update.created_at)

    lines = [
        f"👋 Hurmatli <b>{html.escape(client.name)}</b>!\n",
        "📢 Yukingiz holati bo'yicha yangi xabar:\n",
        f"📦 Yuk raqami: <b>{html.escape(cargo.tracking_number)}</b>",
        f"🔄 Holat: <b>{html.escape(status_update.display_text)}</b>",
    ]

    if status_update.location:
        lines.append(
            f"📍 Joylashuv: <b>{html.escape(status_update.location)}</b>"
        )

    if status_update.comment:
        lines.append(
            f"💬 Izoh: <i>{html.escape(status_update.comment)}</i>"
        )

    lines.append("")

    lines.append(
        f"📅 Vaqt: <b>{local_time.strftime('%d.%m.%Y')}</b> | "
        f"🕒 <b>{local_time.strftime('%H:%M')}</b>"
    )

    success = send_telegram_message(
        client.telegram_id,
        "\n".join(lines),
    )

    # Admin panelga natijani chiqarish
    if request:
        if success:
            messages.success(
                request,
                f"Telegram xabari «{client.name}» mijoziga yuborildi."
            )
        else:
            messages.error(
                request,
                f"Telegram xabari «{client.name}» mijoziga yuborilmadi."
            )
