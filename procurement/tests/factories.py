import factory
from datetime import timedelta
from factory.django import DjangoModelFactory
from django.utils.timezone import now
from decimal import Decimal

from procurement.models import (
    TblInvoiceStatus,
    TblOrderStatus,
    TblOrderUnit,
    TblPurchaseOrder,
    TblPoLines,
    TblDeliveries,
    TblDeliveryLines,
    TblSuppliers,
    TblDeliveryAddresses,
    TblInvoices
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
class TblDeliveryAddressesFactory(DjangoModelFactory):
    class Meta:
        model = TblDeliveryAddresses
        django_get_or_create = ('contact',)

    addr_id = factory.Sequence(lambda n: n + 1)
    first_line = factory.Faker('address')
    postcode = factory.Faker('postcode')
    contact = factory.Iterator(CONTACT_NAMES, cycle=True)

ORDER_STATUS = ['cancelled', 'created', 'awaiting_delivery','transit']
class OrderStatusFactory(DjangoModelFactory):
    class Meta:
        model = TblOrderStatus

    order_status_name = factory.Iterator(ORDER_STATUS, cycle=True)
    order_status_id = factory.Sequence(lambda n: n + 1)



class PurchaseOrderFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TblPurchaseOrder

    supplier = factory.SubFactory(SupplierFactory)
    ship_to_add = factory.SubFactory(TblDeliveryAddressesFactory)
    order_status = factory.SubFactory(OrderStatusFactory)
    po_total = 100 
    sub_total = 100 
    vat_amount = 20

    date_raised = factory.Faker("date_object")

class DeliveriesFactory(DjangoModelFactory):
    class Meta:
        model = TblDeliveries
    
    po = factory.SubFactory(PurchaseOrderFactory)
    delivery_date = factory.Faker('date_this_year')
    delivery_note_number = factory.Faker('ean13')

ORDER_UNIT_NAME = ['Unit', 'Pack']
class TblOrderUnitFactory(DjangoModelFactory):
    class Meta:
        model = TblOrderUnit

    order_unit_id = factory.Sequence(lambda n: n + 1)
    order_unit_name = factory.Iterator(ORDER_UNIT_NAME, cycle=True)


class TblPoLinesFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TblPoLines

    po = factory.SubFactory(PurchaseOrderFactory)
    item = factory.SubFactory("parts.tests.factories.PartFactory")
    qty_ordered = 1
    unit_price = Decimal("100.00")
    vat = Decimal("20.00")
    line_price = Decimal("100.00")
    vat_amount = Decimal("20.00")
    line_price_incl_vat = Decimal("120.00")
    qty_delivered = 0
    line_status_id = 1
    line_description = factory.Faker("sentence")
    order_unit_id = factory.SubFactory(
        TblOrderUnitFactory
    )
    order_unit_quantity = 1


class TblDeliveryLinesFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TblDeliveryLines

    delivery = factory.SubFactory(DeliveriesFactory)

    item = factory.SubFactory("parts.tests.factories.PartFactory")

    qty = factory.Faker(
        "random_int",
        min=1,
        max=100,
    )

    line_description = factory.Faker("sentence")



INVOICE_STATUS = ['Unit', 'Pack']
class InvoiceStatusFactory(DjangoModelFactory):
    class Meta:
        model = TblInvoiceStatus

    invoice_status_id = factory.Sequence(lambda n: n + 1)
    invoice_status_name = factory.Iterator(INVOICE_STATUS, cycle=True)


class TblInvoicesFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TblInvoices

    invoice_no = factory.Sequence(
        lambda n: f"INV-{n:06d}"
    )

    invoice_date = factory.Faker("date_object")

    invoice_due_date = factory.LazyAttribute(
        lambda o: o.invoice_date + timedelta(days=30)
    )

    po = factory.SubFactory(PurchaseOrderFactory)

    invoice_status = factory.SubFactory(
        InvoiceStatusFactory
    )

    invoice_amount = Decimal("120.00")

    creation_date = factory.LazyFunction(
        lambda: now().date()
    )

    fully_paid_date = None
