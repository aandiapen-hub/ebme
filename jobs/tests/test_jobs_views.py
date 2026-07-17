from urllib.parse import urlencode

from django.contrib.auth.models import Permission
import pytest
from django.urls import reverse
from pytest_django.asserts import assertTemplateUsed
from assets.models import (
    Tbljob,
    Tblpartsused,
)



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
def test_filtered_job_list_view_non_staff_with_no_customer(client, user_setup, jobs):
    jobs = jobs()

    user = user_setup
    user.customerid = None
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
    table = response.context['table']
    assert table.data.data.count() == 0

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
    job = job()
    url = reverse(
        "jobs:job_update", kwargs={"pk": job.jobid}
    )  # Update to your actual URL name
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert "/login" in response.url.lower()  # Ensure it's going to the login page


@pytest.mark.django_db
def test_job_udpate_view_permission_denied(client, job, user_setup):
    job = job()
    user = user_setup
    user.customerid = job.assetid.customerid
    user.save()

    client.force_login(user)

    url = reverse("jobs:job_update", kwargs={"pk": job.jobid})
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_job_update_view_renders(client, job, user_setup):
    job = job()
    user = user_setup
    user.customerid = job.assetid.customerid
    user.save()

    client.force_login(user)

    permission = Permission.objects.get(codename="change_tbljob")
    user.user_permissions.add(permission)

    url = reverse("jobs:job_update", kwargs={"pk": job.jobid})
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, "jobs/update_job.html")


@pytest.mark.django_db
def test_job_update_view_post_successfully(
    client,
    job,
    user_setup,
    test_eq,
    check,
    check_result,
    active_spare_part,
):
    job = job()
    part = active_spare_part
    test_eq = test_eq
    check = check()
    user = user_setup
    user.customerid = job.assetid.customerid
    user.save()

    client.force_login(user)

    permission = Permission.objects.get(codename="change_tbljob")
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
            # test_eq formset
            "test_eq-TOTAL_FORMS": "1",
            "test_eq-INITIAL_FORMS": "0",
            "test_eq-MIN_NUM_FORMS": "0",
            "test_eq-MAX_NUM_FORMS": "1000",
            "test_eq-0-id": "",
            "test_eq-0-test_eq": test_eq.pk,
            # checklist formset
            "checklist-TOTAL_FORMS": "1", "checklist-INITIAL_FORMS": "0",
            "checklist-MIN_NUM_FORMS": "0",
            "checklist-MAX_NUM_FORMS": "1000",
            "checklist-0-testid": "",
            "checklist-0-checkid": check.pk,
            "checklist-0-resultid": check_result().pk,
            # parts_used formset
            "parts_used-TOTAL_FORMS": "1",
            "parts_used-INITIAL_FORMS": "0",
            "parts_used-MIN_NUM_FORMS": "0",
            "parts_used-MAX_NUM_FORMS": "1000",
            "parts_used-0-partsusedid": "",
            "parts_used-0-partid": part.pk,
            "parts_used-0-quantity": "1",
            "parts_used-0-unitprice": "",
        },
    )

    job.refresh_from_db()
    assert part.pk in job.parts_used.values_list("partid", flat=True)
    assert test_eq.pk in job.test_eq_used.values_list("test_eq", flat=True)
    assert check.pk in job.test_carried_out.values_list("checkid", flat=True)

    assert response.url == reverse("jobs:job_summary", kwargs={"pk": job.jobid})

