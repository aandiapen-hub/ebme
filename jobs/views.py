from utils.generic_views import FilteredTableView
import datetime
from pickle import NONE
from django.forms import model_to_dict
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from django.views import View
from django.views.generic import (
    CreateView,
    UpdateView,
    DeleteView,
    ListView,
    DetailView,
    FormView,
)
from django.shortcuts import render
from django.db import transaction

from assets.models import (
    AssetView,
    JobView,
    Tbljobstatus,
    Tbljobtypes,
    Tbljob,
    Tbltestscarriedout,
    Tblpartsused,
    Tbltesteqused,
    Tblassets,
    Tbltestresult,
)


from django_filters.views import FilterView


from documents.models import TblDocumentLinks, TblDocumentTypes, TemporaryUpload
from documents.utils import get_extraction_results, save_extraction_results
from documents.views import SaveTempFiles

from utils.generic_views import BulkUpdateView, get_visible_columns


from .forms import (
    JobUpdateForm,
    JobBulkUpdateForm,
    AddTestEquipmentToJobForm,
    JobCreateForm,
    TestCarriedOutForm,
    SparePartsUsedCreateForm,
    SparePartsUsedUpdateForm,
)
# ServiceReportReaderForm)

from .reports.service_reports import generate_service_report
from .reports.job_list import generate_jobs_list
from utils.generic_filters import dynamic_filterset_generator

# import permissions
from django.contrib.auth.mixins import LoginRequiredMixin
from .mixins import (
    CustomerJobPermissionMixin,
    CustomerJobChildPermissionMixin,
    CustomerJobListPermissionMixin,
)


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
    LoginRequiredMixin, CustomerJobListPermissionMixin, FilterView
):
    permission_required = "assets.genreport_tbljob"
    model = JobView

    def get_visible_columns(self):
        # Get user's preferred columns from user_profiles.table_settings
        return get_visible_columns(self.request, self.model)

    def get_filterset_class(self):
        active_filters = [
            key
            for key, value in self.request.GET.items()
            if key
            not in [
                "active_filters",
                "new_active_filter",
                "page",
                "csrfmiddlewaretoken",
                "universal_search",
                "sort",
            ]
        ]
        return dynamic_filterset_generator(
            self.model,
            universal_search_fields=SEARCHFILEDS,
            active_filters=active_filters,
        )

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
    UpdateView,
):
    model = Tbljob
    form_class = JobUpdateForm
    template_name = "jobs/update_job.html"
    permission_required = "assets.change_tbljob"

    def get_success_url(self):
        return reverse_lazy("jobs:job_summary", kwargs={"pk": self.object.jobid})

    def form_valid(self, form):
        self.object = form.save()
        return HttpResponseRedirect(self.get_success_url())


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
    CreateView,
):
    model = Tbljob
    form_class = JobCreateForm
    template_name = "jobs/create_job.html"
    permission_required = "assets.add_tbljob"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["assetid"] = self.request.GET.get("assetid")
        return context

    def get_initial(self):
        """Set a default value for the 'assetid' field using a query parameter"""
        initial = super().get_initial()
        initial["assetid"] = self.request.GET.get("assetid")  # Set default

        # quick ppm job
        quickjob = self.request.GET.get("quickjob", "")
        if "successful_ppm" in quickjob:
            initial["workdone"] = (
                "Service checks as per manufacturer's service manual carried out. All checks passed."
            )
            initial["jobstartdate"] = datetime.date.today
            initial["jobenddate"] = datetime.date.today
            initial["jobstatusid"] = Tbljobstatus.objects.get(
                jobstatusname="Completed")
            initial["jobtypeid"] = Tbljobtypes.objects.get(jobtypename="PPM")

        return initial

    def form_valid(self, form):
        with transaction.atomic():
            self.object = form.save()

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse_lazy("jobs:job_update", kwargs={"pk": self.object.jobid})


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
                TblDocumentLinks.delete_link_documents(self.object)
                self.object.delete()
            # Return an empty 204 response so HTMX knows it's successful
            return HttpResponse(status=204)
        except Exception as e:
            # Return an error message as plain text (not JSON)
            context = self.get_context_data()
            context["error_message"] = (
                f"An error occurred while deleting the Job. Error Details: {
                    str(e)}"
            )
            return self.render_to_response(context)


