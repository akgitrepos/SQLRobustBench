from __future__ import annotations

from dataclasses import asdict, replace

from sqlrobustbench.hashing import stable_hash
from sqlrobustbench.queries.ast import JoinSpec, QueryProgram, SelectItem
from sqlrobustbench.queries.renderer import render_sql
from sqlrobustbench.types import CorruptionRecord, GeneratedSchema


CORRUPTION_FAMILIES = [
    "parser-breaking",
    "schema-breaking",
    "logic-breaking",
    "dialect-breaking",
]


def _clone_program(program: QueryProgram) -> QueryProgram:
    return replace(
        program,
        select_items=[replace(item) for item in program.select_items],
        joins=[replace(join, right_table=replace(join.right_table)) for join in program.joins],
        where_predicates=[replace(predicate) for predicate in program.where_predicates],
        having=[replace(predicate) for predicate in program.having],
        order_by=[replace(item) for item in program.order_by],
        metadata=dict(program.metadata),
    )


def apply_missing_comma(program: QueryProgram, _: GeneratedSchema) -> tuple[str, QueryProgram, CorruptionRecord]:
    target_sql = render_sql(program)
    if len(program.select_items) < 2:
        raise ValueError("missing_comma requires at least two select items")
    first = program.select_items[0]
    second = program.select_items[1]
    first_rendered = f"{first.expression} AS {first.alias}" if first.alias else first.expression
    second_rendered = f"{second.expression} AS {second.alias}" if second.alias else second.expression
    source_sql = target_sql.replace(f"{first_rendered}, {second_rendered}", f"{first_rendered} {second_rendered}", 1)
    record = CorruptionRecord(
        recipe_id="missing_comma",
        operator_name="missing_comma",
        corruption_family="parser-breaking",
        intended_failure_stage="parse",
        source_sql=source_sql,
        target_sql=target_sql,
        error_tags=["missing_comma"],
        source_program_hash=stable_hash(asdict(program)),
    )
    return source_sql, program, record


def apply_unknown_column(program: QueryProgram, _: GeneratedSchema) -> tuple[str, QueryProgram, CorruptionRecord]:
    corrupted = _clone_program(program)
    first_item = corrupted.select_items[0]
    alias = first_item.expression.split(".", 1)[0]
    corrupted.select_items[0] = SelectItem(expression=f"{alias}.unknown_column", alias=first_item.alias)
    source_sql = render_sql(corrupted)
    target_sql = render_sql(program)
    record = CorruptionRecord(
        recipe_id="unknown_column",
        operator_name="unknown_column",
        corruption_family="schema-breaking",
        intended_failure_stage="resolve",
        source_sql=source_sql,
        target_sql=target_sql,
        error_tags=["unknown_column"],
        source_program_hash=stable_hash(asdict(program)),
        corrupted_program_hash=stable_hash(asdict(corrupted)),
    )
    return source_sql, corrupted, record


def apply_invalid_join_condition(program: QueryProgram, schema: GeneratedSchema) -> tuple[str, QueryProgram, CorruptionRecord]:
    if not program.joins:
        raise ValueError("invalid_join_condition requires at least one join")
    corrupted = _clone_program(program)
    first_join = corrupted.joins[0]
    invalid_column = "shipment_status"
    if schema.schema_family != "logistics":
        invalid_column = corrupted.base_table.alias + "_invalid"
    corrupted.joins[0] = JoinSpec(
        join_type=first_join.join_type,
        right_table=first_join.right_table,
        on_expression=f"{corrupted.base_table.alias}.warehouse_id = {first_join.right_table.alias}.{invalid_column}",
    )
    source_sql = render_sql(corrupted)
    target_sql = render_sql(program)
    record = CorruptionRecord(
        recipe_id="invalid_join_condition",
        operator_name="invalid_join_condition",
        corruption_family="logic-breaking",
        intended_failure_stage="logic",
        source_sql=source_sql,
        target_sql=target_sql,
        error_tags=["invalid_join_condition"],
        source_program_hash=stable_hash(asdict(program)),
        corrupted_program_hash=stable_hash(asdict(corrupted)),
    )
    return source_sql, corrupted, record


def apply_missing_group_by(program: QueryProgram, _: GeneratedSchema) -> tuple[str, QueryProgram, CorruptionRecord]:
    if not program.group_by:
        raise ValueError("missing_group_by requires an aggregate query")
    corrupted = _clone_program(program)
    corrupted.group_by = []
    source_sql = render_sql(corrupted)
    target_sql = render_sql(program)
    record = CorruptionRecord(
        recipe_id="missing_group_by",
        operator_name="missing_group_by",
        corruption_family="logic-breaking",
        intended_failure_stage="logic",
        source_sql=source_sql,
        target_sql=target_sql,
        error_tags=["group_by_missing"],
        source_program_hash=stable_hash(asdict(program)),
        corrupted_program_hash=stable_hash(asdict(corrupted)),
    )
    return source_sql, corrupted, record


OPERATOR_REGISTRY = {
    "missing_comma": apply_missing_comma,
    "unknown_column": apply_unknown_column,
    "invalid_join_condition": apply_invalid_join_condition,
    "missing_group_by": apply_missing_group_by,
}