@pytest.mark.django_db
def test_job_update_view_post_integrity_error(
    client,
    job,
    user_setup,
    test_eq,
    check,
    check_result,
    active_spare_part,
):
    job = job()
    part = active_spare_part
    test_eq = test_eq
    check = check()
    user = user_setup
    user.customerid = job.assetid.customerid
    user.save()

    client.force_login(user)

    permission = Permission.objects.get(codename="change_tbljob")
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
            # test_eq formset
            "test_eq-TOTAL_FORMS": "1",
            "test_eq-INITIAL_FORMS": "0",
            "test_eq-MIN_NUM_FORMS": "0",
            "test_eq-MAX_NUM_FORMS": "1000",
            "test_eq-0-id": "",
            "test_eq-0-test_eq": test_eq.pk,
            # checklist formset
            "checklist-TOTAL_FORMS": "1",
            "checklist-INITIAL_FORMS": "0",
            "checklist-MIN_NUM_FORMS": "0",
            "checklist-MAX_NUM_FORMS": "1000",
            "checklist-0-testid": "",
            "checklist-0-checkid": check.pk,
            "checklist-0-resultid": check_result().pk,
            # parts_used formset
            "parts_used-TOTAL_FORMS": "1",
            "parts_used-INITIAL_FORMS": "0",
            "parts_used-MIN_NUM_FORMS": "0",
            "parts_used-MAX_NUM_FORMS": "1000",
            "parts_used-0-partsusedid": "",
            "parts_used-0-partid": part.pk,
            "parts_used-0-quantity": "-1",
            "parts_used-0-unitprice": "",
        },
    )

    assert response.status_code == 200
    assert response.context['parts_used'].errors


@pytest.mark.django_db
def test_job_update_view_post_formset_error(
    client,
    job,
    user_setup,
    test_eq,
    check,
    check_result,
):
    job = job()
    test_eq = test_eq
    check = check()
    user = user_setup
    user.customerid = job.assetid.customerid
    user.save()

    client.force_login(user)

    permission = Permission.objects.get(codename="change_tbljob")
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
            # test_eq formset
            "test_eq-TOTAL_FORMS": "1",
            "test_eq-INITIAL_FORMS": "0",
            "test_eq-MIN_NUM_FORMS": "0",
            "test_eq-MAX_NUM_FORMS": "1000",
            "test_eq-0-id": "",
            "test_eq-0-test_eq": test_eq.pk,
            # checklist formset
            "checklist-TOTAL_FORMS": "1",
            "checklist-INITIAL_FORMS": "0",
            "checklist-MIN_NUM_FORMS": "0",
            "checklist-MAX_NUM_FORMS": "1000",
            "checklist-0-testid": "",
            "checklist-0-checkid": check.pk,
            "checklist-0-resultid": check_result().pk,
            # parts_used formset
            "parts_used-TOTAL_FORMS": "1",
            "parts_used-INITIAL_FORMS": "0",
            "parts_used-MIN_NUM_FORMS": "0",
            "parts_used-MAX_NUM_FORMS": "1000",
            "parts_used-0-partsusedid": "",
            "parts_used-0-unitprice": "",
        },
    )

    assert response.status_code == 200
    assert response.context['parts_used'].errors


@pytest.mark.django_db
def test_job_detail_view_requires_login(client, job):
    job = job()
    url = reverse("jobs:job_summary", kwargs={'pk': job.pk})  
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert "/login" in response.url.lower()  # Ensure it's going to the login page


@pytest.mark.django_db
def test_job_detail_view_permission_denied(client, user, job):
    job = job()
    user = user()
    client.force_login(user)
    url = reverse("jobs:job_summary", kwargs={'pk': job.pk})  
    response = client.get(url)
    assert response.status_code == 403

