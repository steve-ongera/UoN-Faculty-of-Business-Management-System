from django import template
import json

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Get item from dictionary using key
    Usage: {{ dict|get_item:key }}
    """
    if dictionary is None:
        return None
    return dictionary.get(key)

@register.filter
def safe_json(value):
    """
    Safely convert Python dict/list to JSON for JavaScript
    Usage: {{ data|safe_json }}
    """
    return json.dumps(value)