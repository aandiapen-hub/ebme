from django.contrib import messages
from django.db import transaction
from django.http import HttpResponse, HttpResponseRedirect
import json


from django.shortcuts import render
import ast
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    ListView,
    CreateView,
    UpdateView,
    DeleteView,
    DetailView,
)
from datetime import datetime
from documents.models import TblDocumentLinks
from model_information.views import BrandCreateView, CategoryCreateView, ModelUpdateView

from .models import (
    Tblassets,
    AssetView,
    JobView,
)

from .forms import AssetUpdateForm, AssetBulkUpdateForm

from utils.generic_views import BulkUpdateView

# import permissions
from django.contrib.auth.mixins import LoginRequiredMixin
from .mixins import CustomerAssetPermissionMixin

from utils.generic_views import FilteredTableView

UNIVERSAL_SEARCH_FIELDS = [
    "serialnumber__icontains",
    "assetid__icontains",
    "modelname__icontains",
    "brandname__icontains",
    "categoryname__icontains",
    "customerassetnumber__icontains",
]


class FilteredAssetTableView(
    LoginRequiredMixin, CustomerAssetPermissionMixin, FilteredTableView
):
    paginate_by = 25
    permission_required = "assets.view_assetview"
    table_class = None
    model = AssetView
    template_columns = {"open": "assets/tables/open.html"}
    template_name = "assets/assetview_filter.html"
    universal_search_fields = UNIVERSAL_SEARCH_FIELDS
    default_columns = [
        "assetid",
        "brandid",
        "modelid",
        "categoryid",
        "customerid",
        "ppm_compliance",
    ]
    bulk_actions = {
        "bulk_update": {
            "url": reverse_lazy("assets:bulk_update_assets"),
            "permission": "assets.bulk_change_assets",
            "name": "Update",
        },
        "bulk_link_document": {
            "url": reverse_lazy("documents:bulk_link_to_assets"),
            "permission": "documents.bulk_create_links",
            "name": "Link Document",
        },
    }


class Asset(
    LoginRequiredMixin,
    CustomerAssetPermissionMixin,
    DetailView,
):
    model = AssetView
    template_name = "assets/assetview.html"
    context_object_name = "asset"
    permission_required = "assets.view_assetview"


class AssetUpdateView(
    LoginRequiredMixin,
    CustomerAssetPermissionMixin,
    UpdateView,
):
    model = Tblassets
    form_class = AssetUpdateForm
    template_name = "assets/update_form.html"

    permission_required = "assets.change_tblassets"

    def get_success_url(self):
        # Use self.object to access the updated object
        return reverse("assets:view_asset", kwargs={"pk": self.object.assetid})


class AssetDeleteView(
    LoginRequiredMixin,
    CustomerAssetPermissionMixin,
    DeleteView,
):
    """
    Handles the deletion of assets. Ensures the user has the required
    permissions and redirects to the asset list view upon successful deletion.
    """

    model = Tblassets
    success_url = reverse_lazy("assets:assets_list")
    template_name = "assets/partials/delete_modal.html"
    permission_required = "assets.delete_tblassets"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["view_type"] = "delete"
        context["title"] = (
            f"Delete Job: {Tblassets.objects.get(pk=self.kwargs.get('pk'))}"
        )
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        try:
            with transaction.atomic():
                TblDocumentLinks.delete_link_documents(self.object)
                self.object.delete()
            response = HttpResponse(status=204)
            response["HX-Redirect"] = self.success_url
            return response
        except Exception as e:
            messages.error(
                self.request,
                f"An error occurred while deleting the Asset. Error details: {str(e)}",
            )
            return self.render_to_response(self.get_context_data())


