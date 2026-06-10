import pytest

from assets.tests.factories import(
    CategoryFactory,
    BrandFactory,
    ModelFactory,
)
from .factories import TblcheckslistsFactory

@pytest.fixture
def category():
    return CategoryFactory

@pytest.fixture
def brand():
    return BrandFactory

@pytest.fixture
def model():
    return ModelFactory

@pytest.fixture
def check():
    return TblcheckslistsFactory
