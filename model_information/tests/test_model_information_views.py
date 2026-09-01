from reportlab.pdfbase.pdfmetrics import test

from model_information.services import configuration
import pytest
from django.contrib.auth.models import Permission
from pytest_django.asserts import assertTemplateUsed
from django.urls import reverse
from assets.models import (
    Tblmodel,
    Tblbrands,
    Tblcategories,
    Tblcheckslists,
)
from urllib.parse import urlencode
from model_information.models import (
    EquipmentConfiguration,
    EquipmentConfigurationModel,
    EquipmentConfigurationScope,
    Software,
    SoftwareModel,
)

from assets.tests.factories import ModelFactory, CategoryFactory
from jobs.tests.factories import TestsCarriedOutFactory
# test brand views


# test BrandTableView
@pytest.mark.django_db
def test_brand_table_view_requires_login(client):
    url = reverse("model_information:brandlist")  # Update to your actual URL name
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert "/login" in response.url.lower()  # Ensure it's going to the login page


@pytest.mark.django_db
def test_brand_table_view_permission_denied(client, user):
    user = user()
    client.force_login(user)

    url = reverse("model_information:brandlist")  # Update to your actual URL name
    response = client.get(url)

    assert (
        response.status_code == 403
    )  # Depends on how CustomerAssetPermissionMixin handles it


@pytest.mark.parametrize("search_term", ["med 123", "1,2,3"])
@pytest.mark.django_db
def test_brand_table_view_renders(client, user, mocker, search_term):
    user = user()
    client.force_login(user)
    mocker.patch(
        "django.contrib.auth.mixins.PermissionRequiredMixin.has_permission",
        return_value=True,
    )

    url = reverse("model_information:brandlist")  # Update to your actual URL name

    response = client.get(url)

    # test html
    assert (
        response.status_code == 200
    )  # Depends on how CustomerAssetPermissionMixin handles it
    assertTemplateUsed(response, "filter_table.html")

    # test htmx
    response = client.get(url, HTTP_HX_REQUEST="true")
    assert response.status_code == 200

    # test filter
    query_string = urlencode({"universal_search": search_term})
    url = f"{url}?{query_string}"
    response = client.get(url, HTTP_HX_REQUEST="true")
    assert response.status_code == 200


# test BrandUpdateview
@pytest.mark.django_db
def test_brand_update_view_requires_login(client, brand):
    brand = brand()
    url = reverse(
        "model_information:update_brand", kwargs={"pk": brand.brandid}
    )  # Update to your actual URL name
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert "/login" in response.url.lower()  # Ensure it's going to the login page


@pytest.mark.django_db
def test_brand_update_view_requires_permission(client, user, brand):
    brand = brand()
    user = user()

    url = reverse(
        "model_information:update_brand", kwargs={"pk": brand.brandid}
    )  # Update to your actual URL name
    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 403  # Redirect to login


@pytest.mark.django_db
def test_brand_update_view_renders(client, user, brand):
    brand = brand()
    user = user()

    permission = Permission.objects.get(codename="change_tblbrands")
    user.user_permissions.add(permission)
    url = reverse(
        "model_information:update_brand", kwargs={"pk": brand.brandid}
    )  # Update to your actual URL name
    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 200  # Redirect to login
    assertTemplateUsed(response, "model_information/brand_update.html")


@pytest.mark.django_db
def test_brand_update_view_posts_successfully(client, user, brand):
    brand = brand()
    user = user()

    permission = Permission.objects.get(codename="change_tblbrands")
    user.user_permissions.add(permission)
    url = reverse(
        "model_information:update_brand", kwargs={"pk": brand.brandid}
    )  # Update to your actual URL name
    client.force_login(user)

    # test html post
    form = {"brandname": "brandtest"}
    response = client.post(url, data=form)

    assert response.status_code == 302
    brand.refresh_from_db()
    assert brand.brandname == "brandtest"
    assert response.url == reverse(
        "model_information:brand_detail", kwargs={"pk": brand.pk}
    )


# test BrandCreateView


@pytest.mark.django_db
def test_brand_create_view_requires_login(client):
    url = reverse("model_information:create_brand")  # Update to your actual URL name
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert "/login" in response.url.lower()  # Ensure it's going to the login page


@pytest.mark.django_db
def test_brand_create_view_requires_permission(client, user):
    user = user()

    url = reverse("model_information:create_brand")

    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_brand_create_view_renders(client, user):
    user = user()

    permission = Permission.objects.get(codename="add_tblbrands")
    user.user_permissions.add(permission)

    url = reverse("model_information:create_brand")
    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, "model_information/brand_create.html")


@pytest.mark.django_db
def test_brand_create_view_posts_successfully(client, user):
    user = user()

    permission = Permission.objects.get(codename="add_tblbrands")
    user.user_permissions.add(permission)

    url = reverse("model_information:create_brand")
    client.force_login(user)

    # test html post
    form = {"brandname": "brandtest"}
    response = client.post(url, data=form)

    assert response.status_code == 302
    brand = Tblbrands.objects.last()
    assert brand.brandname == "brandtest"


@pytest.mark.django_db
def test_brand_create_view_requires_posts_unsuccessful(client, user):
    user = user()

    permission = Permission.objects.get(codename="add_tblbrands")
    user.user_permissions.add(permission)

    url = reverse("model_information:create_brand")
    client.force_login(user)

    # test html post
    form = {}
    response = client.post(url, data=form)

    assert response.status_code == 200
    assert response.context["form"].errors


# test BrandDeleteView
@pytest.mark.django_db
def test_brand_delete_view_requires_login(client, brand):
    brand = brand()
    url = reverse(
        "model_information:delete_brand", kwargs={"pk": brand.brandid}
    )  # Update to your actual URL name
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert "/login" in response.url.lower()  # Ensure it's going to the login page


@pytest.mark.django_db
def test_brand_delete_view_requires_permission(client, user, brand):
    brand = brand()
    user = user()

    url = reverse(
        "model_information:delete_brand", kwargs={"pk": brand.brandid}
    )  # Update to your actual URL name
    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 403  # Redirect to login


@pytest.mark.django_db
def test_brand_delete_view_renders(client, user, brand):
    brand = brand()
    user = user()

    permission = Permission.objects.get(codename="delete_tblbrands")
    user.user_permissions.add(permission)

    url = reverse(
        "model_information:delete_brand", kwargs={"pk": brand.brandid}
    )  # Update to your actual URL name
    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 200  # Redirect to login
    assertTemplateUsed(response, "model_information/brand_delete.html")


@pytest.mark.django_db
def test_brand_delete_view_posts_unsuccessfully(client, user, brand, model):

    brand = brand()
    user = user()
    model = model(brandid=brand)

    permission = Permission.objects.get(codename="delete_tblbrands")
    user.user_permissions.add(permission)
    url = reverse("model_information:delete_brand", kwargs={"pk": brand.pk})
    client.force_login(user)

    response = client.post(url)

    assert response.context["form"].errors


@pytest.mark.django_db
def test_brand_delete_view_requires_posts_successfully(client, user, brand):
    brand = brand()
    user = user()

    permission = Permission.objects.get(codename="delete_tblbrands")
    user.user_permissions.add(permission)

    url = reverse("model_information:delete_brand", kwargs={"pk": brand.pk})
    client.force_login(user)

    response = client.post(url)
    assert response.status_code == 302
    assert not Tblbrands.objects.filter(brandid=brand.pk).exists()


