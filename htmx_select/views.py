from dataclasses import field
from functools import cached_property
from django.http import Http404
from django.db.models import(
    Q,
    IntegerField,
    DecimalField,
    FloatField,
)
from django.db.models import ForeignKey

from django.views.generic import ListView
from django.apps import apps

from django.contrib.auth.mixins import LoginRequiredMixin


class HtmxPickerSearch(
    LoginRequiredMixin,
    ListView
):
    paginate_by = 20
    template_name = 'htmx_select/search_result.html'

    def dispatch(self, request, *args, **kwargs):
        self.field = self.get_field()
        self.model = self.set_model()
        return super().dispatch(request, *args, **kwargs)

    @cached_property
    def get_model(self):
        model_path = self.kwargs["modelpath"]
        try:
            app_label, model_name = model_path.split("__", 1)
            model = apps.get_model(app_label, model_name)
        except (ValueError, LookupError):
            raise Http404

        picker = getattr(model, "htmx_picker", None)

        if not picker or not getattr(picker, "enabled", False):
            raise Http404

        return model

    def get_field(self):
        fieldname = self.kwargs["fieldname"]
        model = self.get_model

        return model._meta.get_field(fieldname)

    @cached_property
    def is_related_field(self):
        return isinstance(self.field, ForeignKey)

    def set_model(self):
        if not self.is_related_field:
            return self.get_model

        else:
            return self.field.remote_field.model

    @cached_property
    def get_config(self):
        return self.model.htmx_picker

    def apply_customer_scope(self, qs):
        if self.request.user.is_staff:
            return qs

        customer_id = self.request.user.customerid

        if not customer_id:
            return qs.none()

        field_name =  self.get_config.customer_scope
        
        if not field_name:
            return qs

        conditions = Q()

        conditions |= Q(**{field_name:customer_id})

        return qs.filter(conditions)

    def get_option_label(self, obj):
        option_str = getattr(
            self.model.htmx_picker,
            "label_str",
            str,
        ) or str
        return option_str(obj)

    def get_distinct_values(self,qs):

        if isinstance(field, (
            IntegerField,
            DecimalField,
            FloatField,
        )):
            qs = (
                qs.exclude(**{f"{self.field.name}__isnull": True})
                .exclude(**{self.field.name: ""})
            )

        qs = (
            qs.order_by()
            .values_list(self.field.name, flat=True)
            .distinct()
        )
        q = self.request.GET.get("q", "").strip()

        if q:
            qs = qs.filter(
                **{f"{self.field.name}__icontains": q}
            )

        return qs[:20]

    def apply_q_filter(self,qs):

        q = self.request.GET.get('q', None)

        if q:
            search_terms = self.get_config.search_terms
            q_object = Q()

            for term in search_terms:
                q_object |= Q(**{term: q})
            qs = qs.filter(q_object)
        return qs

    def get_queryset(self):
        qs = super().get_queryset()
        qs = self.apply_customer_scope(qs)

        if self.is_related_field:
            qs = self.apply_q_filter(qs)

        else:
            qs =self.get_distinct_values(qs)

        return qs

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        fieldname =  self.request.GET.get('fieldname', None)
        if fieldname:
            context['selected'] = self.request.GET.getlist(fieldname)

        context['multiple'] = self.request.GET.get('multiple', '').lower() == 'true'

        if self.is_related_field:
            context['options'] = [
                {
                    'value': obj.pk,
                    'label': self.get_option_label(obj)
                }
                for obj in context['object_list'] 
            ]
        else:
            context['options'] = [
                {
                    'value': value,
                    'label': str(value), 
                }
                for value in context['object_list'] 
            ]

        return context


