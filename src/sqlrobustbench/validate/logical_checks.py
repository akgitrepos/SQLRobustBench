from __future__ import annotations

from dataclasses import dataclass, field

from sqlrobustbench.queries.ast import QueryProgram
from sqlrobustbench.types import GeneratedSchema


@dataclass(slots=True)
class LogicalCheckResult:
    is_valid: bool
    errors: list[str] = field(default_factory=list)


def validate_program_logic(program: QueryProgram, schema: GeneratedSchema) -> LogicalCheckResult:
    errors: list[str] = []

    has_aggregate = any(item.is_aggregate for item in program.select_items)
    if has_aggregate and not program.group_by:
        errors.append("Aggregate select items require a GROUP BY clause in the current benchmark subset.")

    if program.having and not has_aggregate:
        errors.append("HAVING requires at least one aggregate select item.")

    if program.joins:
        valid_edges = {
            frozenset({(edge.left_table, edge.left_column), (edge.right_table, edge.right_column)})
            for edge in schema.join_graph
        }
        available_aliases = {program.base_table.alias: program.base_table.name}
        available_aliases.update({join.right_table.alias: join.right_table.name for join in program.joins})
        for join in program.joins:
            refs = _extract_eq_refs(join.on_expression)
            if refs is None:
                errors.append(f"Join condition '{join.on_expression}' is not a supported equality join.")
                continue
            left_ref, right_ref = refs
            left_table = available_aliases.get(left_ref[0])
            right_table = available_aliases.get(right_ref[0])
            if left_table is None or right_table is None:
                errors.append(f"Join condition '{join.on_expression}' references an unknown alias.")
                continue
            edge_key = frozenset({(left_table, left_ref[1]), (right_table, right_ref[1])})
            if edge_key not in valid_edges:
                errors.append(f"Join condition '{join.on_expression}' does not match the schema join graph.")

    return LogicalCheckResult(is_valid=not errors, errors=errors)


def _extract_eq_refs(expression: str) -> tuple[tuple[str, str], tuple[str, str]] | None:
    if "=" not in expression:
        return None
    left, right = [part.strip() for part in expression.split("=", maxsplit=1)]
    left_ref = _extract_ref(left)
    right_ref = _extract_ref(right)
    if left_ref is None or right_ref is None:
        return None
    return left_ref, right_ref


def _extract_ref(token: str) -> tuple[str, str] | None:
    if token.count(".") != 1:
        return None
    alias, column = token.split(".")
    if not alias or not column:
        return None
    return alias.strip(), column.strip()
