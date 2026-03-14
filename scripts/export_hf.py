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
    parser = argparse.ArgumentParser(description="Build a release bundle from the configured benchmark corpus.")
    parser.add_argument(
        "config_path",
        nargs="?",
        default="configs/release_2500.yaml",
        help="Path to a corpus generation YAML config.",
    )
    parser.add_argument("--output-dir", default="data/release/sqlrobustbench_v1", help="Release output directory.")
    return parser.parse_args()


def main() -> None:
    from sqlrobustbench.export.corpus import build_corpus_from_config, load_corpus_config

    args = parse_args()
    config = load_corpus_config(args.config_path)
    result = build_corpus_from_config(config, Path(args.output_dir))
    print(result.release_paths["data_path"])
    print(result.release_paths["manifest_path"])


if __name__ == "__main__":
    main()
