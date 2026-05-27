from urllib.parse import urlencode

from django.contrib.auth.models import Permission
import pytest
from django.db import IntegrityError, transaction, transaction
from django.urls import reverse
from pytest_django.asserts import assertTemplateUsed
from assets.models import (
    Tbljob,
    Tbljobstatus,
    Tbltechnicianlist,
    Tbljobtypes,
    Tblassets,
    Tbltestscarriedout,
    Tblcheckslists,
    Tbltestresult,
    Tblpartsused,
    Tbltesteqused,
)

from documents.models import TemporaryUpload
from parts.models import TblPartModel, Tblpartslist
import datetime

from django.contrib.messages import get_messages

from django.core.files import File


# test FilteredJobListView
@pytest.mark.django_db
def test_filtered_job_list_view_requires_login(client):
    url = reverse("jobs:jobs_list")
    response = client.get(url)
    assert response.status_code == 302


@pytest.mark.django_db
def test_filtered_job_list_view_permission_denied(client, user_setup):
    user = user_setup
    client.force_login(user)
    url = reverse("jobs:jobs_list")
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_filtered_job_list_view_renders(client, user_setup, jobs):
    jobs = jobs()
    job = jobs[0]
    customer = job.assetid.customerid

    user = user_setup
    user.customerid = customer
    permission = Permission.objects.get(codename="view_jobview")
    user.user_permissions.add(permission)
    user.save()

    client.force_login(user)

    url = reverse("jobs:jobs_list")
    response = client.get(url)

    assert response.status_code == 200
    assertTemplateUsed(response, "jobs/jobs_list.html")

    # test htmx request
    response = client.get(url, HTTP_HX_REQUEST="true")
    assert response.status_code == 200


# test JobUpdateView
@pytest.mark.django_db
def test_job_update_view_requires_login(client, job):
    job = 
    url = reverse(
        "jobs:job_update", kwargs={"pk": job.jobid}
    )  # Update to your actual URL name
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert "/login" in response.url.lower()  # Ensure it's going to the login page


@pytest.mark.django_db
def test_job_udpate_view_permission_denied(client, job, user_setup):
    job = Tbljob.objects.last()
    customerid = job.assetid.customerid
    user = user_setup
    user.customerid = customerid
    user.save()

    client.force_login(user)

    url = reverse("jobs:job_update", kwargs={"pk": job.jobid})
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_job_update_view_renders(client, job, user_setup):
    job = Tbljob.objects.last()
    customerid = job.assetid.customerid
    user = user_setup
    user.customerid = customerid
    user.save()

    client.force_login(user)

    permission = Permission.objects.get(codename='change_tbljob')
    user.user_permissions.add(permission)

    url = reverse("jobs:job_update", kwargs={"pk": job.jobid})
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, "jobs/update_job.html")


@pytest.mark.django_db
def test_job_update_view_post_successfully(client, job, user_setup):
    job = Tbljob.objects.last()
    customerid = job.assetid.customerid
    user = user_setup
    user.customerid = customerid
    user.save()

    client.force_login(user)

    permission = Permission.objects.get(codename='change_tbljob')
    user.user_permissions.add(permission)
    url = reverse("jobs:job_update", kwargs={"pk": job.jobid})
    response = client.post(
        url,
        data={
            "jobid": job.jobid,
            "jobenddate": "2025-05-07",
            "jobtypeid": job.jobtypeid.jobtypeid,
            "technicianid": job.technicianid.technicianid,
            "jobstatusid": job.jobstatusid.jobstatusid,
        },
    )

    job.refresh_from_db()
    assert job.jobenddate == datetime.date(2025, 5, 7)
    assert response.status_code == 302
    assert response.url == reverse("jobs:job_summary", kwargs={"pk": job.jobid})


# test JobCreateView


@pytest.mark.django_db
def test_job_create_view_requires_login(client):
    url = reverse("jobs:job_create")  # Update to your actual URL name
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert "/login" in response.url.lower()  # Ensure it's going to the login page


@pytest.mark.django_db
def test_job_create_view_permission_denied(client, user_setup):
    user = user_setup
    client.force_login(user)
    url = reverse("jobs:job_create")
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_job_create_view_renders(client, user_setup):
    asset = Tblassets.objects.last()
    customerid = asset.customerid
    user = user_setup
    user.customerid = customerid
    user.save()
    client.force_login(user)

    permission = Permission.objects.get(codename='add_tbljob')
    user.user_permissions.add(permission)

    url = reverse("jobs:job_create")
    query_params = urlencode({"assetid": asset.assetid})
    full_url = f"{url}?{query_params}"
    response = client.get(full_url)
    assert response.status_code == 200
    assert response.context["assetid"] == str(asset.assetid)


