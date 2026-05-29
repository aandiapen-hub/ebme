import datetime
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string

# import permissions
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    UpdateView,
    TemplateView,
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
    "assetid__assetid__icontains",
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
        self.object_list = self.get_queryset()
        base_qs = self.get_queryset()
        report_type = request.GET.get("report_type")
        report_generator = REPORT_GENERATORS.get(report_type)
        filterclass = self.get_filterset_class()
        self.filterset = filterclass(self.request.GET, queryset=base_qs)

        data = self.filterset.qs.values()
        if request.user.is_staff and data.count() < 1000:
            return report_generator(data)
        elif data.count() < 200:
            return report_generator(data)

        return HttpResponse(
            "Too many records selected. Please narrow your filter.",
            status=400,  # or 403 if it's a permissions issue
        )


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
            formsets[prefix] = formset(
                self.request.POST or None, instance=self.object, prefix=prefix
            )
        return formsets

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["assetid"] = self.request.GET.get("assetid", None)
        context.update(self.get_formsets())
        return context

    def form_valid(self, form):
        context = self.get_context_data()

        formsets = [context[prefix] for prefix in JOB_FORMSETS]

        if all([formset.is_valid for formset in formsets]):
            with transaction.atomic():
                self.object = form.save()
                for formset in formsets:
                    formset.instance = self.object
                    formset.save()
                self.after_save(form)

            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.form_invalid(form)

    def form_invalid(self, form):
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


JOB_FORMSETS = {
    "test_eq": TestEqFormset,
    "checklist": ChecklistFormset,
    "parts_used": PartsUsedFormset,
}


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

    def get_formsets(self):
        formsets = {}
        for prefix, formset in JOB_FORMSETS.items():
            formsets[prefix] = formset(
                self.request.POST or None, instance=self.object, prefix=prefix
            )
        return formsets

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["assetid"] = self.request.GET.get("assetid", None)
        context.update(self.get_formsets())
        return context

    def form_valid(self, form):
        context = self.get_context_data()

        formsets = [context[prefix] for prefix in JOB_FORMSETS]

        if all([formset.is_valid for formset in formsets]):
            with transaction.atomic():
                self.object = form.save()
                for formset in formsets:
                    formset.instance = self.object
                    formset.save()
                self.after_save(form)

            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.form_invalid(form)

    def form_invalid(self, form):
        context = self.get_context_data(form=form)
        return self.render_to_response(context)


FORMSET_CONFIG = {
    "parts_used": {
        "prefix": "parts_used",
        "row_template_name":"jobs/partials/job_parts_used.html#row",
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
        "row_template_name":"jobs/partials/job_test_eq.html#row",
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
        "row_template_name":"jobs/partials/job_checklist_update.html#row",
        "formset": ChecklistFormset,
        "lookup_param": "testid",
        "model": Tblcheckslists,
        "pk_field": "testid",
        "initial": lambda obj: {
            "checkid": obj.pk,
        },
    },
}


class AddFormsetRowView(TemplateView):
    def get_template_names(self):
        formset_type = self.kwargs["formset_type"]
        config = FORMSET_CONFIG[formset_type]
        return [config.get('row_template_name')]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        formset_type = self.kwargs["formset_type"]
        config = FORMSET_CONFIG[formset_type]
        prefix = config["prefix"]
        total_forms = int(self.request.GET[f"{prefix}-TOTAL_FORMS"])


        # prefill form before rendering
        lookup_param = 10  # self.request.GET.get(config["lookup_param"], None)
        if lookup_param:
            #check if row already exists
            existing_ids = set()
            for key, value in self.request.GET.items():
                if key.endswith("-id") and value:
                    existing_ids.add(value)
                    return HttpResponse("")  # or return 204 / empty fragment
            obj = get_object_or_404(
                config["model"],
                **{config["pk_field"]: lookup_param},
            )
            initial = config["initial"](obj)

        formset = config["formset"].form
        form = formset(prefix=f"{prefix}-{total_forms}", initial=initial)

        context["prefix"] = prefix
        context["total_forms"] = total_forms
        context["form"] = form
        return context


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
