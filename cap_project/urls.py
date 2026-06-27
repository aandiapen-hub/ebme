from django.urls import path
from .views import(
    CapitalProjectFilterView,
    CapitalProjectCreateView,
    CapitalProjectDetailView,
    CapitalProjectUpdateView,
    CapitalProjectDeleteView,
    CapitalAcquisitionFilterView,
    CapitalAcquisitionCreateView,
    CapitalAcquisitionDetailView,
    CapitalAcquisitionUpdateView,
    CapitalAcquisitionDeleteView,
)


app_name = 'capital_projects'
urlpatterns = [
    path("projects/",CapitalProjectFilterView.as_view(),name='projects'),
    path("projects/create/",CapitalProjectCreateView.as_view(),name='project_create'),
    path("projects/<int:pk>/detail",CapitalProjectDetailView.as_view(),name='project_detail'),
    path("projects/<int:pk>/update",CapitalProjectUpdateView.as_view(),name='project_update'),
    path("projects/<int:pk>/delete",CapitalProjectDeleteView.as_view(),name='project_delete'),


    path("acquisitions/",CapitalAcquisitionFilterView.as_view(),name='acquisitions'),
    path("acquisitions/create/",CapitalAcquisitionCreateView.as_view(),name='acquisition_create'),
    path("acquisitions/<int:pk>/detail",CapitalAcquisitionDetailView.as_view(),name='acquisition_detail'),
    path("acquisitions/<int:pk>/update",CapitalAcquisitionUpdateView.as_view(),name='acquisition_update'),
    path("acquisitions/<int:pk>/delete",CapitalAcquisitionDeleteView.as_view(),name='acquisition_delete'),
]
