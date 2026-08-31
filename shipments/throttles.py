from rest_framework.throttling import ScopedRateThrottle


class CargoTrackThrottle(ScopedRateThrottle):
    scope = "cargo_track"


class CargoHistoryThrottle(ScopedRateThrottle):
    scope = "cargo_history"