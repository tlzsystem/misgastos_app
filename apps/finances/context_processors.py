from django.conf import settings
from django.utils import timezone
from apps.accounts.recaptcha import is_recaptcha_enabled


def finance_preferences(request):
    """Inject global finance settings like currency symbol and current date into templates."""
    today = timezone.localdate()
    return {
        "CURRENCY_SYMBOL": getattr(settings, "CURRENCY_SYMBOL", "$"),
        "CURRENT_YEAR": today.year,
        "CURRENT_MONTH": today.month,
        "RECAPTCHA_ENABLED": is_recaptcha_enabled(),
        "RECAPTCHA_SITE_KEY": getattr(settings, "RECAPTCHA_SITE_KEY", ""),
    }
