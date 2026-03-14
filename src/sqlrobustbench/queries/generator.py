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
AGGREGATE_FUNCTIONS = ["SUM", "AVG", "MAX", "MIN", "COUNT"]


def _table_by_name(schema: GeneratedSchema, name: str) -> TableSpec:
    for table in schema.tables:
        if table.name == name:
            return table
    raise KeyError(f"Unknown table: {name}")


def _dimension_columns(table: TableSpec) -> list[str]:
    preferred = [
        column.name
        for column in table.columns
        if column.data_type in {"text", "date", "timestamp"} and column.name != table.primary_key
    ]
    if preferred:
        return preferred
    fallback = [column.name for column in table.columns if column.name != table.primary_key]
    return fallback or [table.primary_key]


def _metric_columns(table: TableSpec) -> list[str]:
    preferred = [
        column.name
        for column in table.columns
        if (
            column.data_type in {"decimal", "integer"}
            and column.name != table.primary_key
            and column.value_strategy != "foreign_key"
        )
    ]
    if preferred:
        return preferred
    fallback = [
        column.name
        for column in table.columns
        if column.data_type in {"decimal", "integer"} and column.name != table.primary_key
    ]
    return fallback or [table.primary_key]


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


def _dimension_select(table_ref: TableRef, table: TableSpec, rng: random.Random) -> SelectItem:
    dimension = rng.choice(_dimension_columns(table))
    return SelectItem(expression=f"{table_ref.alias}.{dimension}", alias=dimension)


def _metric_select(table_ref: TableRef, table: TableSpec, aggregate: bool, rng: random.Random) -> SelectItem:
    metric = rng.choice(_metric_columns(table))
    if aggregate:
        aggregate_function = rng.choice(AGGREGATE_FUNCTIONS)
        if aggregate_function == "COUNT":
            expression = f"COUNT({table_ref.alias}.{metric})"
            alias = f"count_{metric}"
        else:
            expression = f"{aggregate_function}({table_ref.alias}.{metric})"
            alias = f"{aggregate_function.lower()}_{metric}"
        return SelectItem(expression=expression, alias=alias, is_aggregate=True)
    return SelectItem(expression=f"{table_ref.alias}.{metric}", alias=metric)


def _metric_expression_parts(select_item: SelectItem) -> tuple[str, str] | None:
    if "(" not in select_item.expression or not select_item.expression.endswith(")"):
        return None
    aggregate_function, remainder = select_item.expression.split("(", maxsplit=1)
    inner = remainder[:-1]
    return aggregate_function, inner


def _sample_non_null_predicate(table_ref: TableRef, column_name: str) -> PredicateSpec:
    return PredicateSpec(expression=f"{table_ref.alias}.{column_name} IS NOT NULL")


def _sample_dimension_predicate(table_ref: TableRef, column_name: str, rng: random.Random) -> PredicateSpec:
    if rng.choice([True, False]):
        return PredicateSpec(expression=f"{table_ref.alias}.{column_name} IS NOT NULL")
    return PredicateSpec(expression=f"{table_ref.alias}.{column_name} <> ''")


def _sample_order_by(base_dimension: SelectItem, metric_select: SelectItem | None, rng: random.Random) -> list[OrderBySpec]:
    if metric_select and rng.choice([True, False]):
        return [OrderBySpec(expression=metric_select.expression, direction=rng.choice(["ASC", "DESC"]))]
    return [OrderBySpec(expression=base_dimension.expression, direction=rng.choice(["ASC", "DESC"]))]


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

    base_dimension = _dimension_select(base_table, base_table_spec, rng)
    program = QueryProgram(template_id=template_id, dialect=dialect, base_table=base_table)

    if complexity == "easy":
        metric_select = _metric_select(base_table, base_table_spec, aggregate=False, rng=rng)
        program.select_items = [base_dimension, metric_select]
        program.where_predicates = [_sample_dimension_predicate(base_table, base_dimension.alias or base_table_spec.primary_key, rng)]
        program.order_by = _sample_order_by(base_dimension, metric_select, rng)
        program.limit = _sample_limit(rng, complexity)
    else:
        metric_source_ref = joins[-1].right_table if joins else base_table
        metric_source_spec = _table_by_name(schema, metric_source_ref.name)
        program.joins = joins
        metric_select = _metric_select(metric_source_ref, metric_source_spec, aggregate=True, rng=rng)
        program.select_items = [base_dimension, metric_select]
        program.group_by = [base_dimension.expression]
        program.order_by = _sample_order_by(base_dimension, metric_select, rng)
        metric_column = metric_select.expression.split(".", 1)[1].rstrip(")") if "." in metric_select.expression else rng.choice(_metric_columns(metric_source_spec))
        if complexity == "medium":
            program.where_predicates = [_sample_non_null_predicate(metric_source_ref, metric_column)]
            program.limit = _sample_limit(rng, complexity)
        else:
            metric_parts = _metric_expression_parts(metric_select)
            aggregate_function = metric_parts[0] if metric_parts else "SUM"
            aggregate_argument = metric_parts[1] if metric_parts else f"{metric_source_ref.alias}.{metric_column}"
            program.where_predicates = [
                _sample_non_null_predicate(metric_source_ref, metric_column),
                _sample_dimension_predicate(base_table, base_dimension.alias or base_table_spec.primary_key, rng),
            ]
            threshold = rng.choice([0, 1, 5, 10])
            program.having = [PredicateSpec(expression=f"{aggregate_function}({aggregate_argument}) > {threshold}")]

    program.metadata = {
        "schema_id": schema.schema_id,
        "complexity": complexity,
        "program_hash": stable_hash(asdict(program)),
    }
    return program
