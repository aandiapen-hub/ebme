import pytest
from django.contrib.auth.models import Permission
from pytest_django.asserts import assertTemplateUsed
from django.urls import reverse
from urllib.parse import urlencode
from assets.models import (
    Tblassets,
    Tbljob,
)
from model_information.models import (
    EquipmentConfigurationLink,
    EquipmentSoftware,
)
from unittest.mock import patch


# test AssetCreateView
@pytest.mark.django_db
def test_asset_detail_view_requires_login(client, asset):
    asset = asset()
    url = reverse(
        "assets:view_asset", kwargs={"pk": asset.pk}
    )  # Update to your actual URL name
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert "/login" in response.url.lower()  # Ensure it's going to the login page


@pytest.mark.django_db
def test_asset_detail_view_permission_denied(client, user, asset):
    asset = asset()
    url = reverse(
        "assets:view_asset", kwargs={"pk": asset.pk}
    )  # Update to your actual URL name
    user = user()
    client.force_login(user)

    response = client.get(url)

    assert (
        response.status_code == 403
    )  # Depends on how CustomerAssetPermissionMixin handles it


@pytest.mark.django_db
def test_asset_detail_view_renders(client, user, asset, jobs):
    asset = asset()
    jobs = jobs(count=10, assetid=asset)
    url = reverse(
        "assets:view_asset", kwargs={"pk": asset.pk}
    )  # Update to your actual URL name
    user = user()
    user.is_staff = True
    permission = Permission.objects.get(codename="view_assetview")
    user.user_permissions.add(permission)
    user.save()
    client.force_login(user)

    response = client.get(url)

    assert response.status_code == 200
    assert response.context["open_jobs"].count() > 0


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
def test_asset_create_view_renders(
    client,
    user_setup,
    asset_status,
):
    # Create user and force login
    user = user_setup

    permission = Permission.objects.get(codename="add_tblassets")
    user.user_permissions.add(permission)

    client.force_login(user)

    # Set up required related objects
    asset_status = asset_status()
    # Prepare form data
    url = reverse("assets:create_asset")
    response = client.get(url)
    assert response.status_code == 200

@pytest.mark.django_db
def test_asset_create_view_renders_with_barcode(
    client,
    user_setup,
    asset_status,
):
    # Create user and force login
    user = user_setup

    permission = Permission.objects.get(codename="add_tblassets")
    user.user_permissions.add(permission)

    client.force_login(user)

    # Set up required related objects
    asset_status = asset_status()
    # Prepare form data
    base_url = reverse("assets:create_asset")
    query_params = urlencode({'barcode':'01008854034972331126021921S10009739'})
    url = f"{base_url}?{query_params}"
    response = client.get(url, HTTP_HX_REQUEST='true')

    form = response.context['form']
    assert form['serialnumber'].value() == 'S10009739'
    assert response.status_code == 200

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

@pytest.mark.django_db
def test_asset_create_view_success_post_create_accetance_job_error(
    client,
    user_setup,
    model,
    customer,
    asset_status,
    jobstatus,
    jobtype
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
        "create_acceptance_job": True,
    }

    new_status = jobstatus(jobstatusname='in progress')
    new_job_type = jobtype(jobtypename='acceptance')

    url = reverse("assets:create_asset")
    response = client.post(url, data=form_data)
    assert response.context['form'].errors

@pytest.mark.django_db
def test_asset_create_view_success_post_create_accetance_job(
    client,
    user_setup,
    model,
    customer,
    asset_status,
    technician,
    jobstatus,
    jobtype
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
        "create_acceptance_job": True,
        "technicianid": technician().pk
    }

    new_status = jobstatus(jobstatusname='in progress')
    new_job_type = jobtype(jobtypename='acceptance')

    url = reverse("assets:create_asset")
    response = client.post(url, data=form_data)
    created_asset = Tblassets.objects.last()
    assert Tbljob.objects.filter(assetid=created_asset.pk)


# test set equipment software view
@pytest.mark.django_db
def test_equipment_software_view_requires_login(client):
    url = reverse("assets:set_equipment_software")
    response = client.get(url)
    assert response.status_code == 302


