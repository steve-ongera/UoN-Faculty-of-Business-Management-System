# Create this file: yourapp/templatetags/calendar_filters.py

from django import template
import json

register = template.Library()

@register.filter(name='lookup')
def lookup(dictionary, key):
    """
    Template filter to lookup a value in a dictionary
    Usage: {{ dict|lookup:key }}
    """
    if dictionary is None:
        return None
    return dictionary.get(key, None)


@register.filter(name='safe_json')
def safe_json(value):
    """
    Safely convert Python object to JSON for JavaScript
    Usage: {{ data|safe_json }}
    """
    return json.dumps(value)