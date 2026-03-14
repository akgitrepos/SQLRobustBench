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
    parser = argparse.ArgumentParser(description="Generate a clean SQL query from a schema config.")
    parser.add_argument("schema_config", help="Path to a schema YAML config file.")
    parser.add_argument("--template-id", default="baseline_summary", help="Template identifier.")
    parser.add_argument(
        "--complexity",
        default="easy",
        choices=["easy", "medium", "hard"],
        help="Target query complexity.",
    )
    parser.add_argument("--seed", type=int, default=0, help="Deterministic seed.")
    return parser.parse_args()


def main() -> None:
    from sqlrobustbench.queries.generator import build_query_program
    from sqlrobustbench.queries.renderer import render_sql
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
    print(render_sql(program))


if __name__ == "__main__":
    main()
