from __future__ import annotations

from dataclasses import dataclass, field

from sqlrobustbench.queries.ast import QueryProgram
from sqlrobustbench.types import GeneratedSchema, TableSpec


@dataclass(slots=True)
class ResolutionResult:
    is_valid: bool
    errors: list[str] = field(default_factory=list)


def _table_map(schema: GeneratedSchema) -> dict[str, TableSpec]:
    return {table.name: table for table in schema.tables}


def _column_names(table: TableSpec) -> set[str]:
    return {column.name for column in table.columns}


def validate_program_references(program: QueryProgram, schema: GeneratedSchema) -> ResolutionResult:
    tables = _table_map(schema)
    aliases = {program.base_table.alias: program.base_table.name}
    errors: list[str] = []

    if program.base_table.name not in tables:
        errors.append(f"Base table '{program.base_table.name}' is not present in schema '{schema.schema_id}'.")

    for join in program.joins:
        aliases[join.right_table.alias] = join.right_table.name
        if join.right_table.name not in tables:
            errors.append(f"Joined table '{join.right_table.name}' is not present in schema '{schema.schema_id}'.")

    for table_ref in [program.base_table, *(join.right_table for join in program.joins)]:
        if table_ref.name in tables and table_ref.alias == "":
            errors.append(f"Table '{table_ref.name}' is missing an alias.")

    for alias, table_name in aliases.items():
        if table_name not in tables:
            continue
        available = _column_names(tables[table_name])
        for expression in _program_expressions(program):
            for reference_alias, reference_column in _extract_column_refs(expression):
                if reference_alias != alias:
                    continue
                if reference_column not in available:
                    errors.append(
                        f"Column '{reference_column}' is not present on table '{table_name}' for alias '{alias}'."
                    )

    return ResolutionResult(is_valid=not errors, errors=errors)


def _program_expressions(program: QueryProgram) -> list[str]:
    expressions = [item.expression for item in program.select_items]
    expressions.extend(predicate.expression for predicate in program.where_predicates)
    expressions.extend(join.on_expression for join in program.joins)
    expressions.extend(program.group_by)
    expressions.extend(predicate.expression for predicate in program.having)
    expressions.extend(item.expression for item in program.order_by)
    return expressions


def _extract_column_refs(expression: str) -> list[tuple[str, str]]:
    refs: list[tuple[str, str]] = []
    token = []
    for char in expression:
        if char.isalnum() or char in {"_", "."}:
            token.append(char)
            continue
        refs.extend(_split_token("".join(token)))
        token = []
    refs.extend(_split_token("".join(token)))
    return refs


def _split_token(token: str) -> list[tuple[str, str]]:
    if token.count(".") != 1:
        return []
    alias, column = token.split(".")
    if not alias or not column:
        return []
    if alias.isupper() and column.isupper():
        return []
    return [(alias, column)]
