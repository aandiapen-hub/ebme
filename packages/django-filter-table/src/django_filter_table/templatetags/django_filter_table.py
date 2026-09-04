# templatetags/custom_tags.py
from django import template
import re
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def get(d, key):
    values = {k: v for k, v in d.items() if k.startswith(key) and v != ''}
    if values:
        return True

@register.filter()
def highlight(text, src_re_obj):

    def replace_content(match):
        opening, content, closing = match.groups()

        return (
            opening
            + src_re_obj.sub(
                lambda m: f"<span class='text-bg-success'>{m.group(0)}</span>",
                content,
            )
            + closing
        )

    if not src_re_obj:
        return text

    if text is not None:
        text = str(text)
        parts = re.split(r"(<a\b[^>]*>.*?</a>)", text, flags=re.IGNORECASE | re.DOTALL)

        for i, part in enumerate(parts):
            if re.match(r"<a\b", part, re.IGNORECASE):
                parts[i] = re.sub(
                    r"(<a\b[^>]*>)(.*?)(</a>)",
                    replace_content,
                    part,
                    flags=re.IGNORECASE | re.DOTALL,
                )
            else:
                parts[i] = src_re_obj.sub(
                    lambda m: f"<span class='text-bg-success'>{m.group(0)}</span>",
                    part,
                )

        return mark_safe("".join(parts))

    else:
        return ''


