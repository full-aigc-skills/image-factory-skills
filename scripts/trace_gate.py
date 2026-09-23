#!/usr/bin/env python3
"""Run TRACE across authored skills and verify immutable sourced snapshots."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evaluator", required=True, type=Path)
    parser.add_argument("--skills-dir", default="skills", type=Path)
    parser.add_argument("--provenance-dir", default="provenance", type=Path)
    parser.add_argument("--threshold", default=4.5, type=float)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    evaluator = args.evaluator.resolve()
    skills_dir = args.skills_dir.resolve()
    provenance_dir = args.provenance_dir.resolve()
    if not evaluator.is_file():
        print(f"ERROR: TRACE evaluator not found: {evaluator}", file=sys.stderr)
        return 2

    sourced = {
        path.stem
        for path in provenance_dir.glob("*.json")
        if path.is_file()
    } if provenance_dir.is_dir() else set()
    if sourced:
        verifier = Path(__file__).resolve().with_name("verify_sourced_snapshots.py")
        verified = subprocess.run([sys.executable, str(verifier)], check=False)
        if verified.returncode != 0:
            return verified.returncode

    rows: list[tuple[str, float]] = []
    failures: list[tuple[str, float]] = []
    for skill_dir in sorted(path for path in skills_dir.iterdir() if (path / "SKILL.md").is_file()):
        result = subprocess.run(
            [sys.executable, str(evaluator), "--skill-dir", str(skill_dir)],
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(result.stdout)
        score = float(payload["base_scores"]["overall"])
        rows.append((skill_dir.name, score))
        if score < args.threshold and skill_dir.name not in sourced:
            failures.append((skill_dir.name, score))
        elif score < args.threshold:
            print(
                f"SOURCE-VERIFIED: {skill_dir.name} TRACE={score:.2f}; "
                "threshold exemption is bound to the byte-verified provenance record"
            )

    if not rows:
        print("ERROR: no skills found", file=sys.stderr)
        return 2
    average = sum(score for _, score in rows) / len(rows)
    minimum = min(score for _, score in rows)
    maximum = max(score for _, score in rows)
    print(
        f"TRACE: {len(rows)} skills, average={average:.3f}, "
        f"minimum={minimum:.2f}, maximum={maximum:.2f}, threshold={args.threshold:.2f}"
    )
    if failures:
        for name, score in failures:
            print(f"ERROR: {name} scored {score:.2f} below {args.threshold:.2f}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
