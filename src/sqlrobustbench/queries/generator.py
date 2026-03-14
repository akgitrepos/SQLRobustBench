from __future__ import annotations

from dataclasses import asdict
import random

from sqlrobustbench.hashing import stable_hash
from sqlrobustbench.queries.ast import (
    JoinSpec,
    OrderBySpec,
    PredicateSpec,
    QueryProgram,
    SelectItem,
    TableRef,
)
from sqlrobustbench.types import GeneratedSchema, JoinEdge, TableSpec


COMPLEXITY_LEVELS = {"easy", "medium", "hard"}


def _table_by_name(schema: GeneratedSchema, name: str) -> TableSpec:
    for table in schema.tables:
        if table.name == name:
            return table
    raise KeyError(f"Unknown table: {name}")


def _default_dimension_column(table: TableSpec) -> str:
    for column in table.columns:
        if column.data_type in {"text", "date"} and column.name != table.primary_key:
            return column.name
    for column in table.columns:
        if column.name != table.primary_key:
            return column.name
    return table.primary_key


def _default_metric_column(table: TableSpec) -> str:
    for column in table.columns:
        if (
            column.data_type in {"decimal", "integer"}
            and column.name != table.primary_key
            and column.value_strategy != "foreign_key"
        ):
            return column.name
    for column in table.columns:
        if column.data_type in {"decimal", "integer"} and column.name != table.primary_key:
            return column.name
    return table.primary_key


def _alias(index: int) -> str:
    return f"t{index}"


def _join_candidates(schema: GeneratedSchema, base_table: str) -> list[JoinEdge]:
    return [edge for edge in schema.join_graph if edge.left_table == base_table or edge.right_table == base_table]


def _join_from_edge(edge: JoinEdge, left_table: TableRef, next_alias: str) -> JoinSpec:
    if edge.left_table == left_table.name:
        right_table = TableRef(name=edge.right_table, alias=next_alias)
        on_expression = (
            f"{left_table.alias}.{edge.left_column} = "
            f"{right_table.alias}.{edge.right_column}"
        )
    else:
        right_table = TableRef(name=edge.left_table, alias=next_alias)
        on_expression = (
            f"{right_table.alias}.{edge.left_column} = "
            f"{left_table.alias}.{edge.right_column}"
        )
    return JoinSpec(join_type="INNER JOIN", right_table=right_table, on_expression=on_expression)


def _dimension_select(table_ref: TableRef, table: TableSpec) -> SelectItem:
    dimension = _default_dimension_column(table)
    return SelectItem(expression=f"{table_ref.alias}.{dimension}", alias=dimension)


def _metric_select(table_ref: TableRef, table: TableSpec, aggregate: bool) -> SelectItem:
    metric = _default_metric_column(table)
    if aggregate:
        return SelectItem(expression=f"SUM({table_ref.alias}.{metric})", alias=f"total_{metric}", is_aggregate=True)
    return SelectItem(expression=f"{table_ref.alias}.{metric}", alias=metric)


def _sample_limit(rng: random.Random, complexity: str) -> int | None:
    if complexity == "hard":
        return None
    return rng.choice([10, 25, 50])


def build_query_program(
    schema: GeneratedSchema,
    *,
    template_id: str,
    complexity: str,
    dialect: str = "ansi_like",
    seed: int = 0,
) -> QueryProgram:
    if complexity not in COMPLEXITY_LEVELS:
        raise ValueError(f"Unsupported complexity: {complexity}")

    rng = random.Random(seed)
    base_table_spec = rng.choice(schema.tables)
    base_table = TableRef(name=base_table_spec.name, alias=_alias(1))
    joins: list[JoinSpec] = []

    if complexity in {"medium", "hard"}:
        candidates = _join_candidates(schema, base_table.name)
        if candidates:
            first_edge = rng.choice(candidates)
            joins.append(_join_from_edge(first_edge, base_table, _alias(2)))

    if complexity == "hard" and joins:
        current_table = joins[-1].right_table
        used_tables = {base_table.name, current_table.name}
        next_edges = [
            edge
            for edge in _join_candidates(schema, current_table.name)
            if edge.left_table not in used_tables or edge.right_table not in used_tables
        ]
        if next_edges:
            joins.append(_join_from_edge(rng.choice(next_edges), current_table, _alias(3)))

    base_dimension = _dimension_select(base_table, base_table_spec)
    program = QueryProgram(template_id=template_id, dialect=dialect, base_table=base_table)

    if complexity == "easy":
        program.select_items = [base_dimension, _metric_select(base_table, base_table_spec, aggregate=False)]
        program.where_predicates = [PredicateSpec(expression=f"{base_table.alias}.{base_dimension.alias} IS NOT NULL")]
        program.order_by = [OrderBySpec(expression=base_dimension.expression)]
        program.limit = _sample_limit(rng, complexity)
    else:
        metric_source_ref = joins[-1].right_table if joins else base_table
        metric_source_spec = _table_by_name(schema, metric_source_ref.name)
        program.joins = joins
        program.select_items = [base_dimension, _metric_select(metric_source_ref, metric_source_spec, aggregate=True)]
        program.group_by = [base_dimension.expression]
        program.order_by = [OrderBySpec(expression=base_dimension.expression)]
        metric_column = _default_metric_column(metric_source_spec)
        if complexity == "medium":
            program.where_predicates = [
                PredicateSpec(expression=f"{metric_source_ref.alias}.{metric_column} IS NOT NULL")
            ]
            program.limit = _sample_limit(rng, complexity)
        else:
            program.where_predicates = [
                PredicateSpec(expression=f"{metric_source_ref.alias}.{metric_column} IS NOT NULL"),
                PredicateSpec(expression=f"{base_table.alias}.{base_dimension.alias} IS NOT NULL"),
            ]
            program.having = [PredicateSpec(expression=f"SUM({metric_source_ref.alias}.{metric_column}) > 0")]

    program.metadata = {
        "schema_id": schema.schema_id,
        "complexity": complexity,
        "program_hash": stable_hash(asdict(program)),
    }
    return program