@pytest.mark.django_db
def test_job_detail_view_no_job(client, user, job, customer):
    job = job()
    customer = customer()
    job.assetid.customerid = customer
    job.assetid.save()

    user = user()
    permission = Permission.objects.get(codename="view_jobview")
    user.user_permissions.add(permission)
    user.customerid = customer
    user.save()

    client.force_login(user)
    url = reverse("jobs:job_summary", kwargs={'pk': job.pk+1})  
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_job_update_view_post_database_error(
    client,
    job,
    user_setup,
    test_eq,
    check,
    check_result,
    active_spare_part
):
    job = job()
    test_eq = test_eq
    check = check()
    part = active_spare_part
    user = user_setup
    user.customerid = job.assetid.customerid
    user.save()

    client.force_login(user)

    permission = Permission.objects.get(codename="change_tbljob")
    user.user_permissions.add(permission)
    url = reverse("jobs:job_update", kwargs={"pk": job.jobid})
    response = client.post(
        url,
        data={
            "jobid": job.jobid,
            "jobenddate": "2025-05-07",
            "jobstartdate": "2025-06-07",
            "jobtypeid": job.jobtypeid.jobtypeid,
            "technicianid": job.technicianid.technicianid,
            "jobstatusid": job.jobstatusid.jobstatusid,
            # test_eq formset
            "test_eq-TOTAL_FORMS": "1",
            "test_eq-INITIAL_FORMS": "0",
            "test_eq-MIN_NUM_FORMS": "0",
            "test_eq-MAX_NUM_FORMS": "1000",
            "test_eq-0-id": "",
            "test_eq-0-test_eq": test_eq.pk,
            # checklist formset
            "checklist-TOTAL_FORMS": "1",
            "checklist-INITIAL_FORMS": "0",
            "checklist-MIN_NUM_FORMS": "0",
            "checklist-MAX_NUM_FORMS": "1000",
            "checklist-0-testid": "",
            "checklist-0-checkid": check.pk,
            "checklist-0-resultid": check_result().pk,
            # parts_used formset
            "parts_used-TOTAL_FORMS": "1",
            "parts_used-INITIAL_FORMS": "0",
            "parts_used-MIN_NUM_FORMS": "0",
            "parts_used-MAX_NUM_FORMS": "1000",
            "parts_used-0-partsusedid": "",
            "parts_used-0-partid": part.pk,
            "parts_used-0-quantity": "1",
            "parts_used-0-unitprice": "",
        },
    )

    assert response.status_code == 200
    assert response.context['form'].errors

@pytest.mark.django_db
def test_job_detail_view_renders_non_staff_no_customer_user(client, user, job, customer):
    job = job()

    user = user()
    permission = Permission.objects.get(codename="view_jobview")
    user.user_permissions.add(permission)
    user.customerid = None 
    user.save()

    client.force_login(user)
    url = reverse("jobs:job_summary", kwargs={'pk': job.pk})  
    response = client.get(url)
    assert response.status_code == 403

@pytest.mark.django_db
def test_job_detail_view_renders_for_customer(client, user, job, customer):
    job = job()
    customer = customer()
    job.assetid.customerid = customer
    job.assetid.save()

    user = user()
    permission = Permission.objects.get(codename="view_jobview")
    user.user_permissions.add(permission)
    user.customerid = customer
    user.save()

    client.force_login(user)
    url = reverse("jobs:job_summary", kwargs={'pk': job.pk})  
    response = client.get(url)
    assert response.status_code == 200

@pytest.mark.django_db
def test_job_detail_view_renders_for_staff(client, user, job, customer):
    job = job()
    customer = customer()
    job.assetid.customerid = customer
    job.assetid.save()

    user = user()
    permission = Permission.objects.get(codename="view_jobview")
    user.user_permissions.add(permission)
    user.is_staff = True 
    user.save()

    client.force_login(user)
    url = reverse("jobs:job_summary", kwargs={'pk': job.pk})  
    response = client.get(url)
    assert response.status_code == 200

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
def test_job_create_view_renders(client, user_setup, asset):
    asset = asset()
    customerid = asset.customerid
    user = user_setup
    user.customerid = customerid
    user.save()
    client.force_login(user)

    permission = Permission.objects.get(codename="add_tbljob")
    user.user_permissions.add(permission)

    url = reverse("jobs:job_create")
    query_params = urlencode({"assetid": asset.assetid})
    full_url = f"{url}?{query_params}"
    response = client.get(full_url)
    assert response.status_code == 200
    assert response.context["assetid"] == str(asset.assetid)


