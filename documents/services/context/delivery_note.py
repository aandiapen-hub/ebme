from django.shortcuts import reverse
from urllib.parse import urlencode
from .context import BaseDocumentContextBuilder
from .context_action import Action

from procurement.models import TblPurchaseOrder, TblDeliveries


def temp_group_params(temp_group_id):
    if not temp_group_id:
        return {}
    return urlencode({'temp_group_id': temp_group_id})


def get_purchase_order_from_resolved_data(data, temp_group_id=None):
    po_id = data.get('delivery', {}).get('po')
    output = []
    if po_id:
        po_qs = TblPurchaseOrder.objects.filter(pk=po_id)
        query_params = temp_group_params(temp_group_id)

        for po in po_qs:
            output.append(Action(
                key='create_delivery',
                header='Matched PO',
                label='Open PO',
                obj=po,
                enabled=True,
                action_url=f"{reverse('procurement:deliveries_create', kwargs={'po_id': po_id})}?{query_params}",
                color='success'
                )
            )
        return output
    return None


def get_existing_matching_deliveries(data):

    del_note_number = data.get('delivery', {}).get('delivery_ids')
    output = []
    if del_note_number:
        existing_deliveries = TblDeliveries.objects.filter(pk__in=del_note_number)
        for delivery in existing_deliveries:
            output.append(
                Action(
                    key='matched_delivery',
                    header='Existing Deliveries',
                    label='Open',
                    obj=delivery,
                    enabled=True,
                    open_url=reverse('procurement:po_detail', kwargs={'pk': delivery.po}),
                    color='primary',
                )
            )

        return output


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
                    self.resolved_data, self.get_temp_group_id()
                ),
                'existing_deliveries': get_existing_matching_deliveries(
                    self.resolved_data
                )
        }
