# SQLRobustBench

SQLRobustBench is the working repository for building `SQLCorrupt` and `SQLNormalize`.

Current goals:

- lock the v1 benchmark scope
- define dataset and policy documents before generation
- scaffold the Python package for schema, query, corruption, normalization, validation, deduplication, and export flows
- prepare a reproducible path to a professional Hugging Face release

## Repository layout

- `docs/`: source-of-truth benchmark and policy documents
- `configs/`: benchmark, dialect, and schema-family configs
- `src/sqlrobustbench/`: Python package and typed models
- `scripts/`: future entry points for generation, validation, and export
- `metadata/`: machine-readable taxonomy and rule files
- `tests/`: starter tests for core invariants

## Current status

- repository structure, policies, and versioning setup are in place
- the initial benchmark scope is frozen for the SQL subset, tasks, dialects, and split strategy

## Recommended next implementation steps

1. Implement typed schema-family models and schema generation.
2. Implement the latent query AST and clean query generator.
3. Add parser-backed validation before corruption and normalization.
