"""Client operator Unix IPC; secret nhập ẩn, không truyền qua argv/environment/frontend."""

import argparse
import getpass
import json
import os
from pathlib import Path
import socket
import stat
import sys


def main() -> None:
    parser = argparse.ArgumentParser(description="Vận hành judge local, không HTTP/provider.")
    parser.add_argument("--socket", required=True, type=Path)
    parser.add_argument(
        "operation", choices=("sessions", "provision", "revoke", "holds", "recover")
    )
    parser.add_argument("--reference")
    parser.add_argument("--request-id")
    args = parser.parse_args()
    parent = args.socket.parent
    try:
        directory = parent.lstat()
        endpoint = args.socket.lstat()
        if (
            not args.socket.is_absolute()
            or parent.resolve() != parent
            or not stat.S_ISDIR(directory.st_mode)
            or directory.st_uid != os.getuid()
            or stat.S_IMODE(directory.st_mode) != 0o700
            or not stat.S_ISSOCK(endpoint.st_mode)
            or endpoint.st_uid != os.getuid()
            or stat.S_IMODE(endpoint.st_mode) != 0o600
        ):
            raise OSError("Unsafe local endpoint")
    except OSError:
        parser.error("Socket phải thuộc user hiện tại, mode 0600 trong thư mục riêng 0700.")
    if not sys.stdin.isatty():
        parser.error("Secret chỉ được nhập ẩn qua terminal local; không đọc từ pipe.")
    message = {
        "operation": args.operation,
        "reference": args.reference,
        "request_id": args.request_id,
        "secret": getpass.getpass("Secret operator (không hiển thị): "),
    }
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.settimeout(5)
            client.connect(str(args.socket))
            client.sendall(json.dumps(message).encode("utf-8") + b"\n")
            response = bytearray()
            while not response.endswith(b"\n") and len(response) <= 65536:
                chunk = client.recv(4096)
                if not chunk:
                    raise OSError("IPC response missing")
                response.extend(chunk)
            data = json.loads(response)
            sys.stdout.write(json.dumps(data, ensure_ascii=False) + "\n")
            if data.get("ok") is False:
                raise SystemExit(2)
    except (OSError, ValueError):
        sys.stderr.write("Không kết nối được gateway local; không tự retry/cấp lại quyền.\n")
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
