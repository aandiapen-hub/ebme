import pytest
from .factories import UserFactory, CustomerFactory, AssetFactory, JobFactory

@pytest.fixture
def user():
    return UserFactory

@pytest.fixture
def customer():
    return CustomerFactory

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