# Tests carried out views
"""
class TestsCarriedoutTable(tables.Table):
    class Meta:
        model = Tbltestscarriedout
        template_name = "jobs/tables/testscarriedout_table.html"
        attrs = {
            'class': 'table table-hover table-bordered table-striped  ',
            'thead': {
                'class': 'table-bordered align-middle' ,
            },
    }

class TestsCarriedOutTableView(LoginRequiredMixin,
                               CustomerJobChildPermissionMixin,
                               SingleTableView):
    model = Tbltestscarriedout
    table_class = TestsCarriedoutTable
    permission_required = 'assets.view_tbltestscarriedout'

    def get_queryset(self):
        qs = Tbltestscarriedout.objects.filter(jobid=self.kwargs['jobid'])
        return qs

    def get_context_data(self, **kwargs):
        context = super(TestsCarriedOutTableView,
                        self).get_context_data(**kwargs)
        context['jobid'] = self.kwargs['jobid']
        return context

    def get_template_names(self):
        if self.request.htmx:
            template_name = "jobs/testscarriedout.html#tco-partials"
        else:
            template_name = "jobs/testscarriedout.html"
        return template_name

"""


class TestsCarriedOutView(
    LoginRequiredMixin, CustomerJobChildPermissionMixin, ListView
):
    model = Tbltestscarriedout
    context_object_name = "checklist"
    template_name = "jobs/partials/checklist.html"
    permission_required = "assets.view_tbltestscarriedout"

    def get_queryset(self):
        queryset = Tbltestscarriedout.objects.filter(jobid=self.jobid)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["jobid"] = self.jobid
        return context


class TestsCarriedOutUpdate(
    LoginRequiredMixin, CustomerJobChildPermissionMixin, UpdateView
):
    model = Tbltestscarriedout
    template_name = "jobs/partials/testscarriedout_update.html"
    context_object_name = "check"
    fields = "__all__"
    permission_required = "assets.change_tbltestscarriedout"

    """def get_success_url(self):
        return reverse('jobs:job_testscarriedout', kwargs={'pk': self.object.testid})"""

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        result = self.request.POST.get("result")
        result_mapping = {"Pass": 1, "Fail": 2, "n/a": 3}

        if result in result_mapping:
            resultid = Tbltestresult.objects.get(
                resultid=result_mapping[result])
            self.object.resultid = resultid
        else:
            self.object.resultid = None
        self.object.save(update_fields=["resultid"])

        if self.request.htmx:
            return render(
                self.request,
                "jobs/partials/checklist.html#check",
                {"check": self.object},
            )
        return super().post(self)


class TestsCarriedOutCreate(
    LoginRequiredMixin, CustomerJobChildPermissionMixin, CreateView
):
    model = Tbltestscarriedout
    # fields = ('checkid','resultid')
    form_class = TestCarriedOutForm
    template_name = "jobs/partials/testscarriedout_modal.html"
    permission_required = "assets.add_tbltestscarriedout"

    def get_success_url(self):
        url = reverse("jobs:testscarriedout")
        return f"{url}?jobid={self.jobid}"

    def get_context_data(self, **kwargs):
        context = super(TestsCarriedOutCreate, self).get_context_data(**kwargs)
        context["jobid"] = self.jobid
        return context

    def form_valid(self, form):
        form.instance.jobid = Tbljob.objects.get(jobid=self.jobid)
        check = form.save()
        if self.request.htmx:
            return render(
                self.request, "jobs/partials/checklist.html#check", {
                    "check": check}
            )
        return super().form_valid(form)


