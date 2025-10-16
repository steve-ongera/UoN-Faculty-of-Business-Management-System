# Create this file in your app's templatetags directory
# Path: your_app/templatetags/custom_filters.py

from django import template

register = template.Library()

@register.filter(name='get_item')
def get_item(dictionary, key):
    """Get item from dictionary using key"""
    if dictionary is None:
        return None
    return dictionary.get(key)


# Create this file: your_app/templatetags/custom_filters.py

from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary using a variable key"""
    if dictionary is None:
        return None
    return dictionary.get(key)

@register.filter
def dictsort(value):
    """Sort dictionary keys"""
    if isinstance(value, dict):
        return sorted(value.keys())
    return value