from django.contrib.messages import get_messages
from django.contrib.auth.models import Permission
from urllib.parse import urlencode
import pytest
from django.urls import reverse
from pytest_django.asserts import assertTemplateUsed

from parts.models import Tblpartslist, Tblpartsprice, TblPartModel

from assets.models import Tblpartsused
from django.db import IntegrityError, transaction
# test parts table view


@pytest.mark.django_db
def test_parts_table_view_requires_login(client):
    url = reverse("parts:parts")
    response = client.get(url)
    assert (
        response.status_code == 302
    )  # Expecting a redirect to the login page if not authenticated
    assert "/login" in response.url.lower()


@pytest.mark.django_db
def test_parts_table_view_authentication_required(client, user):
    user = user()
    client.force_login(user)
    url = reverse("parts:parts")
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_parts_table_view_renders(client, user):
    user = user()
    permission = Permission.objects.get(codename="view_tblpartslist")
    user.user_permissions.add(permission)
    client.force_login(user)
    url = reverse("parts:parts")
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, "parts/parts_list.html")
    # test filter
    response_with_params = client.get(url)
    assert response_with_params.status_code == 200

    response_htmx = client.get(url, HTTP_HX_REQUEST="true")
    assert response_htmx.status_code == 200


# test PartUpdateView


@pytest.mark.django_db
def test_part_update_view_login_required(client, part):
    part = part()
    url = reverse("parts:update_part", kwargs={"pk": part.pk})
    response = client.get(url)
    assert response.status_code == 302
    assert "/login" in response.url.lower()


@pytest.mark.django_db
def test_part_update_view_authentication_required(client, user, part):
    part = part()
    user = user()
    client.force_login(user)
    url = reverse("parts:update_part", kwargs={"pk": part.pk})
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_part_update_view_renders(client, user, part):
    part = part()
    user = user()
    permission = Permission.objects.get(codename="change_tblpartslist")
    user.user_permissions.add(permission)
    client.force_login(user)
    url = reverse("parts:update_part", kwargs={"pk": part.partid})
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, "parts/update_part.html")


@pytest.mark.django_db
def test_part_update_view_post_successful(client, user, part):
    part = part()
    user = user()
    permission = Permission.objects.get(codename="change_tblpartslist")
    user.user_permissions.add(permission)
    client.force_login(user)
    url = reverse("parts:update_part", kwargs={"pk": part.partid})
    data = {
        "short_name": "Updated Part",
        "description": "Updated Description",
        "part_id": part.partid,
        "part_number": part.part_number,
    }
    response = client.post(url, data)
    assert response.status_code == 302

    part.refresh_from_db()
    assert part.short_name == "Updated Part"


# test PartDeleteView
@pytest.mark.django_db
def test_part_delete_view_login_required(client, part):
    part = part()
    url = reverse("parts:delete_part", kwargs={"pk": part.pk})
    response = client.get(url)
    assert response.status_code == 302
    assert "/login" in response.url.lower()


@pytest.mark.django_db
def test_part_delete_view_authentication_required(client, user, part):
    part = part()
    user = user()
    client.force_login(user)
    url = reverse("parts:delete_part", kwargs={"pk": part.pk})
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_part_delete_view_renders(client, user, part):
    part = part()
    user = user()
    permission = Permission.objects.get(codename="delete_tblpartslist")
    user.user_permissions.add(permission)
    client.force_login(user)
    url = reverse("parts:delete_part", kwargs={"pk": part.partid})
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, "parts/delete_part.html")


@pytest.mark.django_db
def test_part_delete_view_post_successful(client, user, part):
    part = part()
    user = user()
    permission = Permission.objects.get(codename="delete_tblpartslist")
    user.user_permissions.add(permission)
    client.force_login(user)
    url = reverse("parts:delete_part", kwargs={"pk": part.partid})
    response = client.post(url)
    assert response.status_code == 302


@pytest.mark.django_db
def test_part_delete_view_post_unsuccessful(client, user, active_spare_part, job):
    part = active_spare_part
    Tblpartsused.objects.create(jobid=job(), quantity=1, partid=part)
    user = user()
    permission = Permission.objects.get(codename="delete_tblpartslist")
    user.user_permissions.add(permission)
    client.force_login(user)
    url = reverse("parts:delete_part", kwargs={"pk": part.partid})
    response = client.post(url)
    assert response.status_code == 200

    assert response.context["form"].errors


