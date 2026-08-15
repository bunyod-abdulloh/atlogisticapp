from django.urls import path

from .views import CargoTrackView, index, CargoHistoryListView

app_name = "tracking"

urlpatterns = [
    path("home/", index, name="index"),
    path("api/track/<str:tracking_number>/", CargoTrackView.as_view(),),
    path("api/history/", CargoHistoryListView.as_view(), name="cargo-history"),
]