# test ModelTableView
@pytest.mark.django_db
def test_model_table_view_requires_login(client):
    url = reverse("model_information:modellist")  # Update to your actual URL name
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert "/login" in response.url.lower()  # Ensure it's going to the login page


@pytest.mark.django_db
def test_model_table_view_permission_denied(client, user):
    user = user()
    client.force_login(user)

    url = reverse("model_information:modellist")  # Update to your actual URL name
    response = client.get(url)

    assert (
        response.status_code == 403
    )  # Depends on how CustomerAssetPermissionMixin handles it


@pytest.mark.django_db
def test_model_table_view_renders(client, user):
    user = user()
    permission = Permission.objects.get(codename="view_tblmodel")
    user.user_permissions.add(permission)
    client.force_login(user)

    url = reverse("model_information:modellist")  # Update to your actual URL name

    response = client.get(url)

    # test html
    assert (
        response.status_code == 200
    )  # Depends on how CustomerAssetPermissionMixin handles it
    assertTemplateUsed(response, "filter_table.html")

    # test htmx
    response = client.get(url, HTTP_HX_REQUEST="true")
    assert response.status_code == 200

    # test filter
    query_string = urlencode({"universal_search": ""})
    url = f"{url}?{query_string}"
    response = client.get(url, HTTP_HX_REQUEST="true")
    assert response.status_code == 200


# test ModelUpdateView
@pytest.mark.django_db
def test_model_update_view_requires_login(client, model):
    model = model()
    url = reverse("model_information:update_model", kwargs={"pk": model.modelid})
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert "/login" in response.url.lower()  # Ensure it's going to the login page


@pytest.mark.django_db
def test_model_update_view_requires_permission(client, user, model):
    model = model()
    url = reverse("model_information:update_model", kwargs={"pk": model.modelid})

    user = user()

    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_model_update_view_renders(client, user, model):
    model = model()
    url = reverse("model_information:update_model", kwargs={"pk": model.modelid})

    permission = Permission.objects.get(codename="change_tblmodel")
    user = user()
    user.user_permissions.add(permission)

    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, "model_information/model_update.html")


@pytest.mark.django_db
def test_model_update_view_posts_successfully(client, user, model):
    model = model()
    url = reverse("model_information:update_model", kwargs={"pk": model.modelid})

    permission = Permission.objects.get(codename="change_tblmodel")
    user = user()
    user.user_permissions.add(permission)

    client.force_login(user)

    # test html post
    form = {
        "modelname": "testmodel",
        "brandid": model.brandid.brandid,
        "categoryid": model.categoryid.categoryid,
    }
    response = client.post(url, data=form)
    assert response.status_code == 302
    model.refresh_from_db()
    assert model.modelname == "testmodel"
    assert response.url == reverse(
        "model_information:model_view", kwargs={"pk": model.modelid}
    )


# test ModelCreateView
@pytest.mark.django_db
def test_model_create_view_requires_login(client):
    url = reverse("model_information:create_model")  # Update to your actual URL name
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert "/login" in response.url.lower()  # Ensure it's going to the login page


@pytest.mark.django_db
def test_model_create_view_requires_permission(client, user):
    user = user()
    url = reverse("model_information:create_model")

    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_model_create_view_renders(client, user):
    user = user()

    permission = Permission.objects.get(codename="add_tblmodel")
    user.user_permissions.add(permission)

    url = reverse("model_information:create_model")
    query_params = urlencode({"gtin": 123554})

    client.force_login(user)
    response = client.get(f"{url}?{query_params}")

    assert response.status_code == 200
    assertTemplateUsed(response, "model_information/partials/model_create.html")


@pytest.mark.django_db
def test_model_create_view_requires_posts_successfully(client, user, brand, category):
    user = user()

    permission = Permission.objects.get(codename="add_tblmodel")
    user.user_permissions.add(permission)

    url = reverse("model_information:create_model")
    client.force_login(user)

    # test html post
    form = {
        "modelname": "testmodel",
        "brandid": brand().pk,
        "categoryid": category().pk,
    }
    response = client.post(url, data=form)

    created_model = Tblmodel.objects.last()
    assert response.status_code == 302
    assert created_model.modelname == "testmodel"
    assert response.url == reverse(
        "model_information:model_view", kwargs={"pk": created_model.modelid}
    )


# test ModelDeleteView


@pytest.mark.django_db
def test_model_delete_view_requires_login(client, model):
    model = model()
    url = reverse("model_information:delete_model", kwargs={"pk": model.modelid})
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert "/login" in response.url.lower()  # Ensure it's going to the login page


@pytest.mark.django_db
def test_model_delete_view_requires_permission(client, user, model):
    model = model()
    url = reverse("model_information:delete_model", kwargs={"pk": model.modelid})
    user = user()

    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 403  # Redirect to login


@pytest.mark.django_db
def test_model_delete_view_renders(client, user, model):
    model = model()
    url = reverse("model_information:delete_model", kwargs={"pk": model.modelid})
    user = user()

    permission = Permission.objects.get(codename="delete_tblmodel")
    user.user_permissions.add(permission)

    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, "model_information/model_delete.html")


@pytest.mark.django_db
def test_model_delete_view_posts_unsuccessfully(client, user, model, asset):
    asset = asset()
    model = asset.modelid
    url = reverse("model_information:delete_model", kwargs={"pk": model.modelid})
    user = user()
    permission = Permission.objects.get(codename="delete_tblmodel")
    user.user_permissions.add(permission)

    client.force_login(user)

    response = client.post(url)
    assert response.context["form"].errors


@pytest.mark.django_db
def test_model_delete_view_posts_successfully(client, user, model):
    model = model()
    user = user()
    url = reverse("model_information:delete_model", kwargs={"pk": model.modelid})
    permission = Permission.objects.get(codename="delete_tblmodel")
    user.user_permissions.add(permission)

    client.force_login(user)

    response = client.post(url)
    assert response.status_code == 302
    assert response.url == reverse("model_information:modellist")
    assert not Tblmodel.objects.filter(modelid=model.pk).exists()


# test ModelDetailView
@pytest.mark.django_db
def test_model_detail_view_requires_login(client, model):
    model = model()
    url = reverse("model_information:model_view", kwargs={"pk": model.modelid})
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert "/login" in response.url.lower()  # Ensure it's going to the login page


@pytest.mark.django_db
def test_model_detail_view_requires_permission(client, user, model):
    model = model()
    url = reverse("model_information:model_view", kwargs={"pk": model.modelid})
    user = user()

    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 403  # Redirect to login


@pytest.mark.django_db
def test_model_detail_view_renders(client, user, model):
    model = model()
    url = reverse("model_information:model_view", kwargs={"pk": model.modelid})

    user = user()
    permission = Permission.objects.get(codename="view_tblmodel")
    user.user_permissions.add(permission)

    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, "model_information/model_view.html")


# ----------------
# test Categories
# ----------------
#
# test FilteredCategoryTableView
@pytest.mark.django_db
def test_category_table_view_requires_login(client):
    url = reverse("model_information:categorylist")  # Update to your actual URL name
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert "/login" in response.url.lower()  # Ensure it's going to the login page


