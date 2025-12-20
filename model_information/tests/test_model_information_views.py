from certifi import contents
import pytest
from pytest_django.asserts import assertTemplateUsed
from django.urls import reverse
from assets.models import (Tblmodel,
                        Tblbrands,
                        Tblcategories,
                        Tblcheckslists, Tbltestscarriedout
)
from django.test import RequestFactory
from unittest.mock import patch
from urllib.parse import urlencode

from assets.tests.factories import BrandFactory, ModelFactory,CategoryFactory
from jobs.tests.factories import ChecklistsFactory
#test brand views

#test BrandTableView
@pytest.mark.django_db
def test_brand_table_view_requires_login(client):
    url = reverse('model_information:brandlist')  # Update to your actual URL name
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert '/login' in response.url.lower()  # Ensure it's going to the login page

@pytest.mark.django_db
def test_brand_table_view_permission_denied(client, user_setup):
    user = user_setup
    client.force_login(user)

    url = reverse('model_information:brandlist')  # Update to your actual URL name
    response = client.get(url)
    
    assert response.status_code == 403  # Depends on how CustomerAssetPermissionMixin handles it


@pytest.mark.parametrize("search_term", [
    "med 123", "1,2,3"
])
@pytest.mark.django_db
def test_brand_table_view_renders(client, user_setup,mocker, search_term):
    user = user_setup
    client.force_login(user)
    mocker.patch(
        'django.contrib.auth.mixins.PermissionRequiredMixin.has_permission',
         return_value=True)

    url = reverse('model_information:brandlist')  # Update to your actual URL name
    
    response = client.get(url)

    #test html
    assert response.status_code == 200  # Depends on how CustomerAssetPermissionMixin handles it
    assertTemplateUsed(response,"model_information/brandlist.html")

    #test htmx
    response = client.get(url,HTTP_HX_REQUEST='true' )
    assert response.status_code == 200

    #test filter
    query_string = urlencode({'universal_search': search_term})
    url =   f"{url}?{query_string}"
    response = client.get(url, HTTP_HX_REQUEST='true')
    assert response.status_code == 200 
    

#test BrandUpdateview
@pytest.mark.django_db
def test_brand_update_view_requires_login(client):
    brand = Tblbrands.objects.last()
    url = reverse('model_information:update_brand',kwargs={'pk':brand.brandid})  # Update to your actual URL name
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert '/login' in response.url.lower()  # Ensure it's going to the login page

@pytest.mark.django_db
def test_brand_update_view_requires_permission(client,user_setup):
    brand = Tblbrands.objects.last()
    user = user_setup

    url = reverse('model_information:update_brand',kwargs={'pk':brand.brandid})  # Update to your actual URL name
    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 403  # Redirect to login

@pytest.mark.django_db
def test_brand_update_view_renders(client,user_setup,mocker):
    brand = Tblbrands.objects.last()
    user = user_setup
    mocker.patch(
        'django.contrib.auth.mixins.PermissionRequiredMixin.has_permission',
         return_value=True)

    url = reverse('model_information:update_brand',kwargs={'pk':brand.brandid})  # Update to your actual URL name
    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 200  # Redirect to login
    assertTemplateUsed(response, "model_information/partials/modal.html")
    assert response.context['title'] == 'Update Brand'

@pytest.mark.django_db
def test_brand_update_view_posts_successfully(client,user_setup,mocker):
    brand = Tblbrands.objects.last()
    user = user_setup
    mocker.patch(
        'django.contrib.auth.mixins.PermissionRequiredMixin.has_permission',
         return_value=True)

    url = reverse('model_information:update_brand',kwargs={'pk':brand.brandid})  
    client.force_login(user)

    #test html post
    form = {
        'brandname':'brandtest'
    }
    response = client.post(url,data=form)

    assert response.status_code == 302
    brand.refresh_from_db()
    assert brand.brandname == 'brandtest'
    assert response.url == reverse('model_information:brandlist')

    #test htmx post
    form = {
    'brandname':'brandtest2'
    }
    response = client.post(url,data=form,HTTP_HX_REQUEST='true' )

    assert response.status_code == 204
    brand.refresh_from_db()
    assert brand.brandname == 'brandtest2'

#test BrandCreateView

@pytest.mark.django_db
def test_brand_create_view_requires_login(client):
    url = reverse('model_information:create_brand')  # Update to your actual URL name
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert '/login' in response.url.lower()  # Ensure it's going to the login page

