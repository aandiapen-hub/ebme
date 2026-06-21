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

from assets.tests.factories import ModelFactory, CategoryFactory
from jobs.tests.factories import ChecklistsFactory, TestsCarriedOutFactory
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
    assertTemplateUsed(response, "model_information/brandlist.html")

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
    assertTemplateUsed(response, "model_information/partials/modal.html")
    assert response.context["title"] == "Update Brand"


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
    assert response.url == reverse("model_information:brandlist")

    # test htmx post
    form = {"brandname": "brandtest2"}
    response = client.post(url, data=form, HTTP_HX_REQUEST="true")

    assert response.status_code == 204
    brand.refresh_from_db()
    assert brand.brandname == "brandtest2"


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
    assertTemplateUsed(response, "model_information/partials/delete_modal.html")
    assert response.context["title"] == "Delete Brand"
    assert response.context["view_type"] == "delete"


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

    assert (
        "An error occurred while deleting the brand"
        in response.context["error_message"]
    )

@pytest.mark.django_db
def test_brand_delete_view_requires_posts_successfully(client, user, brand):
    brand = brand()
    user = user()

    permission = Permission.objects.get(codename="delete_tblbrands")
    user.user_permissions.add(permission)

    url = reverse("model_information:delete_brand", kwargs={"pk": brand.pk})
    client.force_login(user)

    response = client.post(url)
    assert response.status_code == 204
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
    assertTemplateUsed(response, "model_information/modellist.html")

    # test htmx
    response = client.get(url, HTTP_HX_REQUEST="true")
    assert response.status_code == 200

    # test filter
    query_string = urlencode({"universal_search": ''})
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
    assertTemplateUsed(response, "model_information/partials/model_update.html")


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
    assertTemplateUsed(response, "model_information/partials/modal.html")
    assert response.context["title"] == "Delete Model"
    assert response.context["view_type"] == "delete"


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
    assert (
        "An error occurred while deleting the model"
        in response.context["error_message"]
    )


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


@pytest.mark.django_db
def test_model_delete_view_posts_successfully_htmx(client, user, model):
    model = ModelFactory(modelname="testmodel")
    modelid = model.modelid
    url = reverse("model_information:delete_model", kwargs={"pk": modelid})
    user = user()

    permission = Permission.objects.get(codename="delete_tblmodel")
    user.user_permissions.add(permission)

    client.force_login(user)
    response = client.post(url, HTTP_HX_REQUEST="true")
    assert response.status_code == 200
    assert not Tblmodel.objects.filter(modelid=modelid).exists()


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
    assertTemplateUsed(response, "model_information/categorylist.html")

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
    assertTemplateUsed(response, "model_information/partials/modal.html")
    assert response.context["title"] == "Update Category"


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
    assert response.url == reverse("model_information:categorylist")

    # test htmx
    form = {"categoryname": "testcategory2"}
    response = client.post(url, data=form, HTTP_HX_REQUEST="true")

    assert response.status_code == 204
    category.refresh_from_db()
    assert category.categoryname == "testcategory2"


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
    assertTemplateUsed(response, "model_information/partials/delete_modal.html")
    assert response.context["title"] == "Delete Category"
    assert response.context["view_type"] == "delete"


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
    assert (
        "An error occurred while deleting the category"
        in response.context["error_message"]
    )


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

#-----------------------
# test Checklists views
#-----------------------

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

