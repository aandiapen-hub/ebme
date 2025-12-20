# tests/factories.py

import factory
from factory.django import DjangoModelFactory
from assets.tests.factories import AssetFactory
from jobs.tests.factories import JobFactory
from documents.models import (TblDocuments,TblDocumentLinks,TblDocTableRef
)



class DocumentsFactory(DjangoModelFactory):
    class Meta:
        model = TblDocuments
    
    document_name = factory.Faker("file_name")

TABLEREF = ['Asset']
TABLEID = [0]
class DocTableRefFactory(DjangoModelFactory):
    class Meta:
        model = TblDocTableRef
        django_get_or_create = ('table_name',)
    
    table_id = factory.Iterator(TABLEID, cycle=True)
    table_name = factory.Iterator(TABLEREF, cycle=True)

class AssetDocumentLinks(DjangoModelFactory):
    class Meta:
        model = TblDocumentLinks
    
    link_table = factory.SubFactory(DocTableRefFactory)
    link_row = factory.SubFactory(AssetFactory)
    documentid = factory.SubFactory(DocumentsFactory)


class JobDocumentLinks(DjangoModelFactory):
    class Meta:
        model = TblDocumentLinks
    
    link_table = factory.SubFactory(DocTableRefFactory)
    link_row = factory.SubFactory(JobFactory)
    documentid = factory.SubFactory(DocumentsFactory)
