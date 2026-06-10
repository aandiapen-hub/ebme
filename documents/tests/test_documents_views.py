import os
from django.contrib.auth.models import Permission
from urllib.parse import urlencode

from django.db.models import query
from documents.tests.conftest import document
import pytest
from pytest_django.asserts import assertTemplateUsed
from django.urls import reverse

from documents.models import (
    DocumentsView,
    TblDocumentLinks,
    TblDocuments,
    TemporaryUpload,
)
from django.core.files.uploadedfile import SimpleUploadedFile

from django.core.files import File

# test DocumentCreateView


@pytest.mark.django_db
def test_document_create_view_requires_login(client):
    url = reverse("documents:create_document_link")
    response = client.get(url)
    assert response.status_code == 302
    assert "/login" in response.url.lower()


@pytest.mark.django_db
def test_document_create_view_requires_permission(client, user_setup):
    user = user_setup
    client.force_login(user)
    url = reverse("documents:create_document_link")
    response = client.get(url)
    assert response.status_code == 403


#
@pytest.mark.django_db
def test_document_create_view_renders(client, user_setup, asset):
    user = user_setup
    asset=asset
    content_type = asset._meta.label
    permission = Permission.objects.get(codename="add_tbldocuments")
    user.user_permissions.add(permission)
    client.force_login(user)

    base_url = reverse("documents:create_document_link")
    query_params = urlencode({"object_id": asset.pk, "content_type": content_type})
    url = f"{base_url}?{query_params}"
    response = client.get(url)

    assert response.status_code == 200


@pytest.mark.django_db
def test_document_create_view_post_successfully(client, user_setup, asset, document_type):
    user = user_setup
    permission = Permission.objects.get(codename="add_tbldocuments")
    user.user_permissions.add(permission)
    client.force_login(user)

    content_type = asset._meta.label

    base_url = reverse("documents:create_document_link")
    query_params = urlencode({"object_id": asset.pk, "content_type": content_type})
    url = f"{base_url}?{query_params}"

    # test html
    test_file = SimpleUploadedFile(
        "test.txt", b"Test content", content_type="text/plain"
    )
    form = {
        "document_type_id": document_type(),
        "document_name": "test_document",
        "document_description": "test_document_description",
        "document_bytea": test_file,
    }

    response = client.post(url, data=form)
    assert response.status_code == 302
    assert TblDocumentLinks.objects.last().documentid.document_name == "test_document"

    # test htmx
    test_file2 = SimpleUploadedFile(
        "test.txt", b"Test content2 ", content_type="text/plain"
    )

    form2 = {
        "document_type_id": document_type(),
        "document_name": "test_document2",
        "document_description": "test_document_description",
        "document_bytea": test_file2,
    }

    response = client.post(url, data=form2, HTTP_HX_REQUEST="true")
    assert response.status_code == 204
    assert TblDocumentLinks.objects.last().documentid.document_name == "test_document2"


@pytest.mark.django_db
def test_document_create_view_post_duplicated_document(client, user_setup, asset, document_type):
    user = user_setup
    permission = Permission.objects.get(codename="add_tbldocuments")
    user.user_permissions.add(permission)
    client.force_login(user)

    asset=asset
    content_type = asset._meta.label

    base_url = reverse("documents:create_document_link")
    query_params = urlencode({"object_id": asset.pk, "content_type": content_type})
    url = f"{base_url}?{query_params}"

    # test html
    test_file = SimpleUploadedFile(
        "test.txt", b"Test content", content_type="text/plain"
    )
    form = {
        "document_type_id": document_type(),
        "document_name": "test_document",
        "document_description": "test_document_description",
        "document_bytea": test_file,
    }
    response = client.post(url, data=form)
    link1_document = TblDocumentLinks.objects.last().documentid


    form2 = {
        "document_type_id": document_type(),
        "document_name": "test_document2",
        "document_description": "test_document_description",
        "document_bytea": test_file,
    }

    response = client.post(url, data=form2)

    link2_document = TblDocumentLinks.objects.last().documentid

    assert link1_document == link2_document

