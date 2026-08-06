from assets.models import Tblassets
from django.contrib.auth.models import Permission
from urllib.parse import urlencode
import pytest
from pytest_django.asserts import assertTemplateUsed
from django.urls import reverse

from documents.models import (
    TblDocumentLinks,
    TblDocuments,
    TemporaryUpload,
    DocumentTypes,
)
from django.core.files.uploadedfile import SimpleUploadedFile


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
    asset = asset()
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
def test_document_create_view_post_successfully(
    client, user_setup, asset, document_type
):
    user = user_setup
    permission = Permission.objects.get(codename="add_tbldocuments")
    user.user_permissions.add(permission)
    client.force_login(user)

    asset = asset()
    content_type = asset._meta.label

    base_url = reverse("documents:create_document_link")
    query_params = urlencode({"object_id": asset.pk, "content_type": content_type})
    url = f"{base_url}?{query_params}"

    doc_type = document_type()
    # test html
    test_file = SimpleUploadedFile(
        "test.txt", b"Test content", content_type="text/plain"
    )
    form = {
        "document_type_id": doc_type,
        "document_name": "test_document",
        "document_description": "test_document_description",
        "document_bytea": test_file,
    }

    response = client.post(url, data=form)
    assert response.status_code == 302
    assert TblDocumentLinks.objects.last().documentid.document_name == "test_document"

    # test htmx
    test_file2 = SimpleUploadedFile(
        "test.txt", b"Test contesdfdskfjknt2 ", content_type="text/plain"
    )

    form2 = {
        "document_type_id": doc_type,
        "document_name": "test_document2",
        "document_description": "test_document_description",
        "document_bytea": test_file2,
    }

    response = client.post(url, data=form2, HTTP_HX_REQUEST="true")
    assert response.status_code == 204
    assert TblDocumentLinks.objects.last().documentid.document_name == "test_document2"


@pytest.mark.django_db
def test_document_create_view_post_duplicated_document(
    client, user_setup, asset, document_type
):
    user = user_setup
    permission = Permission.objects.get(codename="add_tbldocuments")
    user.user_permissions.add(permission)
    client.force_login(user)

    asset = asset()
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
def test_document_delete_view_post_successfully(
    client, user_setup, document_link, customer
):

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
    assert not TblDocumentLinks.objects.filter(
        document_link_id=document_link_id
    ).exists()


@pytest.mark.django_db
def test_document_delete_view_post_successfully_htmx(
    client, user_setup, document_link, customer
):
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
def test_document_link_update_view_requires_permission(
    client, user_setup, document_link
):
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
def test_document_link_update_view_post_successfully(
    client, user_setup, document_link, customer
):
    document_link = document_link()
    document_link_id = document_link.pk
    customera = customer(customer_name="a")

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

    customer2 = customer(customer_name="b")
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
def test_document_link_update_view_post_successfully_htmx(
    client, user_setup, document_link, customer
):
    document_link = document_link()
    document_link_id = document_link.pk
    customera = customer(customer_name="a")

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

    customer2 = customer(customer_name="b")
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


@pytest.mark.django_db
def test_document_link_table_view_non_staff_no_customer(client, document_link, user):
    url = reverse("documents:table_document_links")
    document_link.create_batch(size=20)
    user = user()
    user.is_staff = True
    permission = Permission.objects.get(codename="view_tbldocumentlinks")
    user.user_permissions.add(permission)
    user.save()

    client.force_login(user)

    response = client.get(url)
    assert response.context["table"].data.data.count() == 20


@pytest.mark.django_db
def test_document_link_table_view_non_staff_no_customer(
    client, document_link, user_setup, customer
):
    customer = customer()
    url = reverse("documents:table_document_links")
    document_link.create_batch(size=20)
    user = user_setup
    permission = Permission.objects.get(codename="view_tbldocumentlinks")
    user.user_permissions.add(permission)
    user.customerid = None
    user.save()

    client.force_login(user)

    response = client.get(url)
    assert response.context["table"].data.data.count() == 0


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

    url = reverse(
        "documents:download_document", kwargs={"pk": document_link.documentid.pk}
    )
    response = client.get(url)
    assert response.status_code == 200


# test DocumentDownloadView
@pytest.mark.django_db
def test_download_document_from_link_view_requires_login(client, document_link):
    documentid = document_link().pk
    url = reverse("documents:download_document_from_link", kwargs={"pk": documentid})
    response = client.get(url)
    assert response.status_code == 302
    assert "/login" in response.url.lower()


