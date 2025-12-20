import pytest
from django.urls import reverse
from assets.models import Tblcustomer
from pytest_django.asserts import assertTemplateUsed


@pytest.mark.django_db
def test_model_compliance_view_requires_login(client):
    url = reverse('dashboards:model_compliance')
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login page  
    assert '/login' in response.url.lower()  # Ensure it's going to the login page

@pytest.mark.django_db
def test_model_compliance_view_requires_permission(client, user_setup):
    url = reverse('dashboards:model_compliance')
    user = user_setup
    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 403  # Forbidden if user does not have permission

@pytest.mark.django_db
def test_model_compliance_view_renders(client, user_setup, mocker):
    url = reverse('dashboards:model_compliance')
    user = user_setup
    
    user.customerid = Tblcustomer.objects.first()
    user.save()
    mocker.patch('assets.mixins.CustomerAssetPermissionMixin.has_permission', return_value=True)

    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 200


    user.customerid = Tblcustomer.objects.create(customer_name='Test Customer')
    user.save()
    mocker.patch('assets.mixins.CustomerAssetPermissionMixin.has_permission', return_value=True)

    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 200

    #test htmx
    response = client.get(url, HTTP_HX_REQUEST='true')
    assert response.status_code == 200

@pytest.mark.django_db
def test_asset_compliance_view_requires_login(client):
    url = reverse('dashboards:asset_compliance')
    response = client.get(url)
    assert response.status_code == 302
    assert '/login' in response.url.lower()

@pytest.mark.django_db
def test_asset_compliance_view_requires_permission(client, user_setup):
    url = reverse('dashboards:asset_compliance')
    user = user_setup
    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 403 # Forbidden if user does not have permission 

@pytest.mark.django_db
def test_asset_compliance_view_renders(client, user_setup, mocker):
    url = reverse('dashboards:asset_compliance')
    user = user_setup
    
    user.customerid = Tblcustomer.objects.first()
    user.save()
    mocker.patch('assets.mixins.CustomerAssetPermissionMixin.has_permission', return_value=True)

    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, 'dashboards/partials/asset_overall_compliance.html' )

@pytest.mark.django_db
def test_open_jobs_view_requires_login(client):
    url = reverse('dashboards:open_jobs')
    response = client.get(url)
    assert response.status_code == 302
    assert '/login' in response.url.lower()

@pytest.mark.django_db
def test_open_jobs_view_requires_permission(client, user_setup):
    url = reverse('dashboards:open_jobs')
    user = user_setup
    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 403 # Forbidden if user does not have permission

@pytest.mark.django_db
def test_open_jobs_view_renders(client, user_setup, mocker):
    url = reverse('dashboards:open_jobs')
    user = user_setup
    
    user.customerid = Tblcustomer.objects.first()
    user.save()
    mocker.patch('jobs.mixins.CustomerJobListPermissionMixin.has_permission', return_value=True)

    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, 'dashboards/partials/open_jobs.html')