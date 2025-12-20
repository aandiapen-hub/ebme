from urllib.parse import urlencode
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import render
from django.views.generic.edit import FormMixin
from django_filters.views import FilterView
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django_tables2 import SingleTableMixin, CheckBoxColumn, TemplateColumn, Table
from django.db.models.query import QuerySet
from django.db.models import ForeignKey, DateField
from users.models import UserProfiles
from .qs_summary import data_summary2
from utils.generic_filters import (
    dynamic_filterset_generator,
    get_filter_fields,
    get_filter_from_field_lookup,
)

from django_tables2.export.views import ExportMixin


# get visible columns for a model for a user
def get_visible_columns(request, model):
    # Get user's preferred columns from user_profiles.table_settings
    user = request.user
    try:
        user_profile = UserProfiles.objects.get(user_id=user)
        user_columns = user_profile.get_preference(
            model.__name__, key="visible_columns"
        )
        if user_columns is None:
            # fallback to all model fields
            user_columns = [f.name for f in model._meta.fields]
    except Exception:
        # fallback to all model fields
        user_columns = [f.name for f in model._meta.fields]
    return user_columns


class BulkUpdateView(
    LoginRequiredMixin, PermissionRequiredMixin, FormMixin, FilterView
):
    """
    A reusable view for bulk updating filtered and selected queryset items.
    Requires:
      - model
      - form_class
      - filterset_class
      - context_object_name
      - success_url
      - table_class
    Optional:
      - view
      - summary_field_names
      - record_type
    """

    model = None  # must overide in child class
    template_name = "bulk_update.html"
    permission_required = None  # Optional: for external permission mixins
    summary_field_names = None  # Optional: list of field names for summary
    view = None
    selected_ids = None

    def get(self, request, *args, **kwargs):
        if request.htmx:
            return HttpResponse(headers={"HX-Redirect": request.get_full_path()})
        return super().get(request, *args, **kwargs)

    def get_table_class(self):
        # Dynamically create table class if not provided
        table = get_dynamic_table_class(
            table_model=self.model,
            visible_columns=get_visible_columns(self.request, self.model),
        )
        return table

    def get_filterset_class(self):
        active_filters = [
            key
            for key, value in self.request.GET.items()
            if key
            not in [
                "new_active_filter",
                "page",
                "csrfmiddlewaretoken",
                "universal_search",
                "sort",
            ]
        ]
        return dynamic_filterset_generator(
            self.model,
            universal_search_fields=self.universal_search_fields,
            active_filters=active_filters,
        )

    def get_queryset(self):
        qs = super().get_queryset()
        self.filterset = self.filterset_class(self.request.GET, queryset=qs)
        qs = self.filterset.qs
        selected_ids = self.request.GET.getlist("selected")
        if selected_ids:
            qs = qs.filter(pk__in=selected_ids)
        self.request.session["selected_ids"] = list(qs.values_list("pk", flat=True))
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        data = self.get_queryset()

        context["record_type"] = self.context_object_name

        if self.table_class:
            context["table"] = self.table_class(data)

        if self.summary_field_names:
            context["data_summary"] = data_summary2(
                model=self.model,
                qs=data,
            )

        return context

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        selected_ids = self.request.session.pop("selected_ids", [])

        if form.is_valid():
            updates = {
                field: value
                for field, value in form.cleaned_data.items()
                if value not in [None, ""]
            }

            if updates:
                if self.db_table:
                    self.db_table.objects.filter(pk__in=selected_ids).update(**updates)
                else:
                    self.model.objects.filter(pk__in=selected_ids).update(**updates)
                messages.success(
                    request, f"{self.context_object_name} updated successfully."
                )

            else:
                messages.warning(
                    request, f"No {self.context_object_name} were provided to update."
                )

            base_url = super().get_success_url()
            query_params = urlencode(
                {"universal_search": ",".join(map(str, selected_ids))}
            )
            return HttpResponseRedirect(f"{base_url}?{query_params}")

        return self.form_invalid(form)


class CustomCheckBoxColumn(CheckBoxColumn):
    def header(self):
        return "Select"


# Function to dynamically create table class
def get_dynamic_table_class(
    table_model, excluded_columns, visible_columns=None, template_columns=None
):
    """
    Create a dynamic Table class based on user's column preferences.

    - model: Django model
    - user: request.user
    - template_columns: optional dict of {column_name: template_code} for TemplateColumns
    """

    # Build columns dict
    table_columns = {}

    # remove hidden fields from visible columns
    if visible_columns and excluded_columns:
        visible_columns = [f for f in visible_columns if f not in excluded_columns]

    # Add template columns first (if any)
    if template_columns:
        for col_name, template_name in template_columns.items():
            table_columns[col_name] = TemplateColumn(
                template_name=template_name,
                verbose_name=col_name.title(),
                orderable=False,
                attrs={"td": {"style": "position: sticky; left:0; ; z-index:3;"}},
            )

    # Always include checkbox column
    table_columns["selected"] = CustomCheckBoxColumn(
        accessor="pk"
    )  # Define Meta dynamically

    class Meta:
        model = table_model
        attrs = {
            "class": "table table-hover table-bordered table-striped  ",
            "thead": {
                "class": "table-bordered align-middle",
                "style": ("position: sticky; top: 0; z-index: 1; "),
            },
        }
        template_name = "tables/tables2_with_filter.html"
        if template_columns:
            fields = (
                (["open"] if template_columns.get("open", []) else [])
                + visible_columns
                + (["actions"] if template_columns.get("actions", []) else [])
            )
        else:
            fields = visible_columns
            excluded = excluded_columns

    # Dynamically create the table class
    DynamicTable = type(
        f"{table_model.__name__}DynamicTable", (Table,), {**table_columns, "Meta": Meta}
    )
    return DynamicTable