# test DocumentDeleteView
@pytest.mark.django_db
def test_document_delete_view_requires_login(client, document_link):
    document_link = document_link() 
    document_link_id = document_link.pk
    url = reverse("documents:delete_document_link", kwargs={"pk": document_link_id})

    response = client.get(url)
    assert response.status_code == 302
    assert "/login" in response.url.lower()


@pytest.mark.django_db
def test_document_delete_view_requires_permission(client, user_setup, document_link):
    user = user_setup
    client.force_login(user)

    document_link = document_link() 
    document_link_id = document_link.pk
    url = reverse("documents:delete_document_link", kwargs={"pk": document_link_id})

    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_document_delete_view_renders(client, user_setup, document_link, customer):
    document_link = document_link() 
    document_link_id = document_link.pk
    url = reverse("documents:delete_document_link", kwargs={"pk": document_link_id})
    customer = customer()

    document_link.customer_id = customer.pk
    document_link.save()

    user = user_setup
    permission = Permission.objects.get(codename="delete_tbldocumentlinks")
    user.user_permissions.add(permission)
    user.customerid = customer
    user.save()

    client.force_login(user)

    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, "documents/partials/document_link_delete_view.html")


@pytest.mark.django_db
def test_document_delete_view_post_successfully(client, user_setup, document_link, customer):

    document_link = document_link() 
    document_link_id = document_link.pk
    url = reverse("documents:delete_document_link", kwargs={"pk": document_link_id})
    customer = customer()

    document_link.customer_id = customer.pk
    document_link.save()

    user = user_setup
    permission = Permission.objects.get(codename="delete_tbldocumentlinks")
    user.user_permissions.add(permission)
    user.customerid = customer
    user.save()
    client.force_login(user)

    response = client.post(url)
    assert response.status_code == 302
    assert not TblDocumentLinks.objects.filter(document_link_id=document_link_id).exists()

@pytest.mark.django_db
def test_document_delete_view_post_successfully_htmx(client, user_setup, document_link, customer):
    document_link = document_link() 
    document_link_id = document_link.pk
    url = reverse("documents:delete_document_link", kwargs={"pk": document_link_id})
    customer = customer()

    document_link.customer_id = customer.pk
    document_link.save()

    user = user_setup
    permission = Permission.objects.get(codename="delete_tbldocumentlinks")
    user.user_permissions.add(permission)
    user.customerid = customer
    user.save()
    client.force_login(user)

    response = client.post(url, HTTP_HX_REQUEST="true")
    assert response.status_code == 204
    assert not TblDocuments.objects.filter(document_id=document_link_id).exists()


# test DocumentLinkUpdateView
@pytest.mark.django_db
def test_document_link_update_view_requires_login(client, document_link):
    document_link = document_link() 
    document_link_id = document_link.pk
    url = reverse("documents:update_document_link", kwargs={"pk": document_link_id})

    response = client.get(url)
    assert response.status_code == 302
    assert "/login" in response.url.lower()


@pytest.mark.django_db
def test_document_link_update_view_requires_permission(client, user_setup, document_link):
    user = user_setup
    client.force_login(user)

    document_link = document_link() 
    document_link_id = document_link.pk
    url = reverse("documents:update_document_link", kwargs={"pk": document_link_id})

    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_document_link_update_view_renders(client, user_setup, document_link, customer):
    document_link = document_link() 
    document_link_id = document_link.pk
    customer = customer()

    document_link.customer_id = customer.pk
    document_link.save()

    user = user_setup
    permission = Permission.objects.get(codename="change_tbldocumentlinks")
    user.user_permissions.add(permission)
    user.customerid = customer
    user.save()
    client.force_login(user)


    client.force_login(user)

    url = reverse("documents:update_document_link", kwargs={"pk": document_link_id})
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, "documents/partials/document_crud_modal.html")


