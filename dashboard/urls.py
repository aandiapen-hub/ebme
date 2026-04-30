from django.urls import path

from .views import (DashboardTemplateView,
                    ModelComplianceView,
                    CategoryComplianceView,
                    AssetComplianceView,
                    OpenJobsView)


app_name = 'dashboards'

urlpatterns = [
    path('overview/', DashboardTemplateView.as_view(), name='overview'),
    path('model_compliance/', ModelComplianceView.as_view(), name='model_compliance'),
    path('category_compliance/', CategoryComplianceView.as_view(), name='category_compliance'),
    path('asset_compliance/', AssetComplianceView.as_view(), name='asset_compliance'),
    path('open_jobs/',OpenJobsView.as_view(),name='open_jobs')
]