class AssetCreateView(LoginRequiredMixin, CustomerAssetPermissionMixin, CreateView):
    model = Tblassets
    form_class = AssetUpdateForm
    template_name = "assets/create_form.html"
    permission_required = "assets.add_tblassets"

    def get_success_url(self):
        return reverse("assets:view_asset", kwargs={"pk": self.object.assetid})

    def get(self, request, *args, **kwargs):
        if request.htmx:
            payload = request.GET.get("payload")
            if payload:
                return self.update_form()
        return super().get(request, *args, **kwargs)

    def update_form(self):
        form_data = self.request.GET.dict()
        payload = json.loads(self.request.GET.get("payload", None))
        payload = json.loads(self.request.GET.get("payload", None))
        if payload is not None:
            for field, value in payload.items():
                if field == "prod_date":
                    form_data[field] = datetime.strptime(value, "%y%m%d").date()
                else:
                    form_data[field] = value

        form = self.form_class(form_data)
        form.is_valid()
        self.object = None

        context = self.get_context_data(form=form)
        return self.render_to_response(context)

    def get_initial(self):
        initial = super().get_initial()
        payload = json.loads(self.request.GET.get("payload", None))
        if payload is not None:
            for field, value in payload.items():
                if field == "prod_date":
                    initial[field] = datetime.strptime(value, "%y%m%d").date()
                else:
                    initial[field] = value
        return initial


class AssetJobsListView(
    LoginRequiredMixin,
    CustomerAssetPermissionMixin,
    ListView,
):
    model = AssetView
    template_name = "assets/partials/job_summary.html"
    context_object_name = "jobs"

    permission_required = "assets.view_assetview"

    def get_queryset(self):
        # Get assetid from URL parameters
        asset_id = self.kwargs.get("assetid")
        if not asset_id:
            return (
                JobView.objects.none()
            )  # Return an empty queryset if assetid is missing

        try:
            # Retrieve the asset object
            asset = super().get_queryset().get(assetid=asset_id)
        except AssetView.DoesNotExist:
            return (
                JobView.objects.none()
            )  # Return an empty queryset if no asset is found

        # Filter jobs by the asset ID
        return JobView.objects.filter(assetid=asset.assetid).order_by("-startdate")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["open_jobs"] = context["jobs"].filter(jobstatusid__in=[0, 2, 3, 5])
        return context


class AssetBulkUpdateView(BulkUpdateView, CustomerAssetPermissionMixin):
    model = AssetView
    permission_required = "assets.change_tblassets"
    template_name = "assets/bulk_update.html"
    form_class = AssetBulkUpdateForm
    universal_search_fields = UNIVERSAL_SEARCH_FIELDS
    success_view = "assets:assets_list"
    operation = "update"
    table_to_update = Tblassets


class QuickBrandCreateView(BrandCreateView):
    def form_valid(self, form):
        self.object = form.save()
        context = {
            "data": {
                "brand": {
                    "brandname": self.object.brandname,
                    "brandid": self.object.pk,
                }
            }
        }

        response = render(
            self.request, "model_information/partials/brand_set_select.html", context
        )
        response["HX-Retarget"] = "#brands_list"
        response["HX-Reswap"] = "beforeend"
        return response


class QuickCategoryCreateView(CategoryCreateView):
    def form_valid(self, form):
        self.object = form.save()
        context = {
            "data": {
                "category": {
                    "categoryname": self.object.categoryname,
                    "categoryid": self.object.pk,
                }
            }
        }

        response = render(
            self.request, "model_information/partials/category_set_select.html", context
        )
        response["HX-Retarget"] = "#categories_list"

        response["HX-Reswap"] = "beforeend"
        return response


class QuickModelGtinUpdate(ModelUpdateView):
    def get_success_url(self, **kwargs):
        temp_document_group = self.request.POST.get("temp_document_group")

        return reverse(
            "assets:barcode_output", kwargs={"temp_file_group": temp_document_group}
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        temp_document_group = self.request.GET.get("temp_document_group")
        if temp_document_group:
            context["temp_document_group"] = temp_document_group
        return context
