# orders/templatetags/order_tags.py
from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def multiply(value, arg):
    return Decimal(value) * Decimal(arg)