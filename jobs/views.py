import datetime

import json
from django.utils import timezone
from django.urls import reverse
from django.db.models import Q
from urllib.parse import urlencode
from django.db import transaction, IntegrityError, DatabaseError
from utils.dynamic_formset import (
    AddFormsetRowView,
    FormsetOptionsListView,
    FormsetMixin,
)
from django.db.models import(
    Max,
    OuterRef,
    Subquery,
)


# import permissions
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
)

from assets.models import (
    JobView,
    Tblcheckslists,
    Tbljob,
    Tbljobstatus,
    Tbljobtypes,
    Tblassets,
)
from documents.mixins import TempUploadMixin
from documents.services.documents import delete_object_document_links
from parts.models import Tblpartslist
from django_filter_table.views import BulkUpdateView, FilteredTableView, TableAction

from .forms import (
    JobBulkUpdateForm,
    JobCreateForm,
    JobUpdateForm,
    TestEqFormset,
    ChecklistFormset,
    PartsUsedFormset,
)
from .mixins import (
    CustomerJobListPermissionMixin,
    CustomerJobPermissionMixin,
)
from .reports.job_list import generate_jobs_list

# ServiceReportReaderForm)
from .reports.service_reports import generate_service_report

# Job Views.

SEARCHFILEDS = [
    "modelid__modelname__icontains",
    "serialnumber__icontains",
    "assetid__pk__icontains",
    "brandid__brandname__icontains",
    "jobid__icontains",
]


REPORT_GENERATORS = {
    "service_report": generate_service_report,
    "job_list": generate_jobs_list,
}


class GenerateReportView(
    LoginRequiredMixin, CustomerJobListPermissionMixin, FilteredTableView
):
    permission_required = "assets.genreport_tbljob"
    model = JobView
    universal_search_fields = SEARCHFILEDS

    def get(self, request, *args, **kwargs):
        data = super().get_table_data().values()
        count = data.count()

        staff_allowed = request.user.is_staff and count < 300
        user_allowed = count < 200

        if not staff_allowed and not user_allowed:
            response = HttpResponse(
                "Too many records selected. Please narrow your filter.",
                status=403,  # or 403 if it's a permissions issue
            )
            response["HX-Trigger"] = json.dumps({
                "show_message": {
                    "message": "Too many records selected. Download limit is 200 records",
                    "level": "danger",
                },
            })
            return response

        if request.htmx:
            # HTMX request – respond with a redirect header
            return HttpResponse(headers={"HX-Redirect": request.get_full_path()})

        report_type = request.GET.get("report_type")
        report_generator = REPORT_GENERATORS.get(report_type)


        pdf, filename = report_generator(data)

        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}.pdf"'
        return response

FORMSET_CONFIG = {
    "parts_used": {
        "prefix": "parts_used",
        "row_template_name": None,
        "formset": PartsUsedFormset,
        "model": Tblpartslist,
        "pk_field": "partid",
        "lookup_field": "partid",
        "lookup_filter": Q(inactive=False) | Q(inactive__isnull=True),
        "lookup_view": "jobs:parts_list",
        "lookup_query_params": {
            "modelid": lambda view: view.object.assetid.modelid.pk,
        },
        "title": "Spare Parts",
        "initial": lambda obj: {
            "partid": obj.pk,
            "unitprice": None,
            "quantity": 1,
        },
    },
    "test_eq": {
        "prefix": "test_eq",
        "row_template_name": None,
        "formset": TestEqFormset,
        "model": Tblassets,
        "pk_field": "assetid",
        "lookup_field": "test_eq",
        "lookup_filter": Q(is_test_eq=True) & Q(asset_status_id=1),
        "lookup_view": "jobs:test_eq_list",
        "title": "Test Equipment",
        "initial": lambda obj: {
            "test_eq": obj.pk,
        },
    },
    "checklist": {
        "prefix": "checklist",
        "row_template_name": None,
        "formset": ChecklistFormset,
        "model": Tblcheckslists,
        "pk_field": "testid",
        "lookup_field": "checkid",
        "lookup_filter": None,
        "lookup_view": "jobs:check_list",
        "lookup_query_params": {
            "modelid": lambda view: view.object.assetid.modelid.pk,
        },
        "title": "Checklist",
        "initial": lambda obj: {
            "checkid": obj.pk,
        },
    },
}


