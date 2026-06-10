from django.urls import path
from .views import (AssetCreateView,
                    FilteredAssetTableView,
                    AssetDetailView,
                    AssetUpdateView,
                    AssetDeleteView,
                    AssetBulkUpdateView,
)


app_name = 'assets'
urlpatterns = [
    path("create_asset/",AssetCreateView.as_view(),name='create_asset'),
    path("asset/<int:pk>",AssetDetailView.as_view(),name='view_asset'),
    path("asset/<int:pk>/update",AssetUpdateView.as_view(),name='update_asset'),
    path("delete_asset/<int:pk>",AssetDeleteView.as_view(),name="delete_asset"),
    path("assets/",FilteredAssetTableView.as_view(),name='assets_list'),
    path("bulk_update/",AssetBulkUpdateView.as_view(),name='bulk_update_assets'),
    #utils

]   