@pytest.mark.django_db
def test_document_link_update_view_post_successfully(client, user_setup, document_link, customer):
    document_link = document_link() 
    document_link_id = document_link.pk
    customera = customer(customer_name='a')

    document_link.customer_id = customera.pk
    document_link.save()

    user = user_setup
    permission = Permission.objects.get(codename="change_tbldocumentlinks")
    user.user_permissions.add(permission)
    user.customerid = customera
    user.save()
    client.force_login(user)


    client.force_login(user)

    url = reverse("documents:update_document_link", kwargs={"pk": document_link_id})

    customer2 = customer(customer_name='b')
    form = {
        "customer": customer2.pk,
        "documentid": document_link.documentid.pk,
        "object_id": document_link.object_id,
        "content_type": document_link.content_type.pk,
    }

    response = client.post(url, data=form)
    assert response.status_code == 302
    document_link.refresh_from_db()
    assert document_link.customer_id == customer2.pk


@pytest.mark.django_db
def test_document_link_update_view_post_successfully_htmx(client, user_setup, document_link, customer):
    document_link = document_link() 
    document_link_id = document_link.pk
    customera = customer(customer_name='a')

    document_link.customer_id = customera.pk
    document_link.save()

    user = user_setup
    permission = Permission.objects.get(codename="change_tbldocumentlinks")
    user.user_permissions.add(permission)
    user.customerid = customera
    user.save()
    client.force_login(user)


    client.force_login(user)

    url = reverse("documents:update_document_link", kwargs={"pk": document_link_id})

    customer2 = customer(customer_name='b')
    form = {
        "customer": customer2.pk,
        "documentid": document_link.documentid.pk,
        "object_id": document_link.object_id,
        "content_type": document_link.content_type.pk,
    }
    response = client.post(url, data=form, HTTP_HX_REQUEST="true")
    assert response.status_code == 204
    document_link.refresh_from_db()
    assert document_link.customer_id == customer2.pk



# test FilteredDocumentTableView
@pytest.mark.django_db
def test_document_link_table_view_requires_login(client):
    url = reverse("documents:table_document_links")
    response = client.get(url)
    assert response.status_code == 302
    assert "/login" in response.url.lower()


@pytest.mark.django_db
def test_document_link_table_view_requires_permission(client, user_setup):
    user = user_setup
    client.force_login(user)
    url = reverse("documents:table_document_links")
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_document_link_table_view_renders(client, user_setup, customer):
    customer = customer()
    url = reverse("documents:table_document_links")

    user = user_setup
    permission = Permission.objects.get(codename="view_tbldocumentlinks")
    user.user_permissions.add(permission)
    user.customerid = customer
    user.save()

    client.force_login(user)

    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, "documents/documents_links.html")


# test DocumentDownloadView
@pytest.mark.django_db
def test_download_document_view_requires_login(client, document_link):
    documentid = document_link().pk
    url = reverse("documents:download_document", kwargs={"pk": documentid})
    response = client.get(url)
    assert response.status_code == 302
    assert "/login" in response.url.lower()


@pytest.mark.django_db
def test_download_document_view_requires_permission(client, document_link, user_setup):
    documentid = document_link().pk 
    url = reverse("documents:download_document", kwargs={"pk": documentid})

    user = user_setup
    client.force_login(user)

    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_download_document_view_renders(client, user_setup, document_link, customer):
    document_link = document_link()
    customer1 = customer()
    document_link.customerid = customer1
    document_link.save()

    user = user_setup
    user.customerid = customer1
    permission = Permission.objects.get(codename="view_tbldocuments")
    user.user_permissions.add(permission)
    user.save()
    client.force_login(user)

    url = reverse("documents:download_document", kwargs={"pk": document_link.documentid.pk})
    response = client.get(url)
    assert response.status_code == 200


