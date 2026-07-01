import pytest
from assets.tests.factories import(
    AssetFactory,
    CustomerFactory,
    AssetStatusFactory,
    ModelFactory,
    BrandFactory,
    CategoryFactory,
    SiteFactory,
)
from model_information.tests.factories import (
    SoftwareModelFactory,
    EquipmentSoftwareFactory,
    EquipmentConfigurationModelFactory,
)
from parts.tests.factories import PartFactory
from users.tests.factories import UserFactory
from jobs.tests.factories import JobFactory
from procurement.tests.factories import SupplierFactory
from parts.tests.factories import TblPartModelFactory
from jobs.tests.factories import ChecklistsFactory


@pytest.fixture(scope='session')
def django_db_modify_db_settings():
    """Tell pytest-django to not create a test database."""
    return False

@pytest.fixture(scope='session')
def django_db_use_migrations():
    """Prevent test DB creation from scratch (use your existing DB schema)."""
    return False

@pytest.fixture
def job():
    return JobFactory

@pytest.fixture
def user_setup(django_user_model):
    user = django_user_model.objects.create_user(
        user_name='testuser',
        password='testpass',
        email='test@testing.com',
        first_name='test',
    )
    return user

@pytest.fixture
def supplier():
    return SupplierFactory



@pytest.fixture
def user():
    return UserFactory


@pytest.fixture
def customer():
    return CustomerFactory

@pytest.fixture
def asset():
    return AssetFactory

@pytest.fixture
def model():
    return ModelFactory

@pytest.fixture
def active_spare_part():
    return PartFactory(inactive=False)

@pytest.fixture
def assets():
    def _assets(count=10, **kwargs):
        return AssetFactory.create_batch(count, **kwargs)
    return _assets

@pytest.fixture
def jobs():
    def _jobs(count=10, **kwargs):
        return JobFactory.create_batch(count, **kwargs)
    return _jobs

@pytest.fixture
def part():
    return PartFactory

@pytest.fixture
def asset_status():
    return AssetStatusFactory

@pytest.fixture
def site():
    return SiteFactory

@pytest.fixture
def brand():
    return BrandFactory

@pytest.fixture
def category():
    return CategoryFactory

@pytest.fixture
def part_model():
    return TblPartModelFactory

@pytest.fixture
def checklists():
    def _multiple_checks(count=10, **kwargs):
        return ChecklistsFactory.create_batch(count, **kwargs)
    return _multiple_checks



@pytest.fixture
def software_model_factory():
    return SoftwareModelFactory


@pytest.fixture
def equipment_software_factory():
    return EquipmentSoftwareFactory

@pytest.fixture
def equipment_configuration_model_factory():
    return EquipmentConfigurationModelFactory
