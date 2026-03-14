from __future__ import annotations

from sqlrobustbench.queries.ast import QueryProgram


def estimate_complexity(program: QueryProgram) -> str:
    if len(program.joins) >= 2 or program.having:
        return "hard"
    if program.joins or program.group_by:
        return "medium"
    return "easy"
