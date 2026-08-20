from dataclasses import field
from functools import cached_property
from django.http import Http404
from django.db.models import(
    Q,
    IntegerField,
    DecimalField,
    FloatField,
)
from django.views.generic import ListView
from django.apps import apps


class HtmxModelSelectSearch(ListView):
    paginate_by = 20
    template_name = 'htmx_select/model_search_result.html'

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

    @cached_property
    def get_config(self):
        return self.model.htmx_picker

    def dispatch(self, request, *args, **kwargs):
        self.model = self.get_model()
        return super().dispatch(request, *args, **kwargs)

    def apply_customer_scope(self, qs):
        if self.request.user.is_staff:
            return qs

        customer_id = self.request.user.customer_id

        if not customer_id:
            return qs.none()

        field_names =  self.get_config.customer_scope
        
        if not field_names:
            return qs

        conditions = Q()

        for field in field_names:
            conditions |= Q(**{field:customer_id})

        return qs.filter(conditions)

    def get_option_label(self, obj):
        option_str = getattr(
            self.model.htmx_picker,
            "label_str",
            str,
        )
        return option_str(obj)

    def get_queryset(self):
        qs = super().get_queryset()
        qs = self.apply_customer_scope(qs)

        q = self.request.GET.get('q', None)

        if q:
            search_terms = self.get_config.search_terms
            q_object = Q()

            for term in search_terms:
                q_object |= Q(**{term: q})
            qs = qs.filter(q_object)

        for obj in qs:
            obj.htmx_option_str = self.get_option_label(obj)
        return qs

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['selected'] = self.request.GET.getlist(f"{self.model._meta.pk.name}__iexact")
        if self.request.GET.get('multiple', None):
            context['multiple'] = True
        return context


class HtmxPickerSearch(ListView):
    paginate_by = 20
    template_name = 'htmx_select/search_result.html'

    def dispatch(self, request, *args, **kwargs):
        self.model = self.get_model()
        self.field = self.get_field()
        return super().dispatch(request, *args, **kwargs)

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
        return self.model._meta.get_field(fieldname)

    def apply_customer_scope(self, qs):
        if self.request.user.is_staff:
            return qs

        customer_id = self.request.user.customer_id

        if not customer_id:
            return qs.none()

        field_names =  self.get_config.customer_scope
        
        if not field_names:
            return qs

        conditions = Q()

        for field in field_names:
            conditions |= Q(**{field:customer_id})

        return qs.filter(conditions)       

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

    def get_queryset(self):
        qs = super().get_queryset()
        qs = self.apply_customer_scope(qs)
        return self.get_distinct_values(qs)


    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['multiple'] = True
        return context
