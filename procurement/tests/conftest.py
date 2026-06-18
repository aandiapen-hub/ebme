import pytest
from .factories import(
    InvoiceStatusFactory,
    OrderStatusFactory,
    PurchaseOrderFactory,
    TblInvoicesFactory,
    TblPoLinesFactory,
    TblDeliveryLinesFactory,
    SupplierFactory,
)

@pytest.fixture
def purchase_order():
    return PurchaseOrderFactory

@pytest.fixture
def po_line():
    return TblPoLinesFactory


@pytest.fixture
def delivery_line():
    return TblDeliveryLinesFactory

@pytest.fixture
def delivery_lines():
    def _generate_lines(count=5, **kwargs):
        return TblDeliveryLinesFactory.create_batch(size=count, **kwargs)
    return _generate_lines


@pytest.fixture
def invoice():
    return TblInvoicesFactory

@pytest.fixture
def supplier():
    return SupplierFactory

@pytest.fixture
def order_status():
    return OrderStatusFactory


@pytest.fixture
def invoice_status():
    return InvoiceStatusFactory
