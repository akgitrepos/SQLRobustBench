from __future__ import annotations


def make_row_id(namespace: str, family: str, index: int) -> str:
    return f"{namespace}_{family}_{index:06d}"


def make_versioned_name(name: str, version: str) -> str:
    return f"{name}_{version}"