@pytest.mark.django_db
def test_job_create_view_post_successfully(
    client, user_setup, asset, jobtype, jobstatus, technician
):

    asset = asset()
    user = user_setup
    user.customerid = asset.customerid

    user.save()
    client.force_login(user)

    permission = Permission.objects.get(codename="add_tbljob")
    user.user_permissions.add(permission)

    url = reverse("jobs:job_create")
    query_params = urlencode({"assetid": asset.assetid})
    full_url = f"{url}?{query_params}"

    form = {
        "assetid": asset.pk,
        "jobenddate": "2025-05-07",
        "jobtypeid": jobtype().pk,
        "technicianid": technician().pk,
        "jobstatusid": jobstatus().pk,
    }
    response = client.post(full_url, form)

    created_job = Tbljob.objects.last()
    assert created_job.assetid.assetid == asset.assetid
    assert response.status_code == 302
    assert response.url == reverse("jobs:job_update", kwargs={"pk": created_job.jobid})

    # test quick job
    jobstatus = jobstatus(jobstatusname="Completed")
    jobstype = jobtype(jobtypename="PPM")
    query_params = urlencode({"assetid": asset.assetid, "quickjob": "successful_ppm"})
    full_url = f"{url}?{query_params}"

    response = client.post(full_url, form)
    created_job = Tbljob.objects.last()
    assert created_job.assetid.assetid == asset.assetid
    assert response.status_code == 302
    assert response.url == reverse("jobs:job_update", kwargs={"pk": created_job.jobid})


@pytest.mark.django_db
def test_job_create_view_post_incorrect_customer(
    client, user_setup, asset, customer, jobtype, jobstatus, technician
):

    asset = asset()
    user = user_setup
    user.customerid = customer() 

    user.save()
    client.force_login(user)

    permission = Permission.objects.get(codename="add_tbljob")
    user.user_permissions.add(permission)

    url = reverse("jobs:job_create")
    query_params = urlencode({"assetid": asset.assetid})
    full_url = f"{url}?{query_params}"

    form = {
        "assetid": asset.pk,
        "jobenddate": "2025-05-07",
        "jobtypeid": jobtype().pk,
        "technicianid": technician().pk,
        "jobstatusid": jobstatus().pk,
    }
    response = client.post(full_url, form)
    assert response.status_code == 403 


@pytest.mark.django_db
def test_job_create_view_non_existent_asset(
    client, user_setup, asset, customer, jobtype, jobstatus, technician
):

    asset = asset()
    user = user_setup
    user.customerid = customer() 

    user.save()
    client.force_login(user)

    permission = Permission.objects.get(codename="add_tbljob")
    user.user_permissions.add(permission)

    url = reverse("jobs:job_create")
    query_params = urlencode({"assetid": asset.assetid})
    full_url = f"{url}?{query_params}"

    form = {
        "assetid": '3389',
        "jobenddate": "2025-05-07",
        "jobtypeid": jobtype().pk,
        "technicianid": technician().pk,
        "jobstatusid": jobstatus().pk,
    }
    response = client.post(full_url, form)
    assert response.status_code == 403 

@pytest.mark.django_db
def test_job_create_view_post_invalid_form(
    client, user_setup, asset, jobtype, jobstatus, technician
):

    asset = asset()
    user = user_setup
    user.customerid = asset.customerid

    user.save()
    client.force_login(user)

    permission = Permission.objects.get(codename="add_tbljob")
    user.user_permissions.add(permission)

    url = reverse("jobs:job_create")

    form = {
        "jobenddate": "2025-05-07",
        "technicianid": technician().pk,
        "jobstatusid": jobstatus().pk,
    }


    response = client.post(url, form)
    assert response.context['form'].errors

# test JobDeleteView

@pytest.mark.django_db
def test_job_delete_view_requires_login(client, job):
    job = job()
    url = reverse("jobs:job_delete", kwargs={"pk": job.jobid})
    response = client.get(url)
    assert response.status_code == 302
    assert "/login" in response.url.lower()