@pytest.mark.django_db
def test_set_equipment_sofware_view_permission_denied(client, user):
    user = user()
    client.force_login(user)
    url = reverse("assets:set_equipment_software")
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_set_equipment_sofware_view_renders(client, user, asset):

    user = user()
    user.customerid = None
    permission = Permission.objects.get(codename="add_equipmentsoftware")
    user.user_permissions.add(permission)
    user.save()

    client.force_login(user)

    base_url = reverse("assets:set_equipment_software")
    query_params = urlencode({'equipmentid':asset().pk})
    url = f"{base_url}?{query_params}"

    response = client.get(url)

    assert response.status_code == 200
    assertTemplateUsed(response, "assets/set_equipment_software.html")


@pytest.mark.django_db
def test_set_equipment_sofware_view_posts(client, user, asset, software_model_factory):

    user = user()
    user.customerid = None
    permission = Permission.objects.get(codename="add_equipmentsoftware")
    user.user_permissions.add(permission)
    user.save()

    client.force_login(user)

    url = reverse("assets:set_equipment_software")
    software_model = software_model_factory()
    assetx = asset()
    data = {"equipment": assetx.pk, "software": software_model.software.pk}
    response = client.post(url, data)

    assert response.status_code == 302
    assert EquipmentSoftware.objects.last().software == software_model.software
    assert EquipmentSoftware.objects.last().equipment == assetx


# test delete equipment software view
@pytest.mark.django_db
def test_remove_equipment_software_view_requires_login(
    client, equipment_software_factory
):
    es = equipment_software_factory()
    url = reverse("assets:remove_equipment_software", kwargs={"pk": es.pk})
    response = client.get(url)
    assert response.status_code == 302


@pytest.mark.django_db
def test_remove_equipment_sofware_view_permission_denied(
    client, user, equipment_software_factory
):
    user = user()
    client.force_login(user)
    es = equipment_software_factory()
    url = reverse("assets:remove_equipment_software", kwargs={"pk": es.pk})
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_remove_equipment_sofware_view_renders(
    client, user, equipment_software_factory
):

    user = user()
    user.customerid = None
    permission = Permission.objects.get(codename="delete_equipmentsoftware")
    user.user_permissions.add(permission)
    user.save()

    client.force_login(user)

    es = equipment_software_factory()
    url = reverse("assets:remove_equipment_software", kwargs={"pk": es.pk})

    response = client.get(url)

    assert response.status_code == 200
    assertTemplateUsed(response, "assets/remove_equipment_software.html")


@pytest.mark.django_db
def test_remove_equipment_sofware_view_posts(
    client,
    user,
    equipment_software_factory,
):

    user = user()
    user.customerid = None
    permission = Permission.objects.get(codename="delete_equipmentsoftware")
    user.user_permissions.add(permission)
    user.save()

    client.force_login(user)

    es = equipment_software_factory()
    url = reverse("assets:remove_equipment_software", kwargs={"pk": es.pk})
    data = {}
    response = client.post(url, data)

    assert response.status_code == 302
    assert not EquipmentSoftware.objects.filter(pk=es.pk).exists()


# test set equipment config view
@pytest.mark.django_db
def test_set_equipment_configuration_view_requires_login(client):
    url = reverse("assets:set_equipment_configuration")
    response = client.get(url)
    assert response.status_code == 302


@pytest.mark.django_db
def test_set_equipment_configuration_view_permission_denied(client, user):
    user = user()
    client.force_login(user)
    url = reverse("assets:set_equipment_configuration")
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_set_equipment_configuration_view_renders(client, user, asset):

    user = user()
    user.customerid = None
    permission = Permission.objects.get(codename="add_equipmentconfigurationlink")
    user.user_permissions.add(permission)
    user.save()

    client.force_login(user)

    base_url = reverse("assets:set_equipment_configuration")
    query_params = urlencode({'equipmentid':asset().pk})
    url = f"{base_url}?{query_params}"
    response = client.get(url)

    assert response.status_code == 200
    assertTemplateUsed(response, "assets/set_equipment_configuration.html")


@pytest.mark.django_db
def test_set_equipment_configuration_view_renders_with_initial(
        client,
        user,
        asset,
        location_configuration_scope_factory,
        equipment_configuration_model_factory,
):

    user = user()
    user.customerid = None
    permission = Permission.objects.get(codename="add_equipmentconfigurationlink")
    user.user_permissions.add(permission)
    user.save()

    client.force_login(user)

    scope = location_configuration_scope_factory()
    config_link = equipment_configuration_model_factory(configuration=scope.configuration)

    asset = asset(locationid = scope.location, modelid = config_link.model )

    base_url = reverse("assets:set_equipment_configuration")
    query_params = urlencode({'equipmentid':asset.pk})
    url = f"{base_url}?{query_params}"
    response = client.get(url)

    assert response.status_code == 200
    assert response.context['form']['configuration'].value() == scope.configuration.pk


