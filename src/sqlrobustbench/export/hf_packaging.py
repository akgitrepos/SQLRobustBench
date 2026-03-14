from __future__ import annotations

import json
from pathlib import Path

from sqlrobustbench.export.parquet_writer import write_rows_jsonl
from sqlrobustbench.types import BenchmarkRow


def hf_packaging_ready() -> bool:
    return True


def create_release_bundle(
    rows: list[BenchmarkRow],
    output_dir: str | Path,
    *,
    dataset_name: str = "SQLRobustBench",
) -> dict[str, str]:
    root = Path(output_dir)
    data_path = write_rows_jsonl(rows, root / "data" / "records.jsonl")
    manifest = {
        "dataset_name": dataset_name,
        "num_rows": len(rows),
        "data_file": str(data_path.relative_to(root)),
        "formats": ["jsonl"],
    }
    manifest_path = root / "manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return {"data_path": str(data_path), "manifest_path": str(manifest_path)}
