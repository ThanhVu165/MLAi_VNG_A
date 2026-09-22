"""Khởi động xử lý nền trước máy chủ giao diện, không cần chờ mở trình duyệt."""

import sys
from pathlib import Path

from streamlit.web import cli

from core.worker import start_worker
from corpus.seed import ensure_seeded


def main() -> None:
    ensure_seeded()
    start_worker()
    sys.argv = [
        "streamlit",
        "run",
        str(Path(__file__).with_name("streamlit_app.py")),
        *sys.argv[1:],
    ]
    cli.main()


if __name__ == "__main__":
    main()