@pytest.mark.django_db
def test_brand_create_view_requires_permission(client,user_setup):
    user = user_setup

    url = reverse('model_information:create_brand')

    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 403 

@pytest.mark.django_db
def test_brand_create_view_renders(client,user_setup,mocker):
    user = user_setup
    mocker.patch(
        'django.contrib.auth.mixins.PermissionRequiredMixin.has_permission',
         return_value=True)

    url = reverse('model_information:create_brand')
    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, "model_information/partials/modal.html")
    assert response.context['title'] == 'Create New Brand'
    assert response.context['view_type'] == 'create'
    
def test_brand_create_view_posts_successfully(client,user_setup,mocker):
    
    user = user_setup
    mocker.patch(
        'django.contrib.auth.mixins.PermissionRequiredMixin.has_permission',
         return_value=True)

    url = reverse('model_information:create_brand')  
    client.force_login(user)

    #test html post
    form = {
        'brandname':'brandtest'
    }
    response = client.post(url,data=form)

    assert response.status_code == 200
    brand = Tblbrands.objects.last()
    assert brand.brandname == 'brandtest'



@pytest.mark.django_db
def test_brand_create_view_renders(client,user_setup,mocker):
    user = user_setup
    mocker.patch(
        'django.contrib.auth.mixins.PermissionRequiredMixin.has_permission',
         return_value=True)

    url = reverse('model_information:create_brand')
    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, "model_information/partials/modal.html")
    assert response.context['title'] == 'Create New Brand'
    assert response.context['view_type'] == 'create'
    
def test_brand_create_view_requires_posts_unsuccessful(client,user_setup,mocker):
    
    user = user_setup
    mocker.patch(
        'django.contrib.auth.mixins.PermissionRequiredMixin.has_permission',
         return_value=True)

    url = reverse('model_information:create_brand')  
    client.force_login(user)

    #test html post
    form = {
    }
    response = client.post(url,data=form)

    assert response.status_code == 200
    assert response.context['form'].errors



#test BrandDeleteView
@pytest.mark.django_db
def test_brand_delete_view_requires_login(client):
    brand = Tblbrands.objects.last()
    url = reverse('model_information:delete_brand',kwargs={'pk':brand.brandid})  # Update to your actual URL name
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert '/login' in response.url.lower()  # Ensure it's going to the login page

@pytest.mark.django_db
def test_brand_delete_view_requires_permission(client,user_setup):
    brand = Tblbrands.objects.last()
    user = user_setup

    url = reverse('model_information:delete_brand',kwargs={'pk':brand.brandid})  # Update to your actual URL name
    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 403  # Redirect to login

@pytest.mark.django_db
def test_brand_delete_view_renders(client,user_setup,mocker):
    brand = Tblbrands.objects.last()
    user = user_setup
    mocker.patch(
        'django.contrib.auth.mixins.PermissionRequiredMixin.has_permission',
         return_value=True)

    url = reverse('model_information:delete_brand',kwargs={'pk':brand.brandid})  # Update to your actual URL name
    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 200  # Redirect to login
    assertTemplateUsed(response, "model_information/partials/delete_modal.html")
    assert response.context['title'] == 'Delete Brand'
    assert response.context["view_type"] == 'delete'

@pytest.mark.django_db
def test_brand_delete_view_posts_unsuccessfully(client,user_setup,mocker):
    brand = Tblbrands.objects.first()
    brandid = brand.brandid
    user = user_setup
    mocker.patch(
        'django.contrib.auth.mixins.PermissionRequiredMixin.has_permission',
         return_value=True)

    url = reverse('model_information:delete_brand',kwargs={'pk':brandid})  
    client.force_login(user)

    response = client.post(url)

    assert "An error occurred while deleting the brand" in response.context['error_message']

@pytest.mark.django_db
def test_brand_delete_view_requires_posts_successfully(client,user_setup,mocker):
    brand = BrandFactory(brandname="TestBrand")
    
    brandid = brand.brandid
    user = user_setup
    mocker.patch(
        'django.contrib.auth.mixins.PermissionRequiredMixin.has_permission',
         return_value=True)

    url = reverse('model_information:delete_brand',kwargs={'pk':brandid})  
    client.force_login(user)

    response = client.post(url)

    assert response.status_code == 204
    assert not Tblbrands.objects.filter(brandid=brandid).exists()

#test model views

