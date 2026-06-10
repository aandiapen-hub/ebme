from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import TemplateView
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


    def get_template_names(self):
        formset_type = self.kwargs["formset_type"]
        config = self.formset_config[formset_type]
        return [config.get('row_template_name')]


    def get(self, request, *args, **kwargs):
        formset_type = self.kwargs["formset_type"]
        config = self.formset_config[formset_type]
        lookup_param = self.request.GET.get(config["lookup_param"], None)

        existing_ids = {
            value
            for key, value in request.GET.items()
            if key.endswith("_input_id") and value
        }

        if lookup_param in existing_ids:
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

        context["prefix"] = prefix
        context["total_forms"] = total_forms
        context["form"] = form
        return context

