from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class TableRef:
    name: str
    alias: str


@dataclass(slots=True)
class SelectItem:
    expression: str
    alias: str | None = None
    is_aggregate: bool = False


@dataclass(slots=True)
class JoinSpec:
    join_type: str
    right_table: TableRef
    on_expression: str


@dataclass(slots=True)
class PredicateSpec:
    expression: str


@dataclass(slots=True)
class OrderBySpec:
    expression: str
    direction: str = "ASC"


@dataclass(slots=True)
class QueryProgram:
    template_id: str
    dialect: str
    base_table: TableRef
    select_items: list[SelectItem] = field(default_factory=list)
    joins: list[JoinSpec] = field(default_factory=list)
    where_predicates: list[PredicateSpec] = field(default_factory=list)
    group_by: list[str] = field(default_factory=list)
    having: list[PredicateSpec] = field(default_factory=list)
    order_by: list[OrderBySpec] = field(default_factory=list)
    limit: int | None = None
    metadata: dict[str, str] = field(default_factory=dict)

    @property
    def from_tables(self) -> list[str]:
        tables = [self.base_table.name]
        tables.extend(join.right_table.name for join in self.joins)
        return tables
