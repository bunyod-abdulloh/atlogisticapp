import html
import logging

from django.contrib import messages
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from services.helpers import send_telegram_message
from .models import Stage

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Stage)
def notify_client_on_status_change(sender, instance, created, **kwargs):
    # Faqat yangi Stage (ya'ni yangi status) yaratilganda xabar yuboramiz
    if not created:
        return

    shipment = instance.shipment
    client = shipment.client
    # Admin orqali kelgan bo'lsa, natijani messages framework bilan ko'rsatamiz
    request = getattr(shipment, "_admin_request", None)

    if not client.telegram_id:
        if request:
            transaction.on_commit(
                lambda: messages.warning(
                    request,
                    f"⚠️ «{client.name}» Telegram botga ulanmagan. Xabar yuborilmadi.",
                )
            )
        return

    # Xabar faqat DB transaction muvaffaqiyatli commit bo'lgandan keyin ketadi —
    # aks holda rollback bo'lgan holatda ham xabar ketib qolishi mumkin edi
    transaction.on_commit(lambda: _send_status_notification(instance, client, request))


def _send_status_notification(stage, client, request=None):
    shipment = stage.shipment
    local_time = timezone.localtime(stage.created_at)

    lines = [
        f"👋 Hurmatli <b>{html.escape(client.name)}</b>!\n",
        "📢 Yukingiz holati bo'yicha yangi xabar:\n",
        f"📦 Jo'natma: <b>{html.escape(shipment.shipment_code)}</b>",
        f"🔄 Holat: <b>{html.escape(stage.get_stage_status_display())}</b>",
        "",
        f"📅 Vaqt: <b>{local_time.strftime('%d.%m.%Y')}</b> | 🕒 <b>{local_time.strftime('%H:%M')}</b>",
    ]

    success = send_telegram_message(client.telegram_id, "\n".join(lines))

    if request:
        if success:
            messages.success(request, f"Telegram xabari «{client.name}» mijoziga yuborildi.")
        else:
            messages.error(request, f"Telegram xabari «{client.name}» mijoziga yuborilmadi.")
