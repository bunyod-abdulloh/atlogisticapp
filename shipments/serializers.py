from rest_framework import serializers

from .models import Shipment, Stage


class StageHistorySerializer(serializers.ModelSerializer):
    """Frontend timeline formatiga mos: status_display, location, timestamp, comment."""

    status_display = serializers.CharField(source="get_stage_status_display")
    timestamp = serializers.DateTimeField(source="created_at")

    # Stage modelida hozircha bu maydonlar yo'q — bo'sh qaytariladi.
    # Agar kerak bo'lsa, Stage'ga location/comment CharField qo'shish kerak.
    location = serializers.SerializerMethodField()
    comment = serializers.SerializerMethodField()

    class Meta:
        model = Stage
        fields = ["status_display", "location", "timestamp", "comment"]

    def get_location(self, obj):
        return ""

    def get_comment(self, obj):
        return ""


class ShipmentTrackSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display")
    tracking_number = serializers.CharField(source="shipment_code")
    origin = serializers.CharField(source="loading_city.name", default="—")
    destination = serializers.SerializerMethodField()
    history = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Shipment
        fields = ["tracking_number", "status", "status_display", "origin", "destination", "image", "history"]

    def get_destination(self, obj):
        return obj.route.name if obj.route else "—"

    def get_history(self, obj):
        qs = obj.stages.order_by("created_at")
        return StageHistorySerializer(qs, many=True).data

    def get_image(self, obj):
        if not obj.img:
            return None
        request = self.context.get("request")
        # request contextsiz faqat nisbiy yo'l qaytadi (masalan testda) —
        # shuning uchun view'da context={"request": request} berish SHART
        return request.build_absolute_uri(obj.img.url) if request else obj.img.url


class ShipmentHistoryItemSerializer(serializers.ModelSerializer):
    """GET /history/ ro'yxatidagi har bir qator."""

    status_display = serializers.CharField(source="get_status_display")
    tracking_number = serializers.CharField(source="shipment_code")

    class Meta:
        model = Shipment
        fields = ["tracking_number", "status", "status_display", "created_at"]
