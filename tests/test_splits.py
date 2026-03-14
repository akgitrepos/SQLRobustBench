from __future__ import annotations

from pathlib import Path

from sqlrobustbench.corrupt.recipes import create_corrupted_example
from sqlrobustbench.export.rows import build_clean_row, build_corruption_row, build_normalization_row
from sqlrobustbench.ids import make_row_id
from sqlrobustbench.normalize.canonicalize import create_normalization_example
from sqlrobustbench.queries.generator import build_query_program
from sqlrobustbench.schemas.generator import build_generated_schema, load_schema_definition
from sqlrobustbench.splits.builder import build_splits, summarize_split_plan, template_family_ids


ROOT = Path(__file__).resolve().parents[1]


def _schema(name: str):
    definition = load_schema_definition(ROOT / f"configs/schemas/{name}.yaml")
    return build_generated_schema(definition)


def _rows():
    retail = _schema("retail_sales")
    logistics = _schema("logistics")
    retail_program = build_query_program(retail, template_id="baseline_summary", complexity="easy", seed=3)
    logistics_program = build_query_program(logistics, template_id="carrier_rollup", complexity="medium", seed=2)
    hard_program = build_query_program(logistics, template_id="carrier_rollup_hard", complexity="hard", seed=1)

    rows = [
        build_clean_row(row_id=make_row_id("sqlclean", retail.schema_family, 1), program=retail_program, schema=retail, split="train"),
        build_clean_row(row_id=make_row_id("sqlclean", logistics.schema_family, 1), program=logistics_program, schema=logistics, split="train"),
        build_clean_row(row_id=make_row_id("sqlclean", logistics.schema_family, 2), program=hard_program, schema=logistics, split="train"),
    ]

    corruption = create_corrupted_example(logistics_program, logistics, "missing_group_by")
    rows.append(
        build_corruption_row(
            row_id=make_row_id("sqlcorrupt", logistics.schema_family, 1),
            program=logistics_program,
            schema=logistics,
            record=corruption.record,
            split="train",
        )
    )
    normalization = create_normalization_example(logistics_program)
    rows.append(
        build_normalization_row(
            row_id=make_row_id("sqlnormalize", logistics.schema_family, 1),
            program=logistics_program,
            schema=logistics,
            result=normalization,
            split="train",
        )
    )
    return rows


def test_build_splits_assigns_ood_for_schema_holdout():
    rows = _rows()
    plan = build_splits(rows, ood_schema_families={"logistics"})

    logistics_splits = {row.split for row in plan.rows if row.schema_family == "logistics"}
    assert logistics_splits == {"test_ood"}


def test_build_splits_assigns_validation_for_template_family_holdout():
    rows = _rows()
    family = next(iter(template_family_ids([rows[0]])))
    plan = build_splits(rows, validation_template_families={family})

    held_out = [row for row in plan.rows if row.template_id == rows[0].template_id and row.schema_family == rows[0].schema_family]
    assert held_out
    assert {row.split for row in held_out} == {"validation"}


def test_build_splits_can_send_hard_queries_to_ood():
    rows = _rows()
    plan = build_splits(rows, hard_complexity_to_ood=True)

    hard_rows = [row for row in plan.rows if row.complexity == "hard"]
    assert hard_rows
    assert {row.split for row in hard_rows} == {"test_ood"}


def test_summarize_split_plan_reports_counts():
    rows = _rows()
    plan = build_splits(rows, ood_template_ids={"carrier_rollup_hard"})
    summary = summarize_split_plan(plan.rows)

    assert summary["splits"]
    assert "train" in summary["splits"]
