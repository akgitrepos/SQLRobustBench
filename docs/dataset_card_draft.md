# SQLRobustBench Dataset Card Draft

## Purpose

SQLRobustBench evaluates SQL robustness tasks beyond plain text-to-SQL generation, with an initial focus on corruption detection and repair plus SQL canonicalization and normalization.

## Included benchmark families

- SQLCorrupt
- SQLNormalize

## v1 constraints

- controlled SQL subset
- validator-driven labels
- explicit ambiguity policy
- deduplication and leakage controls

## To complete before release

- final dataset size per config
- exact generation pipeline description
- final validation stack
- baseline metrics
- known limitations and recommended use
