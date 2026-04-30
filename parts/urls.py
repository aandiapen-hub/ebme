from django.urls import path
from .views import (PartsTableView,
                    PartDetailView,
                    PartUpdateView,
                    PartBulkUpdateView,
                    PartDeleteView,
                    PartCreateView,
                    SparePartPriceListView,
                    SparePartPriceCreateView,
                    SparePartPriceDetailView,
                    SparePartPriceDeleteView,
                    SparePartPriceUpdateView,
                    PartLinkedModelListView,
                    LinkModelCreateView,
                    LinkModelDeleteView,
                    LinkedModelDetailView,

)

app_name = 'parts'
urlpatterns = [
    path("parts/",PartsTableView.as_view(),name='parts'),
    path("parts/<int:pk>/detail",PartDetailView.as_view(),name='part_detail'),
    path("parts/<int:pk>/update",PartUpdateView.as_view(),name='update_part'),
    path("parts/bulk_pdate",PartBulkUpdateView.as_view(),name='bulk_update_part'),

    path("parts/<int:pk>/delete",PartDeleteView.as_view(),name='delete_part'),
    path("parts/create/",PartCreateView.as_view(),name='create_part'),
    #part prices
    path("parts/prices/",SparePartPriceListView.as_view(),name="part_prices"),
    path("parts/prices/create/",SparePartPriceCreateView.as_view(),name="part_prices_create"),
    path("parts/prices/<int:pk>/",SparePartPriceDetailView.as_view(),name="part_prices_detail"),
    path("parts/prices/<int:pk>/delete",SparePartPriceDeleteView.as_view(),name="part_prices_delete"),
    path("parts/prices/<int:pk>/Update",SparePartPriceUpdateView.as_view(),name="part_prices_update"),
    #linkedmodels
    path("parts/linked_models/",PartLinkedModelListView.as_view(),name="linked_models"),
    path("parts/linked_models_create/",LinkModelCreateView.as_view(),name="linked_models_create"),
    path("parts/linked_models/<int:pk>/delete/",LinkModelDeleteView.as_view(),name='linked_models_delete'),
    path("parts/linked_models/<int:pk>/",LinkedModelDetailView.as_view(),name="linked_models_detail"),
]           