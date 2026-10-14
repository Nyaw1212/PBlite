from __future__ import annotations

import json
from pathlib import Path

from .models import Gutter, Project, Run, SelectedMaterial


def app_data_dir() -> Path:
    """Return a user-owned folder that survives app restarts and updates."""
    base = Path(__import__("os").environ.get("LOCALAPPDATA", Path.home()))
    folder = base / "PanelBuilderLite"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def catalog_cache_path() -> Path:
    return app_data_dir() / "material_catalog.json"


def save_cached_catalog(catalog: list[dict]) -> None:
    catalog_cache_path().write_text(json.dumps(catalog, ensure_ascii=False, default=str), encoding="utf-8")


def load_cached_catalog() -> list[dict]:
    path = catalog_cache_path()
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else []


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
