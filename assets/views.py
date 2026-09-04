from django.contrib import messages
from urllib.parse import urlencode
from functools import cached_property

from django.shortcuts import redirect
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

from model_information.models import EquipmentConfigurationLink, EquipmentSoftware

from .models import (
    Tblassets,
    AssetView,
    Tbljob,
    Tbljobstatus,
    Tbljobtypes,
    Tbltechnicianlist,
)


from documents.services.process_document import quick_barcode_processor
from .forms import (
    AssetUpdateForm,
    AssetBulkUpdateForm,
    SetEquipmentSoftwareForm,
    SetEquipmentConfigurationForm,
    ReplicateAssetForm,
)

# import permissions
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from .mixins import CustomerAssetPermissionMixin

from documents.models import TempUploadGroup, DocumentTypes

from django_filter_table.views import(
        FilteredTableView,
        RoutingViewMixin,
        BulkUpdateView,
        TableAction
)

UNIVERSAL_SEARCH_FIELDS = [
    "serialnumber__icontains",
    "assetid__icontains",
    "modelid__modelname__icontains",
    "brandid__brandname__icontains",
    "categoryid__categoryname__icontains",
    "customerassetnumber__icontains",
]


class FilteredAssetTableView(
    LoginRequiredMixin, CustomerAssetPermissionMixin, FilteredTableView
):
    title = 'Assets'
    permission_required = "assets.view_assetview"
    table_class = None
    open_column = 'assetid'
    model = AssetView
    universal_search_fields = UNIVERSAL_SEARCH_FIELDS
    default_columns = [
        "assetid",
        "serialnumber",
        "modelid",
        "brandid"
        "ppm_compliance",
    ]
    actions = [
        TableAction(
            name='Add',
            type='link',
            on_selectable_items = False, 
            url=reverse_lazy('assets:create_asset'),
            permission='assets.add_tblassets',
            icon='bi-plus',
            color='outline-secondary'
        ),
        TableAction(
            name="Update",
            type='bulk_htmx',
            on_selectable_items = True, 
            url=reverse_lazy("assets:bulk_update_assets"),
            permission="assets.bulk_change_assets",
            icon="bi-pencil",
            color='outline-secondary'
        ),
        TableAction(
            name='Link Document',
            type='bulk_htmx',
            on_selectable_items = True, 
            url=reverse_lazy("documents:bulk_link_to_assets"),
            permission="documents.bulk_create_links",
            icon="bi-file-earmark-plus",
            color='outline-secondary'
        ),
        TableAction(
            name="View All Jobs",
            type='htmx',
            on_selectable_items = True,
            url=reverse_lazy("assets:asset_to_job"),
            permission="assets.view_jobview",
            icon="",
            color='outline-secondary'
        ),
        TableAction(
            name="View most recent PPM",
            type='htmx',
            on_selectable_items = True,
            qp = urlencode({'additional_filter_options':'filter_latest_ppm'}),
            url=reverse_lazy("assets:asset_to_job"),
            permission="assets.view_jobview",
            icon="",
            color='outline-secondary'
        ),
    ]

class AssetToJobView(
    LoginRequiredMixin, PermissionRequiredMixin, RoutingViewMixin):
    permission_required = "assets.view_assetview"
    origin_model = AssetView
    universal_search_fields = UNIVERSAL_SEARCH_FIELDS
    filter_fieldname = 'assetid'
    redirect_url = reverse_lazy('jobs:jobs_list')

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
        context["open_jobs"] = self.object.asset.jobs.filter(
            jobstatusid__in=[0, 2, 3, 5]
        )
        context["tasks"] = get_equipment_tasks(self.object)

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
    success_url_app_view = "assets:view_asset"


    def form_valid(self, form):
        with transaction.atomic():
            # save document related records from TempUploadMixin
            self.object = form.save()
            self.after_save(form)
        return HttpResponseRedirect(self.get_success_url())


    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        if context.get("cancel_url", None) is None:
            context["cancel_url"] = reverse(
                "assets:view_asset", kwargs={"pk": self.object.pk}
            )

        return context


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
            if barcode:
                resolved_data = quick_barcode_processor(barcode)
                return self.update_form(resolved_data)
        return super().get(request, *args, **kwargs)

    def update_form(self, resolved_data):
        form_data = self.request.GET.dict()
        asset_data = resolved_data.get("asset", None)
        if asset_data is not None:
            for field, value in asset_data.items():
                if field == "prod_date" and value is not None:
                    form_data[field] = datetime.strptime(value, "%y%m%d").date()
                elif value is not None:
                    form_data[field] = value

        form = self.form_class(data=form_data, acceptance=True)
        form.is_valid()
        self.object = None

        context = self.get_context_data(form=form)
        return self.render_to_response(context)

    def get_form_kwargs(self, form_class=None):
        kwargs = super().get_form_kwargs()
        kwargs["acceptance"] = True
        return kwargs

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["com_requests"] = CommissionRequest.objects.all()
        if not context.get("cancel_url", None):
            context["cancel_url"] = reverse("assets:assets_list")
        return context

    def form_valid(self, form):
        create_acceptance = self.request.POST.get("create_acceptance_job", None)
        technician_id = self.request.POST.get("technicianid", None)

        with transaction.atomic():
            self.object = form.save()
            self.after_save(form)

            if create_acceptance:
                acceptance_job, created = Tbljob.objects.get_or_create(
                    assetid=self.object,
                    jobtypeid=Tbljobtypes.objects.filter(
                        jobtypename__icontains="acceptance"
                    ).first(),
                    jobstatusid=Tbljobstatus.objects.filter(
                        jobstatusname__icontains="progress"
                    ).first(),
                    technicianid=Tbltechnicianlist.objects.get(pk=technician_id),
                )

                response = HttpResponseRedirect(
                    reverse("jobs:job_update", kwargs={"pk": acceptance_job.pk})
                )

                return response

            return HttpResponseRedirect(self.get_success_url())


