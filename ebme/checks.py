# myapp/checks.py

from django.apps import apps
from django.core import checks
from django.db import models

from utils.generic_views import FilteredTableView


def all_subclasses(cls):
    for subclass in cls.__subclasses__():
        yield subclass
        yield from all_subclasses(subclass)


@checks.register()
def check_htmx_selectors(app_configs, **kwargs):
    missing = []

    for view_class in all_subclasses(FilteredTableView):
        model = getattr(view_class, "model", None)

        if model is None:
            continue

        for field in model._meta.get_fields():
            if not isinstance(field, models.ForeignKey):
                continue

            related_model = field.remote_field.model

            if not hasattr(related_model, "htmx_selector"):
                missing.append(
                    f"{model._meta.label}.{field.name} "
                    f"→ {related_model._meta.label}"
                )

    if not missing:
        return []

    return [
        checks.Error(
            "ForeignKey models missing htmx_selector:\n"
            + "\n".join(f"  - {item}" for item in missing),
            id="myapp.E001",
        )
    ]
