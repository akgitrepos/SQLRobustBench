from __future__ import annotations

from pathlib import Path

from sqlrobustbench.corrupt.recipes import create_corrupted_example, infer_failure_stage, validate_corrupted_example
from sqlrobustbench.queries.generator import build_query_program
from sqlrobustbench.schemas.generator import build_generated_schema, load_schema_definition


ROOT = Path(__file__).resolve().parents[1]


def _schema(name: str):
    definition = load_schema_definition(ROOT / f"configs/schemas/{name}.yaml")
    return build_generated_schema(definition)


def test_missing_comma_triggers_parse_failure():
    schema = _schema("retail_sales")
    program = build_query_program(schema, template_id="baseline_summary", complexity="easy", seed=3)
    example = create_corrupted_example(program, schema, "missing_comma")

    assert example.intended_failure_stage == "parse"
    assert infer_failure_stage(example, schema) == "parse"
    assert validate_corrupted_example(example, schema)


def test_unknown_column_triggers_resolution_failure():
    schema = _schema("retail_sales")
    program = build_query_program(schema, template_id="baseline_summary", complexity="easy", seed=3)
    example = create_corrupted_example(program, schema, "unknown_column")

    assert example.record.error_tags == ["unknown_column"]
    assert infer_failure_stage(example, schema) == "resolve"
    assert validate_corrupted_example(example, schema)


def test_missing_group_by_triggers_logic_failure():
    schema = _schema("logistics")
    program = build_query_program(schema, template_id="carrier_rollup", complexity="medium", seed=2)
    example = create_corrupted_example(program, schema, "missing_group_by")

    assert example.intended_failure_stage == "logic"
    assert infer_failure_stage(example, schema) == "logic"
    assert validate_corrupted_example(example, schema)


def test_invalid_join_condition_triggers_logic_failure():
    schema = _schema("logistics")
    program = build_query_program(schema, template_id="carrier_rollup", complexity="medium", seed=2)
    example = create_corrupted_example(program, schema, "invalid_join_condition")

    assert example.record.corruption_family == "logic-breaking"
    assert infer_failure_stage(example, schema) == "logic"
    assert validate_corrupted_example(example, schema)
