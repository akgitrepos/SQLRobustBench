# Canonicalization Policy (v1)

This document freezes the canonicalization rules for the first release.

## Goal

Produce a deterministic canonical SQL target for valid source queries while preserving semantics under the benchmark's supported SQL subset.

## Allowed rule families

- keyword casing normalization
- deterministic whitespace and clause formatting
- explicit aliases for derived expressions
- canonical alias renaming where alias references remain internal
- predicate ordering for safe conjunctive predicates
- inner-join normalization when null semantics are unchanged
- quote normalization under a fixed dialect policy

## Disallowed or restricted rules

- projection reordering by default
- left-join reordering unless proven safe
- transformations involving volatile functions
- optimizer-hint manipulation
- semantic rewrites that depend on full DB engine behavior

## Preconditions

Every normalization rule must declare:

- supported SQL fragment
- supported dialects
- semantic safety assumptions
- whether execution validation is required

## Canonical target policy

- one canonical target per non-ambiguous row
- ambiguous cases are excluded from strict exact-match evaluation
- canonical outputs must be reproducible from rule order plus latent program state
