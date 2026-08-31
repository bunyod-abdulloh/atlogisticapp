from django.contrib import admin
from django.utils.html import format_html

from .models import (
    Client,
    Cargo,
    CargoStatusUpdate,
    StatusCategory,
)


# ============================================================
# CLIENT
# ============================================================

class ClientCargoInline(admin.TabularInline):
    model = Cargo

    extra = 0

    can_delete = False

    fields = (
        "tracking_number",
        "origin",
        "destination",
        "current_status_display",
        "created_by",
    )

    readonly_fields = (
        "tracking_number",
        "origin",
        "destination",
        "current_status_display",
        "created_by",
    )

    show_change_link = True

    ordering = (
        "-created_at",
    )

    @admin.display(description="Status")
    def current_status_display(self, obj):
        text = (
                obj.current_status_text
                or obj.get_current_status_category_display()
        )

        return format_html(
            """
            <span style="
                display:inline-flex;
                align-items:center;
                gap:7px;
                padding:5px 11px;
                border-radius:20px;
                background:#eef2ff;
                color:#3730a3;
                font-weight:600;
                font-size:12px;
                white-space:nowrap;
            ">
                <i class="fas fa-circle-check"></i>
                {}
            </span>
            """,
            text,
        )


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = (
        "name_display",
        "phone_display",
        "cargo_count_display",
        "created_at_display",
    )

    search_fields = (
        "name",
        "phone",
    )

    list_filter = (
        "created_at",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
        "cargo_count_display",
    )

    fields = (
        "name",
        "telegram_id",
        "phone",
        "cargo_count_display",
        "created_at",
        "updated_at",
    )

    inlines = (
        ClientCargoInline,
    )

    list_per_page = 25

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .prefetch_related("cargos")
        )

    @admin.display(
        description="Mijoz",
        ordering="name",
    )
    def name_display(self, obj):
        return format_html(
            """
            <div style="
                display:flex;
                align-items:center;
                gap:9px;
            ">
                <span style="
                    width:32px;
                    height:32px;
                    border-radius:9px;
                    display:inline-flex;
                    align-items:center;
                    justify-content:center;
                    background:#eef2ff;
                    color:#4f46e5;
                ">
                    <i class="fas fa-user"></i>
                </span>

                <strong style="font-size:14px;">
                    {}
                </strong>
            </div>
            """,
            obj.name,
        )

    @admin.display(
        description="Telefon",
        ordering="phone",
    )
    def phone_display(self, obj):
        return format_html(
            """
            <span style="
                display:inline-flex;
                align-items:center;
                gap:7px;
                color:#475569;
            ">
                <i class="fas fa-phone"></i>
                {}
            </span>
            """,
            obj.phone,
        )

    @admin.display(
        description="Buyurtmalar",
    )
    def cargo_count_display(self, obj):
        count = obj.cargos.count()

        return format_html(
            """
            <span style="
                display:inline-flex;
                align-items:center;
                gap:7px;
                padding:5px 11px;
                border-radius:9px;
                background:#eff6ff;
                color:#2563eb;
                font-weight:600;
            ">
                <i class="fas fa-box"></i>
                {}
            </span>
            """,
            count,
        )

    @admin.display(
        description="Qo‘shilgan sana",
        ordering="created_at",
    )
    def created_at_display(self, obj):
        return format_html(
            """
            <span style="
                display:inline-flex;
                align-items:center;
                gap:7px;
                color:#64748b;
            ">
                <i class="far fa-calendar-alt"></i>
                {}
            </span>
            """,
            obj.created_at.strftime("%d.%m.%Y %H:%M"),
        )


# ============================================================
# CARGO STATUS INLINE
# ============================================================

