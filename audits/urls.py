from audits.models import AuditLocation
from django.urls import path

from .views import (
    AuditListView,
    AuditCreateView,
    AuditDetailView,
    AuditLocationListView,
    AuditLocationDetailView,
    AuditItemListView,
    AuditItemDetailView,
    AuditItemVerifiedView,
    ModelProposalCreateView,
    BrandProposalCreateView,
    CategoryProposalCreateView,
    CatalogProposalListView,
    CatalogProposalDetailView,
    CatalogProposalReviewView,
    AssetChangeProposalCreateView,
    AssetChangeProposalReviewView,
)

app_name = "audits"

urlpatterns = [
    # Audits
    path("", AuditListView.as_view(), name="audit_list"),
    path("create/", AuditCreateView.as_view(), name="audit_create"),
    path("<int:pk>/", AuditDetailView.as_view(), name="audit_detail"),
    path("audit_location/<int:pk>/", AuditLocationDetailView.as_view(), name="audit_location_detail"),
    path("audit_location/", AuditLocationListView.as_view(), name="audit_location_list"),

    # Audit Items
    path("audit_item/", AuditItemListView.as_view(), name="audit_item_list"),
    path("audit_item/<int:pk>/", AuditItemDetailView.as_view(), name="audit_item_detail"),
    path("audit_item/<int:pk>/verified/", AuditItemVerifiedView.as_view(), name="audit_item_verified"),

    # Shared catalogue proposals
    path(
        "catalogue/proposals/",
        CatalogProposalListView.as_view(),
        name="catalog_proposal_list",
    ),
    path(
        "catalogue/proposals/create_model/",
        ModelProposalCreateView.as_view(),
        name="model_proposal_create",
    ),
    path(
        "catalogue/proposals/create_brand/",
        BrandProposalCreateView.as_view(),
        name="brand_proposal_create",
    ),
    path(
        "catalogue/proposals/create_category/",
        CategoryProposalCreateView.as_view(),
        name="category_proposal_create",
    ),
    path(
        "catalogue/proposals/<int:pk>/",
        CatalogProposalDetailView.as_view(),
        name="catalog_proposal_detail",
    ),
    path(
        "catalogue/proposals/<int:pk>/review/",
        CatalogProposalReviewView.as_view(),
        name="catalog_proposal_review",
    ),

    # Asset change proposals
    path(
        "asset_changes/<int:pk>/create/",
        AssetChangeProposalCreateView.as_view(),
        name="asset_change_create",
    ),
    path(
        "asset-changes/<int:pk>/review/",
        AssetChangeProposalReviewView.as_view(),
        name="asset_change_review",
    ),
]