# test DocumentListView
@pytest.mark.django_db
def test_document_list_view_requires_login(client):
    url = reverse("documents:list_documents")
    response = client.get(url)
    assert response.status_code == 302
    assert "/login" in response.url.lower()


@pytest.mark.django_db
def test_document_list_view_requires_permission(client, user_setup):
    url = reverse("documents:list_documents")

    user = user_setup
    client.force_login(user)

    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_document_list_view_renders(client,asset, user_setup, obj_document_link, customer):
    asset = asset
    document_link = obj_document_link(obj=asset)
    customer1 = customer()
    document_link.customerid = customer1
    document_link.save()

    user = user_setup
    user.customerid = customer1
    permission = Permission.objects.get(codename="view_tbldocumentlinks")
    user.user_permissions.add(permission)
    user.save()
    client.force_login(user)
    url = reverse("documents:list_documents")

    query_param = urlencode(
        {
            "object_id": document_link.object_id,
            "content_type": asset._meta.label
        }
    )

    client.force_login(user)

    response = client.get(f"{url}?{query_param}")
    assert response.status_code == 200
    assertTemplateUsed(response="documents/partials/document_list.html")


# test DocumentLinkDeleteView
@pytest.mark.django_db
def test_document_link_delete_view_requires_login(client, document_link):
    link = document_link()
    url = reverse("documents:delete_document_link", kwargs={"pk": link.pk})
    response = client.get(url)
    assert response.status_code == 302
    assert "/login" in response.url.lower()


@pytest.mark.django_db
def test_document_link_delete_view_requires_permission(client, user_setup, document_link):
    link = document_link()
    url = reverse("documents:delete_document_link", kwargs={"pk": link.pk})
    user = user_setup
    client.force_login(user)

    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_document_link_delete_view_renders(client, user_setup, document_link, customer):
    link = document_link()
    customer = customer()
    link.customer_id = customer
    link.save()

    url = reverse("documents:delete_document_link", kwargs={"pk": link.pk})

    user = user_setup
    permission = Permission.objects.get(codename="delete_tbldocumentlinks")
    user.user_permissions.add(permission)
    user.customerid = customer
    user.save()

    client.force_login(user)

    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response="documents/partials/document_list.html")


@pytest.mark.django_db
def test_document_link_delete_post_successful(client, user_setup, document_link, customer):
    link = document_link()
    customer = customer()
    link.customer_id = customer
    link.save()

    url = reverse("documents:delete_document_link", kwargs={"pk": link.pk})

    user = user_setup
    permission = Permission.objects.get(codename="delete_tbldocumentlinks")
    user.user_permissions.add(permission)
    user.customerid = customer
    user.save()

    client.force_login(user)

    response = client.post(url)
    assert response.status_code == 302

    with pytest.raises(Exception):
        link.refresh_from_db()


# test DocumentPreView
@pytest.mark.django_db
def test_document_pre_view_requires_login(client, temp_document):
    test_doc = temp_document('equipment_gs1.jpg')

    url = reverse("documents:load_image", kwargs={'pk':test_doc.pk})
    response = client.get(url)
    assert response.status_code == 302
    assert "/login" in response.url.lower()


def test_document_pre_view_requires_permission(client, user_setup, temp_document):
    test_doc = temp_document('equipment_gs1.jpg')
    user = user_setup
    client.force_login(user)

    url = reverse("documents:load_image", kwargs={'pk':test_doc.pk})
    response = client.get(url)
    assert response.status_code == 403

@pytest.mark.django_db
def test_document_pre_view_renders_pdf(client, user_setup, temp_document):
    test_doc = temp_document('service_report.pdf')
    user = user_setup
    client.force_login(user)

    permission = Permission.objects.get(codename="view_temporaryupload")
    user.user_permissions.add(permission)
    user.save() 

    url = reverse("documents:load_image", kwargs={'pk':test_doc.pk})
    response = client.get(url)
    assert response["Content-Type"] == "image/png"  # or expected mime type
    assert isinstance(response, type(response))  # FileResponse


