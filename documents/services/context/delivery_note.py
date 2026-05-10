from django.shortcuts import reverse
from urllib.parse import urlencode
from .context import BaseDocumentContextBuilder

from procurement.models import TblPurchaseOrder, TblDeliveries


def get_purchase_order_from_resolved_data(temp_group_id, data):
    po_id = data.get('delivery', {}).get('po')
    if po_id:
        po = TblPurchaseOrder.objects.filter(pk=po_id).first()
        base_url = reverse('procurement:deliveries_create', kwargs={'po_id': po_id})
        query_params = urlencode(
            {'temp_group_id': temp_group_id}
        )
        po.create_delivery_url = f"{base_url}?{query_params}"
        po.url = reverse('procurement:po_detail', kwargs={'pk': po_id})
        return po
    return None

def get_existing_matching_deliveries(data):

    del_note_number = data.get('delivery', {}).get('delivery_ids')
    if del_note_number:
        existing_deliveries = TblDeliveries.objects.filter(pk__in=del_note_number)
        for delivery in existing_deliveries:
            delivery.open_url = reverse('procurement:po_detail', kwargs={'pk': delivery.po})

        return existing_deliveries
    

class DeliveryNoteContext(
    BaseDocumentContextBuilder
):

    def get_payload(self):
        return self.resolved_data.get('delivery', {})

    def template_name(self):
        return 'documents/document_processor/delivery_note_actions.html'

    def get_extra_context(self):
        return {
                'purchase_order': get_purchase_order_from_resolved_data(
                    self.temp_group.pk, self.resolved_data
                ),
                'existing_deliveries': get_existing_matching_deliveries(
                    self.resolved_data
                )
        }
