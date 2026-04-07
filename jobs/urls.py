from django.urls import path
from .views import (
    FilteredJobTableView,
    JobUpdateView,
    JobDetailView,
    JobCreateView,
    JobDeleteView,
    TestsCarriedOutView,
    TestsCarriedOutUpdate,
    TestsCarriedOutCreate,
    TestsCarriedOutDelete,
    SparePartsUsedListView,
    SparePartsUsedUpdate,
    SparePartsUsedDelete,
    SparePartsUsedCreateView,
    TestEquipmentUsedListView,
    TestEquipmentUsedCreate,
    TestEquipmentUsedDelete,
    GenerateReportView,
    SparePartsUsedDetail,
    JobBulkUpdateView,
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
    path("testscarriedout/", TestsCarriedOutView.as_view(), name="testscarriedout"),
    path(
        "testscarriedout_update/<int:pk>/",
        TestsCarriedOutUpdate.as_view(),
        name="testscarriedout_update",
    ),
    path(
        "testscarriedout_create/<int:jobid>/",
        TestsCarriedOutCreate.as_view(),
        name="testscarriedout_create",
    ),
    path(
        "testscarriedout_delete/<int:pk>/",
        TestsCarriedOutDelete.as_view(),
        name="testscarriedout_delete",
    ),
    path("sparepartsused/", SparePartsUsedListView.as_view(), name="sparepartsused"),
    path(
        "sparepartsused/<int:pk>/detail",
        SparePartsUsedDetail.as_view(),
        name="sparepartsused_detail",
    ),
    path(
        "sparepartsused_update/<int:pk>/",
        SparePartsUsedUpdate.as_view(),
        name="sparepartsused_update",
    ),
    path(
        "sparepartsused_delete/<int:pk>/",
        SparePartsUsedDelete.as_view(),
        name="sparepartsused_delete",
    ),
    path(
        "sparepartused_create/<int:jobid>/",
        SparePartsUsedCreateView.as_view(),
        name="sparepartsused_create",
    ),
    path(
        "testequipmentused/",
        TestEquipmentUsedListView.as_view(),
        name="testequipmentused",
    ),
    path(
        "testequipmentused_delete/<int:pk>/",
        TestEquipmentUsedDelete.as_view(),
        name="testequipmentused_delete",
    ),
    path(
        "testequipmentused_create/<int:jobid>/",
        TestEquipmentUsedCreate.as_view(),
        name="testequipmentused_create",
    ),
]
