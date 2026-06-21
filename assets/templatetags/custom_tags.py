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
def get_original(value, name):
    if name in value:
        output = value.get(name, "") or "Empty"
    
        return {'field':name, 'value':output}
