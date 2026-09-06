from .models import JobView
from django_filter_table.views import FilteredTableView
from django.utils import timezone

SEARCHFILEDS = [
    "modelid__modelname__icontains",
    "assetid__pk__icontains",
    "jobid__icontains",
]

class FilteredJobTableView(
    FilteredTableView
):
    paginate_by = 25
    title = "Jobs"
    permission_required = "assets.view_jobview"
    table_class = None
    model = JobView
    open_column = 'jobid'
    universal_search_fields = SEARCHFILEDS
    default_columns = [
        "assetid",
        "serialnumber",
        "jobtypeid",
        "jobstatusid",
        "modelid",
        "startdate",
        "enddate",
        "customerid",
    ]
    additional_filters = (
        "filter_latest_ppm",
    )
    quick_filters = {
        'completed_today': {
            'name':'Completed Today',
            'lookups': {"enddate": timezone.localdate()},
         },
    }