# class CargoStatusUpdateInline(admin.TabularInline):
#     model = CargoStatusUpdate
#
#     extra = 1
#
#     fields = (
#         "status_category",
#         "created_by",
#         "created_at",
#         "custom_text",
#         "location",
#         "comment",
#     )
#
#     readonly_fields = (
#         "status_category",
#         "created_by",
#         "created_at",
#     )
#
#     ordering = (
#         "-created_at",
#     )
#
#     show_change_link = True
#
#     verbose_name = "Status"
#
#     verbose_name_plural = "Statuslar tarixi"
#
#
# # ============================================================
# # CARGO
# # ============================================================
#
# @admin.register(Cargo)
# class CargoAdmin(admin.ModelAdmin):
#     list_display = (
#         "tracking_number_display",
#         "client_display",
#         "route_display",
#         "status_display",
#         "created_by_display",
#     )
#
#     list_display_links = (
#         "tracking_number_display",
#         "client_display",
#     )
#
#     # --------------------------------------------------------
#     # FILTER
#     # --------------------------------------------------------
#
#     list_filter = (
#         "current_status_category",
#         "created_by",
#         "origin",
#         "destination",
#         "created_at",
#     )
#
#     # --------------------------------------------------------
#     # SEARCH
#     # --------------------------------------------------------
#
#     search_fields = (
#         "tracking_number",
#
#         "client__name",
#         "client__phone",
#
#         "origin",
#         "destination",
#
#         "current_status_text",
#
#         "created_by__username",
#         "created_by__first_name",
#         "created_by__last_name",
#     )
#
#     # --------------------------------------------------------
#     # OPTIMIZATION
#     # --------------------------------------------------------
#
#     list_select_related = (
#         "client",
#         "created_by",
#     )
#
#     # --------------------------------------------------------
#     # FORM
#     # --------------------------------------------------------
#
#     autocomplete_fields = (
#         "client",
#     )
#
#     readonly_fields = (
#         "created_by",
#         "created_at",
#         "updated_at",
#         "current_status_preview",
#     )
#
#     fieldsets = (
#         (
#             "Buyurtma ma'lumotlari",
#             {
#                 "fields": (
#                     "tracking_number",
#                     "client",
#                     "origin",
#                     "destination",
#                 ),
#             },
#         ),
#
#         (
#             "Joriy status",
#             {
#                 "fields": (
#                     "current_status_category",
#                     "current_status_text",
#                     "current_status_preview",
#                 ),
#             },
#         ),
#
#         (
#             "Admin ma'lumotlari",
#             {
#                 "fields": (
#                     "created_by",
#                 ),
#             },
#         ),
#
#         (
#             "Vaqt",
#             {
#                 "fields": (
#                     "created_at",
#                     "updated_at",
#                 ),
#             },
#         ),
#     )
#
#     # --------------------------------------------------------
#     # INLINE
#     # --------------------------------------------------------
#
#     inlines = (
#         CargoStatusUpdateInline,
#     )
#
#     list_per_page = 25
#
#     # --------------------------------------------------------
#     # SAVE CARGO
#     # --------------------------------------------------------
#
#     def save_model(self, request, obj, form, change):
#         if not change and not obj.created_by:
#             obj.created_by = request.user
#
#         # Cargo.save() ichida history yaratilganda requestga kirish uchun
#         obj._admin_request = request
#
#         super().save_model(request, obj, form, change)
#
#     # --------------------------------------------------------
#     # SAVE STATUS INLINE
#     # --------------------------------------------------------
#
#     def save_formset(
#             self,
#             request,
#             form,
#             formset,
#             change,
#     ):
#         instances = formset.save(commit=False)
#
#         for instance in instances:
#             if not instance.created_by:
#                 instance.created_by = request.user
#
#             # Admin request'ni signalga yetkazamiz
#             instance._admin_request = request
#
#             instance.save()
#
#         for deleted_object in formset.deleted_objects:
#             deleted_object.delete()
#
#         formset.save_m2m()
#
#     # ========================================================
#     # DISPLAY METHODS
#     # ========================================================
#
#     @admin.display(
#         description="Track-nomer",
#         ordering="tracking_number",
#     )
#     def tracking_number_display(self, obj):
#
#         return format_html(
#             """
#             <div style="
#                 display:flex;
#                 align-items:center;
#                 gap:9px;
#             ">
#                 <span style="
#                     width:34px;
#                     height:34px;
#                     border-radius:9px;
#                     display:inline-flex;
#                     align-items:center;
#                     justify-content:center;
#                     background:#eff6ff;
#                     color:#2563eb;
#                 ">
#                     <i class="fas fa-box"></i>
#                 </span>
#
#                 <strong style="
#                     font-size:14px;
#                     letter-spacing:.3px;
#                 ">
#                     {}
#                 </strong>
#             </div>
#             """,
#             obj.tracking_number,
#         )
#
#     # --------------------------------------------------------
#
#     @admin.display(
#         description="Mijoz",
#         ordering="client__name",
#     )
#     def client_display(self, obj):
#
#         return format_html(
#             """
#             <div>
#                 <div style="
#                     display:flex;
#                     align-items:center;
#                     gap:7px;
#                 ">
#                     <i class="fas fa-user"
#                        style="color:#6366f1;">
#                     </i>
#
#                     <strong>
#                         {}
#                     </strong>
#                 </div>
#
#                 <small style="
#                     color:#64748b;
#                     display:inline-flex;
#                     align-items:center;
#                     gap:5px;
#                     margin-top:3px;
#                 ">
#                     <i class="fas fa-phone"></i>
#                     {}
#                 </small>
#             </div>
#             """,
#             obj.client.name,
#             obj.client.phone,
#         )
#
#     # --------------------------------------------------------
#
#     @admin.display(
#         description="Yo'nalish",
#     )
#     def route_display(self, obj):
#
#         return format_html(
#             """
#             <div style="
#                 line-height:1.8;
#             ">
#
#                 <div style="
#                     display:flex;
#                     align-items:center;
#                     gap:7px;
#                 ">
#                     <i class="fas fa-location-dot"
#                        style="color:#ef4444;">
#                     </i>
#
#                     <span>
#                         {}
#                     </span>
#                 </div>
#
#                 <div style="
#                     display:flex;
#                     align-items:center;
#                     gap:7px;
#                 ">
#                     <i class="fas fa-flag-checkered"
#                        style="color:#16a34a;">
#                     </i>
#
#                     <span>
#                         {}
#                     </span>
#                 </div>
#
#             </div>
#             """,
#             obj.origin,
#             obj.destination,
#         )
#
#     # --------------------------------------------------------
#
#     @admin.display(
#         description="Status",
#         ordering="current_status_category",
#     )
#     def status_display(self, obj):
#
#         category = obj.current_status_category
#
#         colors = {
#             StatusCategory.ACCEPTED: (
#                 "#198754",
#                 "#d1e7dd",
#                 "fa-circle-check",
#             ),
#
#             StatusCategory.CUSTOMS: (
#                 "#fd7e14",
#                 "#ffe5d0",
#                 "fa-shield-halved",
#             ),
#
#             StatusCategory.IN_TRANSIT: (
#                 "#0d6efd",
#                 "#cfe2ff",
#                 "fa-truck-fast",
#             ),
#
#             StatusCategory.ARRIVED_WAREHOUSE: (
#                 "#6f42c1",
#                 "#e2d9f3",
#                 "fa-warehouse",
#             ),
#
#             StatusCategory.OUT_FOR_DELIVERY: (
#                 "#0dcaf0",
#                 "#cff4fc",
#                 "fa-truck",
#             ),
#
#             StatusCategory.DELIVERED: (
#                 "#198754",
#                 "#d1e7dd",
#                 "fa-circle-check",
#             ),
#
#             StatusCategory.CUSTOM: (
#                 "#6c757d",
#                 "#e2e3e5",
#                 "fa-pen",
#             ),
#         }
#
#         text_color, background, icon = colors.get(
#             category,
#             (
#                 "#6c757d",
#                 "#e2e3e5",
#                 "fa-circle-info",
#             ),
#         )
#
#         text = (
#                 obj.current_status_text
#                 or obj.get_current_status_category_display()
#         )
#
#         return format_html(
#             """
#             <span style="
#                 display:inline-flex;
#                 align-items:center;
#                 gap:7px;
#                 padding:6px 12px;
#                 border-radius:20px;
#                 background:{};
#                 color:{};
#                 font-size:12px;
#                 font-weight:600;
#                 white-space:nowrap;
#             ">
#                 <i class="fas {}"></i>
#                 {}
#             </span>
#             """,
#             background,
#             text_color,
#             icon,
#             text,
#         )
#
#     # --------------------------------------------------------
#
#     @admin.display(
#         description="Yaratgan admin",
#         ordering="created_by__username",
#     )
#     def created_by_display(self, obj):
#
#         if not obj.created_by:
#             return format_html(
#                 """
#                 <span style="
#                     color:#94a3b8;
#                 ">
#                     <i class="fas fa-user-slash"></i>
#                     —
#                 </span>
#                 """
#             )
#
#         user = obj.created_by
#
#         name = user.get_full_name()
#
#         if name:
#             return format_html(
#                 """
#                 <div>
#                     <div style="
#                         display:flex;
#                         align-items:center;
#                         gap:7px;
#                     ">
#                         <i class="fas fa-user-shield"
#                            style="color:#6366f1;">
#                         </i>
#
#                         <strong>
#                             {}
#                         </strong>
#                     </div>
#
#                     <small style="
#                         color:#64748b;
#                         margin-left:22px;
#                     ">
#                         @{}
#                     </small>
#                 </div>
#                 """,
#                 name,
#                 user.username,
#             )
#
#         return format_html(
#             """
#             <span style="
#                 display:inline-flex;
#                 align-items:center;
#                 gap:7px;
#             ">
#                 <i class="fas fa-user-shield"
#                    style="color:#6366f1;">
#                 </i>
#
#                 <strong>
#                     {}
#                 </strong>
#             </span>
#             """,
#             user.username,
#         )
#
#     # --------------------------------------------------------
#
#     # @admin.display(
#     #     description="Qabul qilgan",
#     #     ordering="accepted_by__username",
#     # )
#     # def accepted_by_display(self, obj):
#     #
#     #     if not obj.accepted_by:
#     #         return format_html(
#     #             """
#     #             <span style="
#     #                 color:#94a3b8;
#     #                 font-size:12px;
#     #                 display:inline-flex;
#     #                 align-items:center;
#     #                 gap:6px;
#     #             ">
#     #                 <i class="fas fa-clock"></i>
#     #                 Hali qabul qilinmagan
#     #             </span>
#     #             """
#     #         )
#     #
#     #     user = obj.accepted_by
#     #
#     #     name = user.get_full_name()
#     #
#     #     if name:
#     #         return format_html(
#     #             """
#     #             <div>
#     #                 <div style="
#     #                     display:flex;
#     #                     align-items:center;
#     #                     gap:7px;
#     #                 ">
#     #                     <i class="fas fa-circle-check"
#     #                        style="color:#16a34a;">
#     #                     </i>
#     #
#     #                     <strong>
#     #                         {}
#     #                     </strong>
#     #                 </div>
#     #
#     #                 <small style="
#     #                     color:#64748b;
#     #                     margin-left:22px;
#     #                 ">
#     #                     @{}
#     #                 </small>
#     #             </div>
#     #             """,
#     #             name,
#     #             user.username,
#     #         )
#     #
#     #     return format_html(
#     #         """
#     #         <span style="
#     #             display:inline-flex;
#     #             align-items:center;
#     #             gap:7px;
#     #         ">
#     #             <i class="fas fa-circle-check"
#     #                style="color:#16a34a;">
#     #             </i>
#     #
#     #             <strong>
#     #                 {}
#     #             </strong>
#     #         </span>
#     #         """,
#     #         user.username,
#     #     )
#
#     # --------------------------------------------------------
#
#     @admin.display(
#         description="Status ko‘rinishi",
#     )
#     def current_status_preview(self, obj):
#
#         if not obj.pk:
#             return format_html(
#                 """
#                 <span style="
#                     display:inline-flex;
#                     align-items:center;
#                     gap:7px;
#                     color:#94a3b8;
#                 ">
#                     <i class="fas fa-box-open"></i>
#                     Yangi yuk
#                 </span>
#                 """
#             )
#
#         return self.status_display(obj)
#

# ============================================================
# ADMIN SITE CONFIG
# ============================================================

admin.site.site_header = "A&T Logistics"
admin.site.site_title = "A&T Logistics Admin"
admin.site.index_title = "Boshqaruv paneli"