#test ModelTableView
@pytest.mark.django_db
def test_model_table_view_requires_login(client):
    url = reverse('model_information:modellist')  # Update to your actual URL name
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert '/login' in response.url.lower()  # Ensure it's going to the login page

@pytest.mark.django_db
def test_model_table_view_permission_denied(client, user_setup):
    user = user_setup
    client.force_login(user)

    url = reverse('model_information:modellist')  # Update to your actual URL name
    response = client.get(url)
    
    assert response.status_code == 403  # Depends on how CustomerAssetPermissionMixin handles it

@pytest.mark.parametrize("search_term", [
    "med 123", "1,2,3"
])
@pytest.mark.django_db
def test_model_table_view_renders(client, user_setup,mocker, search_term):
    user = user_setup
    client.force_login(user)
    mocker.patch(
        'django.contrib.auth.mixins.PermissionRequiredMixin.has_permission',
         return_value=True)

    url = reverse('model_information:modellist')  # Update to your actual URL name
    
    response = client.get(url)

    #test html
    assert response.status_code == 200  # Depends on how CustomerAssetPermissionMixin handles it
    assertTemplateUsed(response,"model_information/modellist.html")

    #test htmx
    response = client.get(url,HTTP_HX_REQUEST='true' )
    assert response.status_code == 200

    #test filter
    query_string = urlencode({'universal_search': search_term})
    url =   f"{url}?{query_string}"
    response = client.get(url, HTTP_HX_REQUEST='true')
    assert response.status_code == 200 
    

#test ModelUpdateView

@pytest.mark.django_db
def test_model_update_view_requires_login(client):
    model = Tblmodel.objects.last()
    url = reverse('model_information:update_model',kwargs={'pk':model.modelid}) 
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert '/login' in response.url.lower()  # Ensure it's going to the login page

@pytest.mark.django_db
def test_model_update_view_requires_permission(client,user_setup):
    model = Tblmodel.objects.last()
    url = reverse('model_information:update_model',kwargs={'pk':model.modelid})

    user = user_setup
    
    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 403  # Redirect to login

@pytest.mark.django_db
def test_model_update_view_renders(client,user_setup,mocker):
    model = Tblmodel.objects.last()
    url = reverse('model_information:update_model',kwargs={'pk':model.modelid})
    
    user = user_setup
    mocker.patch(
        'django.contrib.auth.mixins.PermissionRequiredMixin.has_permission',
         return_value=True)
    query_params = urlencode({'gtin': 123554})
    
    client.force_login(user)
    response = client.get(f"{url}?{query_params}")
    assert response.status_code == 200  # Redirect to login
    assertTemplateUsed(response, "model_information/partials/model_update.html")

@pytest.mark.django_db
def test_model_update_view_posts_successfully(client,user_setup,mocker):
    model = Tblmodel.objects.last()
    url = reverse('model_information:update_model',kwargs={'pk':model.modelid})

    user = user_setup
    mocker.patch(
        'django.contrib.auth.mixins.PermissionRequiredMixin.has_permission',
         return_value=True)

    
    client.force_login(user)

    #test html post
    form = {
        'modelname': 'testmodel',
        'brandid': model.brandid.brandid,
        'categoryid': model.categoryid.categoryid
    }
    response = client.post(url,data=form)
    assert response.status_code == 302
    model.refresh_from_db()
    assert model.modelname == 'testmodel'
    assert response.url == reverse('model_information:model_view', kwargs={'pk':model.modelid})


#test ModelCreateView

@pytest.mark.django_db
def test_model_create_view_requires_login(client):
    url = reverse('model_information:create_model')  # Update to your actual URL name
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert '/login' in response.url.lower()  # Ensure it's going to the login page

@pytest.mark.django_db
def test_model_create_view_requires_permission(client,user_setup):
    user = user_setup
    url = reverse('model_information:create_model')

    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 403 

@pytest.mark.django_db
def test_model_create_view_renders(client,user_setup,mocker):
    user = user_setup
    mocker.patch(
        'django.contrib.auth.mixins.PermissionRequiredMixin.has_permission',
         return_value=True)

    url = reverse('model_information:create_model')
    query_params = urlencode({'gtin': 123554})
    
    client.force_login(user)
    response = client.get(f"{url}?{query_params}")
    
    assert response.status_code == 200
    assertTemplateUsed(response, "model_information/partials/model_create.html")

    
