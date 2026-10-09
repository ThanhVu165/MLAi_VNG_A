"""Exercise the real pre-collection hook in fresh offline pytest processes."""

import hashlib
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _environment() -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        PYTHONPATH=str(ROOT),
        PYTHONDONTWRITEBYTECODE="1",
        PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
    )
    env.pop("PYTEST_ADDOPTS", None)
    return env


@pytest.mark.parametrize("configuration", ["dotenv", "relative-env", "absolute-env"])
def test_database_isolated_before_import_and_audit(
    monkeypatch, tmp_path, configuration
):
    # This is a synthetic user DB in a sandbox, never the real data/app.db.
    user_db = tmp_path / "data" / "app.db"
    user_db.parent.mkdir()
    with sqlite3.connect(user_db) as connection:
        connection.execute("CREATE TABLE sentinel (value TEXT)")
        connection.execute("INSERT INTO sentinel VALUES ('preserve')")
    before = hashlib.sha256(user_db.read_bytes()).hexdigest()
    (tmp_path / ".env").write_text(
        f"DATABASE_PATH={user_db.as_posix()}\nLLM_MODE=live\n", encoding="utf-8"
    )
    shutil.copyfile(ROOT / "tests/conftest.py", tmp_path / "conftest.py")
    (tmp_path / "test_child.py").write_text(
        """
import os
from pathlib import Path
import socket
import openai
import pytest
from infra import db
from core import extract, pipeline
from infra.llm import LLMResult

# These assertions run at collection, before test fixtures exist.
DEFAULT = db.DEFAULT_DATABASE_PATH
assert DEFAULT.is_absolute()
assert DEFAULT == Path(os.environ["DATABASE_PATH"])
assert DEFAULT != Path("data/app.db").resolve()
assert DEFAULT.parent.name.startswith("mlai-pytest-db-")
assert os.environ["LLM_MODE"] == "replay"

def test_audit_and_network_barriers(monkeypatch, tmp_path):
    before = db.fetch_one("SELECT COUNT(*) AS n FROM audit_events")["n"]
    payload = {
        "language": "vi", "requests": [], "critical_facts": [],
        "missing_critical_facts": [], "injection_suspected": False,
    }
    monkeypatch.setattr(extract, "call_json", lambda *a, **k:
        LLMResult(True, payload, None, 0, "offline", "test"))
    result = extract.extract_facts("Hỏi thủ tục", "isolated-audit")
    assert result.llm_error is None
    assert db.fetch_one("SELECT COUNT(*) AS n FROM audit_events")["n"] == before + 1
    with pytest.raises(pytest.fail.Exception, match="OFFLINE_ONLY"):
        openai.OpenAI(api_key="synthetic-only")
    with socket.socket() as sock:
        with pytest.raises(pytest.fail.Exception, match="OFFLINE_ONLY"):
            sock.connect(("192.0.2.1", 443))
    with monkeypatch.context() as local:
        local.setattr(db, "DEFAULT_DATABASE_PATH", tmp_path / "per-test.db")
        assert db.fetch_one("SELECT COUNT(*) AS n FROM audit_events")["n"] == 0
        extract.extract_facts("Hỏi thủ tục", "per-test-audit")
        assert db.fetch_one("SELECT COUNT(*) AS n FROM audit_events")["n"] == 1
    assert db.DEFAULT_DATABASE_PATH == DEFAULT
    assert db.fetch_one("SELECT COUNT(*) AS n FROM audit_events")["n"] == before + 1
""",
        encoding="utf-8",
    )
    env = _environment()
    if configuration == "dotenv":
        env.pop("DATABASE_PATH", None)
    else:
        env["DATABASE_PATH"] = (
            "data/app.db" if configuration == "relative-env" else str(user_db)
        )
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            "--basetemp",
            str(tmp_path / "child-temp"),
        ],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=45,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "1 passed" in result.stdout
    assert hashlib.sha256(user_db.read_bytes()).hexdigest() == before
    with sqlite3.connect(user_db.as_uri() + "?mode=ro", uri=True) as connection:
        assert connection.execute("SELECT value FROM sentinel").fetchall() == [
            ("preserve",)
        ]


@pytest.mark.parametrize("failure", ["preimported-db", "temp-unavailable"])
def test_database_bootstrap_fails_closed(tmp_path, failure):
    shutil.copyfile(ROOT / "tests/conftest.py", tmp_path / "conftest.py")
    (tmp_path / "test_child.py").write_text(
        "raise AssertionError('collection must not run')"
    )
    setup = (
        "import types; sys.modules['infra.db'] = types.ModuleType('infra.db');"
        if failure == "preimported-db"
        else "import tempfile; tempfile.TemporaryDirectory = lambda **kw: "
        "(_ for _ in ()).throw(OSError('unavailable'));"
    )
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; "
            + setup
            + " import pytest; sys.exit(pytest.main(['-q', '-p', 'no:cacheprovider']))",
        ],
        cwd=tmp_path,
        env=_environment(),
        capture_output=True,
        text=True,
        timeout=45,
    )
    assert result.returncode != 0
    assert "TEST_DATABASE_ISOLATION" in result.stdout + result.stderr
    assert "collection must not run" not in result.stdout + result.stderr
