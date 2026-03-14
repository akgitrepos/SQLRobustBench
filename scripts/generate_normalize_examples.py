# pyright: reportMissingImports=false

from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a normalization example from a clean query.")
    parser.add_argument("schema_config", help="Path to a schema YAML config file.")
    parser.add_argument("--template-id", default="baseline_summary", help="Template identifier.")
    parser.add_argument(
        "--complexity",
        default="medium",
        choices=["easy", "medium", "hard"],
        help="Target clean query complexity.",
    )
    parser.add_argument("--seed", type=int, default=0, help="Deterministic seed.")
    return parser.parse_args()


def main() -> None:
    from sqlrobustbench.normalize.canonicalize import create_normalization_example
    from sqlrobustbench.queries.generator import build_query_program
    from sqlrobustbench.schemas.generator import build_generated_schema, load_schema_definition

    args = parse_args()
    schema_definition = load_schema_definition(args.schema_config)
    generated_schema = build_generated_schema(schema_definition)
    program = build_query_program(
        generated_schema,
        template_id=args.template_id,
        complexity=args.complexity,
        seed=args.seed,
    )
    result = create_normalization_example(program)
    print("-- source_sql")
    print(result.source_sql)
    print("-- target_sql")
    print(result.target_sql)
    print("-- rules")
    print(", ".join(result.record.rule_ids))


if __name__ == "__main__":
    main()