@pytest.mark.django_db
def test_download_document_from_link_view_requires_permission(
    client, document_link, user_setup
):
    documentid = document_link().pk
    url = reverse("documents:download_document_from_link", kwargs={"pk": documentid})

    user = user_setup
    client.force_login(user)

    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_download_document_from_link_view_renders(
    client, user_setup, document_link, customer
):
    document_link = document_link()
    customer1 = customer()
    document_link.customer = customer1
    document_link.save()

    user = user_setup
    user.customerid = customer1
    permission = Permission.objects.get(codename="view_tbldocumentlinks")
    user.user_permissions.add(permission)
    user.save()
    client.force_login(user)

    url = reverse(
        "documents:download_document_from_link", kwargs={"pk": document_link.pk}
    )
    response = client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_download_document_from_link_view_non_staff_no_customer(
    client, user_setup, document_link, customer
):
    document_link = document_link()
    customer1 = customer()
    document_link.customer = customer1
    document_link.save()

    user = user_setup
    user.customerid = None
    permission = Permission.objects.get(codename="view_tbldocumentlinks")
    user.user_permissions.add(permission)
    user.save()
    client.force_login(user)

    url = reverse(
        "documents:download_document_from_link", kwargs={"pk": document_link.pk}
    )
    response = client.get(url)
    assert response.status_code == 404


@pytest.mark.django_db
def test_download_document_from_link_view_staff(client, user, document_link):
    document_link = document_link()
    user = user()
    user.is_staff = True
    permission = Permission.objects.get(codename="view_tbldocumentlinks")
    user.user_permissions.add(permission)
    user.save()
    client.force_login(user)

    url = reverse(
        "documents:download_document_from_link", kwargs={"pk": document_link.pk}
    )
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
def test_document_list_view_renders(
    client, asset, user_setup, obj_document_link, customer
):
    asset = asset()
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
        {"object_id": document_link.object_id, "content_type": asset._meta.label}
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
def test_document_link_delete_view_requires_permission(
    client, user_setup, document_link
):
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
def test_document_link_delete_post_successful(
    client, user_setup, document_link, customer
):
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
    test_doc = temp_document("equipment_gs1.jpg")

    url = reverse("documents:load_image", kwargs={"pk": test_doc.pk})
    response = client.get(url)
    assert response.status_code == 302
    assert "/login" in response.url.lower()


def test_document_pre_view_requires_permission(client, user_setup, temp_document):
    test_doc = temp_document("equipment_gs1.jpg")
    user = user_setup
    client.force_login(user)

    url = reverse("documents:load_image", kwargs={"pk": test_doc.pk})
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_document_pre_view_renders_pdf(client, user_setup, temp_document):
    test_doc = temp_document("service_report.pdf")
    user = user_setup
    client.force_login(user)

    permission = Permission.objects.get(codename="view_temporaryupload")
    user.user_permissions.add(permission)
    user.save()

    url = reverse("documents:load_image", kwargs={"pk": test_doc.pk})
    response = client.get(url)
    assert response["Content-Type"] == "image/png"  # or expected mime type
    assert isinstance(response, type(response))  # FileResponse


@pytest.mark.django_db
def test_document_pre_view_renders_barcode_data(client, user_setup, temp_barcode_only):
    test_doc = temp_barcode_only()
    user = user_setup
    client.force_login(user)

    permission = Permission.objects.get(codename="view_temporaryupload")
    user.user_permissions.add(permission)
    user.save()

    url = reverse("documents:load_image", kwargs={"pk": test_doc.pk})
    response = client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_document_pre_view_renders_image(client, user_setup, temp_document):

    test_doc = temp_document("equipment_gs1.jpg")
    user = user_setup
    client.force_login(user)

    permission = Permission.objects.get(codename="view_temporaryupload")
    user.user_permissions.add(permission)
    user.save()

    url = reverse("documents:load_image", kwargs={"pk": test_doc.pk})

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
def test_temp_files_delete_all_view_posts_requires_permission(
    client, user, temp_document, temp_group
):
    user1 = user(user_name="userA")

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
def test_temp_files_delete_all_view_posts_successfully(
    client, user, temp_document, temp_group
):
    user1 = user(user_name="userA")
    user2 = user(user_name="userB")
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
def test_temporary_upload_create_view_post_new_group(
    client, test_file, temp_document, user
):

    user1 = user()
    permission = Permission.objects.get(codename="add_temporaryupload")
    user1.user_permissions.add(permission)
    user1.is_staff = True
    user1.save()

    client.force_login(user1)

    test_file = test_file("delivery_note.jpeg")
    data = {"files": [test_file]}

    url = reverse("documents:create_temp_file")
    response = client.post(url, data, format="multipart")
    assert response.status_code == 302
    assert TemporaryUpload.objects.filter(group__user=user1.pk).exists()


@pytest.mark.django_db
def test_temporary_upload_create_view_post_validation_error(
    client, test_file, temp_document, user
):
    temp_document = temp_document()
    user1 = temp_document.group.user

    permission = Permission.objects.get(codename="add_temporaryupload")
    user1.user_permissions.add(permission)
    user1.is_staff = True
    user1.save()

    client.force_login(user1)

    test_file = test_file("delivery_note.jpeg")
    data = {"scanned_code": "12323"}

    base_url = reverse("documents:create_temp_file")
    query_params = urlencode({"group": temp_document.group.pk})
    url = f"{base_url}?{query_params}"
    response = client.post(url, data, format="multipart")
    assert response.status_code == 200
    assert response["HX-Reswap"] and response["HX-Retarget"]


