from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class QueryProgram:
    template_id: str
    select_expressions: list[str] = field(default_factory=list)
    from_tables: list[str] = field(default_factory=list)
    where_predicates: list[str] = field(default_factory=list)
    joins: list[str] = field(default_factory=list)
    group_by: list[str] = field(default_factory=list)
    having: list[str] = field(default_factory=list)
    order_by: list[str] = field(default_factory=list)
    limit: int | None = None
