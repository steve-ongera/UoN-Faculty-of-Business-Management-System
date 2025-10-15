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