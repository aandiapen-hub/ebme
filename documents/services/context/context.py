from abc import ABC, abstractmethod


class BaseDocumentContextBuilder(ABC):

    def __init__(self, temp_group):
        self.temp_group = temp_group
        self.resolved_data = temp_group.extracted_json.get('resolved', {})

    def build(self):
        print('resolved data', self.get_extra_context())
        return {
            'payload': self.get_payload(),
            'template_name': self.template_name(),
            **self.get_extra_context(),
        }

    @abstractmethod
    def get_payload(self):
        pass

    @abstractmethod
    def template_name(self):
        pass

    def get_extra_context(self):
        pass
