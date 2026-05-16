from dataclasses import dataclass
from django.db.models import Model

@dataclass
class Action:
    key: str
    header:str
    label: str
    enabled: bool = True
    obj: Model | None = None
    open_url: str | None = None
    action_url: str | None = None
    color: str = 'secondary'

