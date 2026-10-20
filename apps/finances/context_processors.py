from django.conf import settings
from django.utils import timezone


def finance_preferences(request):
    """Inject global finance settings like currency symbol and current date into templates."""
    today = timezone.localdate()
    return {
        "CURRENCY_SYMBOL": getattr(settings, "CURRENCY_SYMBOL", "$"),
        "CURRENT_YEAR": today.year,
        "CURRENT_MONTH": today.month,
    }