def test_model_create_view_requires_posts_successfully(client,user_setup,mocker):
    
    user = user_setup
    mocker.patch(
        'django.contrib.auth.mixins.PermissionRequiredMixin.has_permission',
         return_value=True)

    url = reverse('model_information:create_model')  
    client.force_login(user)

    #test html post
    form = {
        'modelname': 'testmodel',
        'brandid': Tblbrands.objects.last().brandid,
        'categoryid': Tblcategories.objects.last().categoryid
    }
    response = client.post(url,data=form)

    created_model = Tblmodel.objects.last()
    assert response.status_code == 302
    assert created_model.modelname == 'testmodel'
    assert response.url == reverse('model_information:model_view', kwargs={'pk':created_model.modelid})


    
    
#test ModelDeleteView

@pytest.mark.django_db
def test_model_delete_view_requires_login(client):
    model = Tblmodel.objects.last()
    url = reverse('model_information:delete_model',kwargs={'pk':model.modelid}) 
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert '/login' in response.url.lower()  # Ensure it's going to the login page

@pytest.mark.django_db
def test_model_delete_view_requires_permission(client,user_setup):
    model = Tblmodel.objects.last()
    url = reverse('model_information:delete_model',kwargs={'pk':model.modelid})

    user = user_setup
    
    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 403  # Redirect to login

@pytest.mark.django_db
def test_model_delete_view_renders(client,user_setup,mocker):
    model = Tblmodel.objects.last()
    url = reverse('model_information:delete_model',kwargs={'pk':model.modelid})
    
    user = user_setup
    mocker.patch(
        'django.contrib.auth.mixins.PermissionRequiredMixin.has_permission',
         return_value=True)

    
    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 200  
    assertTemplateUsed(response, "model_information/partials/modal.html")
    assert response.context['title'] == 'Delete Model'
    assert response.context['view_type'] == 'delete'

@pytest.mark.django_db
def test_model_delete_view_posts_unsuccessfully(client,user_setup,mocker):
    model = Tblmodel.objects.first()
    modelid = model.modelid
    url = reverse('model_information:delete_model',kwargs={'pk':modelid})

    user = user_setup
    mocker.patch(
        'django.contrib.auth.mixins.PermissionRequiredMixin.has_permission',
         return_value=True)

    
    client.force_login(user)


    response = client.post(url)
    assert "An error occurred while deleting the model" in response.context['error_message']
    

@pytest.mark.django_db
def test_model_delete_view_posts_successfully(client,user_setup,mocker):
    model = ModelFactory(modelname='testmodel')
    modelid = model.modelid
    url = reverse('model_information:delete_model',kwargs={'pk':modelid})

    user = user_setup
    mocker.patch(
        'django.contrib.auth.mixins.PermissionRequiredMixin.has_permission',
         return_value=True)

    
    client.force_login(user)


    response = client.post(url)
    assert response.status_code == 302
    assert response.url == reverse('model_information:modellist')
    assert not Tblmodel.objects.filter(modelid=modelid).exists()


@pytest.mark.django_db
def test_model_delete_view_posts_successfully_htmx(client,user_setup,mocker):
    model = ModelFactory(modelname='testmodel')
    modelid = model.modelid
    url = reverse('model_information:delete_model',kwargs={'pk':modelid})
    user = user_setup
    mocker.patch(
        'django.contrib.auth.mixins.PermissionRequiredMixin.has_permission',
         return_value=True)

    client.force_login(user)
    response = client.post(url,HTTP_HX_REQUEST='true')
    assert response.status_code == 200
    assert not Tblmodel.objects.filter(modelid=modelid).exists()

# test ModelDetailView
@pytest.mark.django_db
def test_model_detail_view_requires_login(client):
    model = Tblmodel.objects.last()
    url = reverse('model_information:model_view',kwargs={'pk':model.modelid}) 
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert '/login' in response.url.lower()  # Ensure it's going to the login page

@pytest.mark.django_db
def test_model_detail_view_requires_permission(client,user_setup):
    model = Tblmodel.objects.last()
    url = reverse('model_information:model_view',kwargs={'pk':model.modelid}) 
    user = user_setup
    
    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 403  # Redirect to login

@pytest.mark.django_db
def test_model_detail_view_renders(client,user_setup,mocker):
    model = Tblmodel.objects.last()
    url = reverse('model_information:model_view',kwargs={'pk':model.modelid}) 
    
    user = user_setup
    mocker.patch(
        'django.contrib.auth.mixins.PermissionRequiredMixin.has_permission',
         return_value=True)

    
    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 200  
    assertTemplateUsed(response, "model_information/model_view.html")

    
