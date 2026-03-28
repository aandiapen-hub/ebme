from django.urls import path
from .views import (
    DocumentAndLinkCreateView,
    DocumentLinksTableView,
    DocumentsTableView,
    DocumentDownloadView,
    DocumentLinkDeleteView,
    DocumentListView,
    DocumentLinkUpdateView,
    DocumentUpdateView,
    DocumentPreView,
    TempUploadListView,
    TempUploadDetailView,
    TemporaryUploadCreateView,
    TempFilesDeleteAllView,
    TempFilesDeleteView,
    QuickScanner,
    LinkTemporaryDocumentView,
    GetExtractedData,
    UpdateExtractedData,
    ExtractedDateDeleteView,
)


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
        "documents/download/<int:pk>/",
        DocumentDownloadView.as_view(),
        name="download_document",
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
        "documents/<int:pk>/update",
        DocumentUpdateView.as_view(),
        name="update_document",
    ),
    path("user_temp_files/", TempUploadListView.as_view(), name="user_temp_files"),
    path("temp_files/<int:pk>", TempUploadDetailView.as_view(), name="temp_file"),
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
        "documents/extracted_data/<int:group>",
        GetExtractedData.as_view(),
        name="get_extracted_data",
    ),
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
]
