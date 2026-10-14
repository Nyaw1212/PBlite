from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any
from uuid import uuid4


def new_id() -> str:
    return str(uuid4())


@dataclass
class SelectedMaterial:
    catalog_number: str
    description: str = ""
    price: float = 0.0
    inventory_category: str = "VAN"
    supplier: str = ""
    vendor_code: str = ""
    quantity: float = 1.0

    @classmethod
    def from_catalog(cls, item: dict[str, Any], quantity: float = 1.0) -> "SelectedMaterial":
        return cls(
            catalog_number=str(item.get("CatalogNumber", "")).strip(),
            description=str(item.get("Description", "")).strip(),
            price=float(item.get("Price", 0) or 0),
            inventory_category=str(item.get("InventoryCategory", "VAN")).strip().upper() or "VAN",
            supplier=str(item.get("Supplier", "")).strip(),
            vendor_code=str(item.get("VendorCode", "")).strip(),
            quantity=float(quantity or 0),
        )


@dataclass
class Run:
    id: str = field(default_factory=new_id)
    name: str = ""
    length_ft: float = 0.0
    conduit: SelectedMaterial | None = None
    wires: list[SelectedMaterial] = field(default_factory=list)
    fittings: list[SelectedMaterial] = field(default_factory=list)

    def total_wire_length(self) -> float:
        return max(0, self.length_ft) + 4


@dataclass
class Gutter:
    id: str = field(default_factory=new_id)
    name: str = ""
    length_ft: float = 0.0
    included_run_ids: list[str] = field(default_factory=list)
    fittings: list[SelectedMaterial] = field(default_factory=list)


@dataclass
class Project:
    version: int = 1
    project_name: str = ""
    address: str = ""
    model: str = ""
    electrician: str = ""
    lender: str = ""
    runs: list[Run] = field(default_factory=list)
    gutters: list[Gutter] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