#test Categories

#test FilteredCategoryTableView

@pytest.mark.django_db
def test_category_table_view_requires_login(client):
    url = reverse('model_information:categorylist')  # Update to your actual URL name
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert '/login' in response.url.lower()  # Ensure it's going to the login page

@pytest.mark.django_db
def test_category_table_view_permission_denied(client, user_setup):
    user = user_setup
    client.force_login(user)

    url = reverse('model_information:categorylist')  # Update to your actual URL name
    response = client.get(url)
    
    assert response.status_code == 403  # Depends on how CustomerAssetPermissionMixin handles it

@pytest.mark.parametrize("search_term", [
    "med 123", "1,2,3"
])
@pytest.mark.django_db
def test_category_table_view_renders(client, user_setup,mocker, search_term):
    user = user_setup
    client.force_login(user)
    mocker.patch(
        'django.contrib.auth.mixins.PermissionRequiredMixin.has_permission',
         return_value=True)

    url = reverse('model_information:categorylist')  # Update to your actual URL name
    
    response = client.get(url)

    #test html
    assert response.status_code == 200  # Depends on how CustomerAssetPermissionMixin handles it
    assertTemplateUsed(response,"model_information/categorylist.html")

    #test htmx
    response = client.get(url,HTTP_HX_REQUEST='true' )
    assert response.status_code == 200

    #test filter
    query_string = urlencode({'universal_search': search_term})
    url =   f"{url}?{query_string}"
    response = client.get(url, HTTP_HX_REQUEST='true')
    assert response.status_code == 200 
    
#test CategoryUpdateView
@pytest.mark.django_db
def test_category_update_view_requires_login(client):
    category = Tblcategories.objects.last()
    url = reverse('model_information:update_category',kwargs={'pk':category.categoryid})  
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert '/login' in response.url.lower()  # Ensure it's going to the login page

@pytest.mark.django_db
def test_category_update_view_requires_permission(client,user_setup):
    category = Tblcategories.objects.last()
    user = user_setup

    url = reverse('model_information:update_category',kwargs={'pk':category.categoryid})
    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 403 

@pytest.mark.django_db
def test_category_update_view_renders(client,user_setup,mocker):
    category = Tblcategories.objects.last()
    user = user_setup
    mocker.patch(
        'django.contrib.auth.mixins.PermissionRequiredMixin.has_permission',
         return_value=True)

    url = reverse('model_information:update_category',kwargs={'pk':category.categoryid}) 
    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 200  
    assertTemplateUsed(response, "model_information/partials/modal.html")
    assert response.context['title'] == 'Update Category'

@pytest.mark.django_db
def test_category_update_view_posts_successfully(client,user_setup,mocker):
    category = Tblcategories.objects.last()
    user = user_setup
    mocker.patch(
        'django.contrib.auth.mixins.PermissionRequiredMixin.has_permission',
         return_value=True)

    url = reverse('model_information:update_category',kwargs={'pk':category.categoryid})  
    client.force_login(user)

    #test html post
    form = {
        'categoryname':'testcategory'
    }
    response = client.post(url,data=form)

    assert response.status_code == 302
    category.refresh_from_db()
    assert category.categoryname == 'testcategory'
    assert response.url == reverse('model_information:categorylist')

    # test htmx
    form = {
        'categoryname':'testcategory2'
    }
    response = client.post(url,data=form, HTTP_HX_REQUEST='true')

    assert response.status_code == 204
    category.refresh_from_db()
    assert category.categoryname == 'testcategory2'


#test CategoryCreateView

@pytest.mark.django_db
def test_category_create_view_requires_login(client):
    url = reverse('model_information:create_category')  # Update to your actual URL name
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert '/login' in response.url.lower()  # Ensure it's going to the login page

@pytest.mark.django_db
def test_category_create_view_requires_permission(client,user_setup):
    user = user_setup

    url = reverse('model_information:create_category')

    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 403 

@pytest.mark.django_db
def test_category_create_view_renders(client,user_setup,mocker):
    user = user_setup
    mocker.patch(
        'django.contrib.auth.mixins.PermissionRequiredMixin.has_permission',
         return_value=True)

    url = reverse('model_information:create_category')
    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, "model_information/partials/modal.html")
    assert response.context['title'] == 'Create New Category'
    assert response.context['view_type'] == 'create'
    
