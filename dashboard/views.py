from django.db.models import Count, Q, FloatField, F
from django.db.models.expressions import ExpressionWrapper
# Create your views here.

#get models from asset model file
from assets.models import AssetView, JobView


#import data analysis libraries

import django_tables2 as tables
from django_tables2.views import SingleTableView
from django.views.generic import TemplateView, ListView

from django.contrib.auth.mixins import LoginRequiredMixin
from assets.mixins import CustomerAssetPermissionMixin
from jobs.mixins import CustomerJobListPermissionMixin


class ModelComplianceTable(tables.Table):
    modelname = tables.Column()
    modelid = tables.Column(visible=False)
    Percentage = tables.Column()

    class Meta:
        template_name = "dashboards/tables/model_compliance_table.html"


class CategoryComplianceTable(tables.Table):
    categoryname = tables.Column()
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
        qs = (
            super()
            .get_queryset()
            .values(*self.group_by_fields)
            .annotate(
                total=Count(self.asset_id_field),
                compliant=Count(
                    self.asset_id_field,
                    filter=Q(**{self.compliance_field: self.filter_compliant_value}),
                ),
            )
            .annotate(
                Percentage=ExpressionWrapper(
                    100.0 * F("compliant") / F("total"),
                    output_field=FloatField(),
                )
            )
            .order_by("-Percentage")
        )
        return qs

    def get_template_names(self):
        if self.request.htmx:
            return [self.template_name + "#table-partial"]
        return [self.template_name]


class ModelComplianceView(BaseComplianceView):
    model = AssetView
    permission_required = 'assets.view_assetview'
    table_class = ModelComplianceTable
    group_by_fields = ['modelid__modelname', 'modelid']


class CategoryComplianceView(BaseComplianceView):
    model = AssetView
    permission_required = 'assets.view_assetview'
    table_class = CategoryComplianceTable
    group_by_fields = ['categoryid__categoryname', 'categoryid']


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
    compliant_value = 'compliant'


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = super().get_queryset()

        overall = qs.aggregate(
            total = Count(self.asset_id_field),
            compliant_count = Count(
                self.asset_id_field,
                filter=Q(**{self.compliance_field: self.compliant_value})
            )
        )
        context['percentage_compliance'] = (
                100.0 * overall['compliant_count']/overall['total']
                if overall['total'] else 0
        )
        context['overall'] = overall

        return context

class OpenJobsView(LoginRequiredMixin,
                    CustomerJobListPermissionMixin,
                    ListView):
    model = JobView
    template_name = 'dashboards/partials/open_jobs.html'
    permission_required = 'assets.view_jobview'

    def get_queryset(self):
        qs = (
            super()
            .get_queryset()
            .filter(jobstatusid__in=[0,2,3,5])
            .values(
                "jobtypeid__jobtypename",
                "jobstatusid__jobstatusname",
                "jobstatusid",
                "jobtypeid",
            ).
            annotate(count=Count('pk'))
        )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["total_jobs"] = (
            super()
            .get_queryset()
            .filter(jobstatusid__in=[0, 2, 3, 5])
            .count()
        )
        return context
