# templatetags/custom_tags.py
import datetime
from django import template

register = template.Library()

@register.filter
def get(d, key):
    values = {k: v for k, v in d.items() if k.startswith(key) and v != ''}
    if values:
        return True


@register.filter
def display_filter_value(value):
    """Return a clean, human-readable string for filter values."""
    if value is None or value == "":
        return ""
    # Handle QuerySet or RelatedManager
    if hasattr(value, 'all'):
        return ", ".join(str(v) for v in value.all())
    # Handle lists/tuples
    if isinstance(value, (list, tuple)):
        return ", ".join(str(v) for v in value)
    # Handle dict-like (ranges)
    if isinstance(value, dict):
        parts = []
        for k, v in value.items():
            parts.append(f"{k}: {v}")
        return ", ".join(parts)
    # Default
    if isinstance(value,slice):
        if isinstance(value.start,datetime.datetime):
            start = value.start.strftime("%Y-%m-%d")
        else:
            start = value.start
        
        if isinstance(value.stop,datetime.datetime):
            stop = value.start.strftime("%Y-%m-%d")
        else:
            stop = value.stop
        return f"{start} - {stop}"
    return str(value)


@register.filter
def get_original(value, name):
    output = value.get(name, "")
    return output
