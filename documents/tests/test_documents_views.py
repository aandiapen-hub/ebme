import os
from tokenize import group
from urllib.parse import urlencode
import pytest
from pytest_django.asserts import assertTemplateUsed
from django.contrib.messages import get_messages
from django.urls import reverse

from documents.service import SaveTempFiles
from assets.models import Tblassets, Tbljob, Tblmodel, Tbltesteqused
from documents.models import (
    DocumentsView,
    TblDocTableRef,
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
def test_document_create_view_renders(client, user_setup, mocker):
    user = user_setup
    mocker.patch(
        "documents.mixins.DocumentPermissionMixin.has_permission", return_value=True
    )

    client.force_login(user)

    base_url = reverse("documents:create_document_link")
    link_row = 0
    link_table = 0
    query_params = urlencode({"link_row": link_row, "link_table": link_table})
    url = f"{base_url}?{query_params}"
    response = client.get(url)

    assert response.status_code == 200
    form = response.context["form"]
    assert form.initial["link_row"] == str(link_row)
    assert form.initial["link_table"] == str(link_table)


@pytest.mark.django_db
def test_document_create_view_post_successfully(client, user_setup, mocker):
    user = user_setup
    mocker.patch(
        "documents.mixins.DocumentPermissionMixin.has_permission", return_value=True
    )

    client.force_login(user)

    url = reverse("documents:create_document_link")
    link_row = 0
    link_table = "tblAssets"

    # test html
    test_file = SimpleUploadedFile(
        "test.txt", b"Test content", content_type="text/plain"
    )
    form = {
        "link_row": link_row,
        "link_table": link_table,
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
        "link_row": link_row,
        "link_table": link_table,
        "document_name": "test_document2",
        "document_description": "test_document_description2",
        "document_bytea": test_file2,
    }

    response = client.post(url, data=form2, HTTP_HX_REQUEST="true")
    assert response.status_code == 204
    assert TblDocumentLinks.objects.last().documentid.document_name == "test_document2"


@pytest.mark.django_db
def test_document_create_view_post_dubplicated_document(client, user_setup, mocker):
    user = user_setup
    mocker.patch(
        "documents.mixins.DocumentPermissionMixin.has_permission", return_value=True
    )

    client.force_login(user)

    url = reverse("documents:create_document_link")
    link_row = 0
    link_table = "tblAssets"

    # test html
    test_file = SimpleUploadedFile(
        "test.txt", b"Test content", content_type="text/plain"
    )
    form = {
        "link_row": link_row,
        "link_table": link_table,
        "document_name": "test_document",
        "document_description": "test_document_description",
        "document_bytea": test_file,
    }
    response = client.post(url, data=form, HTTP_HX_REQUEST="true")
    link1_document = TblDocumentLinks.objects.last().documentid

    test_file2 = SimpleUploadedFile(
        "test.txt", b"Test content", content_type="text/plain"
    )

    form2 = {
        "link_row": link_row + 1,
        "link_table": link_table,
        "document_name": "test_document2",
        "document_description": "test_document_description2",
        "document_bytea": test_file2,
    }

    response2 = client.post(url, data=form2, HTTP_HX_REQUEST="true")

    link2_document = TblDocumentLinks.objects.last().documentid

    assert link1_document == link2_document


# test DocumentDeleteView
@pytest.mark.django_db
def test_document_delete_view_requires_login(client):
    last_document = TblDocumentLinks.objects.last()
    last_document_id = last_document.documentid.document_id
    url = reverse("documents:delete_document_link", kwargs={"pk": last_document_id})

    response = client.get(url)
    assert response.status_code == 302
    assert "/login" in response.url.lower()


@pytest.mark.django_db
def test_document_delete_view_requires_permission(client, user_setup):
    user = user_setup
    client.force_login(user)

    last_document = TblDocumentLinks.objects.last()
    last_document_id = last_document.documentid.document_id
    url = reverse("documents:delete_document_link", kwargs={"pk": last_document_id})

    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_document_delete_view_renders(client, user_setup, mocker):
    last_document = DocumentsView.objects.filter(customerid__isnull=False).last()
    last_document_id = last_document.document_link_id
    customerid = last_document.customerid
    url = reverse("documents:delete_document_link", kwargs={"pk": last_document_id})

    user = user_setup
    user.customerid = customerid
    user.save()
    mocker.patch(
        "documents.mixins.DocumentPermissionMixin.has_permission", return_value=True
    )

    client.force_login(user)

    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, "documents/partials/document_crud_modal.html")


@pytest.mark.django_db
def test_document_delete_view_post_successfully(client, user_setup, mocker):
    last_link = DocumentsView.objects.filter(customerid__isnull=False).last()
    last_link_id = last_link.document_link_id
    last_document_id = last_link.document_id
    customerid = last_link.customerid
    url = reverse("documents:delete_document_link", kwargs={"pk": last_link_id})

    user = user_setup
    user.customerid = customerid
    user.save()
    mocker.patch(
        "documents.mixins.DocumentPermissionMixin.has_permission", return_value=True
    )

    client.force_login(user)

    response = client.post(
        url,
    )
    assert response.status_code == 302
    assert not TblDocumentLinks.objects.filter(document_link_id=last_link_id).exists()


@pytest.mark.django_db
def test_document_delete_view_post_successfully_htmx(client, user_setup, mocker):
    last_link = DocumentsView.objects.filter(customerid__isnull=False).last()
    last_link_id = last_link.document_link_id
    last_document_id = last_link.document_id
    customerid = last_link.customerid
    url = reverse("documents:delete_document_link", kwargs={"pk": last_link_id})

    user = user_setup
    user.customerid = customerid
    user.save()
    mocker.patch(
        "documents.mixins.DocumentPermissionMixin.has_permission", return_value=True
    )

    client.force_login(user)

    response = client.post(url, HTTP_HX_REQUEST="true")
    assert response.status_code == 204
    assert not TblDocuments.objects.filter(document_id=last_document_id).exists()


