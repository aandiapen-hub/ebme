from django_filters import FilterSet
from functools import reduce
from django.db.models import Q, ForeignKey, DateField
from django.forms import (
    CharField,
    CheckboxSelectMultiple,
    DateTimeField,
    FloatField,
    IntegerField,
    TimeField,
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

# For non-model multiple choice fields
CHOICE_FILTER_FIELDS = {
    "ppm_compliance": {
        "label": "PPM Compliance",
        "choices": [("compliant", "Compliant"), ("non-compliant", "Non-Compliant")],
        "widget": CheckboxSelectMultiple,
    }
}

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
}

NULL_CHOICES = (
    (True, "Empty"),
    (False, "Not Empty"),
)


class DateRangeWidget(RangeWidget):
    suffixes = ["_gte", "_lte"]


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
            widget=Select(attrs={"class": "form-select", 'id': f"{field_name}__{lookup}"}),
        )

    # ForeignKey filters
    if isinstance(field, ForeignKey):
        related_model = field.remote_field.model
        model_fields = related_model._meta.fields  # concrete fields only
        # string search on ForeignKey
        if "contains" in lookup:
            # find a field on the related model with 'name' in its name
            foreign_field = [f.name for f in model_fields if "name" in f.name.lower()]

            if foreign_field:
                return CharFilter(
                    label=f"{field.verbose_name} Contains",
                    field_name=f"{field_name}__{foreign_field[0]}",
                    lookup_expr="icontains",
                    widget=TextInput(attrs={"type": "text", "class": "form-control"}),
                )
        # lookup search on foreighkey
        else:
            # get fields in model that contains name or description
            search_fields = [
                f"{field.name}__contains"
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
                        "data-allow-clear": 'false',
                        "data-minimum-input-length": 0,
                        'id': f"{field_name}__{lookup}",
                    },
                ),
            )

    elif "exact" in lookup and not isinstance(field, DateField):
        unique_values = model.objects.values_list(field.name, flat=True).distinct()
        print(unique_values)
        return MultipleChoiceFilter(
            label=f"{field.verbose_name} Lookup",
            field_name=field_name,
            choices=[(v, v) for v in unique_values],
            widget=Select2MultipleWidget(
                attrs={
                    "data-placeholder": "Select",
                    "data-minimum-input-length": 2,
                    "data-allow-clear": 'false',
                    'id': f"{field_name}__{lookup}"
                },
            ),
        )
    # Date field filters
    elif isinstance(field, DateField):
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
    elif field_name in CHOICE_FILTER_FIELDS.keys():
        config = CHOICE_FILTER_FIELDS[field_name]
        return MultipleChoiceFilter(
            label=field.verbose_name,
            choices=config["choices"],
            widget=CheckboxSelectMultiple,
        )
    else:
        return CharFilter(
            label=f"{field.verbose_name} {lookup}",
            field_name=field_name,
            lookup_expr=lookup,
            widget=TextInput(attrs={"type": "text", "class": "form-control"}),
        )


class CustomFilterSet(FilterSet):
    choice_filter_config = CHOICE_FILTER_FIELDS
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

        q_object = Q()
        for term in values_list:
            term_q = reduce(
                lambda acc, field: acc | Q(**{field: term}),
                self.universal_search_fields,
                Q(),
            )
            q_object &= term_q

        return queryset.filter(q_object)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        universal_search = self.filters["universal_search"].field
        # Add help text (correct way)
        universal_search.widget.attrs.update({'placeholder':
            f"{self.universal_search_fields_list}"
        })


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
    if active_filters is None:
        active_filters = []

    attritutes["universal_search_fields"] = universal_search_fields
    attritutes["universal_search_fields_list"] = get_universal_search_fields(
        filter_model, universal_search_fields
    )
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
    numeric_lookups = ["exact", "lt", "lte", "gt", "gte", "isnull"]
    date_lookups = ["exact", "lt", "lte", "gt", "gte", "range", "isnull"]

    for field in model._meta.get_fields():
        if hasattr(field, "get_lookups") and field.name in visible_columns:
            if isinstance(field, (CharField, TimeField)):
                lookups = text_lookups
            elif isinstance(field, (IntegerField, FloatField)):
                lookups = numeric_lookups
            elif isinstance(field, (DateField, DateTimeField)):
                lookups = date_lookups
            elif isinstance(field, ForeignKey):
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
