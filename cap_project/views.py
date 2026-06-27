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
    template_columns = {"open": "capital_project/tables/capital_project_open.html"}
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
    template_name = "capital_project/capital_project_detail.html"
    context_object_name = 'project'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_project_count'] = self.object.acquisition.all().count()

        return context


class CapitalProjectCreateView(CreateView):
    model = CapitalProject
    fields = '__all__'
    template_name = "capital_project/capital_project_create.html"
    context_object_name = 'project'

    def get_success_url(self):
        
        return reverse('capital_projects:project_detail', kwargs={'pk':self.object.pk})

class CapitalProjectUpdateView(UpdateView):
    model = CapitalProject
    fields = '__all__'
    template_name = "capital_project/capital_project_update.html"
    context_object_name = 'project'

    def get_success_url(self):
        return reverse('capital_projects:project_detail', kwargs={'pk':self.object.pk})

class CapitalProjectDeleteView(DeleteView):
    model = CapitalProject
    template_name = "capital_project/capital_project_delete.html"
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
    template_name = "capital_project/acquisition_detail.html"
    context_object_name = 'acquisition'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['request_count'] = self.object.commission_request.all().count()
        return context



class CapitalAcquisitionCreateView(CreateView):
    model = CapitalAcquisition
    fields = '__all__'
    template_name = "capital_project/acquisition_create.html"
    context_object_name = 'acquisition'
    
    def get_initial(self):
        initial = super().get_initial()
        initial.update(**self.request.GET)
        return initial

    def get_success_url(self):
        return reverse('capital_projects:acquisition_detail', kwargs={'pk':self.object.pk})

class CapitalAcquisitionUpdateView(UpdateView):
    model = CapitalAcquisition
    fields = '__all__'
    template_name = "capital_project/acquisition_update.html"
    context_object_name = 'acquisition'

    def get_success_url(self):
        return reverse('capital_projects:acquisition_detail', kwargs={'pk':self.object.pk})

class CapitalAcquisitionDeleteView(DeleteView):
    model = CapitalAcquisition
    template_name = "capital_project/acquisition_delete.html"
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
    template_name = "capital_project/commission_request_detail.html"
    context_object_name = 'request'


class CommissionRequestCreateView(CreateView):
    permission_required = "capital_project.add_commissionrequest"
    model = CommissionRequest
    fields = '__all__'
    template_name = "capital_project/commission_request_create.html"
    context_object_name = 'request'

    def get_initial(self):
        initial = super().get_initial()
        initial.update(**self.request.GET)
        return initial

    def get_success_url(self):
        return reverse('capital_projects:commission_request_detail', kwargs={'pk':self.object.pk})

class CommissionRequestUpdateView(UpdateView):
    permission_required = "capital_project.change_commissionrequest"
    model = CommissionRequest
    fields = '__all__'
    template_name = "capital_project/commission_request_update.html"
    context_object_name = 'request'

    def get_success_url(self):
        return reverse('capital_projects:commission_request_detail', kwargs={'pk':self.object.pk})

class CommissionRequestDeleteView(DeleteView):
    permission_required = "capital_project.delete_commissionrequest"
    model = CommissionRequest
    template_name = "capital_project/commission_request_delete.html"
    context_object_name = 'request'

    def get_success_url(self):
        return reverse('capital_projects:acquisition_detail', kwargs={'pk':self.object.capital_acquisition.pk})