@pytest.mark.django_db
def test_category_table_view_permission_denied(client, user):
    user = user()
    client.force_login(user)

    url = reverse("model_information:categorylist")  # Update to your actual URL name
    response = client.get(url)

    assert (
        response.status_code == 403
    )  # Depends on how CustomerAssetPermissionMixin handles it


@pytest.mark.django_db
def test_category_table_view_renders(client, user):
    user = user()
    client.force_login(user)

    permission = Permission.objects.get(codename="view_tblcategories")
    user.user_permissions.add(permission)
    url = reverse("model_information:categorylist")  # Update to your actual URL name

    response = client.get(url)

    # test html
    assert (
        response.status_code == 200
    )  # Depends on how CustomerAssetPermissionMixin handles it
    assertTemplateUsed(response, "filter_table.html")

    # test htmx
    response = client.get(url, HTTP_HX_REQUEST="true")
    assert response.status_code == 200


# test CategoryUpdateView
@pytest.mark.django_db
def test_category_update_view_requires_login(client, category):
    category = category()
    url = reverse(
        "model_information:update_category", kwargs={"pk": category.categoryid}
    )
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert "/login" in response.url.lower()  # Ensure it's going to the login page


@pytest.mark.django_db
def test_category_update_view_requires_permission(client, user, category):
    category = category()
    user = user()

    url = reverse(
        "model_information:update_category", kwargs={"pk": category.categoryid}
    )
    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_category_update_view_renders(client, user, category):
    category = category()
    user = user()
    permission = Permission.objects.get(codename="change_tblcategories")
    user.user_permissions.add(permission)

    url = reverse(
        "model_information:update_category", kwargs={"pk": category.categoryid}
    )
    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, "model_information/category_update.html")


@pytest.mark.django_db
def test_category_update_view_posts_successfully(client, user, category):
    category = category()
    user = user()
    permission = Permission.objects.get(codename="change_tblcategories")
    user.user_permissions.add(permission)

    url = reverse(
        "model_information:update_category", kwargs={"pk": category.categoryid}
    )
    client.force_login(user)

    # test html post
    form = {"categoryname": "testcategory"}
    response = client.post(url, data=form)

    assert response.status_code == 302
    category.refresh_from_db()
    assert category.categoryname == "testcategory"


# test CategoryCreateView


@pytest.mark.django_db
def test_category_create_view_requires_login(client):
    url = reverse("model_information:create_category")  # Update to your actual URL name
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert "/login" in response.url.lower()  # Ensure it's going to the login page


@pytest.mark.django_db
def test_category_create_view_requires_permission(client, user):
    user = user()

    url = reverse("model_information:create_category")

    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_category_create_view_renders(client, user):
    user = user()
    permission = Permission.objects.get(codename="add_tblcategories")
    user.user_permissions.add(permission)

    url = reverse("model_information:create_category")
    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, "model_information/category_create.html")


@pytest.mark.django_db
def test_category_create_view_posts_successfully(client, user, category):
    user = user()
    permission = Permission.objects.get(codename="add_tblcategories")
    user.user_permissions.add(permission)

    url = reverse("model_information:create_category")
    client.force_login(user)

    # test html post
    form = {"categoryname": "testcategory"}
    response = client.post(url, data=form)

    assert response.status_code == 302
    category = Tblcategories.objects.last()
    assert category.categoryname == "testcategory"


@pytest.mark.django_db
def test_category_create_view_requires_posts_unsuccessfully(client, user):
    user = user()

    permission = Permission.objects.get(codename="add_tblcategories")
    user.user_permissions.add(permission)
    url = reverse("model_information:create_category")
    client.force_login(user)

    # test html post
    form = {}
    response = client.post(url, data=form)

    assert response.status_code == 200
    assert response.context["form"].errors


# test CategoryDeleteView


@pytest.mark.django_db
def test_category_delete_view_requires_login(client, category):
    category = category()
    url = reverse(
        "model_information:delete_category", kwargs={"pk": category.categoryid}
    )
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert "/login" in response.url.lower()  # Ensure it's going to the login page


@pytest.mark.django_db
def test_category_delete_view_requires_permission(client, user, category):
    category = category()
    url = reverse(
        "model_information:delete_category", kwargs={"pk": category.categoryid}
    )

    user = user()

    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 403  # Redirect to login


@pytest.mark.django_db
def test_category_delete_view_renders(client, user, category):
    category = category()
    url = reverse(
        "model_information:delete_category", kwargs={"pk": category.categoryid}
    )

    user = user()

    permission = Permission.objects.get(codename="delete_tblcategories")
    user.user_permissions.add(permission)

    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, "model_information/category_delete.html")


@pytest.mark.django_db
def test_category_delete_view_posts_unsuccessfully(client, user, model):
    model = model()
    category = model.categoryid
    categoryid = category.categoryid
    url = reverse("model_information:delete_category", kwargs={"pk": categoryid})

    user = user()
    permission = Permission.objects.get(codename="delete_tblcategories")
    user.user_permissions.add(permission)
    client.force_login(user)
    response = client.post(url)
    assert response.context["form"].errors


@pytest.mark.django_db
def test_category_delete_view_posts_successfully(client, user, category):
    category = CategoryFactory(categoryname="testcategory")
    categoryid = category.categoryid
    url = reverse("model_information:delete_category", kwargs={"pk": categoryid})

    user = user()
    permission = Permission.objects.get(codename="delete_tblcategories")
    user.user_permissions.add(permission)

    client.force_login(user)

    response = client.post(url)
    assert response.status_code == 302
    assert response.url == reverse("model_information:categorylist")
    assert not Tblcategories.objects.filter(categoryid=categoryid).exists()


# -----------------------
# test Checklists views
# -----------------------

# test CheckslistTableView


@pytest.mark.django_db
def test_checklist_table_view_requires_login(client):
    url = reverse("model_information:checklist")  # Update to your actual URL name
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert "/login" in response.url.lower()  # Ensure it's going to the login page


@pytest.mark.django_db
def test_checklist_table_view_permission_denied(client, user):
    user = user()
    client.force_login(user)

    url = reverse("model_information:checklist")  # Update to your actual URL name
    response = client.get(url)

    assert (
        response.status_code == 403
    )  # Depends on how CustomerAssetPermissionMixin handles it


@pytest.mark.django_db
def test_checklist_table_view_renders(client, user):
    user = user()
    client.force_login(user)

    permission = Permission.objects.get(codename="view_tblcheckslists")
    user.user_permissions.add(permission)

    url = reverse("model_information:checklist")  # Update to your actual URL name

    response = client.get(url)

    # test html
    assert (
        response.status_code == 200
    )  # Depends on how CustomerAssetPermissionMixin handles it
    assertTemplateUsed(response, "model_information/partials/checklist.html")


@pytest.mark.django_db
def test_checklist_table_view_renders_with_model(client, user, check):
    check = check()
    user = user()
    client.force_login(user)
    permission = Permission.objects.get(codename="view_tblcheckslists")
    user.user_permissions.add(permission)

    base_url = reverse("model_information:checklist")  # Update to your actual URL name
    query_params = urlencode({"modelid": check.modelid.pk})
    url = f"{base_url}?{query_params}"

    response = client.get(url)

    # test html
    assert (
        response.status_code == 200
    )  # Depends on how CustomerAssetPermissionMixin handles it
    assertTemplateUsed(response, "model_information/partials/checklist.html")