# test DocumentLinkUpdateView
@pytest.mark.django_db
def test_document_link_update_view_requires_login(client):
    last_document = TblDocumentLinks.objects.last()
    last_document_id = last_document.documentid.document_id
    url = reverse("documents:update_document_link", kwargs={"pk": last_document_id})

    response = client.get(url)
    assert response.status_code == 302
    assert "/login" in response.url.lower()


@pytest.mark.django_db
def test_document_link_update_view_requires_permission(client, user_setup):
    user = user_setup
    client.force_login(user)

    last_document = TblDocumentLinks.objects.last()
    last_document_id = last_document.documentid.document_id
    url = reverse("documents:update_document_link", kwargs={"pk": last_document_id})

    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_document_link_update_view_renders(client, user_setup, mocker):
    last_document = DocumentsView.objects.filter(customerid__isnull=False).last()
    last_document_id = last_document.document_link_id
    customerid = last_document.customerid
    url = reverse("documents:update_document_link", kwargs={"pk": last_document_id})

    user = user_setup
    user.customerid = customerid
    user.save()
    mocker.patch(
        "documents.mixins.DocumentPermissionMixin.has_permission", return_value=True
    )

    client.force_login(user)

    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, "documents/partials/document_crud_modal.html")


@pytest.mark.django_db
def test_document_link_update_view_post_successfully(client, user_setup, mocker):
    last_link = DocumentsView.objects.filter(customerid__isnull=False).last()
    last_link_id = last_link.document_link_id
    last_document_id = last_link.document_id
    customerid = last_link.customerid
    url = reverse("documents:update_document_link", kwargs={"pk": last_link_id})

    user = user_setup
    user.customerid = customerid
    user.save()
    mocker.patch(
        "documents.mixins.DocumentPermissionMixin.has_permission", return_value=True
    )

    client.force_login(user)

    form = {
        "document_link_id": last_link.document_link_id,
        "document_id": last_link.document_id,
        "link_row": last_link.link_row,
        "link_table": last_link.link_table.table_id,
        "document_name": last_link.document_name,
        "customerid": last_link.customerid.customerid,
        "document_description": "test_description",
    }

    response = client.post(url, data=form)
    assert response.status_code == 302
    last_link.refresh_from_db()
    assert last_link.document_description == "test_description"


@pytest.mark.django_db
def test_document_link_update_view_post_successfully_htmx(client, user_setup, mocker):
    last_link = DocumentsView.objects.filter(customerid__isnull=False).last()
    last_link_id = last_link.document_link_id
    last_document_id = last_link.document_id
    customerid = last_link.customerid
    url = reverse("documents:update_document_link", kwargs={"pk": last_link_id})

    user = user_setup
    user.customerid = customerid
    user.save()
    mocker.patch(
        "documents.mixins.DocumentPermissionMixin.has_permission", return_value=True
    )

    client.force_login(user)
    form = {
        "document_link_id": last_link.document_link_id,
        "document_id": last_link.document_id,
        "link_row": last_link.link_row,
        "link_table": last_link.link_table.table_id,
        "document_name": last_link.document_name,
        "customerid": last_link.customerid.customerid,
        "document_description": "test_description2",
    }

    response = client.post(url, data=form, HTTP_HX_REQUEST="true")
    assert response.status_code == 204
    last_link.refresh_from_db()
    assert last_link.document_description == "test_description2"


@pytest.mark.django_db
def test_document_link_update_view_post_unsuccessful(client, user_setup, mocker):
    last_link = DocumentsView.objects.filter(customerid__isnull=False).last()
    last_link_id = last_link.document_link_id
    last_document_id = last_link.document_id
    customerid = last_link.customerid
    url = reverse("documents:update_document_link", kwargs={"pk": last_link_id})

    user = user_setup
    user.customerid = customerid
    user.save()
    mocker.patch(
        "documents.mixins.DocumentPermissionMixin.has_permission", return_value=True
    )

    client.force_login(user)

    form = {
        "document_link_id": last_link.document_link_id,
        "document_id": last_link.document_id,
        "link_row": last_link.link_row,
    }

    response = client.post(url, data=form)
    assert "The form contains invalid data" in response.context["error_message"]

    form2 = {
        "document_link_id": last_link.document_link_id,
        "document_id": last_link.document_id,
        "link_row": last_link.link_row,
        "link_table": last_link.link_table.table_id,
        "document_name": "",
        "customerid": last_link.customerid.customerid,
        "document_description": "test_description2",
    }
    response = client.post(url, data=form2)
    assert (
        "An error occurred while updating the document"
        in response.context["error_message"]
    )


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
def test_document_link_table_view_renders(client, user_setup, mocker):
    last_document = DocumentsView.objects.filter(customerid__isnull=False).last()
    customerid = last_document.customerid
    url = reverse("documents:table_document_links")

    user = user_setup
    user.customerid = customerid
    user.save()
    mocker.patch(
        "documents.mixins.DocumentPermissionMixin.has_permission", return_value=True
    )

    client.force_login(user)

    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, "documents/documents_links.html")

    query_params = urlencode({"universal_search": "bla bla bla"})
    filtered_respose = client.get(f"{url}?{query_params}", HTTP_HX_REQUEST="true")
    assert filtered_respose.status_code == 200


