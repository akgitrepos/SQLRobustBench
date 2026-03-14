from __future__ import annotations

from dataclasses import dataclass


NORMALIZATION_RULE_FAMILIES = [
    "surface",
    "structural",
    "dialect",
]


@dataclass(frozen=True, slots=True)
class NormalizationRule:
    rule_id: str
    family: str
    description: str


RULE_REGISTRY = {
    "keyword_casing": NormalizationRule(
        rule_id="keyword_casing",
        family="surface",
        description="Render SQL keywords in uppercase.",
    ),
    "deterministic_aliases": NormalizationRule(
        rule_id="deterministic_aliases",
        family="structural",
        description="Rename table aliases to deterministic canonical names.",
    ),
    "deterministic_spacing": NormalizationRule(
        rule_id="deterministic_spacing",
        family="surface",
        description="Render clauses with deterministic line breaks and spacing.",
    ),
    "explicit_order_direction": NormalizationRule(
        rule_id="explicit_order_direction",
        family="surface",
        description="Render ORDER BY items with explicit direction tokens.",
    ),
}
