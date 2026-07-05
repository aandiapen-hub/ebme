from assets.models import Tblmodel
from documents.models import TemporaryUpload, TempUploadGroup
import pytest
from django.contrib.auth.models import Permission
from django.urls import reverse
from urllib.parse import urlencode

@pytest.mark.django_db
def test_payload_initial(
        client,
        user,
        asset_data_temp_group,
        asset,
        model,
        brand,
        mocker, 
):

    group = asset_data_temp_group
    user = user()
    user.is_staff = True
    user.save()
    permission = Permission.objects.get(codename="add_tblassets")
    user.user_permissions.add(permission)
    client.force_login(user)

    query_params = urlencode({'temp_group_id': group.pk})
    base_url = reverse('assets:create_asset')
    url = f"{base_url}?{query_params}"
    response = client.get(url)
    assert response.context['form'].initial['serialnumber'] == 'S00455524'

@pytest.mark.django_db
def test_payload_context(
        client,
        user,
        asset_data_temp_group,
):

    group = asset_data_temp_group
    user = user()
    user.is_staff = True
    user.save()
    permission = Permission.objects.get(codename="add_tblmodel")
    user.user_permissions.add(permission)
    client.force_login(user)

    query_params = urlencode({'temp_group_id': group.pk})
    base_url = reverse('model_information:create_model')
    url = f"{base_url}?{query_params}"
    response = client.get(url)
    assert response.context['form'].initial['gtin'] == '00885403497233'


@pytest.mark.django_db
def test_payload_post_with_save_document(
    client,
    user,
    asset_data_temp_group,
    asset_id_temp_document,
    brand,
    category,
    
):
    group = asset_data_temp_group
    document = asset_id_temp_document
    document.group = group
    document.save()
    user = user()
    user.is_staff = True
    user.save()
    permission = Permission.objects.get(codename="add_tblmodel")
    user.user_permissions.add(permission)
    client.force_login(user)

    gtin = '00885403497233'

    url = reverse('model_information:create_model')
    data = {
        'temp_group_id': group.pk,
        'save_and_attach_document': True,
        'brandid': brand().pk,
        'categoryid': category().pk,
        'modelname':'test',
        'gtin': gtin
    }

    response = client.post(url, data=data)

    created_model = Tblmodel.objects.last()
    assert created_model.gtin == gtin
    assert created_model.document_links.all().exists()

    document.refresh_from_db()
    assert document

@pytest.mark.django_db
def test_payload_post_with_save_and_delete_document(
    client,
    user,
    asset_data_temp_group,
    asset_id_temp_document,
    brand,
    category,
    
):
    group = asset_data_temp_group
    document = asset_id_temp_document
    document.group = group
    document.save()
    user = user()
    user.is_staff = True
    user.save()
    permission = Permission.objects.get(codename="add_tblmodel")
    user.user_permissions.add(permission)
    client.force_login(user)

    gtin = '00885403497233'

    url = reverse('model_information:create_model')
    data = {
        'temp_group_id': group.pk,
        'save_and_attach_document': True,
        'delete_temp_files_after_save': True,
        'brandid': brand().pk,
        'categoryid': category().pk,
        'modelname':'test',
        'gtin': gtin
    }

    response = client.post(url, data=data)
    assert response.status_code == 302

    created_model = Tblmodel.objects.last()
    assert created_model.gtin == gtin
    assert created_model.document_links.all().exists()
    assert not TemporaryUpload.objects.filter(pk=document.pk)
    assert not TempUploadGroup.objects.filter(pk=document.group.pk)


@pytest.mark.django_db
def test_payload_post_with_date(
    client,
    user,
    asset_data_temp_group,
    asset_id_temp_document,
    asset,
    
):
    group = asset_data_temp_group
    document = asset_id_temp_document
    asset = asset()
    document.group = group
    document.save()
    user = user()
    user.is_staff = True
    user.save()
    permission = Permission.objects.get(codename="change_tblassets")
    user.user_permissions.add(permission)
    client.force_login(user)

    base_url = reverse('assets:update_asset', kwargs={'pk':asset.pk})
    query_params = urlencode({'temp_group_id': group.pk})
    url = f"{base_url}?{query_params}"

    response = client.get(url)
    assert response.status_code == 200
    from datetime import date
    assert response.context['form'].initial['prod_date'] == date(2023, 4, 23)


