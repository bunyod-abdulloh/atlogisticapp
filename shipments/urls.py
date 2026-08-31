from django.urls import path

from .api_views import CargoHistoryView, CargoTrackView

urlpatterns = [
    path("track/<str:tracking_number>/", CargoTrackView.as_view(), name="cargo-track"),
    path("history/", CargoHistoryView.as_view(), name="cargo-history"),
]