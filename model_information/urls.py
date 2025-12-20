from django.urls import path

from .views import (FilteredBrandTableView,
                    BrandUpdateView,
                    BrandBulkUpdateView,
                    BrandCreateView,
                    BrandDeleteView,
                    FilteredModelTableView,
                    ModelUpdateView,
                    ModelBulkUpdateView,
                    ModelCreateView,
                    ModelDeleteView,
                    ModelDetailView,
                    ExistingModelListView,
                    FilteredCategoryTableView,
                    CategoryUpdateView,
                    CategoryCreateView,
                    CategoryDeleteView,
                    ChecklistsTableView,
                    CheckUpdateView,
                    CheckDeleteView,
                    CheckCreateView,
)


app_name = "model_information"

urlpatterns = [
    path("brandlist/",FilteredBrandTableView.as_view(),name='brandlist'),
    path("update_brand/<int:pk>",BrandUpdateView.as_view(),name='update_brand'),
    #path("bulk_brand_update",BrandBulkUpdateView.as_view(),name='bulk_update_brands'),
    path("create_brand/",BrandCreateView.as_view(),name='create_brand'),
    path("delete_brand/<int:pk>",BrandDeleteView.as_view(),name='delete_brand'),

    path("modellist/",FilteredModelTableView.as_view(),name='modellist'),
    path("existing_modellist/",ExistingModelListView.as_view(),name='existing_modellist'),
    path("update_model/<int:pk>",ModelUpdateView.as_view(),name='update_model'),
    path("bulk_brand_model",ModelBulkUpdateView.as_view(),name='bulk_update_models'),

    path("create_model/",ModelCreateView.as_view(),name='create_model'),
    path("delete_model/<int:pk>",ModelDeleteView.as_view(),name='delete_model'),
    path("view_model/<int:pk>",ModelDetailView.as_view(),name='model_view'),


    path("categorylist/",FilteredCategoryTableView.as_view(),name='categorylist'),
    path("update_category/<int:pk>",CategoryUpdateView.as_view(),name='update_category'),
    path("create_category/",CategoryCreateView.as_view(),name='create_category'),
    path("delete_category/<int:pk>",CategoryDeleteView.as_view(),name='delete_category'),

    path("checklist/",ChecklistsTableView.as_view(),name="checklist"),
    path("update_check/<int:pk>",CheckUpdateView.as_view(),name='update_check'),
    path("delete_check/<int:pk>",CheckDeleteView.as_view(),name='delete_check'),
    path("create_check/",CheckCreateView.as_view(),name='create_check'),
]