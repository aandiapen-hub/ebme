from django.contrib import messages
from django.db import transaction
from assets.services.oustanding_tasks import get_equipment_tasks
from assets.services.sofware_service import apply_software_change
from assets.services.configuration_service import apply_configuration_change
from cap_project.models import CommissionRequest
from documents.mixins import TempUploadMixin
from django.http import HttpResponse, HttpResponseRedirect
from documents.services.documents import delete_object_document_links
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView,
    UpdateView,
    DeleteView,
    DetailView,
    FormView,
)
from datetime import datetime

from model_information.models import EquipmentConfiguration, EquipmentSoftware

from .models import (
    Tblassets,
    AssetView,
)

from documents.services.process_document import quick_barcode_processor
from .forms import(
        AssetUpdateForm,
        AssetBulkUpdateForm,
        SetEquipmentSoftwareForm,
        SetEquipmentConfigurationForm,
)

from utils.generic_views import BulkUpdateView

# import permissions
from django.contrib.auth.mixins import LoginRequiredMixin
from .mixins import CustomerAssetPermissionMixin

from utils.generic_views import FilteredTableView

UNIVERSAL_SEARCH_FIELDS = [
    "serialnumber__icontains",
    "assetid__pk__icontains",
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


class AssetDetailView(
    LoginRequiredMixin,
    CustomerAssetPermissionMixin,
    DetailView,
):
    model = AssetView
    template_name = "assets/assetview.html"
    context_object_name = "asset"
    permission_required = "assets.view_assetview"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["open_jobs"] = self.object.jobs.filter(jobstatusid__in=[0, 2, 3, 5])
        context['tasks'] = get_equipment_tasks(self.object)
        context['required_config'] = EquipmentConfiguration.objects.for_asset(self.object)
        
        return context


class AssetUpdateView(
    LoginRequiredMixin,
    CustomerAssetPermissionMixin,
    TempUploadMixin,
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
                delete_object_document_links(self.object)
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


class AssetCreateView(
    LoginRequiredMixin, CustomerAssetPermissionMixin, TempUploadMixin, CreateView
):
    model = Tblassets
    form_class = AssetUpdateForm
    template_name = "assets/create_form.html"
    permission_required = "assets.add_tblassets"

    def get_success_url(self):
        return reverse("assets:view_asset", kwargs={"pk": self.object.assetid})

    def get(self, request, *args, **kwargs):
        if request.htmx:
            barcode = request.GET.get("barcode")
            print('barcode', barcode)
            if barcode:
                resolved_data = quick_barcode_processor(barcode)
                print('resolved data received', resolved_data)
                return self.update_form(resolved_data)
        return super().get(request, *args, **kwargs)

    def update_form(self, resolved_data):
        form_data = self.request.GET.dict()
        asset_data = resolved_data.get('asset', None)
        if asset_data is not None:
            for field, value in asset_data.items():
                if field == "prod_date" and value is not None:
                    form_data[field] = datetime.strptime(value, "%y%m%d").date()
                elif value is not None:
                    form_data[field] = value

        form = self.form_class(form_data)
        form.is_valid()
        self.object = None

        context = self.get_context_data(form=form)
        return self.render_to_response(context)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['com_requests'] = CommissionRequest.objects.all()
        return context

class SetEquipmentSoftware(FormView):
    template_name = 'assets/set_equipment_software.html'
    form_class = SetEquipmentSoftwareForm
    
    def get_success_url(self):
        equipment = self.object.equipment.pk
        print(self.object, self.object.equipment.pk)
        return reverse('assets:view_asset', kwargs={'pk':equipment})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        equipmentid = self.request.GET.get('equipmentid', None)
        if equipmentid:
            kwargs['equipment_id'] = equipmentid 

        return kwargs
        

    def form_valid(self, form):
        software_id = form.cleaned_data['software']
        equipment_id = form.cleaned_data['equipment']
        self.object = apply_software_change(
            equipment=equipment_id,
            software=software_id,
            user=self.request.user 
        )
        
        response = HttpResponseRedirect(self.get_success_url())
        return response

class RemoveEquipmentSoftware(DeleteView):
    model = EquipmentSoftware
    template_name = 'assets/remove_equipment_software.html'
    fields = '__all__'
    context_object_name = 'software_equipment'

    def get_success_url(self):
        equipment_id = self.object.equipment.pk
        return reverse('assets:view_asset', kwargs={'pk':equipment_id})

class SetEquipmentConfiguration(FormView):
    template_name = 'assets/set_equipment_configuration.html'
    form_class = SetEquipmentConfigurationForm
    
    def get_success_url(self):
        equipment = self.object.equipment.pk
        return reverse('assets:view_asset', kwargs={'pk':equipment})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        equipmentid = self.request.GET.get('equipmentid', None)
        if equipmentid:
            kwargs['equipment_id'] = equipmentid 

        return kwargs
        

    def form_valid(self, form):
        configuration_id = form.cleaned_data['configuration']
        equipment_id = form.cleaned_data['equipment']
        self.object = apply_configuration_change(
            equipment=equipment_id,
            configuration=configuration_id,
        )
        
        response = HttpResponseRedirect(self.get_success_url())
        return response

class AssetBulkUpdateView(BulkUpdateView, CustomerAssetPermissionMixin):
    model = AssetView
    permission_required = "assets.change_tblassets"
    template_name = "assets/bulk_update.html"
    form_class = AssetBulkUpdateForm
    universal_search_fields = UNIVERSAL_SEARCH_FIELDS
    success_view = "assets:assets_list"
    operation = "update"
    table_to_update = Tblassets

