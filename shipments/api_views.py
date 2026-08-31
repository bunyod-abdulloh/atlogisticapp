from rest_framework import status
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from services.telegram_auth import InvalidInitData, parse_and_validate_init_data
from tracking.models import Client
from .models import Shipment
from .serializers import ShipmentHistoryItemSerializer, ShipmentTrackSerializer
from .throttles import CargoHistoryThrottle, CargoTrackThrottle


class CargoTrackView(APIView):
    throttle_classes = [CargoTrackThrottle]

    def get(self, request, tracking_number):
        try:
            shipment = (
                Shipment.objects.select_related("loading_city", "route")
                .prefetch_related("stages")
                .get(shipment_code__iexact=tracking_number.strip())
            )
        except Shipment.DoesNotExist:
            return Response(
                {"detail": "Bunday track-raqam topilmadi."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # context={"request": request} — rasm URL'ini to'liq (absolute) qilib qaytarish uchun shart
        return Response(ShipmentTrackSerializer(shipment, context={"request": request}).data)


class CargoHistoryPagination(LimitOffsetPagination):
    default_limit = 15
    max_limit = 50


class CargoHistoryView(APIView):
    """
    GET /user/api/history/?limit=15&offset=0
    Header: X-Telegram-Init-Data: <Telegram.WebApp.initData>

    MAXFIY — faqat Telegram orqali tasdiqlangan mijozning barcha
    shipmentlarini qaytaradi (qidirilganlarini emas).
    """

    throttle_classes = [CargoHistoryThrottle]
    pagination_class = CargoHistoryPagination

    def get(self, request):
        init_data = request.headers.get("X-Telegram-Init-Data", "")

        try:
            telegram_user = parse_and_validate_init_data(init_data)
        except InvalidInitData as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_401_UNAUTHORIZED)

        telegram_id = telegram_user.get("id")

        try:
            client = Client.objects.get(telegram_id=telegram_id)
        except Client.DoesNotExist:
            return Response({"count": 0, "next": None, "previous": None, "results": []})

        # MUHIM: mijozning BARCHA jo'natmalari — qidirilgan raqamlar emas
        qs = Shipment.objects.filter(client=client).order_by("-created_at")

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(qs, request, view=self)
        serializer = ShipmentHistoryItemSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
