"""Kiểm tra barrier thật của suite, không thay thế bằng mock PASS."""

import os
import socket
from datetime import datetime, timezone

import openai
import pytest

from infra import llm
from infra.settings import load_local_env
from infra import db
from core.pipeline import process_case
from core.types import CaseInput


def test_live_dotenv_cannot_enable_real_provider(monkeypatch, tmp_path) -> None:
    config = tmp_path / "synthetic.env"
    config.write_text("LLM_MODE=live\n", encoding="utf-8")
    load_local_env(config)
    assert os.environ["LLM_MODE"] == "replay"
    # Ngay cả khi caller cố tình override LIVE, provider vẫn bị chặn.
    monkeypatch.delenv("LLM_MODE")
    load_local_env(config)
    assert os.environ["LLM_MODE"] == "live"
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-only")
    with pytest.raises(pytest.fail.Exception, match="OFFLINE_ONLY"):
        llm._call_live("synthetic", {}, "hash", "gpt-6-luna", 30, 0)
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-6-luna")
    monkeypatch.setenv("LLM_CACHE", "0")
    monkeypatch.setattr(db, "DEFAULT_DATABASE_PATH", tmp_path / "offline.db")
    with pytest.raises(pytest.fail.Exception, match="OFFLINE_ONLY"):
        process_case(
            CaseInput(
                sender="student@example.test",
                subject="Hỏi quy trình",
                body="Cho em hỏi quy trình rút học phần?",
                received_at=datetime.now(timezone.utc),
                channel="paste",
            )
        )


@pytest.mark.parametrize("client", ["OpenAI", "AsyncOpenAI"])
def test_sdk_constructors_blocked(client) -> None:
    with pytest.raises(pytest.fail.Exception, match="OFFLINE_ONLY"):
        getattr(openai, client)(api_key="synthetic-only")


@pytest.mark.parametrize("method", ["connect", "connect_ex", "sendto"])
def test_network_barrier_blocks_even_without_sdk(method) -> None:
    with socket.socket() as sock:
        with pytest.raises(pytest.fail.Exception, match="OFFLINE_ONLY"):
            if method == "sendto":
                sock.sendto(b"synthetic", ("192.0.2.1", 443))
            else:
                getattr(sock, method)(("192.0.2.1", 443))


def test_hostname_resolution_blocked_but_numeric_address_needs_no_network() -> None:
    with pytest.raises(pytest.fail.Exception, match="OFFLINE_ONLY"):
        socket.getaddrinfo("api.openai.com", 443)
    assert socket.getaddrinfo("127.0.0.1", 443, type=socket.SOCK_STREAM)
