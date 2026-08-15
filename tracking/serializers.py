from rest_framework import serializers

from .models import Cargo, CargoStatusUpdate


class CargoStatusUpdateSerializer(serializers.ModelSerializer):
    # Model'dagi property va field nomlarini frontend kutgan
    # kalitlarga moslaymiz — JS kodini o'zgartirmasdan ishlatish uchun.
    status_display = serializers.CharField(source="display_text", read_only=True)
    timestamp = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = CargoStatusUpdate
        fields = ["status_display", "location", "timestamp", "comment"]


class CargoTrackSerializer(serializers.ModelSerializer):
    status = serializers.CharField(source="current_status_category", read_only=True)
    status_display = serializers.SerializerMethodField()
    history = CargoStatusUpdateSerializer(many=True, read_only=True)

    class Meta:
        model = Cargo
        fields = [
            "tracking_number",
            "status",
            "status_display",
            "origin",
            "destination",
            "history",
        ]

    def get_status_display(self, obj):
        # current_status_text bo'sh bo'lishi mumkin (masalan CUSTOM
        # bo'lmagan holatlarda) — shu sabab fallback sifatida
        # tayyor label'ni ishlatamiz.
        return obj.current_status_text or obj.get_current_status_category_display()


class CargoHistoryListSerializer(serializers.ModelSerializer):
    status = serializers.CharField(source="current_status_category", read_only=True)
    status_display = serializers.SerializerMethodField()

    class Meta:
        model = Cargo
        fields = [
            "tracking_number",
            "status",
            "status_display",
            "origin",
            "destination",
            "created_at",
        ]

    def get_status_display(self, obj):
        return obj.current_status_text or obj.get_current_status_category_display()
