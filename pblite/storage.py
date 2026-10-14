from __future__ import annotations

import json
from pathlib import Path

from .models import Gutter, Project, Run, SelectedMaterial


def _material(value: dict | None) -> SelectedMaterial | None:
    return SelectedMaterial(**value) if value else None


def _materials(values: list[dict]) -> list[SelectedMaterial]:
    return [SelectedMaterial(**value) for value in values or []]


def save_project(path: str | Path, project: Project) -> None:
    Path(path).write_text(json.dumps(project.to_dict(), indent=2), encoding="utf-8")


def load_project(path: str | Path) -> Project:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    runs = [
        Run(
            id=value.get("id", ""), name=value.get("name", ""), length_ft=float(value.get("length_ft", 0) or 0),
            conduit=_material(value.get("conduit")), wires=_materials(value.get("wires", [])), fittings=_materials(value.get("fittings", [])),
        )
        for value in data.get("runs", [])
    ]
    gutters = [
        Gutter(
            id=value.get("id", ""), name=value.get("name", ""), length_ft=float(value.get("length_ft", 0) or 0),
            included_run_ids=list(value.get("included_run_ids", [])), fittings=_materials(value.get("fittings", [])),
        )
        for value in data.get("gutters", [])
    ]
    return Project(
        version=int(data.get("version", 1)), project_name=data.get("project_name", ""), address=data.get("address", ""),
        model=data.get("model", ""), electrician=data.get("electrician", ""), lender=data.get("lender", ""),
        runs=runs, gutters=gutters,
    )
