import pytest
from .factories import(
    TblPartsPriceFactory,
    TblPartModelFactory,
)
from procurement.tests.factories import TblOrderUnitFactory

@pytest.fixture
def part_price():
    return TblPartsPriceFactory


@pytest.fixture
def order_unit():
    return TblOrderUnitFactory
