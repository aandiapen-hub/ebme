from .action import Action
from .base_action_resolver import BaseActionResolver


class AssetActionResolver(
    BaseActionResolver
):

    def build_actions(self):
        self.gtin_actions()
        self.model_actions()
        self.asset_actions()

    # -------------
    # GTIN Actions
    # -------------

    def gtin_actions(self):
        if self.data.get("gtin", {}).get("add_gtin"):
            # create model
            self.actions["gtin"].append(
                Action(
                    key="create_model",
                    label="Create Model",
                    enabled=True,
                    route_name="model_information:create_model",
                    payload={
                        "temp_group_pk": self.temp_group_pk,
                        "gtin": self.data.get("gtin").get("value"),
                        "modelname": self.data.get("model").get("name_options"),
                        "brandname": self.data.get("brand").get("brand_options"),
                        "brandid": self.data.get("brand").get("brand_ids"),
                        "categoryname": self.data.get("model").get(
                            "category_options"
                        ),
                        "categoryid": self.data.get("category").get("category_ids"),
                    },
                )
            )
            # create spare parts
            self.actions["gtin"].append(
                Action(
                    key="create_spare_part",
                    label="Create Spare Part",
                    enabled=True,
                    route_name="parts:create_part",
                    payload={
                        "temp_group_pk": self.temp_group_pk,
                        "gtin": self.data.get("gtin").get("value")
                    },
                )
            )

    # -------------
    # Model Actions
    # -------------
    def model_actions(self):
        # update existing model
        models_without_gtin = self.data.get("model", {}).get("models_without_gtin", {})
        if models_without_gtin is None:
            for model in models_without_gtin:
                self.actions["model"].append(
                    Action(
                        key=f"update_model_{model}",
                        label=f"Update {model}",
                        enabled=True,
                        route_name="model_information:update_model",
                        pk=model,
                        payload={
                            "temp_group_pk": self.temp_group_pk,
                            "gtin": self.data.get("gtin").get("value"),
                        },
                    )
                )

        models_with_gtin = self.data.get("model", {}).get("models_with_gtin", {})
        if models_with_gtin is None:
            for model in models_with_gtin:
                self.actions["model"].append(
                    Action(
                        key=f"update_model_{model}",
                        label=f"Update {model}",
                        enabled=True,
                        route_name="model_information:update_model",
                        pk=model,
                        payload={
                            "temp_group_pk": self.temp_group_pk,
                        },
                    )
                )

    # -------------
    # Asset Actions
    # -------------

    def asset_actions(self):
        # Open Asset
        asset_id = self.data.get("asset", {}).get("asset_id")
        if asset_id is not None:
            self.actions["asset"].append(
                Action(
                    key="open_asset",
                    label="Open Asset",
                    enabled=True,
                    route_name="assets:view_asset",
                    pk=asset_id,
                    payload={
                        "temp_group_pk": self.temp_group_pk,
                        "pk": asset_id,
                    },
                )
            )

        # Open partially matched Asset
        asset_ids = self.data.get("asset", {}).get("assets")
        if asset_id:
            asset_ids.remove(asset_id)
        for asset in asset_ids:
            self.actions["asset"].append(
                Action(
                    key="open_partially_matched_assets",
                    label=f"{repr(asset)}",
                    enabled=True,
                    route_name="assets:view_asset",
                    pk=asset,
                    payload={
                        "temp_group_pk": self.temp_group_pk,
                    },
                )
            )

        # Create Asset
        if self.data.get("asset", {}).get("create_asset"):
            self.actions["asset"].append(
                Action(
                    key="create_asset",
                    label="Create Asset",
                    enabled=True,
                    route_name="assets:create_asset",
                    payload={
                        "temp_group_pk": self.temp_group_pk,
                        "gtin": self.data.get("gtin", {}).get("value"),
                        "modelid": self.data.get("model", {}).get("model_id"),
                        "serialnumber": self.data.get("asset", {}).get("serial"),
                        "customerassetnumber": self.data.get("asset", {}).get(
                            "asset_no"
                        ),
                        "prod_date": self.data.get("asset", {}).get("prod_date"),
                    },
                )
            )

