import pytest
from django.contrib.auth.models import Permission
from pytest_django.asserts import assertTemplateUsed
from django.urls import reverse
from assets.models import (
    Tblassets,
    Tblmodel,
    Tblcustomer,
    Tblbrands,
    Tblcategories,
    TblAssetStatus,
    Tblppmschedules,
    Tbljob,
)
from assets.views import AssetJobsListView
from django.test import RequestFactory
from unittest.mock import patch

from documents.models import TemporaryUpload
from urllib.parse import urlencode
from django.core.files import File

from django.contrib.messages import get_messages


# test AssetCreateView
@pytest.mark.django_db
def test_asset_create_view_requires_login(client):
    url = reverse("assets:create_asset")  # Update to your actual URL name
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert "/login" in response.url.lower()  # Ensure it's going to the login page


@pytest.mark.django_db
def test_asset_create_view_permission_denied(client, user_setup):
    user = user_setup
    client.force_login(user)

    url = reverse("assets:create_asset")
    response = client.get(url)

    assert (
        response.status_code == 403
    )  # Depends on how CustomerAssetPermissionMixin handles it


@pytest.mark.django_db
def test_asset_create_view_success_post(
    client,
    user_setup,
    model,
    customer,
    asset_status,
):
    # Create user and force login
    user = user_setup

    permission = Permission.objects.get(codename="add_tblassets")
    user.user_permissions.add(permission)

    client.force_login(user)

    # Set up required related objects
    model_instance = model()
    customer_instance = customer()
    asset_status = asset_status()
    # Prepare form data
    form_data = {
        "modelid": model_instance.modelid,
        "customerid": customer_instance.customerid,
        "serialnumber": 12332,
        "asset_status_id": asset_status.pk,
        "ppmscheduleid": "",
    }
    url = reverse("assets:create_asset")
    response = client.post(url, data=form_data)
    created_asset = Tblassets.objects.last()
    assert created_asset.serialnumber == "12332"


# test AssetUpdateView
@pytest.mark.django_db
def test_asset_update_view_requires_login(client, asset):
    asset = asset
    url = reverse("assets:update_asset", kwargs={"pk": asset.assetid})
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert "/login" in response.url.lower()  # Ensure it's going to the login page


@pytest.mark.django_db
def test_asset_update_view_permission_denied(client, asset, user_setup):
    asset = asset
    user = user_setup
    client.force_login(user)

    # test denied permission
    url = reverse("assets:update_asset", kwargs={"pk": asset.assetid})
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_asset_update_view_renders(client, user_setup, asset):
    asset = asset
    user = user_setup
    client.force_login(user)

    user.customerid = asset.customerid
    user.save()
    permission = Permission.objects.get(codename="change_tblassets")
    user.user_permissions.add(permission)

    url = reverse("assets:update_asset", kwargs={"pk": asset.assetid})
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, "assets/update_form.html")


@pytest.mark.django_db
def test_asset_update_view_valid_data_updates_object(client, user_setup, asset):
    asset = asset
    user = user_setup

    client.force_login(user)

    user.customerid = asset.customerid
    user.save()
    permission = Permission.objects.get(codename="change_tblassets")
    user.user_permissions.add(permission)

    url = reverse("assets:update_asset", kwargs={"pk": asset.assetid})
    response = client.post(
        url,
        data={
            "serialnumber": "updated_serialnumber",
            "customerid": asset.customerid.customerid,  # Include the primary key of the customer
            "modelid": asset.modelid.modelid,
        },
    )

    asset.refresh_from_db()
    assert asset.serialnumber == "updated_serialnumber"
    assert response.status_code == 302  # Redirect after success


@pytest.mark.django_db
def test_asset_delete_view_login(client, asset):
    asset = asset
    url = reverse("assets:delete_asset", kwargs={"pk": asset.assetid})
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert "/login" in response.url.lower()  # Ensure it's going to the login page


