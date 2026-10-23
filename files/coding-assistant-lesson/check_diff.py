#!/usr/bin/env python3
"""Validate the tutorial's one-line README edit in a disposable Git fixture.

This checks a human-reviewed working-tree diff only. It does not run or verify
Cursor, Aider, a language model, or scientific analysis.
"""
from pathlib import Path
import subprocess
import sys

BASE_README = (
    "# Sample-count helper\n\n"
    "This documentation-only project describes a tiny arithmetic example.\n\n"
    "Input: 12 reads in sample A and 8 reads in sample B.\n"
    "Expected total: 20 reads.\n"
)
EXPECTED_SENTENCE = "The two sample counts sum to 20 reads."
EXPECTED_README = BASE_README.replace(
    "Expected total: 20 reads.\n",
    EXPECTED_SENTENCE + "\nExpected total: 20 reads.\n",
)


def validate_worktree(project: Path) -> list[str]:
    """Return reasons the worktree does not match the exact tutorial change."""
    errors = []
    try:
        status = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=all"],
            cwd=project,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines()
    except (OSError, subprocess.CalledProcessError) as exc:
        return [f"Could not read Git status: {exc}"]

    if status != [" M README.md"]:
        errors.append("Expected only one unstaged change: README.md; no staged or untracked changes.")

    try:
        readme = (project / "README.md").read_text(encoding="utf-8")
    except OSError as exc:
        return errors + [f"Could not read README.md: {exc}"]
    if readme != EXPECTED_README:
        errors.append("README.md is not exactly the expected one-sentence edit; check all original text and values.")

    try:
        diff = subprocess.run(
            ["git", "diff", "--no-ext-diff", "--unified=0", "--", "README.md"],
            cwd=project,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError) as exc:
        return errors + [f"Could not inspect the README diff: {exc}"]

    additions = [line[1:] for line in diff.splitlines() if line.startswith("+") and not line.startswith("+++")]
    removals = [line[1:] for line in diff.splitlines() if line.startswith("-") and not line.startswith("---")]
    if additions != [EXPECTED_SENTENCE] or removals:
        errors.append("Expected exactly one added sentence and no removed lines in the README diff.")
    return errors


def main() -> int:
    project = Path.cwd()
    errors = validate_worktree(project)
    if errors:
        for error in errors:
            print(f"REJECT: {error}", file=sys.stderr)
        return 1
    print("PASS: only the expected sentence was added to README.md; original values 12, 8, and 20 are unchanged.")
    print("This is a local Git fixture check, not evidence that Cursor, Aider, or a model ran.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