@pytest.mark.django_db
def test_job_delete_view_permission_denied(client, job, user_setup):
    user = user_setup
    client.force_login(user)
    job = job()
    url = reverse("jobs:job_delete", kwargs={"pk": job.jobid})
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_job_delete_view_renders(client, job, user_setup):
    job = job()
    customerid = job.assetid.customerid
    user = user_setup
    user.customerid = customerid
    user.save()
    client.force_login(user)

    permission = Permission.objects.get(codename="delete_tbljob")
    user.user_permissions.add(permission)

    url = reverse("jobs:job_delete", kwargs={"pk": job.jobid})

    response = client.get(url)
    assert response.status_code == 200
    assert response.context["view_type"] == "delete"
    assert response.context["title"] == f"Delete Job: {job.jobid}"


@pytest.mark.django_db
def test_job_delete_view_post_error(
    client, active_spare_part, customer, job, user_setup
):
    job = job()
    part = active_spare_part
    user = user_setup
    user.customerid = job.assetid.customerid
    user.save()
    client.force_login(user)

    permission = Permission.objects.get(codename="delete_tbljob")
    user.user_permissions.add(permission)

    Tblpartsused.objects.create(jobid=job, partid=part, quantity=1, unitprice=100)

    url = reverse("jobs:job_delete", kwargs={"pk": job.jobid})
    response = client.post(url)
    assert response.status_code == 200
    assert Tbljob.objects.filter(pk=job.jobid).exists()


def test_job_delete_view_post_successfully(client, job, user_setup):
    job = job()
    user = user_setup
    user.customerid = job.assetid.customerid
    user.save()
    client.force_login(user)

    permission = Permission.objects.get(codename="delete_tbljob")
    user.user_permissions.add(permission)

    url = reverse("jobs:job_delete", kwargs={"pk": job.jobid})
    response = client.post(url)
    assert response.status_code == 204
    assert not Tbljob.objects.filter(pk=job.jobid).exists()


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
def test_generate_job_report_view_renders(client, user_setup, jobs):
    jobs = jobs()
    customer = jobs[0].assetid.customerid
    user = user_setup
    user.customerid = customer
    user.save()
    permission = Permission.objects.get(codename="genreport_tbljob")
    user.user_permissions.add(permission)

    client.force_login(user)

    url = reverse("jobs:gen_report")
    query_params = urlencode(
        {"customerid": customer.pk, "report_type": "service_report"}
    )

    full_url = f"{url}?{query_params}"
    response = client.get(full_url)
    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"


@pytest.mark.django_db
def test_generate_job_report_view_renders_htmx(client, user_setup, jobs):
    jobs = jobs()
    customer = jobs[0].assetid.customerid
    user = user_setup
    user.customerid = customer
    user.save()
    permission = Permission.objects.get(codename="genreport_tbljob")
    user.user_permissions.add(permission)

    client.force_login(user)

    url = reverse("jobs:gen_report")
    query_params = urlencode(
        {"customerid": customer.pk, "report_type": "service_report"}
    )

    full_url = f"{url}?{query_params}"
    response = client.get(full_url, HTTP_HX_REQUEST='true')
    assert response.status_code == 200
    assert response['HX-Redirect'] == full_url 

@pytest.mark.django_db
def test_generate_job_report_view_renders_for_staff(client, user_setup, jobs):
    jobs = jobs()

    url = reverse("jobs:gen_report")
    user = user_setup
    user.is_staff = True
    user.save()

    permission = Permission.objects.get(codename="genreport_tbljob")
    user.user_permissions.add(permission)
    client.force_login(user)

    url = reverse("jobs:gen_report")
    query_params = urlencode(
        {
            "report_type": "service_report",
        }
    )
    full_url = f"{url}?{query_params}"
    response = client.get(full_url)
    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"


@pytest.mark.django_db
def test_generate_job_report_view_renders_error(client, customer, user, jobs):
    jobs = jobs(count=302)
    customer = customer(customer_name="test")
    user = user()
    user.is_staff = True
    user.save()

    permission = Permission.objects.get(codename="genreport_tbljob")
    user.user_permissions.add(permission)

    client.force_login(user)

    url = reverse("jobs:gen_report")
    query_params = urlencode(
        {
            "report_type": "service_report",
        }
    )
    full_url = f"{url}?{query_params}"
    response = client.get(full_url)
    assert response.status_code == 400


