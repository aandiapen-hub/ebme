from django import forms
from django.urls import reverse
from urllib.parse import urlencode


class HTMXModelSelectWidget(forms.TextInput):
    template_name = "htmx_select/htmx_model_select.html"

    def __init__(
        self,
        *,
        search_url=None,
        placeholder="Select...",
        autocomplete=True,
        modal=True,
        attrs=None,
        model=None,
    ):
        self.search_url = search_url
        self.placeholder = placeholder
        self.autocomplete = autocomplete
        self.modal = modal
        self.model = model

        super().__init__(attrs)

    def get_search_url(self):
        return reverse(
            "htmx_model_search",
            kwargs={
                "modelpath": (
                    f"{self.model._meta.app_label}"
                    f"__"
                    f"{self.model._meta.model_name}"
                )
            },
        )

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        widget = context["widget"]

        # The Django field ID, e.g. id_customer
        widget_id = widget["attrs"].get("id", f"id_{name}")

        widget["picker_id"] = f"{widget_id}_picker"
        widget["modal_id"] = f"{widget_id}_modal"
        widget["autocomplete_id"] = f"{widget_id}_autocomplete"
        widget["results_id"] = f"{widget_id}_results"

        
        widget["search_url"] = self.search_url or self.get_search_url()
        widget["placeholder"] = self.placeholder
        widget["autocomplete"] = self.autocomplete
        widget["modal"] = self.modal
        # Find the label of the currently selected option.
        selected = None
        selected_list =[]

        if value and self.model:
            try:
                selected = self.model.objects.get(pk=value)
            except self.field.queryset.model.DoesNotExist:
                pass

        widget["selected"] = selected


        # We don't want the normal select visible.
        existing_class = widget["attrs"].get("class", "")
        widget["attrs"]["class"] = f"{existing_class} d-none".strip()
        

        return context


class HTMXModelMultiSelectWidget(forms.SelectMultiple):
    template_name = "htmx_select/htmx_model_multi_select.html"

    def __init__(
        self,
        *,
        search_url=None,
        placeholder="Select...",
        autocomplete=True,
        modal=True,
        attrs=None,
        model=None,
    ):
        self.search_url = search_url
        self.placeholder = placeholder
        self.autocomplete = autocomplete
        self.modal = modal
        self.model = model

        super().__init__(attrs)

    def get_search_url(self):
        if self.search_url:
            base_url = self.search_url 

        else:
            base_url = reverse(
                "htmx_model_search",
                kwargs={
                    "modelpath": (
                        f"{self.model._meta.app_label}"
                        f"__"
                        f"{self.model._meta.model_name}"
                    )
                },
            )
        query_params = urlencode({'multiple':True})
        return f"{base_url}?{query_params}"

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        widget = context["widget"]

        # The Django field ID, e.g. id_customer
        widget_id = widget["attrs"].get("id", f"id_{name}")

        widget["picker_id"] = f"{widget_id}_picker"
        widget["modal_id"] = f"{widget_id}_modal"
        widget["autocomplete_id"] = f"{widget_id}_autocomplete"
        widget["results_id"] = f"{widget_id}_results"

        
        widget["search_url"] = self.get_search_url()
        widget["placeholder"] = self.placeholder
        widget["autocomplete"] = self.autocomplete
        widget["modal"] = self.modal

        # Find the label of the currently selected option.
        selected = None
        selected_list =[]

        if value and self.model:
            try:
                selected_list = self.model.objects.filter(pk__in=value)
            except self.field.queryset.model.DoesNotExist:
                pass

        widget['selected_list'] = selected_list

        # We don't want the normal select visible.
        existing_class = widget["attrs"].get("class", "")
        widget["attrs"]["class"] = f"{existing_class} d-none".strip()

        return context


class HTMXMultiPickerWidget(forms.SelectMultiple):
    template_name = "htmx_select/htmx_multi_select.html"

    def __init__(
        self,
        model,
        field,
        *,
        placeholder="Select...",
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
        self.field = field

        super().__init__(attrs)

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
        query_params = urlencode({'multiple':True})
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

        selected_values = []
        # Values submitted by the browser.
        if isinstance(value, str):
            selected_values = value.split(",")
        else:
            selected_values = value or []

        widget["selected_list"] = selected_values

        # Hide the actual Django select.
        existing_class = widget["attrs"].get("class", "")
        widget["attrs"]["class"] = (
            f"{existing_class} d-none"
        ).strip()


        return context
