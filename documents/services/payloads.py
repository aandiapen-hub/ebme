from documents.services.context import delivery_note
from documents.models import TempUploadGroup, DocumentTypes


def map_service_report_data_to_job(resolved_data):
    # data for job is already mapped correctly, no further
    # processing required
    return resolved_data.get('job', None)


def map_delivery_note(resolved_data):
    return resolved_data.get('delivery', None)


INITIAL_PAYLOAD_MAP = {
    DocumentTypes.SERVICE_REPORT: map_service_report_data_to_job,
    DocumentTypes.DELIVERY_NOTE: map_delivery_note,
}


def apply_payload_to_initial(
    temp_group_id,
    initial,
):
    if temp_group_id is None:
        return initial

    temp_group = TempUploadGroup.objects.filter(pk=temp_group_id).first()
    if not temp_group:
        return initial

    resolved_data = temp_group.extracted_json.get('resolved', {})

    mapper = INITIAL_PAYLOAD_MAP.get(temp_group.document_type_id)

    if not mapper:
        return initial

    payload = mapper(resolved_data)

    if payload:
        # update initial based on specifid payload in query params
        for key, value in payload.items():
            if isinstance(value, list) and value:
                initial[key] = value[0]
            else:
                initial[key] = value
    return initial


def delivery_note_items_mapper(resolved_data):
    data = resolved_data.get('delivery', None)
    if not data:
        return None

    return data.get('items_list', None)


CONTEXT_PAYLOAD_MAP = {
    DocumentTypes.DELIVERY_NOTE: delivery_note_items_mapper,
}


def get_formset_initial(
    temp_group_id,
):
    if temp_group_id is None:
        return None

    temp_group = TempUploadGroup.objects.filter(pk=temp_group_id).first()
    if not temp_group:
        return None

    resolved_data = temp_group.extracted_json.get('resolved', {})

    mapper = CONTEXT_PAYLOAD_MAP.get(temp_group.document_type_id)

    if not mapper:
        return None

    return mapper(resolved_data)


