from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from .models import (
    CapitalProject,
    CapitalAcquisition,
    CommissionRequest,
)

from utils.generic_views import FilteredTableView, TableAction
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    UpdateView,
)


CAPITAL_PROJECT_SEARCH_FIELDS = ["code", "name"]


class CapitalProjectFilterView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    FilteredTableView
):
    paginate_by = 25
    title = 'Projects'
    permission_required = "capital_project.view_capitalproject"
    table_class = None
    open_column = 'code'
    model = CapitalProject
    universal_search_fields = CAPITAL_PROJECT_SEARCH_FIELDS
    default_columns = [
        "code",
        "name",
        "statusid",
        "typeid",
        "startdate",
        "enddate",
    ]

    actions = [
        TableAction(
                name='Add',
                type='link',
                url=reverse_lazy('capital_projects:project_create'),
                permission='capital_project.add_capitalproject',
                icon='bi-plus',
                color='outline-secondary'
            ),
    ]


class CapitalProjectDetailView(DetailView):
    model = CapitalProject
    template_name = "capital_project/capital_project_detail.html"
    context_object_name = "project"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_project_count"] = self.object.acquisition.all().count()

        return context


class CapitalProjectCreateView(CreateView):
    model = CapitalProject
    fields = "__all__"
    template_name = "capital_project/capital_project_create.html"
    context_object_name = "project"

    def get_success_url(self):

        return reverse("capital_projects:project_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = reverse("capital_projects:projects")
        return context


class CapitalProjectUpdateView(UpdateView):
    model = CapitalProject
    fields = "__all__"
    template_name = "capital_project/capital_project_update.html"
    context_object_name = "project"

    def get_success_url(self):
        return reverse("capital_projects:project_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = reverse(
            "capital_projects:project_detail", kwargs={"pk": self.object.pk}
        )
        return context


class CapitalProjectDeleteView(DeleteView):
    model = CapitalProject
    template_name = "capital_project/capital_project_delete.html"
    context_object_name = "project"
    success_url = reverse_lazy("capital_projects:projects")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = reverse(
            "capital_projects:project_detail", kwargs={"pk": self.object.pk}
        )
        return context


CAPITAL_ACQUISITION_SEARCH_FIELDS = ["code", "name"]


class CapitalAcquisitionFilterView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    FilteredTableView
):
    model = CapitalAcquisition
    permission_required = "capital_project.view_capitalacquisition"
    title = 'Acquisitions' 
    open_column = 'code'
    table_class = None
    paginate_by = 25
    universal_search_fields = CAPITAL_ACQUISITION_SEARCH_FIELDS
    default_columns = [
        "code",
        "name",
        "statusid",
        "typeid",
        "startdate",
        "enddate",
    ]
    actions = [
    TableAction(
            name='Add',
            type='link',
            url=reverse_lazy('capital_projects:acquisition_create'),
            permission='capital_project.add_capitalacquisition',
            icon='bi-plus',
            color='outline-secondary'
        )
    ]


class CapitalAcquisitionDetailView(DetailView):
    model = CapitalAcquisition
    template_name = "capital_project/acquisition_detail.html"
    context_object_name = "acquisition"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["request_count"] = self.object.commission_request.all().count()
        return context


class CapitalAcquisitionCreateView(CreateView):
    model = CapitalAcquisition
    fields = "__all__"
    template_name = "capital_project/acquisition_create.html"
    context_object_name = "acquisition"

    def get_initial(self):
        initial = super().get_initial()
        initial.update(**self.request.GET)
        return initial

    def get_success_url(self):
        return reverse(
            "capital_projects:acquisition_detail", kwargs={"pk": self.object.pk}
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = reverse("capital_projects:acquisitions")
        return context


class CapitalAcquisitionUpdateView(UpdateView):
    model = CapitalAcquisition
    fields = "__all__"
    template_name = "capital_project/acquisition_update.html"
    context_object_name = "acquisition"

    def get_success_url(self):
        return reverse(
            "capital_projects:acquisition_detail", kwargs={"pk": self.object.pk}
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = reverse(
            "capital_projects:acquisition_detail", kwargs={"pk": self.object.pk}
        )
        return context


class CapitalAcquisitionDeleteView(DeleteView):
    model = CapitalAcquisition
    template_name = "capital_project/acquisition_delete.html"
    context_object_name = "project"

    def get_success_url(self):
        return reverse(
            "capital_projects:project_detail",
            kwargs={"pk": self.object.capitalproject.pk},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = reverse(
            "capital_projects:acquisition_detail", kwargs={"pk": self.object.pk}
        )
        return context


COMMISSION_REQUEST_SEARCH_FIELDS = ["code", "capital_acquisition"]


class CommissionRequestFilterView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    FilteredTableView
):
    paginate_by = 25
    title = 'Commission Requests'
    permission_required = "capital_project.view_commissionrequest"
    model = CommissionRequest
    open_column = 'code'
    table_class = None
    universal_search_fields = COMMISSION_REQUEST_SEARCH_FIELDS
    default_columns = [
        "code",
        "name",
        "statusid",
        "typeid",
        "startdate",
        "enddate",
    ]
    actions = [
    TableAction(
            name='Add',
            type='link',
            url=reverse_lazy('capital_projects:commission_request_create'),
            permission='capital_project.add_commissionrequest',
            icon='bi-plus',
            color='outline-secondary'
        )
    ]


class CommissionRequestDetailView(DetailView):
    permission_required = "capital_project.view_commissionrequest"
    model = CommissionRequest
    template_name = "capital_project/commission_request_detail.html"
    context_object_name = "request"


class CommissionRequestCreateView(CreateView):
    permission_required = "capital_project.add_commissionrequest"
    model = CommissionRequest
    fields = "__all__"
    template_name = "capital_project/commission_request_create.html"
    context_object_name = "request"

    def get_initial(self):
        initial = super().get_initial()
        initial.update(**self.request.GET)
        return initial

    def get_success_url(self):
        return reverse(
            "capital_projects:commission_request_detail", kwargs={"pk": self.object.pk}
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = reverse("capital_projects:commission_requests")
        return context


class CommissionRequestUpdateView(UpdateView):
    permission_required = "capital_project.change_commissionrequest"
    model = CommissionRequest
    fields = "__all__"
    template_name = "capital_project/commission_request_update.html"
    context_object_name = "request"

    def get_success_url(self):
        return reverse(
            "capital_projects:commission_request_detail", kwargs={"pk": self.object.pk}
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = reverse(
            "capital_projects:commission_request_detail", kwargs={"pk": self.object.pk}
        )
        return context


class CommissionRequestDeleteView(DeleteView):
    permission_required = "capital_project.delete_commissionrequest"
    model = CommissionRequest
    template_name = "capital_project/commission_request_delete.html"
    context_object_name = "request"

    def get_success_url(self):
        return reverse(
            "capital_projects:acquisition_detail",
            kwargs={"pk": self.object.capital_acquisition.pk},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = reverse("capital_projects:commission_requests")
        return context
