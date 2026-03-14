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
    parser = argparse.ArgumentParser(description="Generate JSON schema artifacts from YAML configs.")
    parser.add_argument("schema_config", help="Path to a schema YAML config file.")
    parser.add_argument(
        "--output-dir",
        default="data/raw/schemas",
        help="Directory where generated schema JSON files will be written.",
    )
    return parser.parse_args()


def main() -> None:
    from sqlrobustbench.schemas.generator import (
        build_generated_schema,
        load_schema_definition,
        write_generated_schema,
    )

    args = parse_args()
    schema_definition = load_schema_definition(args.schema_config)
    generated_schema = build_generated_schema(schema_definition)
    output_path = Path(args.output_dir) / f"{generated_schema.schema_id}.json"
    write_generated_schema(generated_schema, output_path)
    print(output_path)


if __name__ == "__main__":
    main()
