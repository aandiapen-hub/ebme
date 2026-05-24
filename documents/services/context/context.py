from abc import ABC, abstractmethod
from urllib.parse import urlencode


class BaseDocumentContextBuilder(ABC):

    def __init__(self, temp_group=None, resolved_data=None):
        self.temp_group = temp_group
        self.resolved_data = (
            resolved_data if resolved_data is not None
            else self._extract_resolved_data(temp_group)
        )

    def _extract_resolved_data(self, temp_group):
        if not temp_group:
            return {}
        return (
            temp_group.extracted_json.get('resolved', {})
        )

    def build(self):
        return {
            **self.get_extra_context(),
        }

    def group_pk_params(self):
        if self.temp_group and self.temp_group.pk:
            return urlencode({'temp_group_id': self.temp_group.pk})

    def get_temp_group_id(self):
        if self.temp_group:
            return self.temp_group.pk


    def get_extra_context(self):
        pass
