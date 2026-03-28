from django.contrib import messages
from django.db import transaction
from django.http import HttpResponse, HttpResponseRedirect

from django_htmx.http import HttpResponseClientRedirect

from django.shortcuts import render
import ast
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    ListView,
    CreateView,
    UpdateView,
    DeleteView,
    DetailView,
    FormView,
)
from datetime import datetime
from documents.models import TblDocumentLinks, TemporaryUpload
from model_information.views import (
    BrandCreateView,
    CategoryCreateView,
    ModelUpdateView
)

from .models import (
    Tblassets,
    AssetView,
    Tblmodel,
    Tblcategories,
    JobView,
    Tblbrands,
)
from documents.utils import save_extraction_results, get_extraction_results


from .forms import (
    AssetUpdateForm,
    AssetBulkUpdateForm,
    AssetCreateFromFileForm
)

from documents.services.gs1_parser import process_barcode

from django.db.models import Q

# Universal search filter imports
import operator
from functools import reduce

from utils.generic_views import BulkUpdateView

from .utils.barcode_reader import scan_barcode
from .utils.barcode_reader_ai import barcode_reader_ai

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
        'assetid',
        'brandid',
        'modelid',
        'categoryid',
        'customerid',
        'ppm_compliance',
    ]

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
                f"An error occurred while deleting the Asset. Error details: {
                    str(e)}",
            )
            return self.render_to_response(self.get_context_data())


class AssetCreateView(
    LoginRequiredMixin,
    CustomerAssetPermissionMixin,
    CreateView
):
    model = Tblassets
    form_class = AssetUpdateForm
    template_name = "assets/create_form.html"
    permission_required = "assets.add_tblassets"

    def get_success_url(self):
        return reverse("assets:view_asset", kwargs={"pk": self.object.assetid})

    def get(self, request, *args, **kwargs):
        if request.htmx:
            barcode = request.GET.get('barcode')
            if barcode:
                return self.resolve_barcode()
        return super().get(request, *args, **kwargs)

    def resolve_barcode(self):
        form_data = self.request.GET.dict()
        decoded_info = process_barcode(scanned_code=self.request.GET.get('barcode'))
        gs1_data = decoded_info.get('gs1', None)
        decoded_model = decoded_info.get('model')

        if gs1_data:
            gs1_to_asset_map = {
                'PROD DATE': 'prod_date',
                'SERIAL': 'serialnumber',
                'ASSET_NO': 'customerassetnumber',
            }

            for ai, field in gs1_to_asset_map.items():
                value = gs1_data.get(ai)
                if value and ai == 'PROD DATE':
                    value = datetime.strptime(value, "%y%m%d").date()

                if value:
                    form_data[field] = value

        if decoded_model and form_data.get('modelid') is None:
            form_data['modelid'] = decoded_model

        form = self.form_class(form_data)
        form.is_valid()
        self.object = None

        context = self.get_context_data(form=form)
        return self.render_to_response(context)


    def get_initial(self):
        initial = super().get_initial()
        modelid = self.request.GET.get('modelid', None)

        if modelid:
            initial['modelid'] = modelid

        gs1_data_string = self.request.GET.get('gs1_data')
        if gs1_data_string:
            gs1_data = ast.literal_eval(gs1_data_string)
            if gs1_data:
                gs1_to_asset_map = {
                    'PROD DATE': 'prod_date',
                    'SERIAL': 'serialnumber',
                    'ASSET_NO':''
                }
                for ai, asset_field in gs1_to_asset_map.items():
                    value = gs1_data.get(ai, None)
                    if value and ai == "PROD DATE":
                        value = datetime.strptime(value, "%y%m%d").date()
                    initial[asset_field] = value
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
        return JobView.objects.filter(
            assetid=asset.assetid
        ).order_by("-startdate")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["open_jobs"] = context["jobs"].filter(
            jobstatusid__in=[0, 2, 3, 5])
        return context


