import json
import urllib.parse
import urllib.request
from django.conf import settings


RECAPTCHA_VERIFY_URL = "https://www.google.com/recaptcha/api/siteverify"


def get_client_ip(request) -> str | None:
    """Extract client IP address from request headers."""
    if not request:
        return None
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_PROTO_IP") or request.META.get(
        "HTTP_X_FORWARDED_FOR"
    )
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def is_recaptcha_enabled() -> bool:
    """Return True if reCAPTCHA validation is enabled and keys are configured."""
    if not getattr(settings, "RECAPTCHA_ENABLED", True):
        return False
    site_key = getattr(settings, "RECAPTCHA_SITE_KEY", "").strip()
    secret_key = getattr(settings, "RECAPTCHA_SECRET_KEY", "").strip()
    return bool(site_key and secret_key)


def verify_recaptcha_token(token: str, remote_ip: str | None = None) -> bool:
    """Verify Google reCAPTCHA response token against Google's siteverify API."""
    if not is_recaptcha_enabled():
        return True

    if not token:
        return False

    secret_key = getattr(settings, "RECAPTCHA_SECRET_KEY", "").strip()
    payload = {
        "secret": secret_key,
        "response": token,
    }
    if remote_ip:
        payload["remoteip"] = remote_ip

    data = urllib.parse.urlencode(payload).encode("utf-8")
    req = urllib.request.Request(RECAPTCHA_VERIFY_URL, data=data, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            result = json.loads(response.read().decode("utf-8"))
            return bool(result.get("success", False))
    except Exception:
        return False
