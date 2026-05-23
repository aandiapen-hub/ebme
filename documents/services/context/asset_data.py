from functools import partial
from django.urls import reverse
from urllib.parse import urlencode
from .context import BaseDocumentContextBuilder
from .context_action import Action
from assets.models import (
    Tblmodel,
    Tblassets,
)


def temp_group_params(temp_group_id):
    if not temp_group_id:
        return {}
    return urlencode({'temp_group_id': temp_group_id})


def get_gtin_actions(data, temp_group_id=None):
    output = []
    query_params = temp_group_params(temp_group_id)

    if data.get("gtin", {}).get("add_gtin"):
        base_url = reverse("model_information:create_model")
        # create model
        output.append(
            Action(
                key="create_model",
                header="Unknown GTIN",
                label="Add as Model",
                obj=data.get("gtin", {}).get("value"),
                enabled=True,
                action_url=f"{base_url}?{query_params}",
                color='warning'
            )
        )
        # create spare parts
        base_url = reverse("parts:create_part")
        output.append(
            Action(
                key="create_spare_part",
                header="Unknown GTIN",
                label="Add as Spare Part",
                obj=data.get("gtin", {}).get("value"),
                enabled=True,
                action_url=f"{base_url}?{query_params}",
                color='warning'
                )
            )

        return output


def get_model(data, temp_group_id=None):
    output = []

    model_id = data.get("model", {}).get("model_id")
    if model_id:
        model = Tblmodel.objects.get(pk=model_id)
        output.append(
            Action(
                key="open_model",
                header="Exact Model Found",
                label="Open",
                obj=model,
                enabled=True,
                open_url=reverse('model_information:model_view', kwargs={'pk': model.pk}),
                color='success',
                )
            )

        return output


def get_models_without_gtin(data, temp_group_id=None):
    query_params = temp_group_params(temp_group_id)
    output = []

    model_ids_without_gtin = data.get("model", {}).get("models_without_gtin", {})
    models_without_gtin = Tblmodel.objects.filter(
        pk__in=model_ids_without_gtin,
        gtin__isnull=True,
    )
    if models_without_gtin:
        for model in models_without_gtin:
            output.append(
                Action(
                    key=f"update_model_{model}",
                    header="Partial Model Matches",
                    label=f"Update {model}",
                    obj=model,
                    enabled=True,
                    action_url=f"{reverse('model_information:update_model', kwargs={'pk': model.pk})}?{query_params}",
                    open_url=f"{reverse('model_information:model_view', kwargs={'pk': model.pk})}?{query_params}",
                    color='secondary'
                )
            )
    return output


def get_duplicatable_models(data, temp_group_id=None):
    query_params = temp_group_params(temp_group_id)
    output = []
    duplicatable_models_id = data.get("model", {}).get("duplicatable_models", {})
    if duplicatable_models_id:
        duplicatable_models = Tblmodel.objects.filter(
            pk__in=duplicatable_models_id
        )
        for model in duplicatable_models:
            output.append(
                Action(
                    key=f"clone_model_{model}",
                    header="Similar model with different GTIN",
                    label=f"Copy Model: {model} with new GTIN",
                    obj=model,
                    enabled=True,
                    action_url=f"{reverse('model_information:update_model', kwargs={'pk': model.pk})}?{query_params}",
                    open_url=f"{reverse('model_information:model_view', kwargs={'pk': model.pk})}?{query_params}",
                    color='secondary'
                )
            )
    return output


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


def get_create_asset(data, temp_group_id=None):
    output = []
    query_params = temp_group_params(temp_group_id)
    print(data)

    output.append(
        Action(
            key="create_asset",
            header='Exact Asset not found',
            label="Create New Asset",
            enabled=True,
            action_url=f"{reverse("assets:create_asset")}?{query_params}",
            color='warning'
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
        temp_group = self.get_temp_group_id()
        gtin_actions = None
        models_without_gtin = None
        
        partially_matched_asset = None
        create_asset = None

        fully_matched_model = get_model(
                    self.resolved_data,  self.get_temp_group_id()
                )
        fully_matched_asset = get_fully_matched_asset(
                    self.resolved_data,  self.get_temp_group_id()
                )

        if not fully_matched_asset and self.resolved_data.get('asset', {}).get('serialnumber', None):
            create_asset = get_create_asset(
                    self.resolved_data,  temp_group
                )
            partially_matched_asset = get_partially_matched_asset(
                    self.resolved_data, temp_group 
                )

        if not fully_matched_model:
            gtin_actions = get_gtin_actions(
                    self.resolved_data, temp_group
                )
            models_without_gtin = get_models_without_gtin(
                    self.resolved_data, temp_group 
                )

        return {
                'gtin_actions': gtin_actions,
                'fully_matched_model': fully_matched_asset,
                'duplicatable_models': get_duplicatable_models(
                    self.resolved_data, temp_group 
                ),
                'models_without_gtin': models_without_gtin,
                'fully_matched_asset':  fully_matched_asset ,
                'partially_matched_assets': partially_matched_asset,
                'create_asset': create_asset
        }