class SetEquipmentSoftware(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    template_name = "assets/set_equipment_software.html"
    form_class = SetEquipmentSoftwareForm
    permission_required = "model_information.add_equipmentsoftware"

    def get_success_url(self):
        equipment = self.object.equipment.pk
        return reverse("assets:view_asset", kwargs={"pk": equipment})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        equipmentid = self.request.GET.get("equipmentid", None)
        if equipmentid:
            kwargs["equipment_id"] = equipmentid

        return kwargs

    def form_valid(self, form):
        software_id = form.cleaned_data["software"]
        equipment_id = form.cleaned_data["equipment"]
        self.object = apply_software_change(
            equipment=equipment_id, software=software_id, user=self.request.user
        )

        response = HttpResponseRedirect(self.get_success_url())
        return response


class RemoveEquipmentSoftware(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = EquipmentSoftware
    template_name = "assets/remove_equipment_software.html"
    permission_required = "model_information.delete_equipmentsoftware"
    fields = "__all__"
    context_object_name = "software_equipment"

    def get_success_url(self):
        equipment_id = self.object.equipment.pk
        return reverse("assets:view_asset", kwargs={"pk": equipment_id})


class SetEquipmentConfiguration(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    template_name = "assets/set_equipment_configuration.html"
    form_class = SetEquipmentConfigurationForm
    permission_required = "model_information.add_equipmentconfigurationlink"

    def get_success_url(self):
        equipment = self.object.equipment.pk
        return reverse("assets:view_asset", kwargs={"pk": equipment})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        equipmentid = self.request.GET.get("equipmentid", None)
        if equipmentid:
            kwargs["equipment_id"] = equipmentid

        return kwargs

    def form_valid(self, form):
        configuration_id = form.cleaned_data["configuration"]
        equipment_id = form.cleaned_data["equipment"]
        self.object = apply_configuration_change(
            equipment=equipment_id,
            configuration=configuration_id,
        )

        response = HttpResponseRedirect(self.get_success_url())
        return response


class RemoveEquipmentConfiguration(
    LoginRequiredMixin, PermissionRequiredMixin, DeleteView
):
    model = EquipmentConfigurationLink
    template_name = "assets/remove_equipment_configuration.html"
    permission_required = "model_information.delete_equipmentconfigurationlink"
    fields = "__all__"
    context_object_name = "config"

    def get_success_url(self):
        equipment_id = self.object.equipment.pk
        return reverse("assets:view_asset", kwargs={"pk": equipment_id})


class AssetBulkUpdateView(LoginRequiredMixin, CustomerAssetPermissionMixin, BulkUpdateView):
    model = AssetView
    permission_required = "assets.change_tblassets"
    template_name = "assets/bulk_update.html"
    form_class = AssetBulkUpdateForm
    universal_search_fields = UNIVERSAL_SEARCH_FIELDS
    success_view = "assets:assets_list"
    operation = "update"
    table_to_update = Tblassets


def asset_already_exists(resolved_data, **kwargs):
    return bool(
        resolved_data.get("asset", {}).get("asset_id", None)
    )


def model_matches(resolved_data, modelid, **kwargs):
    group_model_id = resolved_data.get("model", {}).get("model_id", None)
    return group_model_id == modelid.pk


def model_mismatched(resolved_data, modelid, **kwargs):
    group_model_id = resolved_data.get("model", {}).get("modelid", None)

    asset_model_id = modelid
    return group_model_id != asset_model_id.pk


def is_unresolved(resolved_data, **kwargs):
    return not bool(resolved_data)


REPLICATION_CONFIG = {
    "unresolved": {
        "check": is_unresolved,
        "context": {
            "valid": False,
            "replication_status": "disabled",
            "replication_message": "Not enough data to copy asset.",
            "replication_color": "secondary",
            "error_message": "Upload or scan new asset information",
        },
    },
    "asset_exists": {
        "check": asset_already_exists,
        "context": {
            "valid": False,
            "replication_status": "disabled",
            "replication_message": "Asset Already Exists",
            "replication_color": "secondary",
            "error_message": "Uploaded information is for asset that already exists in database",
        },
    },
    "model_matched": {
        "check": model_matches,
        "context": {
            "valid": True,
            "replication_status": "enabled",
            "replication_message": "Serial number recognised and new asset matches model of original asset.",
            "replication_color": "success",
            "error_message": None,
        },
    },
    "model_not_matched": {
        "check": model_mismatched,
        "context": {
            "valid": True,
            "replication_status": "enabled",
            "replication_message": "Serial number recognised but model of new asset is different from original asset.",
            "replication_color": "warning",
            "error_message": None,
        },
    },
}


class ReplicateAsset(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    permission_required = "assets.add_tblassets"
    form_class = ReplicateAssetForm
    template_name = "assets/replicate_from_group.html"
    config = REPLICATION_CONFIG

    def get(self, *args, **kwargs):
        group_id = self.kwargs["group_id"]
        if group_id == "new":
            group = self.get_group
            return redirect(
                "assets:replicate_asset", group_id=str(group.pk), pk=self.kwargs["pk"]
            )
        return super().get(*args, **kwargs)

    @cached_property
    def get_template_object(self):
        if self.request.POST:
            asset_id = self.request.POST.get("template_asset")
        else:
            asset_id = self.kwargs["pk"]
        return Tblassets.objects.get(assetid=asset_id)

    def get_form_kwargs(self, form_class=None):
        kwargs = super().get_form_kwargs()
        asset = self.get_template_object
        acceptance_job = asset.jobs.filter(jobtypeid=0).first()
        if acceptance_job:
            kwargs["acceptance_job"] = True
        return kwargs

    @cached_property
    def get_group(self):
        if self.request.POST:
            group_id = self.request.POST.get("group_id")
        group_id = self.kwargs["group_id"]

        if group_id == "new":
            group = TempUploadGroup.objects.filter(
                user=self.request.user,
                document_type_id=DocumentTypes.ASSET_DATA,
                temp_uploads__isnull=True,
            ).first()

            if group is None:
                group = TempUploadGroup.objects.create(
                    user=self.request.user,
                    document_type_id=DocumentTypes.ASSET_DATA,
                )

        else:
            group = TempUploadGroup.objects.filter(
                pk=group_id,
            ).first()

        return group

    def get_customerassetnumber(self):
        return (
            self.get_group.extracted_json.get("parsed", {})
            .get("asset", {})
            .get("customreassetnumber", None)
        )

    def get_serialnumber(self):
        return (
            self.get_group.extracted_json.get("resolved", {})
            .get("asset", {})
            .get("serialnumber", None)
        )

    def form_valid(self, form):

        resolved_data = self.get_group.extracted_json.get("resolved", None)

        has_error = False
        for config in self.config.values():
            if config["check"](
                resolved_data=resolved_data, modelid=self.get_template_object.modelid
            ):
                error = config["context"]["error_message"]
                if error:
                    has_error = True
                    form.add_error(None, error)

        if has_error:
            return self.form_invalid(form)

        self.object = self.get_template_object
        acceptance_job = self.object.jobs.filter(jobtypeid=0).first()
        copy_acceptance = self.request.POST.get("create_acceptance_job", None)

        self.object.pk = None
        self.object.serialnumber = self.get_serialnumber()
        self.object.customerassetnumber = self.get_customerassetnumber()

        with transaction.atomic():
            self.object.save()
            if acceptance_job and copy_acceptance:
                acceptance_job.pk = None
                acceptance_job.assetid = self.object
                acceptance_job.save()

            self.get_group.delete()


        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse("assets:view_asset", kwargs={"pk": self.object.pk})

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["asset"] = self.get_template_object
        context["group"] = self.get_group
        resolved_data = self.get_group.extracted_json.get("resolved", None)

        for config in self.config.values():
            if config["check"](
                resolved_data=resolved_data, modelid=self.get_template_object.modelid
            ):
                context.update(config["context"])
                return context



