from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from sqlrobustbench.hashing import stable_hash
from sqlrobustbench.dedup.hashes import template_family_key
from sqlrobustbench.dedup.leakage import LeakageReport, audit_split_leakage
from sqlrobustbench.types import BenchmarkRow


SPLIT_NAMES = [
    "train",
    "validation",
    "test_in_domain",
    "test_ood",
]


@dataclass(slots=True)
class SplitPlan:
    rows: list[BenchmarkRow]
    split_counts: dict[str, int]
    leakage_report: LeakageReport


def build_splits(
    rows: list[BenchmarkRow],
    *,
    validation_template_families: set[str] | None = None,
    in_domain_template_families: set[str] | None = None,
    ood_schema_families: set[str] | None = None,
    ood_template_ids: set[str] | None = None,
    hard_complexity_to_ood: bool = False,
    in_domain_eval_ratio: float = 0.2,
) -> SplitPlan:
    validation_template_families = validation_template_families or set()
    in_domain_template_families = in_domain_template_families or set()
    ood_schema_families = ood_schema_families or set()
    ood_template_ids = ood_template_ids or set()

    grouped_rows: dict[str, list[BenchmarkRow]] = defaultdict(list)
    for row in rows:
        grouped_rows[_split_group_key(row)].append(row)

    assigned_rows: list[BenchmarkRow] = []
    for group_key, group in grouped_rows.items():
        split = _choose_split(
            group[0],
            group_key=group_key,
            validation_template_families=validation_template_families,
            in_domain_template_families=in_domain_template_families,
            ood_schema_families=ood_schema_families,
            ood_template_ids=ood_template_ids,
            hard_complexity_to_ood=hard_complexity_to_ood,
            in_domain_eval_ratio=in_domain_eval_ratio,
        )
        assigned_rows.extend(_replace_split(row, split) for row in group)

    split_counts = _count_splits(assigned_rows)
    leakage_report = audit_split_leakage(assigned_rows)
    return SplitPlan(rows=assigned_rows, split_counts=split_counts, leakage_report=leakage_report)


def summarize_split_plan(rows: list[BenchmarkRow]) -> dict[str, dict[str, int]]:
    summary: dict[str, dict[str, int]] = {
        "splits": _count_splits(rows),
        "schema_families": defaultdict(int),
        "complexities": defaultdict(int),
    }
    for row in rows:
        summary["schema_families"][f"{row.split}:{row.schema_family}"] += 1
        summary["complexities"][f"{row.split}:{row.complexity}"] += 1
    return {
        "splits": dict(summary["splits"]),
        "schema_families": dict(summary["schema_families"]),
        "complexities": dict(summary["complexities"]),
    }


def template_family_ids(rows: list[BenchmarkRow]) -> set[str]:
    return {template_family_key(row) for row in rows}


def _choose_split(
    row: BenchmarkRow,
    *,
    group_key: str,
    validation_template_families: set[str],
    in_domain_template_families: set[str],
    ood_schema_families: set[str],
    ood_template_ids: set[str],
    hard_complexity_to_ood: bool,
    in_domain_eval_ratio: float,
) -> str:
    family_key = template_family_key(row)
    if row.schema_family in ood_schema_families:
        return "test_ood"
    if row.template_id in ood_template_ids:
        return "test_ood"
    if hard_complexity_to_ood and row.complexity == "hard":
        return "test_ood"
    if family_key in validation_template_families:
        return "validation"
    if family_key in in_domain_template_families:
        return "test_in_domain"
    bucket = int(stable_hash({"group_key": group_key})[:8], 16) % 100
    if bucket < int(in_domain_eval_ratio * 100):
        return "test_in_domain"
    return "train"


def _split_group_key(row: BenchmarkRow) -> str:
    return template_family_key(row)


def _replace_split(row: BenchmarkRow, split: str) -> BenchmarkRow:
    return BenchmarkRow(
        id=row.id,
        config=row.config,
        task=row.task,
        dialect=row.dialect,
        db_schema_id=row.db_schema_id,
        schema_family=row.schema_family,
        source_sql=row.source_sql,
        is_source_valid=row.is_source_valid,
        complexity=row.complexity,
        template_id=row.template_id,
        source_ast_hash=row.source_ast_hash,
        semantic_hash=row.semantic_hash,
        provenance=row.provenance,
        split=split,
        target_sql=row.target_sql,
        error_tags=list(row.error_tags),
        normalization_rules=list(row.normalization_rules),
        num_joins=row.num_joins,
        nesting_depth=row.nesting_depth,
        corruption_recipe_id=row.corruption_recipe_id,
        target_ast_hash=row.target_ast_hash,
        ambiguity_flag=row.ambiguity_flag,
        render_variant_id=row.render_variant_id,
        extra=dict(row.extra),
    )


def _count_splits(rows: list[BenchmarkRow]) -> dict[str, int]:
    counts = {name: 0 for name in SPLIT_NAMES}
    for row in rows:
        counts[row.split] = counts.get(row.split, 0) + 1
    return counts
