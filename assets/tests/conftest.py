from .factories import(
    AssetFactory,
    ModelFactory,
)
import pytest


@pytest.fixture
def model():
    return ModelFactory

@pytest.fixture
def create_assets():
    def _create_assets(count=10, **kwargs):
        return AssetFactory.create_batch(count, **kwargs)

    return _create_assets
