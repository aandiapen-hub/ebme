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
            'merged_gs1_ai': {'asset': {'asset_id': None,
                        'assets': [1541],
                        'create_asset': True,
                        'customerassetnumber': None,
                        'modelid': None,
                        'prod_date': '200526',
                        'serialnumber': 'S00404465',
                        'too_many_assets': False},
                'brand': {'brand_ids': [0, 2, 3, 5, 7, 10, 34, 35, 37, 51],
                        'brand_options': ['Fresenius', 'Fresenius Medical Care']},
                'category': {'category_ids': [2, 3, 4, 5, 6, 24, 35],
                            'category_options': ['Infusion Pump', 'Medical Device']},
                'gtin': {'add_gtin': True, 'value': '00885403477310'},
                'job': {'jobs': [5487], 'too_many_jobs': False},
                'model': {'brand_ids': [0, 2, 3, 5, 7, 10, 34, 35, 37, 51],
                        'brandname': ['Fresenius', 'Fresenius Medical Care'],
                        'category_ids': [2, 3, 4, 5, 6, 24, 35],
                        'categoryname': ['Infusion Pump', 'Medical Device'],
                        'duplicatable_models': [],
                        'gtin': '00885403477310',
                        'model_id': None,
                        'modelname': ['IP22', '999-103EN'],
                        'models_without_gtin': [42]},
                'part': {'part_id': None, 'suggested_new_name': []}}
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
    def _get_temp_document(filename=None,content_type=None, group=None):
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
            return TemporaryUploadFactory(
                file = file,
                mime_type = file.content_type,
                file_size = file.size,
            )
        
        else:
            return TemporaryUploadFactory(
                file = file,
                mime_type = file.content_type,
                file_size = file.size,
                group = group
            )

    return _get_temp_document


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
                    "BACKEND": "django.tasks.backends.dummy.DummyBackend",
        }
    }

