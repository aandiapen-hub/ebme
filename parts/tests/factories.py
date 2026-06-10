import factory
from decimal import Decimal
from factory.django import DjangoModelFactory

from parts.models import (
    Tblpartslist,
    Tblpartsprice,
    TblPartModel,
)

class PartFactory(DjangoModelFactory):
    class Meta:
        model = Tblpartslist
        django_get_or_create = ('part_number',)

    part_number = factory.Faker('ean13')
    description = factory.Faker('sentence', nb_words=6)
    short_name = factory.Faker('word')
    supplier_id = factory.SubFactory('procurement.tests.factories.SupplierFactory')
    order_unit = factory.SubFactory('procurement.tests.factories.TblOrderUnitFactory')
    inactive = factory.Faker('boolean', chance_of_getting_true=5)
    
class TblPartsPriceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Tblpartsprice

    partid = factory.SubFactory("parts.tests.factories.PartFactory")
    price = Decimal("100.00")
    effectivedate = factory.Faker("date_object")

class TblPartModelFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TblPartModel

    model = factory.SubFactory("assets.tests.factories.ModelFactory")
    part = factory.SubFactory("parts.tests.factories.PartFactory")
