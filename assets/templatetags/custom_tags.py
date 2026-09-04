# templatetags/custom_tags.py
from django import template

register = template.Library()

@register.filter
def get_original(value, name):
    if name in value:
        output = value.get(name, "") or "Empty"
    
        return {'field':name, 'value':output}


