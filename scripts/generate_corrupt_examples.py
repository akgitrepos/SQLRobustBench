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
    parser = argparse.ArgumentParser(description="Generate a corrupted SQL example from a clean query.")
    parser.add_argument("schema_config", help="Path to a schema YAML config file.")
    parser.add_argument("--template-id", default="baseline_summary", help="Template identifier.")
    parser.add_argument(
        "--complexity",
        default="medium",
        choices=["easy", "medium", "hard"],
        help="Target clean query complexity.",
    )
    parser.add_argument(
        "--operator",
        default="unknown_column",
        choices=["missing_comma", "unknown_column", "invalid_join_condition", "missing_group_by"],
        help="Corruption operator to apply.",
    )
    parser.add_argument("--seed", type=int, default=0, help="Deterministic seed.")
    return parser.parse_args()


def main() -> None:
    from sqlrobustbench.corrupt.recipes import create_corrupted_example, infer_failure_stage
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
    example = create_corrupted_example(program, generated_schema, args.operator)
    print("-- source_sql")
    print(example.source_sql)
    print("-- target_sql")
    print(example.target_sql)
    print("-- intended_failure_stage")
    print(example.intended_failure_stage)
    print("-- observed_failure_stage")
    print(infer_failure_stage(example, generated_schema))


if __name__ == "__main__":
    main()
