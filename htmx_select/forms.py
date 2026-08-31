from django import forms
from django.urls import reverse
from urllib.parse import urlencode
from django.db.models import ForeignKey, CharField


class HTMXMultiPickerWidget(forms.SelectMultiple):
    template_name = "htmx_select/htmx_multi_select.html"

    def __init__(
        self,
        model,
        fieldname,
        *,
        multiple=False,
        placeholder="Select ",
        search_url=None,
        autocomplete=True,
        modal=True,
        attrs=None,
    ):
        self.placeholder = placeholder
        self.autocomplete = autocomplete
        self.search_url=search_url
        self.modal = modal
        self.model = model
        self.field = self.get_field(fieldname)
        self.multiple = multiple
        self.widget_mode = self.get_widget_mode()

        super().__init__(attrs)

    def get_field(self, fieldname):
        return self.model._meta.get_field(fieldname)

    def get_widget_mode(self):
        if self.field.primary_key:
            return "model"

        if self.field.remote_field:
            return "foreign_key"

        if self.field.choices:
            return "choices"

        if isinstance(self.field, CharField):
            return "values"

        return None

    def get_search_url(self):
        if self.search_url:
            base_url = self.search_url 

        else:
            base_url = reverse(
                "htmx_picker_search",
                kwargs={
                    "modelpath": (
                        f"{self.model._meta.app_label}"
                        f"__"
                        f"{self.model._meta.model_name}"
                    ),
                    'fieldname': self.field.name
                },
            )
        query_params = urlencode({'multiple':self.multiple})
        return f"{base_url}?{query_params}"

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        widget = context["widget"]

        widget_id = widget["attrs"].get("id", f"id_{name}")

        widget["picker_id"] = f"{widget_id}_picker"
        widget["modal_id"] = f"{widget_id}_modal"
        widget["autocomplete_id"] = f"{widget_id}_autocomplete"
        widget["results_id"] = f"{widget_id}_results"
        widget["search_url"] = self.search_url or self.get_search_url()

        widget["placeholder"] = self.placeholder
        widget["autocomplete"] = self.autocomplete
        widget["modal"] = self.modal
        widget["multiple"] = self.multiple
        widget["fieldname"] = self.field.verbose_name

        existing_class = widget["attrs"].get("class", "")
        widget["attrs"]["class"] = (
            f"{existing_class} d-none"
        ).strip()

        if not value:
            return context

        selected_values = []

        # Values submitted by the browser.
        if not isinstance(value, list):
            value = [value]

        if self.widget_mode == 'foreign_key':
            selected_list = self.field.remote_field.model.objects.filter(pk__in=value)

            widget["selected_list"] = [
                    {
                        'value': obj.pk,
                        'label': str(obj), 
                    }
                    for obj in selected_list
                ]

        elif self.widget_mode == 'model':
            selected_list = self.field.model.objects.filter(pk__in=value)

            widget["selected_list"] = [
                    {
                        'value': obj.pk,
                        'label': str(obj), 
                    }
                    for obj in selected_list
                ]

        elif self.widget_mode == 'choices':
            selected_list = [
                (choice_value, choice_label)
                for choice_value, choice_label in self.field.choices
                if str(choice_value) in value
            ]

            widget["selected_list"] = [
                    {
                        'value': obj[0],
                        'label': obj[1], 
                    }
                    for obj in selected_list
                ]

        elif self.widget_mode == 'values':
            if isinstance(value, str):
                selected_values = value.split(",")
            elif isinstance(value, list):
                selected_values = value

            widget["selected_list"] = [
                    {
                        'value': value,
                        'label': str(value), 
                    }
                    for value in selected_values
                ]

        # Hide the actual Django select.


        return context

    def value_from_datadict(self, data, files, name):
        value = super().value_from_datadict(data, files, name)

        # if not multiple then return first value from value list 
        if value:
            if not self.multiple and len(value)>0:
                return value[0]

        return value 
