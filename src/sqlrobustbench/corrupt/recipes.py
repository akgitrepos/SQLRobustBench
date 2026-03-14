from __future__ import annotations

from dataclasses import dataclass

from sqlrobustbench.corrupt.operators import OPERATOR_REGISTRY
from sqlrobustbench.queries.ast import QueryProgram
from sqlrobustbench.types import CorruptionRecord, GeneratedSchema
from sqlrobustbench.validate.parser import parse_sql
from sqlrobustbench.validate.pipeline import validate_generated_query


@dataclass(slots=True)
class CorruptedExample:
    source_sql: str
    target_sql: str
    intended_failure_stage: str
    record: CorruptionRecord
    corrupted_program: QueryProgram | None = None


def make_recipe_id(*parts: str) -> str:
    return "+".join(parts)


def create_corrupted_example(
    program: QueryProgram,
    schema: GeneratedSchema,
    operator_name: str,
) -> CorruptedExample:
    operator = OPERATOR_REGISTRY[operator_name]
    source_sql, corrupted_program, record = operator(program, schema)
    record.recipe_id = make_recipe_id(operator_name)
    return CorruptedExample(
        source_sql=source_sql,
        target_sql=record.target_sql,
        intended_failure_stage=record.intended_failure_stage,
        record=record,
        corrupted_program=corrupted_program,
    )


def infer_failure_stage(example: CorruptedExample, schema: GeneratedSchema) -> str:
    parse_result = parse_sql(example.source_sql)
    if not parse_result.is_valid:
        return "parse"
    if example.corrupted_program is None:
        return "parse"
    report = validate_generated_query(example.corrupted_program, schema, example.source_sql)
    for stage in ["parse", "resolve", "logic"]:
        if not report.stage_results[stage]:
            return stage
    return "valid"


def validate_corrupted_example(example: CorruptedExample, schema: GeneratedSchema) -> bool:
    return infer_failure_stage(example, schema) == example.intended_failure_stage
