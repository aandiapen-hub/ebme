from documents.models import TempUploadGroup, DocumentTypes
from datetime import datetime
from assets.models import Tblbrands, Tblcategories


def map_service_report_data_to_job(resolved_data):
    # data for job is already mapped correctly, no further
    # processing required
    return resolved_data.get("job", None)


def map_delivery_note(resolved_data):
    return resolved_data.get("delivery", None)


def map_asset_data(resolved_data):
    payload = resolved_data.get("asset", None)
    for field, value in payload.items():
        if field == "prod_date":
            value = datetime.strptime(value, "%y%m%d").date()
    return payload


def map_model_data(resolved_data):
    payload = resolved_data.get("model", None)
    return payload


INITIAL_PAYLOAD_MAP = {
    DocumentTypes.SERVICE_REPORT: map_service_report_data_to_job,
    DocumentTypes.DELIVERY_NOTE: map_delivery_note,
    DocumentTypes.ASSET_DATA: map_asset_data,
    "create_model": map_model_data,
    DocumentTypes.UNKNOWN: map_asset_data,
}


def apply_payload_to_initial(
    temp_group_id,
    initial,
    initial_mapper=None,
):
    if temp_group_id is None:
        return initial

    temp_group = TempUploadGroup.objects.filter(pk=temp_group_id).first()
    if not temp_group:
        return initial

    resolved_data = temp_group.extracted_json.get("resolved", {})

    if initial_mapper:
        mapper = INITIAL_PAYLOAD_MAP.get(initial_mapper)
    else:
        mapper = INITIAL_PAYLOAD_MAP.get(temp_group.document_type_id)

    if not mapper:
        return initial

    payload = mapper(resolved_data)

    if payload:
        # update initial based on specifid payload in query params
        for key, value in payload.items():
            print(key, ':', value)
            v = initial.get(key, None)
            if v in [None, '']:
                if isinstance(value, list):
                    if len(value) > 0:
                        initial[key] = value[0]
                else:
                    initial[key] = value
    return initial


def delivery_note_items_mapper(resolved_data):
    data = resolved_data.get("delivery", None)
    if not data:
        return None

    return data.get("items_list", None)


def get_formset_initial(
    temp_group_id,
):
    if temp_group_id is None:
        return None

    temp_group = TempUploadGroup.objects.filter(pk=temp_group_id).first()
    if not temp_group:
        return None

    resolved_data = temp_group.extracted_json.get("resolved", {})

    mapper = CONTEXT_PAYLOAD_MAP.get(temp_group.document_type_id)

    if not mapper:
        return None

    return mapper(resolved_data)


def map_model_data_to_context(resolved_data):
    model_data = resolved_data.get("model", None)
    if model_data:
        return {
            "modelname": model_data.get("modelname"),
            "existing_categories": Tblcategories.objects.filter(
                pk__in=model_data.get("category_ids"),
            ),
            "categoryname": model_data.get("categoryname"),
            "existing_brands": Tblbrands.objects.filter(
                pk__in=model_data.get("brand_ids"),
            ),
            "brandname": model_data.get("brandname"),
        }


CONTEXT_PAYLOAD_MAP = {
    DocumentTypes.DELIVERY_NOTE: delivery_note_items_mapper,
    "create_model": map_model_data_to_context,
}


def apply_payload_to_context(temp_group_id, context, context_mapper=None):
    if temp_group_id is None:
        return context

    temp_group = TempUploadGroup.objects.filter(pk=temp_group_id).first()
    if not temp_group:
        return context

    resolved_data = temp_group.extracted_json.get("resolved", {})

    if context_mapper:
        mapper = CONTEXT_PAYLOAD_MAP.get(context_mapper)
    else:
        mapper = CONTEXT_PAYLOAD_MAP.get(temp_group.document_type_id)

    if not mapper:
        return context

    context.update(**mapper(resolved_data))
    
    return context