# test CheckUpdateView
@pytest.mark.django_db
def test_check_update_view_requires_login(client, check):
    check = check()
    testid = check.testid
    url = reverse("model_information:update_check", kwargs={"pk": testid})
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert "/login" in response.url.lower()  # Ensure it's going to the login page


@pytest.mark.django_db
def test_check_update_view_requires_permission(client, user, check):
    check = check()
    testid = check.testid
    url = reverse("model_information:update_check", kwargs={"pk": testid})

    user = user()

    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 403  # Redirect to login


@pytest.mark.django_db
def test_check_update_view_renders(client, user, check):
    check = check()
    testid = check.testid
    url = reverse("model_information:update_check", kwargs={"pk": testid})

    user = user()

    permission = Permission.objects.get(codename="change_tblcheckslists")
    user.user_permissions.add(permission)

    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 200  # Redirect to login
    assertTemplateUsed(response, "model_information/partials/modal.html")
    assert response.context["title"] == "Update Check"
    assert response.context["view_type"] == "update"


@pytest.mark.django_db
def test_check_update_view_posts_successfully(client, user, check):
    check = check()
    testid = check.testid
    url = reverse("model_information:update_check", kwargs={"pk": testid})

    user = user()
    permission = Permission.objects.get(codename="change_tblcheckslists")
    user.user_permissions.add(permission)

    client.force_login(user)

    # test html post
    form = {
        "testname": "test_test",
        "test_description": "testdescripton",
        "modelid": Tblmodel.objects.last().modelid,
    }
    response = client.post(url, data=form)
    assert response.status_code == 302
    check.refresh_from_db()
    assert "test_test" in check.testname
    assert response.url == reverse("model_information:checklist")

    # test htmx post
    form = {
        "testname": "test_test2",
        "test_description": "testdescripton",
        "modelid": Tblmodel.objects.last().modelid,
    }
    response = client.post(url, data=form, HTTP_HX_REQUEST="true")

    assert response.status_code == 204
    check.refresh_from_db()
    assert "test_test2" in check.testname


# test CheckDeleteView


@pytest.mark.django_db
def test_check_delete_view_requires_login(client, check):
    check = check()
    checkid = check.testid
    url = reverse("model_information:delete_check", kwargs={"pk": checkid})
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert "/login" in response.url.lower()  # Ensure it's going to the login page


@pytest.mark.django_db
def test_check_delete_view_requires_permission(client, user, check):
    check = check()
    checkid = check.testid
    url = reverse("model_information:delete_check", kwargs={"pk": checkid})

    user = user()
    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 403  # Redirect to login


@pytest.mark.django_db
def test_check_delete_view_renders(client, user, check):
    check = check()
    checkid = check.testid
    url = reverse("model_information:delete_check", kwargs={"pk": checkid})
    user = user()

    permission = Permission.objects.get(codename="delete_tblcheckslists")
    user.user_permissions.add(permission)

    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, "model_information/partials/modal.html")
    assert response.context["title"] == "Delete Test"
    assert response.context["view_type"] == "delete"


@pytest.mark.django_db
def test_check_delete_view_posts_unsuccessfully(client, user):
    test = TestsCarriedOutFactory()
    checkid = test.checkid.pk
    url = reverse("model_information:delete_check", kwargs={"pk": checkid})

    user = user()
    permission = Permission.objects.get(codename="delete_tblcheckslists")
    user.user_permissions.add(permission)

    client.force_login(user)

    response = client.post(url)
    assert (
        "An error occurred while deleting the test" in response.context["error_message"]
    )


@pytest.mark.django_db
def test_check_delete_view_posts_successfully(client, user, check):
    check = check()
    url = reverse("model_information:delete_check", kwargs={"pk": check.pk})

    user = user()
    permission = Permission.objects.get(codename="delete_tblcheckslists")
    user.user_permissions.add(permission)

    client.force_login(user)
    response = client.post(url)
    assert response.status_code == 302
    assert response.url == reverse("model_information:checklist")
    assert not Tblcheckslists.objects.filter(testid=check.pk).exists()


@pytest.mark.django_db
def test_check_delete_view_posts_successfully_htmx(client, user, check):
    check = check()
    url = reverse("model_information:delete_check", kwargs={"pk": check.pk})

    user = user()
    permission = Permission.objects.get(codename="delete_tblcheckslists")
    user.user_permissions.add(permission)

    client.force_login(user)

    response = client.post(url, HTTP_HX_REQUEST="true")
    assert response.status_code == 204
    assert not Tblcheckslists.objects.filter(testid=check.pk).exists()


# test CheckCreateView


@pytest.mark.django_db
def test_check_create_view_requires_login(client):
    url = reverse("model_information:create_check")  # Update to your actual URL name
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert "/login" in response.url.lower()  # Ensure it's going to the login page


@pytest.mark.django_db
def test_check_create_view_requires_permission(client, user):
    user = user()
    url = reverse("model_information:create_check")

    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_check_create_view_renders(client, user):
    user = user()
    permission = Permission.objects.get(codename="add_tblcheckslists")
    user.user_permissions.add(permission)

    url = reverse("model_information:create_check")
    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, "model_information/partials/modal.html")
    assert response.context["title"] == "Create New Test"
    assert response.context["view_type"] == "create"


@pytest.mark.django_db
def test_check_create_view_requires_posts_successfully(client, user, model):
    user = user()
    permission = Permission.objects.get(codename="add_tblcheckslists")
    user.user_permissions.add(permission)

    url = reverse("model_information:create_check")
    client.force_login(user)

    # test html post
    form = {
        "testname": "test_test",
        "test_description": "testdescripton",
        "modelid": model().pk,
    }
    response = client.post(url, data=form)

    created_test = Tblcheckslists.objects.last()
    assert response.status_code == 302
    assert "test_test" in created_test.testname
    assert response.url == reverse("model_information:checklist")

    # test htmx post
    form = {
        "testname": "test_test2",
        "test_description": "testdescripton",
        "modelid": Tblmodel.objects.last().modelid,
    }
    response = client.post(url, data=form, HTTP_HX_REQUEST="true")

    created_test = Tblcheckslists.objects.last()
    assert response.status_code == 204
    assert "test_test2" in created_test.testname


@pytest.mark.django_db
def test_exitint_model_list_view_requires_login(client):
    url = reverse(
        "model_information:existing_modellist"
    )  # Update to your actual URL name
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert "/login" in response.url.lower()  # Ensure it's going to the login page


@pytest.mark.django_db
def test_exitint_model_list_view_requires_permission(client, user):
    user = user()
    client.force_login(user)

    url = reverse("model_information:existing_modellist")
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_exitint_model_list_view_renders(client, user, mocker):
    user = user()
    client.force_login(user)
    mocker.patch(
        "django.contrib.auth.mixins.PermissionRequiredMixin.has_permission",
        return_value=True,
    )

    url = reverse("model_information:existing_modellist")
    query_params = urlencode({"modelname": "sam 12"})
    response = client.get(f"{url}?{query_params}")

    # test html
    assert response.status_code == 200
    assertTemplateUsed(response, "model_information/partials/existing_model_list.html")


