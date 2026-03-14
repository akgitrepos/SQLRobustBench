from __future__ import annotations

from dataclasses import asdict, dataclass, replace

from sqlrobustbench.hashing import stable_hash
from sqlrobustbench.normalize.rules import RULE_REGISTRY
from sqlrobustbench.queries.ast import JoinSpec, OrderBySpec, PredicateSpec, QueryProgram, SelectItem, TableRef
from sqlrobustbench.queries.renderer import render_sql
from sqlrobustbench.types import NormalizationRecord


@dataclass(slots=True)
class NormalizationResult:
    source_sql: str
    target_sql: str
    normalized_program: QueryProgram
    record: NormalizationRecord


def _canonical_alias(index: int) -> str:
    return f"s{index}"


def _clone_program(program: QueryProgram) -> QueryProgram:
    return replace(
        program,
        base_table=replace(program.base_table),
        select_items=[replace(item) for item in program.select_items],
        joins=[replace(join, right_table=replace(join.right_table)) for join in program.joins],
        where_predicates=[replace(predicate) for predicate in program.where_predicates],
        group_by=list(program.group_by),
        having=[replace(predicate) for predicate in program.having],
        order_by=[replace(item) for item in program.order_by],
        metadata=dict(program.metadata),
    )


def _apply_alias_map(text: str, alias_map: dict[str, str]) -> str:
    updated = text
    for old_alias, new_alias in alias_map.items():
        updated = updated.replace(f"{old_alias}.", f"{new_alias}.")
    return updated


def canonicalize_program(program: QueryProgram) -> tuple[QueryProgram, list[str]]:
    normalized = _clone_program(program)
    alias_map = {program.base_table.alias: _canonical_alias(1)}
    normalized.base_table = TableRef(name=program.base_table.name, alias=alias_map[program.base_table.alias])

    normalized_joins: list[JoinSpec] = []
    for index, join in enumerate(program.joins, start=2):
        alias_map[join.right_table.alias] = _canonical_alias(index)
        normalized_joins.append(
            JoinSpec(
                join_type=join.join_type.upper(),
                right_table=TableRef(name=join.right_table.name, alias=alias_map[join.right_table.alias]),
                on_expression=_apply_alias_map(join.on_expression, alias_map),
            )
        )
    normalized.joins = normalized_joins

    normalized.select_items = [
        SelectItem(
            expression=_apply_alias_map(item.expression, alias_map),
            alias=item.alias,
            is_aggregate=item.is_aggregate,
        )
        for item in program.select_items
    ]
    normalized.where_predicates = [
        PredicateSpec(expression=_apply_alias_map(predicate.expression, alias_map))
        for predicate in program.where_predicates
    ]
    normalized.group_by = [_apply_alias_map(group_item, alias_map) for group_item in program.group_by]
    normalized.having = [
        PredicateSpec(expression=_apply_alias_map(predicate.expression, alias_map))
        for predicate in program.having
    ]
    normalized.order_by = [
        OrderBySpec(expression=_apply_alias_map(item.expression, alias_map), direction=item.direction.upper())
        for item in program.order_by
    ]
    normalized.metadata["program_hash"] = stable_hash(asdict(normalized))

    return normalized, [
        RULE_REGISTRY["deterministic_aliases"].rule_id,
        RULE_REGISTRY["keyword_casing"].rule_id,
        RULE_REGISTRY["deterministic_spacing"].rule_id,
        RULE_REGISTRY["explicit_order_direction"].rule_id,
    ]


def render_noncanonical_sql(program: QueryProgram) -> str:
    canonical_sql = render_sql(program)
    lowercased_keywords = canonical_sql
    replacements = {
        "SELECT": "select",
        "FROM": "from",
        "INNER JOIN": "inner join",
        "WHERE": "where",
        "GROUP BY": "group by",
        "HAVING": "having",
        "ORDER BY": "order by",
        "LIMIT": "limit",
        " AS ": " as ",
        " ASC": " asc",
    }
    for source, target in replacements.items():
        lowercased_keywords = lowercased_keywords.replace(source, target)
    return lowercased_keywords.replace("\n", "  \n")


def create_normalization_example(program: QueryProgram) -> NormalizationResult:
    normalized_program, rule_ids = canonicalize_program(program)
    source_sql = render_noncanonical_sql(program)
    target_sql = render_sql(normalized_program)
    record = NormalizationRecord(
        source_sql=source_sql,
        target_sql=target_sql,
        rule_ids=rule_ids,
        source_program_hash=stable_hash(asdict(program)),
        normalized_program_hash=stable_hash(asdict(normalized_program)),
    )
    return NormalizationResult(
        source_sql=source_sql,
        target_sql=target_sql,
        normalized_program=normalized_program,
        record=record,
    )
