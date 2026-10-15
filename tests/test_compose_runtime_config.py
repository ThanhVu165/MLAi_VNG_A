"""Regression cho ranh giới mode của các runtime Compose."""

from pathlib import Path

import yaml  # type: ignore[import-untyped]


ROOT = Path(__file__).resolve().parents[1]


def _environment(service: str) -> dict[str, str]:
    config = yaml.safe_load((ROOT / "compose.yaml").read_text(encoding="utf-8"))
    return config["services"][service]["environment"]


def test_study_resolves_private_replay_environment() -> None:
    assert _environment("study") == {
        "APP_MODE": "private",
        "DATABASE_PATH": "/runtime/app.db",
        "LLM_MODE": "replay",
        "LLM_CACHE": "0",
    }


def test_demo_resolves_restricted_replay_environment() -> None:
    assert _environment("demo") == {
        "APP_MODE": "restricted_demo",
        "DATABASE_PATH": "/runtime/app.db",
        "LLM_MODE": "replay",
        "LLM_CACHE": "0",
    }
