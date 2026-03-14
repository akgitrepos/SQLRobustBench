from __future__ import annotations

from pathlib import Path

from sqlrobustbench.corrupt.recipes import create_corrupted_example
from sqlrobustbench.dedup.hashes import cap_render_variants, deduplicate_rows, group_rows_by_semantic_hash
from sqlrobustbench.dedup.leakage import audit_split_leakage
from sqlrobustbench.export.rows import build_clean_row, build_corruption_row, build_normalization_row
from sqlrobustbench.ids import make_row_id
from sqlrobustbench.normalize.canonicalize import create_normalization_example
from sqlrobustbench.queries.generator import build_query_program
from sqlrobustbench.schemas.generator import build_generated_schema, load_schema_definition


ROOT = Path(__file__).resolve().parents[1]


def _schema(name: str):
    definition = load_schema_definition(ROOT / f"configs/schemas/{name}.yaml")
    return build_generated_schema(definition)


def test_deduplicate_rows_removes_exact_duplicates():
    schema = _schema("retail_sales")
    program = build_query_program(schema, template_id="baseline_summary", complexity="easy", seed=3)
    row = build_clean_row(row_id=make_row_id("sqlclean", schema.schema_family, 1), program=program, schema=schema, split="train")
    dup = build_clean_row(row_id=make_row_id("sqlclean", schema.schema_family, 2), program=program, schema=schema, split="train")

    rows, stats = deduplicate_rows([row, dup])

    assert len(rows) == 1
    assert stats["removed_exact_duplicates"] == 1


def test_cap_render_variants_limits_semantic_group_membership():
    schema = _schema("logistics")
    program = build_query_program(schema, template_id="carrier_rollup", complexity="medium", seed=2)
    clean = build_clean_row(row_id=make_row_id("sqlclean", schema.schema_family, 1), program=program, schema=schema, split="train")
    norm = build_normalization_row(
        row_id=make_row_id("sqlnormalize", schema.schema_family, 1),
        program=program,
        schema=schema,
        result=create_normalization_example(program),
        split="train",
    )
    alt = build_normalization_row(
        row_id=make_row_id("sqlnormalize", schema.schema_family, 2),
        program=program,
        schema=schema,
        result=create_normalization_example(program),
        split="train",
    )
    alt.render_variant_id = "normalized_alt"
    alt.semantic_hash = clean.semantic_hash
    norm.semantic_hash = clean.semantic_hash

    kept, stats = cap_render_variants([clean, norm, alt], max_per_group=2)

    assert len(kept) == 2
    assert stats["removed_render_variants"] == 1


def test_audit_split_leakage_detects_semantic_and_template_overlap():
    schema = _schema("logistics")
    program = build_query_program(schema, template_id="carrier_rollup", complexity="medium", seed=2)
    clean_train = build_clean_row(
        row_id=make_row_id("sqlclean", schema.schema_family, 1),
        program=program,
        schema=schema,
        split="train",
    )
    corruption = create_corrupted_example(program, schema, "missing_group_by")
    corrupt_eval = build_corruption_row(
        row_id=make_row_id("sqlcorrupt", schema.schema_family, 1),
        program=program,
        schema=schema,
        record=corruption.record,
        split="test_in_domain",
    )
    report = audit_split_leakage([clean_train, corrupt_eval])

    assert report.has_leakage
    assert report.overlap_counts["template_family"] >= 1


def test_group_rows_by_semantic_hash_groups_related_rows():
    schema = _schema("retail_sales")
    program = build_query_program(schema, template_id="baseline_summary", complexity="easy", seed=3)
    clean = build_clean_row(row_id=make_row_id("sqlclean", schema.schema_family, 1), program=program, schema=schema, split="train")
    corruption = create_corrupted_example(program, schema, "unknown_column")
    corrupt_row = build_corruption_row(
        row_id=make_row_id("sqlcorrupt", schema.schema_family, 1),
        program=program,
        schema=schema,
        record=corruption.record,
        split="validation",
    )
    corrupt_row.semantic_hash = clean.semantic_hash

    groups = group_rows_by_semantic_hash([clean, corrupt_row])

    assert len(groups[clean.semantic_hash]) == 2