@pytest.mark.django_db
def test_exitint_model_list_view_renders_missing_model(client, user, mocker):
    user = user()
    client.force_login(user)
    mocker.patch(
        "django.contrib.auth.mixins.PermissionRequiredMixin.has_permission",
        return_value=True,
    )

    url = reverse("model_information:existing_modellist")
    query_params = urlencode({})
    response = client.get(f"{url}?{query_params}")

    # test html
    assert response.status_code == 200
    assert not response.context['models']


@pytest.mark.django_db
def test_software_filter_view_permission_denied(client, user_setup):
    user = user_setup
    client.force_login(user)
    url = reverse("model_information:softwares")
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_software_filter_view_renders(client, user_setup, jobs):
    jobs = jobs()

    user = user_setup
    user.customerid = None
    permission = Permission.objects.get(codename="view_software")
    user.user_permissions.add(permission)
    user.save()

    client.force_login(user)

    url = reverse("model_information:softwares")
    response = client.get(url)

    assert response.status_code == 200
    assertTemplateUsed(response, "filter_table.html")

    # test htmx request
    response = client.get(url, HTTP_HX_REQUEST="true")
    table = response.context["table"]
    assert table.data.data.count() == 0


# test Software detail view
@pytest.mark.django_db
def test_software_detail_view_requires_login(client, software_factory):
    software = software_factory()
    url = reverse("model_information:software_detail", kwargs={"pk": software.pk})
    response = client.get(url)
    assert response.status_code == 302


@pytest.mark.django_db
def test_software_detail_view_permission_denied(client, user, software_factory):
    user = user()
    client.force_login(user)
    software = software_factory()
    url = reverse("model_information:software_detail", kwargs={"pk": software.pk})
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_software_detail_view_renders(client, user, software_factory):

    user = user()
    user.customerid = None
    permission = Permission.objects.get(codename="view_software")
    user.user_permissions.add(permission)
    user.save()

    client.force_login(user)

    software = software_factory()
    url = reverse("model_information:software_detail", kwargs={"pk": software.pk})

    response = client.get(url)

    assert response.status_code == 200
    assertTemplateUsed(response, "model_information/software_detail.html")


# test Software detail view
@pytest.mark.django_db
def test_software_create_view_requires_login(client):
    url = reverse("model_information:software_create")
    response = client.get(url)
    assert response.status_code == 302


@pytest.mark.django_db
def test_software_create_view_permission_denied(client, user):
    user = user()
    client.force_login(user)
    url = reverse("model_information:software_create")
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_software_create_view_renders(client, user):

    user = user()
    user.customerid = None
    permission = Permission.objects.get(codename="add_software")
    user.user_permissions.add(permission)
    user.save()

    client.force_login(user)

    url = reverse("model_information:software_create")

    response = client.get(url)

    assert response.status_code == 200
    assertTemplateUsed(response, "model_information/software_create.html")


@pytest.mark.django_db
def test_software_create_view_posts(client, user, brand, software_type_factory):

    user = user()
    user.customerid = None
    permission = Permission.objects.get(codename="add_software")
    user.user_permissions.add(permission)
    user.save()

    client.force_login(user)

    url = reverse("model_information:software_create")

    software_type = software_type_factory()
    data = {
        "brand": brand().pk,
        "name": "Test Software",
        "version": "1.0.0",
        "version_number": 1,
        "software_type": software_type.pk,
    }
    response = client.post(url, data)
    assert response.status_code == 302
    assert Software.objects.last().name == "Test Software"


# test Software update view
@pytest.mark.django_db
def test_software_update_view_requires_login(client, software_factory):
    software = software_factory()
    url = reverse("model_information:software_update", kwargs={"pk": software.pk})
    response = client.get(url)
    assert response.status_code == 302


@pytest.mark.django_db
def test_software_update_view_permission_denied(client, user, software_factory):
    user = user()
    client.force_login(user)
    software = software_factory()
    url = reverse("model_information:software_update", kwargs={"pk": software.pk})
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_software_update_view_renders(client, user, software_factory):

    user = user()
    user.customerid = None
    permission = Permission.objects.get(codename="change_software")
    user.user_permissions.add(permission)
    user.save()

    client.force_login(user)

    software = software_factory()
    url = reverse("model_information:software_update", kwargs={"pk": software.pk})

    response = client.get(url)

    assert response.status_code == 200
    assertTemplateUsed(response, "model_information/software_update.html")


@pytest.mark.django_db
def test_software_update_view_posts(client, user, software_factory):

    user = user()
    user.customerid = None
    permission = Permission.objects.get(codename="change_software")
    user.user_permissions.add(permission)
    user.save()

    client.force_login(user)

    software = software_factory()
    url = reverse("model_information:software_update", kwargs={"pk": software.pk})

    data = {
        "brand": software.brand.pk,
        "name": "Test Software",
        "version": "1.0.0",
        "version_number": 3,
        "software_type": software.software_type.pk,
    }
    response = client.post(url, data)

    assert response.status_code == 302
    assert Software.objects.get(pk=software.pk).name == "Test Software"


# test Software create new version view
@pytest.mark.django_db
def test_add_software_version_view_requires_login(client, software_factory):
    software = software_factory()
    url = reverse("model_information:software_add_version", kwargs={"pk": software.pk})
    response = client.get(url)
    assert response.status_code == 302


@pytest.mark.django_db
def test_add_software_version_view_permission_denied(client, user, software_factory):
    user = user()
    client.force_login(user)
    software = software_factory()
    url = reverse("model_information:software_add_version", kwargs={"pk": software.pk})
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_add_software_version_view_renders(client, user, software_factory):

    user = user()
    user.customerid = None
    permission = Permission.objects.get(codename="add_software")
    user.user_permissions.add(permission)
    user.save()

    client.force_login(user)

    software = software_factory()
    url = reverse("model_information:software_add_version", kwargs={"pk": software.pk})

    response = client.get(url)

    assert response.status_code == 200
    assertTemplateUsed(response, "model_information/software_add_version.html")


@pytest.mark.django_db
def test_add_software_version_view_posts(client, user, software_factory):

    user = user()
    user.customerid = None
    permission = Permission.objects.get(codename="add_software")
    user.user_permissions.add(permission)
    user.save()

    client.force_login(user)

    software = software_factory()

    url = reverse("model_information:software_add_version", kwargs={"pk": software.pk})

    data = {"new_version": "new_test_version"}
    response = client.post(url, data)

    assert response.status_code == 302
    latest = (
        Software.objects.filter(name=software.name, brand=software.brand)
        .exclude(pk=software.pk)
        .first()
    )
    assert latest.version_number == int(software.version_number) + 1
    assert latest.version == "new_test_version"


# test Software delete view
@pytest.mark.django_db
def test_software_delete_view_requires_login(client, software_factory):
    software = software_factory()
    url = reverse("model_information:software_delete", kwargs={"pk": software.pk})
    response = client.get(url)
    assert response.status_code == 302


