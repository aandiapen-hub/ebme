from django.shortcuts import reverse
from urllib.parse import urlencode
from .context import BaseDocumentContextBuilder
from .context_action import(
    Action,
    MatchedGroup,
    MatchedItem,
)

from procurement.models import TblPurchaseOrder, TblDeliveries


def temp_group_params(temp_group_id):
    return urlencode({'temp_group_id': temp_group_id})


def get_purchase_order_from_resolved_data(data, temp_group_id=None):
    po_id = data.get('delivery', {}).get('po')
    query_params = temp_group_params(temp_group_id)

    items = []
    if po_id:
        po = TblPurchaseOrder.objects.filter(pk=po_id).first()

        actions = []
        actions.append(
            Action(
                label='Create Delivery',
                enabled=True,
                url=f"{reverse('procurement:deliveries_create', kwargs={'po_id': po_id})}?{query_params}",
                color='primary'
                )
        ) 
        actions.append(
            Action(
                label='Open',
                enabled=True,
                url=f"{reverse('procurement:po_detail', kwargs={'pk': po_id})}",
                color='outline-primary'
                )
        ) 
        items += [ MatchedItem(
            item_type='Purchase Order',
            title='PO Found',
            description=f'{po} - {po.order_status}',
            obj=po,
            actions=actions
        ) ]
    return items



def get_key_information(data):
    output = {}
    po = data.get('delivery',{}).get('po')
    if po:
        output.update({
            'Purchase Order': po 
            })

    return output

def get_existing_matching_deliveries(data):
    delivery_ids = data.get('delivery', {}).get('delivery_ids')
    items = []
    if delivery_ids:
        existing_deliveries = TblDeliveries.objects.filter(pk__in=delivery_ids)
        for delivery in existing_deliveries:
            actions = []
            actions.append(
                Action(
                    label='Open',
                    enabled=True,
                    url=reverse('procurement:po_detail', kwargs={'pk': delivery.po}),
                    color='outline-primary',
                )
            )
        items += [ MatchedItem(
            item_type='Delivery Note',
            title='Delivery Note Found',
            description=f'{delivery} for {delivery.po}({delivery.po.order_status})',
            obj=delivery,
            actions=actions
        ) ]
    return items

class DeliveryNoteContext(
    BaseDocumentContextBuilder
):

    def template_name(self):
       return 'documents/document_processor/delivery_note.html' 

    def get_extra_context(self):

        purchase_order =  MatchedGroup(
            title='Purchase Order',
            confidence='Full',
            items=[],
            color='primary')


        purchase_order.items += get_purchase_order_from_resolved_data(
                    self.resolved_data, self.get_temp_group_id()
                )


        existing_deliveries = MatchedGroup(
            title='Matched Deliveries',
            confidence='Full',
            items=[],
            color='success')

        existing_deliveries.items += get_existing_matching_deliveries(
                    self.resolved_data
                )

        return {
            'key_data_extracted': get_key_information(self.resolved_data),
            'purchase_order': purchase_order,
            'existing_deliveries': existing_deliveries,
            }