# 3. Generic filtered table view
class FilteredTableView(SingleTableMixin, ExportMixin, FilterView):
    paginate_by = 20
    permission_required = None  # Override in subclass - Mandatory
    model = None  # override in subclass - Mandatory
    template_columns = None  # override in subclass - optional
    template_name = None  # override in subclass - Mandatory
    universal_search_fields = None  # override in subclass - Mandatory
    exclude = []  # override in subclass - optional

    def dispatch(self, request, *args, **kwargs):
        self.visible_columns = get_visible_columns(self.request, self.model)
        # check if only summary of a field is required
        self.summary_field = request.GET.get("summary_field")
        response = super().dispatch(request, *args, **kwargs)
        if self.summary_field:
            query = request.GET.copy()
            for k in list(query.keys()):
                if "summary_field" in k:
                    del query[k]
            context_data = {}
            context_data["querystring"] = query.urlencode()
            field_data = self.get_summary_field_data()
            context_data["summary_field_data"] = field_data
            return render(request, "partials/field_summary_data.html", context_data)

        if getattr(self, "new_filter_context", False):
            return render(request, "partials/new_filter.html", self.new_filter_context)
        return response

    def get_table_class(self):
        # Dynamically create table class if not provided
        table = get_dynamic_table_class(
            table_model=self.model,
            visible_columns=get_visible_columns(self.request, self.model),
            excluded_columns=self.exclude,
            template_columns=self.template_columns,
        )
        return table

    def get_summary_field_data(self):
        # get summary get_context_data
        # summary not available for date fields
        field = self.model._meta.get_field(self.summary_field)
        # check for datefield
        if isinstance(field, DateField):
            return {
                "status": "datefield",
                "data": {"field": field},
            }

        table_data = self.get_table_data()

        from collections import Counter

        values_qs = Counter(table_data.values_list(field.name, flat=True))
        if len(values_qs) > 5000:
            return {"status": "high_row_count", "data": {"field": field}}

        if isinstance(field, ForeignKey):
            related_model = field.remote_field.model
            related_objs = related_model.objects.filter(pk__in=values_qs.keys())
            id_to_name = {a.pk: str(a) for a in related_objs}

            items = [
                {
                    "pk": pk,
                    "name": id_to_name.get(pk, "Unknown"),
                    "count": count,
                    "fieldname": field.name,
                    "checked": str(pk)
                    in self.request.GET.getlist(f"{field.name}__iexact", None),
                }
                for pk, count in values_qs.items()
            ]

        else:
            items = [
                {
                    "pk": pk,
                    "name": str(pk),
                    "count": count,
                    "fieldname": field.name,
                    "checked": str(pk)
                    in self.request.GET.getlist(f"{field.name}__iexact", None),
                }
                for pk, count in values_qs.items()
            ]

        return {
            "status": "list",
            "data": sorted(items, key=lambda x: (x["name"] or "")),
        }

    def get_filterset_kwargs(self, filterset_class):
        # Copy the GET params to make them mutable
        data = self.request.GET.copy()
        # Remove unwanted parameter(s)
        param_to_remove = "summary_field"
        field = data.get("summary_field")
        if param_to_remove in data:
            del data[param_to_remove]

        # Or remove all keys containing a substring
        if field:
            for key in list(data.keys()):
                if "summary_field" in key or field in key:
                    del data[key]
        # Pass the cleaned GET data to the FilterSet
        return {
            "data": data,
            "queryset": self.get_queryset(),
            "request": self.request,
        }

    def get_filterset_class(self):
        active_filters = [
            key
            for key, value in self.request.GET.items()
            if key
            not in [
                "new_active_filter",
                "page",
                "csrfmiddlewaretoken",
                "universal_search",
                "sort",
            ]
        ]
        new_filter = self.request.GET.get("new_active_filter")
        if new_filter is not None and new_filter in active_filters:
            return None

        if new_filter is not None and new_filter not in active_filters:
            active_filters += new_filter
            self.new_filter_context = {}

            filter_obj = get_filter_from_field_lookup(self.model, new_filter)
            # Build a temporary Form class with that field
            from django import forms

            class DynamicForm(forms.Form):
                pass

            DynamicForm.base_fields[new_filter] = filter_obj.field
            form = DynamicForm()

            # Return the *bound* field
            self.new_filter_context["form"] = form

        return dynamic_filterset_generator(
            self.model,
            universal_search_fields=self.universal_search_fields,
            active_filters=active_filters,
        )

    def get_template_names(self):
        if self.request.htmx:
            return ["filter_table.html#table-partial"]
        return [self.template_name]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        table_data = self.get_table_data()
        # give a model name that can be used by
        # column chooser to get column list
        context["model_name"] = self.model._meta.label
        context["filter_fields"] = get_filter_fields(self.model, self.visible_columns)

        # get columns

        if self.visible_columns:
            self.visible_columns = [
                f for f in self.visible_columns if f not in self.exclude
            ]
            # Example of adding data summary
            if table_data is not None and hasattr(self, "model"):
                context["data_summary"] = data_summary2(model=self.model, qs=table_data)

        cleaned_data = getattr(context["filter"].form, "cleaned_data", {})
        context["has_active_filters"] = any(
            v not in ("", [], {}, None)
            and not (isinstance(v, QuerySet) and not v.exists())
            for v in cleaned_data.values()
        )

        return context
