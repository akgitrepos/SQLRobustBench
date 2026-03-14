from __future__ import annotations

from collections import defaultdict

from sqlrobustbench.hashing import stable_hash
from sqlrobustbench.types import BenchmarkRow


def semantic_group_hash(payload: dict) -> str:
    return stable_hash(payload)


def exact_row_key(row: BenchmarkRow) -> str:
    return stable_hash(
        {
            "task": row.task,
            "schema": row.db_schema_id,
            "source_sql": row.source_sql,
            "target_sql": row.target_sql,
            "dialect": row.dialect,
        }
    )


def template_family_key(row: BenchmarkRow) -> str:
    return stable_hash(
        {
            "schema_family": row.schema_family,
            "template_id": row.template_id,
        }
    )


def deduplicate_rows(rows: list[BenchmarkRow]) -> tuple[list[BenchmarkRow], dict[str, int]]:
    seen_exact: set[str] = set()
    deduped: list[BenchmarkRow] = []
    stats = {
        "input_rows": len(rows),
        "removed_exact_duplicates": 0,
    }

    for row in rows:
        key = exact_row_key(row)
        if key in seen_exact:
            stats["removed_exact_duplicates"] += 1
            continue
        seen_exact.add(key)
        deduped.append(row)

    stats["output_rows"] = len(deduped)
    return deduped, stats


def group_rows_by_semantic_hash(rows: list[BenchmarkRow]) -> dict[str, list[BenchmarkRow]]:
    groups: dict[str, list[BenchmarkRow]] = defaultdict(list)
    for row in rows:
        groups[row.semantic_hash].append(row)
    return dict(groups)


def cap_render_variants(rows: list[BenchmarkRow], max_per_group: int = 2) -> tuple[list[BenchmarkRow], dict[str, int]]:
    kept: list[BenchmarkRow] = []
    groups = group_rows_by_semantic_hash(rows)
    removed = 0

    for semantic_hash, group in groups.items():
        _ = semantic_hash
        variant_seen: set[str] = set()
        group_kept = 0
        for row in group:
            variant_id = row.render_variant_id or exact_row_key(row)
            if variant_id in variant_seen:
                removed += 1
                continue
            if group_kept >= max_per_group:
                removed += 1
                continue
            variant_seen.add(variant_id)
            group_kept += 1
            kept.append(row)

    return kept, {"removed_render_variants": removed, "output_rows": len(kept)}
