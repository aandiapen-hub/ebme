from django.urls import path
from .views import (AssetCreateView,
                    FilteredAssetTableView,
                    Asset,
                    AssetUpdateView,
                    AssetDeleteView,
                    AssetJobsListView,
                    AssetBulkUpdateView,
                    QuickBrandCreateView,
                    QuickCategoryCreateView,
                    QuickModelGtinUpdate)


app_name = 'assets'
urlpatterns = [
    path("create_asset/",AssetCreateView.as_view(),name='create_asset'),
    path("asset/<int:pk>",Asset.as_view(),name='view_asset'),
    path("asset/<int:pk>/update",AssetUpdateView.as_view(),name='update_asset'),
    path("delete_asset/<int:pk>",AssetDeleteView.as_view(),name="delete_asset"),
    path("assets/",FilteredAssetTableView.as_view(),name='assets_list'),
    path("jobsummary/<int:assetid>/", AssetJobsListView.as_view(), name="asset_jobs"),
    path("bulk_update/",AssetBulkUpdateView.as_view(),name='bulk_update_assets'),
    #utils

    path("quickbrandcreate/",QuickBrandCreateView.as_view(),name='quick_create_brand'),
    path("quickcategorycreate/",QuickCategoryCreateView.as_view(),name='quick_create_category'),
    path("quickmodelgtinupdate/<int:pk>/",QuickModelGtinUpdate.as_view(),name="quick_update_model"),

]   
