# tests/factories.py
import factory
from django.contrib.contenttypes.models import ContentType
from factory.django import DjangoModelFactory
from assets.tests.factories import AssetFactory
from jobs.tests.factories import JobFactory
from users.tests.factories import UserFactory
from django.core.files.uploadedfile import SimpleUploadedFile
import hashlib
from documents.models import (
    TblDocuments,
    TblDocumentLinks,
    DocumentTypes,
    TempUploadGroup,
    TemporaryUpload,
)


class DocumentsFactory(DjangoModelFactory):
    class Meta:
        model = TblDocuments

    document_name = factory.Faker("file_name")
    document_description = factory.Faker("sentence")
    document_bytea = factory.LazyFunction(
        lambda: factory.Faker._get_faker().sentence().encode("utf-8")
    )
    file_size = factory.LazyAttribute(lambda o: len(o.document_bytea))
    document_hash = factory.LazyAttribute(
        lambda o: hashlib.sha256(o.document_bytea).hexdigest()
    )
    mime_type = "application/pdf"
    document_type_id = factory.Iterator(DocumentTypes.values)


class DocumentLinkFactory(DjangoModelFactory):
    class Meta:
        model = TblDocumentLinks

    documentid = factory.SubFactory(DocumentsFactory)
    content_type = factory.LazyFunction(
        lambda: ContentType.objects.get_for_model(TblDocumentLinks)
    )
    object_id = factory.Sequence(lambda n: n + 1)

class TaskFactory(factory.Factory):
    class Meta:
        model = dict

    status = "SUCCESSFUL"



class TempUploadGroupFactory(DjangoModelFactory):
    class Meta:
        model = TempUploadGroup

    id = factory.Faker("uuid4")
    user = factory.SubFactory(UserFactory)

    document_type_id = DocumentTypes.UNKNOWN

    combined_ocr_text = "test ocr text"
    extracted_json = factory.LazyFunction(dict)
    task_result_id = factory.SubFactory(TaskFactory)


def fake_test_file(name="test.pdf", content=b"fake file content"):
    return SimpleUploadedFile(name, content, content_type="application/pdf")


class TemporaryUploadFactory(DjangoModelFactory):
    class Meta:
        model = TemporaryUpload

    group = factory.SubFactory(TempUploadGroupFactory)