# test DocumentDownloadView
@pytest.mark.django_db
def test_download_document_view_requires_login(client):
    documentid = DocumentsView.objects.last().document_id
    url = reverse("documents:download_document", kwargs={"pk": documentid})
    response = client.get(url)
    assert response.status_code == 302
    assert "/login" in response.url.lower()


@pytest.mark.django_db
def test_download_document_view_requires_permission(client, user_setup):
    documentid = DocumentsView.objects.last().document_id
    url = reverse("documents:download_document", kwargs={"pk": documentid})

    user = user_setup
    client.force_login(user)

    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_download_document_view_renders(client, user_setup, mocker):
    last_document = DocumentsView.objects.filter(customerid__isnull=False).last()
    last_document_id = last_document.document_link_id
    customerid = last_document.customerid
    url = reverse("documents:download_document", kwargs={"pk": last_document_id})

    user = user_setup
    user.customerid = customerid
    user.save()
    client.force_login(user)
    mocker.patch(
        "documents.mixins.DocumentPermissionMixin.has_permission", return_value=True
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
def test_document_list_view_renders(client, user_setup, mocker):
    asset = Tblassets.objects.first()
    customerid = asset.customerid
    url = reverse("documents:list_documents")

    query_param = urlencode(
        {
            "link_row": asset.pk,
            "link_table": "tblAssets",
            "app_model": "assets.Tblassets",
        }
    )

    user = user_setup
    user.customerid = customerid
    user.save()
    mocker.patch(
        "documents.mixins.DocumentPermissionMixin.has_permission", return_value=True
    )

    client.force_login(user)

    response = client.get(f"{url}?{query_param}")
    assert response.status_code == 200
    assertTemplateUsed(response="documents/partials/document_list.html")


# test DocumentLinkDeleteView
@pytest.mark.django_db
def test_document_link_delete_view_requires_login(client):
    link = DocumentsView.objects.last()
    url = reverse("documents:delete_document_link", kwargs={"pk": link.pk})
    response = client.get(url)
    assert response.status_code == 302
    assert "/login" in response.url.lower()


@pytest.mark.django_db
def test_document_link_delete_view_requires_permission(client, user_setup):
    link = DocumentsView.objects.last()
    url = reverse("documents:delete_document_link", kwargs={"pk": link.pk})
    user = user_setup
    client.force_login(user)

    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_document_link_delete_view_renders(client, user_setup, mocker):
    link = DocumentsView.objects.filter(customerid__isnull=False).last()
    url = reverse("documents:delete_document_link", kwargs={"pk": link.pk})

    user = user_setup
    user.customerid = link.customerid
    user.save()
    mocker.patch(
        "documents.mixins.DocumentPermissionMixin.has_permission", return_value=True
    )

    client.force_login(user)

    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response="documents/partials/document_list.html")


@pytest.mark.django_db
def test_document_link_delete_post_successful(client, user_setup, mocker):
    link = DocumentsView.objects.filter(customerid__isnull=False).last()
    url = reverse("documents:delete_document_link", kwargs={"pk": link.pk})
    document = TblDocuments.objects.get(document_id=link.document_id)
    TblDocumentLinks.objects.create(
        link_table=link.link_table, link_row=link.link_row + 1, documentid=document
    )

    user = user_setup
    user.customerid = link.customerid
    user.save()
    mocker.patch(
        "documents.mixins.DocumentPermissionMixin.has_permission", return_value=True
    )

    client.force_login(user)

    response = client.post(url)
    assert response.status_code == 302

    with pytest.raises(Exception):
        link.refresh_from_db()


# test DocumentPreView
@pytest.mark.django_db
def test_document_pre_view_requires_login(client):
    documentid = DocumentsView.objects.last().document_id
    url = reverse("documents:load_image") + f"?pk={documentid})"
    response = client.get(url)
    assert response.status_code == 302
    assert "/login" in response.url.lower()


@pytest.mark.django_db
def test_document_pre_view_renders_pdf(client, user_setup):
    user = user_setup
    client.force_login(user)

    base_dir = os.path.dirname(__file__)
    image1_path = os.path.join(base_dir, "test_files", "service_report.pdf")
    with open(image1_path, "rb") as f:
        testFile = File(f, name="service_report.pdf")
        image = TemporaryUpload.objects.create(
            user=user,
            file=testFile,
            file_size=testFile.size,
            mime_type="application/pdf",
        )
    temp_document = TemporaryUpload.objects.last()
    temp_document_id = temp_document.pk
    base_url = reverse("documents:load_image")
    query_params = urlencode({"pk": temp_document_id})
    url = f"{base_url}?{query_params}"

    response = client.get(url)
    assert response["Content-Type"] == "image/png"  # or expected mime type
    assert isinstance(response, type(response))  # FileResponse


@pytest.mark.django_db
def test_document_pre_view_renders_use_specific_file(client, user_setup):
    user = user_setup
    client.force_login(user)

    base_dir = os.path.dirname(__file__)
    image1_path = os.path.join(base_dir, "test_files", "service_report.pdf")
    with open(image1_path, "rb") as f:
        testFile = File(f, name="service_report.pdf")
        image = TemporaryUpload.objects.create(
            user=user,
            file=testFile,
            file_size=testFile.size,
            mime_type="application/pdf",
        )
    temp_document = TemporaryUpload.objects.last()
    temp_document_id = temp_document.pk
    base_url = reverse("documents:load_image")
    query_params = urlencode({"pk": temp_document_id})
    url = f"{base_url}?{query_params}"

    user2 = user_setup
    user2.pk = 9999
    user.email = "test@test.com"
    user2.save(force_insert=True)
    temp_document.user = user2
    temp_document.save()

    response = client.get(url)
    assert response.status_code == 404


