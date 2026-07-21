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


def get_gtin_actions(data, temp_group_id=None):
    query_params = temp_group_params(temp_group_id)
    gtin = data.get("gtin", {}).get("add_gtin", None)
    items = []

    actions = []
    if gtin:
        actions.append(
            Action(
                label='Add as a Model',
                enabled=True,
                url = f'{reverse("model_information:create_model")}?{query_params}',
                color='primary'
            )
        )

        actions.append(
            Action(
                label='Add as a Part',
                enabled=True,
                url = f'{reverse("parts:create_part")}?{query_params}',
                color='primary'
            )
        )
        items += [ MatchedItem(
            item_type='GTIN',
            title='GTIN not recognised',
            description='',
            obj=None,
            actions=actions
        ) ]
    return items


def get_model(data, temp_group_id=None):
    model_id = data.get("model", {}).get("model_id")
    if model_id:
        model = Tblmodel.objects.get(pk=model_id)
        actions = []
        actions.append(
            Action(
                label='Open',
                enabled=True,
                url=reverse('model_information:model_view', kwargs={'pk': model.pk}),
                color='primary'
            )
        )
        item = MatchedItem(
            item_type='model',
            title=f"{model}",
            description='',
            obj=model,
            actions=actions
        )
        return [item] 
    return []

def get_part(data, temp_group_id=None):
    part_id = data.get("part", {}).get("part_id")
    if part_id:
        part = Tblpartslist.objects.get(pk=part_id)
        actions = []
        actions.append(
            Action(
                label='Open',
                enabled=True,
                url=reverse('parts:part_detail', kwargs={'pk': part.pk}),
                color='primary'
            )
        )
        item = MatchedItem(
            item_type='part',
            title=f"{part}",
            description='',
            obj=part,
            actions=actions
        )
        return [item] 
    return []

def get_models_without_gtin(data, temp_group_id=None):
    query_params = temp_group_params(temp_group_id)

    model_ids_without_gtin = data.get("model", {}).get("models_without_gtin", {})
    models_without_gtin = Tblmodel.objects.filter(
        pk__in=model_ids_without_gtin,
        gtin__isnull=True,
    )
    items = []
    if models_without_gtin:
        for model in models_without_gtin:
            actions = []
            actions.append(
                Action(
                    label='Open',
                    enabled=True,
                    url=reverse('model_information:model_view', kwargs={'pk': model.pk}),
                    color='secondary'
                )
            )
            actions.append(
                Action(
                    label='Update',
                    enabled=True,
                    url=f"{reverse('model_information:update_model', kwargs={'pk': model.pk})}?{query_params}",
                    color='primary'
                )
            )
            items += [MatchedItem(
                item_type='Model without GTIN',
                title=f"{model}",
                description='',
                obj=model,
                actions=actions
            )]
    return items 

def get_duplicatable_models(data, temp_group_id=None):
    query_params = temp_group_params(temp_group_id)
    duplicatable_models_id = data.get("model", {}).get("duplicatable_models", {})
    items = []
    if duplicatable_models_id:
        duplicatable_models = Tblmodel.objects.filter(
            pk__in=duplicatable_models_id
        )
        for model in duplicatable_models:
            actions = []
            actions.append(
                Action(
                    label='Open',
                    enabled=True,
                    url=reverse('model_information:model_view', kwargs={'pk': model.pk}),
                    color='secondary'
                )
            )
            actions.append(
                Action(
                    label='Copy',
                    enabled=True,
                    url=f"{reverse('model_information:update_model', kwargs={'pk': model.pk})}?{query_params}",
                    color='primary'
                )
            )
            items += [ MatchedItem(
                item_type='Model',
                title=f"{model}",
                description='',
                obj=model,
                actions=actions
            ) ]

    return items


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
        actions.append(
            Action(
                label='Update',
                enabled=True,
                url=f"{reverse("assets:update_asset", kwargs={'pk':asset.pk})}?{query_params}",
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
                    color='secondary'
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


def get_create_asset(data, temp_group_id=None):
    query_params = temp_group_params(temp_group_id)
    items = []

    asset = data.get("asset", {})
    has_no_asset_id = not asset.get("asset_id")
    has_serial = bool(asset.get("serialnumber"))

    if has_no_asset_id and has_serial:
    
        action = Action(
                label='Create',
                enabled=True,
                url=f"{reverse("assets:create_asset")}?{query_params}",
                color='primary'
            )
        items += [ MatchedItem(
            item_type='Asset',
            title="Create Asset",
            description='Create Asset using the extracted information',
            obj=None,
            actions=[action]
        ) ]
    return items

def get_key_information(data):
    output = {}
    serialno = data.get('asset',{}).get('serialnumber')
    if serialno:
        output.update({
            'Serial no': serialno 
            })

    gtin = data.get('gtin',{}).get('value')
    if gtin: 
        output.update({
            'GTIN': gtin 
            })

    return output

class AssetDataContext(
    BaseDocumentContextBuilder
):

    def template_name(self):
       return 'documents/document_processor/asset_data.html' 

    def get_extra_context(self):
        temp_group = self.get_temp_group_id()

        exact_match_group = MatchedGroup(
            title='Exact Matches',
            confidence='Full',
            items=[],
            color='success')
        exact_match_group.items += get_fully_matched_asset(
            self.resolved_data,  self.get_temp_group_id()
        )
        exact_match_group.items += get_model(
            self.resolved_data,  self.get_temp_group_id()
        )
        exact_match_group.items += get_part(
            self.resolved_data,  self.get_temp_group_id()
        )

        suggested_actions = MatchedGroup(
            title='Recommended Actions',
            confidence='Full',
            items=[],
            color='primary')
 
        suggested_actions.items += get_create_asset(
                self.resolved_data,  temp_group
        )
        suggested_actions.items += get_gtin_actions(
                    self.resolved_data, temp_group
                )

        partial_matches = MatchedGroup(
            title='Partial Matches (matched on serial number only)',
            confidence='partial',
            items=[],
            color='secondary')

        partial_matches.items += get_partially_matched_asset(
                self.resolved_data,  temp_group
        )

        partial_matches.items += get_models_without_gtin(
                self.resolved_data,  temp_group
        )

        partial_matches.items += get_duplicatable_models(
                self.resolved_data,  temp_group
        )

        

        return {
            'key_data_extracted': get_key_information(self.resolved_data),
            'groups': [
                suggested_actions,
                exact_match_group,
                partial_matches,
            ]}