@pytest.mark.django_db
def test_temporary_upload_create_view_post_specific_group(
    client, test_file, temp_document, user
):

    temp_document = temp_document()
    user1 = temp_document.group.user

    permission = Permission.objects.get(codename="add_temporaryupload")
    user1.user_permissions.add(permission)
    user1.is_staff = True
    user1.save()

    client.force_login(user1)

    test_file = test_file("delivery_note.jpeg")
    data = {"files": [test_file]}

    base_url = reverse("documents:create_temp_file")
    query_params = urlencode({"group": temp_document.group.pk})
    url = f"{base_url}?{query_params}"
    response = client.post(url, data, format="multipart")
    assert response.status_code == 302
    assert TemporaryUpload.objects.filter(group=temp_document.group).exists()


@pytest.mark.django_db
def test_temporary_upload_create_view_post_htmx(client, test_file, temp_document, user):

    temp_document = temp_document()
    user1 = temp_document.group.user

    permission = Permission.objects.get(codename="add_temporaryupload")
    user1.user_permissions.add(permission)
    user1.is_staff = True
    user1.save()

    client.force_login(user1)

    test_file = test_file("delivery_note.jpeg")
    data = {"files": [test_file]}

    base_url = reverse("documents:create_temp_file")
    query_params = urlencode({"group": temp_document.group.pk})
    url = f"{base_url}?{query_params}"
    response = client.post(url, data, format="multipart", HTTP_HX_REQUEST="true")
    assert response.status_code == 200
    assertTemplateUsed(response, "documents/partials/temp_file.html")


@pytest.mark.django_db
def test_temporary_upload_create_view_post__new_group_htmx(
    client, test_file, temp_document, user
):

    temp_document = temp_document()
    user1 = temp_document.group.user

    permission = Permission.objects.get(codename="add_temporaryupload")
    user1.user_permissions.add(permission)
    user1.is_staff = True
    user1.save()

    client.force_login(user1)

    test_file = test_file("delivery_note.jpeg")
    data = {"files": [test_file]}

    url = reverse("documents:create_temp_file")
    response = client.post(url, data, format="multipart", HTTP_HX_REQUEST="true")
    assert response.status_code == 200
    assertTemplateUsed(response, "documents/partials/temp_file.html")


@pytest.mark.django_db
def test_temporary_upload_create_view_post_non_staff(
    client, test_file, temp_document, user
):

    temp_document = temp_document()
    user1 = temp_document.group.user

    permission = Permission.objects.get(codename="add_temporaryupload")
    user1.user_permissions.add(permission)
    user1.save()

    client.force_login(user1)

    test_file = test_file("delivery_note.jpeg")
    data = {"files": [test_file]}

    base_url = reverse("documents:create_temp_file")
    query_params = urlencode({"group": temp_document.group.pk})
    url = f"{base_url}?{query_params}"
    response = client.post(url, data, format="multipart")
    assert response.status_code == 302
    assert not TemporaryUpload.objects.filter(group=temp_document.group).exists()
    assert TemporaryUpload.objects.all().count() == 1


