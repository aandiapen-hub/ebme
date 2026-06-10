import pytest
from django.urls import reverse
from django.contrib.auth.models import Permission
from assets.models import AssetView

@pytest.mark.django_db
def test_customer_asse_permission_mixin_list(
    client,
    user_setup,
    customer,
    create_assets,
):

    customer1 = customer(customer_name='customerA')
    customer2 = customer(customer_name='customerb')

    assets1 = create_assets(customerid=customer1, count=10)
    assets2 = create_assets(customerid=customer2, count=20)

    user = user_setup
    user.is_staff = False
    permission = Permission.objects.get(codename="view_assetview")
    user.user_permissions.add(permission)
    user.customerid = customer1
    user.save()

    client.force_login(user)
    url = reverse('assets:assets_list') 
    response = client.get(url)

    table = response.context['table']
    assert table.data.data.count() == 10

    #asset that no asset from customer2 is in the list
    asset = assets2[0]

    assert asset not in table.data.data


def test_customer_asse_permission_mixin_list_for_staff(
    client,
    user_setup,
    customer,
    create_assets,
):

    customer1 = customer(customer_name='customerA')
    customer2 = customer(customer_name='customerb')

    assets1 = create_assets(customerid=customer1, count=10)
    assets2 = create_assets(customerid=customer2, count=20)

    user = user_setup
    user.is_staff = True 
    permission = Permission.objects.get(codename="view_assetview")
    user.user_permissions.add(permission)
    user.save()

    client.force_login(user)
    url = reverse('assets:assets_list') 
    response = client.get(url)

    table = response.context['table']
    assert table.data.data.count() == 30


@pytest.mark.django_db
def test_customer_asset_permission_mixin_object_for_staff(
    client,
    user_setup,
    customer,
    create_assets,
):

    customer1 = customer(customer_name='customerA')
    customer2 = customer(customer_name='customerb')

    assets1 = create_assets(customerid=customer1, count=10)
    assets2 = create_assets(customerid=customer2, count=20)

    user = user_setup
    user.is_staff = True 
    permission = Permission.objects.get(codename="view_assetview")
    user.user_permissions.add(permission)
    user.save()

    client.force_login(user)
    url = reverse('assets:view_asset', kwargs={'pk': assets1[0].pk}) 
    response = client.get(url)

    obj = AssetView.objects.get(pk=assets1[0].pk)
    assert obj == response.context['asset']

@pytest.mark.django_db
def test_customer_asset_permission_mixin_other_object(
    client,
    user_setup,
    customer,
    create_assets,
):

    customer1 = customer(customer_name='customerA')
    customer2 = customer(customer_name='customerb')

    assets1 = create_assets(customerid=customer1, count=10)
    assets2 = create_assets(customerid=customer2, count=20)

    user = user_setup
    user.is_staff = False
    user.customerid = customer1
    permission = Permission.objects.get(codename="view_assetview")
    user.user_permissions.add(permission)
    user.save()

    client.force_login(user)
    url = reverse('assets:view_asset', kwargs={'pk': assets1[0].pk}) 
    response = client.get(url)

    obj = AssetView.objects.get(pk=assets1[0].pk)
    assert obj == response.context['asset']
    


@pytest.mark.django_db
def test_customer_asset_permission_mixin_other_denied(
    client,
    user_setup,
    customer,
    create_assets,
):

    customer1 = customer(customer_name='customerA')
    customer2 = customer(customer_name='customerb')

    assets1 = create_assets(customerid=customer1, count=10)
    assets2 = create_assets(customerid=customer2, count=20)

    user = user_setup
    user.customerid=customer1
    user.is_staff = False
    permission = Permission.objects.get(codename="view_assetview")
    user.user_permissions.add(permission)
    user.save()

    client.force_login(user)
    url = reverse('assets:view_asset', kwargs={'pk': assets2[0].pk}) 
    response = client.get(url)
    assert response.status_code == 404


@pytest.mark.django_db
def test_non_staff_with_no_customer_obj_permission_denied(
    client,
    user_setup,
    customer,
    create_assets,
):

    customer1 = customer(customer_name='customerA')
    customer2 = customer(customer_name='customerb')

    assets1 = create_assets(customerid=customer1, count=10)
    assets2 = create_assets(customerid=customer2, count=20)

    user = user_setup
    user.customerid = None
    user.is_staff = False
    permission = Permission.objects.get(codename="view_assetview")
    user.user_permissions.add(permission)
    user.save()

    client.force_login(user)
    url = reverse('assets:view_asset', kwargs={'pk': assets2[0].pk}) 

    response = client.get(url)
    assert response.status_code == 404


@pytest.mark.django_db
def test_non_staff_with_no_customer_qs_permission_denied(
    client,
    user_setup,
    customer,
    create_assets,
):

    customer1 = customer(customer_name='customerA')
    customer2 = customer(customer_name='customerb')

    assets1 = create_assets(customerid=customer1, count=10)
    assets2 = create_assets(customerid=customer2, count=20)

    user = user_setup
    user.customerid = None
    user.is_staff = False
    permission = Permission.objects.get(codename="view_assetview")
    user.user_permissions.add(permission)
    user.save()

    client.force_login(user)
    url = reverse('assets:view_asset', kwargs={'pk': assets2[0].pk}) 

    response = client.get(url)
    assert response.status_code == 404
