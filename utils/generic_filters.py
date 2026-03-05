from django_filters import FilterSet
from functools import reduce

from django.db import models

from django.forms import (
    CheckboxSelectMultiple,
)

from django_filters import (
    DateFilter,
    ModelMultipleChoiceFilter,
    MultipleChoiceFilter,
    CharFilter,
    DateFromToRangeFilter,
    TypedChoiceFilter,
)

from django_select2.forms import (
    ModelSelect2MultipleWidget,
    Select2MultipleWidget,
)
from django_filters.widgets import RangeWidget as RangeWidget

from django.forms.widgets import (
    TextInput,
    DateInput,
    Select,
)
from django.core.exceptions import FieldDoesNotExist

LOOKUP_SYMBOL = {
    "exact": "is",
    "iexact": "is",
    "icontains": "contains",
    "isnull": "empty",
    "startswith": "starts with",
    "istartswith": "starts with",
    "lt": "<",
    "lte": "≤",
    "gt": ">",
    "gte": "≥",
    "range": "between",
    "year": "year =",
    "month": "month =",
    "day": "day =",
    "ne": "is not",
}

NULL_CHOICES = (
    (True, "Empty"),
    (False, "Not Empty"),
)


class DateRangeWidget(RangeWidget):
    suffixes = ["_gte", "_lte"]


def filter_name_not(self, queryset, name, value):
    if not value:
        return queryset
    return queryset.exclude(**{name: value})


def generate_filter_for_field(model, field_name, lookup):
    try:
        field = model._meta.get_field(field_name)
    except FieldDoesNotExist:
        return None
    # Null filter

    if "isnull" in lookup:
        return TypedChoiceFilter(
            field_name=field_name,
            lookup_expr="isnull",
            choices=NULL_CHOICES,
            coerce=lambda v: None if v in ("", None) else v == "True",
            label=f"{field.verbose_name} is Empty",
            widget=Select(
                attrs={"class": "form-select", "id": f"{field_name}__{lookup}"}
            ),
        )

    if "ne" in lookup:
        return CharFilter(
            method="filter_name_not",
            label=f"{field.verbose_name} {LOOKUP_SYMBOL.get(lookup, lookup)}",
            field_name=field_name,
            widget=TextInput(attrs={"type": "text", "class": "form-control"}),
        )

    if field.choices:
        return MultipleChoiceFilter(
            field_name=field_name,
            label=field.verbose_name,
            choices=field.choices,
            widget=Select2MultipleWidget(
                attrs={
                    "class": "form-control",
                    "id": f"{field_name}__{lookup}",
                }
            ),
        )

    # ForeignKey filters
    if isinstance(field, models.ForeignKey):
        related_model = field.remote_field.model
        model_fields = related_model._meta.fields  # concrete fields only
        # string search on ForeignKey
        if "icontains" in lookup:
            # find a field on the related model with 'name' in its name
            foreign_fields = [f.name for f in model_fields if "name" in f.name.lower()]

            if foreign_fields:
                field_path = f"{field_name}__{foreign_fields[0]}"
            else:
                # fallback to raw FK field
                field_path = field_name

            return CharFilter(
                label=f"{field.verbose_name} Contains",
                field_name=field_path,
                lookup_expr="icontains",
                widget=TextInput(attrs={"type": "text", "class": "form-control"}),
            )
        # lookup search on foreighkey
        else:
            # get fields in model that contains name or description
            search_fields = [
                f"{field.name}__icontains"
                for field in model_fields
                if "name" in field.name.lower()
                or "description" in field.name.lower()
                or "_id" in field.name
            ]

            return ModelMultipleChoiceFilter(
                label=f"{field.verbose_name} Lookup",
                field_name=field_name,
                queryset=related_model.objects.all(),
                widget=ModelSelect2MultipleWidget(
                    model=related_model,
                    search_fields=search_fields,
                    attrs={
                        "data-placeholder": "Select",
                        "data-allow-clear": "false",
                        "data-minimum-input-length": 0,
                        "id": f"{field_name}__{lookup}",
                    },
                ),
            )

    elif "exact" in lookup and not isinstance(field, models.DateField):
        unique_values = model.objects.order_by().values_list(field.name, flat=True).distinct()
        return MultipleChoiceFilter(
            label=f"{field.verbose_name} Lookup",
            field_name=field_name,
            choices=[(v, v) for v in unique_values],
            widget=Select2MultipleWidget(
                attrs={
                    "data-placeholder": "Select",
                    "data-minimum-input-length": 0,
                    "data-allow-clear": "false",
                    "id": f"{field_name}__{lookup}",
                },
            ),
        )
    # Date field filters
    elif isinstance(field, models.DateField):
        if "range" in lookup:
            return DateFromToRangeFilter(
                label=f"{field.verbose_name} Between",
                widget=DateRangeWidget(
                    attrs={"type": "date", "class": "form-control"},
                ),
            )

        else:
            return DateFilter(
                label=f"{field.verbose_name} {lookup}",
                field_name=field_name,
                lookup_expr=lookup,
                widget=DateInput(attrs={"type": "date", "class": "form-control"}),
            )

    else:
        return CharFilter(
            label=f"{field.verbose_name} {lookup}",
            field_name=field_name,
            lookup_expr=lookup,
            widget=TextInput(attrs={"type": "text", "class": "form-control"}),
        )


