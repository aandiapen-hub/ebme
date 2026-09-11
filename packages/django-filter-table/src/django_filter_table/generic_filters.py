from django_filters import FilterSet, Filter
from functools import reduce
from django.db.models import ForeignKey, Model, Field, QuerySet

from django.db import models


from .forms import HTMXMultiPickerWidget

from django_filters import (
    DateFilter,
    ModelMultipleChoiceFilter,
    MultipleChoiceFilter,
    CharFilter,
    DateFromToRangeFilter,
    TypedChoiceFilter,
    BaseInFilter,
)

from django_filters.widgets import RangeWidget as RangeWidget

from django.forms.widgets import (
    TextInput,
    DateInput,
    Select,
)
from django.forms import Widget, Field
from django.core.exceptions import FieldDoesNotExist

LOOKUP_SYMBOL = {
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
    (None, "--------")
)



class CharListField(Field):
    """
        Defining a django form field that would 
        return a list as cleaned output
    """
    def to_python(self, value):
        if value in (None, ""):
            return []

        if isinstance(value, (list, tuple)):
            return [str(v) for v in value]

        return [str(value)]


class CharListFilter(Filter):
    """
        A django filter field using
        CharListField as base and returning 
        values present in a search list.
    """
    field_class = CharListField

    def filter(self, qs, value):
        if not value:
            return qs

        return qs.filter(**{
            f"{self.field_name}__in": value
        })


class DateRangeWidget(RangeWidget):
    suffixes = ["_gte", "_lte"]

class MyInFilter(BaseInFilter, CharFilter):
    pass

class MyDateInFilter(BaseInFilter, DateFilter):
    pass

def filter_name_not[T:Model](self, queryset: QuerySet[T], name: str, value: str) -> QuerySet[T]:
    """ django filter function for ''not equal'' filtering """
    if not value:
        return queryset
    return queryset.exclude(**{name: value})

def filter_label(field, lookup):
    """ returning labels for filter fields """
    return f"{field.verbose_name} {LOOKUP_SYMBOL.get(lookup, lookup)}"


def text_widget() -> Widget:
    return TextInput(
        attrs={
            "type": "text",
            "class": "form-control",
        }
    )


def select_widget(field_name, lookup):
    return Select(
        attrs={
            "class": "form-select",
            "id": f"{field_name}__{lookup}",
        }
    )


def picker_widget(model, field):
    return HTMXMultiPickerWidget(
        model=model,
        fieldname=field.name,
        multiple=True,
    )


def create_isnull_filter(model, field, lookup):
    return TypedChoiceFilter(
        field_name=field.name,
        lookup_expr="isnull",
        choices=NULL_CHOICES,
        coerce=lambda value: None if value in ("", None) else value == "True",
        label=filter_label(field, lookup),
        widget=select_widget(field.name, lookup),
    )


def create_not_equal_filter(model, field, lookup):
    return CharFilter(
        method="filter_name_not",
        field_name=field.name,
        label=filter_label(field, lookup),
        widget=text_widget(),
    )


def create_choices_filter(model, field, lookup):
    return MultipleChoiceFilter(
        field_name=field.name,
        label=filter_label(field, lookup),
        choices=field.choices,
        widget=picker_widget(model, field),
    )


def get_foreign_key_search_field(field):

    related_model = field.remote_field.model

    search_terms = related_model.htmx_picker.search_terms
    if search_terms:
        return search_terms

    return field.name


def get_foreign_key_name_field(field):
    related_model = field.remote_field.model

    for related_field in related_model._meta.fields:
        if "name" in related_field.name.lower():
            return f"{field.name}__{related_field.name}"

    return field.name

def create_foreign_key_contains_filter(model, field, lookup):
    field_path = get_foreign_key_name_field(field)

    return CharFilter(
        field_name=field_path,
        lookup_expr="icontains",
        label=filter_label(field, lookup),
        widget=text_widget(),
    )


def create_foreign_key_filter(model, field, lookup):
    related_model = field.remote_field.model

    return ModelMultipleChoiceFilter(
        field_name=field.name,
        label=filter_label(field, lookup),
        queryset=related_model.objects.all(),
        widget=picker_widget(model, field),
    )


def create_exact_filter(model, field, lookup):
    filter = MyInFilter(
        field_name=field.name,
        lookup_expr="in",
        label=filter_label(field, lookup),
    )

    filter.field.widget = picker_widget(model, field)

    return filter


def create_date_range_filter(model, field, lookup):
    return DateFromToRangeFilter(
        label=f"{field.verbose_name} Between",
        widget=DateRangeWidget(
            attrs={
                "type": "date",
                "class": "form-control",
            }
        ),
    )


def create_date_iexact_filter(model, field, lookup):
    filter_ = MyDateInFilter(
        field_name=field.name,
        lookup_expr="in",
        label=filter_label(field, lookup),
    )

    filter_.field.widget = picker_widget(model, field)

    return filter_


