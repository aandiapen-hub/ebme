
import pytest

from documents.tests.factories import AssetDocumentLinks
    

@pytest.fixture(scope='session')
def django_db_modify_db_settings():
    """Tell pytest-django to not create a test database."""
    return False

@pytest.fixture(scope='session')
def django_db_use_migrations():
    """Prevent test DB creation from scratch (use your existing DB schema)."""
    return False

@pytest.fixture
def user_setup(django_user_model):
    user = django_user_model.objects.create_user(
        user_name='testuser',
        password='testpass',
        email='test@testing.com',
        first_name='test',
    )
    return user


@pytest.fixture(scope="function")
def asset_documents(django_db_blocker):
    print('------------creating Asset Documents------------')
    with django_db_blocker.unblock():
        from assets.models import Tblassets  
        asset_documents = []
        for asset in Tblassets.objects.all():
            asset_documents.append(AssetDocumentLinks.create(link_row=asset.assetid))
        return asset_documents