class JobUpdateView(
    LoginRequiredMixin,
    CustomerJobPermissionMixin,
    TempUploadMixin,
    FormsetMixin,
):
    model = Tbljob
    form_class = JobUpdateForm
    template_name = "jobs/update_job.html"
    permission_required = "assets.change_tbljob"
    config = FORMSET_CONFIG
    success_url_app_view = "jobs:job_summary"


    def form_valid(self, form):
        try:
            with transaction.atomic():
                # saving of formset and form handled in FormsetMixin
                response = super().form_valid(form)
                # save document related records from TempUploadMixin
                self.after_save(form)
                return response

        except Exception as e:
            form.add_error(None, f"Error while saving: {e}")
            return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if context.get("cancel_url", None) is None:
            context["cancel_url"] = reverse(
                "jobs:job_summary", kwargs={"pk": self.object.pk}
            )

        return context


class JobBulkUpdateView(BulkUpdateView, CustomerJobPermissionMixin):
    model = JobView
    permission_required = "assets.change_tbljob"
    template_name = "jobs/bulk_update_jobs.html"
    form_class = JobBulkUpdateForm
    universal_search_fields = SEARCHFILEDS
    success_view = "jobs:jobs_list"
    operation = "update"
    table_to_update = Tbljob


class JobDetailView(
    LoginRequiredMixin,
    CustomerJobPermissionMixin,
    DetailView,
):
    model = JobView
    template_name = "jobs/job_summary.html"
    context_object_name = "job"
    permission_required = "assets.view_jobview"


class JobCreateView(
    LoginRequiredMixin,
    CustomerJobPermissionMixin,
    TempUploadMixin,
    CreateView,
):
    model = Tbljob
    form_class = JobCreateForm
    template_name = "jobs/create_job.html"
    permission_required = "assets.add_tbljob"
    success_url_app_view = "jobs:job_update"

    def get_initial(self):
        """Set a default value for the 'assetid' field using a query parameter"""
        initial = super().get_initial()

        # quick ppm job
        quickjob = self.request.GET.get("quickjob", "")
        if "successful_ppm" in quickjob:
            initial["workdone"] = (
                "Service checks as per manufacturer's service manual carried out. All checks passed."
            )
            initial["jobstartdate"] = datetime.date.today
            initial["jobenddate"] = datetime.date.today
            initial["jobstatusid"] = Tbljobstatus.objects.get(jobstatusname="Completed")
            initial["jobtypeid"] = Tbljobtypes.objects.get(jobtypename="PPM")

        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        asset_id = self.request.GET.get("assetid", None)
        context["assetid"] = asset_id

        if asset_id:
            cancel_url = reverse("assets:view_asset", kwargs={"pk": asset_id})
        else:
            cancel_url = reverse("jobs:jobs_list")
        if context.get("cancel_url", None) is None:
            context["cancel_url"] = cancel_url

        return context

    def form_valid(self, form):
        with transaction.atomic():
            self.object = form.save()
            self.after_save(form)

            return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        context = self.get_context_data(form=form)
        return self.render_to_response(context)


class TestEqListView(
    LoginRequiredMixin, PermissionRequiredMixin, FormsetOptionsListView
):
    model = Tblassets
    permission_required = "assets.change_tbljob"
    template_name = "jobs/partials/available_test_eq.html"
    config = FORMSET_CONFIG
    add_formset_row_view = "jobs:add_formset_row"
    search_fields = [
        "serialnumber",
        "modelid__modelname",
    ]


class SparePartsListView(
    LoginRequiredMixin, PermissionRequiredMixin, FormsetOptionsListView
):
    model = Tblpartslist
    permission_required = "assets.change_tbljob"
    config = FORMSET_CONFIG
    add_formset_row_view = "jobs:add_formset_row"

    def get_queryset(self):
        qs = super().get_queryset()

        qs = qs.filter()

        modelid = self.request.GET.get("modelid")
        if modelid:
            qs = qs.filter(part_model__model=modelid)

        return qs