@pytest.mark.django_db
def test_set_equipment_configuration_view_posts(
    client,
    user,
    asset,
    equipment_configuration_model_factory,
):

    user = user()
    user.customerid = None
    permission = Permission.objects.get(codename="add_equipmentconfigurationlink")
    user.user_permissions.add(permission)
    user.save()

    client.force_login(user)

    url = reverse("assets:set_equipment_configuration")
    configuration_model = equipment_configuration_model_factory()
    assetx = asset()
    data = {
        "equipment": assetx.pk,
        "configuration": configuration_model.configuration.pk,
    }
    response = client.post(url, data)

    assert response.status_code == 302
    assert (
        EquipmentConfigurationLink.objects.last().configuration
        == configuration_model.configuration
    )
    assert EquipmentConfigurationLink.objects.last().equipment == assetx


# test delete equipment configuration view
@pytest.mark.django_db
def test_remove_equipment_configuration_link_view_requires_login(
    client, equipment_configuration_link
):
    es = equipment_configuration_link()
    url = reverse("assets:remove_equipment_configuration", kwargs={"pk": es.pk})
    response = client.get(url)
    assert response.status_code == 302


@pytest.mark.django_db
def test_remove_equipment_configuration_link_view_permission_denied(
    client, user, equipment_configuration_link
):
    user = user()
    client.force_login(user)
    es = equipment_configuration_link()
    url = reverse("assets:remove_equipment_configuration", kwargs={"pk": es.pk})
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_remove_equipment_configuration_link_view_renders(
    client, user, equipment_configuration_link
):

    user = user()
    user.customerid = None
    permission = Permission.objects.get(codename="delete_equipmentconfigurationlink")
    user.user_permissions.add(permission)
    user.save()

    client.force_login(user)

    es = equipment_configuration_link()
    url = reverse("assets:remove_equipment_configuration", kwargs={"pk": es.pk})

    response = client.get(url)

    assert response.status_code == 200
    assertTemplateUsed(response, "assets/remove_equipment_configuration.html")


@pytest.mark.django_db
def test_remove_equipment_configuration_link_view_posts(
    client,
    user,
    equipment_configuration_link,
):

    user = user()
    user.customerid = None
    permission = Permission.objects.get(codename="delete_equipmentconfigurationlink")
    user.user_permissions.add(permission)
    user.save()

    client.force_login(user)

    es = equipment_configuration_link()
    url = reverse("assets:remove_equipment_configuration", kwargs={"pk": es.pk})
    data = {}
    response = client.post(url, data)

    assert response.status_code == 302
    assert not EquipmentConfigurationLink.objects.filter(pk=es.pk).exists()


# test AssetUpdateView
@pytest.mark.django_db
def test_asset_update_view_requires_login(client, asset):
    asset = asset()
    url = reverse("assets:update_asset", kwargs={"pk": asset.assetid})
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert "/login" in response.url.lower()  # Ensure it's going to the login page


@pytest.mark.django_db
def test_asset_update_view_permission_denied(client, asset, user_setup):
    asset = asset()
    user = user_setup
    client.force_login(user)

    # test denied permission
    url = reverse("assets:update_asset", kwargs={"pk": asset.assetid})
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_asset_update_view_renders(client, user_setup, asset):
    asset = asset()
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
def test_asset_update_view_invali(client, user_setup, asset):
    asset = asset()
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
            "modelid": '',
            "asset_status_id": asset.asset_status_id.pk,
        },
    )

    assert response.context['form'].errors

@pytest.mark.django_db
def test_asset_update_view_valid_data_updates_object(client, user_setup, asset):
    asset = asset()
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
            "asset_status_id": asset.asset_status_id.pk,
        },
    )

    asset.refresh_from_db()
    assert asset.serialnumber == "updated_serialnumber"
    assert response.status_code == 302  # Redirect after success


@pytest.mark.django_db
def test_asset_delete_view_login(client, asset):
    asset = asset()
    url = reverse("assets:delete_asset", kwargs={"pk": asset.assetid})
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert "/login" in response.url.lower()  # Ensure it's going to the login page


