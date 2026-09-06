from dataclasses import dataclass
@dataclass(frozen=True)
class PickerDependency:
    field: str
    lookup: str

@dataclass(frozen=True)
class HtmxPicker:
    enabled: bool = True # True
    search_terms: tuple[str, ...] = () # ('fieldname__icontains',)
    label_str: str | None = None  # lambda obj: f"{obj.modelname} ({obj.brandid})"
    customer_scope: str | None = None # 'customerid'
    dependency: tuple[PickerDependency, ...] =()