@pytest.mark.django_db
def test_document_pre_view_renders_image(client, user_setup):
    user = user_setup
    client.force_login(user)

    base_dir = os.path.dirname(__file__)
    image1_path = os.path.join(base_dir, "test_files", "delivery_note.jpeg")
    with open(image1_path, "rb") as f:
        testFile = File(f, name="delivery_note.jpeg")
        image = TemporaryUpload.objects.create(
            user=user, file=testFile, file_size=testFile.size, mime_type="image/jpeg"
        )
    temp_document = TemporaryUpload.objects.last()
    temp_document_id = temp_document.pk
    base_url = reverse("documents:load_image")
    query_params = urlencode({"pk": temp_document_id})
    url = f"{base_url}?{query_params}"

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
def test_temp_files_delete_all_view_posts(client, user_setup, mocker):
    user = user_setup
    client.force_login(user)
    mocker.patch(
        "documents.mixins.DocumentPermissionMixin.has_permission", return_value=True
    )

    base_dir = os.path.dirname(__file__)
    image1_path = os.path.join(base_dir, "test_files", "delivery_note.jpeg")
    with open(image1_path, "rb") as f:
        testFile = File(f, name="delivery_note.jpeg")
        image = TemporaryUpload.objects.create(
            user=user, file=testFile, file_size=testFile.size, mime_type="image/jpeg"
        )
    temp_document = TemporaryUpload.objects.last()
    assert TemporaryUpload.objects.filter(user=user).exists()

    url = reverse("documents:delete_all_temp_files")
    response = client.post(url)
    assert response.status_code == 302
    assert not TemporaryUpload.objects.filter(user=user).exists()


# Test TempFilesDeleteView
@pytest.mark.django_db
def test_temp_file_delete_view_requires_login(user_setup, client):
    base_dir = os.path.dirname(__file__)
    image1_path = os.path.join(base_dir, "test_files", "delivery_note.jpeg")
    with open(image1_path, "rb") as f:
        testFile = File(f, name="delivery_note.jpeg")
        image = TemporaryUpload.objects.create(
            user=user_setup,
            file=testFile,
            file_size=testFile.size,
            mime_type="image/jpeg",
        )
    temp_file = TemporaryUpload.objects.last()
    url = reverse("documents:delete_temp_file", kwargs={"pk": temp_file.pk})
    response = client.get(url)
    assert response.status_code == 302
    assert "/login" in response.url.lower()


@pytest.mark.django_db
def test_temp_file_delete_view_posts(client, user_setup, mocker):
    user = user_setup
    client.force_login(user)

    base_dir = os.path.dirname(__file__)
    image1_path = os.path.join(base_dir, "test_files", "delivery_note.jpeg")
    with open(image1_path, "rb") as f:
        testFile = File(f, name="delivery_note.jpeg")
        image = TemporaryUpload.objects.create(
            user=user, file=testFile, file_size=testFile.size, mime_type="image/jpeg"
        )
    temp_document = TemporaryUpload.objects.filter(user=user).last()
    assert TemporaryUpload.objects.filter(user=user).exists()

    url = reverse("documents:delete_temp_file", kwargs={"pk": temp_document.pk})
    response = client.post(url)
    assert response.status_code == 302
    assert not TemporaryUpload.objects.filter(pk=temp_document.pk).exists()


@pytest.mark.django_db
def test_temp_file_delete_view_posts_htmx(client, user_setup, mocker):
    user = user_setup
    client.force_login(user)

    base_dir = os.path.dirname(__file__)
    image1_path = os.path.join(base_dir, "test_files", "delivery_note.jpeg")
    with open(image1_path, "rb") as f:
        testFile = File(f, name="delivery_note.jpeg")
        image = TemporaryUpload.objects.create(
            user=user, file=testFile, file_size=testFile.size, mime_type="image/jpeg"
        )
    temp_document = TemporaryUpload.objects.filter(user=user).last()
    assert TemporaryUpload.objects.filter(user=user).exists()

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
def test_temporary_upload_create_view_renders(client, user_setup, mocker):
    user = user_setup
    client.force_login(user)
    mocker.patch(
        "django.contrib.auth.mixins.PermissionRequiredMixin.has_permission",
        return_value=True,
    )

    url = reverse("documents:create_temp_files")
    response = client.get(url, HTTP_HX_REQUEST="true")
    assert response.status_code == 200
    assertTemplateUsed(response, "documents/partials/temp_document_create.html")


@pytest.mark.django_db
def test_temporary_upload_create_view_post_new_group(client, user_setup, mocker):
    user = user_setup
    client.force_login(user)
    mocker.patch(
        "django.contrib.auth.mixins.PermissionRequiredMixin.has_permission",
        return_value=True,
    )
    test_file = SimpleUploadedFile(
        "test.pdf", b"test image data", content_type="application/pdf"
    )

    data = {"files": [test_file]}

    url = reverse("documents:create_temp_files")
    response = client.post(url, data, format="multipart")
    assert response.status_code == 302
    assert TemporaryUpload.objects.filter(user=user, group=0).exists()


@pytest.mark.django_db
def test_temporary_upload_create_view_post_specific_group(client, user_setup, mocker):
    user = user_setup
    client.force_login(user)

    user = user_setup
    client.force_login(user)
    mocker.patch(
        "django.contrib.auth.mixins.PermissionRequiredMixin.has_permission",
        return_value=True,
    )

    base_dir = os.path.dirname(__file__)
    image1_path = os.path.join(base_dir, "test_files", "delivery_note.jpeg")
    with open(image1_path, "rb") as f:
        testFile = File(f, name="delivery_note.jpeg")
        image = TemporaryUpload.objects.create(
            user=user, file=testFile, file_size=testFile.size, mime_type="image/jpeg"
        )

    test_file = SimpleUploadedFile(
        "test.pdf", b"test image data", content_type="application/pdf"
    )

    data = {"group": "2", "files": [test_file]}

    url = reverse("documents:create_temp_files")
    response = client.post(url, data, format="multipart")
    assert response.status_code == 302
    assert TemporaryUpload.objects.filter(user=user, group=2).exists()