class TestsCarriedOutDelete(
    LoginRequiredMixin, CustomerJobChildPermissionMixin, DeleteView
):
    model = Tbltestscarriedout
    template_name = "jobs/partials/testscarriedout_modal.html"
    permission_required = "assets.delete_tbltestscarriedout"

    def get_success_url(self):
        url = reverse("jobs:testscarriedout")
        return f"{url}?jobid={self.jobid}"

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()

        if request.htmx:
            # Send an empty response to remove the row in HTMX
            return HttpResponse("")
        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["view_type"] = "delete"
        context["title"] = "Delete Test"
        return context


# spare parts used views
"""
class SparePartsUsedTable(tables.Table):
    class Meta:
        model = Tblpartsused
        template_name = "jobs/tables/sparepartsused_table.html"

class SparePartsUsedTableView(LoginRequiredMixin,
                              CustomerJobChildPermissionMixin,
                              SingleTableView):
    model = Tblpartsused
    table_class = SparePartsUsedTable
    permission_required = 'assets.view_tblpartsused'

    def get_queryset(self):
        qs = Tblpartsused.objects.filter(jobid=self.kwargs['jobid'])
        return qs

    def get_context_data(self, **kwargs):
        context = super(SparePartsUsedTableView,
                        self).get_context_data(**kwargs)
        context['jobid'] = self.kwargs['jobid']
        return context

    def get_template_names(self):
        if self.request.htmx:
            template_name =  "jobs/sparepartsused.html#spu-partials"
        else:
            template_name =  "jobs/sparepartsused.html"
        return template_name
"""


class SparePartsUsedListView(
    LoginRequiredMixin, CustomerJobChildPermissionMixin, ListView
):
    model = Tblpartsused
    context_object_name = "partslist"
    template_name = "jobs/partials/partslist.html"
    permission_required = "assets.view_tblpartsused"

    def get_queryset(self):
        jobid = self.request.GET.get("jobid")
        queryset = Tblpartsused.objects.filter(jobid=jobid)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["jobid"] = self.request.GET.get("jobid")
        return context


class SparePartsUsedDetail(
    LoginRequiredMixin, CustomerJobChildPermissionMixin, DetailView
):
    model = Tblpartsused
    context_object_name = "part"

    template_name = "jobs/partials/partslist.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["jobid"] = self.jobid
        return context

    def render_to_response(self, context, **response_kwargs):
        if self.request.htmx:
            return render(self.request, "jobs/partials/partslist.html#part", context)
        return super().render_to_response(context, **response_kwargs)


class SparePartsUsedUpdate(
    LoginRequiredMixin, CustomerJobChildPermissionMixin, UpdateView
):
    model = Tblpartsused
    template_name = "jobs/partials/sparepartsused_update.html"
    form_class = SparePartsUsedUpdateForm
    context_object_name = "part"
    permission_required = "assets.change_tblpartsused"

    def get_success_url(self):
        url = reverse("jobs:sparepartsused")
        return f"{url}?jobid={self.jobid}"

    def form_valid(self, form):
        try:
            part = form.save()
        except Exception as e:
            messages.warning(
                self.request, f"There was an error saving the update. Details: {
                    str(e)}"
            )
            context = self.get_context_data(form=form)
            return self.render_to_response(context)

        saved_part = Tblpartsused.objects.get(partsusedid=part.partsusedid)
        if self.request.htmx:
            return render(
                self.request, "jobs/partials/partslist.html#part", {
                    "part": saved_part}
            )
        return HttpResponseRedirect(self.get_success_url())


