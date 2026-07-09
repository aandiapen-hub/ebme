from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import TemplateView
from django import forms
import json
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

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
        return [config.get('row_template_name', None) or 'partials/dynamic_formset.html#row']

    def get(self, request, *args, **kwargs):
        formset_type = self.kwargs["formset_type"]
        config = self.formset_config[formset_type]
        new_item_id = self.request.GET.get(config["lookup_param"], None)

        existing_ids = {
            value
            for key, value in request.GET.items()
            if key.startswith(formset_type) and key.endswith(config["pk_field"]) and value
        }

        if new_item_id in existing_ids:
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
        lookup_param = self.request.GET.get(config["lookup_param"], None)
        if lookup_param:
            obj = get_object_or_404(
                config["model"],
                **{config["pk_field"]: lookup_param},

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

