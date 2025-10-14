from django import template
import json

register = template.Library()


@register.filter
def get(value, arg):
    """
    Safely gets a value from a dictionary or list.
    Usage: {{ dict|get:key }}
    """
    try:
        if isinstance(value, dict):
            return value.get(arg, None)
        elif isinstance(value, (list, tuple)):
            try:
                return value[int(arg)]
            except (ValueError, IndexError):
                return None
    except (AttributeError, TypeError):
        return None
    return None


@register.filter
def safe_json(value):
    """
    Converts a Python object to JSON string safely.
    Usage: {{ object|safe_json }}
    """
    try:
        if value is None:
            return 'null'
        
        # Convert datetime objects to ISO format strings
        if hasattr(value, 'isoformat'):
            return json.dumps(value.isoformat())
        
        # Handle dictionaries
        if isinstance(value, dict):
            result = {}
            for k, v in value.items():
                if hasattr(v, 'isoformat'):
                    result[k] = v.isoformat()
                elif isinstance(v, (list, tuple)):
                    result[k] = [
                        item.isoformat() if hasattr(item, 'isoformat') else item 
                        for item in v
                    ]
                else:
                    result[k] = v
            return json.dumps(result)
        
        # Handle lists/tuples
        if isinstance(value, (list, tuple)):
            result = []
            for item in value:
                if hasattr(item, 'isoformat'):
                    result.append(item.isoformat())
                elif isinstance(item, dict):
                    sub_dict = {}
                    for k, v in item.items():
                        if hasattr(v, 'isoformat'):
                            sub_dict[k] = v.isoformat()
                        else:
                            sub_dict[k] = v
                    result.append(sub_dict)
                else:
                    result.append(item)
            return json.dumps(result)
        
        return json.dumps(value)
    except (TypeError, ValueError):
        return json.dumps(str(value))


@register.filter
def lookup(dictionary, key):
    """
    Looks up a key in a dictionary (similar to get filter).
    Usage: {{ dict|lookup:key }}
    """
    if isinstance(dictionary, dict):
        return dictionary.get(key, None)
    return None


@register.filter
def time_format(value, format_str="%H:%M"):
    """
    Formats a time object.
    Usage: {{ time_obj|time_format }}
    or {{ time_obj|time_format:"%H:%M:%S" }}
    """
    if value is None:
        return ""
    try:
        if hasattr(value, 'strftime'):
            return value.strftime(format_str)
        return str(value)
    except (AttributeError, ValueError):
        return str(value)


@register.filter
def dict_keys(value):
    """
    Returns dictionary keys as a list.
    Usage: {% for key in dict|dict_keys %}
    """
    if isinstance(value, dict):
        return value.keys()
    return []


@register.filter
def dict_values(value):
    """
    Returns dictionary values as a list.
    Usage: {% for val in dict|dict_values %}
    """
    if isinstance(value, dict):
        return value.values()
    return []


@register.filter
def increment(value, increment=1):
    """
    Increments a number.
    Usage: {{ number|increment }} or {{ number|increment:5 }}
    """
    try:
        return int(value) + int(increment)
    except (ValueError, TypeError):
        return value


@register.filter
def default_if_empty(value, default_value):
    """
    Returns default value if value is empty.
    Usage: {{ value|default_if_empty:"N/A" }}
    """
    if not value or (isinstance(value, (list, dict)) and len(value) == 0):
        return default_value
    return value


@register.filter
def class_status(value):
    """
    Returns a status badge class based on enrollment status.
    Usage: {{ status|class_status }}
    """
    status_map = {
        'ENROLLED': 'badge-success',
        'DROPPED': 'badge-danger',
        'COMPLETED': 'badge-info',
        'FAILED': 'badge-warning',
    }
    return status_map.get(value, 'badge-secondary')


@register.filter
def display_time_range(start_time, end_time):
    """
    Formats time range nicely.
    Usage: {{ start|display_time_range:end }}
    """
    try:
        if hasattr(start_time, 'strftime') and hasattr(end_time, 'strftime'):
            return f"{start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}"
        return f"{start_time} - {end_time}"
    except:
        return ""


@register.filter
def json_script(value):
    """
    Safely converts Python object to JSON for use in <script> tags.
    Usage: const data = {{ object|json_script }};
    """
    return json.dumps(value, default=str)