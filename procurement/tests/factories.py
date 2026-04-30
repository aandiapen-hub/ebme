import factory
from factory.django import DjangoModelFactory

from procurement.models import (
    TblPurchaseOrder,
    TblPoLines,
    TblDeliveries,
    TblDeliveryLines,
    TblSuppliers,
    TblDeliveryAddresses
)


COMPANY_NAMES = ['Acme Corp', 'Globex Corporation', 'Initech', 'Umbrella Corp', 'Hooli']
class SupplierFactory(DjangoModelFactory):
    class Meta:
        model = TblSuppliers
        django_get_or_create = ('supplier_name',)

    
    supplier_name = factory.Iterator(COMPANY_NAMES, cycle=True)
    email_address = factory.Faker('email')
    phone_number = factory.Faker('phone_number')
    addr_first_line = factory.Faker('address')
    addr_postcode = factory.Faker('postcode')


CONTACT_NAMES = ['John Doe', 'Jane Smith', 'Alice Johnson', 'Bob Brown', 'Charlie Davis']
class TbldeliveryAddressesFactory(DjangoModelFactory):
    class Meta:
        model = TblDeliveryAddresses
        django_get_or_create = ('contact',)

    addr_id = factory.Sequence(lambda n: n + 1)
    first_line = factory.Faker('address')
    postcode = factory.Faker('postcode')
    contact = factory.Iterator(CONTACT_NAMES, cycle=True)



class PurchaseOrderFactory(DjangoModelFactory):
    class Meta:
        model = TblPurchaseOrder
    
    supplier = factory.SubFactory(SupplierFactory)
    date_raised = factory.Faker('date_this_year')
    ship_to_add = factory.SubFactory(TbldeliveryAddressesFactory)

class tbldeliveriesFactory(DjangoModelFactory):
    class Meta:
        model = TblDeliveries
    
    po = factory.SubFactory(PurchaseOrderFactory)
    delivery_date = factory.Faker('date_this_year')
    delivery_note_number = factory.Faker('ean13')

