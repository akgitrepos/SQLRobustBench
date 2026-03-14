from __future__ import annotations

import json
from pathlib import Path

from sqlrobustbench.schemas.generator import (
    build_generated_schema,
    load_schema_definition,
    write_generated_schema,
)


ROOT = Path(__file__).resolve().parents[1]


def test_load_schema_definition_reads_tables_and_seed_hints():
    schema = load_schema_definition(ROOT / "configs/schemas/retail_sales.yaml")

    assert schema.schema_family == "retail_sales"
    assert len(schema.tables) == 4
    assert schema.seed_hints


def test_build_generated_schema_builds_join_graph():
    schema = load_schema_definition(ROOT / "configs/schemas/logistics.yaml")
    generated = build_generated_schema(schema)

    assert generated.schema_id == "logistics_v1"
    assert len(generated.join_graph) == 3
    assert generated.join_graph[0].left_table in {"shipments", "delivery_events"}


def test_write_generated_schema_writes_json(tmp_path: Path):
    schema = load_schema_definition(ROOT / "configs/schemas/hr_payroll.yaml")
    generated = build_generated_schema(schema)
    output_path = tmp_path / "hr_payroll_v1.json"

    write_generated_schema(generated, output_path)

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["schema_id"] == "hr_payroll_v1"
    assert payload["tables"][0]["name"] == "departments"
