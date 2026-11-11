import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from darija_eval_set.cli import app
from darija_eval_set.dataset import load_items

runner = CliRunner()
REPO_DATA = Path(__file__).parent.parent / "data" / "items.jsonl"

GOOD = {
    "id": "qa-001",
    "category": "qa",
    "prompt": "شنو هي عاصمة المغرب؟",
    "expected": ["الرباط"],
    "scoring": "normalized",
    "languages": ["ary"],
    "notes": None,
    "review_status": "draft",
}


def write(path: Path, *lines: str) -> Path:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def test_real_data_is_valid() -> None:
    items, errors = load_items(REPO_DATA)
    assert errors == []
    assert len(items) == 150
    assert {i.review_status.value for i in items} == {"draft"}


def test_real_data_has_twenty_five_items_per_category() -> None:
    items, _ = load_items(REPO_DATA)
    counts: dict[str, int] = {}
    for item in items:
        counts[item.category.value] = counts.get(item.category.value, 0) + 1
    assert counts == dict.fromkeys(
        [
            "translation",
            "qa",
            "sentiment",
            "code_switching",
            "instruction_following",
            "safety_refusal",
        ],
        25,
    )


def test_cli_accepts_valid_file(tmp_path: Path) -> None:
    f = write(tmp_path / "ok.jsonl", json.dumps(GOOD, ensure_ascii=False))
    result = runner.invoke(app, ["validate", str(f)])
    assert result.exit_code == 0
    assert "1 items OK" in result.output


def test_cli_reports_file_line_and_reason(tmp_path: Path) -> None:
    bad = GOOD | {"id": "qa-002", "expected": []}
    f = write(tmp_path / "bad.jsonl", json.dumps(GOOD), json.dumps(bad))
    result = runner.invoke(app, ["validate", str(f)])
    assert result.exit_code == 1
    assert f"{f}:2:" in result.output
    assert "expected" in result.output


def test_invalid_json_line(tmp_path: Path) -> None:
    f = write(tmp_path / "bad.jsonl", "{not json")
    _, errors = load_items(f)
    assert len(errors) == 1
    assert errors[0].line == 1
    assert "invalid JSON" in errors[0].reason


def test_duplicate_id_and_blank_lines(tmp_path: Path) -> None:
    line = json.dumps(GOOD)
    f = write(tmp_path / "dup.jsonl", line, "", line)
    items, errors = load_items(f)
    assert len(items) == 1
    assert errors[0].line == 3
    assert "duplicate id" in errors[0].reason


def test_cli_missing_file(tmp_path: Path) -> None:
    result = runner.invoke(app, ["validate", str(tmp_path / "nope.jsonl")])
    assert result.exit_code == 2


@pytest.mark.parametrize("field", ["prompt", "scoring", "review_status"])
def test_missing_required_field(tmp_path: Path, field: str) -> None:
    broken = {k: v for k, v in GOOD.items() if k != field}
    f = write(tmp_path / "m.jsonl", json.dumps(broken))
    _, errors = load_items(f)
    assert len(errors) == 1
    assert field in errors[0].reason
