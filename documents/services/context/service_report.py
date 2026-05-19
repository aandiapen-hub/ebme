from urllib.parse import urlencode
from .context import BaseDocumentContextBuilder
from django.shortcuts import reverse
from assets.models import Tblassets


def temp_group_params(temp_group_id):
    if not temp_group_id:
        return {}
    return urlencode({'temp_group_id': temp_group_id})


def get_assets_from_resolved_data(data, temp_group_id=None):
    asset_ids = data.get('asset', {}).get('assets', [])
    qs = Tblassets.objects.filter(pk__in=asset_ids).prefetch_related('jobs')
    create_url = reverse('jobs:job_create')
    query_params = temp_group_params(temp_group_id)
    url = f"{create_url}?{query_params}"

    for asset in qs:
        asset.create_job_url = url

        for job in asset.jobs.all():
            update_url = reverse('jobs:job_update', kwargs={'pk': job.pk})
            job.update_url = f"{update_url}?{query_params}"

    return qs


class ServiceReportContext(
    BaseDocumentContextBuilder
):

    def get_payload(self):
        return self.resolved_data.get('job', {})

    def template_name(self):
        return 'documents/document_processor/service_report_actions.html'

    def get_extra_context(self):
        return {
            'assets': get_assets_from_resolved_data(
                self.resolved_data, self.get_temp_group_id()
            )

        }