@pytest.mark.django_db
def test_temporary_upload_create_view_post_specific_group_htmx(
    client, user_setup, mocker
):
    user = user_setup
    client.force_login(user)
    mocker.patch(
        "django.contrib.auth.mixins.PermissionRequiredMixin.has_permission",
        return_value=True,
    )

    test_file = SimpleUploadedFile(
        "test.pdf", b"test image data", content_type="application/pdf"
    )

    data = {"group": "2", "files": [test_file]}

    url = reverse("documents:create_temp_files")
    response = client.post(url, data, format="multipart", HTTP_HX_REQUEST="true")
    assert response.status_code == 200
    assert TemporaryUpload.objects.filter(user=user, group=2).exists()


@pytest.mark.django_db
def test_temporary_upload_create_view_post_new_group_htmx(client, user_setup, mocker):
    user = user_setup
    client.force_login(user)
    mocker.patch(
        "django.contrib.auth.mixins.PermissionRequiredMixin.has_permission",
        return_value=True,
    )

    test_file = SimpleUploadedFile(
        "test.pdf", b"test image data", content_type="application/pdf"
    )

    data = {"group": "new", "files": [test_file]}
    url = reverse("documents:create_temp_files")
    response = client.post(url, data, format="multipart", HTTP_HX_REQUEST="true")
    assert response.status_code == 200
    assert TemporaryUpload.objects.filter(user=user, group=1).exists()


@pytest.mark.django_db
def test_temporary_upload_create_view_post_rejects_dissimilar_file_format(
    client, user_setup, mocker
):
    user = user_setup
    client.force_login(user)
    mocker.patch(
        "django.contrib.auth.mixins.PermissionRequiredMixin.has_permission",
        return_value=True,
    )

    base_dir = os.path.dirname(__file__)
    image1_path = os.path.join(base_dir, "test_files", "delivery_note.jpeg")
    with open(image1_path, "rb") as f:
        testFile = File(f, name="delivery_note.jpeg")
        image = TemporaryUpload.objects.create(
            user=user,
            file=testFile,
            file_size=testFile.size,
            mime_type="image/jpeg",
            group=1,
        )

    test_file = SimpleUploadedFile(
        "test.pdf", b"test image data", content_type="application/pdf"
    )

    data = {"group": "1", "files": [test_file]}

    url = reverse("documents:create_temp_files")
    response = client.post(url, data, format="multipart", HTTP_HX_REQUEST="true")
    assert response.status_code == 200
    assert TemporaryUpload.objects.filter(user=user, group=1).count() == 1


@pytest.mark.django_db
def test_temporary_upload_create_view_poKst_existing_group_htmx(
    client, user_setup, mocker
):
    user = user_setup
    client.force_login(user)
    mocker.patch(
        "django.contrib.auth.mixins.PermissionRequiredMixin.has_permission",
        return_value=True,
    )

    base_dir = os.path.dirname(__file__)
    image1_path = os.path.join(base_dir, "test_files", "delivery_note.jpeg")
    with open(image1_path, "rb") as f:
        testFile = File(f, name="delivery_note.jpeg")
        image = TemporaryUpload.objects.create(
            user=user,
            file=testFile,
            file_size=testFile.size,
            mime_type="image/jpeg",
            group=1,
        )

    test_file = SimpleUploadedFile(
        "test.pdf", b"test image data", content_type="image/jpeg"
    )

    data = {"group": "1", "files": [test_file]}

    url = reverse("documents:create_temp_files")
    response = client.post(url, data, format="multipart", HTTP_HX_REQUEST="true")
    assert response.status_code == 200
    assert TemporaryUpload.objects.filter(user=user, group=1).count() == 2


@pytest.mark.django_db
def test_temporary_upload_create_view_post_invalid(client, user_setup, mocker):
    user = user_setup
    client.force_login(user)
    mocker.patch(
        "django.contrib.auth.mixins.PermissionRequiredMixin.has_permission",
        return_value=True,
    )

    test_file = SimpleUploadedFile(
        "test.pdf", b"test image data", content_type="text/plain"
    )

    data = {"group": "1", "files": [test_file]}

    url = reverse("documents:create_temp_files")
    response = client.post(url, data, format="multipart", HTTP_HX_REQUEST="true")
    assert response.status_code == 200
    assert response["HX-Retarget"] == "this"


# test TempUploadDetailView
@pytest.mark.django_db
def test_temp_file_detail_view_requires_login(user_setup, client):
    base_dir = os.path.dirname(__file__)
    image1_path = os.path.join(base_dir, "test_files", "delivery_note.jpeg")
    with open(image1_path, "rb") as f:
        testFile = File(f, name="delivery_note.jpeg")
        image = TemporaryUpload.objects.create(
            user=user_setup,
            file=testFile,
            file_size=testFile.size,
            mime_type="image/jpeg",
        )
    temp_file = TemporaryUpload.objects.last()
    url = reverse("documents:temp_file", kwargs={"pk": temp_file.pk})
    response = client.get(url)
    assert response.status_code == 302
    assert "/login" in response.url.lower()