@pytest.mark.django_db
def test_asset_delete_view_permission_denied(client, user_setup, asset):
    asset = asset()
    user = user_setup
    client.force_login(user)
    url = reverse("assets:delete_asset", kwargs={"pk": asset.assetid})
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_asset_delete_view_renders(client, user_setup, asset):
    asset = asset()
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
    asset = asset()

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
    asset = asset()
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


@pytest.mark.django_db
def test_filtered_asset_table_view_renders(client, user_setup, asset):
    user = user_setup

    permission = Permission.objects.get(codename="view_assetview")
    user.user_permissions.add(permission)

    asset = asset()
    user.customerid = asset.customerid
    user.save()
    client.force_login(user)

    url = reverse("assets:assets_list")

    # test html get
    response = client.get(url)
    assert response.status_code == 200

# test asset to job filter 
@pytest.mark.django_db
def test_asset_to_job_view_login(
    client,
):
    url = reverse("assets:asset_to_job")
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert "/login" in response.url.lower()  # Ensure it's going to the login page


@pytest.mark.django_db
def test_asset_to_job_view_permission_denied(client, user_setup):
    user = user_setup
    client.force_login(user)
    url = reverse("assets:asset_to_job")
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_asset_to_job_view_renders(client, user, jobs):
    user = user()
    user.is_staff = True
    user.save()
    client.force_login(user)

    permission = Permission.objects.get(codename="view_assetview")
    permission2 = Permission.objects.get(codename="view_jobview")
    user.user_permissions.add(permission)
    user.user_permissions.add(permission2)

    jobs = jobs(count=10)

    base_url = reverse("assets:asset_to_job")
    query_params = urlencode({'additional_filter_options':'filter_latest_ppm'})
    url = f"{base_url}?{query_params}"

    response = client.get(url, HTTP_HX_REQUEST="true")
    assert response.status_code == 200
    session_filter = response.wsgi_request.session["/jobs/jobs/"]
    assert  session_filter

    response = client.get(response['HX-Redirect'])
    assert 0 < len(response.context["table"].rows) < 10

@pytest.mark.django_db
def test_asset_to_job_view_renders_with_selected_ids(client, user, jobs):
    user = user()
    user.is_staff = True
    user.save()
    client.force_login(user)

    permission = Permission.objects.get(codename="view_assetview")
    permission2 = Permission.objects.get(codename="view_jobview")
    user.user_permissions.add(permission)
    user.user_permissions.add(permission2)

    jobs = jobs(count=10)
    asset0 = jobs[0].assetid.pk
    asset0_job_count = Tbljob.objects.filter(assetid=asset0).count()

    base_url = reverse("assets:asset_to_job")
    query_params = urlencode({'selected_ids': asset0})
    url = f"{base_url}?{query_params}"

    response = client.get(url, HTTP_HX_REQUEST="true")
    assert response.status_code == 200
    session_filter = response.wsgi_request.session["/jobs/jobs/"]
    assert  session_filter

    response = client.get(response['HX-Redirect'])
    assert len(response.context["table"].rows) == asset0_job_count

@pytest.mark.django_db
def test_asset_bulk_update_view_renders(client, user_setup, create_assets):
    user = user_setup

    permission = Permission.objects.get(codename="change_tblassets")
    user.user_permissions.add(permission)

    assets = create_assets(count=10)
    user.is_staff = True
    user.save()
    client.force_login(user)

    url = reverse("assets:bulk_update_assets")

    # test html get
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, "assets/bulk_update.html")

@pytest.mark.django_db
def test_asset_bulk_update_view_post_errors(client, user_setup, create_assets):
    user = user_setup

    permission = Permission.objects.get(codename="change_tblassets")
    user.user_permissions.add(permission)

    assets = create_assets(count=10)
    user.is_staff = True
    user.save()
    client.force_login(user)

    url = reverse("assets:bulk_update_assets")

    # test html get
    response = client.post(url)
    assert response.context['form'].errors

@pytest.mark.django_db
def test_asset_bulk_update_view_post(client, user_setup, create_assets):
    user = user_setup

    permission = Permission.objects.get(codename="change_tblassets")
    user.user_permissions.add(permission)

    assets = create_assets(count=10)
    assert Tblassets.objects.filter(is_test_eq=True).count() < 10
    user.is_staff = True
    user.save()
    client.force_login(user)

    url = reverse("assets:bulk_update_assets")
    data = {
        'is_test_eq': True 
    }

    # test html get
    response = client.post(url, data=data)

    assert Tblassets.objects.filter(is_test_eq=True).count() == 10
