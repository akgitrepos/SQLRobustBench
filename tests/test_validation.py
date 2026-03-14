from __future__ import annotations

from pathlib import Path

from sqlrobustbench.queries.generator import build_query_program
from sqlrobustbench.queries.renderer import render_sql
from sqlrobustbench.schemas.generator import build_generated_schema, load_schema_definition
from sqlrobustbench.validate.parser import parse_sql
from sqlrobustbench.validate.pipeline import validate_generated_query


ROOT = Path(__file__).resolve().parents[1]


def _schema(name: str):
    definition = load_schema_definition(ROOT / f"configs/schemas/{name}.yaml")
    return build_generated_schema(definition)


def test_parse_sql_rejects_invalid_sql():
    result = parse_sql("SELECT FROM", dialect="")
    assert not result.is_valid
    assert result.errors


def test_validation_pipeline_accepts_generated_query():
    schema = _schema("retail_sales")
    program = build_query_program(schema, template_id="baseline_summary", complexity="medium", seed=1)
    sql = render_sql(program)

    report = validate_generated_query(program, schema, sql)

    assert report.is_valid
    assert report.stage_results == {"parse": True, "resolve": True, "logic": True}


def test_validation_pipeline_rejects_unknown_column_reference():
    schema = _schema("retail_sales")
    program = build_query_program(schema, template_id="baseline_summary", complexity="easy", seed=3)
    program.select_items[0].expression = "t1.unknown_column"
    sql = render_sql(program)

    report = validate_generated_query(program, schema, sql)

    assert not report.is_valid
    assert not report.stage_results["resolve"]
    assert report.errors["resolve"]


def test_validation_pipeline_rejects_invalid_join_condition():
    schema = _schema("logistics")
    program = build_query_program(schema, template_id="carrier_rollup", complexity="medium", seed=2)
    program.joins[0].on_expression = "t1.warehouse_id = t2.shipment_status"
    sql = render_sql(program)

    report = validate_generated_query(program, schema, sql)

    assert not report.is_valid
    assert not report.stage_results["logic"]
    assert report.errors["logic"]