@pytest.mark.django_db
def test_temporary_upload_create_view_post_specific_group_htmx(
    client, temp_document, test_file
):
    temp_document = temp_document()
    user1 = temp_document.group.user

    permission = Permission.objects.get(codename="add_temporaryupload")
    user1.user_permissions.add(permission)
    user1.is_staff = True
    user1.save()

    client.force_login(user1)

    test_file = test_file("delivery_note.jpeg")
    data = {"files": [test_file]}

    base_url = reverse("documents:create_temp_file")
    query_params = urlencode({"group": temp_document.group.pk})
    url = f"{base_url}?{query_params}"
    response = client.post(url, data, format="multipart", HTTP_HX_REQUEST="true")
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
    user1 = user(user_name="userA")
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
    assert "testurl" in response.context["success_url"]
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

    url = reverse(
        "documents:update_document", kwargs={"pk": document_link.documentid.pk}
    )

    test_file = SimpleUploadedFile(
        "test.txt", b"Test content_XXX1232XX", content_type="text/plain"
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


@pytest.mark.django_db
def test_document_update_view_post_htmx(client, user, document_link, customer):
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

    url = reverse(
        "documents:update_document", kwargs={"pk": document_link.documentid.pk}
    )

    test_file = SimpleUploadedFile(
        "test.txt", b"Test content", content_type="text/plain"
    )
    form = {
        "document_name": "test_document",
        "document_description": "test_document_description",
        "document_bytea": test_file,
    }

    response = client.post(url, data=form, format="multipart", HTTP_HX_REQUEST="true")

    assert response.status_code == 204
    last_document.refresh_from_db()
    assert last_document.document_name == "test_document"


@pytest.mark.django_db
def test_document_update_view_post_invalid_form(
    client, test_file, user, document, customer
):
    document1 = document("equipment_gs1.jpg")
    user = user()

    permission = Permission.objects.get(codename="change_tbldocuments")
    user.user_permissions.add(permission)

    user.is_staff = True
    user.save()
    client.force_login(user)

    url = reverse("documents:update_document", kwargs={"pk": document1.pk})
    test_file = test_file("delivery_note.jpeg")

    form = {
        "document_description": "test_document_description",
        "document_bytea": test_file,
    }

    response = client.post(url, data=form, format="multipart")

    assert response.status_code == 200


# test DocumentUpdateView
@pytest.mark.django_db
def test_temporary_group_view_requires_login(client, temp_document):
    document = temp_document()
    url = reverse("documents:temp_group", kwargs={"pk": document.group.pk})

    response = client.get(url)
    assert response.status_code == 302
    assert "/login" in response.url.lower()


@pytest.mark.django_db
def test_temp_group_view_requires_permission(client, temp_document, user):
    document = temp_document()
    url = reverse("documents:temp_group", kwargs={"pk": document.group.pk})
    user = user()
    client.force_login(user)

    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_temp_group_view_renders(client, temp_group, temp_document, user):
    user = user()
    permission = Permission.objects.get(codename="view_tempuploadgroup")
    user.user_permissions.add(permission)

    group1 = temp_group(user=user)
    document = temp_document("equipment_gs1.jpg", group=group1)
    url = reverse("documents:temp_group", kwargs={"pk": document.group.pk})

    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 200
    assert response.context["group"] is not None


# test extract information from group
@pytest.mark.django_db
def test_temp_group_extract_text_requires_login(client, temp_document):
    document = temp_document()
    url = reverse("documents:extract_text", kwargs={"pk": document.group.pk})

    response = client.get(url)
    assert response.status_code == 302
    assert "/login" in response.url.lower()


@pytest.mark.django_db
def test_temp_group_extract_text_requires_permission(client, temp_document, user):
    document = temp_document()
    url = reverse("documents:extract_text", kwargs={"pk": document.group.pk})
    user = user()
    client.force_login(user)

    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_temp_group_extract_text_posts(client, temp_document, user):
    document = temp_document()
    url = reverse("documents:extract_text", kwargs={"pk": document.group.pk})
    user = user()
    permission = Permission.objects.get(codename="change_tempuploadgroup")
    user.user_permissions.add(permission)
    client.force_login(user)

    response = client.post(url)
    assert response.status_code == 200
    assert response["HX-Redirect"] == reverse(
        "documents:temp_group", kwargs={"pk": document.group.pk}
    )


MOCK_ASSET_DATA = {
    "GTIN": "00885403497233",
    "SERIAL": "S00455524",
    "ASSET_NO": "5533488",
    "PROD_DATE": "2304-04-23",
    "brand": None,
    "model": None,
    "category": None,
    "brand_name_options": ["NHS", "GE Healthcare", "Siemens Healthineers"],
    "model_name_options": ["Model 999-103DEN", "Model PRL001311"],
    "category_name_options": [
        "Infusion Pump",
        "Medical Device",
        "Healthcare Equipment",
    ],
    "model_description": None,
}


@pytest.mark.django_db
def test_group_extract_text_asset_data_non_staff(
    client,
    asset_id_temp_document,
    asset_no_temp_document,
    user,
    immediate_task_backend,
    asset,
    model,
    brand,
    mocker,
):

    document1 = asset_id_temp_document
    document2 = asset_no_temp_document
    group = document1.group
    document2.group = group
    document2.save()

    brand1 = brand(brandname="GE")
    brand2 = brand(brandname="Siemens")

    mocker.patch(
        "documents.services.process_document.extract_group_info_with_ai",
        return_value=MOCK_ASSET_DATA,
    )

    extract_url = reverse("documents:extract_text", kwargs={"pk": group.pk})
    user = user()
    group.user = user
    group.save()
    permission1 = Permission.objects.get(codename="change_tempuploadgroup")
    permission2 = Permission.objects.get(codename="view_tempuploadgroup")
    user.user_permissions.add(permission1)
    user.user_permissions.add(permission2)
    client.force_login(user)

    get_url = reverse("documents:temp_group", kwargs={"pk": group.pk})
    # no asset and not model
    client.post(extract_url)
    response = client.get(get_url)

    # asset no identified
    asset1 = asset(customerassetnumber="5533488")
    client.post(extract_url)
    asset1.delete()
    response = client.get(get_url)

    # asset partial matches
    asset3 = asset(serialnumber="S004555248943")
    asset4 = asset(serialnumber="S004555243489")
    asset5 = asset(serialnumber="S0045552438")
    client.post(extract_url)
    response = client.get(get_url)

    # asset id identified
    model = model(gtin="00885403497233")
    asset2 = asset(serialnumber="S00455524", modelid=model)
    client.post(extract_url)
    asset2.delete()
    response = client.get(get_url)


@pytest.mark.django_db
def test_group_extract_text_asset_data_staff(
    client,
    asset_id_temp_document,
    asset_no_temp_document,
    user,
    immediate_task_backend,
    asset,
    model,
    brand,
    mocker,
):

    document1 = asset_id_temp_document
    document2 = asset_no_temp_document
    group = document1.group
    document2.group = group
    document2.save()

    brand1 = brand(brandname="GE")
    brand2 = brand(brandname="Siemens")

    mocker.patch(
        "documents.services.process_document.extract_group_info_with_ai",
        return_value=MOCK_ASSET_DATA,
    )

    extract_url = reverse("documents:extract_text", kwargs={"pk": group.pk})
    user = user()
    user.is_staff = True
    user.save()
    group.user = user
    group.save()
    permission1 = Permission.objects.get(codename="change_tempuploadgroup")
    permission2 = Permission.objects.get(codename="view_tempuploadgroup")
    user.user_permissions.add(permission1)
    user.user_permissions.add(permission2)
    client.force_login(user)

    get_url = reverse("documents:temp_group", kwargs={"pk": group.pk})
    # no asset and not model
    client.post(extract_url)
    response = client.get(get_url)

    # asset no identified
    asset1 = asset(customerassetnumber="5533488")
    client.post(extract_url)
    asset1.delete()
    response = client.get(get_url)

    # asset partial matches
    asset3 = asset(serialnumber="S004555248943")
    asset4 = asset(serialnumber="S004555243489")
    asset5 = asset(serialnumber="S0045552438")

    client.post(extract_url)
    response = client.get(get_url)

    # asset id identified
    model1 = model(gtin="00885403497233")
    asset2 = asset(serialnumber="S00455524", modelid=model1)
    client.post(extract_url)
    response = client.get(get_url)
    asset2.delete()
    model1.delete()

    # duplicatable_models
    model2 = model(gtin="00885403494378")
    asset3 = asset(serialnumber="S00455524", modelid=model2)
    client.post(extract_url)
    response = client.get(get_url)
    asset3.delete()
    model2.delete()


MOCK_SERVICE_REPORT_DATA = {
    "GIAI": "50552395105533488",
    "GTIN": "00885403497233",
    "brand": None,
    "model": "4040 Flowmeter",
    "SERIAL": "S00455524",
    "job_ref": "300364863",
    "ASSET_NO": "5533488",
    "cal_date": "2021-08-18",
    "end_date": "2021-08-18",
    "workdone": """Calibration of Flowmeter 4040. Unit cleaned, calibrated, and complete operational checkout
        performed. As-Found and As-Left calibration with NIST/UKAS traceable calibration.""",
    "PROD DATE": "230423",
    "jobtypeid": 1,
    "start_date": "2021-08-15",
    "jobstatusid": 2,
    "non_gs1_codes": [],
}


@pytest.mark.django_db
def test_group_extract_text_service_report(
    client,
    service_report_temp_document,
    asset_id_temp_document,
    asset_no_temp_document,
    user,
    immediate_task_backend,
    asset,
    model,
    mocker,
):
    user = user()
    user.is_staff = True
    user.save()

    document1 = service_report_temp_document
    document2 = asset_id_temp_document
    document3 = asset_no_temp_document

    group = document1.group
    group.user = user
    group.save()

    document2.group = group
    document2.save()

    document3.group = group
    document3.save()

    mocker.patch(
        "documents.services.process_document.extract_group_info_with_ai",
        return_value=MOCK_ASSET_DATA,
    )
    permission1 = Permission.objects.get(codename="change_tempuploadgroup")
    permission2 = Permission.objects.get(codename="view_tempuploadgroup")
    user.user_permissions.add(permission1)
    user.user_permissions.add(permission2)

    client.force_login(user)

    extract_url = reverse("documents:extract_text", kwargs={"pk": group.pk})
    get_url = reverse("documents:temp_group", kwargs={"pk": group.pk})
    # start data extraction
    client.post(extract_url)
    response = client.get(get_url)

    # test exsiting asset id
    model = model(gtin="00885403497233")
    asset2 = asset(serialnumber="S00455524", modelid=model)
    client.post(extract_url)
    response = client.get(get_url)
    asset2.delete()
    model.delete()

    # test exsiting asset id
    asset2 = asset(serialnumber="S00455524")
    client.post(extract_url)
    response = client.get(get_url)
    asset2.delete()

    # test exsiting asset asset no
    asset2 = asset(customerassetnumber="5533488")
    client.post(extract_url)
    asset2.delete()


MOCK_DELIVERY_DATA = {
    "delivery_date": "2023-06-18",
    "non_gs1_codes": ["0002791747"],
    "delivery_items": [
        {"quantity": 2, "part_number": "72035-514"},
        {"quantity": 5, "part_number": "72035-507"},
    ],
    "purchase_order": [5100186],
    "delivery_note_number": "0002791747",
    "delivery_note_number_options": ["0002791747", "0002792257", "18062025"],
}


@pytest.mark.django_db
def test_group_extract_text_delivery_note(
    client,
    delivery_note_temp_document,
    user,
    immediate_task_backend,
    purchase_order,
    delivery,
    mocker,
):
    user = user()
    user.is_staff = True
    user.save()
    document = delivery_note_temp_document
    group = document.group

    group.user = user
    group.save()
    permission1 = Permission.objects.get(codename="change_tempuploadgroup")
    permission2 = Permission.objects.get(codename="view_tempuploadgroup")
    user.user_permissions.add(permission1)
    user.user_permissions.add(permission2)
    client.force_login(user)

    extract_url = reverse("documents:extract_text", kwargs={"pk": document.group.pk})
    get_url = reverse("documents:temp_group", kwargs={"pk": group.pk})

    mocker.patch(
        "documents.services.process_document.extract_group_info_with_ai",
        return_value=MOCK_DELIVERY_DATA,
    )
    # check with no data
    client.post(extract_url)
    response = client.get(get_url)

    # check with po
    purchase_order = purchase_order(po_id="5100186")
    client.post(extract_url)
    response = client.get(get_url)

    # check with po and delivery
    delivery = delivery(po=purchase_order, delivery_note_number="0002791747")
    client.post(extract_url)
    response = client.get(get_url)


@pytest.mark.django_db
def test_group_extract_unknown_document_type(
    client,
    asset_id_temp_document,
    user,
    immediate_task_backend,
    asset,
    model,
    brand,
    mocker,
):

    document1 = asset_id_temp_document
    group = document1.group
    group.document_type_id = DocumentTypes.UNKNOWN
    group.save()

    mocker.patch(
        "documents.services.process_document.extract_group_info_with_ai",
        return_value={},
    )

    extract_url = reverse("documents:extract_text", kwargs={"pk": group.pk})
    user = user()
    user.is_staff = True
    user.save()
    group.user = user
    group.save()
    permission1 = Permission.objects.get(codename="change_tempuploadgroup")
    permission2 = Permission.objects.get(codename="view_tempuploadgroup")
    user.user_permissions.add(permission1)
    user.user_permissions.add(permission2)
    client.force_login(user)

    get_url = reverse("documents:temp_group", kwargs={"pk": group.pk})
    # no asset and not model
    client.post(extract_url)
    response = client.get(get_url)


@pytest.mark.django_db
def test_group_extract_ai_error(
    client,
    asset_id_temp_document,
    user,
    immediate_task_backend,
    asset,
    model,
    brand,
    mocker,
):

    document1 = asset_id_temp_document
    group = document1.group
    group.document_type_id = DocumentTypes.UNKNOWN
    group.save()

    mocker.patch(
        "documents.services.process_document.extract_group_info_with_ai",
        side_effect=TimeoutError("simulated timeout error"),
    )

    extract_url = reverse("documents:extract_text", kwargs={"pk": group.pk})
    user = user()
    user.is_staff = True
    user.save()
    group.user = user
    group.save()
    permission1 = Permission.objects.get(codename="change_tempuploadgroup")
    permission2 = Permission.objects.get(codename="view_tempuploadgroup")
    user.user_permissions.add(permission1)
    user.user_permissions.add(permission2)
    client.force_login(user)

    get_url = reverse("documents:temp_group", kwargs={"pk": group.pk})
    # no asset and not model
    client.post(extract_url)
    response = client.get(get_url)


# test get get task result
@pytest.mark.django_db
def test_get_task_result_requires_login(client, temp_document):
    document = temp_document()
    url = reverse("documents:task_progress", kwargs={"pk": document.group.pk})

    response = client.get(url)
    assert response.status_code == 302
    assert "/login" in response.url.lower()


@pytest.mark.django_db
def test_get_task_result_requires_permission(client, temp_document, user):
    document = temp_document()
    url = reverse("documents:task_progress", kwargs={"pk": document.group.pk})
    user = user()
    client.force_login(user)

    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_get_task_result_renders(client, temp_document, user):
    document = temp_document("equipment_gs1.jpg")

    user = user()
    permission1 = Permission.objects.get(codename="view_tempuploadgroup")
    permission2 = Permission.objects.get(codename="change_tempuploadgroup")
    user.user_permissions.add(permission1)
    user.user_permissions.add(permission2)
    client.force_login(user)

    # start data extraction
    extract_url = reverse("documents:extract_text", kwargs={"pk": document.group.pk})
    response = client.post(extract_url)
    import time

    time.sleep(4)
    url = reverse("documents:task_progress", kwargs={"pk": document.group.pk})
    response = client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_get_extracted_text_renders(client, temp_document, user):
    document = temp_document()
    extract_url = reverse("documents:extract_text", kwargs={"pk": document.group.pk})
    user = user()
    permission1 = Permission.objects.get(codename="change_tempuploadgroup")
    permission2 = Permission.objects.get(codename="view_tempuploadgroup")
    user.user_permissions.add(permission1)
    user.user_permissions.add(permission2)
    client.force_login(user)

    # start data extraction
    response = client.post(extract_url)

    # get extraction result
    url = reverse("documents:task_progress", kwargs={"pk": document.group.pk})
    response = client.get(url)
    assert response.status_code == 200


# test temp_update_group_update
@pytest.mark.django_db
def test_temp_group_update_requires_login(client, temp_document):
    document = temp_document()
    url = reverse("documents:temp_group_update", kwargs={"pk": document.group.pk})

    response = client.get(url)
    assert response.status_code == 302
    assert "/login" in response.url.lower()


@pytest.mark.django_db
def test_temp_group_update_requires_permission(client, temp_document, user):
    document = temp_document()
    url = reverse("documents:temp_group_update", kwargs={"pk": document.group.pk})
    user = user()
    client.force_login(user)

    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_temp_group_update__renders(client, temp_document, user):
    document = temp_document()
    user = document.group.user
    permission1 = Permission.objects.get(codename="change_tempuploadgroup")
    user.user_permissions.add(permission1)
    url = reverse("documents:temp_group_update", kwargs={"pk": document.group.pk})
    client.force_login(user)

    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, "documents/temp_file_group_update.html")


