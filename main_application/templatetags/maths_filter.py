from django import template
from decimal import Decimal
from decimal import InvalidOperation
register = template.Library()


@register.filter(name='get_item')
def get_item(dictionary, key):
    """
    Get an item from a dictionary using a key.
    Usage: {{ dictionary|get_item:key }}
    """
    if dictionary is None:
        return None
    return dictionary.get(key)


@register.filter(name='mul')
def mul(value, arg):
    """
    Multiply the value by the argument.
    Usage: {{ value|mul:100 }}
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter(name='div')
def div(value, arg):
    """
    Divide the value by the argument.
    Usage: {{ value|div:total }}
    """
    try:
        if float(arg) == 0:
            return 0
        return float(value) / float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter(name='percentage')
def percentage(value, total):
    """
    Calculate percentage of value out of total.
    Usage: {{ value|percentage:total }}
    """
    try:
        if float(total) == 0:
            return 0
        return round((float(value) / float(total)) * 100, 2)
    except (ValueError, TypeError):
        return 0


@register.filter(name='add_decimal')
def add_decimal(value, arg):
    """
    Add two decimal values.
    Usage: {{ value|add_decimal:other_value }}
    """
    try:
        return Decimal(str(value)) + Decimal(str(arg))
    except (ValueError, TypeError, InvalidOperation):
        return Decimal('0')


@register.filter(name='sub')
def sub(value, arg):
    """
    Subtract arg from value.
    Usage: {{ value|sub:arg }}
    """
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0