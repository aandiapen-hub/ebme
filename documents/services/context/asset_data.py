from django.urls import reverse
from urllib.parse import urlencode
from .context import BaseDocumentContextBuilder
from .context_action import Action
from assets.models import (
    Tblmodel,
    Tblassets,
)


def gtin_actions(temp_group_id, data):
    output = []
    query_params = urlencode(
        {'temp_group_id': temp_group_id}
    )

    if data.get("gtin", {}).get("add_gtin"):
        base_url = reverse("model_information:create_model")
        # create model
        output.append(
            Action(
                key="create_model",
                label="Create Model",
                enabled=True,
                action_url=f"{base_url}?{query_params}",
            )
        )
        # create spare parts
        base_url = reverse("parts:create_part")
        output.append(
            Action(
                key="create_spare_part",
                label="Create Spare Part",
                enabled=True,
                action_url=f"{base_url}?{query_params}",
                )
            )

        return output


def get_model(temp_group_id, data):
    output = []
    query_params = urlencode(
        {'temp_group_id': temp_group_id}
    )

    model_id = data.get("model", {}).get("model_id")
    if model_id:
        model = Tblmodel.objects.get(pk=model_id)
        base_url = reverse('model_information:model_view', kwargs={'pk': model.pk})
        output.append(
            Action(
                key="open_model",
                label="Model Found",
                enabled=True,
                action_url=f"{base_url}?{query_params}",
                )
            )

        return output


def get_models_without_gtin(temp_group_id, data):
    query_params = urlencode(
        {'temp_group_id': temp_group_id}
    )
    output = []

    model_ids_without_gtin = data.get("model", {}).get("models_without_gtin", {})
    models_without_gtin = Tblmodel.objects.filter(pk__in=model_ids_without_gtin)
    if models_without_gtin is None:
        for model in models_without_gtin:
            output.append(
                Action(
                    key=f"update_model_{model}",
                    label=f"Update {model}",
                    obj=model,
                    enabled=True,
                    action_url=f"{reverse('model_information:update_model', kwargs={'pk': model.pk})}?{query_params}",
                    open_url=f"{reverse('model_information:model_view', kwargs={'pk': model.pk})}?{query_params}",
                )
            )
    return output

def get_models_with_gtin(temp_group_id, data):
    query_params = urlencode(
        {'temp_group_id': temp_group_id}
    )
    output = []
    models_with_gtin = data.get("model", {}).get("models_with_gtin", {})
    if models_with_gtin is None:
        for model in models_with_gtin:
            output.append(
                Action(
                    key=f"update_model_{model}",
                    label=f"Update {model}",
                    obj=model,
                    enabled=True,
                    action_url=f"{reverse('model_information:update_model', kwargs={'pk': model.pk})}?{query_params}",
                    open_url=f"{reverse('model_information:model_view', kwargs={'pk': model.pk})}?{query_params}",
                )
            )

    return output


def get_fully_matched_asset(temp_group_id, data):
    query_params = urlencode(
        {'temp_group_id': temp_group_id}
    )
    output = []

    asset_id = data.get("asset", {}).get("asset_id")
    asset = Tblassets.objects.filter(pk=asset_id).first()
    if asset:
        output.append(
            Action(
                key=f"open_{asset}",
                label=f"Open {asset}",
                obj=asset,
                enabled=True,
                base_url=reverse("assets:view_asset"),
                open_url=f"{reverse("assets:view_asset")}?{query_params}",
            )
        )
    return output


def get_partially_matched_asset(temp_group_id, data):
    query_params = urlencode(
        {'temp_group_id': temp_group_id}
    )
    output = []

    asset_id = data.get("asset", {}).get("asset_id")
    asset_ids = data.get("asset", {}).get("assets")
    # remove fully matched asset from partially matched list
    if asset_id:
        asset_ids.remove(asset_id)

    assets = Tblassets.objects.filter(pk__in=asset_ids)
    for asset in assets:
        output.append(
            Action(
                key=f"open_{asset}",
                label=f"Open {asset}",
                obj=asset,
                enabled=True,
                open_url=f"{reverse("assets:view_asset")}?{query_params}",
            )
        )
    return output


def create_asset(temp_group_id, data):
    query_params = urlencode(
        {'temp_group_id': temp_group_id}
    )
    output = []

    output.append(
        Action(
            key="create_asset",
            label="Create New Asset",
            enabled=True,
            action_url=f"{reverse("assets:create_asset")}?{query_params}",
        )
    )
    return output


class AssetDataContext(
    BaseDocumentContextBuilder
):

    def get_payload(self):
        return self.resolved_data.get('delivery', {})

    def template_name(self):
        return 'documents/document_processor/asset_data_actions.html'

    def get_extra_context(self):
        return {
                'gtin_actions': gtin_actions(
                    self.temp_group.pk, self.resolved_data
                ),
                'fully_matched_model': get_model(
                    self.temp_group.pk, self.resolved_data
                ),
                'models_with_gtin': get_models_with_gtin(
                    self.temp_group.pk, self.resolved_data
                ),
                'models_without_gtin': get_models_without_gtin(
                    self.temp_group.pk, self.resolved_data
                ),
                'fully_matched_asset': get_fully_matched_asset(
                    self.temp_group.pk, self.resolved_data
                ),
                'partially_matched_assets': get_partially_matched_asset(
                    self.temp_group.pk, self.resolved_data
                ),
                'create_asset': create_asset(
                    self.temp_group.pk, self.resolved_data
                ),

        }