@pytest.mark.django_db
def test_temp_file_detail_view_renders(client, user_setup, mocker):
    user = user_setup
    client.force_login(user)
    mocker.patch(
        "django.contrib.auth.mixins.PermissionRequiredMixin.has_permission",
        return_value=True,
    )

    base_dir = os.path.dirname(__file__)
    image1_path = os.path.join(base_dir, "test_files", "delivery_note.jpeg")
    with open(image1_path, "rb") as f:
        testFile = File(f, name="delivery_note.jpeg")
        image = TemporaryUpload.objects.create(
            user=user, file=testFile, file_size=testFile.size, mime_type="image/jpeg"
        )
    temp_document = TemporaryUpload.objects.filter(user=user).last()

    url = reverse("documents:temp_file", kwargs={"pk": temp_document.pk})
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, "documents/partials/temp_file.html")


@pytest.mark.django_db
def test_temp_file_detail_view_renders_not_your_file(client, user_setup, mocker):
    user = user_setup
    mocker.patch(
        "django.contrib.auth.mixins.PermissionRequiredMixin.has_permission",
        return_value=True,
    )

    base_dir = os.path.dirname(__file__)
    image1_path = os.path.join(base_dir, "test_files", "delivery_note.jpeg")
    with open(image1_path, "rb") as f:
        testFile = File(f, name="delivery_note.jpeg")
        image = TemporaryUpload.objects.create(
            user=user, file=testFile, file_size=testFile.size, mime_type="image/jpeg"
        )
    temp_document = TemporaryUpload.objects.filter(user=user).last()
    user2 = user_setup
    user2.pk = 9999
    user2.email = "test@test.com"

    user2.save(force_insert=True)
    client.force_login(user2)

    url = reverse("documents:temp_file", kwargs={"pk": temp_document.pk})
    response = client.get(url)
    assert response.status_code == 404


# test TempUploadListView
@pytest.mark.django_db
def test_temp_file_list_view_requires_login(client):
    url = reverse("documents:user_temp_files")
    response = client.get(url)
    assert response.status_code == 302
    assert "/login" in response.url.lower()


@pytest.mark.django_db
def test_temp_file_list_view_renders(client, user_setup, mocker):
    user = user_setup
    client.force_login(user)
    mocker.patch(
        "django.contrib.auth.mixins.PermissionRequiredMixin.has_permission",
        return_value=True,
    )

    base_dir = os.path.dirname(__file__)
    image1_path = os.path.join(base_dir, "test_files", "service_report.pdf")
    with open(image1_path, "rb") as f:
        testFile = File(f, name="service_report.pdf")
        image = TemporaryUpload.objects.create(
            user=user,
            file=testFile,
            file_size=testFile.size,
            mime_type="application/pdf",
        )
    temp_document = TemporaryUpload.objects.filter(user=user).last()

    url = reverse("documents:user_temp_files")
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, "documents/temp_files_list.html")

    query_params = urlencode({"group": temp_document.group, "success_url": "testurl"})
    filtered_respose = client.get(f"{url}?{query_params}")
    assert filtered_respose.status_code == 200
    assert "testurl" in filtered_respose.context["success_url"]


# test DocumentUpdateView
@pytest.mark.django_db
def test_document_update_view_requires_login(client):
    last_document = TblDocumentLinks.objects.last()
    last_document_id = last_document.documentid.document_id
    url = reverse("documents:update_document", kwargs={"pk": last_document_id})

    response = client.get(url)
    assert response.status_code == 302
    assert "/login" in response.url.lower()


@pytest.mark.django_db
def test_document_update_view_requires_permission(client, user_setup):
    user = user_setup
    client.force_login(user)

    last_document = TblDocumentLinks.objects.last()
    last_document_id = last_document.documentid.document_id
    url = reverse("documents:update_document", kwargs={"pk": last_document_id})

    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_document_update_view_renders(client, user_setup, mocker):
    document_link = DocumentsView.objects.filter(customerid__isnull=False).first()
    customerid = document_link.customerid
    last_document = TblDocuments.objects.filter(
        document_id=document_link.document_id
    ).first()

    url = reverse("documents:update_document", kwargs={"pk": last_document.document_id})

    user = user_setup
    user.customerid = customerid
    user.save()
    mocker.patch(
        "documents.mixins.DocumentPermissionMixin.has_permission", return_value=True
    )

    client.force_login(user)

    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, "documents/document_update.html")


@pytest.mark.django_db
def test_document_update_view_post(client, user_setup, mocker):
    document_link = DocumentsView.objects.filter(customerid__isnull=False).first()
    customerid = document_link.customerid
    last_document = TblDocuments.objects.filter(
        document_id=document_link.document_id
    ).first()
    url = reverse("documents:update_document", kwargs={"pk": last_document.document_id})

    user = user_setup
    user.customerid = customerid
    user.save()
    mocker.patch(
        "documents.mixins.DocumentPermissionMixin.has_permission", return_value=True
    )
    client.force_login(user)

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


# test saving temp file permanently
@pytest.mark.django_db
def test_save_temp_file_permanently(user_setup, client):
    user = user_setup
    client.force_login(user)
    last_document = TblDocuments.objects.last()

    base_dir = os.path.dirname(__file__)
    image1_path = os.path.join(base_dir, "test_files", "delivery_note.jpeg")
    with open(image1_path, "rb") as f:
        testFile = File(f, name="delivery_note.jpeg")
        image = TemporaryUpload.objects.create(
            user=user,
            original_name="delivery_note.jpeg",
            file=testFile,
            file_size=testFile.size,
            mime_type="image/jpeg",
        )
    temp_document = TemporaryUpload.objects.filter(user=user)

    assert TemporaryUpload.objects.filter(user=user).exists()

    temp_files = SaveTempFiles(
        temp_document, 300, TblDocTableRef.objects.first().table_name
    )
    temp_files.save_all()

    last_document = TblDocuments.objects.last()
    assert not TemporaryUpload.objects.filter(user=user).exists()

    assert TblDocuments.objects.filter(document_name="delivery_note.jpeg").exists()


