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
class CorruptionRecord:
    recipe_id: str
    operator_name: str
    corruption_family: str
    intended_failure_stage: str
    source_sql: str
    target_sql: str
    error_tags: list[str] = field(default_factory=list)
    source_program_hash: str = ""
    corrupted_program_hash: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class SchemaFamilyConfig:
    schema_family: str
    version: str
    description: str


@dataclass(slots=True)
class ColumnSpec:
    name: str
    data_type: str
    nullable: bool = False
    description: str = ""
    value_strategy: str = "generic"


@dataclass(slots=True)
class ForeignKeySpec:
    column: str
    references_table: str
    references_column: str


@dataclass(slots=True)
class TableSpec:
    name: str
    description: str
    primary_key: str
    columns: list[ColumnSpec] = field(default_factory=list)
    foreign_keys: list[ForeignKeySpec] = field(default_factory=list)


@dataclass(slots=True)
class SchemaDefinition:
    schema_family: str
    version: str
    description: str
    tables: list[TableSpec] = field(default_factory=list)
    seed_hints: list[str] = field(default_factory=list)


@dataclass(slots=True)
class JoinEdge:
    left_table: str
    left_column: str
    right_table: str
    right_column: str


@dataclass(slots=True)
class GeneratedSchema:
    schema_id: str
    schema_family: str
    version: str
    description: str
    tables: list[TableSpec] = field(default_factory=list)
    join_graph: list[JoinEdge] = field(default_factory=list)
    provenance: str = "manual_config_v1"


@dataclass(slots=True)
class DialectProfile:
    name: str
    role: str
    notes: list[str] = field(default_factory=list)
    supports: list[str] = field(default_factory=list)
    restrictions: list[str] = field(default_factory=list)