def create_date_filter(model, field, lookup):
    return DateFilter(
        field_name=field.name,
        lookup_expr=lookup,
        label=filter_label(field, lookup),
        widget=DateInput(
            attrs={
                "type": "date",
                "class": "form-control",
            }
        ),
    )


def create_default_filter(model, field, lookup):
    return CharFilter(
        field_name=field.name,
        lookup_expr=lookup,
        label=filter_label(field, lookup),
        widget=text_widget(),
    )

FILTER_RULES = [
    (
        lambda field, lookup: "isnull" in lookup,
        create_isnull_filter,
    ),
    (
        lambda field, lookup: "ne" in lookup,
        create_not_equal_filter,
    ),
    (
        lambda field, lookup: bool(field.choices),
        create_choices_filter,
    ),
    (
        lambda field, lookup: (
            isinstance(field, models.ForeignKey)
            and "icontains" in lookup
        ),
        create_foreign_key_contains_filter,
    ),
    (
        lambda field, lookup: isinstance(field, models.ForeignKey),
        create_foreign_key_filter,
    ),
    (
        lambda field, lookup: ( "iexact" in lookup),
        create_exact_filter,
    ),
    (
        lambda field, lookup: (
            isinstance(field, models.DateField)
            and "range" in lookup
        ),
        create_date_range_filter,
    ),
    (
        lambda field, lookup: (
            isinstance(field, models.DateField)
            and "iexact" in lookup
        ),
        create_date_iexact_filter,
    ),
    (
        lambda field, lookup: isinstance(field, models.DateField),
        create_date_filter,
)]

def generate_filter_for_field(model, field_name, lookup):
    try:
        field = model._meta.get_field(field_name)
    except FieldDoesNotExist:
        return None

    for condition, field_factory in FILTER_RULES:
        if condition(field, lookup):
            return field_factory(model, field, lookup)

    return create_default_filter(model, field, lookup)


class CustomFilterSet(FilterSet):
    """
        Custom ``FilterSet`` providing a universal fuzzy-search filter.
        The universal search applies a search term across the fields defined by
        ``universal_search_fields`` and combines the resulting lookups into a single filter.
        Class attributes:
                visible_columns: Optional collection of columns available to the associated table view.
                universal_search_fields: Fields and lookup expressions used by the universal search,
                    for example ``["name__icontains", "assetid__istartswith"]``.
                    The ``universal_search`` filter exposes the search functionality to forms
                    and views using this filter set.
    """
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
    return 'Search' + ' ' + ", ".join(fields)


def dynamic_filterset_generator(
    filter_model: type[Model],
    universal_search_fields: list[str] | None = None,
    active_filters: list[str] | None = None
):
    """ 
        Dynamically generate a ``FilterSet`` subclass for the given model.
        Builds a ``CustomFilterSet`` subclass with the supplied universal search fields and active filters.
        Filter definitions are generated from the model's field lookup expressions
        and attached to the dynamically created class.
        Args:
            filter_model: Django model the generated filter set operates on.
            universal_search_fields: Optional field lookup expressions used by the universal search.
            active_filters: Optional iterable of field lookup expressions for which filters should be generated.
            Returns: A dynamically generated ``CustomFilterSet`` subclass configured for ``filter_model``. """
    attritutes = {}

    if active_filters is None:
        active_filters = []

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


def get_filter_fields(model: type[Model], visible_columns: list[str]) -> dict[str, list[str]]:
    """
     This uses model meta information and returns filters available for visible model fields
    """
    fields = {}
    # Define relevant lookups per type
    text_lookups = ["iexact", "icontains", "istartswith", "isnull"]
    foreign_lookups = ["iexact", "icontains", "isnull"]
    numeric_lookups = ["iexact", "lt", "lte", "gt", "gte", "isnull", "ne"]
    date_lookups = ["iexact", "lt", "lte", "gt", "gte", "range", "isnull"]
    choice_lookups = ["iexact"]

    for field in model._meta.get_fields():
        if hasattr(field, "get_lookups") and field.name in visible_columns:
            if field.choices:
                lookups = choice_lookups
            elif isinstance(field, (models.CharField, models.TimeField)):
                lookups = text_lookups
            elif isinstance(
                field,
                (
                    models.DecimalField,
                    models.IntegerField,
                    models.FloatField,
                ),
            ):
                lookups = numeric_lookups
            elif isinstance(field, (models.DateField, models.DateTimeField)):
                lookups = date_lookups

            elif isinstance(field, models.ForeignKey):
                related_model = field.remote_field.model
                if not hasattr(related_model, 'htmx_picker'):
                    lookups = text_lookups
                lookups = foreign_lookups
            else:
                lookups = text_lookups

            fields[field.name] = {
                "lookups": [
                    {
                        "lookup_expr": f"{field.name}__{lk}",
                        "label": LOOKUP_SYMBOL.get(lk, lk),
                    }
                    for lk in lookups
                ],
                "verbose_name": getattr(field, "verbose_name", field.name),
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
