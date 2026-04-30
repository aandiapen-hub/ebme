from users.models import Roles
import pytest

@pytest.mark.django_db  # This allows access to the database in this test
def test_role_str_representation():
    role = Roles.objects.create(role_name="Admin2")
    assert str(role) == "Admin2"


