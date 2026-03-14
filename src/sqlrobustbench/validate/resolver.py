from __future__ import annotations


def resolve_stub(sql: str, schema_id: str) -> bool:
    return bool(sql.strip()) and bool(schema_id)
