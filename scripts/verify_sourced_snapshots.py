#!/usr/bin/env python3
"""Verify that sourced skill snapshots match their recorded file digests."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    errors: list[str] = []
    proof_path = ROOT / "provenance" / "imagegen.json"
    proof = json.loads(proof_path.read_text(encoding="utf-8"))
    skill_dir = ROOT / "skills" / "imagegen"
    expected = proof.get("files", {})
    actual = {
        path.relative_to(skill_dir).as_posix()
        for path in skill_dir.rglob("*")
        if path.is_file()
    } if skill_dir.is_dir() else set()

    for relative in sorted(set(expected) - actual):
        errors.append(f"imagegen: missing sourced file {relative}")
    for relative in sorted(actual - set(expected)):
        errors.append(f"imagegen: unrecorded sourced file {relative}")
    for relative in sorted(actual & set(expected)):
        observed = sha256(skill_dir / relative)
        if observed != expected[relative]:
            errors.append(
                f"imagegen: digest mismatch for {relative}; "
                f"expected {expected[relative]}, got {observed}"
            )

    for error in errors:
        print(f"ERROR: {error}")
    print(f"verify_sourced_snapshots: {len(actual)} files, {len(errors)} errors")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
