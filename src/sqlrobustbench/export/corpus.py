from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from sqlrobustbench.corrupt.recipes import create_corrupted_example, validate_corrupted_example
from sqlrobustbench.dedup.hashes import cap_render_variants, deduplicate_rows
from sqlrobustbench.export.hf_packaging import create_release_bundle
from sqlrobustbench.export.rows import build_clean_row, build_corruption_row, build_normalization_row
from sqlrobustbench.ids import make_row_id
from sqlrobustbench.normalize.canonicalize import create_normalization_example
from sqlrobustbench.queries.generator import build_query_program
from sqlrobustbench.queries.complexity import estimate_complexity
from sqlrobustbench.queries.renderer import render_sql
from sqlrobustbench.schemas.generator import build_generated_schema, load_schema_definition
from sqlrobustbench.splits.builder import build_splits, summarize_split_plan
from sqlrobustbench.types import BenchmarkRow, GeneratedSchema
from sqlrobustbench.validate.pipeline import validate_generated_query


@dataclass(slots=True)
class CorpusBuildResult:
    rows: list[BenchmarkRow]
    stats: dict[str, Any]
    release_paths: dict[str, str]


def load_corpus_config(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def build_corpus_from_config(config: dict[str, Any], output_dir: str | Path) -> CorpusBuildResult:
    schemas = _load_schemas(config["schemas"])
    generation = config["generation"]
    target_rows = int(generation["target_total_rows"])
    task_targets = generation["task_targets"]
    complexities = generation["complexities"]
    templates = generation["templates"]
    operators = generation["corruption_operators"]
    split_cfg = config["splits"]

    rows: list[BenchmarkRow] = []
    counters = {"clean": 0, "corrupt": 0, "normalize": 0}
    seed = int(generation.get("seed_start", 0))
    attempt = 0
    max_attempts = int(generation.get("max_attempts", target_rows * 20))
    oversample_factor = int(generation.get("oversample_factor", 4))
    candidate_target = target_rows * max(oversample_factor, 1)

    while len(rows) < candidate_target and attempt < max_attempts:
        schema = schemas[attempt % len(schemas)]
        complexity = complexities[attempt % len(complexities)]
        template_id = templates[complexity][attempt % len(templates[complexity])]
        program = build_query_program(schema, template_id=template_id, complexity=complexity, seed=seed + attempt)
        sql = render_sql(program)
        report = validate_generated_query(program, schema, sql)
        if not report.is_valid:
            attempt += 1
            continue

        task_kind = _next_task_kind(counters, task_targets)
        row = _build_task_row(task_kind, program, schema, operators, counters)
        if row is not None:
            rows.append(row)
        attempt += 1

    deduped_rows, dedup_stats = deduplicate_rows(rows)
    variant_capped_rows, variant_stats = cap_render_variants(
        deduped_rows,
        max_per_group=int(generation.get("max_render_variants_per_semantic_group", 2)),
    )

    if len(variant_capped_rows) < target_rows:
        raise ValueError(
            f"Generated only {len(variant_capped_rows)} unique rows after deduplication, need {target_rows}."
        )

    final_rows = variant_capped_rows[:target_rows]
    validation_holdouts = _template_family_holdouts(final_rows, int(split_cfg.get("validation_template_families", 1)))
    in_domain_holdouts = _template_family_holdouts(
        final_rows,
        int(split_cfg.get("in_domain_template_families", 1)),
        skip=validation_holdouts,
    )
    split_plan = build_splits(
        final_rows,
        validation_template_families=validation_holdouts,
        in_domain_template_families=in_domain_holdouts,
        ood_schema_families=set(split_cfg.get("ood_schema_families", [])),
        ood_template_ids=set(split_cfg.get("ood_template_ids", [])),
        hard_complexity_to_ood=bool(split_cfg.get("hard_complexity_to_ood", False)),
        in_domain_eval_ratio=float(split_cfg.get("in_domain_eval_ratio", 0.2)),
    )
    stats = {
        "requested_rows": target_rows,
        "generated_candidates": len(rows),
        "candidate_target": candidate_target,
        "dedup": dedup_stats,
        "render_variants": variant_stats,
        "final_rows": len(split_plan.rows),
        "split_counts": split_plan.split_counts,
        "split_summary": summarize_split_plan(split_plan.rows),
        "leakage_report": {
            "has_leakage": split_plan.leakage_report.has_leakage,
            "overlap_counts": split_plan.leakage_report.overlap_counts,
        },
        "task_counts": _task_counts(split_plan.rows),
    }
    release_paths = create_release_bundle(
        split_plan.rows,
        output_dir,
        dataset_name=config["dataset"]["name"],
        stats=stats,
    )
    return CorpusBuildResult(rows=split_plan.rows, stats=stats, release_paths=release_paths)


def _load_schemas(schema_config_paths: list[str]) -> list[GeneratedSchema]:
    return [build_generated_schema(load_schema_definition(path)) for path in schema_config_paths]


def _next_task_kind(counters: dict[str, int], targets: dict[str, int]) -> str:
    ratios = {
        key: counters[key] / max(targets[key], 1)
        for key in ["clean", "corrupt", "normalize"]
    }
    return min(ratios, key=lambda key: ratios[key])


def _build_task_row(
    task_kind: str,
    program,
    schema: GeneratedSchema,
    operators: list[str],
    counters: dict[str, int],
) -> BenchmarkRow | None:
    if task_kind == "clean":
        counters["clean"] += 1
        return build_clean_row(
            row_id=make_row_id("sqlclean", schema.schema_family, counters["clean"]),
            program=program,
            schema=schema,
            split="train",
        )

    if task_kind == "corrupt":
        operator_name = operators[counters["corrupt"] % len(operators)]
        try:
            corruption = create_corrupted_example(program, schema, operator_name)
        except ValueError:
            return None
        if not validate_corrupted_example(corruption, schema):
            return None
        counters["corrupt"] += 1
        return build_corruption_row(
            row_id=make_row_id("sqlcorrupt", schema.schema_family, counters["corrupt"]),
            program=program,
            schema=schema,
            record=corruption.record,
            split="train",
            config=f"corrupt_{estimate_complexity(program)}",
        )

    normalization = create_normalization_example(program)
    counters["normalize"] += 1
    return build_normalization_row(
        row_id=make_row_id("sqlnormalize", schema.schema_family, counters["normalize"]),
        program=program,
        schema=schema,
        result=normalization,
        split="train",
    )


def _template_family_holdouts(rows: list[BenchmarkRow], count: int, skip: set[str] | None = None) -> set[str]:
    if count <= 0:
        return set()
    skip = skip or set()
    family_keys: list[str] = []
    seen: set[str] = set()
    from sqlrobustbench.dedup.hashes import template_family_key

    for row in rows:
        key = template_family_key(row)
        if key in seen or key in skip:
            continue
        seen.add(key)
        family_keys.append(key)
    return set(family_keys[:count])


def _task_counts(rows: list[BenchmarkRow]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        counts[row.task] = counts.get(row.task, 0) + 1
    return counts