@pytest.mark.django_db
def test_temp_group_update_posts(client, temp_document, user):
    document = temp_document()
    user = document.group.user
    permission1 = Permission.objects.get(codename="change_tempuploadgroup")
    user.user_permissions.add(permission1)
    url = reverse("documents:temp_group_update", kwargs={"pk": document.group.pk})
    client.force_login(user)
    from documents.models import DocumentTypes

    data = {"document_type_id": DocumentTypes.ASSET_DATA}

    response = client.post(url, data=data)
    assert response.status_code == 302


# test link_temp_document
@pytest.mark.django_db
def test_link_temp_document_requires_login(client):
    url = reverse("documents:link_temporary_document")

    response = client.get(url)
    assert response.status_code == 302
    assert "/login" in response.url.lower()


@pytest.mark.django_db
def test_link_temp_document_requires_permission(client, user):
    url = reverse("documents:link_temporary_document")
    user = user()
    client.force_login(user)

    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_link_temp_document_renders(client, user):
    url = reverse("documents:link_temporary_document")
    user = user()
    permission = Permission.objects.get(codename="add_tbldocuments")
    user.user_permissions.add(permission)
    client.force_login(user)

    response = client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_link_temp_document_posts(client, temp_document, asset, document_type, user):
    asset = asset()
    document_name = "equipment_gs1.jpg"
    temp_document = temp_document(document_name)
    user = user()
    permission = Permission.objects.get(codename="add_tbldocuments")
    user.user_permissions.add(permission)
    client.force_login(user)

    data = {
        "group": temp_document.group.pk,
        "document_type": document_type(),
    }
    query_params = urlencode(
        {"object_id": asset.pk, "content_type": "assets.tblassets"}
    )
    base_url = reverse("documents:link_temporary_document")
    full_url = f"{base_url}?{query_params}"
    response = client.post(full_url, data=data)
    assert response.status_code == 302


