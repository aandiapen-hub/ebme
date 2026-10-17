from dataclasses import dataclass, asdict

@dataclass
class KeyInformation:
    name: str
    value: str | None
    comment: str | None
    color: str
    icon: str

ICON_MAP = {
    'success': 'bi-check2',
    'warning': 'bi-exclamation-triangle',
    'danger': 'bi-exclamation-octagon-fill',
    'secondary':'bi-exclamation-triangle' 
}

def new_key_information(name, color, value=None, comment=None):
    return asdict(
        KeyInformation(
        name=name,
        color=color,
        value=value,
        comment=comment,
        icon=ICON_MAP.get(color, '')
        )
    )
