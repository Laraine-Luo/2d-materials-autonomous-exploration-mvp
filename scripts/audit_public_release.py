#!/usr/bin/env python3
"""Fail-closed audit for files intended for a public GitHub repository."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path


FORBIDDEN_PATH_PARTS = {
    ".git",
    ".local-data",
    ".local-secrets",
    ".venv",
    "outputs",
    "__pycache__",
}
FORBIDDEN_FILENAMES = {".env", ".DS_Store"}
TEXT_SUFFIXES = {
    ".csv", ".json", ".md", ".py", ".txt", ".yaml", ".yml", ".toml", ".ini"
}
SENSITIVE_PATTERNS = {
    "literal_mp_api_key_assignment": re.compile(
        r"(?i)(?:MP_API_KEY|api[_ -]?key)\s*[:=]\s*['\"]?[A-Za-z0-9_-]{20,}"
    ),
    "private_key_block": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
}


def iter_public_files(root: Path):
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if any(part in FORBIDDEN_PATH_PARTS for part in relative.parts):
            continue
        yield path, relative


def audit(root: Path) -> dict:
    violations: list[dict[str, str]] = []
    checked_files = 0
    for path, relative in iter_public_files(root):
        checked_files += 1
        if path.name in FORBIDDEN_FILENAMES or path.name.endswith(".env"):
            violations.append({"path": str(relative), "reason": "forbidden_filename"})
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES and path.name not in {"LICENSE", ".gitignore"}:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for name, pattern in SENSITIVE_PATTERNS.items():
            if pattern.search(content):
                violations.append({"path": str(relative), "reason": name})

    forbidden_present = [
        name for name in sorted(FORBIDDEN_PATH_PARTS)
        if (root / name).exists() and name not in {".git", ".local-data", ".local-secrets", ".venv", "outputs"}
    ]
    report = {
        "schema_version": "1.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "root": str(root.resolve()),
        "checked_public_files": checked_files,
        "excluded_local_paths": sorted(FORBIDDEN_PATH_PARTS),
        "forbidden_paths_unexpectedly_present": forbidden_present,
        "violations": violations,
        "result": "pass" if not violations and not forbidden_present else "fail",
        "interpretation": (
            "This audit checks repository-visible text and path hygiene. It does not prove that a "
            "credential disclosed elsewhere has never been exposed; rotate disclosed credentials before publication."
        ),
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = audit(args.root.resolve())
    output = args.output or args.root / "artifacts" / "public_release_audit.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["result"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())

