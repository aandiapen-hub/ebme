from django.urls import path

from .views import (DeliveryDeleteView, InvoicesCreateView, PoTableView,PoCreateView, PoDetailView, PoDeleteView,PoUpdateView,
                    PoLinesListView, DeliveryLinesListView,OutstandingItemsListView,
                    DeliveryCreateView,DeliveryUpdateView,DeliveriesListView, DeliveryDeleteView,
                    GeneratePurchaseOrder, DeliveryNoteReader, DeliveryNoteReaderOutput,
                    FilteredInvoiceTableView, InvoicesCreateView, InvoicesDetailView, InvoicesUpdateView,
                    InvoicesDeleteView, InvoicesListView, InvoiceReader, InvoiceReaderOutput,
)

app_name = 'procurement'
urlpatterns = [
    path("purchase_orders/",PoTableView.as_view(),name='po'),
    path("purchase_orders/create/",PoCreateView.as_view(),name='po_create'),
    path("purchase_orders/<int:pk>/detail/",PoDetailView.as_view(),name='po_detail'),
    path("purchase_orders/<int:pk>/delete/",PoDeleteView.as_view(),name='po_delete'),
    path("purchase_orders/<int:pk>/update/",PoUpdateView.as_view(),name='po_update'),
    path("gen_purchase_orders/<int:pk>/",GeneratePurchaseOrder.as_view(),name='gen_po'),

    #po lines
    path("po_lines/",PoLinesListView.as_view(),name='po_lines'),
    #del lines
    path("deliveries/",DeliveriesListView.as_view(),name='deliveries'),
    path("delivery_lines/",DeliveryLinesListView.as_view(),name='del_lines'),
    path("deliveries/create/",DeliveryCreateView.as_view(),name='deliveries_create'),
    path("deliveries/<int:pk>/update/",DeliveryUpdateView.as_view(),name='deliveries_update'),
    path("deliveries/<int:pk>/delete/",DeliveryDeleteView.as_view(),name='deliveries_delete'),

    #utils
    path("deliveries/delivery_note_reader/<int:temp_file_group>/",DeliveryNoteReader.as_view(),name='delivery_note_reader'),
    path("deliveries/delivery_note_reader_output/<int:temp_file_group>/",DeliveryNoteReaderOutput.as_view(),name='delivery_note_reader_output'),

    
    #po lines view
    path("outstanding_items/",OutstandingItemsListView.as_view(),name='outstanding_items'),
   
    #invoices
    path("invoices/",FilteredInvoiceTableView.as_view(),name='invoices_table'),
    path("invoices/create/",InvoicesCreateView.as_view(),name='invoices_create'),
    path("invoices/<int:pk>/detail/",InvoicesDetailView.as_view(),name='invoices_detail'),
    path("invoices/<int:pk>/update/",InvoicesUpdateView.as_view(),name='invoices_update'),
    path("invoices/<int:pk>/delete/",InvoicesDeleteView.as_view(),name='invoices_delete'),
    path("invoices/list/",InvoicesListView.as_view(),name='invoiceslist'),

    path("invoices/reader/<int:temp_file_group>/",InvoiceReader.as_view(),name='invoices_reader'),
    path("invoices/reader_output/<int:temp_file_group>/",InvoiceReaderOutput.as_view(),name='invoices_reader_output'),


]