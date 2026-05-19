from .service_report import ServiceReportContext
from .delivery_note import DeliveryNoteContext
from .asset_data import AssetDataContext
from .non_staff import NonStaffContext
from documents.models import DocumentTypes


CONTEXT_BUILDERS = {
    DocumentTypes.SERVICE_REPORT: ServiceReportContext,
    DocumentTypes.DELIVERY_NOTE: DeliveryNoteContext,
    DocumentTypes.ASSET_DATA: AssetDataContext,
    'global_search': AssetDataContext,
    'non_staff': NonStaffContext,
}


def build_document_context(*, user, temp_group=None, resolved_data=None):
    if not user.is_staff:
        builder_cls = CONTEXT_BUILDERS.get(
            'non_staff', None
        )

    elif temp_group and temp_group.document_type_id:
        builder_cls = CONTEXT_BUILDERS.get(
            temp_group.document_type_id, None
        )
    else:
        builder_cls = CONTEXT_BUILDERS.get(
            'global_search', None
        )

    if not builder_cls:
        return {}
    return builder_cls(
        temp_group=temp_group, resolved_data=resolved_data
    ).build()
