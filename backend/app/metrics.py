"""Custom business metrics (exposed on /metrics next to the HTTP metrics)."""

from prometheus_client import Counter

APPOINTMENTS_BOOKED = Counter(
    "clinicq_appointments_booked_total",
    "Total number of appointments booked",
)
APPOINTMENTS_CANCELLED = Counter(
    "clinicq_appointments_cancelled_total",
    "Total number of appointments cancelled",
)
