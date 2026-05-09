from .action import Action
from .base_action_resolver import BaseActionResolver


class ServiceReportActionResolver(
    BaseActionResolver
):
    def build_actions(self):
        self.service_report_actions()

    def service_report_actions(self):
        # Log Service Report
        if self.data.get('job', {}).get("create_job", None):
            self.actions["job"].append(
                Action(
                    key="log_service_report",
                    label="Log Report",
                    enabled=True,
                    route_name="documents:log_service_report",
                    pk=self.temp_group_pk,
                    payload=self.data,
                )
            )