# test PartCreateView
@pytest.mark.django_db
def test_part_create_view_login_required(client):
    url = reverse("parts:create_part")
    response = client.get(url)
    assert response.status_code == 302
    assert "/login" in response.url.lower()


@pytest.mark.django_db
def test_part_create_view_authentication_required(client, user):
    user = user()
    client.force_login(user)
    url = reverse("parts:create_part")
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_part_create_view_renders(client, user):
    user = user()
    permission = Permission.objects.get(codename="add_tblpartslist")
    user.user_permissions.add(permission)
    client.force_login(user)
    url = reverse("parts:create_part")
    query_params = urlencode({"part_number": "test"})
    response = client.get(f"{url}?{query_params}")
    assert response.status_code == 200
    assertTemplateUsed(response, "parts/create_part.html")


@pytest.mark.django_db
def test_part_create_view_post_successful(client, user, supplier, order_unit):
    user = user()
    permission = Permission.objects.get(codename="add_tblpartslist")
    user.user_permissions.add(permission)
    client.force_login(user)
    url = reverse("parts:create_part")
    supplier = supplier()

    data = {
        "short_name": "New Partsss",
        "description": "New Description",
        "part_number": "1234567890123sss",
        "inactive": False,
        "supplier_id": supplier.supplier_id,
        "order_unit": order_unit().pk,
    }
    response = client.post(url, data)
    messages = list(get_messages(response.wsgi_request))
    assert response.status_code == 302
    new_part = Tblpartslist.objects.last()
    assert new_part.part_number == "1234567890123sss"


@pytest.mark.django_db
def test_part_create_view_post_unsuccessful_duplicate_record(client, user, part):
    user = user()
    permission = Permission.objects.get(codename="add_tblpartslist")
    user.user_permissions.add(permission)
    client.force_login(user)
    url = reverse("parts:create_part")
    part = part()
    supplier = part.supplier_id.pk
    part_number = part.part_number
    data = {
        "short_name": "New",
        "description": "New Description",
        "part_number": part_number,
        "inactive": False,
        "supplier_id": supplier,
        "order_unit": part.order_unit.pk,
    }
    # Simulate failure: duplicate part number
    response = client.post(url, data)
    assert response.context["form"].errors
    assert response.status_code == 200


# test Spare Parts Price List View
@pytest.mark.django_db
def test_spare_part_price_list_view_requires_login(client):
    url = reverse("parts:part_prices")
    response = client.get(url)
    assert response.status_code == 302
    assert "/login" in response.url.lower()


@pytest.mark.django_db
def test_spare_part_price_list_view_authentication_required(client, user):
    user = user()
    client.force_login(user)
    url = reverse("parts:part_prices")
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_spare_part_price_list_view_renders(client, user, part_price):
    part_price = part_price()

    user = user()
    permission = Permission.objects.get(codename="view_tblpartsprice")
    user.user_permissions.add(permission)
    client.force_login(user)
    url = reverse("parts:part_prices")
    query_params = urlencode({"partid": part_price.partid.pk})
    # test response with partid
    response = client.get(f"{url}?{query_params}")
    assert response.status_code == 200
    assertTemplateUsed(response, "parts/partials/part_prices.html")

    # test response without partid
    response = client.get(url)
    assert response.status_code == 200


# test_SparePartPriceCreateView
@pytest.mark.django_db
def test_spare_part_price_create_view_login_required(client):
    url = reverse("parts:part_prices_create")
    response = client.get(url)
    assert response.status_code == 302
    assert "/login" in response.url.lower()


@pytest.mark.django_db
def test_spare_part_prices_create_view_authentication_required(client, user):
    user = user()
    client.force_login(user)
    url = reverse("parts:part_prices_create")
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_spare_part_prices_create_view_renders(client, user):
    user = user()
    permission = Permission.objects.get(codename="add_tblpartsprice")
    user.user_permissions.add(permission)
    client.force_login(user)
    url = reverse("parts:part_prices_create")
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, "parts/partials/part_prices_create.html")


@pytest.mark.django_db
def test_spare_part_prices_create_view_post_successful(client, user, part):
    part = part()
    user = user()
    permission = Permission.objects.get(codename="add_tblpartsprice")
    user.user_permissions.add(permission)
    client.force_login(user)
    url = reverse("parts:part_prices_create")
    data = {
        "partid": part.pk,
        "price": 100.00,
        "effectivedate": "2023-10-01",
    }
    response = client.post(url, data)

    assert response.status_code == 302

    # Check if the price was created
    from parts.models import Tblpartsprice

    new_price = Tblpartsprice.objects.last()
    assert new_price.price == 100.00


