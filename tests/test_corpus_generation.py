from __future__ import annotations

import json
from pathlib import Path

from sqlrobustbench.export.corpus import build_corpus_from_config, load_corpus_config


ROOT = Path(__file__).resolve().parents[1]


def test_corpus_builder_generates_requested_rows(tmp_path: Path):
    config = load_corpus_config(ROOT / "configs/release_2500.yaml")
    config["generation"]["target_total_rows"] = 60
    config["generation"]["task_targets"] = {"clean": 12, "corrupt": 28, "normalize": 20}
    config["generation"]["max_attempts"] = 3000
    config["splits"]["validation_template_families"] = 1

    result = build_corpus_from_config(config, tmp_path)

    manifest = json.loads(Path(result.release_paths["manifest_path"]).read_text(encoding="utf-8"))
    assert len(result.rows) == 60
    assert manifest["num_rows"] == 60
    assert manifest["stats"]["final_rows"] == 60
    assert result.stats["task_counts"]
