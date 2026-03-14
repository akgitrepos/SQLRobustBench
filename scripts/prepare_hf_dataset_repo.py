# pyright: reportMissingImports=false

from __future__ import annotations

import argparse
from pathlib import Path
import shutil


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare a Hugging Face dataset repo folder from a local release build.")
    parser.add_argument(
        "--release-dir",
        default="data/release/sqlrobustbench_v1",
        help="Local release bundle directory.",
    )
    parser.add_argument(
        "--output-dir",
        default="data/release/sqlrobustbench_hf_dataset",
        help="Output directory for the Hugging Face dataset repo staging folder.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    release_dir = Path(args.release_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "data").mkdir(parents=True, exist_ok=True)

    shutil.copy2(release_dir / "manifest.json", output_dir / "manifest.json")
    shutil.copy2(release_dir / "data" / "records.jsonl", output_dir / "data" / "records.jsonl")
    shutil.copy2(Path("docs/hf_dataset_README.md"), output_dir / "README.md")

    print(output_dir)


if __name__ == "__main__":
    main()
