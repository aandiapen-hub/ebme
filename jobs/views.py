import datetime
from urllib.parse import urlencode
from django.urls import reverse
from django.db.models import Q
from django.db import transaction, IntegrityError, DatabaseError
from utils.dynamic_formset import AddFormsetRowView

# import permissions
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import  reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    UpdateView,
    ListView,
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
from utils.generic_views import BulkUpdateView, FilteredTableView

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
    "brandname__icontains",
    "jobid__icontains",
    "jobstatus__icontains",
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
        if request.htmx:
            # HTMX request – respond with a redirect header
            return HttpResponse(headers={"HX-Redirect": request.get_full_path()})
        base_qs = self.get_queryset()
        report_type = request.GET.get("report_type")
        report_generator = REPORT_GENERATORS.get(report_type)
        filterclass = self.get_filterset_class()
        self.filterset = filterclass(self.request.GET, queryset=base_qs)

        data = self.filterset.qs.values()
        if request.user.is_staff and data.count() < 300:
            return report_generator(data)
        elif data.count() < 200:
            return report_generator(data)

        return HttpResponse(
            "Too many records selected. Please narrow your filter.",
            status=400,  # or 403 if it's a permissions issue
        )


JOB_FORMSETS = {
    "test_eq": TestEqFormset,
    "checklist": ChecklistFormset,
    "parts_used": PartsUsedFormset,
}
JOB_FORMSET_CONFIG = {
    "parts_used": {
            'lookup_view': "jobs:parts_list",
            'title':'Spare Parts'
    },
    "test_eq": {
        'lookup_view': 'jobs:test_eq_list',
        'title':'Test Equipment',
    },
    "checklist": {
            'lookup_view':"jobs:check_list",
            'title': 'Checklist'
    }

}

class JobUpdateView(
    LoginRequiredMixin,
    CustomerJobPermissionMixin,
    TempUploadMixin,
    UpdateView,
):
    model = Tbljob
    form_class = JobUpdateForm
    template_name = "jobs/update_job.html"
    permission_required = "assets.change_tbljob"

    def get_success_url(self):
        return reverse_lazy("jobs:job_summary", kwargs={"pk": self.object.jobid})

    def get_formsets(self):
        formsets = {}
        for prefix, formset in JOB_FORMSETS.items():
            if self.request.POST:
                formset = formset(
                    self.request.POST, instance=self.object, prefix=prefix
                )
            else:
                formset = formset(
                    instance=self.object, prefix=prefix
                )

            formset_config = JOB_FORMSET_CONFIG.get(prefix, {})
            # add url for list of new formset value option
            list_app_view = formset_config.get('lookup_view', None)

            if list_app_view:
                url = reverse(list_app_view)
                query_params = urlencode({
                    'formset_type': prefix,
                    'modelid': self.object.assetid.modelid.pk,
                })
                formset.get_list_url = f"{url}?{query_params}"
                formset.title = formset_config.get('title', None)

            formsets[prefix] = formset
        return formsets

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["assetid"] = self.request.GET.get("assetid", None)
        context.update(self.get_formsets())
        return context


    def form_valid(self, form):
        context = self.get_context_data()
        formsets = [context[prefix] for prefix in JOB_FORMSETS]

        if not all(formset.is_valid() for formset in formsets):
            return self.form_invalid(form)

        try:
            with transaction.atomic():
                self.object = form.save()

                for formset in formsets:
                    formset.instance = self.object
                    formset.save()

                self.after_save(form)

        except IntegrityError as e:
            form.add_error(None, f"Database integrity error: {e}")
            return self.form_invalid(form)

        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        print('form invalid')
        context = self.get_context_data(form=form)
        return self.render_to_response(context)


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
        context["assetid"] = self.request.GET.get("assetid", None)
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
    LoginRequiredMixin,
    PermissionRequiredMixin,
    ListView
):
    model = Tblassets
    permission_required = "assets.change_tbljob"
    template_name = 'jobs/partials/available_test_eq.html'
    context_object_name = 'test_eq'

    def get_queryset(self):
       return super().get_queryset().filter(is_test_eq=True, asset_status_id=1)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        formset_type = self.request.GET.get('formset_type') 
        config = FORMSET_CONFIG[formset_type]
        context['prefix'] = config["prefix"]
        return context

class SparePartsListView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    ListView
):
    model = Tblpartslist 
    template_name = 'jobs/partials/available_parts.html'
    permission_required = "assets.change_tbljob"
    context_object_name = 'parts'

    def get_queryset(self):
        qs = super().get_queryset()

        qs = qs.filter(Q(inactive=False)|Q(inactive__isnull=True))

        modelid = self.request.GET.get('modelid')
        if modelid:
            qs = qs.filter(part_model__model=modelid)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        formset_type = self.request.GET.get('formset_type') 
        
        config = FORMSET_CONFIG[formset_type]
        context['prefix'] = config["prefix"]
        context['pk_field'] = config["pk_field"]
        return context


class ChecklistListView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    ListView
):
    model = Tblcheckslists 
    permission_required = "assets.change_tbljob"
    template_name = 'jobs/partials/available_checks.html'
    context_object_name = 'checks'

    def get_queryset(self):
        qs = super().get_queryset()

        # qs = qs.filter(Q(inactive=False)|Q(inactive__isnull=True))

        modelid = self.request.GET.get('modelid', None)
        if modelid:
            qs = qs.filter(modelid=modelid)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        formset_type = self.request.GET.get('formset_type')
        config = FORMSET_CONFIG[formset_type]
        context['prefix'] = config["prefix"]
        return context


FORMSET_CONFIG = {
    "parts_used": {
        "prefix": "parts_used",
        "title": 'Parts',
        "row_template_name": None,
        "formset": PartsUsedFormset,
        "lookup_param": "sparepartid",
        "model": Tblpartslist,
        "pk_field": "partid",
        "initial": lambda obj: {
            "partid": obj.pk,
            "unitprice": None,
            "quantity": 1,
        },
    },
    "test_eq": {
        "prefix": "test_eq",
        "title": 'Test eq',
        "row_template_name": None,
        "formset": TestEqFormset,
        "lookup_param": "assetid",
        "model": Tblassets,
        "pk_field": "assetid",
        "initial": lambda obj: {
            "test_eq": obj.pk,
        },
    },
    "checklist": {
        "prefix": "checklist",
        "title": 'Checklist',
        "row_template_name": None,
        "formset": ChecklistFormset,
        "lookup_param": "testid",
        "model": Tblcheckslists,
        "pk_field": "testid",
        "initial": lambda obj: {
            "checkid": obj.pk,
        },
    },
}


class JobAddFormsetRowView(AddFormsetRowView):
    permission_required = "assets.change_tbljob"
    formset_config = FORMSET_CONFIG


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
    permission_required = "assets.view_jobview"
    table_class = None
    model = JobView
    template_columns = {"open": "jobs/tables/open.html"}
    template_name = "jobs/jobs_list.html"
    universal_search_fields = SEARCHFILEDS
    default_columns = [
        "jobid",
        "assetid",
        "jobtypeid",
        "jobstatusid",
        "brandid",
        "modelid",
        "startdate",
        "enddate",
    ]
    bulk_actions = {
        "bulk_update": {
            "url": reverse_lazy("jobs:bulk_update_jobs"),
            "permission": "assets.bulk_update_tbljob",
            "name": "Update",
        },
        "bulk_link_document": {
            "url": reverse_lazy("documents:bulk_link_to_jobs"),
            "permission": "documents.bulk_create_links",
            "name": "Link Document",
        },
    }