class SparePartsUsedDelete(
    LoginRequiredMixin, CustomerJobChildPermissionMixin, DeleteView
):
    model = Tblpartsused
    template_name = "jobs/partials/sparepartsused_modal.html"
    permission_required = "assets.delete_tblpartsused"

    def get_success_url(self):
        url = reverse("jobs:testscarriedout")
        return f"{url}?jobid={self.jobid}"

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if request.htmx:
            self.object.delete()
            # Return an empty response to indicate successful deletion
            return HttpResponse("")
        return super().post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["view_type"] = "delete"
        return context


class SparePartsUsedCreateView(
    LoginRequiredMixin, CustomerJobChildPermissionMixin, CreateView
):
    model = Tblpartsused
    template_name = "jobs/partials/sparepartsused_modal.html"
    form_class = SparePartsUsedCreateForm
    permission_required = "assets.add_tblpartsused"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        modelid = Tbljob.objects.get(jobid=self.jobid).assetid.modelid
        kwargs["modelid"] = modelid
        return kwargs

    def get_success_url(self):
        url = reverse("jobs:sparepartsused")
        return f"{url}?jobid={self.jobid}"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["jobid"] = self.jobid
        return context

    def form_valid(self, form):
        form.instance.jobid = Tbljob.objects.get(jobid=self.jobid)
        part = form.save()
        saved_part = Tblpartsused.objects.get(partsusedid=part.partsusedid)
        if self.request.htmx:
            return render(
                self.request, "jobs/partials/partslist.html#part", {
                    "part": saved_part}
            )
        return HttpResponseRedirect(self.get_success_url())


# Test equipment used views
"""class TestEquipmentUsedTable(tables.Table):
    class Meta:
        model = Tbltesteqused
        template_name = "jobs/tables/testeqused_table.html"

class TestEquipmentUsedTableView(LoginRequiredMixin,
                                 CustomerJobChildPermissionMixin,
                                 SingleTableView):
    model = Tbltesteqused
    table_class = TestEquipmentUsedTable
    permission_required = 'assets.view_tbltesteqused'

    def get_queryset(self):
        qs = Tbltesteqused.objects.filter(jobid=self.kwargs['jobid'])
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['jobid'] = self.kwargs['jobid']
        return context


    def get_template_names(self):
        if self.request.htmx:
            template_name =  "jobs/testequipmentused.html#teu-partials"
        else:
            template_name =  "jobs/testequipmentused.html"
        return template_name"""


class TestEquipmentUsedListView(
    LoginRequiredMixin, CustomerJobChildPermissionMixin, ListView
):
    model = Tbltesteqused
    context_object_name = "TestEquipmentList"
    template_name = "jobs/partials/testeqlist.html"
    permission_required = "assets.view_tbltesteqused"

    def get_queryset(self):
        jobid = self.request.GET.get("jobid")
        queryset = Tbltesteqused.objects.filter(jobid=jobid)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["jobid"] = self.jobid
        return context


class TestEquipmentUsedCreate(
    LoginRequiredMixin, CustomerJobChildPermissionMixin, CreateView
):
    model = Tbltesteqused
    template_name = "jobs/partials/testeqused_modal.html"
    form_class = AddTestEquipmentToJobForm
    permission_required = "assets.add_tbltesteqused"

    def get_success_url(self):
        url = reverse("jobs:testequipmentused")
        return f"{url}?jobid={self.jobid}"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["jobid"] = self.jobid
        used_eq = list(
            Tbltesteqused.objects.filter(jobid=self.jobid).values_list(
                "test_eq", flat=True
            )
        )
        context["test_eq_options"] = Tblassets.objects.filter(
            is_test_eq=True,
            asset_status_id=1,
        ).exclude(assetid__in=used_eq)

        return context

    def post(self, request, *args, **kwargs):
        test_eq_ids = self.request.POST.getlist("selected")
        job = Tbljob.objects.get(jobid=self.jobid)
        used_eq_objects = [
            Tbltesteqused(test_eq_id=test_eq_id, jobid=job)
            for test_eq_id in test_eq_ids
        ]

        # Bulk create all at once
        Tbltesteqused.objects.bulk_create(used_eq_objects)

        return HttpResponseRedirect(self.get_success_url())