@pytest.mark.django_db
def test_job_create_view_post_successfully(client, user_setup):
    asset = Tblassets.objects.first()
    user = user_setup
    user.customerid = asset.customerid

    user.save()
    client.force_login(user)

    permission = Permission.objects.get(codename='add_tbljob')
    user.user_permissions.add(permission)

    url = reverse("jobs:job_create")
    query_params = urlencode({"assetid": asset.assetid})
    full_url = f"{url}?{query_params}"

    form = {
        "assetid": asset.assetid,
        "jobstatusid": Tbljobstatus.objects.last().jobstatusid,
        "technicianid": Tbltechnicianlist.objects.last().technicianid,
        "jobtypeid": Tbljobtypes.objects.last().jobtypeid,
    }
    response = client.post(full_url, form)
    created_job = Tbljob.objects.last()
    assert created_job.assetid.assetid == asset.assetid
    assert response.status_code == 302
    assert response.url == reverse("jobs:job_update", kwargs={"pk": created_job.jobid})

    # test quick job
    query_params = urlencode({"assetid": asset.assetid, "quickjob": "successful_ppm"})
    full_url = f"{url}?{query_params}"

    response = client.post(full_url, form)
    created_job = Tbljob.objects.last()
    assert created_job.assetid.assetid == asset.assetid
    assert response.status_code == 302
    assert response.url == reverse("jobs:job_update", kwargs={"pk": created_job.jobid})


# test JobDeleteView


@pytest.mark.django_db
def test_job_delete_view_requires_login(client, job):
    job = Tbljob.objects.last()
    url = reverse("jobs:job_delete", kwargs={"pk": job.jobid})
    response = client.get(url)
    assert response.status_code == 302
    assert "/login" in response.url.lower()


@pytest.mark.django_db
def test_job_delete_view_permission_denied(client, job, user_setup):
    user = user_setup
    client.force_login(user)
    job = Tbljob.objects.last()
    url = reverse("jobs:job_delete", kwargs={"pk": job.jobid})
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_job_delete_view_renders(client, job, user_setup):
    job = Tbljob.objects.last()
    customerid = job.assetid.customerid
    user = user_setup
    user.customerid = customerid
    user.save()
    client.force_login(user)

    permission = Permission.objects.get(codename='delete_tbljob')
    user.user_permissions.add(permission)

    url = reverse("jobs:job_delete", kwargs={"pk": job.jobid})

    response = client.get(url)
    assert response.status_code == 200
    assert response.context["view_type"] == "delete"
    assert response.context["title"] == f"Delete Job: {job.jobid}"


@pytest.mark.django_db
def test_job_delete_view_post_error(client, job, user_setup):
    asset = Tblassets.objects.first()
    user = user_setup
    user.customerid = asset.customerid
    user.save()
    client.force_login(user)

    permission = Permission.objects.get(codename='delete_tbljob')
    user.user_permissions.add(permission)

    created_job = Tbljob.objects.create(
        assetid=asset,
        jobstatusid=Tbljobstatus.objects.last(),
        technicianid=Tbltechnicianlist.objects.last(),
        jobtypeid=Tbljobtypes.objects.last(),
    )

    Tblpartsused.objects.create(
        jobid=created_job, partid=Tblpartslist.objects.last(), quantity=1, unitprice=100
    )

    url = reverse("jobs:job_delete", kwargs={"pk": created_job.jobid})
    response = client.post(url)
    assert response.status_code == 200
    assert Tbljob.objects.filter(pk=created_job.jobid).exists()


def test_job_delete_view_post_successfully(client, job, user_setup):
    asset = Tblassets.objects.first()
    user = user_setup
    user.customerid = asset.customerid
    user.save()
    client.force_login(user)

    permission = Permission.objects.get(codename='delete_tbljob')
    user.user_permissions.add(permission)

    created_job = Tbljob.objects.create(
        assetid=asset,
        jobstatusid=Tbljobstatus.objects.last(),
        technicianid=Tbltechnicianlist.objects.last(),
        jobtypeid=Tbljobtypes.objects.last(),
    )

    Tbltestscarriedout.objects.filter(jobid=created_job.jobid).delete()

    url = reverse("jobs:job_delete", kwargs={"pk": created_job.jobid})
    response = client.post(url)
    assert response.status_code == 204
    assert not Tbljob.objects.filter(pk=created_job.jobid).exists()


# test GenerateJobReportView
@pytest.mark.django_db
def test_generate_job_report_view_requires_login(client):
    url = reverse("jobs:gen_report")
    response = client.get(url)

    assert response.status_code == 302
    assert "/login" in response.url.lower()


@pytest.mark.django_db
def test_generate_job_report_view_permission_required(client, user_setup):
    client.force_login(user_setup)
    url = reverse("jobs:gen_report")
    response = client.get(url)

    assert response.status_code == 403


