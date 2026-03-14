from __future__ import annotations


def parseable_stub(sql: str) -> bool:
    return bool(sql.strip())