class AssetBulkUpdateView(BulkUpdateView, CustomerAssetPermissionMixin):
    model = AssetView
    permission_required = "assets.change_tblassets"
    template_name = 'assets/bulk_update.html'
    form_class = AssetBulkUpdateForm
    universal_search_fields = UNIVERSAL_SEARCH_FIELDS

    def get_template_names(self):
        return ['assets/bulk_update.html']

    def get_success_url(self):
        base_url = reverse('assets:assets_list')
        query_params = self.request.GET.urlencode()
        return f"{base_url}?{query_params}"

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        qs = self.get_filtered_objects()

        if form.is_valid():
            print('for is valid')
            updates = {
                field: value
                for field, value in form.cleaned_data.items()
                if value not in [None, ""]
            }

            if updates:
                Tblassets.objects.filter(pk__in=qs.values("pk")).update(**updates)
                messages.success(
                    request, f"{self.context_object_name} updated successfully."
                )

            else:
                messages.warning(
                    request, f"No {self.context_object_name} were provided to update."
                )

            return HttpResponseClientRedirect(self.get_success_url())

        print('form is invalid')
        return self.form_invalid(form)

class BarCodeReader(
    LoginRequiredMixin,
    CustomerAssetPermissionMixin,
    FormView
):
    form_class = AssetCreateFromFileForm
    permission_required = "assets.add_tblassets"
    template_name = "documents/temp_files_list.html"

    def get_success_url(self, **kwargs):
        return reverse(
            "assets:barcode_output",
            kwargs={"temp_file_group": self.group}
        )

    def form_valid(self, form):
        self.group = self.kwargs.get("temp_file_group")
        use_ai = self.request.GET.get("use_ai")

        files = TemporaryUpload.objects.filter(
            user=self.request.user, group=self.group)

        for file in files:
            if file.mime_type not in ["image/jpeg", "image/png", "image/jpg"]:
                messages.warning(self.request, "Incorrect file type.")
                return render(
                    self.request,
                    "partials/messages.html",
                    context=None
                )

        if use_ai:
            output = barcode_reader_ai(files)
        else:
            output = scan_barcode(files)

        if len(output) == 0:
            messages.warning(
                self.request,
                """No barcodes recognised from these images.
                Upload more images or use AI to extract more information.""",
            )
            return render(self.request, "partials/messages.html", context=None)

        cleaned_output = self.clean_parsed_data(output)
        save_extraction_results(
            user_id=self.request.user,
            group=self.group,
            results=cleaned_output,
            hours=1
        )

        response = HttpResponse()
        response["HX-Redirect"] = self.get_success_url()
        return response

    def clean_parsed_data(self, raw):
        # Example sanitization or remapping
        return {
            "gtin": raw.get("GTIN", ""),
            "serialnumber": raw.get("SERIAL", ""),
            "prod_date": raw.get("PROD_DATE", ""),
            "customerassetnumber": raw.get("ASSET_NO", ""),
            "modelname": raw.get("model_name", ""),
            "suggested_brands": raw.get("brands"),
            "suggested_categories": raw.get("categories"),
            "document_type": "device_id",
        }


