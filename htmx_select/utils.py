from dataclasses import dataclass

@dataclass(frozen=True)
class PickerDependency:
    field: str
    lookup: str

@dataclass(frozen=True)
class HtmxPicker:
    enabled: bool = True
    search_terms: tuple[str, ...] = ()
    label_str: str | None = None
    customer_scope: str | None = None
    dependency: tuple[PickerDependency, ...] =()