class TestEquipmentUsedDelete(
    LoginRequiredMixin, CustomerJobChildPermissionMixin, DeleteView
):
    model = Tbltesteqused
    permission_required = "assets.delete_tbltesteqused"
    template_name = "jobs/partials/testeqused_delete_modal.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["view_type"] = "delete"
        return context

    def get_success_url(self):
        url = reverse("jobs:testequipmentused")
        return f"{url}?jobid={self.jobid}"

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        if request.htmx:
            self.object.delete()
            # Return an empty response to indicate successful deletion
            return HttpResponse(status=200)
        return super().post(request, *args, **kwargs)


class JobBulkUpdateView(BulkUpdateView, CustomerJobListPermissionMixin):
    context_object_name = "jobs"
    model = JobView
    db_table = Tbljob
    permission_required = "assets.change_tblassets"
    form_class = JobBulkUpdateForm
    context_object_name = "assets"
    summary_field_names = ["model", "customer"]
    table_class = NONE
    success_url = reverse_lazy("jobs:jobs_list")


class ServiceReportReader(LoginRequiredMixin, CustomerJobPermissionMixin, View):
    # form_class = ServiceReportReaderForm
    template_name = "jobs/report_reader.html"
    permission_required = "assets.add_tbljob"

    def post(self, request, *args, **kwargs):
        return self.form_valid(request.POST)

    def form_valid(self, form):
        self.group = self.kwargs.get("temp_file_group")

        files = TemporaryUpload.objects.filter(
            user=self.request.user, group=self.group)

        from .utils.report_reader import report_reader

        output = report_reader(files)

        # output = {'serialnumber': 'MBP0000998', 'jobtypename': 'PPM', 'jobstatus': 'Completed', 'job_no': '400203903', 'reported_fault': 'Preventative maintenance', 'call_date': '2018-02-15', 'jobstartdate': '2018-02-15', 'jobenddate': '2018-02-26', 'workdone': 'Device cleaned and disinfected. Main board and battery clips replaced. SpO2 module error 010 resolved. Device fully checked for functionality and safety. Software version V1.05.00 used.', 'further_work': 'None'}

        if len(output) == 0:
            messages.warning(
                self.request, "Document does not contain service or calibration data"
            )
            return render(self.request, "partials/messages.html", context=None)
        cleaned_output = self.clean_parsed_data(output)

        save_extraction_results(
            user_id=self.request.user, group=self.group, results=cleaned_output, hours=1
        )

        response = HttpResponse()
        response["HX-Redirect"] = reverse(
            "jobs:report_reader_output", kwargs={"temp_file_group": self.group}
        )
        return response

    def clean_parsed_data(self, raw):
        # Example sanitization or remapping
        jobtypeid = Tbljobtypes.objects.get(
            jobtypename=raw.get("jobtypename")
        ).jobtypeid
        jobstatusid = Tbljobstatus.objects.get(
            jobstatusname=raw.get("jobstatus")
        ).jobstatusid
        return {
            "serialnumber": raw.get("serialnumber", ""),
            "jobtypeid": jobtypeid,
            "jobstatusid": jobstatusid,
            "workdone": raw.get("workdone"),
            "jobstartdate": raw.get("jobstartdate"),
            "jobenddate": raw.get("jobenddate"),
            "document_type": "service_report",
        }


class ServiceReportOutput(LoginRequiredMixin, CustomerJobPermissionMixin, FormView):
    form_class = JobCreateForm
    template_name = "jobs/partials/report_reader_output.html"
    permission_required = "assets.add_tbljob"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.group = self.kwargs.get("temp_file_group")

        new_job_data = get_extraction_results(
            user_id=self.request.user, group=self.group
        )
        serial_number = new_job_data.get("serialnumber")
        assets = AssetView.objects.filter(
            serialnumber__icontains=serial_number)
        jobslist = {}
        for asset in assets:
            jobslist[asset.assetid] = JobView.objects.filter(
                assetid=asset.assetid
            ).order_by("-startdate")

        context["jobslist"] = jobslist
        context["temp_document_group"] = self.group
        return context


