import uuid

from django.db import models
from django.utils import timezone
from django.utils.text import slugify

from tracking.models import Client


def client_image_path(instance, filename):
    ext = filename.rsplit(".", 1)[-1] if "." in filename else ""
    client_slug = slugify(instance.client.name)
    timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
    unique = uuid.uuid4().hex[:8]
    return f"clients/{client_slug}/{timestamp}_{unique}.{ext}"


class Sender(models.Model):
    name = models.CharField("Jo'natuvchi nomi", max_length=255, unique=True)

    class Meta:
        verbose_name = "Jo'natuvchi"
        verbose_name_plural = "Jo'natuvchilar"
        ordering = ["name"]

    def __str__(self):
        return self.name


class LoadingCity(models.Model):
    name = models.CharField("Shahar nomi", max_length=255, unique=True)

    class Meta:
        verbose_name = "Yuklash shahri"
        verbose_name_plural = "Yuklash shaharlari"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Route(models.Model):
    name = models.CharField("Marshrut nomi", max_length=255, unique=True)

    class Meta:
        verbose_name = "Marshrut"
        verbose_name_plural = "Marshrutlar"
        ordering = ["name"]

    def __str__(self):
        return self.name


class TransportCompany(models.Model):
    name = models.CharField("Transport firmasi nomi", max_length=255, unique=True)

    class Meta:
        verbose_name = "Transport firmasi"
        verbose_name_plural = "Transport firmalari"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Driver(models.Model):
    full_name = models.CharField(verbose_name="Haydovchi", max_length=255, unique=True)
    phone = models.CharField(verbose_name="Telefon raqam", max_length=50, unique=True, db_index=True)
    tg_id = models.IntegerField(verbose_name="Telegram ID")
    plate_number = models.CharField(verbose_name="Fura raqami", max_length=50, unique=True)

    class Meta:
        verbose_name = "Haydovchi"
        verbose_name_plural = "Haydovchilar"
        ordering = ["plate_number"]

    def __str__(self):
        return f"{self.full_name} | {self.plate_number}"


class Shipment(models.Model):
    """Excel'dagi 'Отправки' varag'iga mos model."""

    class StatusCode(models.TextChoices):
        SHIPPING = "shipping", "Yuklashda"
        AT_BORDER = "at_border", "Ulug'chat/Xargosda"
        RELOADING = "reloading", "Qayta yuklashda"
        DELIVERED = "delivered", "Yetkazildi"

    shipment_code = models.CharField(
        "Jo'natma ID", max_length=20, unique=True, db_index=True,
        editable=False, blank=True,
        help_text="Avtomatik generatsiya qilinadi (masalan: ATLG-0001)",
    )
    client = models.ForeignKey(Client, on_delete=models.PROTECT, related_name="shipments", verbose_name="Mijoz")
    sender = models.ForeignKey(Sender, on_delete=models.PROTECT, related_name="shipments", verbose_name="Jo'natuvchi")
    recipient = models.CharField("Qabul qiluvchi", max_length=255)
    product = models.CharField("Tovar", max_length=255)
    loading_city = models.ForeignKey(LoadingCity, on_delete=models.PROTECT, related_name="shipments",
                                     verbose_name="Yuklash shahri")
    route = models.ForeignKey(Route, on_delete=models.PROTECT, related_name="shipments", null=True, blank=True,
                              verbose_name="Marshrut")
    transport_company = models.ForeignKey(TransportCompany, on_delete=models.PROTECT, related_name="shipments",
                                          null=True, blank=True, verbose_name="Transport firmasi")
    driver = models.ForeignKey(Driver, on_delete=models.PROTECT, related_name="shipments", null=True, blank=True,
                               verbose_name="Haydovchi")
    img = models.ImageField(upload_to=client_image_path, verbose_name="Rasm")

    # Endi hisoblanadigan property emas, haqiqiy field — shu tufayli
    # admin list_editable to'g'ri ishlaydi va bazada indekslanadi/filtrlanadi
    status = models.CharField(
        "Status", max_length=20, choices=StatusCode.choices,
        default=StatusCode.SHIPPING, db_index=True,
    )

    planned_shipping_date = models.DateField("Jo'natish sanasi (reja)")
    actual_shipping_date = models.DateField("Jo'natish sanasi (fakt)", null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Jo'natma"
        verbose_name_plural = "Jo'natmalar"
        ordering = ["-planned_shipping_date", "shipment_code"]

    def __str__(self):
        return self.shipment_code or f"Jo'natma #{self.pk}"

    def save(self, *args, **kwargs):
        is_new = self._state.adding

        # Statusning eski qiymatini bazadan olamiz (self.status emas!) — chunki
        # instance memory'da status maydoni allaqachon yangi qiymatga
        # o'zgartirilgan bo'ladi (masalan admin list_editable orqali kelganda)
        old_status = None
        if not is_new:
            old_status = Shipment.objects.filter(pk=self.pk).values_list("status", flat=True).first()

        super().save(*args, **kwargs)

        if is_new and not self.shipment_code:
            self.shipment_code = f"ATLG-{self.pk:04d}"
            super().save(update_fields=["shipment_code"])

        # Yaratilganda ham, status o'zgarganda ham tarixga yozamiz.
        # Bu Stage yaratish Stage.post_save signalini ishga tushiradi va
        # o'sha yerda mijozga Telegram xabari ketadi.
        if is_new or old_status != self.status:
            Stage.objects.create(shipment=self, stage_status=self.status)


class Stage(models.Model):
    """Jo'natma statusi tarixi (audit log) — status har o'zgarganda yangi yozuv qo'shiladi, eskisi o'zgartirilmaydi."""

    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name="stages", verbose_name="Jo'natma")
    stage_status = models.CharField("Status", max_length=20, choices=Shipment.StatusCode.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Bosqich"
        verbose_name_plural = "Bosqichlar"
        ordering = ["shipment", "created_at"]

    def __str__(self):
        return f"{self.shipment.shipment_code} — {self.get_stage_status_display()}"
