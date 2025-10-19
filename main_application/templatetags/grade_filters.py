from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get item from dictionary by key"""
    if dictionary is None:
        return None
    return dictionary.get(key)

@register.filter
def dict_key(dictionary, key):
    """Alternative way to get dictionary item"""
    return dictionary.get(key, {})

@register.filter
def multiply(value, arg):
    """Multiply two values"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def divide(value, arg):
    """Divide two values"""
    try:
        if float(arg) == 0:
            return 0
        return float(value) / float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def grade_class(grade):
    """Return CSS class for grade badge"""
    if grade:
        grade = str(grade).upper()
        if grade in ['A', 'A+', 'A-']:
            return 'grade-A'
        elif grade in ['B', 'B+', 'B-']:
            return 'grade-B'
        elif grade in ['C', 'C+', 'C-']:
            return 'grade-C'
        elif grade in ['D', 'D+', 'D-']:
            return 'grade-D'
        elif grade in ['E', 'F']:
            return 'grade-F'
    return 'grade-F'

@register.filter
def sort_by_semester(semesters_data):
    """
    Sort semesters dictionary or dict_items by semester number.
    Handles dict, OrderedDict, or odict_items safely.
    """
    if not semesters_data:
        return []
    
    # If it's already dict_items (odict_items), convert to list
    if hasattr(semesters_data, "__iter__") and not isinstance(semesters_data, dict):
        try:
            items = list(semesters_data)
        except Exception:
            return []
    else:
        items = semesters_data.items()
    
    # Sort by semester key (e.g., 1, 2, 3...)
    return sorted(items, key=lambda x: x[0])

@register.filter
def percentage(value, max_value):
    """Calculate percentage"""
    try:
        if float(max_value) == 0:
            return 0
        return (float(value) / float(max_value)) * 100
    except (ValueError, TypeError):
        return 0
