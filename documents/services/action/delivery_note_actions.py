from .action import Action
from .base_action_resolver import BaseActionResolver


class DeliveryNoteActionResolver(
    BaseActionResolver
):
    def build_actions(self):
        self.delivery_note_actions()

    def delivery_note_actions(self):
        if self.data.get('delivery').get('create_delivery', False):
            self.actions["delivery"].append(
                Action(
                    key="log_delivery_note",
                    label="Log Delivery Note",
                    enabled=True,
                    route_name="documents:log_service_report",
                    pk=self.temp_group_pk,
                    payload=self.data,
                )
            )
