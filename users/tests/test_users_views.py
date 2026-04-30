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


# test columns chooser
@pytest.mark.django_db
def test_column_chooser_requires_login(client, django_user_model):
    url = reverse("users:column_chooser")
    response = client.get(url)

    assert response.status_code == 302
    assert "/login" in response.url.lower()


@pytest.mark.django_db
def test_column_chooser_view_renders(client, django_user_model, user_setup):
    user = user_setup
    client.force_login(user)
    base_url = reverse("users:column_chooser")
    query_params = urlencode({"appmodel": "assets.AssetView"})
    url = f"{base_url}?{query_params}"
    response = client.get(url)

    assert response.status_code == 200
    assert "users/partials/column_chooser.html" in [t.name for t in response.templates]


@pytest.mark.django_db
def test_column_chooser_post_updates_preferences(client, django_user_model, user_setup):
    user = user_setup
    client.force_login(user)
    base_url = reverse("users:column_chooser")
    query_params = urlencode({"appmodel": "assets.AssetView"})
    url = f"{base_url}?{query_params}"
    response = client.get(url)
    assert response.status_code == 200

    # Post data to update preferences
    post_data = {
        "request_model": "AssetView",
        "columns": ["assetid", "serialnumber", "modelname"],
        "success_url": "assets:assets_list",
    }
    response = client.post(url, post_data)

    # Check for redirect to success URL
    assert response.status_code == 302
    assert reverse("assets:assets_list") in response.url

    # Verify that the user's preferences were updated
    profile = user.userprofiles
    visible_columns = profile.get_preference("AssetView", "visible_columns")

    assert visible_columns == [
        "assetid",
        "serialnumber",
        "modelname",
    ]

    response = client.get(url)
    assert response.context["visible_columns"] == [
        "assetid",
        "serialnumber",
        "modelname",
    ]
