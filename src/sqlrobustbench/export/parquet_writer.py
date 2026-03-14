from __future__ import annotations

import json
from pathlib import Path

from sqlrobustbench.export.rows import serialize_row
from sqlrobustbench.types import BenchmarkRow


def parquet_export_available() -> bool:
    return False


def write_rows_jsonl(rows: list[BenchmarkRow], output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(serialize_row(row), sort_keys=True))
            handle.write("\n")
    return path