class ChecklistListView(
    LoginRequiredMixin, PermissionRequiredMixin, FormsetOptionsListView
):
    model = Tblcheckslists
    permission_required = "assets.change_tbljob"
    config = FORMSET_CONFIG
    add_formset_row_view = "jobs:add_formset_row"

    def get_queryset(self):
        qs = super().get_queryset()
        modelid = self.request.GET.get("modelid", None)
        if modelid:
            qs = qs.filter(modelid=modelid)

        return qs


SCANNER_CONFIG_MAP = {
    "assetid": {
        "value": lambda data: data.get("asset", {}).get("asset_id", None),
        "formset_type": "test_eq",
    },
    "partid": {
        "value": lambda data: data.get("part", {}).get("part_id", None),
        "formset_type": "parts_used",
    },
}


class JobAddFormsetRowView(AddFormsetRowView):
    permission_required = "assets.change_tbljob"
    formset_config = FORMSET_CONFIG
    scanner_config_map = SCANNER_CONFIG_MAP


class JobDeleteView(
    LoginRequiredMixin,
    CustomerJobPermissionMixin,
    DeleteView,
):
    model = Tbljob
    template_name = "jobs/partials/delete_modal.html"
    permission_required = "assets.delete_tbljob"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["view_type"] = "delete"
        context["title"] = f"Delete Job: {self.object.jobid}"
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        try:
            with transaction.atomic():
                delete_object_document_links(self.object)
                self.object.delete()
            # Return an empty 204 response so HTMX knows it's successful
            return HttpResponse(status=204)
        except Exception as e:
            # Return an error message as plain text (not JSON)
            context = self.get_context_data()
            context["error_message"] = (
                f"An error occurred while deleting the Job. Error Details: {str(e)}"
            )
            return self.render_to_response(context)


class FilteredJobTableView(
    LoginRequiredMixin, CustomerJobListPermissionMixin, FilteredTableView
):
    paginate_by = 25
    title = "Jobs"
    permission_required = "assets.view_jobview"
    table_class = None
    model = JobView
    open_column = 'jobid'
    universal_search_fields = SEARCHFILEDS
    default_columns = [
        "assetid",
        "serialnumber",
        "jobtypeid",
        "jobstatusid",
        "modelid",
        "startdate",
        "enddate",
        "customerid",
    ]
    additional_filters = (
        "filter_latest_ppm",
    )
    quick_filters = {
        'completed_today': {
            'name':'Completed Today',
            'lookups': {"enddate": timezone.localdate()},
         },
        'completed_last_7_days': {
            'name':'Completed in last 7 days',
            "lookups": {
                "enddate__gte": timezone.localdate() - datetime.timedelta(days=7),
            }
         },
    }

    def filter_latest_ppm(self, qs):
        qs = qs.filter(
            jobtypeid__jobtypename__icontains="PPM"
        )
        latest = qs.filter(assetid=OuterRef("assetid")).order_by("-enddate").values("enddate")[:1]
        return qs.filter(
            enddate=Subquery(latest)
        )

    actions = [
        TableAction(
            name="New",
            type='link',
            on_selectable_items = False,
            url=reverse_lazy("jobs:job_create"),
            permission="assets.add_tbljob",
            icon="bi-plus",
            color='outline-secondary'
        ),
        TableAction(
            name="Update",
            type='bulk_htmx',
            on_selectable_items = True,
            url=reverse_lazy("jobs:bulk_update_jobs"),
            permission="assets.bulk_update_tbljob",
            icon="bi-pencil",
            color='outline-secondary',
        ),
        TableAction(
            name="Link Document",
            type='bulk_htmx',
            on_selectable_items = True,
            url=reverse_lazy("documents:bulk_link_to_jobs"),
            permission="documents.bulk_create_links",
            icon="bi-file-earmark-plus",
            color='outline-secondary',
        ),
        TableAction(
            name="Service Report",
            type='htmx',
            on_selectable_items = True,
            url=reverse_lazy('jobs:gen_report'),
            qp = urlencode({'report_type':'service_report'}),
            permission="assets.view_jobview",
            icon="bi-file-earmark-pdf ",
            color='outline-secondary',
        ),
        TableAction(
            name="Job List",
            type='htmx',
            on_selectable_items = True,
            url=reverse_lazy('jobs:gen_report'),
            qp=urlencode({'report_type':'job_list'}),
            permission="assets.view_jobview",
            icon="bi-file-earmark-pdf ",
            color='outline-secondary',
        ),
    ]


