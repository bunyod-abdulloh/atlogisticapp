from django.contrib import admin
from django.db.models import Count
from django.urls import reverse
from django.utils.html import format_html

from .models import Client


class ClientAdmin(admin.ModelAdmin):
    list_display = (
        "name_display",
        "phone_display",
        "shipment_count_display",
        "created_at_display",
    )

    search_fields = ("name", "phone")
    list_filter = ("created_at",)
    list_per_page = 25

    # Bitta so'rovda barcha mijozlarning shipment sonini hisoblaymiz —
    # har bir qator uchun alohida so'rov yubormaslik uchun (N+1 oldini olish)
    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .annotate(shipment_count=Count("shipments"))
        )

    @admin.display(description="Mijoz", ordering="name")
    def name_display(self, obj):
        return obj.name

    @admin.display(description="Telefon")
    def phone_display(self, obj):
        return obj.phone

    @admin.display(description="Jo'natmalar", ordering="shipment_count")
    def shipment_count_display(self, obj):
        count = obj.shipment_count  # annotate qilingan qiymat, qo'shimcha so'rov yo'q

        # Bosilganda: aynan shu mijozning jo'natmalari ro'yxatiga o'tadi
        url = reverse("admin:shipments_shipment_changelist") + f"?client__id__exact={obj.pk}"

        return format_html(
            '<a href="{}" style="'
            'display:inline-flex;align-items:center;gap:6px;'
            'padding:4px 10px;border-radius:8px;'
            'background:var(--bs-info-bg-subtle);'
            'color:var(--bs-info-text-emphasis);'
            'font-weight:600;text-decoration:none;">'
            '<i class="fas fa-box"></i> {}</a>',
            url,
            count,
        )

    @admin.display(description="Qo'shilgan sana", ordering="created_at")
    def created_at_display(self, obj):
        return obj.created_at.strftime("%d.%m.%Y %H:%M")


admin.site.register(Client, ClientAdmin)