@pytest.mark.django_db
def test_spare_part_prices_create_view_post_unsuccessful(client, user, part):
    part = part()
    user = user()
    permission = Permission.objects.get(codename="add_tblpartsprice")
    user.user_permissions.add(permission)
    client.force_login(user)
    url = reverse("parts:part_prices_create")
    data = {
        "partid": part.pk,
        "price": -100.00,
        "effectivedate": "2023-10-01",
    }

    with pytest.raises(transaction.TransactionManagementError):
        try:
            # Simulate failure: missing required field
            response = client.post(url, data)

        except IntegrityError:
            messages = [m.message for m in get_messages(response.wsgi_request)]
            assert "valid_price" in messages
            # Django marks transaction as broken
            pass


# test SparePartPriceDeleteView
@pytest.mark.django_db
def test_spare_part_price_delete_view_login_required(client, part_price):
    part_price = part_price()
    url = reverse("parts:part_prices_delete", kwargs={"pk": part_price.pk})
    response = client.get(url)
    assert response.status_code == 302
    assert "/login" in response.url.lower()


@pytest.mark.django_db
def test_spare_part_price_delete_view_authentication_required(client, user, part_price):
    part_price = part_price()
    user = user()
    client.force_login(user)
    url = reverse("parts:part_prices_delete", kwargs={"pk": part_price.pk})
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_spare_part_price_delete_view_renders(client, user, part_price):
    part_price = part_price()
    user = user()
    permission = Permission.objects.get(codename="delete_tblpartsprice")
    user.user_permissions.add(permission)
    client.force_login(user)
    url = reverse("parts:part_prices_delete", kwargs={"pk": part_price.pk})
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, "parts/partials/part_prices_delete.html")


@pytest.mark.django_db
def test_spare_part_price_delete_view_post_successfull(client, user, part_price):
    part_price = part_price()
    user = user()
    permission = Permission.objects.get(codename="delete_tblpartsprice")
    user.user_permissions.add(permission)
    client.force_login(user)
    url = reverse("parts:part_prices_delete", kwargs={"pk": part_price.pk})
    response = client.post(url)

    assert response.status_code == 302

    with pytest.raises(Tblpartsprice.DoesNotExist):
        part_price.refresh_from_db()


@pytest.mark.django_db
def test_spare_part_price_delete_view_post_htmx_successfull(client, user, part_price):
    part_price = part_price()
    user = user()
    permission = Permission.objects.get(codename="delete_tblpartsprice")
    user.user_permissions.add(permission)
    client.force_login(user)
    price = Tblpartsprice.objects.last()
    url = reverse("parts:part_prices_delete", kwargs={"pk": part_price.pk})
    response = client.post(url, HTTP_HX_REQUEST="true")

    assert response.status_code == 200

    with pytest.raises(Tblpartsprice.DoesNotExist):
        price.refresh_from_db()


# test SparePartPriceUpdateView
@pytest.mark.django_db
def test_spare_part_price_update_view_login_required(client, part_price):
    part_price = part_price()
    url = reverse("parts:part_prices_update", kwargs={"pk": part_price.pk})
    response = client.get(url)
    assert response.status_code == 302
    assert "/login" in response.url.lower()


@pytest.mark.django_db
def test_spare_part_price_update_view_authentication_required(client, user, part_price):
    part_price = part_price()
    user = user()
    client.force_login(user)
    url = reverse("parts:part_prices_update", kwargs={"pk": 0})
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_spare_part_price_update_view_renders(client, user, part_price):
    part_price = part_price()
    user = user()
    permission = Permission.objects.get(codename="change_tblpartsprice")
    user.user_permissions.add(permission)
    client.force_login(user)
    url = reverse("parts:part_prices_update", kwargs={"pk": part_price.pk})
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, "parts/partials/part_prices_update.html")


@pytest.mark.django_db
def test_spare_part_price_update_view_post_successful(client, user, part_price):
    part_price = part_price()
    user = user()
    permission = Permission.objects.get(codename="change_tblpartsprice")
    user.user_permissions.add(permission)
    client.force_login(user)
    price = Tblpartsprice.objects.last()
    url = reverse("parts:part_prices_update", kwargs={"pk": part_price.pk})
    data = {
        "partid": part_price.partid.pk,
        "price": 75.00,
        "effectivedate": "2023-11-01",
    }
    response = client.post(url, data)

    assert response.status_code == 302

    price.refresh_from_db()
    assert price.price == 75.00