class CustomFilterSet(FilterSet):
    visible_columns = None
    universal_search_fields = None

    universal_search = CharFilter(
        method="my_custom_filter",
        label="Search",
        widget=TextInput(
            attrs={"type": "search", "class": "form-control", "autofocus": None}
        ),
    )

    def my_custom_filter(self, queryset, name, value):
        values_list = value.split(",") if "," in value else value.split()

        q_object = models.Q()
        for term in values_list:
            term_q = reduce(
                lambda acc, field: acc | models.Q(**{field: term}),
                self.universal_search_fields,
                models.Q(),
            )
            q_object &= term_q

        return queryset.filter(q_object)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        universal_search = self.filters["universal_search"].field
        # Add help text (correct way)
        universal_search.widget.attrs.update(
            {"placeholder": f"{self.universal_search_fields_list}"}
        )


def get_universal_search_fields(filter_model, field_list):
    fields = [x.split("__", 2)[0] for x in field_list]
    fields = [
        filter_model._meta.get_field(field_name).verbose_name for field_name in fields
    ]
    return ",".join(fields)


def dynamic_filterset_generator(
    filter_model, universal_search_fields=None, active_filters=None
):
    attritutes = {}
    # remove hidden fields from visible columns

    attritutes["universal_search_fields"] = universal_search_fields
    attritutes["universal_search_fields_list"] = get_universal_search_fields(
        filter_model, universal_search_fields
    )
    attritutes["filter_name_not"] = filter_name_not

    for f in active_filters:
        attritutes[f] = get_filter_from_field_lookup(filter_model, f)

    class Meta:
        model = filter_model
        fields = ["universal_search"]

    DynamicFilterSet = type(
        f"{filter_model.__name__}_filterclass",
        (CustomFilterSet,),
        {**attritutes, "Meta": Meta},
    )

    return DynamicFilterSet


def get_filter_fields(model, visible_columns):
    fields = {}
    # Define relevant lookups per type
    text_lookups = ["iexact", "icontains", "startswith", "istartswith", "isnull"]
    foreign_lookups = ["iexact", "icontains", "isnull"]
    numeric_lookups = ["iexact", "lt", "lte", "gt", "gte", "isnull", "ne"]
    date_lookups = ["exact", "lt", "lte", "gt", "gte", "range", "isnull"]
    choice_lookups = ["iexact"]

    for field in model._meta.get_fields():
        if hasattr(field, "get_lookups") and field.name in visible_columns:
            if field.choices:
                lookups = choice_lookups
            elif isinstance(field, (models.CharField, models.TimeField)):
                lookups = text_lookups
            elif isinstance(field, models.DecimalField):
                lookups = numeric_lookups
            elif isinstance(
                field,
                (
                    models.IntegerField,
                    models.FloatField,
                ),
            ):
                lookups = numeric_lookups
            elif isinstance(field, (models.DateField, models.DateTimeField)):
                lookups = date_lookups
            elif isinstance(field, models.ForeignKey):
                lookups = foreign_lookups
            else:
                lookups = text_lookups

            fields[field.name] = {
                "lookups": lookups,
                "verbose_name": getattr(field, "verbose_name", field.name),
                "lookup_labels": {lk: LOOKUP_SYMBOL.get(lk, lk) for lk in lookups},
            }

    return fields


def get_filter_from_field_lookup(model, field_lookup):
    parts = field_lookup.split("__", 2)
    if len(parts) >= 2:
        field_name = parts[0]
        lookup_expr = parts[-1]

    else:
        field_name = parts[0]
        lookup_expr = "icontains"

    return generate_filter_for_field(
        model=model, field_name=field_name, lookup=lookup_expr
    )
