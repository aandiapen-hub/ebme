from .service_report import ServiceReportContext
from .delivery_note import DeliveryNoteContext
from .asset_data import AssetDataContext
from documents.models import DocumentTypes


CONTEXT_BUILDERS = {
    DocumentTypes.SERVICE_REPORT: ServiceReportContext,
    DocumentTypes.DELIVERY_NOTE: DeliveryNoteContext,
    DocumentTypes.ASSET_DATA: AssetDataContext,
}


def build_document_context(temp_group):

    builder_cls = CONTEXT_BUILDERS.get(
        temp_group.document_type_id, None
    )

    if not builder_cls:
        return {}

    return builder_cls(temp_group).build()
