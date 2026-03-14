from __future__ import annotations


def make_recipe_id(*parts: str) -> str:
    return "+".join(parts)
