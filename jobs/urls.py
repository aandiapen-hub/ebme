from django.urls import path
from .views import (
    FilteredJobTableView,
    JobUpdateView,
    JobDetailView,
    JobCreateView,
    JobDeleteView,
    GenerateReportView,
    JobBulkUpdateView,
    AddFormsetRowView,
    TestEqListView,
    SparePartsListView
)

app_name = "jobs"

urlpatterns = [
    path("jobs/", FilteredJobTableView.as_view(), name="jobs_list"),
    path("job_update/<int:pk>/", JobUpdateView.as_view(), name="job_update"),
    path("job_summary/<int:pk>/", JobDetailView.as_view(), name="job_summary"),
    path("job_create/", JobCreateView.as_view(), name="job_create"),
    path("job_delete/<int:pk>", JobDeleteView.as_view(), name="job_delete"),
    path("jobs/generate-report", GenerateReportView.as_view(), name="gen_report"),
    # bulk update job
    path("job_bulk_update", JobBulkUpdateView.as_view(), name="bulk_update_jobs"),
    path("jobs/test_eq_list", TestEqListView.as_view(), name="test_eq_list"),
    path("jobs/parts_list", SparePartsListView.as_view(), name="parts_list"),
    path("jobs/add_formset_row/<str:formset_type>/", AddFormsetRowView.as_view(), name="add_formset_row"),
]