@pytest.mark.django_db
def test_software_delete_view_permission_denied(client, user, software_factory):
    user = user()
    client.force_login(user)
    software = software_factory()
    url = reverse("model_information:software_delete", kwargs={"pk": software.pk})
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_software_delete_view_renders(client, user, software_factory):

    user = user()
    user.customerid = None
    permission = Permission.objects.get(codename="delete_software")
    user.user_permissions.add(permission)
    user.save()

    client.force_login(user)

    software = software_factory()
    url = reverse("model_information:software_delete", kwargs={"pk": software.pk})

    response = client.get(url)

    assert response.status_code == 200
    assertTemplateUsed(response, "model_information/software_delete.html")


@pytest.mark.django_db
def test_add_software_delete_view_posts(client, user, software_factory):

    user = user()
    user.customerid = None
    permission = Permission.objects.get(codename="delete_software")
    user.user_permissions.add(permission)
    user.save()

    client.force_login(user)

    software = software_factory()

    url = reverse("model_information:software_delete", kwargs={"pk": software.pk})

    data = {}
    response = client.post(url, data)

    assert response.status_code == 302
    assert not Software.objects.filter(pk=software.pk).exists()


# test Software model create view
@pytest.mark.django_db
def test_software_model_create_view_requires_login(client):
    url = reverse("model_information:software_model_create")
    response = client.get(url)
    assert response.status_code == 302


@pytest.mark.django_db
def test_software_model_create_view_permission_denied(client, user):
    user = user()
    client.force_login(user)
    url = reverse("model_information:software_model_create")
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_software_model_create_view_renders(client, user):

    user = user()
    user.customerid = None
    permission = Permission.objects.get(codename="add_softwaremodel")
    user.user_permissions.add(permission)
    user.save()

    client.force_login(user)

    url = reverse("model_information:software_model_create")

    response = client.get(url)

    assert response.status_code == 200
    assertTemplateUsed(response, "model_information/software_model_create.html")


@pytest.mark.django_db
def test_add_software_model_create_view_posts(client, user, software_factory, model):

    user = user()
    user.customerid = None
    permission = Permission.objects.get(codename="add_softwaremodel")
    user.user_permissions.add(permission)
    user.save()

    client.force_login(user)

    software = software_factory()
    model = model()

    url = reverse("model_information:software_model_create")

    data = {"software": software.pk, "model": model.pk}
    response = client.post(url, data)

    assert response.status_code == 302
    assert SoftwareModel.objects.last().software == software
    assert SoftwareModel.objects.last().model == model


# test Software model delete view
@pytest.mark.django_db
def test_software_model_delete_view_requires_login(client, software_model_factory):
    sm = software_model_factory()
    url = reverse("model_information:software_model_delete", kwargs={"pk": sm.pk})
    response = client.get(url)
    assert response.status_code == 302


@pytest.mark.django_db
def test_software_model_delete_view_permission_denied(
    client, user, software_model_factory
):
    user = user()
    client.force_login(user)
    sm = software_model_factory()
    url = reverse("model_information:software_model_delete", kwargs={"pk": sm.pk})
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_software_model_delete_view_renders(client, user, software_model_factory):

    user = user()
    user.customerid = None
    permission = Permission.objects.get(codename="delete_softwaremodel")
    user.user_permissions.add(permission)
    user.save()

    client.force_login(user)

    sm = software_model_factory()
    url = reverse("model_information:software_model_delete", kwargs={"pk": sm.pk})

    response = client.get(url)

    assert response.status_code == 200
    assertTemplateUsed(response, "model_information/software_model_delete.html")


@pytest.mark.django_db
def test_add_software_model_delete_view_posts(client, user, software_model_factory):

    user = user()
    user.customerid = None
    permission = Permission.objects.get(codename="delete_softwaremodel")
    user.user_permissions.add(permission)
    user.save()

    client.force_login(user)

    sm = software_model_factory()
    url = reverse("model_information:software_model_delete", kwargs={"pk": sm.pk})

    data = {}
    response = client.post(url, data)

    assert response.status_code == 302
    assert not SoftwareModel.objects.filter(pk=sm.pk).exists()


# test equipment configuration filter view
@pytest.mark.django_db
def test_equipment_configuration_filter_view_requires_login(client):
    url = reverse("model_information:configurations")
    response = client.get(url)
    assert response.status_code == 302


@pytest.mark.django_db
def test_equipment_configuration_filter_view_permission_denied(client, user):
    user = user()
    client.force_login(user)
    url = reverse("model_information:configurations")
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_equipment_configuration_filter_view_renders(client, user):

    user = user()
    user.customerid = None
    permission = Permission.objects.get(codename="view_equipmentconfiguration")
    user.user_permissions.add(permission)
    user.save()

    client.force_login(user)

    url = reverse("model_information:configurations")

    response = client.get(url)

    assert response.status_code == 200
    assertTemplateUsed(response, "filter_table.html")


# test equipment configuration filter view
@pytest.mark.django_db
def test_equipment_configuration_detail_view_requires_login(
    client, equipment_configuration_factory
):
    config = equipment_configuration_factory()
    url = reverse("model_information:configuration_detail", kwargs={"pk": config.pk})
    response = client.get(url)
    assert response.status_code == 302


@pytest.mark.django_db
def test_equipment_configuration_detail_view_permission_denied(
    client, user, equipment_configuration_factory
):
    user = user()
    client.force_login(user)
    config = equipment_configuration_factory()
    url = reverse("model_information:configuration_detail", kwargs={"pk": config.pk})
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_equipment_configuration_detail_view_renders(
    client, user, equipment_configuration_factory
):

    user = user()
    user.customerid = None
    permission = Permission.objects.get(codename="view_equipmentconfiguration")
    user.user_permissions.add(permission)
    user.save()

    client.force_login(user)

    config = equipment_configuration_factory()
    url = reverse("model_information:configuration_detail", kwargs={"pk": config.pk})

    response = client.get(url)

    assert response.status_code == 200
    assertTemplateUsed(response, "model_information/configuration_detail.html")


# test equipment configuration create view
@pytest.mark.django_db
def test_equipment_configuration_create_view_requires_login(client):
    url = reverse("model_information:configuration_create")
    response = client.get(url)
    assert response.status_code == 302


@pytest.mark.django_db
def test_equipment_configuration_create_view_permission_denied(client, user):
    user = user()
    client.force_login(user)
    url = reverse("model_information:configuration_create")
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_equipment_configuration_create_view_renders(client, user):

    user = user()
    user.customerid = None
    permission = Permission.objects.get(codename="add_equipmentconfiguration")
    user.user_permissions.add(permission)
    user.save()

    client.force_login(user)

    url = reverse("model_information:configuration_create")

    response = client.get(url)

    assert response.status_code == 200
    assertTemplateUsed(response, "model_information/configuration_create.html")


@pytest.mark.django_db
def test_equipment_configuration_create_view_posts(
    client, user, brand, equipment_configuration_status_factory
):

    user = user()
    user.customerid = None
    permission = Permission.objects.get(codename="add_equipmentconfiguration")
    user.user_permissions.add(permission)
    user.save()

    client.force_login(user)

    url = reverse("model_information:configuration_create")

    config_name = "test_config"
    data = {
        "name": config_name,
        "configuration_status": equipment_configuration_status_factory().pk,
        "brand": brand().pk,
        "version": 1,
    }

    response = client.post(url, data)
    assert response.status_code == 302

    assert EquipmentConfiguration.objects.last().name == config_name


