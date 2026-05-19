from django.urls import reverse
from urllib.parse import urlencode
from .context import BaseDocumentContextBuilder
from .context_action import Action
from assets.models import (
    Tblassets,
)


def temp_group_params(temp_group_id):
    if not temp_group_id:
        return {}
    return urlencode({'temp_group_id': temp_group_id})


def get_fully_matched_asset(data, temp_group_id=None):
    query_params = temp_group_params(temp_group_id)
    output = []

    asset_id = data.get("asset", {}).get("asset_id")
    asset = Tblassets.objects.filter(pk=asset_id).first()
    if asset:
        output.append(
            Action(
                key=f"open_{asset}",
                header='Asset Found',
                label=f"Open {asset}",
                obj=asset,
                enabled=True,
                base_url=reverse("assets:view_asset"),
                open_url=f"{reverse("assets:view_asset")}?{query_params}",
                color='success'
            )
        )
    return output


def get_partially_matched_asset(data, temp_group_id=None):
    query_params = temp_group_params(temp_group_id)
    output = []

    asset_id = data.get("asset", {}).get("asset_id")
    asset_ids = data.get("asset", {}).get("assets")
    # remove fully matched asset from partially matched list
    if asset_id:
        asset_ids.remove(asset_id)

    if asset_ids:
        assets = Tblassets.objects.filter(pk__in=asset_ids)
        for asset in assets:
            output.append(
                Action(
                    key=f"open_{asset}",
                    header='Partially Matched Asset',
                    label=f"Open {asset}",
                    obj=asset,
                    enabled=True,
                    open_url=f"{reverse("assets:view_asset", kwargs={'pk': asset.pk})}?{query_params}",
                    color='secondary'
                )
            )
    return output


class NonStaffContext(
    BaseDocumentContextBuilder
):

    def get_payload(self):
        return self.resolved_data.get('delivery', {})

    def template_name(self):
        return 'documents/document_processor/asset_data_actions.html'

    def get_extra_context(self):
        return {
                'fully_matched_asset': get_fully_matched_asset(
                    self.resolved_data,  self.get_temp_group_id()
                ),
                'partially_matched_assets': get_partially_matched_asset(
                    self.resolved_data,  self.get_temp_group_id()
                ),

        }
