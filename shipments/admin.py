from datetime import timedelta

from django.contrib import admin
from django.db.models import Count, ExpressionWrapper, F, DurationField
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html

from .models import LoadingCity, Route, Sender, Shipment, Stage, TransportCompany, Driver

STATUS_COLORS = {
    Shipment.StatusCode.SHIPPING: "#6c757d",
    Shipment.StatusCode.AT_BORDER: "#0d6efd",
    Shipment.StatusCode.RELOADING: "#fd7e14",
    Shipment.StatusCode.DELIVERED: "#198754",
}


@admin.register(Sender)
class SenderAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(LoadingCity)
class LoadingCityAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(TransportCompany)
class TransportCompanyAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ("full_name", "phone", "plate_number")
    search_fields = ("full_name", "phone", "plate_number")


class StageInline(admin.TabularInline):
    """Faqat tarixni ko'rish uchun — Stage endi qo'lda qo'shilmaydi/o'zgartirilmaydi,
    u avtomatik ravishda Shipment.status o'zgarganda yaratiladi."""

    model = Stage
    extra = 0
    fields = ("stage_status", "created_at")
    readonly_fields = ("stage_status", "created_at")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class ShipmentOverdueFilter(admin.SimpleListFilter):
    """Shipment.planned_shipping_date vs actual_shipping_date solishtirib kechikkanlarni ajratadi."""

    title = "Kechikkanmi"
    parameter_name = "overdue"

    def lookups(self, request, model_admin):
        return [("yes", "Kechikkan"), ("no", "Vaqtida / hali topshirilmagan")]

    def _annotated(self, queryset):
        return queryset.filter(
            actual_shipping_date__isnull=False
        ).annotate(
            deviation=ExpressionWrapper(
                F("actual_shipping_date") - F("planned_shipping_date"),
                output_field=DurationField(),
            )
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == "yes":
            return self._annotated(queryset).filter(deviation__gt=timedelta(days=0))
        if value == "no":
            overdue_ids = self._annotated(queryset).filter(
                deviation__gt=timedelta(days=0)
            ).values_list("pk", flat=True)
            return queryset.exclude(pk__in=overdue_ids)
        return queryset


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = (
        "client",
        "driver",
        "shipment_code",
        "route",
        "status",
        "planned_shipping_date",
        "actual_shipping_date",
        "overdue_badge",
    )
    list_filter = (
        "status",
        "loading_city",
        ShipmentOverdueFilter,
        "planned_shipping_date",
        "actual_shipping_date",
        "client__name",
        "driver",
    )
    search_fields = ("shipment_code", "client__name", "sender__name", "recipient", "driver__plate_number")
    date_hierarchy = "planned_shipping_date"
    inlines = [StageInline]
    readonly_fields = ("shipment_code",)
    autocomplete_fields = ("client", "sender", "loading_city", "route", "transport_company", "driver")
    list_editable = ("status", "actual_shipping_date")
    list_display_links = ("client",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("client", "driver", "route")

    def save_model(self, request, obj, form, change):
        obj._admin_request = request
        super().save_model(request, obj, form, change)

    @admin.display(description="Kechikish (kun)")
    def overdue_badge(self, obj: Shipment):
        if not obj.actual_shipping_date:
            return "—"
        deviation = (obj.actual_shipping_date - obj.planned_shipping_date).days
        if deviation <= 0:
            return "—"
        color = "var(--bs-danger-text-emphasis)" if deviation > 3 else "var(--bs-warning-text-emphasis)"
        return format_html('<b style="color:{}">+{} kun</b>', color, deviation)

    # --- Dashboard ---
    def get_urls(self):
        custom_urls = [
            path("dashboard/", self.admin_site.admin_view(self.dashboard_view), name="shipments_dashboard"),
        ]
        return custom_urls + super().get_urls()

    def dashboard_view(self, request):
        context = {
            **self.admin_site.each_context(request),
            "title": "Yuklar dashboardi",
            **self._build_dashboard_stats(),
        }
        return TemplateResponse(request, "admin/shipments/dashboard.html", context)

    def _build_dashboard_stats(self):
        shipment_list_url = reverse("admin:shipments_shipment_changelist")

        counts_by_status = dict(
            Shipment.objects.values_list("status").annotate(count=Count("id")).values_list("status", "count")
        )

        overdue_total = Shipment.objects.filter(
            actual_shipping_date__isnull=False
        ).annotate(
            deviation=ExpressionWrapper(
                F("actual_shipping_date") - F("planned_shipping_date"),
                output_field=DurationField(),
            )
        ).filter(deviation__gt=timedelta(days=0)).count()

        return {
            "total_shipments": Shipment.objects.count(),
            "total_url": shipment_list_url,
            "status_counts": [
                {
                    "label": label,
                    "count": counts_by_status.get(code, 0),
                    "color": STATUS_COLORS.get(code),
                    "url": f"{shipment_list_url}?status__exact={code}",
                }
                for code, label in Shipment.StatusCode.choices
            ],
            "overdue_total": overdue_total,
            "overdue_total_url": f"{shipment_list_url}?overdue=yes",
        }