# test add new config version view
@pytest.mark.django_db
def test_add_new_config_version_view_requires_login(
    client, equipment_configuration_factory
):
    config = equipment_configuration_factory()
    url = reverse(
        "model_information:configuration_add_version", kwargs={"pk": config.pk}
    )
    response = client.get(url)
    assert response.status_code == 302


@pytest.mark.django_db
def test_add_new_config_version_view_permission_denied(
    client, user, equipment_configuration_factory
):
    user = user()
    client.force_login(user)
    config = equipment_configuration_factory()
    url = reverse(
        "model_information:configuration_add_version", kwargs={"pk": config.pk}
    )
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_add_new_config_version_view_renders(
    client, user, equipment_configuration_factory
):

    user = user()
    user.customerid = None
    permission = Permission.objects.get(codename="add_equipmentconfiguration")
    user.user_permissions.add(permission)
    user.save()

    client.force_login(user)

    config = equipment_configuration_factory()
    url = reverse(
        "model_information:configuration_add_version", kwargs={"pk": config.pk}
    )

    response = client.get(url)

    assert response.status_code == 200
    assertTemplateUsed(response, "model_information/configuration_add_version.html")


@pytest.mark.django_db
def test_add_new_config_version_view_posts(
    client, user, equipment_configuration_factory
):

    user = user()
    user.customerid = None
    permission = Permission.objects.get(codename="add_equipmentconfiguration")
    user.user_permissions.add(permission)
    user.save()

    client.force_login(user)

    config = equipment_configuration_factory()
    url = reverse(
        "model_information:configuration_add_version", kwargs={"pk": config.pk}
    )

    data = {}

    response = client.post(url, data)

    assert response.status_code == 302
    assert EquipmentConfiguration.objects.last().name == config.name
    assert EquipmentConfiguration.objects.last().version == config.version + 1


# test configuration_update view
@pytest.mark.django_db
def test_configuration_update_view_requires_login(
    client, equipment_configuration_factory
):
    config = equipment_configuration_factory()
    url = reverse("model_information:configuration_update", kwargs={"pk": config.pk})
    response = client.get(url)
    assert response.status_code == 302


@pytest.mark.django_db
def test_configuration_update_view_permission_denied(
    client, user, equipment_configuration_factory
):
    user = user()
    client.force_login(user)
    config = equipment_configuration_factory()
    url = reverse("model_information:configuration_update", kwargs={"pk": config.pk})
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_configuration_update_view_renders(
    client, user, equipment_configuration_factory
):

    user = user()
    user.customerid = None
    permission = Permission.objects.get(codename="change_equipmentconfiguration")
    user.user_permissions.add(permission)
    user.save()

    client.force_login(user)

    config = equipment_configuration_factory()
    url = reverse("model_information:configuration_update", kwargs={"pk": config.pk})

    response = client.get(url)

    assert response.status_code == 200
    assertTemplateUsed(response, "model_information/configuration_update.html")


@pytest.mark.django_db
def test_configuration_update_view_posts(client, user, equipment_configuration_factory):

    user = user()
    user.customerid = None
    permission = Permission.objects.get(codename="change_equipmentconfiguration")
    user.user_permissions.add(permission)
    user.save()

    client.force_login(user)

    config = equipment_configuration_factory()
    url = reverse("model_information:configuration_update", kwargs={"pk": config.pk})
    new_config_name = "new_config_testx"
    data = {
        "name": new_config_name,
        "configuration_status": config.configuration_status.pk,
        "brand": config.brand.pk,
        "version": 1,
    }
    response = client.post(url, data)

    assert response.status_code == 302
    assert EquipmentConfiguration.objects.get(pk=config.pk).name == new_config_name


# test configuration_delete view
@pytest.mark.django_db
def test_configuration_delete_view_requires_login(
    client, equipment_configuration_factory
):
    config = equipment_configuration_factory()
    url = reverse("model_information:configuration_delete", kwargs={"pk": config.pk})
    response = client.get(url)
    assert response.status_code == 302


@pytest.mark.django_db
def test_configuration_delete_view_permission_denied(
    client, user, equipment_configuration_factory
):
    user = user()
    client.force_login(user)
    config = equipment_configuration_factory()
    url = reverse("model_information:configuration_delete", kwargs={"pk": config.pk})
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_configuration_delete_view_renders(
    client, user, equipment_configuration_factory
):

    user = user()
    user.customerid = None
    permission = Permission.objects.get(codename="delete_equipmentconfiguration")
    user.user_permissions.add(permission)
    user.save()

    client.force_login(user)

    config = equipment_configuration_factory()
    url = reverse("model_information:configuration_delete", kwargs={"pk": config.pk})

    response = client.get(url)

    assert response.status_code == 200
    assertTemplateUsed(response, "model_information/configuration_delete.html")


@pytest.mark.django_db
def test_configuration_delete_view_posts(client, user, equipment_configuration_factory):

    user = user()
    user.customerid = None
    permission = Permission.objects.get(codename="delete_equipmentconfiguration")
    user.user_permissions.add(permission)
    user.save()

    client.force_login(user)

    config = equipment_configuration_factory()
    url = reverse("model_information:configuration_delete", kwargs={"pk": config.pk})
    data = {}
    response = client.post(url, data)

    assert response.status_code == 302
    assert not EquipmentConfiguration.objects.filter(pk=config.pk).exists()


# test configuration model create view
@pytest.mark.django_db
def test_configuration_model_create_view_requires_login(client):
    url = reverse("model_information:configuration_model_create")
    response = client.get(url)
    assert response.status_code == 302


@pytest.mark.django_db
def test_configuration_model_create_view_permission_denied(client, user):
    user = user()
    client.force_login(user)
    url = reverse("model_information:configuration_model_create")
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_configuration_model_create_view_renders(client, user):

    user = user()
    user.customerid = None
    permission = Permission.objects.get(codename="add_equipmentconfigurationmodel")
    user.user_permissions.add(permission)
    user.save()

    client.force_login(user)

    url = reverse("model_information:configuration_model_create")

    response = client.get(url)

    assert response.status_code == 200
    assertTemplateUsed(response, "model_information/configuration_model_create.html")


@pytest.mark.django_db
def test_configuration_model_create_view_posts(
    client, user, model, equipment_configuration_factory
):

    user = user()
    user.customerid = None
    permission = Permission.objects.get(codename="add_equipmentconfigurationmodel")
    user.user_permissions.add(permission)
    user.save()

    client.force_login(user)

    config = equipment_configuration_factory()
    modelx = model()
    url = reverse("model_information:configuration_model_create")
    data = {"configuration": config.pk, "model": modelx.pk}
    response = client.post(url, data)

    assert response.status_code == 302
    assert not EquipmentConfigurationModel.objects.last().configuration == configuration
    assert not EquipmentConfigurationModel.objects.last().model == model


# test configuration model delete view
@pytest.mark.django_db
def test_configuration_model_delete_view_requires_login(
    client, equipment_configuration_model_factory
):
    sm = equipment_configuration_model_factory()
    url = reverse("model_information:configuration_model_delete", kwargs={"pk": sm.pk})
    response = client.get(url)
    assert response.status_code == 302


