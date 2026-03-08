from decimal import Decimal, InvalidOperation

from django import template


register = template.Library()


@register.filter
def ariary(value):
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return value

    text = f"{amount:,.2f}".replace(",", " ")
    if text.endswith(".00"):
        text = text[:-3]
    return f"{text} Ar"
