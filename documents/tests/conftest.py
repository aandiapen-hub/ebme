from django.core.files.uploadedfile import SimpleUploadedFile
from uuid import uuid4
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
def document():
    return DocumentsFactory

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


