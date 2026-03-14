# Ambiguity Policy (v1)

This document defines when a row is considered too ambiguous for strict benchmark use.

## General rule

Keep only rows with a single intended gold target under benchmark policy.

## Exclude from strict gold sets

- queries with multiple equally plausible repairs
- corruptions that erase key intent information
- normalization cases with more than one acceptable canonical form under the current rules
- dialect cases that require unsupported engine-specific assumptions

## Row handling

- set `ambiguity_flag = true` for retained but non-strict rows
- exclude ambiguous rows from strict exact-match evaluation splits
- document ambiguity rates in the release notes

## Repair policy

Use minimal-intent-preserving repair, not aggressive rewriting.
