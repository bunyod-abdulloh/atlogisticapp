from django.db import models


class Client(models.Model):
    name = models.CharField(
        max_length=120,
        verbose_name="Mijoz",
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
        verbose_name = "Mijoz"
        verbose_name_plural = "Mijozlar"

    def __str__(self):
        return f"{self.name} — {self.phone}"