@pytest.mark.django_db
def test_link_temp_document_posts_htmx(
    client, temp_document, asset, document_type, user
):
    asset = asset()
    document_name = "equipment_gs1.jpg"
    temp_document = temp_document(document_name)
    user = user()
    permission = Permission.objects.get(codename="add_tbldocuments")
    user.user_permissions.add(permission)
    client.force_login(user)

    data = {
        "group": temp_document.group.pk,
        "document_type": document_type(),
    }
    query_params = urlencode(
        {"object_id": asset.pk, "content_type": "assets.tblassets"}
    )
    base_url = reverse("documents:link_temporary_document")
    full_url = f"{base_url}?{query_params}"
    response = client.post(full_url, data=data, HTTP_HX_REQUEST="true")
    assert response.status_code == 204


@pytest.mark.django_db
def test_link_temp_document_posts_unsuccessful(
    client, temp_document, asset, document_type, user
):
    document_name = "equipment_gs1.jpg"
    temp_document = temp_document(document_name)
    user = user()
    permission = Permission.objects.get(codename="add_tbldocuments")
    user.user_permissions.add(permission)
    client.force_login(user)

    data = {
        "group": temp_document.group.pk,
        "document_type": document_type(),
    }
    query_params = urlencode({"object_id": 30, "content_type": "assets.tblassets"})
    base_url = reverse("documents:link_temporary_document")
    full_url = f"{base_url}?{query_params}"
    response = client.post(full_url, data=data, HTTP_HX_REQUEST="true")
    assert response.status_code == 200


