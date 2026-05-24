from dataclasses import dataclass
from typing import Any

@dataclass
class Action:
    label: str
    enabled: bool = True
    url: str | None = None
    color: str = 'secondary'

@dataclass
class MatchedItem:
    item_type: str
    title: str
    description: str
    obj: Any # Any django model instance
    actions: list[Action]

@dataclass
class MatchedGroup:
    title: str
    confidence: str
    color: str
    items: list[MatchedItem]