def test_category_create_view_posts_successfully(client,user_setup,mocker):
    
    user = user_setup
    mocker.patch(
        'django.contrib.auth.mixins.PermissionRequiredMixin.has_permission',
         return_value=True)

    url = reverse('model_information:create_category')  
    client.force_login(user)

    #test html post
    form = {
        'categoryname':'testcategory'
    }
    response = client.post(url,data=form)

    assert response.status_code == 200
    category = Tblcategories.objects.last()
    assert category.categoryname == 'testcategory'


def test_category_create_view_requires_posts_unsuccessfully(client,user_setup,mocker):
    
    user = user_setup
    mocker.patch(
        'django.contrib.auth.mixins.PermissionRequiredMixin.has_permission',
         return_value=True)

    url = reverse('model_information:create_category')  
    client.force_login(user)

    #test html post
    form = {
    }
    response = client.post(url,data=form)

    assert response.status_code == 200
    assert response.context['form'].errors

#test CategoryDeleteView


@pytest.mark.django_db
def test_category_delete_view_requires_login(client):
    category = Tblcategories.objects.last()
    url = reverse('model_information:delete_category',kwargs={'pk':category.categoryid}) 
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert '/login' in response.url.lower()  # Ensure it's going to the login page

@pytest.mark.django_db
def test_category_delete_view_requires_permission(client,user_setup):
    category = Tblcategories.objects.last()
    url = reverse('model_information:delete_category',kwargs={'pk':category.categoryid})

    user = user_setup
    
    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 403  # Redirect to login

@pytest.mark.django_db
def test_category_delete_view_renders(client,user_setup,mocker):
    category = Tblcategories.objects.last()
    url = reverse('model_information:delete_category',kwargs={'pk':category.categoryid})
    
    user = user_setup
    mocker.patch(
        'django.contrib.auth.mixins.PermissionRequiredMixin.has_permission',
         return_value=True)

    
    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 200  
    assertTemplateUsed(response, "model_information/partials/delete_modal.html")
    assert response.context['title'] == 'Delete Category'
    assert response.context['view_type'] == 'delete'

@pytest.mark.django_db
def test_category_delete_view_posts_unsuccessfully(client,user_setup,mocker):
    category = Tblcategories.objects.first()
    categoryid = category.categoryid
    url = reverse('model_information:delete_category',kwargs={'pk':categoryid})

    user = user_setup
    mocker.patch(
        'django.contrib.auth.mixins.PermissionRequiredMixin.has_permission',
         return_value=True)
    client.force_login(user)
    response = client.post(url)
    assert "An error occurred while deleting the category" in response.context['error_message']
    

@pytest.mark.django_db
def test_category_delete_view_posts_successfully(client,user_setup,mocker):
    category = CategoryFactory(categoryname='testcategory')
    categoryid = category.categoryid
    url = reverse('model_information:delete_category',kwargs={'pk':categoryid})

    user = user_setup
    mocker.patch(
        'django.contrib.auth.mixins.PermissionRequiredMixin.has_permission',
         return_value=True)

    
    client.force_login(user)


    response = client.post(url)
    assert response.status_code == 302
    assert response.url == reverse('model_information:categorylist')
    assert not Tblcategories.objects.filter(categoryid=categoryid).exists()




#test Checklists views

#test CheckslistTableView

@pytest.mark.django_db
def test_checklist_table_view_requires_login(client):
    url = reverse('model_information:checklist')  # Update to your actual URL name
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert '/login' in response.url.lower()  # Ensure it's going to the login page

@pytest.mark.django_db
def test_checklist_table_view_permission_denied(client, user_setup):
    user = user_setup
    client.force_login(user)

    url = reverse('model_information:checklist')  # Update to your actual URL name
    response = client.get(url)
    
    assert response.status_code == 403  # Depends on how CustomerAssetPermissionMixin handles it

@pytest.mark.django_db
def test_checklist_table_view_renders(client, user_setup,mocker):
    user = user_setup
    client.force_login(user)
    mocker.patch(
        'django.contrib.auth.mixins.PermissionRequiredMixin.has_permission',
         return_value=True)

    url = reverse('model_information:checklist')  # Update to your actual URL name
    
    response = client.get(url)

    #test html
    assert response.status_code == 200  # Depends on how CustomerAssetPermissionMixin handles it
    assertTemplateUsed(response,"model_information/partials/checklist.html")