@pytest.mark.django_db
def test_document_pre_view_renders_image(client, user_setup, temp_document):

    test_doc = temp_document('equipment_gs1.jpg')
    user = user_setup
    client.force_login(user)

    permission = Permission.objects.get(codename="view_temporaryupload")
    user.user_permissions.add(permission)
    user.save() 

    url = reverse("documents:load_image", kwargs={'pk':test_doc.pk})

    response = client.get(url)
    assert response["Content-Type"] == "image/jpeg"  # or expected mime type
    assert isinstance(response, type(response))  # FileResponse


# test TempFilesDeleteAllView
@pytest.mark.django_db
def test_temp_files_delete_all_view_requires_login(client):
    url = reverse("documents:delete_all_temp_files")
    response = client.get(url)
    assert response.status_code == 302
    assert "/login" in response.url.lower()


@pytest.mark.django_db
def test_temp_files_delete_all_view_posts_requires_permission(client, user, temp_document, temp_group):
    user1 = user(user_name='userA')

    client.force_login(user1)

    group1 = temp_group(user=user1)
    group2 = temp_group(user=user1)
    user1_file1 = temp_document(group=group1)
    user1_file2 = temp_document(group=group1)
    user1_file3 = temp_document(group=group2)
    user1_file4 = temp_document(group=group2)

    assert TemporaryUpload.objects.filter(group__user=user1).exists() 
    assert user1.temp_upload_group.all().exists()

    url = reverse("documents:delete_all_temp_files")
    response = client.post(url)
    assert response.status_code == 403

@pytest.mark.django_db
def test_temp_files_delete_all_view_posts_successfully(client, user, temp_document, temp_group):
    user1 = user(user_name='userA')
    user2 = user(user_name='userB')
    permission = Permission.objects.get(codename="delete_temporaryupload")
    user1.user_permissions.add(permission)
    user1.save() 

    client.force_login(user1)

    group1 = temp_group(user=user1)
    group2 = temp_group(user=user1)
    group3 = temp_group(user=user2)
    group4 = temp_group(user=user2)
    user1_file1 = temp_document(group=group1)
    user1_file2 = temp_document(group=group1)
    user1_file3 = temp_document(group=group2)
    user1_file4 = temp_document(group=group2)

    user2_file1 = temp_document(group=group3)
    user2_file2 = temp_document(group=group3)
    user2_file3 = temp_document(group=group4)
    user2_file4 = temp_document(group=group4)

    assert TemporaryUpload.objects.filter(group__user=user1).exists() 
    assert user1.temp_upload_group.all().exists()

    url = reverse("documents:delete_all_temp_files")
    response = client.post(url)
    assert response.status_code == 302
    assert not TemporaryUpload.objects.filter(group__user=user1).exists() 
    assert not user1.temp_upload_group.all().exists()

    # check that other users' files still exisits
    assert TemporaryUpload.objects.filter(group__user=user2).exists() 
    assert user2.temp_upload_group.all().exists()

# Test TempFilesDeleteView
@pytest.mark.django_db
def test_temp_file_delete_view_requires_login(temp_document, client):
    temp_document = temp_document()

    url = reverse("documents:delete_temp_file", kwargs={"pk": temp_document.pk})
    response = client.get(url)
    assert response.status_code == 302
    assert "/login" in response.url.lower()

@pytest.mark.django_db
def test_temp_file_delete_view_requires_permission(client, temp_document):
    temp_document = temp_document()
    user1 = temp_document.group.user
    user1.save() 

    client.force_login(user1)

    url = reverse("documents:delete_temp_file", kwargs={"pk": temp_document.pk})
    response = client.post(url)
    assert response.status_code == 403 

