from typing import Sized
from urllib.parse import urlencode
import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_home_view_annonymous_user(client):
    url = reverse("home")
    response = client.get(url)
    assert response.status_code == 302
    assert "users/login" in response.url


@pytest.mark.django_db
def test_home_view_known_user(client, user_setup):
    user = user_setup
    client.force_login(user)
    url = reverse("home")
    response = client.get(url)
    assert response.status_code == 200
    assert "dashboards/overview.html" in [t.name for t in response.templates]


@pytest.mark.django_db
def test_custom_login_page_renders(client):
    response = client.get(reverse("users:login"))
    assert response.status_code == 200
    assert "users/login.html" in [t.name for t in response.templates]


@pytest.mark.django_db
def test_authenticated_user_redirects(client, user_setup):
    user = user_setup
    client.force_login(user)
    response = client.get(reverse("users:login"))
    assert response.status_code == 302
    assert response.url == reverse("users:landing")


@pytest.mark.django_db
def test_successful_login_redirects(client, django_user_model):
    user = django_user_model.objects.create_user(
        user_name="testuser",
        password="testpass",
        email="test@testing.com",
        first_name="test",
    )
    response = client.force_login(user)
    response = client.get(reverse("users:login"))
    assert response.status_code == 302
    assert response.url == reverse("users:landing")


@pytest.mark.django_db
def test_logout_confirmation_view_renders(client):
    response = client.get(reverse("users:logout"))

    assert response.status_code == 200
    assert "users/logout.html" in [t.name for t in response.templates]


@pytest.mark.django_db
def test_logout_view_logs_out_and_redirects(client, django_user_model):
    # Create and log in a user
    user = django_user_model.objects.create_user(
        user_name="testuser",
        password="testpass",
        email="test@testing.com",
        first_name="test",
    )
    response = client.force_login(user)

    # Call logout via POST (LogoutView requires POST by default for security)
    response = client.post(
        reverse("users:logout_confirmation")
    )  # Adjust URL name if needed

    # Check for redirect
    assert response.status_code == 302
    assert response.url == reverse("users:login")

    # Check that the user is logged out
    response = client.get(reverse("home"))  # Or another protected view
    assert not response.wsgi_request.user.is_authenticated


