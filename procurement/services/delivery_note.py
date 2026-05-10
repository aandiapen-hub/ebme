from procurement.models import Outstandngdeliveriesview


def delivery_items_formset_get_context(
    po_id,
    instance,
    formset_class,
    delivered_items=None,
):

    outstanding_items = Outstandngdeliveriesview.objects.filter(po_id=po_id)
    delivered_items = delivered_items or {}
    initial = []

    for item in outstanding_items:
        delivered = delivered_items.get(item.part_number, None)
        qty = item.outstanding

        if delivered:
            try:
                qty = int(delivered)
            except (TypeError, ValueError):
                pass

        initial.append({
            'item': item.item.pk,
            'qty': qty,
        })

    return {
            "formset": formset_class(
                        instance=instance,
                        initial=initial,
                        extra=len(initial))
            }

