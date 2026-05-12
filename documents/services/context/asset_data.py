from django.urls import reverse
from urllib.parse import urlencode
from .context import BaseDocumentContextBuilder
from .context_action import Action


def gtin_actions(temp_group_id, data):
    output = []
    if data.get("gtin", {}).get("add_gtin"):
        base_url = reverse("model_information:create_model")
        query_params = urlencode(
            {'temp_group_id': temp_group_id}
        )
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
        query_params = urlencode(
            {'temp_group_id': temp_group_id}
        )
        output.append(
            Action(
                key="create_spare_part",
                label="Create Spare Part",
                enabled=True,
                action_url=f"{base_url}?{query_params}",
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
        }
