from decimal import Decimal, InvalidOperation
from django import template
from django.conf import settings

register = template.Library()


@register.filter(name="currency")
def currency(value):
    """Format a numeric value as clean currency (e.g., $1.250.000 or $1,250.50)."""
    if value is None or value == "":
        value = Decimal("0")
    try:
        num = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return value

    symbol = getattr(settings, "CURRENCY_SYMBOL", "$")
    sign = "-" if num < 0 else ""
    abs_num = abs(num)

    # If the number has no fractional cents, format without decimals; otherwise show 2 decimals
    if abs_num == abs_num.to_integral_value():
        formatted = f"{int(abs_num):,}".replace(",", ".")
    else:
        formatted = f"{abs_num:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    return f"{sign}{symbol}{formatted}"


@register.filter(name="abs_val")
def abs_val(value):
    try:
        return abs(Decimal(str(value)))
    except Exception:
        return value
