from urllib.parse import urlencode
from .context import BaseDocumentContextBuilder
from django.shortcuts import reverse
from assets.models import(
    Tblassets,
    Tbljobstatus,
    Tbljobtypes,
    ) 

from .context_action import(
    Action,
    MatchedGroup,
    MatchedItem,
)

def temp_group_params(temp_group_id):
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
        
        items += [ MatchedItem(
            item_type='Asset',
            title=f"{asset}",
            description='Create or Update Job',
            obj=asset,
            actions=actions
        ) ]


    return items 


def get_key_information(data):
    output = {}
    serialno = data.get('asset',{}).get('serial')
    if serialno:
        output.update({
            'Serialno':  serialno
            })
    workdone = data.get('job',{}).get('workdone')
    if workdone:
        output.update({
            'Work Done':  workdone
            })
    jobenddate = data.get('job',{}).get('jobenddate')
    if jobenddate:
        output.update({
            'End Date':  jobenddate
            })
    jobtypeid = data.get('job',{}).get('jobtypeid')
    if jobtypeid:
        jobtype = Tbljobtypes.objects.get(pk=jobtypeid)
        output.update({
            'Type':  jobtype
            })
    jobstatusid = data.get('job',{}).get('jobstatusid')
    if jobstatusid:
        jobstatus = Tbljobstatus.objects.get(pk=jobstatusid)
        output.update({
            'Status':  jobstatus
            })

    return output

class ServiceReportContext(
    BaseDocumentContextBuilder
):

    def template_name(self):
       return 'documents/document_processor/service_report.html' 
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
            'key_data_extracted': get_key_information(self.resolved_data),
            'asset_groups': [
                assets
            ]
        }
