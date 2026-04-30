import factory
from factory.django import DjangoModelFactory
from procurement.tests.factories import SupplierFactory

from parts.models import (
    Tblpartslist,
    Tblpartsprice,
      TblPartModel
)

class PartFactory(DjangoModelFactory):
    class Meta:
        model = Tblpartslist
        django_get_or_create = ('part_number',)

    part_number = factory.Faker('ean13')
    description = factory.Faker('sentence', nb_words=6)
    short_name = factory.Faker('word')
    supplier_id = factory.SubFactory(SupplierFactory)
    inactive = factory.Faker('boolean', chance_of_getting_true=5)  # 10% chance of being inactive
    