# test PartLinkedModelListView
@pytest.mark.django_db
def test_part_linked_model_list_view_requires_login(client):
    url = reverse("parts:linked_models")
    response = client.get(url)
    assert response.status_code == 302
    assert "/login" in response.url.lower()


@pytest.mark.django_db
def test_part_linked_model_list_view_authentication_required(client, user):
    user = user()
    client.force_login(user)
    url = reverse("parts:linked_models")
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_part_linked_model_list_view_renders(client, user, part):
    user = user()
    permission = Permission.objects.get(codename="view_tblpartmodel")
    user.user_permissions.add(permission)
    client.force_login(user)
    url = reverse("parts:linked_models")
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, "parts/partials/linked_models.html")

    # test with partid
    query_params = urlencode({"partid": part().pk})
    response_with_params = client.get(f"{url}?{query_params}")
    assert response_with_params.status_code == 200


# test LinkModelCreateTableView
@pytest.mark.django_db
def test_link_model_create_view_login_required(client):
    url = reverse("parts:linked_models_create")
    response = client.get(url)
    assert response.status_code == 302
    assert "/login" in response.url.lower()


@pytest.mark.django_db
def test_link_model_create_view_authentication_required(client, user):
    user = user()
    client.force_login(user)
    url = reverse("parts:linked_models_create")
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_link_model_create_view_renders(client, user, part):
    user = user()
    permission = Permission.objects.get(codename="add_tblpartmodel")
    user.user_permissions.add(permission)
    client.force_login(user)
    url = reverse("parts:linked_models_create")
    query_params = urlencode({"partid": part().pk})
    response = client.get(f"{url}?{query_params}")
    assert response.status_code == 200
    assertTemplateUsed(response, "parts/partials/linked_model_create.html")


@pytest.mark.django_db
def test_link_model_create_view_post_successful(client, user, part, assets):
    user = user()
    permission = Permission.objects.get(codename="add_tblpartmodel")
    user.user_permissions.add(permission)
    client.force_login(user)
    url = reverse("parts:linked_models_create")

    part = part()
    assets = assets()
    models = [asset.modelid.pk for asset in assets]

    data = {"partid": part.partid, "models": models}
    response = client.post(url, data)

    assert response.status_code == 302

    new_link = TblPartModel.objects.last()
    assert new_link.part.partid == part.partid
    assert new_link.model.modelid == models[-1]


# test PartModelDeleteview


@pytest.mark.django_db
def test_link_model_delete_view_login_required(client, part_model):
    part_model = part_model()
    url = reverse("parts:linked_models_delete", kwargs={"pk": part_model.pk})
    response = client.get(url)
    assert response.status_code == 302
    assert "/login" in response.url.lower()


@pytest.mark.django_db
def test_link_model_delete_view_authentication_required(client, user, part_model):
    part_model = part_model()
    user = user()
    client.force_login(user)
    url = reverse("parts:linked_models_delete", kwargs={"pk": part_model.pk})
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_link_model_delete_view_renders(client, user, part_model):
    part_model = part_model()
    user = user()
    permission = Permission.objects.get(codename="delete_tblpartmodel")
    user.user_permissions.add(permission)
    client.force_login(user)
    part_model = TblPartModel.objects.last()
    url = reverse("parts:linked_models_delete", kwargs={"pk": part_model.part_model_id})
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, "parts/partials/linked_model_delete.html")


@pytest.mark.django_db
def test_link_model_delete_view_post_htmx_successful(client, user, part_model):
    part_model = part_model()
    user = user()
    permission = Permission.objects.get(codename="delete_tblpartmodel")
    user.user_permissions.add(permission)
    client.force_login(user)
    part_model = TblPartModel.objects.last()
    url = reverse("parts:linked_models_delete", kwargs={"pk": part_model.part_model_id})
    response = client.post(url, HTTP_HX_REQUEST="true")

    assert response.status_code == 200

    with pytest.raises(TblPartModel.DoesNotExist):
        part_model.refresh_from_db()


@pytest.mark.django_db
def test_link_model_delete_view_post_successful(client, user, part_model):

    part_model = part_model()
    user = user()
    permission = Permission.objects.get(codename="delete_tblpartmodel")
    user.user_permissions.add(permission)
    client.force_login(user)
    part_model = TblPartModel.objects.last()
    url = reverse("parts:linked_models_delete", kwargs={"pk": part_model.part_model_id})
    response = client.post(url)

    assert response.status_code == 302

    with pytest.raises(TblPartModel.DoesNotExist):
        part_model.refresh_from_db()
