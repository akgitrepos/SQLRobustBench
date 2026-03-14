from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class BenchmarkRow:
    id: str
    config: str
    task: str
    dialect: str
    db_schema_id: str
    schema_family: str
    source_sql: str
    is_source_valid: bool
    complexity: str
    template_id: str
    source_ast_hash: str
    semantic_hash: str
    provenance: str
    split: str
    target_sql: str | None = None
    error_tags: list[str] = field(default_factory=list)
    normalization_rules: list[str] = field(default_factory=list)
    num_joins: int = 0
    nesting_depth: int = 0
    corruption_recipe_id: str | None = None
    target_ast_hash: str | None = None
    ambiguity_flag: bool = False
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class SchemaFamilyConfig:
    schema_family: str
    version: str
    description: str


@dataclass(slots=True)
class DialectProfile:
    name: str
    role: str
    notes: list[str] = field(default_factory=list)
    supports: list[str] = field(default_factory=list)
    restrictions: list[str] = field(default_factory=list)
