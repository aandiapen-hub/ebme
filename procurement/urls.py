from django.urls import path

from .views import (
    DeliveryDeleteView,
    InvoicesCreateView,
    PoTableView,
    PoCreateView,
    PoDetailView,
    PoDeleteView,
    PoUpdateView,
    DeliveryCreateView,
    DeliveryUpdateView,
    GeneratePurchaseOrder,
    FilteredInvoiceTableView,
    InvoicesDetailView,
    InvoicesUpdateView,
    InvoicesDeleteView,
)

app_name = "procurement"
urlpatterns = [
    path("purchase_orders/", PoTableView.as_view(), name="po"),
    path("purchase_orders/create/", PoCreateView.as_view(), name="po_create"),
    path("purchase_orders/<int:pk>/detail/", PoDetailView.as_view(), name="po_detail"),
    path("purchase_orders/<int:pk>/delete/", PoDeleteView.as_view(), name="po_delete"),
    path("purchase_orders/<int:pk>/update/", PoUpdateView.as_view(), name="po_update"),
    path(
        "gen_purchase_orders/<int:pk>/", GeneratePurchaseOrder.as_view(), name="gen_po"
    ),
    # del lines
    path("deliveries/create/<int:po_id>/", DeliveryCreateView.as_view(), name="deliveries_create"),
    path(
        "deliveries/<int:pk>/update/",
        DeliveryUpdateView.as_view(),
        name="deliveries_update",
    ),
    path(
        "deliveries/<int:pk>/delete/",
        DeliveryDeleteView.as_view(),
        name="deliveries_delete",
    ),
    # invoices
    path("invoices/", FilteredInvoiceTableView.as_view(), name="invoices_table"),
    path("invoices/create/", InvoicesCreateView.as_view(), name="invoices_create"),
    path(
        "invoices/<int:pk>/detail/",
        InvoicesDetailView.as_view(),
        name="invoices_detail",
    ),
    path(
        "invoices/<int:pk>/update/",
        InvoicesUpdateView.as_view(),
        name="invoices_update",
    ),
    path(
        "invoices/<int:pk>/delete/",
        InvoicesDeleteView.as_view(),
        name="invoices_delete",
    ),
]

