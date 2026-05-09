from dataclasses import dataclass


@dataclass
class Action:
    key: str
    label: str
    enabled: True 
    route_name: str
    pk: str | None = None
    payload: dict | None = None

