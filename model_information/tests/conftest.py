import pytest
from model_information.tests.factories import (
    SoftwareTypeFactory,
    SoftwareFactory,
    EquipmentConfigurationStatusFactory,
    ActiveConfigurationStatusFactory,
    DraftConfigurationStatusFactory,
    RetiredConfigurationStatusFactory,
    EquipmentConfigurationFactory,
    EquipmentConfigurationModelFactory,
    EquipmentConfigurationScopeFactory,
    LocationConfigurationScopeFactory,
    EquipmentConfigurationLinkFactory,
)

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


# Software

@pytest.fixture
def software_type_factory():
    return SoftwareTypeFactory


@pytest.fixture
def software_factory():
    return SoftwareFactory


# Configuration status

@pytest.fixture
def equipment_configuration_status_factory():
    return EquipmentConfigurationStatusFactory


@pytest.fixture
def active_configuration_status_factory():
    return ActiveConfigurationStatusFactory


@pytest.fixture
def draft_configuration_status_factory():
    return DraftConfigurationStatusFactory


@pytest.fixture
def retired_configuration_status_factory():
    return RetiredConfigurationStatusFactory


# Configuration

@pytest.fixture
def equipment_configuration_factory():
    return EquipmentConfigurationFactory


@pytest.fixture
def equipment_configuration_model_factory():
    return EquipmentConfigurationModelFactory


@pytest.fixture
def equipment_configuration_scope_factory():
    return EquipmentConfigurationScopeFactory


@pytest.fixture
def location_configuration_scope_factory():
    return LocationConfigurationScopeFactory


@pytest.fixture
def equipment_configuration_link_factory():
    return EquipmentConfigurationLinkFactory
