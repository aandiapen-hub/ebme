from django.core.files.uploadedfile import SimpleUploadedFile
from uuid import uuid4
import hashlib
import mimetypes
from pathlib import Path
import pytest
from documents .models import DocumentTypes, TempUploadGroup
from .factories import(
    DocumentLinkFactory,
    DocumentsFactory,
    TempUploadGroupFactory,
    TemporaryUploadFactory,
)
from django.contrib.contenttypes.models import ContentType
from procurement.tests.factories import(
    PurchaseOrderFactory,
    DeliveriesFactory,
)


@pytest.fixture
def document_link():
    return DocumentLinkFactory

@pytest.fixture
def document_type():
    def make_document_type(name='USER_MANUAL'):
        return {
        'USER_MANUAL': DocumentTypes.USER_MANUAL,
        'SERVICE_MANUAL':DocumentTypes.SERVICE_MANUAL,
        }[name]
    return make_document_type

@pytest.fixture
def obj_document_link():
    def _object_document_link(obj):
        content_type_id = ContentType.objects.get_for_model(obj)
        return DocumentLinkFactory(
        content_type=content_type_id,
        object_id=obj.pk 
        )
    return _object_document_link

@pytest.fixture
def temp_group():
    return TempUploadGroupFactory

@pytest.fixture
def asset_data_temp_group():
    return TempUploadGroupFactory(
        document_type_id=DocumentTypes.ASSET_DATA,
        extracted_json = {
            'merged_gs1_ai':{
                'GIAI': '50552395105533488', 'GTIN': '00885403497233', 'brand': None,
                'model': None, 'SERIAL': 'S00455524', 'ASSET_NO': '5533488',
                'category': None, 'PROD DATE': '230423',
                'PROD_DATE': '2304-04-23', 'non_gs1_codes': [],
                'model_description': None,
                'brand_name_options': ['NHS', 'GE Healthcare', 'Siemens Healthineers'],
                'model_name_options': ['Model 999-103DEN', 'Model PRL001311'],
                'category_name_options': ['Infusion Pump', 'Medical Device', 'Healthcare Equipment']
            },
            'resolved': {
                'gtin': {'value': '00885403497233', 'add_gtin': True},
                'asset': {'asset_id': None, 'serialnumber': 'S00455524', 'customerassetnumber': '5533488', 'modelid': None, 'assets': [37818, 37819, 37820, 37822], 'prod_date': '230423', 'create_asset': True, 'too_many_assets': False}, 'job': {'jobs': [], 'too_many_jobs': False}, 'model': {'gtin': '00885403497233', 'modelname': ['Model 999-103DEN', 'Model PRL001311'], 'brandname': ['NHS', 'GE Healthcare', 'Siemens Healthineers'], 'brand_ids': [6661], 'categoryname': ['Infusion Pump', 'Medical Device', 'Healthcare Equipment'], 'category_ids': [], 'model_id': None, 'duplicatable_models': [34763], 'models_without_gtin': [34759, 34760, 34761]}, 'part': {'part_id': None, 'suggested_new_name': []}, 'brand': {'brand_options': ['NHS', 'GE Healthcare', 'Siemens Healthineers'], 'brand_ids': [6661]}, 'category': {'category_options': ['Infusion Pump', 'Medical Device', 'Healthcare Equipment'], 'category_ids': []}},
        }
    )

TEST_FILE_DIR = Path(__file__).parent/'test_files'

@pytest.fixture
def test_file():
    def _get(filename, content_type=None):
        path = TEST_FILE_DIR / filename
        if content_type is None:
            content_type = mimetypes.guess_type(path.name)[0]

        return SimpleUploadedFile(
            name=path.name,
            content=path.read_bytes(),
            content_type=content_type,
        )
    return _get

@pytest.fixture
def document(test_file):
    def _get_document(filename=None, content_type=None):
        if filename:
            file = test_file(filename, content_type)
            content = file.read()

        # when no filename is given
        # generate random temp file
        else:
            content = b"random test content"
            file = SimpleUploadedFile(
                name=f"{uuid4()}.text",
                content=content,
                content_type="text/plain"
            )
        return DocumentsFactory(
            document_name='test_dcocument',
            document_bytea=content,
            mime_type=file.content_type,
            file_size=file.size,
            document_type_id=DocumentTypes.UNKNOWN,
            document_hash = hashlib.sha256(content).hexdigest()
        )

    return _get_document

@pytest.fixture
def temp_document(test_file):
    def _get_temp_document(filename=None, group_type= None, content_type=None, group=None):
        if filename:
            file = test_file(filename, content_type)

        # when no filename is given
        # generate random temp file
        else:
            content = b"random test content"
            file = SimpleUploadedFile(
                name=f"{uuid4()}.text",
                content=content,
                content_type="text/plain"
            )
        if group is None:
            temp_doc = TemporaryUploadFactory(
                file = file,
                mime_type = file.content_type,
                file_size = file.size,
            )

        
        else:
            temp_doc = TemporaryUploadFactory(
                file = file,
                mime_type = file.content_type,
                file_size = file.size,
                group = group
            )
        if group_type:
            temp_doc.group.document_type_id = group_type
            temp_doc.group.save()

        return temp_doc
    return _get_temp_document

@pytest.fixture
def asset_id_temp_document(temp_document):
    return temp_document(filename='equipment_gs2.jpg', group_type=DocumentTypes.ASSET_DATA)

@pytest.fixture
def gs1_conflict_temp_document(temp_document):
    return temp_document(filename='gs1_conflict.jpg', group_type=DocumentTypes.ASSET_DATA)

@pytest.fixture
def asset_no_temp_document(temp_document):
    return temp_document(filename='asset_no.jpg', group_type=DocumentTypes.ASSET_DATA)

@pytest.fixture
def asset_temp_document(temp_document):
    return temp_document(filename='equipment_gs1.jpg', group_type=DocumentTypes.ASSET_DATA)

@pytest.fixture
def service_report_temp_document(temp_document):
    return temp_document(filename='service_report.pdf', group_type=DocumentTypes.SERVICE_REPORT)

@pytest.fixture
def delivery_note_temp_document(temp_document):
    return temp_document(filename='delivery_note.jpeg', group_type=DocumentTypes.DELIVERY_NOTE)

@pytest.fixture
def temp_barcode_only():
    def _get_temp_document(barcode_data='test_barcode_data', group=None):
        if group is None:
            return TemporaryUploadFactory(
                mime_type = '',
                barcode_data=barcode_data
            )
        
        else:
            return TemporaryUploadFactory(
                mime_type = '',
                barcode_data='test',
                group = group
            )

    return _get_temp_document

@pytest.fixture
def immediate_task_backend(settings):
    settings.TASKS = {
        "default": {
                    "BACKEND": "django.tasks.backends.immediate.ImmediateBackend",
        }
    }

@pytest.fixture
def purchase_order():
    return PurchaseOrderFactory

@pytest.fixture
def delivery():
    return DeliveriesFactory
