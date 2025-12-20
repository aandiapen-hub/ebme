from codecs import lookup
from functools import reduce
from itertools import chain
from re import search
from django.db.models import Q, ForeignKey,DateField
from django.forms import CheckboxSelectMultiple,ChoiceField
from django_filters import( ModelMultipleChoiceFilter,
                           MultipleChoiceFilter,
                            CharFilter,
                            DateFromToRangeFilter,
                            BooleanFilter)

from django_select2.forms import (
                            ModelSelect2MultipleWidget,
                        )
from django_filters.widgets import RangeWidget

from django.forms.widgets import CheckboxSelectMultiple, TextInput,CheckboxInput

# For non-model multiple choice fields
CHOICE_FILTER_FIELDS = {
    'ppm_compliance': {
        'label': 'PPM Compliance',
        'choices': [
            ('compliant', 'Compliant'),
            ('non-compliant', 'Non-Compliant')
        ],
        'widget': CheckboxSelectMultiple
    }
}


from django_filters import FilterSet

NULL_CHOICES = (
        ('not_null', 'Yes'),   # NOT NULL
        ('null', 'No'),        # IS NULL
    )



def generate_checkbox_filter_for_field(model,field_name):
    field = model._meta.get_field(field_name)   
    return BooleanFilter(
        field_name=field_name,
        lookup_expr='isnull', 
        label=f'{field_name} is Empty',
        )


def generate_filter_for_field(model,field_name,all_fields):
    field = model._meta.get_field(field_name)   
    filters = {}

    #if foreign key then use select2
    if isinstance(field,ForeignKey):
        related_model = field.remote_field.model

        #get fields in model that contains name or description
        model_fields = related_model._meta.get_fields()
        search_fields = [
            F"{field.name}__icontains"
            for field in model_fields
            if 'name' in field.name.lower() or 'description' in field.name.lower() or '_id' in field.name
        ]

        dependent_fields = [
            field.name
            for field in related_model._meta.get_fields()
            if isinstance(field, ForeignKey) and field.name in all_fields
        ]
        dependent_fields = {field:field for field in dependent_fields}
        filters['lookup'] = ModelMultipleChoiceFilter(
            label=f"{field_name} lookup",
            queryset=related_model.objects.all(),
            widget=ModelSelect2MultipleWidget(
                model = related_model,
                search_fields=search_fields,
                dependent_fields=dependent_fields,
                attrs={'data-placeholder': 'Select',
                
                "data-minimum-input-length": 0},
                

            )
        )
    elif isinstance(field,DateField):
        filters[f"{field_name}_range"] = DateFromToRangeFilter(
            widget=RangeWidget(attrs={'type':'date','class': 'form-control' })
        )
    elif field_name in CHOICE_FILTER_FIELDS.keys():
        config = CHOICE_FILTER_FIELDS[field_name]
        
        filters[f"{field_name}_lookup"] = MultipleChoiceFilter(
        choices=config['choices'],
        widget=CheckboxSelectMultiple
    )
    
    filters['contains'] = CharFilter(
            field_name=field_name,
            lookup_expr='icontains',
            widget=TextInput(attrs={'type':'text','class': 'form-control' }),
        )
    return filters

class CustomFilterSet(FilterSet):
    choice_filter_config = CHOICE_FILTER_FIELDS
    visible_columns = None
    universal_search_fields = None

    universal_search = CharFilter(
        method='my_custom_filter',
          label='Search',
          widget=TextInput(attrs={'type':'search','class': 'form-control','autofocus':None })    
          )

    def my_custom_filter(self, queryset, name, value):
        values_list = value.split(',') if ',' in value else value.split()

        q_object = Q()
        for term in values_list:
            term_q = reduce(
                lambda acc, field: acc | Q(**{field: term}),
                self.universal_search_fields,
                Q()
            )
            q_object &= term_q

        return queryset.filter(q_object)

    def filter_null_field(self, queryset, name, value):
        # value is a list, e.g. ['null', 'not_null']
        if not value:
            return queryset  # No filter (show all)

        queries = []
        if 'null' in value:
            queries.append({'my_field__isnull': True})
        if 'not_null' in value:
            queries.append({'my_field__isnull': False})

        q = queryset.none()
        for query in queries:
            q = q | queryset.filter(**query)
        return q


def dynamic_filterset_generator(filter_model, universal_search_fields, visible_columns=None, hidden_columns=None):
    attritutes = {}
    #remove hidden fields from visible columns
    if visible_columns and hidden_columns:
        visible_columns = [field for field in visible_columns if field not in hidden_columns]
    attritutes['visible_columns'] = visible_columns
    attritutes['universal_search_fields'] = universal_search_fields
    if visible_columns:
        attritutes = {}
        for key in visible_columns:
            filters = (generate_filter_for_field(filter_model, key, visible_columns))
            for filter_type,filter in filters.items():
                attritutes.update({f"{key}_{filter_type}":filter})
        attritutes.update({f"{key}_isnull":generate_checkbox_filter_for_field(filter_model,key) for key in visible_columns})


    class Meta:
        model = filter_model
        fields = ['universal_search']
        exclude = hidden_columns
    
    DynamicFilterSet =  type(
        f"{filter_model.__name__}_filterclass",
        (CustomFilterSet,),
        {**attritutes, 'Meta':Meta}    
    )

    return DynamicFilterSet