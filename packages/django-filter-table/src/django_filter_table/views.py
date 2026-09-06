from datetime import datetime
from typing import Literal
import re

from dataclasses import field
from datetime import datetime
from functools import cached_property
from django.urls import reverse
from django_htmx.http import HttpResponseClientRedirect
from django.db import IntegrityError
from django.contrib import messages
from django.shortcuts import render
from django.views.generic.edit import FormMixin
from django.views.generic import View, TemplateView, ListView
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin, CheckBoxColumn, TemplateColumn, Table, Column
from django.db.models import(
    ForeignKey,
    DateField,
    JSONField,
    Subquery,
    IntegerField,
    DecimalField,
    FloatField,
    CharField,
    Q,
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.core.paginator import Paginator
from urllib.parse import urlencode
from .generic_filters import (
    dynamic_filterset_generator,
    get_filter_fields,
    get_filter_from_field_lookup,
)
from django_tables2.export.views import ExportMixin
from django.core.exceptions import ValidationError

from django.http.response import HttpResponse, HttpResponseRedirect
from django import forms
from django.apps import apps
from django.http import QueryDict
from dataclasses import dataclass
from django.conf import settings

from django.http import Http404


EXPORT_LIMIT = 3000


# get visible columns for a model for a user
# Get user's preferred columns from user_profiles.table_settings
#

def get_user_profile_model():
    return apps.get_model(
        settings.DJANGO_TABLE["user_profile_model"]
    )

def get_visible_columns(request, model, open_column=None):
    UserProfiles = get_user_profile_model()
    user = request.user
    try:
        user_profile = UserProfiles.objects.get(user_id=user)
        user_columns = user_profile.get_preference(
            model.__name__, key="visible_columns"
        )
    except Exception:
        # fallback to all model fields
        return [field.name for field in model._meta.get_fields() if field.concrete and not field.auto_created]

    user_columns.append(open_column)
    return user_columns


class CustomCheckBoxColumn(CheckBoxColumn):
    verbose_name = ""


from django_tables2.utils import OrderByTuple

class CustomBaseTable(Table):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self._meta.model._meta.get_fields():
            if not isinstance(field, ForeignKey):
                continue

            try:
                column = self.columns[field.name]
            except KeyError:
                continue

            ordering = field.remote_field.model._meta.ordering
            if not ordering:
                continue

            column.column.order_by = OrderByTuple(
                (
                    f"-{field.name}__{item.lstrip('-')}"
                    if item.startswith("-")
                    else f"{field.name}__{item}"
                    for item in ordering
                )
            )

# Function to dynamically create table class
def get_dynamic_table_class(
        table_model,
        visible_columns=None,
        template_columns=None,
        open_column=None):
    """
    Create a dynamic Table class based on user's column preferences.

    - model: Django model
    - user: request.user
    - template_columns: optional dict of {column_name: template_code} for TemplateColumns
    """

    # Build columns dict
    table_columns = {}

    # Add template columns first (if any)
    if template_columns:
        for col_name, template_name in template_columns.items():
            table_columns[col_name] = TemplateColumn(
                template_name=template_name,
                verbose_name=col_name.title(),
                orderable=False,
                attrs={"td": {"style": "position: sticky; left:0; ; z-index:3;"}},
            )

    if open_column:
        table_columns[open_column] = Column(
            linkify=True,
        )
        if open_column in visible_columns:
            visible_columns.remove(open_column)


    # Always include checkbox column
    table_columns["selected"] = CustomCheckBoxColumn(
        accessor="pk", exclude_from_export=True,
    )  # Define Meta dynamically


    class Meta:
        model = table_model

        per_page = 20
        attrs = {
            "class": "table table-hover table-bordered table-striped  ",
            "thead": {
                "class": "table-bordered align-middle",
                "style": "position: sticky; top: 0; z-index: 1;",
            },
        }
        template_name = "django_filter_table/tables/tables2_with_filter.html"
        if template_columns:
            fields = (
                ["selected"]
                + ([open_column] if open_column else [])
                + visible_columns
                + (["actions"] if template_columns.get("actions", []) else [])
            )
        else:
            fields = ['selected'] + [open_column] if open_column else [] 
            fields += visible_columns

    # Dynamically create the table class
    DynamicTable = type(
        f"{table_model.__name__}DynamicTable", (CustomBaseTable,), {**table_columns, "Meta": Meta}
    )
    return DynamicTable


class TableViewActionsContentMixins:
    actions = {}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        actions = []
        if self.actions:
            for action in self.actions:
                if self.request.user.has_perm(action.permission):
                    actions.append(action)
        context["actions"] = actions
        return context


# 3. Generic filtered table view
class FilteredTableView(
    TableViewActionsContentMixins,
    SingleTableMixin,
    ExportMixin,
    FilterView,
):
    title = None  # Override in subclass - Mandatory
    permission_required = None  # Override in subclass - Mandatory
    model = None  # override in subclass - Mandatory
    open_column = None # override in subclass - Mandatory
    template_columns = None  # override in subclass - optional
    template_name = "django_filter_table/filter_table.html"  # override in subclass - Mandatory
    universal_search_fields = None  # override in subclass - Mandatory
    default_columns = None
    actions = None  # overridein subclass if bulk actions are available
    quick_filters = None # list of django filters made up of lookup combinations. e.g {'quick_filter': ['pk__in'=[1,2], field2 = 'value2']}
    additional_session_filters = None # Set of filter function names. the filter functions needs to be defined on the child class

    def dispatch(self, request, *args, **kwargs):
        self.visible_columns = (
            get_visible_columns(self.request, self.model, open_column=self.open_column) or self.default_columns
        )

        # --- check what type of request---#
        # request options are  summary data, new filter, remove session filter or  actual filter result data
        # if remove session filter
        if self.request.GET.get("reset_session_filter"):
            self.request.session.pop(self.request.path, None)

        # if summary data requested, process and return list of summary field data values
        self.summary_field = request.GET.get("summary_field")
        if self.summary_field:

            return self.get_summary_field_data()

        # if new filter is requested to, return the requested filter widget
        # call parent's dispatch so that the check for new filter is completed
        response = super().dispatch(request, *args, **kwargs)
        if getattr(self, "new_filter_context", False):
            return render(request, "django_filter_table/new_filter.html", self.new_filter_context)

        # fallback is to return of filtered table data
        return response

    def create_export(self, export_format):
        queryset = self.get_table_data()
        total = queryset.count()
        if total > EXPORT_LIMIT:
            messages.error(self.request, f"Export limited to {EXPORT_LIMIT} rows.")
            return HttpResponseRedirect(self.request.path)
        if self.request.htmx:
            response = HttpResponse(status=200)
            response["HX-Redirect"] = self.request.get_full_path()
            return response
        return super().create_export(export_format)

    def get_table_class(self):
        # Dynamically create table class if not provided
        table = get_dynamic_table_class(
            table_model=self.model,
            visible_columns=self.visible_columns.copy(),
            template_columns=self.template_columns,
            open_column=self.open_column
        )
        table.search_term = self.request.GET.get('universal_search','')
        return table

    def get_table(self, **kwargs):
        
        table = super().get_table(**kwargs)
        # add the regex for the text to be hightlighted in the table
        # to the table context
        search_term = self.request.GET.get("universal_search", None)
        if search_term:
            table.src_re_obj = re.compile(re.escape(search_term), re.IGNORECASE)
            table.search_fields = [x.split("__", 2)[0] for x in self.universal_search_fields]
        else:
            table.src_re_obj =  None
            table.search_fields = None
            
        return table

    def clean_name(self, value):
        REMOVE_CHARS = str.maketrans("", "", '\n\r"')
        if not value:
            return "Unknown"

        return str(value).translate(REMOVE_CHARS).strip()

    def get_summary_field_data(self):
        # get requested summary field from model
        field = self.model._meta.get_field(self.summary_field)

        # return full template or partial of only the results
        result_only = self.request.GET.get('result_only')



        # summary data not available for date fields
        if isinstance(field, JSONField):
            summary_field_data = {
                "status": "datefield",
                "data": None,
            }

            return self._render_field_summary(summary_field_data, field)

        if isinstance(field, ForeignKey):
            config = field.related_model._meta.ordering
            if config:
                order_fieldname = config[0]
                order_by_field = f"{field.name}__{order_fieldname}"
            else:
                order_by_field = f"{field.name}"
        elif isinstance(field, DateField):
            order_by_field = f"-{field.name}"
        else:
            order_by_field = field.name
        table_data = self.get_table_data()

        items = {}
        summary_qs = (
            table_data
            .values(field.name)
            .annotate(count=Count("pk"))
            .order_by(order_by_field)
        )
        

        
        #filter summary data by search term
        search_term = self.request.GET.get('search_summary_data','').strip()
        if search_term:
            if isinstance(field, ForeignKey):
                search_terms = field.related_model.htmx_picker.search_terms

                q_object = Q()
                for term in search_terms:
                    q_object |= Q(**{f"{field.name}__{term}": search_term})
                summary_qs = summary_qs.filter(q_object)
            else:
                summary_qs = summary_qs.filter(
                    **{
                        f"{field.name}__icontains": search_term
                    }
                )

        paginator = Paginator(summary_qs, 20)


        page_number = self.request.GET.get(
            "summary_page",
            1,
        )

        page = paginator.get_page(page_number)


        values = list(page.object_list)

        selected_values = self.request.GET.getlist(
            f"{field.name}__iexact"
        )

        if page.number == 1:

            existing_values = {
                str(row[field.name])
                for row in values
            }

            missing_selected = [
                value for value in selected_values
                if value not in existing_values
            ]

            unfiltered_data = (
                self.model
                .objects 
                .values(field.name)
                .annotate(count=Count("pk"))
                .order_by(order_by_field)
            )
            selected_values_qs = unfiltered_data.filter(
                **{f"{field.name}__in": missing_selected}
            ) if missing_selected else summary_qs.none()

            #add selected values to page values
            values += list(selected_values_qs)

        if result_only:
            values = [
                row for row in values
                if row[field.name] not in selected_values
            ]

        page_offset = (page.number - 1) * paginator.per_page

        if field.choices:
            # map value -> label
            value_to_label = dict(field.choices)
            items = [
                {
                    "pk": row[field.name],
                    "name": self.clean_name(value_to_label.get(row[field.name])),
                    "count": row["count"],
                    "order": page_offset + index,
                    "fieldname": field.name,
                    "checked": str(row[field.name]) in selected_values,
                }
                for index, row in enumerate(values, start=1)
            ]
        elif isinstance(field, ForeignKey):
            related_ids = [row[field.name] for row in values]

            related_objs = field.remote_field.model.objects.filter(
                pk__in=related_ids
            )

            id_to_name = {
                obj.pk: str(obj)
                for obj in related_objs
            }
            items = [
                {
                    "pk": row[field.name],
                    "name": self.clean_name(id_to_name.get(row[field.name])),
                    "count": row["count"],
                    "order": page_offset + index,
                    "fieldname": field.name,
                    "checked": str(row[field.name]) in selected_values,
                }
                for index, row in enumerate(values, start=1)
            ]

        elif isinstance(field, DateField):
            items = [
                {
                    "pk": datetime.strftime(row[field.name], '%Y-%m-%d'),
                    "name": datetime.strftime(row[field.name], '%Y-%m-%d'),
                    "order_by": row[field.name],
                    "count": row["count"],
                    "order": page_offset + index,
                    "fieldname": field.name,
                    "checked": str(row[field.name]) in selected_values,
                }
                for index, row in enumerate(values, start=1) if row[field.name]
            ]
        else:
            items = [
                {
                    "pk": row[field.name],
                    "name": self.clean_name(row[field.name]),
                    "count": row["count"],
                    "order": page_offset + index,
                    "fieldname": field.name,
                    "checked": str(row[field.name]) in selected_values,
                }
                for index, row in enumerate(values, start=1)
            ]

        # summariese all other type of data
        summary_field_data = {
            "status": "list",
            "data": items,
            "page": page,
            "page_number_name": "summary_page",
            "search_term":search_term
        }

        return self._render_field_summary(summary_field_data, field, result_only)

    def _render_field_summary(self, summary_field_data, field, result_only):
        query = self.request.GET.copy()
        for k in list(query.keys()):
            if "summary_field" in k:
                del query[k]
        context_data = {}
        context_data["querystring"] = query.urlencode()
        context_data["summary_field_data"] = summary_field_data
        context_data['field'] = field
        if result_only:
            return render(self.request, "django_filter_table/field_summary_data.html#values", context_data)
        return render(self.request, "django_filter_table/field_summary_data.html", context_data)

    def get_filterset_kwargs(self, filterset_class):
        # Copy the GET params to make them mutable
        data = self.request.GET.copy()  # Remove unwanted parameter(s)
        param_to_remove = "summary_field"
        field = data.get("summary_field")
        if param_to_remove in data:
            del data[param_to_remove]

        # Or remove all keys containing a substring
        if field:
            for key in list(data.keys()):
                if "summary_field" in key or field in key:
                    del data[key]

        qs = self.get_queryset()

        if self.request.method == "GET":
            selected_ids = self.request.GET.getlist("selected")
        else:
            selected_ids = self.request.POST.getlist("selected")

        if selected_ids:
            qs = qs.filter(pk__in=selected_ids)
        # Pass the cleaned GET data to the FilterSet
        return {
            "data": data,
            "queryset": qs,
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
            return ["django_filter_table/filter_table.html#table-partial"]
        return [self.template_name]

    def apply_additional_session_filter(self, qs, session_filter, filter_qd):

        addional_filter_name = filter_qd.get('additional_filter_options', None)
        if addional_filter_name:
            filter = getattr(self, addional_filter_name, None)
            if filter:
                return filter(qs)
        return qs

    def get_table_data(self):
        self.filterset = self.get_filterset(self.get_filterset_class())

        queryset = self.filterset.qs

        session_filter = self.request.session.get(self.request.path, {})

        if session_filter:
            filter_params = session_filter.get("filter_params")
            filter_qd = QueryDict(mutable=True)
            if filter_params:
                for key, values in filter_params:
                    for v in values:
                        filter_qd.update({key: v})

            queryset = apply_session_filter(queryset, session_filter, filter_qd)
            queryset = self.apply_additional_session_filter(queryset, session_filter, filter_qd)

        self.session_filter_active = bool(session_filter)

        return queryset

    @property
    def filter_active(self):
        return any(
            self.request.GET.get(name) not in ("", None)
            for name in self.filterset.filters
        )

    def add_quick_filters_to_ctx(self, context):
        if self.quick_filters:
            context["quick_filters"] = [
                {
                    **quick_filter,
                    "url": f"{self.request.path}?{urlencode(quick_filter['lookups'])}",
                }
                for quick_filter in self.quick_filters.values()
            ]
        return context

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.add_quick_filters_to_ctx(context)

        context["model_name"] = self.model._meta.label
        context["filter_fields"] = get_filter_fields(self.model, self.visible_columns)
        context["title"] = self.title
        context['session_filter'] = self.session_filter_active
        context['filters_active'] = self.filter_active

        return context


class BulkUpdateView(FilteredTableView, FormMixin):
    permission_required = None  # Override in subclass - Mandatory
    model = None  # override in subclass - Mandatory
    template_name = None  # override in subclass - Mandatory
    universal_search_fields = None  # override in subclass - Mandatory
    success_view = None  # override in sublcass - Mandatory
    validator = None  # override in subclass for record specifid validator
    operation = None  # override in subclass or 'delete', 'update' or 'create_link',
    table_to_update = None  # table to update
    form_class = None  # override in subclass - Mandatory
    link_source_field = None
    link_target_field = None

    def get_template_names(self):
        return [self.template_name]

    def get_filtered_objects(self):
        if not hasattr(self, "filterset"):
            self.filterset = self.get_filterset(self.get_filterset_class())
        if not hasattr(self, "object_list"):
            self.object_list = self.filterset.qs
        return self.object_list

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # column chooser to get column list
        context["count"] = self.object_list.count()
        return context

    def get_success_url(self):
        base_url = reverse(self.success_view)
        query_params = self.request.GET.urlencode()
        return f"{base_url}?{query_params}"

    def validate_records(self, objects, updates):
        validator = getattr(self, "validator", None)
        for obj in objects:
            for field, value in updates.items():
                setattr(obj, field, value)
            obj.full_clean()
            if validator:
                self.validator(obj)

    def get_update_fields(self, cleaned_data):
        return {
            field: value
            for field, value in cleaned_data.items()
            if value not in [None, ""]
        }

    def persist_objects(self, qs, updates):
        self.table_to_update.objects.filter(pk__in=qs.values("pk")).update(**updates)

    def delete_objects(self, qs):
        return qs.delete()

    def bulk_link_objects(
        self,
        source_object,
        target_qs,
        link_model,
        source_field,
        target_field,
        extra_fields=None,
    ):
        if not target_qs.exists():
            return
        extra_fields = extra_fields or {}
        objects_to_create = [
            link_model(
                **{source_field: source_object, target_field: target}, **extra_fields
            )
            for target in target_qs
        ]
        link_model.objects.bulk_create(objects_to_create, ignore_conflicts=True)

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        qs = self.get_filtered_objects()

        if form.is_valid():
            if self.operation == "update":
                updates = self.get_update_fields(form.cleaned_data)
                if updates:
                    try:
                        self.validate_records(qs, updates)
                    except ValidationError as e:
                        form.add_error(None, e)
                        return self.form_invalid(form)

                    try:
                        self.persist_objects(qs, updates)
                    except ValidationError as e:
                        form.add_error(None, e)
                        return self.form_invalid(form)

                    messages.success(
                        request, f"{self.context_object_name} updated successfully."
                    )

                else:
                    messages.warning(
                        request,
                        f"No {self.context_object_name} were provided to update.",
                    )

            if self.operation == "create_link":
                self.bulk_link_objects(
                    source_object=form.cleaned_data["source_object"],
                    target_qs=qs,
                    link_model=self.table_to_update,
                    source_field=self.link_source_field,
                    target_field=self.link_target_field,
                )

            if self.operation == "delete":
                try:
                    self.delete_objects(qs)
                except ValidationError as e:
                    form.add_error(None, e)
                    return self.form_invalid(form)
                except IntegrityError as e:
                    form.add_error(None, e)
                    return self.form_invalid(form)

            return HttpResponseClientRedirect(self.get_success_url())

        return self.form_invalid(form)


def apply_session_filter(queryset, session_filter, filter_qd):
    origin_model = apps.get_model(session_filter.get("origin_model"))
    filterset_class = dynamic_filterset_generator(
        origin_model,
        universal_search_fields=session_filter.get("universal_search"),
        active_filters=session_filter.get("active_filters"),
    )
    filter_params = session_filter.get("filter_params")
    field_name = session_filter.get("field_name")

    if filter_qd:
        filterset = filterset_class(
            data=filter_qd if filter_qd else None,
            queryset=origin_model.objects.all(),
        )
    data = filterset.qs

    # filter by selected checkbox
    selected_ids = next((x[1] for x in filter_params if "selected" in x[0]), None)
    if selected_ids:
        data = data.filter(pk__in=selected_ids)

    # Pass the cleaned GET data to the FilterSet
    # get the list of the current model's PK from the original model's filtered data
    field_filter = f"{field_name}__in"
    qs = queryset.filter(**{field_filter: Subquery(data.values(field_name))})

    return qs


# define table actions
ActionType = Literal["link", "bulk_htmx"]
@dataclass(frozen=True)
class TableAction:
    name: str
    url: str
    permission: str
    on_selectable_items: bool
    type: ActionType = "link"
    qp: str | None = None
    icon: str | None = None
    color: str | None = None



class RoutingViewMixin(View):
    origin_model = None
    universal_search_fields = None
    filter_fieldname = None
    redirect_url = None
    

    def get(self, request, *args, **kwargs):

        excluded = {
            "new_active_filter",
            "page",
            "csrfmiddlewaretoken",
            "universal_search",
            "sort",
            "app_view_name",
            "model_name",
        }

        request.session[str(self.redirect_url)] = {
            "origin_model": (
                f"{self.origin_model._meta.app_label}."
                f"{self.origin_model._meta.model_name}"
            ),
            "filter_params": list(request.GET.lists()),
            "universal_search": self.universal_search_fields,
            "active_filters": [
                key
                for key in request.GET
                if key not in excluded
            ],
            "field_name": self.filter_fieldname,
        }

        response = HttpResponse(status=200)
        
        response["HX-Redirect"] = self.redirect_url

        return response


# column chooser

class ColumnChooser(LoginRequiredMixin, TemplateView):
    template_name = 'django_filter_table/column_chooser.html'

    def get_success_url(self):
        url = self.request.POST.get("next")
        return url

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # get user's visible colums if exists
        user = self.request.user
        request_app_model = self.request.GET.get('appmodel')
        model_name = request_app_model.split('.')[1]

        # list available columns
        model = apps.get_model(request_app_model)
        if model:
            all_columns = [field for field in model._meta.get_fields() if field.concrete and not field.auto_created]

        UserProfiles = get_user_profile_model()
        profile = UserProfiles.objects.filter(user_id=user).first()
        available_columns = []
        if profile and model_name:
            visible_columns_names = profile.get_preference(model_name, 'visible_columns')
            all_column_names = [c.name for c in all_columns]
            visible_columns = []
            for col_name in visible_columns_names:
                if col_name in all_column_names:
                    visible_columns.append(all_columns[all_column_names.index(col_name)]) 


            if visible_columns:
                context['visible_columns'] = visible_columns
                available_columns = [f for f in all_columns if f not in visible_columns]

        context["available_columns"] = available_columns or all_columns

        context['request_model'] = model_name

        next_url = self.request.GET.get("next_path")
        query_params = self.request.GET.urlencode()
        context['next'] = f"{next_url}?{query_params}"
        return context

    def post(self, request, *args, **kwargs):
        request_model = request.POST.get('request_model')
        user_id = self.request.user
        UserProfiles = get_user_profile_model()
        profile, created = UserProfiles.objects.get_or_create(
            user_id=user_id, defaults={"table_settings": {}}
        )

        columns = request.POST.getlist('columns', None)
        if columns and profile:
            profile.set_preference(request_model, 'visible_columns', columns)
        return HttpResponseRedirect(self.get_success_url())


#htmx search


class HtmxPickerSearch(
    LoginRequiredMixin,
    ListView
):
    paginate_by = 20
    template_name = 'htmx_select/search_result.html'

    def dispatch(self, request, *args, **kwargs):
        self.field = self.get_field()
        self.picker_mode = self.get_picker_mode()
        self.model = self.get_options_data_source()


        return super().dispatch(request, *args, **kwargs)

    @cached_property
    def get_model(self):
        model_path = self.kwargs["modelpath"]
        try:
            app_label, model_name = model_path.split("__", 1)
            model = apps.get_model(app_label, model_name)
        except (ValueError, LookupError):
            raise Http404

        return model

    def get_field(self):
        fieldname = self.kwargs["fieldname"]
        model = self.get_model

        return model._meta.get_field(fieldname)

    def get_picker_mode(self):
        if self.field.primary_key:
            return "model"

        if self.field.remote_field:
            return "foreign_key"

        if self.field.choices:
            return "choices"

        if isinstance(self.field, CharField):
            return "values"

        if isinstance(self.field, DateField):
            return "date"

        raise Http404


    def get_options_data_source(self):
        if self.picker_mode != 'foreign_key':
            model = self.get_model

        else:
            model = self.field.remote_field.model

        picker = getattr(model, "htmx_picker", None)

        if not picker or not getattr(picker, "enabled", False):
            raise Http404

        return model

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

        return qs

    def get_choices(self):

        qs = self.field.choices

        q = self.request.GET.get("q", "").strip()

        if q:
            qs = [choice for choice in qs if str(q) in choice[1].lower()]


        return qs

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

        if self.picker_mode in ['foreign_key', 'model']:
            qs = self.apply_q_filter(qs)

        elif self.picker_mode == 'choices':
            qs = self.get_choices()

        elif self.picker_mode == 'values':
            qs =self.get_distinct_values(qs)

        elif self.picker_mode == 'date':
            qs =self.get_distinct_values(qs)

        else:
            raise Http404
        
        return qs


    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        fieldname =  self.request.GET.get('fieldname', None)
        context['fieldname'] = fieldname
        if fieldname:
            context['selected'] = self.request.GET.getlist(fieldname)

        context['multiple'] = self.request.GET.get('multiple', '').lower() == 'true'

        if self.picker_mode in ['foreign_key', 'model']:
            context['options'] = [
                {
                    'value': obj.pk,
                    'label': self.get_option_label(obj)
                }
                for obj in context['object_list'] 
            ]
        elif self.picker_mode == 'choices':
            context['options'] = [
                {
                    'value': obj[0],
                    'label': obj[1] 
                }
                for obj in context['object_list'] 
            ]

        elif self.picker_mode == 'values':
            context['options'] = [
                {
                    'value': value,
                    'label': str(value), 
                }
                for value in context['object_list'] 
            ]

        elif self.picker_mode == 'date':
            context['options'] = [
                {
                    'value': datetime.strftime(value, '%Y-%m-%d'),
                    'label': datetime.strftime(value, '%Y-%m-%d'), 
                }
                for value in context['object_list'] if value
            ]


        return context



