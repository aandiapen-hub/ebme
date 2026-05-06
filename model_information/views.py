from django.db import transaction, IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse_lazy, reverse
import json

# import models
from assets.models import Tblbrands, Tblmodel, Tblcategories, Tblcheckslists
from documents.models import TempUploadGroup

from django.views.generic import (
    UpdateView,
    CreateView,
    DeleteView,
    ListView,
    DetailView,
)

from documents.services.document_parser import temp_group_resolver

# import django-tables2
from django_tables2 import tables, SingleTableMixin, columns

from documents.models import TblDocumentLinks
from utils.generic_views import BulkUpdateView

# import forms
from .forms import (
    ModelQuickCreateForm,
    BrandBulkUpdateForm,
    ModelBulkUpdateForm,
)

# import permissions mixins
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin


from utils.generic_views import FilteredTableView


class CreateWithPayloadView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    success_url_app_view = None  # override in child class

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        processed_payload = json.loads(self.request.GET.get("payload", "{}"))

        if processed_payload is not None:
            context["payload"] = self.request.GET.get("payload", "{}")
            context["processed_payload"] = processed_payload

            brandid_list = processed_payload.get("brandid", None)
            if brandid_list is not None:
                context["existing_brands"] = Tblbrands.objects.filter(
                    pk__in=brandid_list
                )
            categoryid_list = processed_payload.get("categoryid", None)
            if categoryid_list is not None:
                context["existing_categories"] = Tblcategories.objects.filter(
                    pk__in=categoryid_list
                )

            temp_group = processed_payload.get("temp_group_pk", None)
            context["temp_group"] = TempUploadGroup.objects.filter(
                pk=temp_group
            ).first()
        return context

    def form_valid(self, form):
        try:
            with transaction.atomic():
                response = super().form_valid(form)
                self.temp_group_pk = self.request.POST.get("temp_group_pk", None)
                if self.temp_group_pk:
                    temp_group_resolver(self.temp_group_pk)

                return response
        except IntegrityError as e:
            form.add_error(None, e)
            return super.form_invalid(form)

    def get_initial(self):
        initial = super().get_initial()
        # update initial based on direct query params matching form fields
        initial.update(self.request.GET.items())

        # update initial based on specifid payload in query params
        payload = json.loads(self.request.GET.get("payload", "{}"))
        for key, value in payload.items():
            if isinstance(value, list) and value:
                initial[key] = value[0]
            else:
                initial[key] = value
        return initial

    def get_success_url(self):
        temp_group_pk = self.request.POST.get("temp_group_pk", None)
        if temp_group_pk:
            return reverse("documents:temp_group", kwargs={"pk": temp_group_pk})

        return reverse(self.success_url_app_view, kwargs={"pk": self.object.pk})


# brand views
class FilteredBrandTableView(
    LoginRequiredMixin, PermissionRequiredMixin, FilteredTableView
):
    paginate_by = 25
    permission_required = "assets.view_tblbrands"
    table_class = None
    model = Tblbrands
    template_columns = {
        "actions": "model_information/tables/brandlist_buttons.html",
        "open": "model_information/tables/brand_open.html",
    }
    template_name = "model_information/brandlist.html"
    universal_search_fields = ["brandname__icontains"]
    default_columns = ["brandname"]


class BrandUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Tblbrands
    fields = "__all__"
    template_name = "model_information/partials/modal.html"
    success_url = reverse_lazy("model_information:brandlist")
    permission_required = "assets.change_tblbrands"

    def form_valid(self, form):
        self.object = form.save()
        if self.request.htmx:
            # Return empty 204 response so HTMX knows it's successful
            response = HttpResponse("", status=204)
            response["HX-Trigger"] = "closeModal"
            return response
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Update Brand"
        context["view_type"] = "update"
        return context


class BrandBulkUpdateView(BulkUpdateView):
    context_object_name = "brand"
    model = Tblbrands
    permission_required = "assets.change_tblbrands"
    form_class = BrandBulkUpdateForm
    summary_field_names = None
    success_url = reverse_lazy("model_information:brandlist")


class BrandCreateView(CreateWithPayloadView):
    model = Tblbrands
    fields = "__all__"
    template_name = "model_information/partials/brand_create.html"
    permission_required = "assets.add_tblbrands"
    success_url_app_view = "model_information:brand_detail"


class BrandDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Tblbrands
    context_object_name = "brand"
    template_name = "model_information/partials/brand_detail.html"
    permission_required = "assets.view_tblbrands"


class BrandDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Tblbrands
    template_name = "model_information/partials/delete_modal.html"
    permission_required = "assets.delete_tblbrands"
    success_url = reverse_lazy("model_information:brandlist")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Delete Brand"
        context["brand"] = Tblbrands.objects.get(pk=self.kwargs.get("pk"))

        context["view_type"] = "delete"
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        try:
            with transaction.atomic():
                TblDocumentLinks.delete_link_documents(self.object)
                self.object.delete()
            response = HttpResponse("", status=204)
            # Optional: prevent swapping any content
            response["HX-Trigger"] = "closeModal"
            return response

        except Exception as e:
            # Return an error message as plain text (not JSON)
            context = self.get_context_data()
            context["error_message"] = (
                f"An error occurred while deleting the brand. Error Details: {str(e)}"
            )
            return self.render_to_response(context)


# model views
class FilteredModelTableView(
    LoginRequiredMixin, PermissionRequiredMixin, FilteredTableView
):
    model = Tblmodel
    paginate_by = 25
    permission_required = "assets.view_tblmodel"
    template_name = "model_information/modellist.html"
    universal_search_fields = ["modelname__icontains"]
    template_columns = {"open": "model_information/tables/model_open.html"}


class ModelUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Tblmodel
    fields = "__all__"
    template_name = "model_information/partials/model_update.html"
    permission_required = "assets.change_tblmodel"

    def get_success_url(self):
        return reverse(
            "model_information:model_view", kwargs={"pk": self.object.modelid}
        )

    def get_initial(self):
        initial = super().get_initial()
        # Add query parameters to initial
        gtin = self.request.GET.get("gtin")
        if gtin:
            initial["gtin"] = gtin
        return initial


class ModelBulkUpdateView(BulkUpdateView):
    context_object_name = "model"
    model = Tblmodel
    permission_required = "assets.change_tblmodel"
    form_class = ModelBulkUpdateForm
    summary_field_names = None
    success_url = reverse_lazy("model_information:modellist")


class ModelCreateView(CreateWithPayloadView):
    model = Tblmodel
    form_class = ModelQuickCreateForm
    template_name = "model_information/partials/model_create.html"
    permission_required = "assets.add_tblmodel"
    success_url_app_view = "model_information:model_view"


class ExistingModelListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Tblmodel
    permission_required = "assets.view_tblmodel"
    template_name = "model_information/partials/existing_model_list.html"
    context_object_name = "models"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["temp_document_group"] = self.request.GET.get("temp_document_group")
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        modelname = self.request.GET.get("modelname")

        if modelname:
            queryset = queryset.filter(modelname__icontains=modelname).exclude(
                gtin__isnull=False
            )[:10]
            return queryset


class ModelDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Tblmodel
    template_name = "model_information/partials/modal.html"
    permission_required = "assets.delete_tblmodel"
    success_url = reverse_lazy("model_information:modellist")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Delete Model"
        context["model"] = Tblmodel.objects.get(pk=self.kwargs.get("pk"))
        context["view_type"] = "delete"
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        try:
            with transaction.atomic():
                TblDocumentLinks.delete_link_documents(self.object)
                self.object.delete()
            if self.request.htmx:
                response = HttpResponse()
                response["HX-Redirect"] = success_url
                return response
            return HttpResponseRedirect(success_url)

        except Exception as e:
            # Return an error message as plain text (not JSON)
            context = self.get_context_data()
            context["error_message"] = (
                f"An error occurred while deleting the model. Error Details: {str(e)}"
            )
            return self.render_to_response(context)


class ModelDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Tblmodel
    template_name = "model_information/model_view.html"
    fields = "__all__"
    permission_required = "assets.view_tblmodel"


# category views
class FilteredCategoryTableView(
    LoginRequiredMixin, PermissionRequiredMixin, FilteredTableView
):
    model = Tblcategories
    paginate_by = 25
    permission_required = "assets.view_tblcategories"
    template_name = "model_information/categorylist.html"
    universal_search_fields = ["categoryname__icontains"]
    template_columns = {
        "actions": "model_information/tables/categorylist_buttons.html",
        "open": "model_information/tables/category_open.html",
    }
    default_columns = ["categoryid", "categoryname"]


class CategoryUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Tblcategories
    fields = "__all__"
    template_name = "model_information/partials/modal.html"
    success_url = reverse_lazy("model_information:categorylist")
    permission_required = "assets.change_tblcategories"

    def form_valid(self, form):
        self.object = form.save()
        if self.request.htmx:
            response = HttpResponse("", status=204)
            response["HX-Trigger"] = "closeModal"
            return response
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Update Category"
        context["view_type"] = "update"
        return context


