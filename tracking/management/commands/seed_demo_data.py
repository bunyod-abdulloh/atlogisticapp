from django.core.management.base import BaseCommand
from django.utils import timezone

from tracking.models import Cargo, CargoStatusUpdate, StatusCategory


class Command(BaseCommand):
    help = "Frontend (tracking-frontend/script.js DEMO_DATA) bilan bir xil demo yuklarni yaratadi."

    def handle(self, *args, **options):
        Cargo.objects.filter(
            tracking_number__in=["ATL-24081", "ATL-24002", "ATL-24150"]
        ).delete()

        # ATL-24081 — hali yo'lda
        cargo1 = Cargo.objects.create(
            tracking_number="ATL-24081",
            client_name="Aziz Aliyev",
            client_phone="+998901234567",
            origin="Guangzhou, Xitoy",
            destination="Toshkent, O'zbekiston",
        )
        for category, location, comment in [
            (StatusCategory.ACCEPTED, "Guangzhou", ""),
            (StatusCategory.CUSTOMS, "Xorgos", ""),
            (StatusCategory.IN_TRANSIT, "Shymkent", "Ob-havo sababli ~1 kunlik kechikish bo'lishi mumkin."),
        ]:
            CargoStatusUpdate.objects.create(
                cargo=cargo1, status_category=category, location=location, comment=comment
            )

        # ATL-24002 — yetkazib berilgan
        cargo2 = Cargo.objects.create(
            tracking_number="ATL-24002",
            client_name="Malika Yusupova",
            client_phone="+998912223344",
            origin="Guangzhou, Xitoy",
            destination="Samarqand, O'zbekiston",
        )
        for category, location, comment in [
            (StatusCategory.ACCEPTED, "Guangzhou", ""),
            (StatusCategory.CUSTOMS, "Xorgos", ""),
            (StatusCategory.ARRIVED_WAREHOUSE, "Toshkent", ""),
            (StatusCategory.DELIVERED, "Samarqand", "Mijoz tomonidan qabul qilingan."),
        ]:
            CargoStatusUpdate.objects.create(
                cargo=cargo2, status_category=category, location=location, comment=comment
            )

        # ATL-24150 — endigina qabul qilingan
        cargo3 = Cargo.objects.create(
            tracking_number="ATL-24150",
            client_name="Bekzod Qodirov",
            client_phone="+998933335566",
            origin="Guangzhou, Xitoy",
            destination="Farg'ona, O'zbekiston",
        )
        CargoStatusUpdate.objects.create(
            cargo=cargo3, status_category=StatusCategory.ACCEPTED, location="Guangzhou"
        )

        self.stdout.write(self.style.SUCCESS(
            f"Demo ma'lumotlar yaratildi: {Cargo.objects.count()} ta yuk "
            f"({timezone.now():%Y-%m-%d %H:%M})"
        ))
