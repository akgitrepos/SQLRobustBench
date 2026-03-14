# pyright: reportMissingImports=false

from __future__ import annotations

from dataclasses import dataclass, field

from sqlglot import parse_one
from sqlglot.errors import ParseError


DIALECT_MAP = {
    "ansi_like": "",
    "postgres_like": "postgres",
}


@dataclass(slots=True)
class ParseResult:
    is_valid: bool
    normalized_sql: str | None = None
    errors: list[str] = field(default_factory=list)


def parse_sql(sql: str, dialect: str = "") -> ParseResult:
    if not sql.strip():
        return ParseResult(is_valid=False, errors=["SQL string is empty."])

    sqlglot_dialect = DIALECT_MAP.get(dialect, dialect)

    try:
        expression = parse_one(sql, read=sqlglot_dialect or None)
    except (ParseError, ValueError) as exc:
        return ParseResult(is_valid=False, errors=[str(exc)])

    return ParseResult(is_valid=True, normalized_sql=expression.sql())
