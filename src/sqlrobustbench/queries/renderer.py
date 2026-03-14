from __future__ import annotations

from sqlrobustbench.queries.ast import QueryProgram


def render_stub(program: QueryProgram) -> str:
    if not program.select_expressions or not program.from_tables:
        return "SELECT 1"
    return f"SELECT {', '.join(program.select_expressions)} FROM {', '.join(program.from_tables)}"