@pytest.mark.django_db
def test_checklist_table_view_renders_with_model(client, user_setup,mocker):
    user = user_setup
    client.force_login(user)
    mocker.patch(
        'django.contrib.auth.mixins.PermissionRequiredMixin.has_permission',
         return_value=True)

    base_url = reverse('model_information:checklist')  # Update to your actual URL name
    query_params = urlencode({'modelid':2})
    url = f"{base_url}?{query_params}"
    
    response = client.get(url)

    #test html
    assert response.status_code == 200  # Depends on how CustomerAssetPermissionMixin handles it
    assertTemplateUsed(response,"model_information/partials/checklist.html")

#test CheckUpdateView
@pytest.mark.django_db
def test_check_update_view_requires_login(client):
    check = Tblcheckslists.objects.last()
    testid = check.testid
    url = reverse('model_information:update_check',kwargs={'pk':testid}) 
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert '/login' in response.url.lower()  # Ensure it's going to the login page

@pytest.mark.django_db
def test_check_update_view_requires_permission(client,user_setup):
    check = Tblcheckslists.objects.last()
    testid = check.testid
    url = reverse('model_information:update_check',kwargs={'pk':testid})

    user = user_setup
    
    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 403  # Redirect to login

@pytest.mark.django_db
def test_check_update_view_renders(client,user_setup,mocker):
    check = Tblcheckslists.objects.last()
    testid = check.testid
    url = reverse('model_information:update_check',kwargs={'pk':testid})

    user = user_setup
    mocker.patch(
        'django.contrib.auth.mixins.PermissionRequiredMixin.has_permission',
         return_value=True)

    
    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 200  # Redirect to login
    assertTemplateUsed(response, "model_information/partials/modal.html")
    assert response.context['title'] == 'Update Check'
    assert response.context['view_type'] == 'update'

@pytest.mark.django_db
def test_check_update_view_posts_successfully(client,user_setup,mocker):
    check = Tblcheckslists.objects.last()
    testid = check.testid
    url = reverse('model_information:update_check',kwargs={'pk':testid})

    user = user_setup
    mocker.patch(
        'django.contrib.auth.mixins.PermissionRequiredMixin.has_permission',
         return_value=True)

    
    client.force_login(user)

    #test html post
    form = {
        'testname': 'test_test',
        'test_description': 'testdescripton',
        'modelid': Tblmodel.objects.last().modelid
    }
    response = client.post(url,data=form)
    assert response.status_code == 302
    check.refresh_from_db()
    assert 'test_test' in check.testname
    assert response.url == reverse('model_information:checklist')

    #test htmx post
    form = {
        'testname': 'test_test2',
        'test_description': 'testdescripton',
        'modelid': Tblmodel.objects.last().modelid
    }
    response = client.post(url,data=form,HTTP_HX_REQUEST='true' )

    assert response.status_code == 204
    check.refresh_from_db()
    assert 'test_test2' in check.testname

# test CheckDeleteView

@pytest.mark.django_db
def test_check_delete_view_requires_login(client):
    check = Tblcheckslists.objects.last()
    checkid = check.testid
    url = reverse('model_information:delete_check',kwargs={'pk':checkid}) 
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert '/login' in response.url.lower()  # Ensure it's going to the login page

@pytest.mark.django_db
def test_check_delete_view_requires_permission(client,user_setup):
    check = Tblcheckslists.objects.last()
    checkid = check.testid
    url = reverse('model_information:delete_check',kwargs={'pk':checkid}) 
    
    user = user_setup
    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 403  # Redirect to login

@pytest.mark.django_db
def test_model_delete_view_renders(client,user_setup,mocker):
    check = Tblcheckslists.objects.last()
    checkid = check.testid
    url = reverse('model_information:delete_check',kwargs={'pk':checkid}) 
    user = user_setup

    mocker.patch(
        'django.contrib.auth.mixins.PermissionRequiredMixin.has_permission',
         return_value=True)

    
    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 200  
    assertTemplateUsed(response, "model_information/partials/modal.html")
    assert response.context['title'] == 'Delete Test'
    assert response.context['view_type'] == 'delete'

@pytest.mark.django_db
def test_check_delete_view_posts_unsuccessfully(client,user_setup,mocker):
    testcarriedout = Tbltestscarriedout.objects.last()
    check = Tblcheckslists.objects.get(testid=testcarriedout.checkid.testid)
    checkid = check.testid
    url = reverse('model_information:delete_check',kwargs={'pk':checkid}) 

    user = user_setup
    mocker.patch(
        'django.contrib.auth.mixins.PermissionRequiredMixin.has_permission',
         return_value=True)

    
    client.force_login(user)


    response = client.post(url)
    assert "An error occurred while deleting the test" in response.context['error_message']
    

