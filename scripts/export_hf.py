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
    parser = argparse.ArgumentParser(description="Build a small release bundle from generated benchmark rows.")
    parser.add_argument("schema_config", help="Path to a schema YAML config file.")
    parser.add_argument("--output-dir", default="data/release/sample_bundle", help="Release output directory.")
    parser.add_argument("--seed", type=int, default=0, help="Deterministic seed.")
    return parser.parse_args()


def main() -> None:
    from sqlrobustbench.corrupt.recipes import create_corrupted_example
    from sqlrobustbench.export.hf_packaging import create_release_bundle
    from sqlrobustbench.export.rows import build_clean_row, build_corruption_row, build_normalization_row
    from sqlrobustbench.ids import make_row_id
    from sqlrobustbench.normalize.canonicalize import create_normalization_example
    from sqlrobustbench.queries.generator import build_query_program
    from sqlrobustbench.schemas.generator import build_generated_schema, load_schema_definition

    args = parse_args()
    schema = build_generated_schema(load_schema_definition(args.schema_config))
    program = build_query_program(schema, template_id="baseline_summary", complexity="medium", seed=args.seed)
    corruption = create_corrupted_example(program, schema, "missing_group_by")
    normalization = create_normalization_example(program)
    rows = [
        build_clean_row(row_id=make_row_id("sqlclean", schema.schema_family, 1), program=program, schema=schema, split="train"),
        build_corruption_row(
            row_id=make_row_id("sqlcorrupt", schema.schema_family, 1),
            program=program,
            schema=schema,
            record=corruption.record,
            split="train",
        ),
        build_normalization_row(
            row_id=make_row_id("sqlnormalize", schema.schema_family, 1),
            program=program,
            schema=schema,
            result=normalization,
            split="train",
        ),
    ]
    bundle = create_release_bundle(rows, Path(args.output_dir))
    print(bundle["data_path"])
    print(bundle["manifest_path"])


if __name__ == "__main__":
    main()