# test group_merged_data_update
@pytest.mark.django_db
def test_group_merged_data_requires_login(client, temp_document):
    document_name = "equipment_gs1.jpg"
    temp_document = temp_document(document_name)
    url = reverse("documents:update_group_data", kwargs={"pk": temp_document.group.pk})

    response = client.get(url)
    assert response.status_code == 302
    assert "/login" in response.url.lower()


@pytest.mark.django_db
def test_group_merged_data_requires_permission(client, user, temp_document):
    document_name = "equipment_gs1.jpg"
    temp_document = temp_document(document_name)
    url = reverse("documents:update_group_data", kwargs={"pk": temp_document.group.pk})
    user = user()
    client.force_login(user)

    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_group_merged_data_renders(client, asset_data_temp_group, user, temp_document):
    group = asset_data_temp_group
    document_name = "equipment_gs1.jpg"
    temp_document = temp_document(document_name)
    temp_document.group = group
    url = reverse("documents:update_group_data", kwargs={"pk": temp_document.group.pk})
    user = temp_document.group.user
    permission = Permission.objects.get(codename="change_tempuploadgroup")
    user.user_permissions.add(permission)
    client.force_login(user)

    response = client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_group_merged_data_posts(client, asset_data_temp_group, user, temp_document):
    group = asset_data_temp_group
    document_name = "equipment_gs1.jpg"
    temp_document = temp_document(document_name)
    temp_document.group = group
    url = reverse("documents:update_group_data", kwargs={"pk": temp_document.group.pk})
    user = temp_document.group.user
    permission = Permission.objects.get(codename="change_tempuploadgroup")
    user.user_permissions.add(permission)
    client.force_login(user)
    data = {"SERIAL": "test", "GTIN": "testGTIN"}

    response = client.post(url, data=data)
    assert response.status_code == 302

    group.refresh_from_db()
    new_data = group.extracted_json["merged_gs1_ai"]
    assert new_data["SERIAL"] == data["SERIAL"]
    assert new_data["GTIN"] == data["GTIN"]