class JobCreateFromReportView(JobCreateView):
    template_name = "jobs/partials/create_job_from_report.html"

    def get_initial(self):
        """Set a default value for the 'assetid' field using a query parameter"""
        initial = super().get_initial()
        group = self.kwargs.get("temp_file_group")
        # job info from session data
        new_job_data = get_extraction_results(
            user_id=self.request.user, group=group)

        if new_job_data:
            initial.update(new_job_data)
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["temp_document_group"] = self.kwargs.get("temp_file_group")
        return context

    def form_valid(self, form):
        try:
            with transaction.atomic():
                self.object = form.save()
                self.group = self.kwargs.get("temp_file_group")
                files = TemporaryUpload.objects.filter(
                    user=self.request.user, group=self.group
                )
                if files:
                    save_temp_files = SaveTempFiles(
                        temp_files=files,
                        link_row=self.object.pk,
                        link_table=self.model._meta.db_table,
                    )
                    save_temp_files.save_all()

            response = HttpResponse(status=200)
            response["HX-redirect"] = self.get_success_url()
            return response

        except Exception as e:
            messages.warning(
                self.request, f"job could not be updated. Error:{str(e)}")
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse_lazy("jobs:job_update", kwargs={"pk": self.object.jobid})

    def form_invalid(self, form):
        response = render(
            self.request, "partials/messages.html", context={"form": form}
        )
        response["HX-Retarget"] = "this"
        response["HX-Reswap"] = "beforeend"

        return response


class JobUpdateFromReportView(JobUpdateView):
    template_name = "jobs/partials/update_job_from_report.html"

    def get_success_url(self):
        return reverse_lazy("jobs:job_summary", kwargs={"pk": self.object.jobid})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Store original model values
        job = JobView.objects.get(jobid=self.object.jobid)
        context["temp_document_group"] = self.request.GET.get("group")
        context["original_values"] = model_to_dict(job)
        return context

    def get_initial(self):
        initial = super().get_initial()
        self.group = self.kwargs.get("temp_file_group")
        new_job_data = get_extraction_results(
            user_id=self.request.user, group=self.group
        )
        if new_job_data:
            current_job_data = self.get_object()
            initial.update(new_job_data)
            initial["workdone"] = (
                current_job_data.workdone
                + "\nInformation From Job Report: \n"
                + new_job_data["workdone"]
            )
            initial["temp_document_group"] = self.group
        return initial

    def form_valid(self, form):
        try:
            with transaction.atomic():
                self.object = form.save()
                self.group = self.kwargs.get("temp_file_group")
                files = TemporaryUpload.objects.filter(
                    user=self.request.user, group=self.group
                )

                if files:
                    save_temp_files = SaveTempFiles(
                        temp_files=files,
                        link_row=self.object.pk,
                        link_table=self.model._meta.db_table,
                        document_type=TblDocumentTypes.objects.filter(
                            document_type_name="Service Report"
                        ).first(),
                        file_name="job" + str(self.object.pk),
                    )
                    save_temp_files.save_all()
        except Exception as e:
            if "unique_hash" in str(e):
                messages.warning(
                    self.request,
                    "Job could not be updated because service report already exists in database.\
                                         The report cannot be saved again.",
                )
            else:
                messages.warning(
                    self.request, f"job could not be updated. Error:{str(e)}"
                )
            return self.form_invalid(form)

        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        response = render(
            self.request, "partials/messages.html", context={"form": form}
        )
        response["HX-Retarget"] = f"#job_update_div_{self.object.jobid}"
        response["HX-Reswap"] = "beforeend"
        return response


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
