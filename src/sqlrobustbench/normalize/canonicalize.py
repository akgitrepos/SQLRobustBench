from __future__ import annotations


def canonicalize_stub(sql: str) -> str:
    return " ".join(sql.strip().split())
