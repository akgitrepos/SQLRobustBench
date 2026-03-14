from __future__ import annotations

from sqlrobustbench.types import SchemaFamilyConfig


def load_schema_family(config: dict) -> SchemaFamilyConfig:
    return SchemaFamilyConfig(**config)
