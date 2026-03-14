from __future__ import annotations

from sqlrobustbench.hashing import stable_hash


def semantic_group_hash(payload: dict) -> str:
    return stable_hash(payload)