# test LinkTemporaryDocumentView
@pytest.mark.django_db
def test_link_temporary_document_view_requires_login(client):
    url = reverse("documents:link_temporary_document")

    response = client.get(url)
    assert response.status_code == 302
    assert "/login" in response.url.lower()


@pytest.mark.django_db
def test_link_temporary_document_view_requires_permission(client, user_setup):
    user = user_setup
    client.force_login(user)

    url = reverse("documents:link_temporary_document")

    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_link_temporary_document_view_renders(client, user_setup, mocker):
    user = user_setup
    client.force_login(user)
    mocker.patch(
        "django.contrib.auth.mixins.PermissionRequiredMixin.has_permission",
        return_value=True,
    )

    url = reverse("documents:link_temporary_document")

    response = client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_link_temporary_document_view_post_successfully(client, user_setup, mocker):
    user = user_setup
    client.force_login(user)
    mocker.patch(
        "django.contrib.auth.mixins.PermissionRequiredMixin.has_permission",
        return_value=True,
    )

    link_table = TblDocTableRef.objects.first()
    link_row = 1
    group = 1

    base_dir = os.path.dirname(__file__)
    image1_path = os.path.join(base_dir, "test_files", "delivery_note.jpeg")
    with open(image1_path, "rb") as f:
        testFile = File(f, name="delivery_note.jpeg")
        image = TemporaryUpload.objects.create(
            user=user,
            file=testFile,
            file_size=testFile.size,
            mime_type="image/jpeg",
            group=group,
            original_name="delivery_note.jpeg",
        )

    form_data = {
        "group": "1",
        "link_row": link_row,
        "link_table": link_table.table_name,
        "document_type": 0,
    }

    url = reverse("documents:link_temporary_document")

    response = client.post(url, form_data)
    assert response.status_code == 302
    assert "delivery_note.jpeg" in DocumentsView.objects.filter(
        link_table=link_table,
        link_row=link_row,
    ).values_list("document_name", flat=True)


@pytest.mark.django_db
def test_link_temporary_document_view_post_successfully_htmx(
    client, user_setup, mocker
):
    user = user_setup
    client.force_login(user)
    mocker.patch(
        "django.contrib.auth.mixins.PermissionRequiredMixin.has_permission",
        return_value=True,
    )

    link_table = TblDocTableRef.objects.first()
    link_row = 1
    group = 1

    base_dir = os.path.dirname(__file__)
    image1_path = os.path.join(base_dir, "test_files", "delivery_note.jpeg")
    with open(image1_path, "rb") as f:
        testFile = File(f, name="delivery_note.jpeg")
        image = TemporaryUpload.objects.create(
            user=user,
            file=testFile,
            file_size=testFile.size,
            mime_type="image/jpeg",
            group=group,
            original_name="delivery_note.jpeg",
        )

    form_data = {
        "group": "1",
        "link_row": link_row,
        "link_table": link_table.table_name,
        "document_type": 0,
    }

    url = reverse("documents:link_temporary_document")

    response = client.post(url, form_data, HTTP_HX_REQUEST="true")
    assert response.status_code == 204
    assert "delivery_note.jpeg" in DocumentsView.objects.filter(
        link_table=link_table,
        link_row=link_row,
    ).values_list("document_name", flat=True)


@pytest.mark.django_db
def test_link_temporary_document_view_post_successfully_multiple_images(
    client, user_setup, mocker
):
    user = user_setup
    client.force_login(user)
    mocker.patch(
        "django.contrib.auth.mixins.PermissionRequiredMixin.has_permission",
        return_value=True,
    )

    link_table = TblDocTableRef.objects.first()
    link_row = 1
    group = 1

    base_dir = os.path.dirname(__file__)
    image1_path = os.path.join(base_dir, "test_files", "delivery_note.jpeg")
    with open(image1_path, "rb") as f:
        testFile = File(f, name="delivery_note.jpeg")
        image = TemporaryUpload.objects.create(
            user=user,
            file=testFile,
            file_size=testFile.size,
            mime_type="image/jpeg",
            group=group,
            original_name="delivery_note.jpeg",
        )

    image2_path = os.path.join(base_dir, "test_files", "equipment_gs1.jpeg")
    with open(image1_path, "rb") as f:
        testFile = File(f, name="delivery_note.jpeg")
        image = TemporaryUpload.objects.create(
            user=user,
            file=testFile,
            file_size=testFile.size,
            mime_type="image/jpeg",
            group=group,
            original_name="delivery_note.jpeg",
        )

    form_data = {
        "group": "1",
        "link_row": link_row,
        "link_table": link_table.table_name,
        "document_type": 0,
    }

    url = reverse("documents:link_temporary_document")

    TblDocumentLinks.objects.filter(link_row=link_row, link_table=link_table).delete()

    response = client.post(url, form_data)
    assert response.status_code == 302
    filenames = DocumentsView.objects.filter(
        link_table=link_table,
        link_row=link_row,
    ).values_list("document_name", flat=True)
    assert any(name.endswith(".pdf") for name in filenames)


