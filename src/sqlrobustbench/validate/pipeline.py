from __future__ import annotations

from dataclasses import dataclass, field

from sqlrobustbench.queries.ast import QueryProgram
from sqlrobustbench.types import GeneratedSchema
from sqlrobustbench.validate.logical_checks import validate_program_logic
from sqlrobustbench.validate.parser import parse_sql
from sqlrobustbench.validate.resolver import validate_program_references


@dataclass(slots=True)
class ValidationReport:
    is_valid: bool
    stage_results: dict[str, bool]
    errors: dict[str, list[str]] = field(default_factory=dict)


def validate_generated_query(
    program: QueryProgram,
    schema: GeneratedSchema,
    sql: str,
) -> ValidationReport:
    parse_result = parse_sql(sql, dialect=program.dialect)
    resolution_result = validate_program_references(program, schema)
    logical_result = validate_program_logic(program, schema)

    stage_results = {
        "parse": parse_result.is_valid,
        "resolve": resolution_result.is_valid,
        "logic": logical_result.is_valid,
    }
    errors = {
        stage: stage_errors
        for stage, stage_errors in {
            "parse": parse_result.errors,
            "resolve": resolution_result.errors,
            "logic": logical_result.errors,
        }.items()
        if stage_errors
    }

    return ValidationReport(is_valid=all(stage_results.values()), stage_results=stage_results, errors=errors)
