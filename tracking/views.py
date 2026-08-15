from django.shortcuts import render
from rest_framework.generics import ListAPIView
from rest_framework.generics import RetrieveAPIView
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import AllowAny
from rest_framework.throttling import AnonRateThrottle

from .models import Cargo
from .permissions import IsTelegramWebAppUser
from .serializers import CargoHistoryListSerializer
from .serializers import CargoTrackSerializer


def index(request):
    return render(request, "index.html")


class CargoTrackThrottle(AnonRateThrottle):
    # Track-nomerlarni "urinib ko'rish" (enumeration) hujumini
    # sekinlashtirish uchun. settings.py da rate qiymatini belgilaymiz.
    scope = "cargo_track"


class CargoTrackView(RetrieveAPIView):
    # Mijoz shaxsiy kabinetsiz, faqat track-nomer bilan qidiradi —
    # shuning uchun login talab qilinmaydi.
    permission_classes = [AllowAny]
    throttle_classes = [CargoTrackThrottle]

    serializer_class = CargoTrackSerializer
    lookup_field = "tracking_number"
    lookup_url_kwarg = "tracking_number"

    def get_queryset(self):
        # select_related — client'ni alohida query bilan olmaslik uchun
        # (garchi serializer'da client ko'rsatilmasa ham, kelajakda
        # kerak bo'lishi mumkin).
        # prefetch_related — history'ni N+1 query muammosisiz olish uchun,
        # chunki har bir Cargo uchun bir nechta CargoStatusUpdate bor.
        return Cargo.objects.select_related("client").prefetch_related("history")


class CargoHistoryThrottle(AnonRateThrottle):
    scope = "cargo_history"


class CargoHistoryPagination(LimitOffsetPagination):
    default_limit = 15  # frontend hech narsa yubormasa shuncha keladi
    max_limit = 50  # ?limit=1000 deb urinishning oldini olamiz


class CargoHistoryListView(ListAPIView):
    permission_classes = [IsTelegramWebAppUser]
    throttle_classes = [CargoHistoryThrottle]
    pagination_class = CargoHistoryPagination
    serializer_class = CargoHistoryListSerializer

    def get_queryset(self):
        # IsTelegramWebAppUser allaqachon tekshirib, request.telegram_user'ni yozgan —
        # shu yerda faqat foydalanamiz
        telegram_id = self.request.telegram_user["id"]

        return (
            Cargo.objects
            .select_related("client")
            .filter(client__telegram_id=telegram_id)
            .order_by("-created_at")
        )
