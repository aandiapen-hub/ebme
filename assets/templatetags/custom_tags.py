# templatetags/custom_tags.py
import datetime
from django import template
from django import template
import re
from django.utils.safestring import mark_safe

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




@register.filter()
def highlight(text, src_str):
    if not src_str:
        return text
    if text is not None:
        text = str(text)
        str_replaced = src_str.sub(
            lambda m: f"<span class='text-bg-success'>{m.group(0)}</span>",
            text,
        )
    else:
        str_replaced = ''

    return mark_safe(str_replaced)
