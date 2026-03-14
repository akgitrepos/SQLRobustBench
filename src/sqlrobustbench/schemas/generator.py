from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import json

import yaml

from sqlrobustbench.ids import make_versioned_name
from sqlrobustbench.types import (
    ColumnSpec,
    ForeignKeySpec,
    GeneratedSchema,
    JoinEdge,
    SchemaDefinition,
    SchemaFamilyConfig,
    TableSpec,
)


def load_schema_family(config: dict) -> SchemaFamilyConfig:
    return SchemaFamilyConfig(**config)


def _load_column(column_config: dict) -> ColumnSpec:
    return ColumnSpec(**column_config)


def _load_foreign_key(foreign_key_config: dict) -> ForeignKeySpec:
    return ForeignKeySpec(**foreign_key_config)


def _load_table(table_config: dict) -> TableSpec:
    columns = [_load_column(column) for column in table_config.get("columns", [])]
    foreign_keys = [_load_foreign_key(fk) for fk in table_config.get("foreign_keys", [])]
    return TableSpec(
        name=table_config["name"],
        description=table_config["description"],
        primary_key=table_config["primary_key"],
        columns=columns,
        foreign_keys=foreign_keys,
    )


def load_schema_definition(path: str | Path) -> SchemaDefinition:
    with Path(path).open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)

    tables = [_load_table(table) for table in config.get("tables", [])]
    return SchemaDefinition(
        schema_family=config["schema_family"],
        version=config["version"],
        description=config["description"],
        tables=tables,
        seed_hints=config.get("seed_hints", []),
    )


def build_join_graph(schema: SchemaDefinition) -> list[JoinEdge]:
    join_graph: list[JoinEdge] = []
    for table in schema.tables:
        for foreign_key in table.foreign_keys:
            join_graph.append(
                JoinEdge(
                    left_table=table.name,
                    left_column=foreign_key.column,
                    right_table=foreign_key.references_table,
                    right_column=foreign_key.references_column,
                )
            )
    return join_graph


def build_generated_schema(schema: SchemaDefinition) -> GeneratedSchema:
    return GeneratedSchema(
        schema_id=make_versioned_name(schema.schema_family, schema.version),
        schema_family=schema.schema_family,
        version=schema.version,
        description=schema.description,
        tables=schema.tables,
        join_graph=build_join_graph(schema),
    )


def serialize_generated_schema(schema: GeneratedSchema) -> dict:
    return asdict(schema)


def write_generated_schema(schema: GeneratedSchema, output_path: str | Path) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(serialize_generated_schema(schema), indent=2), encoding="utf-8")
