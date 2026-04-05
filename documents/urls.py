from django.urls import path
from .views import (
    DocumentAndLinkCreateView,
    DocumentLinksTableView,
    DocumentsTableView,
    DocumentDownloadFromLinkView,
    DocumentLinkDeleteView,
    DocumentListView,
    DocumentLinkUpdateView,
    DocumentDetailView,
    DocumentUpdateView,
    DocumentDeleteView,
    DocumentDownloadView,
    DocumentPreView,
    TempUploadListView,
    TempUploadGroupView,
    TemporaryUploadCreateView,
    TempFilesDeleteAllView,
    TempFilesDeleteView,
    QuickScanner,
    LinkTemporaryDocumentView,
    UpdateExtractedData,
    ExtractedDateDeleteView,
    BulkLinkDocument,
    BulkDeleteLink,
)

from assets.views import UNIVERSAL_SEARCH_FIELDS as ASSET_UNIVERSAL_SEARCH_FIELDS
from jobs.views import SEARCHFILEDS as JOB_UNIVERSAL_SEARCH_FIELDS
from assets.models import AssetView, JobView

app_name = "documents"

urlpatterns = [
    path(
        "table_document_links/",
        DocumentLinksTableView.as_view(),
        name="table_document_links",
    ),
    path("table_documents/", DocumentsTableView.as_view(), name="table_documents"),
    path(
        "document_links/create/",
        DocumentAndLinkCreateView.as_view(),
        name="create_document_link",
    ),
    path(
        "documents/downloadfromlink/<int:pk>/",
        DocumentDownloadFromLinkView.as_view(),
        name="download_document_from_link",
    ),
    path(
        "document_links/<int:pk>/delete/",
        DocumentLinkDeleteView.as_view(),
        name="delete_document_link",
    ),
    path("list_documents/", DocumentListView.as_view(), name="list_documents"),
    path(
        "document_links/<int:pk>/update/",
        DocumentLinkUpdateView.as_view(),
        name="update_document_link",
    ),
    path(
        "documents/<int:pk>/",
        DocumentDetailView.as_view(),
        name="view_document",
    ),
    path(
        "documents/<int:pk>/download",
        DocumentDownloadView.as_view(),
        name="download_document",
    ),
    path(
        "documents/<int:pk>/update",
        DocumentUpdateView.as_view(),
        name="update_document",
    ),
    path(
        "documents/<int:pk>/delete",
        DocumentDeleteView.as_view(),
        name="delete_document",
    ),
    path("user_temp_files/", TempUploadListView.as_view(), name="user_temp_files"),
    path("temp_files/<int:pk>", TempUploadGroupView.as_view(), name="temp_group"),
    path("temp_files/load_image/", DocumentPreView.as_view(), name="load_image"),
    path(
        "temp_files/delete_all/",
        TempFilesDeleteAllView.as_view(),
        name="delete_all_temp_files",
    ),
    path(
        "temp_files/delete/<int:pk>/",
        TempFilesDeleteView.as_view(),
        name="delete_temp_file",
    ),
    path(
        "temp_document_create_link/",
        LinkTemporaryDocumentView.as_view(),
        name="link_temporary_document",
    ),
    path(
        "temp_files/create/",
        TemporaryUploadCreateView.as_view(),
        name="create_temp_files",
    ),
    path("documents/quickscanner/", QuickScanner.as_view(), name="quick_scanner"),
    path(
        "documents/extracted_data/<int:temp_file_group>/update",
        UpdateExtractedData.as_view(),
        name="update_extracted_data",
    ),
    path(
        "documents/extracted_data/<str:group>/delete",
        ExtractedDateDeleteView.as_view(),
        name="delete_extracted_data",
    ),
    #  bulk document create links
    path(
        "documents/bulk_link_assets/",
        BulkLinkDocument.as_view(
            model=AssetView,
            universal_search_fields=ASSET_UNIVERSAL_SEARCH_FIELDS,
            success_view="assets:assets_list",
        ),
        name="bulk_link_to_assets",
    ),
    path(
        "documents/bulk_link_jobs/",
        BulkLinkDocument.as_view(
            model=JobView,
            universal_search_fields=JOB_UNIVERSAL_SEARCH_FIELDS,
            success_view="jobs:jobs_list",
        ),
        name="bulk_link_to_jobs",
    ),
    path(
        "documents/bulk_delete_link",
        BulkDeleteLink.as_view(),
        name="bulk_delete_links",
    ),
]
