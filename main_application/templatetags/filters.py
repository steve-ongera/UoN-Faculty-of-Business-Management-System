from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    """Multiply the value by the argument safely."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0.0

@register.filter
def divide(value, arg):
    """Divide the value by the argument safely and return a clean number string."""
    try:
        arg = float(arg)
        if arg == 0:
            return 0.0
        result = float(value) / arg
        # Always return a clean, trimmed string (no spaces or extra decimals)
        return f"{result:.2f}".rstrip('0').rstrip('.')
    except (ValueError, TypeError, ZeroDivisionError):
        return "0"
