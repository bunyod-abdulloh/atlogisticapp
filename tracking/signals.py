import html
import logging

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from services.helpers import send_telegram_message
from .models import CargoStatusUpdate

logger = logging.getLogger(__name__)


@receiver(post_save, sender=CargoStatusUpdate)
def notify_client_on_status_update(sender, instance, created, **kwargs):
    # Faqat YANGI status yozuvi yaratilganda xabar yuboramiz —
    # mavjud yozuv tahrirlanganda (masalan izoh qo'shilsa) qayta yubormaymiz.
    if not created:
        return

    client = instance.cargo.client

    if not client.telegram_id:
        # Mijoz hali Telegram botga ulanmagan — jim o'tkazib yuboramiz
        return

    # Tranzaksiya muvaffaqiyatli yakunlangandan keyin yuboriladi —
    # aks holda rollback bo'lsa, "sodir bo'lmagan" status haqida xabar ketishi mumkin edi.
    transaction.on_commit(lambda: _send_status_notification(instance, client))


def _send_status_notification(status_update, client):
    cargo = status_update.cargo

    # created_at UTC'da saqlanadi — mijozga mahalliy vaqtda ko'rsatamiz
    local_time = timezone.localtime(status_update.created_at)

    lines = [
        f"👋 Hurmatli <b>{html.escape(client.name)}</b>!\n",
        f"📢 Yukingiz holati bo'yicha yangi xabar:\n",
        f"📦 Yuk raqami: <b>{html.escape(cargo.tracking_number)}</b>",
        f"🔄 Holat: <b>{html.escape(status_update.display_text)}</b>",
    ]

    if status_update.location:
        lines.append(f"📍 Joylashuv: <b>{html.escape(status_update.location)}</b>")

    if status_update.comment:
        lines.append(f"💬 Izoh: <i>{html.escape(status_update.comment)}</i>")

    lines.append("")
    lines.append(f"📅 Vaqt: <b>{local_time.strftime('%d.%m.%Y')}</b> | 🕒 <b>{local_time.strftime('%H:%M')}</b>")

    send_telegram_message(client.telegram_id, "\n".join(lines))