@pytest.mark.django_db
def test_configuration_model_delete_view_permission_denied(
    client, user, equipment_configuration_model_factory
):
    user = user()
    client.force_login(user)
    sm = equipment_configuration_model_factory()
    url = reverse("model_information:configuration_model_delete", kwargs={"pk": sm.pk})
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_configuration_model_delete_view_renders(
    client, user, equipment_configuration_model_factory
):

    user = user()
    user.customerid = None
    permission = Permission.objects.get(codename="delete_equipmentconfigurationmodel")
    user.user_permissions.add(permission)
    user.save()

    client.force_login(user)

    sm = equipment_configuration_model_factory()
    url = reverse("model_information:configuration_model_delete", kwargs={"pk": sm.pk})

    response = client.get(url)

    assert response.status_code == 200
    assertTemplateUsed(response, "model_information/configuration_model_delete.html")


@pytest.mark.django_db
def test_configuration_software_model_delete_view_posts(
    client, user, equipment_configuration_model_factory
):

    user = user()
    user.customerid = None
    permission = Permission.objects.get(codename="delete_equipmentconfigurationmodel")
    user.user_permissions.add(permission)
    user.save()

    client.force_login(user)

    sm = equipment_configuration_model_factory()
    url = reverse("model_information:configuration_model_delete", kwargs={"pk": sm.pk})

    data = {}
    response = client.post(url, data)

    assert response.status_code == 302
    assert not EquipmentConfigurationModel.objects.filter(pk=sm.pk).exists()


# test configuration scope create view
@pytest.mark.django_db
def test_configuration_scope_create_view_requires_login(client):
    url = reverse("model_information:configuration_scope_create")
    response = client.get(url)
    assert response.status_code == 302


@pytest.mark.django_db
def test_configuration_scope_create_view_permission_denied(client, user):
    user = user()
    client.force_login(user)
    url = reverse("model_information:configuration_scope_create")
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_configuration_scope_create_view_renders(client, user):

    user = user()
    user.customerid = None
    permission = Permission.objects.get(codename="add_equipmentconfigurationscope")
    user.user_permissions.add(permission)
    user.save()

    client.force_login(user)

    url = reverse("model_information:configuration_scope_create")

    response = client.get(url)

    assert response.status_code == 200
    assertTemplateUsed(response, "model_information/configuration_scope_create.html")


@pytest.mark.django_db
def test_configuration_scope_create_view_posts(
    client, user, site, equipment_configuration_factory
):

    user = user()
    user.customerid = None
    permission = Permission.objects.get(codename="add_equipmentconfigurationscope")
    user.user_permissions.add(permission)
    user.save()

    client.force_login(user)

    config = equipment_configuration_factory()
    site = site()
    url = reverse("model_information:configuration_scope_create")
    data = {"configuration": config.pk, "site": site.pk}
    response = client.post(url, data)

    assert response.status_code == 302
    assert EquipmentConfigurationScope.objects.last().site == site


# test configuration model delete view
@pytest.mark.django_db
def test_configuration_scope_delete_view_requires_login(
    client, equipment_configuration_scope_factory
):
    sm = equipment_configuration_scope_factory()
    url = reverse("model_information:configuration_model_delete", kwargs={"pk": sm.pk})
    response = client.get(url)
    assert response.status_code == 302


@pytest.mark.django_db
def test_configuration_scope_delete_view_permission_denied(
    client, user, equipment_configuration_scope_factory
):
    user = user()
    client.force_login(user)
    sm = equipment_configuration_scope_factory()
    url = reverse("model_information:configuration_model_delete", kwargs={"pk": sm.pk})
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_configuration_scope_delete_view_renders(
    client, user, equipment_configuration_scope_factory
):

    user = user()
    user.customerid = None
    permission = Permission.objects.get(codename="delete_equipmentconfigurationscope")
    user.user_permissions.add(permission)
    user.save()

    client.force_login(user)

    sm = equipment_configuration_scope_factory()
    url = reverse("model_information:configuration_scope_delete", kwargs={"pk": sm.pk})

    response = client.get(url)

    assert response.status_code == 200
    assertTemplateUsed(response, "model_information/configuration_scope_delete.html")


@pytest.mark.django_db
def test_configuration_scope_delete_view_posts(
    client, user, equipment_configuration_scope_factory
):

    user = user()
    user.customerid = None
    permission = Permission.objects.get(codename="delete_equipmentconfigurationscope")
    user.user_permissions.add(permission)
    user.save()

    client.force_login(user)

    sm = equipment_configuration_scope_factory()
    url = reverse("model_information:configuration_scope_delete", kwargs={"pk": sm.pk})

    data = {}
    response = client.post(url, data)

    assert response.status_code == 302
    assert not EquipmentConfigurationScope.objects.filter(pk=sm.pk).exists()


@pytest.mark.django_db
def test_model_copy_view_requires_login(client, model):
    model = model()
    url = reverse("model_information:copy_model", kwargs={"pk": model.modelid})
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert "/login" in response.url.lower()  # Ensure it's going to the login page


@pytest.mark.django_db
def test_model_copy_view_requires_permission(client, user, model):
    model = model()
    url = reverse("model_information:copy_model", kwargs={"pk": model.modelid})
    user = user()

    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 403  # Redirect to login


@pytest.mark.django_db
def test_model_copyp_view_renders(client, user, model):
    model = model()
    url = reverse("model_information:copy_model", kwargs={"pk": model.modelid})
    user = user()

    permission = Permission.objects.get(codename="add_tblmodel")
    user.user_permissions.add(permission)

    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, "model_information/model_copy.html")


@pytest.mark.django_db
def test_model_copy_view_posts_unsuccessfully(client, user, model, asset):
    asset = asset()
    model = asset.modelid
    url = reverse("model_information:copy_model", kwargs={"pk": model.modelid})
    user = user()
    permission = Permission.objects.get(codename="add_tblmodel")
    user.user_permissions.add(permission)

    client.force_login(user)

    response = client.post(url)
    assert response.context["form"].errors

@pytest.mark.django_db
def test_model_copy_view_posts_successfully_error(client, user, model):
    model = model()
    user = user()
    url = reverse("model_information:copy_model", kwargs={"pk": model.modelid})
    permission = Permission.objects.get(codename="add_tblmodel")
    user.user_permissions.add(permission)
    test_gtin = 'testgtin34349'
    data = {
        'model_id': model.pk,
        'gtin':''
    }

    client.force_login(user)

    assert not Tblmodel.objects.filter(gtin=test_gtin).exists()
    response = client.post(url, data=data)
    assert response.status_code == 200
    assert response.context['form'].errors


@pytest.mark.django_db
def test_model_copy_view_posts_successfully(client, user, model):
    model = model()
    user = user()
    url = reverse("model_information:copy_model", kwargs={"pk": model.modelid})
    permission = Permission.objects.get(codename="add_tblmodel")
    user.user_permissions.add(permission)
    test_gtin = 'testgtin34349'
    data = {
        'model_id': model.pk,
        'gtin': test_gtin 
    }

    client.force_login(user)

    assert not Tblmodel.objects.filter(gtin=test_gtin).exists()
    response = client.post(url, data=data)
    assert response.status_code == 302

    assert Tblmodel.objects.filter(gtin=test_gtin).exists()

