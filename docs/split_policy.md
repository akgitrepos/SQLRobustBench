# Split Policy (v1)

This document freezes how train and evaluation splits will be built.

## Split names

- `train`
- `validation`
- `test_in_domain`
- `test_ood`

## Core rule

Do not split purely at the row level. Split by latent program family and audit with hash-based checks.

## Holdout strategy

- hold out some `template_id` families from evaluation
- hold out some schema families for OOD evaluation
- hold out some corruption combinations for OOD evaluation
- hold out some higher-complexity regions for OOD evaluation

## Leakage checks

- exact tuple duplicate checks
- AST-hash overlap checks
- semantic-hash overlap checks
- template-family overlap checks