@pytest.mark.django_db
def test_temp_file_delete_view_posts(client, temp_document):
    temp_document = temp_document()
    user1 = temp_document.group.user

    permission = Permission.objects.get(codename="delete_temporaryupload")
    user1.user_permissions.add(permission)
    user1.save() 

    client.force_login(user1)

    url = reverse("documents:delete_temp_file", kwargs={"pk": temp_document.pk})
    response = client.post(url)
    assert response.status_code == 302
    assert not TemporaryUpload.objects.filter(pk=temp_document.pk).exists()


@pytest.mark.django_db
def test_temp_file_delete_view_posts_htmx(client, temp_document):
    temp_document = temp_document()
    user1 = temp_document.group.user

    permission = Permission.objects.get(codename="delete_temporaryupload")
    user1.user_permissions.add(permission)
    user1.save() 

    client.force_login(user1)


    url = reverse("documents:delete_temp_file", kwargs={"pk": temp_document.pk})
    response = client.post(url, HTTP_HX_REQUEST="true")
    assert response.status_code == 200
    assert not TemporaryUpload.objects.filter(pk=temp_document.pk).exists()


# test TemporaryUploadCreateView
# Test TempFilesDeleteView
@pytest.mark.django_db
def test_temporary_upload_create_view_requires_login(user_setup, client):
    url = reverse("documents:create_temp_file")
    response = client.get(url)
    assert response.status_code == 302
    assert "/login" in response.url.lower()


@pytest.mark.django_db
def test_temporary_upload_create_view_requires_permission(client, user):
    user = user()
    client.force_login(user)

    url = reverse("documents:create_temp_file")
    response = client.get(url, HTTP_HX_REQUEST="true")
    assert response.status_code == 403


@pytest.mark.django_db
def test_temporary_upload_create_view_renders(client, user):
    user = user()
    client.force_login(user)

    permission = Permission.objects.get(codename="add_temporaryupload")
    user.user_permissions.add(permission)
    user.save() 

    url = reverse("documents:create_temp_file")
    response = client.get(url, HTTP_HX_REQUEST="true")
    assert response.status_code == 200
    assertTemplateUsed(response, "documents/partials/temp_upload_create.html")



@pytest.mark.django_db
def test_temporary_upload_create_view_post_specific_group(client, test_file, temp_document, user):

    temp_document = temp_document()
    user1 = temp_document.group.user

    permission = Permission.objects.get(codename="add_temporaryupload")
    user1.user_permissions.add(permission)
    user1.is_staff = True
    user1.save() 

    client.force_login(user1)

    test_file = test_file('delivery_note.jpeg')
    data = {"files": [test_file]}

    base_url = reverse("documents:create_temp_file")
    query_params = urlencode({'group': temp_document.group.pk})
    url = f"{base_url}?{query_params}"
    response = client.post(url, data, format="multipart")
    assert response.status_code == 302
    assert TemporaryUpload.objects.filter(group=temp_document.group).exists()

@pytest.mark.django_db
def test_temporary_upload_create_view_post_non_staff(client, test_file, temp_document, user):

    temp_document = temp_document()
    user1 = temp_document.group.user

    permission = Permission.objects.get(codename="add_temporaryupload")
    user1.user_permissions.add(permission)
    user1.save() 

    client.force_login(user1)

    test_file = test_file('delivery_note.jpeg')
    data = {"files": [test_file]}

    base_url = reverse("documents:create_temp_file")
    query_params = urlencode({'group': temp_document.group.pk})
    url = f"{base_url}?{query_params}"
    response = client.post(url, data, format="multipart")
    assert response.status_code == 302
    assert not TemporaryUpload.objects.filter(group=temp_document.group).exists()
    assert TemporaryUpload.objects.all().count() == 1

