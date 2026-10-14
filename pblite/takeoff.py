from __future__ import annotations

from collections import defaultdict

from .models import Project, SelectedMaterial


def used_materials(project: Project) -> list[SelectedMaterial]:
    totals: dict[tuple[str, str], SelectedMaterial] = {}

    def add(material: SelectedMaterial | None, quantity: float) -> None:
        if not material or not material.catalog_number:
            return
        category = material.inventory_category.upper() or "VAN"
        key = (category, material.catalog_number)
        if key not in totals:
            totals[key] = SelectedMaterial(**material.__dict__)
            totals[key].quantity = 0
        totals[key].quantity += float(quantity or 0)

    for run in project.runs:
        if run.conduit:
            add(run.conduit, run.length_ft * run.conduit.quantity)
        for wire in run.wires:
            add(wire, run.total_wire_length() * wire.quantity)
        for fitting in run.fittings:
            add(fitting, fitting.quantity)

    runs_by_id = {run.id: run for run in project.runs}
    for gutter in project.gutters:
        for run_id in gutter.included_run_ids:
            run = runs_by_id.get(run_id)
            if not run:
                continue
            for wire in run.wires:
                add(wire, gutter.length_ft * wire.quantity)
        for fitting in gutter.fittings:
            add(fitting, fitting.quantity)

    order = {"BOS": 0, "VAN": 1}
    return sorted(totals.values(), key=lambda item: (order.get(item.inventory_category.upper(), 2), item.catalog_number))


def material_total(materials: list[SelectedMaterial]) -> float:
    return sum(item.quantity * item.price for item in materials)
