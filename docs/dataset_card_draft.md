# SQLRobustBench

## Dataset summary

SQLRobustBench is a synthetic benchmark for SQL robustness under explicit schema, parsing, and logical validation constraints. The first public release focuses on two complementary task families:

- `SQLCorrupt`: invalid SQL detection and repair
- `SQLNormalize`: SQL canonicalization and normalization

The benchmark is designed for evaluation and controlled stress testing rather than for training production text-to-SQL systems on natural language supervision.

## Supported task types

- `generate_clean_query`
- `repair`
- `canonicalization`

## Why this dataset exists

Many SQL benchmarks focus on generation from natural language but do not test whether systems can reliably:

- detect malformed SQL
- identify schema and logic failures
- repair invalid queries
- normalize meaning-equivalent SQL into deterministic canonical forms

SQLRobustBench is intended to cover that gap.

## Data generation process

Rows are generated through a staged pipeline:

1. build schema families from structured YAML configs
2. generate clean SQL from latent query programs
3. validate generated SQL with parser, schema, and logical checks
4. derive corrupted or normalized variants
5. deduplicate and cap near-duplicate render variants
6. assign benchmark splits with template-family and OOD controls
7. export release records and manifest metadata

## Dataset fields

Important fields include:

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

The release uses:

- `train`
- `validation`
- `test_in_domain`
- `test_ood`

Splits are assigned with template-family and schema-family controls, then audited for exact, AST, semantic, and template leakage.

## Known limitations

- synthetic schemas are simpler than many production databases
- the SQL subset is intentionally constrained
- semantic equivalence is benchmark-defined rather than fully database-complete
- natural language supervision is not the primary target of this release

## Recommended uses

- benchmark SQL repair systems
- benchmark SQL canonicalization systems
- evaluate parser-aware and schema-aware LLM pipelines
- stress test robustness to syntax, schema, and logic failures

## Not recommended uses

- measuring broad real-world SQL coverage claims
- replacing enterprise SQL validation in production systems
- assuming equivalence guarantees outside the documented subset and policies

## Reproducibility

The benchmark is config-driven. Users can regenerate the corpus or create scaled variants by editing release configuration files such as `configs/release_2500.yaml`.

## Release checklist before publication

- final manual row review
- final wording and usage examples
- baseline results and evaluation scripts
- license selection
- publication to GitHub and Hugging Face
