from django.shortcuts import render

# Create your views here.
from django.urls import reverse,reverse_lazy

#get models from asset model file
from assets.models import AssetView, JobView


#import data analysis libraries
import pandas as pd

#import plotly libraries
import plotly.express as px

import django_tables2 as tables
from django_tables2.views import SingleTableView
from django.views.generic import TemplateView, ListView

from django.contrib.auth.mixins import LoginRequiredMixin
from assets.mixins import CustomerAssetPermissionMixin
from jobs.mixins import CustomerJobListPermissionMixin


class ModelComplianceTable(tables.Table):
    model = tables.Column()
    modelid = tables.Column(visible=False)
    Percentage = tables.Column()

    class Meta:
        template_name = "dashboards/tables/model_compliance_table.html"


class CategoryComplianceTable(tables.Table):
    category = tables.Column()
    categoryid = tables.Column(visible=False)
    Percentage = tables.Column()

    class Meta:
        template_name = "dashboards/tables/category_compliance_table.html"


class DashboardTemplateView(LoginRequiredMixin,
                           TemplateView):
    template_name = 'dashboards/overview.html'


class BaseComplianceView(
    LoginRequiredMixin,
    CustomerAssetPermissionMixin,
    SingleTableView
):
    table_pagination = False  # Disable pagination by default
    compliance_field = 'ppm_compliance'
    asset_id_field = 'assetid'
    group_by_fields = None
    model_field_map = None
    filter_compliant_value = 'compliant'  # Default compliance value to filter
    template_name = "dashboards/partials/compliance.html"

    def get_queryset(self):
        qs = super().get_queryset()
        values_fields = self.group_by_fields + [self.compliance_field, self.asset_id_field]
        df = pd.DataFrame.from_records(qs.values(*values_fields))

        if df.empty:
            return []

        # Group by asset type and compliance status
        group_cols = self.group_by_fields + [self.compliance_field]
        grouped = df.groupby(group_cols, group_keys=False)[self.asset_id_field].count().to_frame()

        # Calculate percentage per model (excluding compliance status)
        percentage = grouped.groupby(level=0).apply(lambda x: 100 * x / x.sum()).round(2)
        percentage.index = percentage.index.droplevel(0)
        percentage = percentage.reset_index()

        # Rename fields for table display
        percentage.rename(columns={self.asset_id_field: 'Percentage'}, inplace=True)
        for old_name, new_name in self.model_field_map.items():
            percentage.rename(columns={old_name: new_name}, inplace=True)

        # Sort and filter
        percentage = percentage.sort_values(by='Percentage', ascending=False)
        output = percentage[percentage[self.compliance_field] == self.filter_compliant_value]
        return output.to_dict(orient='records')

    def get_template_names(self):
        if self.request.htmx:
            return [self.template_name + "#table-partial"]
        return [self.template_name]


class ModelComplianceView(BaseComplianceView):
    model = AssetView
    permission_required = 'assets.view_assetview'
    table_class = ModelComplianceTable
    group_by_fields = ['modelname', 'modelid']
    model_field_map = {'modelname': 'model'}  # Field renames for output


class CategoryComplianceView(BaseComplianceView):
    model = AssetView
    permission_required = 'assets.view_assetview'
    table_class = CategoryComplianceTable
    group_by_fields = ['categoryname', 'categoryid']
    model_field_map = {'categoryname': 'category'}


class AssetComplianceView(
    LoginRequiredMixin,
    CustomerAssetPermissionMixin,
    ListView
):
    model = AssetView
    compliance_field = 'ppm_compliance'
    asset_id_field = 'assetid'
    template_name = 'dashboards/partials/asset_overall_compliance.html'
    permission_required = 'assets.view_assetview'


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
    
        qs = super().get_queryset()
        values_fields = [self.compliance_field, self.asset_id_field]
        df = pd.DataFrame.from_records(qs.values(*values_fields))

        # Group by asset type and compliance status
        group_cols = self.compliance_field
        grouped = df.groupby(group_cols, group_keys=False)[self.asset_id_field].count().to_frame()
        
        context['total_assets'] = grouped['assetid'].sum()
        # Calculate percentage per model (excluding compliance status)
        grouped['percentage'] = (grouped['assetid']/grouped['assetid'].sum())*100
        context['compliant_assets'] = grouped.loc['compliant']['assetid']
        context['non_compliant_assets'] = grouped.loc['non-compliant']['assetid']
        context['percentage_compliance'] = grouped.loc['compliant']['percentage']

        return context

class OpenJobsView(LoginRequiredMixin,
                    CustomerJobListPermissionMixin,
                    ListView):
    model = JobView
    template_name = 'dashboards/partials/open_jobs.html'
    permission_required = 'assets.view_jobview'


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
    
        qs = super().get_queryset().filter(jobstatusid__in=[0,2,3,5])
        values_fields = ['jobid','jobtypename','jobstatus','jobstatusid','jobtypeid']
        group_cols = ['jobtypename','jobstatus','jobstatusid','jobtypeid']
        df = pd.DataFrame.from_records(qs.values(*values_fields))
        
        grouped = df.groupby(group_cols, group_keys=False)['jobid'].count().to_frame()
        grouped = grouped.rename(columns={'jobid': 'count'})
        context['total_jobs'] = grouped['count'].sum()
        # Calculate percentage per model (excluding compliance status)
        nested = {}
        for (jobtypename, jobstatus,jobstatusid,jobtypeid), row in grouped.iterrows():
            nested.setdefault(jobtypename, []).append({
                'jobstatus': jobstatus,
                'jobtypeid':jobtypeid,
                'jobstatusid':jobstatusid,
                'count': row['count'],
            })

        context['details'] = nested

        return context
