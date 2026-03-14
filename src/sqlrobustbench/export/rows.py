from __future__ import annotations

from dataclasses import asdict

from sqlrobustbench.hashing import stable_hash
from sqlrobustbench.normalize.canonicalize import NormalizationResult
from sqlrobustbench.queries.ast import QueryProgram
from sqlrobustbench.queries.complexity import estimate_complexity
from sqlrobustbench.queries.renderer import render_sql
from sqlrobustbench.types import BenchmarkRow, CorruptionRecord, GeneratedSchema


def _program_hash(program: QueryProgram) -> str:
    return stable_hash(asdict(program))


def _semantic_hash(schema: GeneratedSchema, template_id: str, task: str) -> str:
    return stable_hash(
        {
            "schema_id": schema.schema_id,
            "template_id": template_id,
            "task": task,
        }
    )


def build_clean_row(
    *,
    row_id: str,
    program: QueryProgram,
    schema: GeneratedSchema,
    split: str,
    config: str = "clean_reference",
) -> BenchmarkRow:
    sql = render_sql(program)
    return BenchmarkRow(
        id=row_id,
        config=config,
        task="generate_clean_query",
        dialect=program.dialect,
        db_schema_id=schema.schema_id,
        schema_family=schema.schema_family,
        source_sql=sql,
        is_source_valid=True,
        complexity=estimate_complexity(program),
        template_id=program.template_id,
        source_ast_hash=_program_hash(program),
        semantic_hash=_semantic_hash(schema, program.template_id, "clean"),
        provenance=schema.provenance,
        split=split,
        num_joins=len(program.joins),
        nesting_depth=0,
        render_variant_id="canonical",
    )


def build_corruption_row(
    *,
    row_id: str,
    program: QueryProgram,
    schema: GeneratedSchema,
    record: CorruptionRecord,
    split: str,
    config: str = "corrupt_medium",
) -> BenchmarkRow:
    return BenchmarkRow(
        id=row_id,
        config=config,
        task="repair",
        dialect=program.dialect,
        db_schema_id=schema.schema_id,
        schema_family=schema.schema_family,
        source_sql=record.source_sql,
        is_source_valid=False,
        complexity=estimate_complexity(program),
        template_id=program.template_id,
        source_ast_hash=record.corrupted_program_hash or record.source_program_hash,
        semantic_hash=_semantic_hash(schema, program.template_id, "repair"),
        provenance=schema.provenance,
        split=split,
        target_sql=record.target_sql,
        error_tags=list(record.error_tags),
        num_joins=len(program.joins),
        nesting_depth=0,
        corruption_recipe_id=record.recipe_id,
        target_ast_hash=record.source_program_hash,
        render_variant_id=record.operator_name,
        extra={"intended_failure_stage": record.intended_failure_stage},
    )


def build_normalization_row(
    *,
    row_id: str,
    program: QueryProgram,
    schema: GeneratedSchema,
    result: NormalizationResult,
    split: str,
    config: str = "normalize_structural",
) -> BenchmarkRow:
    return BenchmarkRow(
        id=row_id,
        config=config,
        task="canonicalization",
        dialect=program.dialect,
        db_schema_id=schema.schema_id,
        schema_family=schema.schema_family,
        source_sql=result.source_sql,
        is_source_valid=True,
        complexity=estimate_complexity(program),
        template_id=program.template_id,
        source_ast_hash=result.record.source_program_hash,
        semantic_hash=_semantic_hash(schema, program.template_id, "canonicalization"),
        provenance=schema.provenance,
        split=split,
        target_sql=result.target_sql,
        normalization_rules=list(result.record.rule_ids),
        num_joins=len(program.joins),
        nesting_depth=0,
        target_ast_hash=result.record.normalized_program_hash,
        render_variant_id="normalized",
    )


def serialize_row(row: BenchmarkRow) -> dict:
    return asdict(row)