@pytest.mark.django_db
def test_asset_delete_view_permission_denied(client, user_setup, asset):
    asset = asset
    user = user_setup
    client.force_login(user)
    url = reverse("assets:delete_asset", kwargs={"pk": asset.assetid})
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_asset_delete_view_renders(client, user_setup, asset):
    asset = asset
    user = user_setup

    user.customerid = asset.customerid
    user.save()

    permission = Permission.objects.get(codename="delete_tblassets")
    user.user_permissions.add(permission)

    client.force_login(user)
    url = reverse("assets:delete_asset", kwargs={"pk": asset.assetid})
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, "assets/partials/delete_modal.html")
    assert response.context["view_type"] == "delete"


@pytest.mark.django_db
def test_asset_delete_view_post_success(client, user_setup, asset):
    asset = asset

    user = user_setup
    permission = Permission.objects.get(codename="delete_tblassets")
    user.user_permissions.add(permission)

    user.customerid = asset.customerid
    user.save()

    client.force_login(user)
    url = reverse("assets:delete_asset", kwargs={"pk": asset.assetid})
    response = client.post(url)

    assert response["HX-Redirect"] == reverse("assets:assets_list")


@pytest.mark.django_db
def test_asset_delete_view_handles_exception(client, user_setup, asset):
    asset = asset
    user = user_setup

    user.customerid = asset.customerid
    user.save()

    permission = Permission.objects.get(codename="delete_tblassets")
    user.user_permissions.add(permission)

    client.force_login(user)
    # Mock the delete method to raise an exception
    with patch(
        "assets.models.Tblassets.delete", side_effect=Exception("Mocked deletion error")
    ):
        url = reverse("assets:delete_asset", kwargs={"pk": asset.assetid})
        response = client.post(url)

        # Assert the response status code
        assert (
            response.status_code == 200
        )  # The view renders the template with the error message

        from django.contrib.messages import get_messages

        storage = list(get_messages(response.wsgi_request))
        assert any("An error occurred" in str(msg) for msg in storage)
        # Assert the template used
        assertTemplateUsed(response, "assets/partials/delete_modal.html")


@pytest.mark.django_db
def test_filtered_asset_table_view_login(
    client,
):
    url = reverse("assets:assets_list")
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert "/login" in response.url.lower()  # Ensure it's going to the login page


@pytest.mark.django_db
def test_filtered_asset_table_view_permission_denied(client, user_setup):
    user = user_setup
    client.force_login(user)
    url = reverse("assets:assets_list")
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.parametrize("search_term", ["med 123", "1,2,3"])
@pytest.mark.django_db
def test_filtered_asset_table_view_renders(
    django_db_setup, client, user_setup, asset, search_term
):
    user = user_setup

    permission = Permission.objects.get(codename="view_assetview")
    user.user_permissions.add(permission)

    asset = asset
    user.customerid = asset.customerid
    user.save()
    client.force_login(user)

    url = reverse("assets:assets_list")

    # test html get
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, "assets/assetview_filter.html")
    content = response.content.decode()

    # test htmx get
    response = client.get(url, HTTP_HX_REQUEST="true")
    assert response.status_code == 200

    # test with query parameters
    query_params = urlencode({"universal_search": search_term})
    url_with_params = f"{url}?{query_params}"
    response = client.get(url_with_params, HTTP_HX_REQUEST="true")
    assert response.status_code == 200


@pytest.mark.django_db
def test_filtered_asset_filterset(django_db_setup, client, user_setup, asset):
    user = user_setup

    permission = Permission.objects.get(codename="view_assetview")
    user.user_permissions.add(permission)

    user.customerid = asset.customerid
    user.save()
    client.force_login(user)

    base_url = reverse("assets:assets_list")

    # test supersearch
    query_string = urlencode({"supersearch": "Meditech 123 $ bla bla"})
    url = f"{base_url}?{query_string}"
    response = client.get(url, HTTP_HX_REQUEST="true")
    assert response.status_code == 200