# test Add formset
@pytest.mark.django_db
def test_generate_test_eq_list_view_requires_login(client, assets, asset_status):
    asset_status = asset_status(asset_status_id=1)
    test_eq = assets(count=10, is_test_eq=True, asset_status_id=asset_status)
    url = reverse("jobs:test_eq_list", kwargs={'formset_type':'test_eq'})
    response = client.get(url)

    assert response.status_code == 302
    assert "/login" in response.url.lower()


@pytest.mark.django_db
def test_generate_test_eq_listview_permission_required(client, user):
    client.force_login(user())
    url = reverse("jobs:test_eq_list", kwargs={'formset_type':'test_eq'})
    response = client.get(url)

    assert response.status_code == 403


@pytest.mark.django_db
def test_generate_test_eq_listview_renders(client, user, assets, asset_status):
    asset_status = asset_status(asset_status_id=1)

    test_eq = assets(count=10, is_test_eq=True, asset_status_id=asset_status)
    user = user()
    permission = Permission.objects.get(codename="change_tbljob")
    user.user_permissions.add(permission)
    client.force_login(user)
    
    url = reverse("jobs:test_eq_list", kwargs={'formset_type':'test_eq'})
    response = client.get(url)

    assert response.status_code == 200
    assert response.context['object_list'].count() == 10


# test add parts formset
@pytest.mark.django_db
def test_generate_parts_list_view_requires_login(client):
    url = reverse("jobs:parts_list", kwargs={'formset_type':'parts_used'})
    response = client.get(url)

    assert response.status_code == 302
    assert "/login" in response.url.lower()


@pytest.mark.django_db
def test_generate_parts_list_permission_required(client, user):
    client.force_login(user())
    url = reverse("jobs:parts_list", kwargs={'formset_type':'parts_used'})
    response = client.get(url)

    assert response.status_code == 403


@pytest.mark.django_db
def test_generate_parts_list_view_renders(client, user, asset, part_model):
    asset = asset()

    part1_model = part_model(model=asset.modelid)
    part2_model = part_model(model=asset.modelid)
    part3_model = part_model(model=asset.modelid)

    user = user()
    permission = Permission.objects.get(codename="change_tbljob")
    user.user_permissions.add(permission)
    client.force_login(user)
    
    url = reverse("jobs:parts_list", kwargs={'formset_type':'parts_used'})
    query_params = urlencode({'modelid':asset.modelid.pk})
    full_url = f"{url}?{query_params}"
    response = client.get(full_url)

    assert response.status_code == 200
    assert response.context['object_list'].count() == 3


# test add check formset
@pytest.mark.django_db
def test_generate_check_list_view_requires_login(client, asset):
    asset = asset()
    url = reverse("jobs:check_list", kwargs={'formset_type':'checklist'})
    response = client.get(url)

    assert response.status_code == 302
    assert "/login" in response.url.lower()


@pytest.mark.django_db
def test_generate_check_list_permission_required(client, user, asset):
    asset = asset()
    client.force_login(user())
    url = reverse("jobs:check_list", kwargs={'formset_type':'checklist'})
    response = client.get(url)

    assert response.status_code == 403


@pytest.mark.django_db
def test_generate_check_list_view_renders(client, user, asset, checklists):
    asset = asset()
    checkllists = checklists(count=10, modelid=asset.modelid) 
    user = user()
    permission = Permission.objects.get(codename="change_tbljob")
    user.user_permissions.add(permission)
    client.force_login(user)
    
    url = reverse("jobs:check_list", kwargs={'formset_type':'checklist'})
    query_params = urlencode({'formset_type': 'checklist'})
    full_url = f"{url}?{query_params}"
    response = client.get(full_url)

    assert response.status_code == 200
    assert response.context['object_list'].count() == 10