@pytest.mark.django_db
def test_link_temporary_document_view_post_invalid(client, user_setup, mocker):
    user = user_setup
    client.force_login(user)
    mocker.patch(
        "django.contrib.auth.mixins.PermissionRequiredMixin.has_permission",
        return_value=True,
    )

    link_table = TblDocTableRef.objects.first()
    link_row = 1
    group = 1

    base_dir = os.path.dirname(__file__)
    image1_path = os.path.join(base_dir, "test_files", "delivery_note.jpeg")
    with open(image1_path, "rb") as f:
        testFile = File(f, name="delivery_note.jpeg")
        image = TemporaryUpload.objects.create(
            user=user,
            file=testFile,
            file_size=testFile.size,
            mime_type="image/jpeg",
            group=group,
            original_name="delivery_note.jpeg",
        )

    form_data = {
        "group": "1",
        "link_row": link_row,
        "link_table": link_table.table_name,
    }

    url = reverse("documents:link_temporary_document")

    response = client.post(url, form_data)
    assert response.status_code == 200

    messages = list(get_messages(response.wsgi_request))

    messages_list = [m.message for m in messages]
    assert any("Failed" in msg for msg in messages_list)


# test QuickScanner
@pytest.mark.django_db
def test_quick_scanner_requires_login(client):
    url = reverse("documents:quick_scanner")

    response = client.get(url)
    assert response.status_code == 302
    assert "/login" in response.url.lower()


# test QuickScanner
@pytest.mark.django_db
def test_quick_scanner_renders(client, user_setup):
    user = user_setup
    client.force_login(user)
    url = reverse("documents:quick_scanner")
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed("documents/quick_scanner.html")


@pytest.mark.django_db
def test_quick_scanner_post_unknown_gtin(client, user_setup, mocker):
    user = user_setup
    client.force_login(user)

    Tbltesteqused.objects.filter(jobid__assetid__serialnumber="S00455524").delete()
    Tbljob.objects.filter(assetid__serialnumber="S00455524").delete()
    Tblassets.objects.filter(serialnumber="S00455524").delete()
    model = Tblmodel.objects.filter(gtin="00885403497233").first()
    model.gtin = ""
    model.save()

    base_dir = os.path.dirname(__file__)

    image2_path = os.path.join(base_dir, "test_files", "equipment_gs1.jpg")

    with open(image2_path, "rb") as f:
        test_file = SimpleUploadedFile(
            name="equipment_gs1.jpg", content=f.read(), content_type="image/jpg"
        )

    data = {"file": [test_file]}
    url = reverse("documents:quick_scanner")
    response = client.post(url, data, format="multipart")
    assert response.status_code == 200
    assertTemplateUsed("documents/partials/quick_scan/unknown_gtin.html")


@pytest.mark.django_db
def test_quick_scanner_post_known_equipment_model(client, user_setup, mocker):
    user = user_setup
    client.force_login(user)

    Tbltesteqused.objects.filter(jobid__assetid__serialnumber="S00455524").delete()
    Tbljob.objects.filter(assetid__serialnumber="S00455524").delete()
    Tblassets.objects.filter(serialnumber="S00455524").delete()

    base_dir = os.path.dirname(__file__)

    image2_path = os.path.join(base_dir, "test_files", "equipment_gs1.jpg")

    with open(image2_path, "rb") as f:
        test_file = SimpleUploadedFile(
            name="equipment_gs1.jpg", content=f.read(), content_type="image/jpg"
        )

    data = {"file": [test_file]}
    url = reverse("documents:quick_scanner")
    response = client.post(url, data, format="multipart")
    assert response.status_code == 302
    assertTemplateUsed("assets/create_form.html")


@pytest.mark.django_db
def test_quick_scanner_post_known_equipment(client, user_setup, mocker):
    user = user_setup
    client.force_login(user)

    base_dir = os.path.dirname(__file__)

    image2_path = os.path.join(base_dir, "test_files", "equipment_gs1.jpg")

    with open(image2_path, "rb") as f:
        test_file = SimpleUploadedFile(
            name="equipment_gs1.jpg", content=f.read(), content_type="image/jpg"
        )

    data = {"file": [test_file]}
    url = reverse("documents:quick_scanner")
    response = client.post(url, data, format="multipart")
    assert response.status_code == 302
    assertTemplateUsed("assets/assetview.html")


@pytest.mark.django_db
def test_quick_scanner_post_no_information(client, user_setup, mocker):
    user = user_setup
    client.force_login(user)

    base_dir = os.path.dirname(__file__)

    image2_path = os.path.join(base_dir, "test_files", "delivery_note.jpeg")

    with open(image2_path, "rb") as f:
        test_file = SimpleUploadedFile(
            name="delivery_note.jpeg", content=f.read(), content_type="image/jpeg"
        )

    data = {}
    url = reverse("documents:quick_scanner")
    response = client.post(url, data, format="multipart")
    assert response.status_code == 200

    messages = list(get_messages(response.wsgi_request))
    messages_list = [m.message for m in messages]

    assert any("No information" in msg for msg in messages_list)


@pytest.mark.django_db
def test_quick_scanner_post_incorrect_filetype(client, user_setup, mocker):
    user = user_setup
    client.force_login(user)

    Tbltesteqused.objects.filter(jobid__assetid__serialnumber="S00455524").delete()
    Tbljob.objects.filter(assetid__serialnumber="S00455524").delete()
    Tblassets.objects.filter(serialnumber="S00455524").delete()

    base_dir = os.path.dirname(__file__)

    image2_path = os.path.join(base_dir, "test_files", "service_report.pdf")

    with open(image2_path, "rb") as f:
        test_file = SimpleUploadedFile(
            name="service_report.pdf", content=f.read(), content_type="application/pdf"
        )

    data = {"file": [test_file]}
    url = reverse("documents:quick_scanner")
    response = client.post(url, data, format="multipart")
    assert response.status_code == 200

    messages = list(get_messages(response.wsgi_request))

    messages_list = [m.message for m in messages]
    assert any("Incorrect" in msg for msg in messages_list)