class BarcodeOutput(
    LoginRequiredMixin,
    CustomerAssetPermissionMixin,
    CreateView
):
    model = None  # will be set dynamically
    form_class = None  # will be set dynamically
    template_name = "assets/partials/barcode_scanner_output.html"
    permission_required = "assets.add_tblassets"

    def dispatch(self, request, *args, **kwargs):
        self.group = self.kwargs.get("temp_file_group")
        self.extracted_data = get_extraction_results(
            user_id=request.user, group=self.group
        )

        if self.extracted_data:
            """if a serial number if recognised in the
            database, the page is redirected to the asset's page"""
            serialnumber = self.extracted_data.get("serialnumber", None)
            if serialnumber:
                asset = Tblassets.objects.filter(
                    serialnumber__icontains=serialnumber
                ).first()
                if asset:
                    if request.htmx:
                        response = HttpResponse(status=200)
                        response["HX-Redirect"] = reverse(
                            "assets:view_asset", kwargs={"pk": asset}
                        )
                        return response
                    return HttpResponseRedirect(
                        reverse("assets:view_asset", kwargs={"pk": asset})
                    )

            gtin = self.extracted_data.get("gtin", None)
            if gtin:
                model = Tblmodel.objects.filter(gtin=gtin)
                if model.exists():
                    self.extracted_data["modelid"] = model[0].modelid
                    self.extracted_data["form_type"] = "asset"
                else:
                    self.extracted_data["modelid"] = None
                    self.extracted_data["form_type"] = "model"

            else:
                self.extracted_data["form_type"] = "asset"

            save_extraction_results(
                user_id=self.request.user,
                group=self.group,
                results=self.extracted_data,
                hours=1,
            )

        return super().dispatch(request, *args, **kwargs)

    def get_form_class(self):
        form_type = self.extracted_data["form_type"]

        if form_type == "model":
            self.model = Tblmodel
            from model_information.forms import ModelQuickCreateForm

            return ModelQuickCreateForm
        else:
            self.model = Tblassets
            return AssetUpdateForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # find and return brands that match suggested brands
        suggested_brands = self.extracted_data.get("suggested_brands", None)
        if suggested_brands:
            suggested_brands = [
                word
                for line in suggested_brands
                for word in line.split()
                if len(word) > 2
            ]
            brand_query = reduce(
                operator.or_,
                (Q(brandname__icontains=brandname)
                 for brandname in suggested_brands),
            )
            context["existing_brands"] = Tblbrands.objects.filter(brand_query)

        # find and return brands that match suggested categories
        suggested_categories = self.extracted_data.get(
            "suggested_categories", None)

        if suggested_categories:
            suggested_categories = [
                word
                for line in suggested_categories
                for word in line.split()
                if len(word) > 2
            ]
            category_query = reduce(
                operator.or_,
                (
                    Q(categoryname__icontains=categoryname)
                    for categoryname in suggested_categories
                ),
            )
            context["existing_categories"] = Tblcategories.objects.filter(
                category_query
            )

        form_type = self.extracted_data["form_type"]
        if "model" in form_type:
            context["form_title"] = "Create Model"
        else:
            context["form_title"] = "Create Asset"

        context["temp_document_group"] = self.group

        return context

    def get_initial(self):
        initial = super().get_initial()
        initial.update(self.extracted_data)
        return initial

    def form_valid(self, form):
        self.object = form.save()
        form_type = self.extracted_data["form_type"]

        if form_type == "model":
            self.extracted_data["modelid"] = self.object.modelid
            save_extraction_results(
                user_id=self.request.user,
                group=self.group,
                results=self.extracted_data,
                hours=1,
            )

            return HttpResponseRedirect(
                reverse("assets:barcode_output", kwargs={
                        "temp_file_group": self.group})
            )

        else:
            # delete related temporary pictures and cache
            images = TemporaryUpload.objects.filter(
                user=self.request.user, group=self.group
            )
            for file in images:
                file.delete()

            return HttpResponseRedirect(
                reverse("assets:view_asset", kwargs={"pk": self.object.pk})
            )


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
            self.request,
            "model_information/partials/brand_set_select.html",
            context
        )
        response["HX-Retarget"] = (
            "#brands_list"
        )
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
            self.request,
            "model_information/partials/category_set_select.html",
            context
        )
        response["HX-Retarget"] = "#categories_list"

        response["HX-Reswap"] = "beforeend"
        return response


class QuickModelGtinUpdate(ModelUpdateView):
    def get_success_url(self, **kwargs):
        temp_document_group = self.request.POST.get("temp_document_group")

        return reverse(
            "assets:barcode_output",
            kwargs={"temp_file_group": temp_document_group}
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        temp_document_group = self.request.GET.get("temp_document_group")
        if temp_document_group:
            context["temp_document_group"] = temp_document_group
        return context
