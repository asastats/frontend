"""Template filters for the DAO voting pages."""

from decimal import Decimal

from django import template

register = template.Library()


@register.filter
def micro(value):
    """Return micro-units as whole units with thousands separators.

    :param value: amount in micro-units
    :type value: int
    :return: str
    """
    if value is None:
        return "-"
    text = f"{Decimal(value) / Decimal(1_000_000):,.6f}".rstrip("0").rstrip(".")
    return text or "0"


@register.filter
def short_address(address):
    """Return the first and last six characters of an address.

    :param address: public Algorand address
    :type address: str
    :return: str
    """
    return f"{address[:6]}…{address[-6:]}" if len(address) > 14 else address
