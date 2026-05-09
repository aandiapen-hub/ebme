from abc import ABC, abstractmethod
from collections import defaultdict
import json


class BaseActionResolver(ABC):
    def __init__(self, temp_group_pk, data):
        self.actions = defaultdict(list)
        self.temp_group_pk = str(temp_group_pk)
        self.data = data

    def resolve(self):
        self.build_actions()
        for action_list in self.actions.values():
            for action in action_list:
                action.payload_json = json.dumps(action.payload)
        return dict(self.actions)

    @abstractmethod
    def build_actions(self):
        pass
