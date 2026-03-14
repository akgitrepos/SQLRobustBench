from __future__ import annotations

import json
from pathlib import Path

from sqlrobustbench.corrupt.recipes import create_corrupted_example
from sqlrobustbench.export.hf_packaging import create_release_bundle
from sqlrobustbench.export.rows import build_clean_row, build_corruption_row, build_normalization_row
from sqlrobustbench.ids import make_row_id
from sqlrobustbench.normalize.canonicalize import create_normalization_example
from sqlrobustbench.queries.generator import build_query_program
from sqlrobustbench.schemas.generator import build_generated_schema, load_schema_definition


ROOT = Path(__file__).resolve().parents[1]


def _schema(name: str):
    definition = load_schema_definition(ROOT / f"configs/schemas/{name}.yaml")
    return build_generated_schema(definition)


def test_release_bundle_writes_manifest_and_records(tmp_path: Path):
    schema = _schema("logistics")
    program = build_query_program(schema, template_id="carrier_rollup", complexity="medium", seed=2)
    corruption = create_corrupted_example(program, schema, "missing_group_by")
    normalization = create_normalization_example(program)
    rows = [
        build_clean_row(row_id=make_row_id("sqlclean", schema.schema_family, 1), program=program, schema=schema, split="train"),
        build_corruption_row(
            row_id=make_row_id("sqlcorrupt", schema.schema_family, 1),
            program=program,
            schema=schema,
            record=corruption.record,
            split="validation",
        ),
        build_normalization_row(
            row_id=make_row_id("sqlnormalize", schema.schema_family, 1),
            program=program,
            schema=schema,
            result=normalization,
            split="test_in_domain",
        ),
    ]

    bundle = create_release_bundle(rows, tmp_path)
    manifest = json.loads(Path(bundle["manifest_path"]).read_text(encoding="utf-8"))
    records = Path(bundle["data_path"]).read_text(encoding="utf-8").strip().splitlines()

    assert manifest["num_rows"] == 3
    assert len(records) == 3
    assert json.loads(records[1])["task"] == "repair"
