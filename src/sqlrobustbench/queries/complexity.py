from __future__ import annotations

from sqlrobustbench.queries.ast import QueryProgram


def estimate_complexity(program: QueryProgram) -> str:
    if len(program.joins) >= 2 or program.having:
        return "hard"
    if program.joins or program.group_by or any(item.is_aggregate for item in program.select_items):
        return "medium"
    return "easy"
