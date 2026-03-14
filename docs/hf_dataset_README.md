---
pretty_name: SQLRobustBench
task_categories:
  - text-generation
  - text-classification
language:
  - en
tags:
  - synthetic
  - sql
  - robustness
  - benchmark
  - evaluation
  - canonicalization
  - repair
size_categories:
  - 1K<n<10K
---

# SQLRobustBench

SQLRobustBench is a synthetic benchmark for SQL robustness under explicit schema, parsing, and logical validation constraints.

## Dataset Summary

This release focuses on two benchmark families:

- `SQLCorrupt`: invalid SQL detection and repair
- `SQLNormalize`: deterministic SQL canonicalization and normalization

SQLRobustBench evaluates model behavior on SQL tasks that require more than straightforward generation:

- generating valid clean SQL under schema constraints
- detecting and repairing corrupted SQL
- canonicalizing meaning-preserving SQL variants into deterministic targets

The benchmark is designed for evaluation and robustness analysis rather than for broad natural-language-to-SQL supervision.

## What Is In This Release

- `data/records.jsonl`: one JSON object per benchmark row
- `manifest.json`: build statistics and split summary
- `code/`: generation, validation, split, and export assets used to build the release

Current release summary:

- `2500` rows total
- `623` clean reference rows
- `1312` repair rows
- `565` canonicalization rows

## Supported Tasks

- `generate_clean_query`
- `repair`
- `canonicalization`

## Data Splits

This release provides:

- `train`
- `validation`
- `test_in_domain`
- `test_ood`

The current release is audited for exact, AST, semantic, and template-family leakage.

## Data Fields

- `id`
- `task`
- `config`
- `source_sql`
- `target_sql`
- `schema_family`
- `db_schema_id`
- `template_id`
- `source_ast_hash`
- `target_ast_hash`
- `semantic_hash`
- `error_tags`
- `corruption_recipe_id`
- `normalization_rules`
- `split`

## Dataset Creation

Rows are generated through a staged pipeline:

1. build schema families from structured YAML configs
2. generate clean SQL from latent query programs
3. validate generated SQL with parser, schema, and logical checks
4. derive corrupted or normalized variants
5. deduplicate exact repeats and cap render variants
6. assign splits with template-family and OOD controls
7. export records plus release metadata

The release configuration used for this build is included under `code/configs/release_2500.yaml`.

## Validation And QA

Quality checks include:

- parser validation of generated SQL
- schema-aware reference resolution
- logical validation of aggregation and join behavior
- corruption-stage validation against intended failure types
- deduplication and split leakage auditing

Release statistics are stored in `manifest.json`.

## Load with `datasets`

```python
from datasets import load_dataset

dataset = load_dataset("json", data_files="data/records.jsonl")
print(dataset["train"][0])
```

Users can also clone the dataset repository directly and inspect the release manifest and generation assets.

## Intended Uses

- benchmark SQL repair systems
- benchmark SQL canonicalization systems
- evaluate parser-aware and schema-aware LLM pipelines
- stress test robustness to syntax, schema, and logic failures

## Out-Of-Scope Uses

- claiming broad coverage of all SQL dialect behavior
- replacing production SQL validation systems
- treating benchmark-defined canonicalization as universal SQL equivalence

## Limitations

- synthetic schemas are simpler than many production databases
- the SQL subset is intentionally constrained
- semantic equivalence is benchmark-defined rather than fully database-complete
- this release is for robustness benchmarking, not broad natural-language SQL supervision

## Reproducibility

The benchmark is generated from the companion code repository using a config-driven pipeline. The default release configuration targets a 2500-row corpus and can be scaled or modified.

Source code and generation pipeline:

- GitHub: `https://github.com/akgitrepos/SQLRobustBench`

## Citation

If you use this dataset, cite the dataset repository and include the release manifest details from `manifest.json`.