@pytest.mark.django_db
def test_temporary_upload_create_view_post_specific_group_htmx( client, temp_document, test_file):
    temp_document = temp_document()
    user1 = temp_document.group.user

    permission = Permission.objects.get(codename="add_temporaryupload")
    user1.user_permissions.add(permission)
    user1.is_staff = True
    user1.save() 

    client.force_login(user1)

    test_file = test_file('delivery_note.jpeg')
    data = {"files": [test_file]}

    base_url = reverse("documents:create_temp_file")
    query_params = urlencode({'group': temp_document.group.pk})
    url = f"{base_url}?{query_params}"
    response = client.post(url, data, format="multipart", HTTP_HX_REQUEST='true')
    assert response.status_code == 200
    assertTemplateUsed(response, "documents/partials/temp_file.html")
    assert TemporaryUpload.objects.filter(group=temp_document.group).exists()


# test TempUploadListView
@pytest.mark.django_db
def test_temp_file_list_view_requires_login(client):
    url = reverse("documents:user_temp_files")
    response = client.get(url)
    assert response.status_code == 302
    assert "/login" in response.url.lower()


# test TempUploadListView
@pytest.mark.django_db
def test_temp_file_list_view_requires_permission(client, temp_document):
    
    temp_document = temp_document()
    user1 = temp_document.group.user

    user1.save() 

    client.force_login(user1)

    url = reverse("documents:user_temp_files")
    response = client.get(url)
    assert response.status_code == 403

@pytest.mark.django_db
def test_temp_file_list_view_renders(client, user, temp_document, temp_group):
    user1 = user(user_name='userA')
    permission = Permission.objects.get(codename="view_temporaryupload")
    user1.user_permissions.add(permission)
    user1.save() 

    client.force_login(user1)

    group1 = temp_group(user=user1)
    group2 = temp_group(user=user1)
    user1_file1 = temp_document(group=group1)
    user1_file2 = temp_document(group=group1)
    user1_file3 = temp_document(group=group2)
    user1_file4 = temp_document(group=group2)

    query_params = urlencode({"group": group1, "success_url": "testurl"})
    base_url = reverse("documents:user_temp_files")
    url = f"{base_url}?{query_params}"
    response = client.get(url)
    assert response.status_code == 200
    assert 'testurl' in response.context['success_url']
    assertTemplateUsed(response, "documents/temp_group_list.html")


# test DocumentUpdateView
@pytest.mark.django_db
def test_document_update_view_requires_login(client, document):
    document = document()
    url = reverse("documents:update_document", kwargs={"pk": document.pk})

    response = client.get(url)
    assert response.status_code == 302
    assert "/login" in response.url.lower()


@pytest.mark.django_db
def test_document_update_view_requires_permission(client, document, user):
    document = document()
    user = user()
    client.force_login(user)

    url = reverse("documents:update_document", kwargs={"pk": document.pk})

    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_document_update_view_renders(client, user, document):
    document = document()
    user = user()

    permission = Permission.objects.get(codename="change_tbldocuments")

    user.user_permissions.add(permission)
    user.save()
    url = reverse("documents:update_document", kwargs={"pk": document.pk})

    client.force_login(user)

    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, "documents/document_update.html")


@pytest.mark.django_db
def test_document_update_view_post(client, user, document_link, customer):
    document_link = document_link()
    last_document = document_link.documentid
    user = user()

    permission = Permission.objects.get(codename="change_tbldocuments")
    user.user_permissions.add(permission)

    customer = customer()
    document_link.customerid = customer.pk
    user.customerid = customer
    user.save()
    client.force_login(user)

    url = reverse("documents:update_document", kwargs={"pk": document_link.documentid.pk})


    test_file = SimpleUploadedFile(
        "test.txt", b"Test content", content_type="text/plain"
    )
    form = {
        "document_name": "test_document",
        "document_description": "test_document_description",
        "document_bytea": test_file,
    }

    response = client.post(url, data=form, format="multipart")

    assert response.status_code == 302
    last_document.refresh_from_db()
    assert last_document.document_name == "test_document"

