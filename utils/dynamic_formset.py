from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import TemplateView
from django import forms
import json
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic import (
    ListView,
)
from django.db import transaction
from urllib.parse import urlencode
from django.urls import reverse
from django.views.generic import UpdateView

from django.core.exceptions import ValidationError
from django.http import HttpResponse, HttpResponseRedirect
'''

config_example ={"test_eq":
                    {
                    "prefix": ,
                    "title": , 
                    "row_template_name": None,
                    "formset": ,
                    "model": Tblassets, # parent model used for lookup
                    "pk_field": pk_field of parent model
                    "initial": lambda obj: {
                        "fieldx": obj.fieldy, used to apply initial data to formset
                },
}
'''
class AddFormsetRowView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    TemplateView
):

    permission_required = None
    formset_config = None # Override in child
    template_name  = 'partials/dynamic_formset.html#row'


    def get_template_names(self):
        formset_type = self.kwargs["formset_type"]
        config = self.formset_config[formset_type]
        # use default template or one set from the config
        return [config.get('row_template_name', None) or 'partials/dynamic_formset.html#row']

    def get(self, request, *args, **kwargs):
        formset_type = self.kwargs["formset_type"]
        config = self.formset_config[formset_type]
        self.new_item_id = self.request.GET.get("lookup_id", None)

        existing_ids = {
            value
            for key, value in request.GET.items()
            if key.startswith(formset_type) and key.endswith(config["lookup_field"]) and value
        }

        if self.new_item_id in existing_ids:
            response = HttpResponse(status=200)
            response["HX-Trigger"] = json.dumps({
                "deliveries_updated": True,
                "show_message": {
                    "message": "Already added",
                    "level": "warning",
                },
            })
            return response

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        formset_type = self.kwargs["formset_type"]
        config = self.formset_config[formset_type]
        prefix = config["prefix"]
        total_forms = int(self.request.GET[f"{prefix}-TOTAL_FORMS"])


        # prefill form before rendering
        if self.new_item_id:
            obj = get_object_or_404(
                config["model"],
                **{config["pk_field"]: self.new_item_id},

            )
            initial = config["initial"](obj)

        form = config["formset"].form

        form = form(prefix=f"{prefix}-{total_forms}", initial=initial)

        if config["formset"].can_delete:
            form.fields["DELETE"] = forms.BooleanField(
                required=False,
                label="Delete"
            )

        context["prefix"] = prefix
        context["total_forms"] = total_forms
        context["form"] = form
        return context



class FormsetOptionsListView(
    ListView
):
    model = None # has to be overriden in child 
    config = None # has to be overriden in child
    template_name = 'formsets/formset_options.html' # can be overriden
    permission_required = None # has to be overriden
    add_formset_row_view = None


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        formset_type = self.kwargs.get('formset_type') 
        config = self.config[formset_type] 
        prefix = config["prefix"]
        context['prefix'] = prefix
        context['pk_field'] = config["pk_field"]
        context['lookup_field'] = config['lookup_field']
        context['add_url'] = reverse(self.add_formset_row_view, kwargs={'formset_type':prefix})
        return context


class CustomFormsetForm(forms.ModelForm):
    lookup_model = None
    lookup_field = None
    obj_str_repr = str 

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        obj = getattr(self.instance, self.lookup_field, None)

        if not obj:
            obj_id = (
                self.data.get(self.add_prefix(self.lookup_field))
                or self.initial.get(self.lookup_field)
                )
            if obj_id:
                obj = self.lookup_model.objects.filter(pk=obj_id).first()
                self.display_label = self.obj_str_repr(obj)
        if obj:
            self.display_label = self.obj_str_repr(obj)


class FormsetMixin(UpdateView):
    config = None

    def get_formsets(self):
            formsets = {}
            for prefix, formset_config in self.config.items():
                formset = formset_config['formset']
                if self.request.POST:
                    formset = formset(
                        self.request.POST, instance=self.object, prefix=prefix
                    )
                else:
                    formset = formset(
                        instance=self.object, prefix=prefix
                    )

                # add url for list of new formset value option
                list_app_view = formset_config.get('lookup_view', None)

                if list_app_view:
                    url = reverse(list_app_view, kwargs={'formset_type': prefix})
                    query_params_dict = {}
                    for k, v in formset_config.get('lookup_query_params', {}).items():
                        query_params_dict[k] = v(self) if callable(v) else v
                    
                    query_params = urlencode(query_params_dict)
                    formset.get_list_url = f"{url}?{query_params}"
                    formset.title = formset_config.get('title', None)

                formsets[prefix] = formset
            return formsets

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_formsets())
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formsets = [context[prefix] for prefix in self.config.keys()]


        if not all(formset.is_valid() for formset in formsets):
            raise ValidationError('Save not successful')

        try:
            with transaction.atomic():
                self.object = form.save()

                for formset in formsets:
                    formset.instance = self.object
                    formset.save()

        except Exception as e:
            form.add_error(None, f"Database integrity error: {e}")
            return self.form_invalid(form)

        response = HttpResponseRedirect(self.get_success_url())
        return response

    def form_invalid(self, form):
        context = self.get_context_data(form=form)
        context.update(self.get_formsets())
        return self.render_to_response(context)
