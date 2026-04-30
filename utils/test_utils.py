
import pytest
from django.urls import reverse
from assets.models import JobView
import html

from django.db.models import DateField, JSONField
from utils.generic_filters import get_filter_fields 

from django.contrib.auth.models import Permission

URL = reverse("jobs:jobs_list")
GET_TEMPLATE = "jobs/jobs_list.html"
PERMISSION = 'view_jobview'
FK_FIELD = 'modelid'
TEXT_FIELD = 'brandname'
DATE_FIELD = 'startdate'
NUMERIC_FIELD = 'total_cost'
#CHOICE_FIELD = 'status_id'
MODEL = JobView


def context_has_field(response, field_name):
    # Iterate through all context layers
    for layer in response.context:
        # RequestContext or dict
        dicts_to_check = getattr(layer, "dicts", [layer])  # layer.dicts if exists, else layer itself
        for d in dicts_to_check:
            if field_name in d:
                return True
    return False


@pytest.mark.django_db
def test_filtered_table_view_get_success(client, user_setup):
    # --- Setup user and permissions ---
    user = user_setup
    permission = Permission.objects.filter(codename=PERMISSION).last()
    user.user_permissions.add(permission)

    client.force_login(user)


    # --- Test normal GET ---
    response = client.get(URL)
    assert response.status_code == 200
    assert GET_TEMPLATE in [t.name for t in response.templates]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "lookup",
    get_filter_fields(MODEL, [FK_FIELD])[FK_FIELD]["lookups"]
)
def test_filtered_table_view_add_filter_fk(client, user_setup, lookup):
    # --- Setup user and permission ---
    user = user_setup
    permission = Permission.objects.filter(codename=PERMISSION).last()
    user.user_permissions.add(permission)
    client.force_login(user)

    # --- Prepare test data ---

    filter_name = f"{FK_FIELD}__{lookup}"

    response = client.get(
        URL,
        {"new_active_filter": filter_name},
        HTTP_HX_REQUEST="true"
    )

    assert response.status_code == 200
    assert f'name="{filter_name}"' in response.content.decode()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "lookup",
    get_filter_fields(MODEL, [TEXT_FIELD])[TEXT_FIELD]["lookups"]
)
def test_filtered_table_view_add_filter_text(client, user_setup, lookup):
    # --- Setup user and permission ---
    user = user_setup
    permission = Permission.objects.filter(codename=PERMISSION).last()
    user.user_permissions.add(permission)
    client.force_login(user)

    # --- Prepare test data ---

    filter_name = f"{TEXT_FIELD}__{lookup}"

    response = client.get(
        URL,
        {"new_active_filter": filter_name},
        HTTP_HX_REQUEST="true"
    )

    assert response.status_code == 200
    assert f'name="{filter_name}"' in response.content.decode()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "lookup",
    get_filter_fields(MODEL, [DATE_FIELD])[DATE_FIELD]["lookups"]
)
def test_filtered_table_view_add_filter_date(client, user_setup, lookup):
    # --- Setup user and permission ---
    user = user_setup
    permission = Permission.objects.filter(codename=PERMISSION).last()
    user.user_permissions.add(permission)
    client.force_login(user)

    # --- Prepare test data ---

    filter_name = f"{DATE_FIELD}__{lookup}"

    response = client.get(
        URL,
        {"new_active_filter": filter_name},
        HTTP_HX_REQUEST="true"
    )

    assert response.status_code == 200
    if lookup == 'range':
        assert f'name="{DATE_FIELD}__range__lte"' in response.content.decode()
    else:
        assert f'name="{filter_name}"' in response.content.decode()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "lookup",
    get_filter_fields(MODEL, [NUMERIC_FIELD])[NUMERIC_FIELD]["lookups"]
)
def test_filtered_table_view_add_filter_numeric(client, user_setup, lookup):
    # --- Setup user and permission ---
    user = user_setup
    permission = Permission.objects.filter(codename=PERMISSION).last()
    user.user_permissions.add(permission)
    client.force_login(user)

    # --- Prepare test data ---

    filter_name = f"{NUMERIC_FIELD}__{lookup}"

    response = client.get(
        URL,
        {"new_active_filter": filter_name},
        HTTP_HX_REQUEST="true"
    )

    assert response.status_code == 200
    assert f'name="{filter_name}"' in response.content.decode()


@pytest.mark.django_db
def test_filtered_table_view_get_universal_search_result(client, user_setup):
    # --- Setup user and permissions ---
    user = user_setup
    permission = Permission.objects.filter(codename=PERMISSION).last()
    user.user_permissions.add(permission)

    client.force_login(user)

    # --- Prepare test data ---

    # --- Test normal GET ---
    response = client.get(
        URL,
        {'universal_search': '12'},
    )
    assert response.status_code == 200


@pytest.mark.django_db
@pytest.mark.parametrize(
    "summary_field",
    [
        FK_FIELD,
        TEXT_FIELD,
        DATE_FIELD,
        NUMERIC_FIELD,
    ],
)
def test_filtered_table_view_get_summary_field(
    client,
    user_setup,
    summary_field,
):
    # --- Setup user and permissions ---
    user = user_setup
    permission = Permission.objects.filter(codename=PERMISSION).last()
    user.user_permissions.add(permission)
    user.is_staff = True
    user.save()
    client.force_login(user)


    # --- Perform request ---
    response = client.get(
        URL,
        {"summary_field": summary_field},
    )
    

    assert response.status_code == 200

    content = response.content.decode()

    # --- Validate that expected values appear in response ---
    values = MODEL.objects.all().values_list(summary_field, flat=True)
    field = MODEL._meta.get_field(summary_field)

    if isinstance(field, JSONField) or isinstance(field, DateField):
        assert 'Lookup not available for this field' in content
    else:
        for value in values:
            if value is not None:
                assert str(value) in html.unescape(response.text)
