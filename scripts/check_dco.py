"""Verify Developer Certificate of Origin (DCO) sign-off on commits.

cuere requires every commit to carry a ``Signed-off-by:`` trailer (see
CONTRIBUTING.md and https://developercertificate.org/). This helper enforces it
in two places:

* ``message`` mode — the pre-commit ``commit-msg`` hook checks the in-progress
  commit message file for a well-formed sign-off trailer.
* ``range`` mode — the DCO CI workflow checks that every non-merge commit in a
  ``base..head`` range carries a sign-off matching its author's email.

Stdlib-only and fast on purpose: the CI job runs it with plain ``python3`` (no
project install), and the commit-msg hook must not slow committing down.

Usage:
    python scripts/check_dco.py message <commit-msg-file>
    python scripts/check_dco.py range <base-sha> <head-sha>
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

# A sign-off trailer with any name and an email in angle brackets.
TRAILER_RE = re.compile(r"^Signed-off-by:\s*.+\s+<([^<>@\s]+@[^<>@\s]+)>\s*$", re.MULTILINE)

DCO_URL = "https://developercertificate.org/"
HINT = (
    "Every commit must be signed off (DCO). Use `git commit -s` (or "
    f"`git commit --amend -s` to fix the last one). See {DCO_URL} and CONTRIBUTING.md."
)


def _err(message: str) -> None:
    """Write a line to stderr (print is disallowed by the linter)."""
    sys.stderr.write(f"{message}\n")


def _strip_comments(message: str) -> str:
    """Drop git comment lines so a commented-out trailer does not count."""
    return "\n".join(line for line in message.splitlines() if not line.lstrip().startswith("#"))


def _signoff_emails(message: str) -> set[str]:
    """Return the lower-cased emails from every sign-off trailer in a message."""
    return {email.lower() for email in TRAILER_RE.findall(_strip_comments(message))}


def check_message(path: str) -> int:
    """Check a single commit-message file has a well-formed sign-off trailer."""
    try:
        message = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        _err(f"check_dco: cannot read commit message {path!r}: {exc}")
        return 1
    if _signoff_emails(message):
        return 0
    _err("check_dco: missing Signed-off-by trailer.")
    _err(HINT)
    return 1


def _run_git(*args: str) -> str:
    """Run a git command and return its stdout, raising on failure."""
    return subprocess.run(
        ["git", *args],
        capture_output=True,
        encoding="utf-8",
        check=True,
    ).stdout


def check_range(base: str, head: str) -> int:
    """Check every non-merge commit in base..head has an author-matching sign-off."""
    try:
        listing = _run_git("rev-list", "--no-merges", "--reverse", f"{base}..{head}")
    except subprocess.CalledProcessError as exc:
        _err(f"check_dco: git rev-list failed: {exc.stderr.strip()}")
        return 1
    commits = listing.split()
    failures = 0
    for sha in commits:
        try:
            name, email, body = _run_git("show", "-s", "--format=%an%n%ae%n%B", sha).split("\n", 2)
        except (subprocess.CalledProcessError, ValueError) as exc:
            failures += 1
            _err(f"check_dco: cannot read commit {sha[:12]}: {exc}")
            continue
        if email.lower() not in _signoff_emails(body):
            failures += 1
            _err(f"check_dco: {sha[:12]} by {name} <{email}> has no matching sign-off")
    if failures:
        _err(f"\ncheck_dco: {failures} of {len(commits)} commit(s) not signed off.")
        _err(HINT)
        return 1
    sys.stdout.write(f"check_dco: all {len(commits)} commit(s) signed off.\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check DCO sign-off on commits.")
    sub = parser.add_subparsers(dest="mode", required=True)
    msg = sub.add_parser("message", help="check a commit-message file (commit-msg hook)")
    msg.add_argument("path")
    rng = sub.add_parser("range", help="check non-merge commits in base..head (CI)")
    rng.add_argument("base")
    rng.add_argument("head")
    args = parser.parse_args(argv)
    if args.mode == "message":
        return check_message(args.path)
    return check_range(args.base, args.head)


if __name__ == "__main__":
    sys.exit(main())