@pytest.mark.django_db
def test_check_delete_view_posts_successfully(client,user_setup,mocker):
    check = ChecklistsFactory(testname='test_test')
    checkid = check.testid
    url = reverse('model_information:delete_check',kwargs={'pk':checkid})

    user = user_setup
    mocker.patch(
        'django.contrib.auth.mixins.PermissionRequiredMixin.has_permission',
         return_value=True)

    
    client.force_login(user)
    response = client.post(url)
    assert response.status_code == 302
    assert response.url == reverse('model_information:checklist')
    assert not Tblcheckslists.objects.filter(testid=checkid).exists()


@pytest.mark.django_db
def test_check_delete_view_posts_successfully_htmx(client,user_setup,mocker):
    check = ChecklistsFactory(testname='test_test')
    checkid = check.testid
    url = reverse('model_information:delete_check',kwargs={'pk':checkid})

    user = user_setup
    mocker.patch(
        'django.contrib.auth.mixins.PermissionRequiredMixin.has_permission',
         return_value=True)

    client.force_login(user)

    response = client.post(url, HTTP_HX_REQUEST = 'true')
    assert response.status_code == 204
    assert not Tblcheckslists.objects.filter(testid=checkid).exists()

#test CheckCreateView

@pytest.mark.django_db
def test_check_create_view_requires_login(client):
    url = reverse('model_information:create_check')  # Update to your actual URL name
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert '/login' in response.url.lower()  # Ensure it's going to the login page

@pytest.mark.django_db
def test_check_create_view_requires_permission(client,user_setup):
    user = user_setup
    url = reverse('model_information:create_check')

    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 403 

@pytest.mark.django_db
def test_check_create_view_renders(client,user_setup,mocker):
    user = user_setup
    mocker.patch(
        'django.contrib.auth.mixins.PermissionRequiredMixin.has_permission',
         return_value=True)

    url = reverse('model_information:create_check')
    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, "model_information/partials/modal.html")
    assert response.context['title'] == 'Create New Test'
    assert response.context['view_type'] == 'create'
    
def test_check_create_view_requires_posts_successfully(client,user_setup,mocker):
    
    user = user_setup
    mocker.patch(
        'django.contrib.auth.mixins.PermissionRequiredMixin.has_permission',
         return_value=True)

    url = reverse('model_information:create_check')  
    client.force_login(user)

    #test html post
    form = {
        'testname': 'test_test',
        'test_description': 'testdescripton',
        'modelid': Tblmodel.objects.last().modelid
    }
    response = client.post(url,data=form)

    created_test = Tblcheckslists.objects.last()
    assert response.status_code == 302
    assert 'test_test' in created_test.testname
    assert response.url == reverse('model_information:checklist')


    #test htmx post
    form = {
        'testname': 'test_test2',
        'test_description': 'testdescripton',
        'modelid': Tblmodel.objects.last().modelid
    }
    response = client.post(url,data=form,HTTP_HX_REQUEST='true' )
    
    created_test = Tblcheckslists.objects.last()
    assert response.status_code == 204
    assert 'test_test2' in created_test.testname
    
    
@pytest.mark.django_db
def test_exitint_model_list_view_requires_login(client):
    url = reverse('model_information:existing_modellist')  # Update to your actual URL name
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert '/login' in response.url.lower()  # Ensure it's going to the login page  

@pytest.mark.django_db
def test_exitint_model_list_view_requires_permission(client, user_setup):
    user = user_setup
    client.force_login(user)

    url = reverse('model_information:existing_modellist')
    response = client.get(url)
    assert response.status_code == 403

@pytest.mark.django_db
def test_exitint_model_list_view_renders(client, user_setup, mocker):
    user = user_setup
    client.force_login(user)
    mocker.patch(
        'django.contrib.auth.mixins.PermissionRequiredMixin.has_permission',
         return_value=True)

    url = reverse('model_information:existing_modellist')
    query_params = urlencode({'modelname': 'sam 12'})
    response = client.get(f"{url}?{query_params}")

    #test html
    assert response.status_code == 200
    assertTemplateUsed(response, 'model_information/partials/existing_model_list.html')