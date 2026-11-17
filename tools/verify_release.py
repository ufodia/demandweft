#!/usr/bin/env python3
"""Read-only SHA-256 verification for files listed in this release manifest."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path, PurePosixPath, PureWindowsPath

MAX_MANIFEST_BYTES = 2 * 1024 * 1024
ENTRY = re.compile(r"([0-9a-f]{64})[ \t]{2,}(.+)")
IGNORED_PARTS = {".git", "__pycache__"}
IGNORED_NAMES = {".DS_Store", "Thumbs.db"}
IGNORED_SUFFIXES = {".pyc", ".pyo"}


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_manifest(manifest_path: Path) -> tuple[int, dict]:
    """Return (exit_code, JSON-ready report); never writes or follows outside root."""
    manifest_path = Path(manifest_path)
    try:
        raw = manifest_path.read_bytes()
        if len(raw) > MAX_MANIFEST_BYTES:
            raise ValueError("Manifest exceeds the 2 MiB input limit")
        manifest_text = raw.decode("utf-8-sig")
    except (OSError, UnicodeError, ValueError) as exc:
        return 2, {
            "status": "invalid_manifest",
            "manifest": manifest_path.name,
            "checked_files": 0,
            "errors": [str(exc) if isinstance(exc, ValueError) else type(exc).__name__],
            "caveat": "Checks only the file bytes listed in this manifest; it does not establish provenance.",
        }

    root = manifest_path.resolve().parent
    seen = set()
    entries = []
    errors = []
    mismatches = []
    declared_count = 0
    unlisted_files = []
    for line_number, raw_line in enumerate(manifest_text.splitlines(), 1):
        if not raw_line.strip():
            continue
        match = ENTRY.fullmatch(raw_line)
        if not match:
            errors.append(f"line {line_number}: expected a lowercase SHA-256 digest, two spaces, and a relative path")
            continue
        expected, relative_text = match.groups()
        relative = PurePosixPath(relative_text)
        windows = PureWindowsPath(relative_text)
        if ("\x00" in relative_text or "\\" in relative_text
                or relative.is_absolute() or windows.is_absolute()
                or windows.drive or ".." in relative.parts or "." in relative.parts
                or relative.as_posix() != relative_text):
            errors.append(f"line {line_number}: path must be a normalized, safe relative path")
            continue
        declared_count += 1
        candidate = root.joinpath(*relative.parts)
        try:
            resolved = candidate.resolve(strict=True)
            if not resolved.is_relative_to(root):
                errors.append(f"line {line_number}: path resolves outside the release directory")
                continue
        except (OSError, RuntimeError, ValueError):
            mismatches.append({"path": relative_text, "line": line_number, "status": "missing_or_unresolvable"})
            continue
        if resolved == manifest_path.resolve():
            errors.append(f"line {line_number}: the manifest cannot hash itself")
            continue
        if not resolved.is_file():
            mismatches.append({"path": relative_text, "line": line_number, "status": "not_a_regular_file"})
            continue
        duplicate_key = relative_text.casefold()
        if duplicate_key in seen:
            errors.append(f"line {line_number}: duplicate path {relative_text}")
            continue
        seen.add(duplicate_key)
        entries.append((expected, relative_text, resolved, line_number))

    if declared_count == 0 and not errors:
        errors.append("manifest contains no file entries")

    for expected, relative_text, path, line_number in entries:
        try:
            actual = file_sha256(path)
        except OSError:
            mismatches.append({"path": relative_text, "line": line_number, "status": "unreadable"})
            continue
        if actual != expected:
            mismatches.append({"path": relative_text, "line": line_number, "status": "hash_mismatch"})

    for candidate in root.rglob("*"):
        if not candidate.is_file():
            continue
        relative_text = candidate.relative_to(root).as_posix()
        parts = set(candidate.relative_to(root).parts)
        if (candidate.name == manifest_path.name or candidate.name in IGNORED_NAMES
                or parts & IGNORED_PARTS or candidate.suffix in IGNORED_SUFFIXES):
            continue
        if relative_text.casefold() not in seen:
            unlisted_files.append(relative_text)

    if errors or unlisted_files:
        code, status = 2, "invalid_manifest"
    elif mismatches:
        code, status = 1, "integrity_failure"
    else:
        code, status = 0, "verified"
    return code, {
        "status": status,
        "manifest": manifest_path.name,
        "checked_files": len(entries),
        "errors": errors,
        "mismatches": mismatches,
        "unlisted_files": sorted(unlisted_files, key=str.casefold),
        "caveat": "A matching digest and complete file list do not establish provenance or safety.",
    }


def main(argv=None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) > 1:
        report = {
            "status": "invalid_manifest",
            "manifest": None,
            "checked_files": 0,
            "errors": ["usage: verify_release.py [CHECKSUMS.sha256]"],
            "caveat": "Checks only the file bytes listed in this manifest; it does not establish provenance.",
        }
        code = 2
    else:
        default_manifest = Path(__file__).resolve().parents[1] / "CHECKSUMS.sha256"
        code, report = verify_manifest(Path(args[0]) if args else default_manifest)
    print(json.dumps(report, ensure_ascii=False, allow_nan=False, sort_keys=True, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
