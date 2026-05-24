from dataclasses import dataclass
from typing import Any

@dataclass
class Action:
    label: str
    obj: Any | None = None # Any django model instance
    enabled: bool = True
    color: str = 'secondary'
    url: str | None = None

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




