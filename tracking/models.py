from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models


# Menejer status yozganda tanlaydigan tayyor variantlar.
# "value" — badge rangini aniqlash uchun kategoriya (frontend shu bo'yicha
# "yetkazildi" holatini yashil qilib ko'rsatadi), "label" — ekranda ko'rinadigan matn.
class StatusCategory(models.TextChoices):
    ACCEPTED = "accepted", "Qabul qilindi (Xitoy sklad)"
    CUSTOMS = "customs", "Chegaradan o'tmoqda"
    IN_TRANSIT = "in_transit", "Yo'lda"
    ARRIVED_WAREHOUSE = "arrived_warehouse", "Toshkent skladiga yetib keldi"
    OUT_FOR_DELIVERY = "out_for_delivery", "Yetkazib berish jarayonida"
    DELIVERED = "delivered", "Yetkazib berildi"
    CUSTOM = "custom", "Boshqa (o'z matni)"


tracking_number_validator = RegexValidator(
    regex=r"^[A-Za-z0-9\-]+$",
    message="Track-nomerda faqat harf, raqam va tire (-) bo'lishi mumkin.",
)


class Client(models.Model):
    name = models.CharField(
        max_length=120,
        verbose_name="Ism va familiya",
    )

    telegram_id = models.BigIntegerField(
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Telegram ID",
    )

    phone = models.CharField(
        max_length=32,
        unique=True,
        verbose_name="Telefon raqami",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Qo'shilgan sana",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Yangilangan sana",
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Mijoz"
        verbose_name_plural = "Mijozlar"

    def __str__(self):
        return f"{self.name} — {self.phone}"


class Cargo(models.Model):
    tracking_number = models.CharField(
        max_length=32,
        unique=True,
        db_index=True,
        validators=[tracking_number_validator],
        help_text="Track-nomer, masalan: ATL-24081",
    )

    client = models.ForeignKey(
        Client,
        on_delete=models.PROTECT,
        related_name="cargos",
        verbose_name="Mijoz",
    )

    origin = models.CharField(
        max_length=120,
        verbose_name="Qayerdan",
    )

    destination = models.CharField(
        max_length=120,
        verbose_name="Qayerga",
    )

    current_status_category = models.CharField(
        max_length=20,
        choices=StatusCategory.choices,
        default=StatusCategory.ACCEPTED,
        verbose_name="Joriy status",
    )

    current_status_text = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Joriy status matni",
    )

    # Buyurtmani kim yaratgan
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_cargos",
        verbose_name="Yaratgan admin",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Yaratilgan vaqt",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Yangilangan vaqt",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Yuk"
        verbose_name_plural = "Yuklar"

    def __str__(self):
        return f"{self.tracking_number} — {self.client.name}"

    def sync_current_status(self):
        latest = self.history.order_by("-created_at").first()

        if not latest:
            return

        self.current_status_category = latest.status_category
        self.current_status_text = latest.display_text

        self.save(
            update_fields=[
                "current_status_category",
                "current_status_text",
                "updated_at",
            ]
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # DB'dan yuklangan (yoki hozirgi) statusni saqlab qo'yamiz —
        # keyinroq save() da "status o'zgardimi?" ni shu bilan solishtiramiz
        self._original_status_category = self.current_status_category

    def save(self, *args, **kwargs):
        is_new = self._state.adding

        # sync_current_status() faqat shu fieldlarni yozadi — demak bu chaqiruv
        # tarixdan (CargoStatusUpdate.save()) kelayapti, admin formadan emas.
        # Shu tekshiruv orqali cheksiz loopni oldini olamiz.
        sync_fields = {"current_status_category", "current_status_text", "updated_at"}
        is_sync_call = kwargs.get("update_fields") is not None and set(kwargs["update_fields"]) <= sync_fields

        status_changed = (
                not is_new
                and not is_sync_call
                and self.current_status_category != self._original_status_category
        )

        super().save(*args, **kwargs)

        if is_new or status_changed:
            history_entry = CargoStatusUpdate(
                cargo=self,
                status_category=self.current_status_category,
                custom_text=(
                    self.current_status_text
                    if self.current_status_category == StatusCategory.CUSTOM
                    else ""
                ),
                created_by=self.created_by,
            )

            # Admin view'dan kelgan requestni tarix yozuviga uzatamiz —
            # shu orqali signal admin panelga alert chiqara oladi
            if hasattr(self, "_admin_request"):
                history_entry._admin_request = self._admin_request

            history_entry.save()


class CargoStatusUpdate(models.Model):
    cargo = models.ForeignKey(
        Cargo,
        on_delete=models.CASCADE,
        related_name="history",
        verbose_name="Yuk",
    )

    status_category = models.CharField(
        max_length=20,
        choices=StatusCategory.choices,
        verbose_name="Status",
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cargo_status_updates",
        verbose_name="Admin",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Yaratilgan vaqt",
    )

    custom_text = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Maxsus matn",
    )

    location = models.CharField(
        max_length=120,
        blank=True,
        verbose_name="Joylashuv",
    )

    comment = models.TextField(
        blank=True,
        verbose_name="Izoh",
    )

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Status yangilanishi"
        verbose_name_plural = "Status tarixi"

    def __str__(self):
        return f"{self.cargo.tracking_number}: {self.display_text}"

    @property
    def display_text(self):
        if (
                self.status_category == StatusCategory.CUSTOM
                and self.custom_text
        ):
            return self.custom_text

        return self.get_status_category_display()

    def clean(self):
        if (
                self.status_category == StatusCategory.CUSTOM
                and not self.custom_text.strip()
        ):
            raise ValidationError(
                {
                    "custom_text":
                        "\"Boshqa (o'z matni)\" tanlanganda "
                        "matn kiritish shart."
                }
            )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        self.cargo.sync_current_status()
