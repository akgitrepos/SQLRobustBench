from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from sqlrobustbench.dedup.hashes import template_family_key
from sqlrobustbench.types import BenchmarkRow


def same_template_family(a: str, b: str) -> bool:
    return a == b


@dataclass(slots=True)
class LeakageReport:
    has_leakage: bool
    overlap_counts: dict[str, int]
    details: dict[str, list[str]] = field(default_factory=dict)


def audit_split_leakage(rows: list[BenchmarkRow]) -> LeakageReport:
    by_split: dict[str, list[BenchmarkRow]] = defaultdict(list)
    for row in rows:
        by_split[row.split].append(row)

    exact_overlap: set[str] = set()
    ast_overlap: set[str] = set()
    semantic_overlap: set[str] = set()
    template_overlap: set[str] = set()

    split_names = sorted(by_split)
    for index, left_split in enumerate(split_names):
        left_rows = by_split[left_split]
        for right_split in split_names[index + 1 :]:
            right_rows = by_split[right_split]
            exact_overlap.update(_shared_exact_keys(left_rows, right_rows))
            ast_overlap.update(_shared_values(left_rows, right_rows, lambda row: row.source_ast_hash))
            semantic_overlap.update(_shared_values(left_rows, right_rows, lambda row: row.semantic_hash))
            template_overlap.update(
                _shared_values(left_rows, right_rows, lambda row: template_family_key(row))
            )

    overlap_counts = {
        "exact": len(exact_overlap),
        "ast": len(ast_overlap),
        "semantic": len(semantic_overlap),
        "template_family": len(template_overlap),
    }
    details = {
        "exact": sorted(exact_overlap),
        "ast": sorted(ast_overlap),
        "semantic": sorted(semantic_overlap),
        "template_family": sorted(template_overlap),
    }
    return LeakageReport(has_leakage=any(overlap_counts.values()), overlap_counts=overlap_counts, details=details)


def _shared_exact_keys(left_rows: list[BenchmarkRow], right_rows: list[BenchmarkRow]) -> set[str]:
    left_keys = {_exact_tuple_key(row) for row in left_rows}
    right_keys = {_exact_tuple_key(row) for row in right_rows}
    return left_keys & right_keys


def _exact_tuple_key(row: BenchmarkRow) -> str:
    return "|".join(
        [
            row.task,
            row.db_schema_id,
            row.source_sql,
            row.target_sql or "",
            row.dialect,
        ]
    )


def _shared_values(
    left_rows: list[BenchmarkRow],
    right_rows: list[BenchmarkRow],
    value_getter,
) -> set[str]:
    left_values = {value_getter(row) for row in left_rows if value_getter(row)}
    right_values = {value_getter(row) for row in right_rows if value_getter(row)}
    return left_values & right_values
