import factory
from assets.tests.factories import ModelFactory
from assets.models import Tblcheckslists

class TblcheckslistsFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Tblcheckslists

    testname = factory.Sequence(lambda n: f"Test {n}")

    test_description = factory.Faker(
        "paragraph",
        nb_sentences=3,
    )
    modelid = factory.SubFactory(ModelFactory)