@pytest.mark.django_db
def test_generate_job_report_view_renders(client, user_setup):
    from assets.models import Tblcustomer

    url = reverse("jobs:gen_report")
    customer = Tblcustomer.objects.get(customerid=6)
    user = user_setup
    user.customerid = customer
    user.save()
    mocker.patch(
        "jobs.mixins.CustomerJobListPermissionMixin.has_permission", return_value=True
    )
    client.force_login(user)

    query_params = urlencode(
        {
            "customerid": customer.pk,
            "report_type": "service_report",
            "enddate_min": "2025-04-03",
        }
    )
    full_url = f"{url}?{query_params}"
    response = client.get(full_url)
    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"

    query_params = urlencode(
        {
            "customerid": customer.pk,
            "report_type": "job_list",
            "enddate_min": "2025-07-03",
        }
    )
    full_url = f"{url}?{query_params}"
    response = client.get(full_url)
    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"


@pytest.mark.django_db
def test_generate_job_report_view_renders_for_staff(client, user_setup):

    url = reverse("jobs:gen_report")
    user = user_setup
    user.is_staff = True
    user.save()

    mocker.patch(
        "jobs.mixins.CustomerJobListPermissionMixin.has_permission", return_value=True
    )
    client.force_login(user)

    query_params = urlencode(
        {"customerid": "1", "report_type": "service_report", "enddate_min": "2025-7-03"}
    )
    full_url = f"{url}?{query_params}"
    response = client.get(full_url)
    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"


@pytest.mark.django_db
def test_generate_job_report_view_renders_error(client, user_setup):
    from assets.models import Tblcustomer

    url = reverse("jobs:gen_report")
    customer = Tblcustomer.objects.get(customerid=0)
    user = user_setup
    user.customerid = customer
    user.save()
    mocker.patch(
        "jobs.mixins.CustomerJobListPermissionMixin.has_permission", return_value=True
    )
    client.force_login(user)

    full_url = f"{url}"
    response = client.get(full_url)
    assert response.status_code == 400

    # htmx request are redirected to full http

    full_url = f"{url}"
    response = client.get(full_url, HTTP_HX_REQUEST="true")
    assert response.status_code == 200


@pytest.mark.django_db
def test_service_report_reader_requires_login(client):
    url = reverse("jobs:report_scanner", kwargs={"temp_file_group": 1})
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert "/login" in response.url.lower()  # Ensure it's going to the login page


@pytest.mark.django_db
def test_service_report_reader_permission_required(client, user_setup):
    user = user_setup
    client.force_login(user)
    url = reverse("jobs:report_scanner", kwargs={"temp_file_group": 1})
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_service_report_reader_post(client, user_setup):
    user = user_setup
    mocker.patch(
        "jobs.mixins.CustomerJobPermissionMixin.has_permission", return_value=True
    )
    user.customerid = Tblassets.objects.first().customerid
    user.save()
    client.force_login(user)
    import os

    base_dir = os.path.dirname(__file__)

    image1_path = os.path.join(base_dir, "test_files", "service_report.pdf")

    with open(image1_path, "rb") as f:
        testfile = File(f)
        testFile = File(f, name=".jpg")
        image = TemporaryUpload.objects.create(
            user=user,
            file=testFile,
            file_size=testFile.size,
            mime_type="application/pdf",
        )
    group = image.group
    data = {"group": group}

    url = reverse("jobs:report_scanner", kwargs={"temp_file_group": group})
    response = client.post(url, data)
    assert response.status_code == 200
    assert "report_output" in response["HX-Redirect"]


@pytest.mark.django_db
def test_service_report_reader_post_incorrect_file_type(client, user_setup):
    user = user_setup
    mocker.patch(
        "jobs.mixins.CustomerJobPermissionMixin.has_permission", return_value=True
    )
    user.customerid = Tblassets.objects.first().customerid
    user.save()
    client.force_login(user)
    import os

    base_dir = os.path.dirname(__file__)

    image1_path = os.path.join(base_dir, "test_files", "delivery_note.jpeg")

    with open(image1_path, "rb") as f:
        testfile = File(f)
        testFile = File(f, name=".jpg")
        image = TemporaryUpload.objects.create(
            user=user, file=testFile, file_size=testFile.size, mime_type="image/jpeg"
        )
    group = image.group
    data = {"group": group}

    url = reverse("jobs:report_scanner", kwargs={"temp_file_group": group})
    response = client.post(url, data)
    assert response.status_code == 200

    assertTemplateUsed("partials/messages.html")
    error_messages = list(get_messages(response.wsgi_request))
    assert any(
        "Document does not contain service or calibration data" in str(message)
        for message in error_messages
    )


@pytest.mark.django_db
def test_service_report_output_requires_login(client):
    url = reverse("jobs:report_reader_output", kwargs={"temp_file_group": 1})
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert "/login" in response.url.lower()  # Ensure it's going to the login page


@pytest.mark.django_db
def test_service_report_output_permission_required(client, user_setup):
    user = user_setup
    client.force_login(user)
    url = reverse("jobs:report_reader_output", kwargs={"temp_file_group": 1})
    response = client.get(url)
    assert response.status_code == 403
