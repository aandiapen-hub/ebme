from urllib.parse import urlencode
from .context import BaseDocumentContextBuilder
from django.shortcuts import reverse
from assets.models import Tblassets

from .context_action import(
    Action,
    MatchedGroup,
    MatchedItem,
)

def temp_group_params(temp_group_id):
    if not temp_group_id:
        return {}
    return urlencode({'temp_group_id': temp_group_id})


def get_assets_from_resolved_data(data, temp_group_id=None):
    query_params = temp_group_params(temp_group_id)
    items = []

    asset_ids = data.get('asset', {}).get('assets', [])
    qs = Tblassets.objects.filter(pk__in=asset_ids).prefetch_related('jobs')

    for asset in qs:
        actions = []

        actions.append(
                Action(
                    label='Create New Job',
                    enabled=True,
                    url=f"{reverse('jobs:job_create')}?{query_params}",
                    color='primary'
                )
        )
        for job in asset.jobs.all():
            actions.append(
                Action(
                    label=f'Update Job:{job} - {job.jobstatusid} (Start:{job.jobstartdate}, End:{job.jobenddate})',
                    enabled=True,
                    url = f"{reverse('jobs:job_update', kwargs={'pk': job.pk})}?{query_params}",
                    color='primary',
                )
        )
        

        items += [ MatchedItem(
            item_type='Asset',
            title=f"{asset}",
            description='Create or Update Job',
            obj=asset,
            actions=actions
        ) ]


    return items 


class ServiceReportContext(
    BaseDocumentContextBuilder
):
    def get_extra_context(self):
        assets = MatchedGroup(
            title='Assets',
            confidence='Partial',
            items=[],
            color='success')

        assets.items += get_assets_from_resolved_data(
                    self.resolved_data, self.get_temp_group_id()
                )


        return {
            'groups': [
                assets
            ]
        }
