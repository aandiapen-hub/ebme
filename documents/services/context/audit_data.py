from django.urls import reverse
from urllib.parse import urlencode

from parts.models import Tblpartslist
from .context import BaseDocumentContextBuilder
from .context_action import(
    Action,
    MatchedGroup,
    MatchedItem,
)
from assets.models import (
    Tblmodel,
    Tblassets,
)


def temp_group_params(temp_group_id):
    return urlencode({'temp_group_id': temp_group_id})


def get_fully_matched_asset(data, temp_group_id=None):
    query_params = temp_group_params(temp_group_id)
    asset_id = data.get("asset", {}).get("asset_id")
    items = [] 
    asset = Tblassets.objects.filter(pk=asset_id).first()
    if asset:
        actions = []
        actions.append(
            Action(
                label='Open',
                enabled=True,
                url=f"{reverse("assets:view_asset", kwargs={'pk':asset.pk})}?{query_params}",
                color='primary'
            )
        )
        items += [ MatchedItem(
            item_type='Asset',
            title=f"{asset}",
            description=f'{asset.modelid}-{asset.serialnumber}',
            obj=asset,
            actions=actions
        ) ]
    return items 

def get_partially_matched_asset(data, temp_group_id=None):
    query_params = temp_group_params(temp_group_id)
    items = []

    asset_id = data.get("asset", {}).get("asset_id")
    asset_ids = data.get("asset", {}).get("assets", [])
    # remove fully matched asset from partially matched list
    asset_ids = [x for x in asset_ids if x != asset_id]

    if asset_ids:
        assets = Tblassets.objects.filter(pk__in=asset_ids)
        for asset in assets:
            actions = []
            actions.append(
                Action(
                    label='Open',
                    enabled=True,
                    url=f"{reverse("assets:view_asset", kwargs={'pk': asset.pk})}?{query_params}",
                    color='outline-secondary'
                )
            )
            actions.append(
                Action(
                    label='Update',
                    enabled=True,
                    url=f"{reverse("assets:update_asset", kwargs={'pk': asset.pk})}?{query_params}",
                    color='warning'
                )
            )
            items += [ MatchedItem(
                item_type='Asset',
                title=f"{asset}",
                description=f'{asset.modelid}-{asset.serialnumber}',
                obj=asset,
                actions=actions
            ) ]
    return items


def get_create_audit_item(data, audit_location_id, temp_group_id=None):
    query_params = temp_group_params(temp_group_id)
    items = []

    asset_data = data.get("asset", {})
    model_id = bool(asset_data.get("model_id"))
    gtin = data.get("gtin", {}).get("add_gtin", None)


    if asset_data.get('create_asset'):

        action = Action(
                label='Suggest New Asset',
                enabled=True,
            url=f"{reverse("audits:new_asset_create", kwargs={'pk': audit_location_id})}?{query_params}",
                color='warning'
            )
        items += [ MatchedItem(
            item_type='Asset',
            title="Suggest New Asset",
            description='Suggest New item',
            obj=None,
            actions=[action]
        ) ]
    return items


class AuditDataContext(
    BaseDocumentContextBuilder
):


    def template_name(self):
       return 'documents/document_processor/asset_data.html' 

    def get_extra_context(self):
        temp_group = self.get_temp_group_id

        exact_match_group = MatchedGroup(
            title='Exact Matches',
            confidence='Full',
            items=[],
            color='success')
        exact_match_group.items += get_fully_matched_asset(
            self.resolved_data,  self.get_temp_group_id
        )

        suggested_actions = MatchedGroup(
            title='Recommended Actions',
            confidence='Full',
            items=[],
            color='primary')
 
        suggested_actions.items += get_create_audit_item(
                self.resolved_data,  audit_location_id=self.temp_group.audit_location.pk, temp_group_id=temp_group
        )

        partial_matches = MatchedGroup(
            title='Partial Matches (matched on serial number only)',
            confidence='partial',
            items=[],
            color='secondary')

        partial_matches.items += get_partially_matched_asset(
                self.resolved_data,  temp_group
        )

        return {
            'groups': [
                suggested_actions,
                exact_match_group,
                partial_matches,
            ]}


