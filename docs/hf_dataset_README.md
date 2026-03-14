---
pretty_name: SQLRobustBench
task_categories:
  - text-generation
  - text-classification
language:
  - sql
tags:
  - sql
  - robustness
  - benchmark
  - synthetic
size_categories:
  - 1K<n<10K
---

# SQLRobustBench

SQLRobustBench is a synthetic benchmark for SQL robustness under explicit schema, parsing, and logical validation constraints.

This release focuses on two benchmark families:

- `SQLCorrupt`: invalid SQL detection and repair
- `SQLNormalize`: deterministic SQL canonicalization and normalization

## What is in this release

- `data/records.jsonl`: one JSON object per benchmark row
- `manifest.json`: build statistics and split summary

Current release summary:

- `2500` rows total
- `623` clean reference rows
- `1312` repair rows
- `565` canonicalization rows

## Supported tasks

- `generate_clean_query`
- `repair`
- `canonicalization`

## Key row fields

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

## Splits

- `train`
- `validation`
- `test_in_domain`
- `test_ood`

The release is audited for exact, AST, semantic, and template-family leakage.

## Load with `datasets`

```python
from datasets import load_dataset

dataset = load_dataset("json", data_files="data/records.jsonl")
print(dataset["train"][0])
```

If this repository is published on Hugging Face as `YOUR_NAME/SQLRobustBench`, users can also clone it directly and load the JSONL file locally.

## Intended uses

- benchmark SQL repair systems
- benchmark SQL canonicalization systems
- evaluate parser-aware and schema-aware LLM pipelines
- stress test robustness to syntax, schema, and logic failures

## Limitations

- synthetic schemas are simpler than many production databases
- the SQL subset is intentionally constrained
- semantic equivalence is benchmark-defined rather than fully database-complete
- this release is for robustness benchmarking, not broad natural-language SQL supervision

## Reproducibility

The benchmark is generated from the companion code repository using a config-driven pipeline. The default release configuration targets a 2500-row corpus and can be scaled or modified.

Source code and generation pipeline:

- GitHub: `https://github.com/akgitrepos/SQLRobustBench`
