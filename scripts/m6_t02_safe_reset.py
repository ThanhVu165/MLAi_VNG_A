"""Reset only a disposable M6-T02 Compose validation project."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys

DISPOSABLE_PROJECT = re.compile(r"^exodia-m6t02-validation(?:-[a-z0-9][a-z0-9_-]*)?$")
PROJECT_LABEL = "com.docker.compose.project"


def docker(*args: str) -> str:
    return subprocess.run(
        ["docker", *args], check=True, capture_output=True, text=True
    ).stdout.strip()


def validated_volumes(project: str) -> list[str]:
    if not DISPOSABLE_PROJECT.fullmatch(project):
        raise ValueError(
            "ABORT: project must be exodia-m6t02-validation or start with "
            "exodia-m6t02-validation-."
        )
    names = docker(
        "volume", "ls", "--filter", f"label={PROJECT_LABEL}={project}", "--format", "{{.Name}}"
    ).splitlines()
    if not names:
        raise ValueError(f"ABORT: no Compose volumes found for project {project!r}.")
    inspected = json.loads(docker("volume", "inspect", *names))
    if len(inspected) != len(names) or any(
        volume.get("Labels", {}).get(PROJECT_LABEL) != project for volume in inspected
    ):
        raise ValueError("ABORT: a discovered volume does not belong to the exact project.")
    return names


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", help="Disposable Compose validation project name")
    args = parser.parse_args()
    try:
        volumes = validated_volumes(args.project)
    except (ValueError, subprocess.CalledProcessError, json.JSONDecodeError) as error:
        sys.stderr.write(f"{error}\n")
        return 2
    sys.stdout.write(
        f"Validated disposable project {args.project!r}; volumes: {', '.join(volumes)}\n"
    )
    subprocess.run(
        ["docker", "compose", "--project-name", args.project, "down", "--volumes"], check=True
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
