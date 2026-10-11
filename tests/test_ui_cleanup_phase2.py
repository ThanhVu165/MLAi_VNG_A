from __future__ import annotations

import dataclasses
import hashlib
import json
from enum import Enum
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from ui.deterministic_fixtures import get_deterministic_fixtures


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_FIXTURE_HASHES = {
    "with_fail": "b8f61f11d9706d04c6ac220d28266ea96ba8af6907ca130062842fcd307ba486",
    "all_pass": "8fceb1d06f8c5ac1be18f1248026c9b398060eb50265d590132c09b0a5f55e69",
}


def _normalize(value: object) -> object:
    if dataclasses.is_dataclass(value):
        return {
            field.name: _normalize(getattr(value, field.name))
            for field in dataclasses.fields(value)
        }
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, tuple):
        return [_normalize(item) for item in value]
    return value


@pytest.mark.parametrize(
    ("fixture_type", "expected_count", "expected_elapsed", "expected_case_set"),
    [
        ("with_fail", 12, 18.2, "m2_combined_dev"),
        ("all_pass", 4, 5.7, "verify4"),
    ],
)
def test_shared_fixture_keeps_reviewed_content_and_metadata(
    fixture_type: str,
    expected_count: int,
    expected_elapsed: float,
    expected_case_set: str,
) -> None:
    results, elapsed, case_set = get_deterministic_fixtures(fixture_type)
    payload = _normalize((results, elapsed, case_set))
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode(
        "utf-8"
    )

    assert len(results) == expected_count
    assert elapsed == expected_elapsed
    assert case_set == expected_case_set
    assert hashlib.sha256(encoded).hexdigest() == EXPECTED_FIXTURE_HASHES[fixture_type]


@pytest.mark.parametrize("fixture_type", ["with_fail", "all_pass"])
def test_verify_query_keeps_synthetic_label_and_export(fixture_type: str) -> None:
    app = AppTest.from_file(str(ROOT / "pages/5_Verify.py"))
    app.query_params["fixture"] = fixture_type
    app.run(timeout=20)

    assert not app.exception
    assert any("DỮ LIỆU MÔ PHỎNG" in item.value for item in app.warning)
    assert len(app.get("download_button")) == 1


@pytest.mark.parametrize("fixture_type", ["with_fail", "all_pass"])
def test_measurement_query_keeps_synthetic_label(fixture_type: str) -> None:
    app = AppTest.from_file(str(ROOT / "pages/6_Do_luong.py"))
    app.query_params["fixture"] = fixture_type
    app.run(timeout=20)

    assert not app.exception
    assert any("DỮ LIỆU MÔ PHỎNG" in item.value for item in app.warning)