# Test Quick sanner
@pytest.mark.django_db
def test_quick_scanner_requires_login(client):
    url = reverse("documents:quick_scanner")
    response = client.get(url)
    assert response.status_code == 302
    assert "/login" in response.url.lower()


@pytest.mark.django_db
def test_quick_scanner_renders(client, user):
    user = user()
    client.force_login(user)

    url = reverse("documents:quick_scanner")
    response = client.get(url, HTTP_HX_REQUEST="true")
    assert response.status_code == 200
    assertTemplateUsed(response, "documents/quick_scanner.html")


@pytest.mark.django_db
def test_quick_scanner_post(client, test_file, user):
    user = user()
    client.force_login(user)
    test_file = test_file("delivery_note.jpeg")
    data = {"files": [test_file]}
    url = reverse("documents:quick_scanner")
    response = client.post(url, data, format="multipart")

    assert response.status_code == 302


@pytest.mark.django_db
def test_quick_scanner_post_staff(client, test_file, user):
    user = user()
    user.is_staff = True
    user.save()
    client.force_login(user)
    test_file = test_file("equipment_gs1.jpg")
    data = {"files": [test_file]}
    url = reverse("documents:quick_scanner")
    response = client.post(url, data, format="multipart")

    assert response.status_code == 302


@pytest.mark.django_db
def test_quick_scanner_post_non_gs1(client, user):
    user = user()
    user.is_staff = True
    user.save()
    client.force_login(user)
    data = {"scanned_code": "1234"}
    url = reverse("documents:quick_scanner")
    response = client.post(url, data, format="multipart")

    assert response.status_code == 302


@pytest.mark.django_db
def test_quick_scanner_post_invalid_form(client, user):
    user = user()
    user.is_staff = True
    user.save()
    client.force_login(user)
    data = {}
    url = reverse("documents:quick_scanner")
    response = client.post(url, data, format="multipart")

    assert response.status_code == 302


# test replicate asset


@pytest.mark.django_db
def test_replicate_asset_view_login(
    client,
    asset,
):
    asset = asset()
    url = reverse("assets:replicate_asset", kwargs={"group_id": "new", "pk": asset.pk})
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert "/login" in response.url.lower()  # Ensure it's going to the login page


@pytest.mark.django_db
def test_replicate_asset_view_permission_denied(client, user_setup, asset):
    user = user_setup
    client.force_login(user)
    asset = asset()
    url = reverse("assets:replicate_asset", kwargs={"group_id": "new", "pk": asset.pk})
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_replicate_asset_view_renders(client, user_setup, asset):
    user = user_setup
    permission = Permission.objects.get(codename="add_tblassets")
    user.user_permissions.add(permission)

    client.force_login(user)
    asset = asset()
    url = reverse("assets:replicate_asset", kwargs={"group_id": "new", "pk": asset.pk})
    response = client.get(url)
    assert response.status_code == 302


@pytest.mark.django_db
def test_replicate_asset_view_renders_with_group(
    client, user_setup, asset, temp_document
):
    user = user_setup
    permission = Permission.objects.get(codename="add_tblassets")
    user.user_permissions.add(permission)

    test_doc = temp_document("equipment_gs1.jpg")

    client.force_login(user)
    asset = asset()
    url = reverse(
        "assets:replicate_asset", kwargs={"group_id": test_doc.group.pk, "pk": asset.pk}
    )
    response = client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_replicate_asset_view_posts(client, user_setup, asset, temp_document, model):
    model = model(gtin="00885403497233")
    user = user_setup
    user.is_staff = True
    permission = Permission.objects.get(codename="add_tblassets")
    user.user_permissions.add(permission)
    user.save()
    client.force_login(user)

    test_doc = temp_document("equipment_gs2.jpg")

    from documents.services.process_document import quick_group_processor

    quick_group_processor(test_doc)
    asset = asset(modelid=model)

    url = reverse(
        "assets:replicate_asset", kwargs={"group_id": test_doc.group.pk, "pk": asset.pk}
    )
    data = {"group_id": test_doc.group.pk, "template_asset": asset.pk}
    response = client.post(url, data=data)
    assert response.status_code == 302
    assert Tblassets.objects.last().serialnumber == "S00455524"
