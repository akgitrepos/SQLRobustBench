from __future__ import annotations

from sqlrobustbench.queries.ast import QueryProgram


def make_stub_query_program(template_id: str) -> QueryProgram:
    return QueryProgram(template_id=template_id)
