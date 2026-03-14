from __future__ import annotations

from pathlib import Path

from sqlrobustbench.queries.complexity import estimate_complexity
from sqlrobustbench.queries.generator import build_query_program
from sqlrobustbench.queries.renderer import render_sql
from sqlrobustbench.schemas.generator import build_generated_schema, load_schema_definition


ROOT = Path(__file__).resolve().parents[1]


def _schema(name: str):
    definition = load_schema_definition(ROOT / f"configs/schemas/{name}.yaml")
    return build_generated_schema(definition)


def test_easy_query_generation_is_deterministic():
    schema = _schema("retail_sales")
    program_one = build_query_program(schema, template_id="baseline_summary", complexity="easy", seed=11)
    program_two = build_query_program(schema, template_id="baseline_summary", complexity="easy", seed=11)

    assert program_one == program_two
    assert estimate_complexity(program_one) == "easy"


def test_medium_query_generation_uses_join_and_group_by_when_available():
    schema = _schema("logistics")
    program = build_query_program(schema, template_id="carrier_rollup", complexity="medium", seed=2)
    sql = render_sql(program)

    assert program.joins
    assert program.group_by
    assert "INNER JOIN" in sql
    assert "GROUP BY" in sql
    assert estimate_complexity(program) == "medium"


def test_hard_query_generation_adds_having_clause():
    schema = _schema("hr_payroll")
    program = build_query_program(schema, template_id="department_payroll", complexity="hard", seed=1)
    sql = render_sql(program)

    assert program.having
    assert "HAVING" in sql
    assert estimate_complexity(program) == "hard"


def test_renderer_outputs_expected_clause_order():
    schema = _schema("retail_sales")
    program = build_query_program(schema, template_id="baseline_summary", complexity="medium", seed=5)
    sql = render_sql(program)

    clause_order = ["SELECT", "FROM", "WHERE", "GROUP BY", "ORDER BY"]
    positions = [sql.index(clause) for clause in clause_order if clause in sql]
    assert positions == sorted(positions)
