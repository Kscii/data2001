#!/usr/bin/env python3
"""Strip notebook outputs and reset execution counts.

Usage:
    uv run python scripts/nbclean.py              # clean all notebooks under notebooks/
    uv run python scripts/nbclean.py notebooks/full_workflow.ipynb
    uv run python scripts/nbclean.py notebooks/xfan0282
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
NOTEBOOKS_DIR = PROJECT_ROOT / "notebooks"

_VOLATILE_CELL_METADATA = {"collapsed", "scrolled", "execution", "jupyter"}


def clean_notebook(path: Path) -> bool:
    """Strip outputs and reset execution counts. Return True if file was changed."""
    raw = path.read_text(encoding="utf-8")
    nb = json.loads(raw)

    changed = False
    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "code":
            continue

        if cell.get("execution_count") is not None:
            cell["execution_count"] = None
            changed = True

        if cell.get("outputs"):
            cell["outputs"] = []
            changed = True

        cell_meta = cell.get("metadata", {})
        volatile = _VOLATILE_CELL_METADATA & set(cell_meta)
        for key in volatile:
            del cell_meta[key]
        if volatile:
            changed = True

    if changed:
        path.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"cleaned: {path.relative_to(PROJECT_ROOT)}")
    else:
        print(f"already clean: {path.relative_to(PROJECT_ROOT)}")
    return changed


def resolve_targets(args: list[str]) -> list[Path]:
    """Resolve CLI arguments into notebook files.

    With no arguments, only notebooks under notebooks/ are cleaned. File arguments
    clean that single notebook; directory arguments clean notebooks recursively.
    """
    if not args:
        return sorted(NOTEBOOKS_DIR.rglob("*.ipynb"))

    targets: list[Path] = []
    for arg in args:
        path = Path(arg)
        if not path.is_absolute():
            path = PROJECT_ROOT / path

        if path.is_dir():
            targets.extend(sorted(path.rglob("*.ipynb")))
        elif path.suffix == ".ipynb":
            targets.append(path)
        else:
            raise ValueError(f"target is not a notebook or directory: {path}")

    return sorted(dict.fromkeys(targets))


def main() -> None:
    targets = resolve_targets(sys.argv[1:])

    if not targets:
        print("no notebooks found")
        return

    total_changed = sum(clean_notebook(p) for p in targets)
    print(f"\n{total_changed}/{len(targets)} notebook(s) cleaned")


if __name__ == "__main__":
    main()
