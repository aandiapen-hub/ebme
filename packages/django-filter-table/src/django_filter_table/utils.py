from dataclasses import dataclass
import json
from django.http import HttpResponse

@dataclass(frozen=True)
class PickerDependency:
    field: str
    lookup: str

@dataclass(frozen=True)
class HtmxPicker:
    enabled: bool = True # True
    search_terms: tuple[str, ...] = () # ('fieldname__icontains',)
    label_str: str | None = None  # lambda obj: f"{obj.modelname} ({obj.brandid})"
    customer_scope: str | None = None # 'customerid'
    dependency: tuple[PickerDependency, ...] =()


def set_preference(profile, table_name, key, value):
    """
    Update a single preference for a specific table.
    Example: set_table_preference("orders", "visible_columns",["id", "status"])
    table_settings will look like {"orders":{"visible_columns":['id','status']}}
    """
    settings = profile.table_settings.get(table_name, {})
    settings[key] = value
    profile.table_settings[table_name] = settings
    profile.save(update_fields=['table_settings', 'updated_at'])

def get_preference(profile, table_name, key, default=None):
    return profile.table_settings.get(table_name, {}).get(key, default)


def add_htmx_message(
    response: type[HttpResponse],
    message_level: str,
    message: str
):

    response["HX-Trigger"] = json.dumps({
            "show_message": {
                "message": message,
                "level": message_level,
            },
        })
    return response
