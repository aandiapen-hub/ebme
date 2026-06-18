from .factories import(
    AssetFactory,
)
import pytest



@pytest.fixture
def create_assets():
    def _create_assets(count=10, **kwargs):
        return AssetFactory.create_batch(count, **kwargs)

    return _create_assets
