from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import TemplateView
from django import forms
import json
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic import (
    ListView,
)

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

    permission_required = "assets.change_tbljob"
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

        formset = config["formset"].form
        form = formset(prefix=f"{prefix}-{total_forms}", initial=initial)

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
    LoginRequiredMixin,
    PermissionRequiredMixin,
    ListView
):
    model = None # has to be overriden in child 
    config = None # has to be overriden in child
    template_name = 'formsets/formset_options.html' # can be overriden
    permission_required = None # has to be overriden


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        formset_type = self.request.GET.get('formset_type') 
        config = self.config[formset_type] 
        context['prefix'] = config["prefix"]
        context['pk_field'] = config["pk_field"]
        context['lookup_field'] = config['lookup_field']
        return context
