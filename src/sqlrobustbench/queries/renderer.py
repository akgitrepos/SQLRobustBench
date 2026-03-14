from __future__ import annotations

from sqlrobustbench.queries.ast import QueryProgram


def render_sql(program: QueryProgram) -> str:
    select_clause = ", ".join(
        f"{item.expression} AS {item.alias}" if item.alias else item.expression
        for item in program.select_items
    )
    lines = [f"SELECT {select_clause}"]
    lines.append(f"FROM {program.base_table.name} AS {program.base_table.alias}")

    for join in program.joins:
        lines.append(
            f"{join.join_type} {join.right_table.name} AS {join.right_table.alias} ON {join.on_expression}"
        )

    if program.where_predicates:
        where_clause = " AND ".join(predicate.expression for predicate in program.where_predicates)
        lines.append(f"WHERE {where_clause}")

    if program.group_by:
        lines.append(f"GROUP BY {', '.join(program.group_by)}")

    if program.having:
        having_clause = " AND ".join(predicate.expression for predicate in program.having)
        lines.append(f"HAVING {having_clause}")

    if program.order_by:
        order_clause = ", ".join(
            f"{item.expression} {item.direction}" for item in program.order_by
        )
        lines.append(f"ORDER BY {order_clause}")

    if program.limit is not None:
        lines.append(f"LIMIT {program.limit}")

    return "\n".join(lines)
