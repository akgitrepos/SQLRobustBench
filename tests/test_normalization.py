from __future__ import annotations

from pathlib import Path

from sqlrobustbench.normalize.canonicalize import create_normalization_example
from sqlrobustbench.queries.generator import build_query_program
from sqlrobustbench.schemas.generator import build_generated_schema, load_schema_definition
from sqlrobustbench.validate.parser import parse_sql


ROOT = Path(__file__).resolve().parents[1]


def _schema(name: str):
    definition = load_schema_definition(ROOT / f"configs/schemas/{name}.yaml")
    return build_generated_schema(definition)


def test_normalization_tracks_rules_and_preserves_parseability():
    schema = _schema("logistics")
    program = build_query_program(schema, template_id="carrier_rollup", complexity="medium", seed=2)
    result = create_normalization_example(program)

    assert result.record.rule_ids
    assert parse_sql(result.target_sql, dialect=program.dialect).is_valid
    assert "SELECT" in result.target_sql
    assert "select" in result.source_sql


def test_normalization_renames_aliases_deterministically():
    schema = _schema("retail_sales")
    program = build_query_program(schema, template_id="baseline_summary", complexity="medium", seed=1)
    result = create_normalization_example(program)

    assert "s1." in result.target_sql