class CategoryCreateView(CreateWithPayloadView):
    model = Tblcategories
    fields = "__all__"
    template_name = "model_information/partials/create_category.html"
    success_url = reverse_lazy("model_information:categorylist")
    success_url_app_view = "model_information:category_detail"


class CategoryDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Tblcategories
    template_name = "model_information/partials/category_detail.html"
    context_object_name = "category"
    permission_required = "assets.view_tblcategories"


class CategoryDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Tblcategories
    template_name = "model_information/partials/delete_modal.html"
    permission_required = "assets.delete_tblcategories"
    success_url = reverse_lazy("model_information:categorylist")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Delete Category"
        context["view_type"] = "delete"
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        try:
            with transaction.atomic():
                TblDocumentLinks.delete_link_documents(self.object)
                self.object.delete()
            return HttpResponseRedirect(success_url)

        except Exception as e:
            # Return an error message as plain text (not JSON)
            context = self.get_context_data()
            context["error_message"] = (
                f"An error occurred while deleting the category. Error Details: {str(e)}"
            )
            return self.render_to_response(context)


class ChecklistsTable(tables.Table):
    Actions = columns.TemplateColumn(
        template_name="model_information/tables/checklist_buttons.html",  # Path to your button template
        verbose_name="Actions",
        orderable=False,
    )  # Prevent sorting on this column

    class Meta:
        model = Tblcheckslists
        attrs = {
            "class": "table table-hover table-bordered table-striped  ",
            "thead": {
                "class": "table-bordered align-middle",
            },
        }
        template_name = "tables/tables2_with_filter.html"
        fields = ("testid", "modelid", "testname", "test_description")


class ChecklistsTableView(
    LoginRequiredMixin, PermissionRequiredMixin, SingleTableMixin, ListView
):
    model = Tblcheckslists
    table_class = ChecklistsTable
    template_name = "model_information/partials/checklist.html"
    paginate_by = 20
    permission_required = "assets.view_tblcheckslists"

    def get_queryset(self):
        queryset = super().get_queryset()
        modelid = self.request.GET.get("modelid")
        if modelid:
            queryset = queryset.filter(modelid=int(modelid))
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        modelid = self.request.GET.get("modelid")
        if modelid:
            context["model"] = Tblmodel.objects.get(
                modelid=self.request.GET.get("modelid")
            )
        return context


class CheckUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Tblcheckslists
    fields = "__all__"
    template_name = "model_information/partials/modal.html"
    success_url = reverse_lazy("model_information:checklist")
    permission_required = "assets.change_tblcheckslists"

    def form_valid(self, form):
        self.object = form.save()
        if self.request.htmx:
            # Return empty 204 response so HTMX knows it's successful
            return HttpResponse(status=204)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Update Check"
        context["view_type"] = "update"
        return context


class CheckDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Tblcheckslists
    template_name = "model_information/partials/modal.html"
    permission_required = "assets.delete_tblcheckslists"
    success_url = reverse_lazy("model_information:checklist")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Delete Test"
        context["check"] = Tblcheckslists.objects.get(pk=self.kwargs.get("pk"))

        context["view_type"] = "delete"
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        try:
            with transaction.atomic():
                TblDocumentLinks.delete_link_documents(self.object)
                self.object.delete()
            if self.request.htmx:
                return HttpResponse(status=204)
            return HttpResponseRedirect(success_url)

        except Exception as e:
            # Return an error message as plain text (not JSON)
            context = self.get_context_data()
            context["error_message"] = (
                f"An error occurred while deleting the test. Error Details: {str(e)}"
            )
            return self.render_to_response(context)


class CheckCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Tblcheckslists
    fields = "__all__"
    template_name = "model_information/partials/modal.html"
    permission_required = "assets.add_tblcheckslists"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["modelid"] = self.request.GET.get("modelid")
        context["title"] = "Create New Test"
        context["view_type"] = "create"
        return context

    def get_initial(self):
        """Set a default value for the 'assetid' field using a query parameter"""
        initial = super().get_initial()
        initial["modelid"] = self.request.GET.get("modelid")  # Set default
        return initial

    def get_success_url(self):
        return reverse("model_information:checklist")

    def form_valid(self, form):
        self.object = form.save()
        if self.request.htmx:
            # Return empty 204 response so HTMX knows it's successful
            return HttpResponse(status=204)
        return super().form_valid(form)
