from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from .models import(
    CapitalProject,
    CapitalAcquisition,
    CommissionRequest,
    CapitalProjectEquipment
)

from utils.generic_views import FilteredTableView

from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    UpdateView,
    ListView,
    TemplateView,
)


CAPITAL_PROJECT_SEARCH_FIELDS = [
    'code',
    'name'
]
class CapitalProjectFilterView(FilteredTableView):

    paginate_by = 25
    permission_required = "capital_project.view_capitalproject"
    table_class = None
    model = CapitalProject
    template_columns = {"open": "capital_project/tables/capital_prject_open.html"}
    template_name = "capital_project/capital_projects.html"
    universal_search_fields = CAPITAL_PROJECT_SEARCH_FIELDS
    default_columns = [
        'code',
        'name',
        'statusid',
        'typeid',
        'startdate',
        'enddate',
    ]
    bulk_actions = {
    }

class CapitalProjectDetailView(DetailView):
    model = CapitalProject
    template_name = "capital_project/capital_project_detail_view.html"
    context_object_name = 'project'



class CapitalProjectCreateView(CreateView):
    model = CapitalProject
    fields = '__all__'
    template_name = "capital_project/capital_project_create_view.html"
    context_object_name = 'project'

    def get_success_url(self):
        return reverse('capital_projects:project_detail', kwargs={'pk':self.object.pk})

class CapitalProjectUpdateView(UpdateView):
    model = CapitalProject
    fields = '__all__'
    template_name = "capital_project/capital_project_update_view.html"
    context_object_name = 'project'

    def get_success_url(self):
        return reverse('capital_projects:project_detail', kwargs={'pk':self.object.pk})

class CapitalProjectDeleteView(DeleteView):
    model = CapitalProject
    template_name = "capital_project/capital_project_delete_view.html"
    context_object_name = 'project'
    success_url = reverse_lazy('capital_projects:projects')


CAPITAL_ACQUISITION_SEARCH_FIELDS = [
    'code',
    'name'
]
class CapitalAcquisitionFilterView(FilteredTableView):

    paginate_by = 25
    permission_required = "capital_project.view_capitalacquisition"
    table_class = None
    model = CapitalAcquisition
    template_columns = {"open": "capital_project/tables/acquisition_open.html"}
    template_name = "capital_project/acquisitions.html"
    universal_search_fields = CAPITAL_ACQUISITION_SEARCH_FIELDS
    default_columns = [
        'code',
        'name',
        'statusid',
        'typeid',
        'startdate',
        'enddate',
    ]
    bulk_actions = {
    }

class CapitalAcquisitionDetailView(DetailView):
    model = CapitalAcquisition
    template_name = "capital_project/acquisition_detail_view.html"
    context_object_name = 'acquisition'


class CapitalAcquisitionCreateView(CreateView):
    model = CapitalAcquisition
    fields = '__all__'
    template_name = "capital_project/acquisition_create_view.html"
    context_object_name = 'project'

    def get_success_url(self):
        return reverse('capital_projects:project_detail', kwargs={'pk':self.object.capitalproject.pk})

class CapitalAcquisitionUpdateView(UpdateView):
    model = CapitalAcquisition
    fields = '__all__'
    template_name = "capital_project/acquisition_update_view.html"
    context_object_name = 'project'

    def get_success_url(self):
        return reverse('capital_projects:project_detail', kwargs={'pk':self.object.capitalproject.pk})

class CapitalAcquisitionDeleteView(DeleteView):
    model = CapitalAcquisition
    template_name = "capital_project/acquisition_delete_view.html"
    context_object_name = 'project'

    def get_success_url(self):
        return reverse('capital_projects:project_detail', kwargs={'pk':self.object.capitalproject.pk})



COMMISSION_REQUEST_SEARCH_FIELDS = [
    'code',
    'capital_acquisition'
]
class CommissionRequestFilterView(FilteredTableView):

    paginate_by = 25
    permission_required = "capital_project.view_commissionrequest"
    model = CommissionRequest
    table_class = None
    template_columns = {"open": "capital_project/tables/commission_request_open.html"}
    template_name = "capital_project/commission_requests.html"
    universal_search_fields = COMMISSION_REQUEST_SEARCH_FIELDS
    default_columns = [
        'code',
        'name',
        'statusid',
        'typeid',
        'startdate',
        'enddate',
    ]
    bulk_actions = {
    }

class CommissionRequestDetailView(DetailView):
    permission_required = "capital_project.view_commissionrequest"
    model = CommissionRequest
    template_name = "capital_project/commission_request_detail_view.html"
    context_object_name = 'acquisition'


class CommissionRequestCreateView(CreateView):
    permission_required = "capital_project.add_commissionrequest"
    model = CommissionRequest
    fields = '__all__'
    template_name = "capital_project/commission_request_create_view.html"
    context_object_name = 'request'

    def get_success_url(self):
        return reverse('capital_projects:project_detail', kwargs={'pk':self.object.capitalproject.pk})

class CommissionRequestUpdateView(UpdateView):
    permission_required = "capital_project.change_commissionrequest"
    model = CommissionRequest
    fields = '__all__'
    template_name = "capital_project/commission_request_update_view.html"
    context_object_name = 'request'

    def get_success_url(self):
        return reverse('capital_projects:project_detail', kwargs={'pk':self.object.capitalproject.pk})

class CommissionRequestDeleteView(DeleteView):
    permission_required = "capital_project.delete_commissionrequest"
    model = CommissionRequest
    template_name = "capital_project/commission_request_delete_view.html"
    context_object_name = 'request'

    def get_success_url(self):
        return reverse('capital_projects:project_detail', kwargs={'pk':self.object.capitalproject.pk})
