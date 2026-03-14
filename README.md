# SQLRobustBench

SQLRobustBench is a synthetic benchmark for SQL robustness tasks under explicit schema and validation constraints.

Links:

- GitHub: `https://github.com/akgitrepos/SQLRobustBench`
- Hugging Face dataset: `https://huggingface.co/datasets/sigdelakshey/SQLRobustBench`

It currently focuses on two benchmark families:

- `SQLCorrupt`: invalid SQL detection, error typing, localization, and repair
- `SQLNormalize`: SQL normalization and canonicalization under deterministic benchmark rules

The project is built for reproducibility: queries are generated from structured programs, validated against schemas, deduplicated, split with leakage controls, and exported as release-ready records.

## Dataset Summary

SQLRobustBench evaluates SQL tasks that require more than straightforward generation:

- generating valid clean SQL under schema constraints
- detecting and repairing corrupted SQL
- canonicalizing meaning-preserving SQL variants into deterministic targets

The benchmark is intended for evaluation and robustness analysis, not for broad natural-language-to-SQL supervision claims.

## What is included

- configurable schema-family generation
- deterministic clean query generation
- parser-backed and schema-aware validation
- labeled corruption generation
- normalization and canonicalization targets with rule tracking
- deduplication and split auditing
- corpus generation for release bundles

## Current dataset build

The repository includes a configurable release pipeline and a generated local build at `data/release/sqlrobustbench_v1/`.

Current build summary:

- `2500` rows total
- `623` clean reference rows
- `1312` repair rows
- `565` canonicalization rows
- zero exact, AST, semantic, and template-family leakage in the current split audit

Published dataset assets:

- `data/records.jsonl`
- `manifest.json`
- `code/` generation assets on the Hugging Face dataset repo

Generated release artifacts are local build outputs and are intentionally ignored by git.

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest
```

## Generate the benchmark corpus

Build the default release bundle:

```bash
python scripts/export_hf.py configs/release_2500.yaml --output-dir data/release/sqlrobustbench_v1
```

This writes:

- `data/release/sqlrobustbench_v1/data/records.jsonl`
- `data/release/sqlrobustbench_v1/manifest.json`

## Inspect the generated rows

The exported dataset uses one JSON object per row. Core fields include:

- `task`: benchmark task such as `generate_clean_query`, `repair`, or `canonicalization`
- `source_sql`: model input SQL
- `target_sql`: gold output SQL when applicable
- `schema_family` and `db_schema_id`: schema provenance
- `template_id`: latent query family identifier
- `source_ast_hash`, `target_ast_hash`, `semantic_hash`: audit and deduplication keys
- `error_tags` and `corruption_recipe_id`: corruption metadata
- `normalization_rules`: canonicalization rule trace
- `split`: assigned benchmark split

## Load the published dataset

```python
from datasets import load_dataset

dataset = load_dataset("sigdelakshey/SQLRobustBench")
print(dataset["train"][0])
```

## Customize the dataset

Edit `configs/release_2500.yaml` to control:

- total row count
- clean/corrupt/normalize task mix
- schema families
- complexity mix
- template pools
- corruption operators
- deduplication oversampling
- split holdouts for validation and OOD evaluation

This makes it possible to regenerate the release exactly or create custom benchmark variants.

## Repository layout

- `configs/`: benchmark, release, dialect, and schema configs
- `docs/`: benchmark spec and policy documents
- `metadata/`: machine-readable taxonomies and rule registries
- `scripts/`: command-line entry points for generation and export
- `src/sqlrobustbench/`: Python implementation
- `tests/`: automated tests for generation, validation, deduplication, and splits

## Important docs

- `docs/SQLCorrupt_SQLNormalize.md`: benchmark specification
- `docs/canonicalization_policy.md`: canonicalization policy
- `docs/ambiguity_policy.md`: ambiguity handling
- `docs/corruption_taxonomy.md`: corruption taxonomy
- `docs/split_policy.md`: split methodology
- `docs/dataset_card_draft.md`: draft dataset card for release

## Quality and release expectations

Before publication, the intended review flow is:

1. inspect a representative sample from `data/release/sqlrobustbench_v1/data/records.jsonl`
2. review `data/release/sqlrobustbench_v1/manifest.json`
3. confirm split behavior, duplicate controls, and example quality
4. finalize the dataset card and release metadata

## Citation

If you use SQLRobustBench, cite the repository and include the release manifest details.

```bibtex
@misc{sqlrobustbench2026,
  title        = {SQLRobustBench: A Synthetic Benchmark for SQL Robustness},
  author       = {Sigdel, Akshey},
  year         = {2026},
  howpublished = {GitHub and Hugging Face dataset repository},
  url          = {https://github.com/akgitrepos/SQLRobustBench}
}
```

## Development checks

```bash
ruff check src tests scripts
pytest
```
