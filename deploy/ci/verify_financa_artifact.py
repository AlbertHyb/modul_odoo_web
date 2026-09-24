#!/usr/bin/env python3
"""Verify a rendered Financa artifact before it can reach Odoo."""

import argparse
import hashlib
import json
import sys
from pathlib import Path


def fail(message):
    raise ValueError(message)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify(root, commit, environment, domain):
    root = root.resolve()
    manifest_path = root / "artifact-manifest.json"
    if not manifest_path.is_file() or manifest_path.is_symlink():
        fail("artifact manifest is missing or is a symbolic link")

    manifest = json.loads(manifest_path.read_text())
    expected = {"commit": commit, "environment": environment, "domain": domain}
    for key, value in expected.items():
        if manifest.get(key) != value:
            fail(f"manifest {key} does not match: expected {value!r}")

    declared = manifest.get("files")
    if not isinstance(declared, dict) or not declared:
        fail("manifest files must be a non-empty object")

    actual = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            fail(f"symbolic link in artifact: {path.relative_to(root)}")
        if path.is_file() and path != manifest_path:
            actual[str(path.relative_to(root))] = path

    if set(actual) != set(declared):
        missing = sorted(set(declared) - set(actual))
        extra = sorted(set(actual) - set(declared))
        fail(f"artifact file set differs; missing={missing}, extra={extra}")

    for relative_path, path in actual.items():
        if sha256(path) != declared[relative_path]:
            fail(f"hash mismatch: {relative_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--environment", required=True)
    parser.add_argument("--domain", required=True)
    args = parser.parse_args()
    verify(args.artifact, args.commit, args.environment, args.domain)
    print(f"Verified {args.environment} artifact at commit {args.commit}")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"ARTIFACT VERIFY FAILED: {error}", file=sys.stderr)
        raise SystemExit(1)
