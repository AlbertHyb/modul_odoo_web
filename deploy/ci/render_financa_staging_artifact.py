#!/usr/bin/env python3
"""Render the Financa staging artifact without changing the checkout."""

import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path


STAGING_DOMAIN = "https://staging.financa.mx"
TOKEN = "__FINANCA_DOMAIN__"
LEGACY_DOMAIN = "https://financa-mx"
TEMPLATE_PATHS = (
    "financa_website/data/redirects.xml",
    "financa_website/views/homepage.xml",
    "financa_website/views/legal.xml",
    "financa_website/views/thank_you.xml",
    "deploy/odoo/preflight_financa.py",
)
COPIED_PATHS = ("financa_website", "deploy/odoo")


def fail(message):
    raise ValueError(message)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--domain", default=STAGING_DOMAIN)
    return parser.parse_args()


def main():
    args = parse_args()
    source = args.source.resolve()
    output = args.output.resolve()
    if args.domain != STAGING_DOMAIN or not re.fullmatch(r"https://[A-Za-z0-9.-]+", args.domain):
        fail(f"only {STAGING_DOMAIN} is valid for staging")
    if not re.fullmatch(r"[A-Za-z0-9._-]+", args.commit):
        fail("commit contains unsupported characters")
    if output.exists():
        fail(f"output already exists: {output}")
    if not source.is_dir():
        fail(f"source is not a directory: {source}")

    for relative_path in COPIED_PATHS:
        origin = source / relative_path
        if not origin.is_dir():
            fail(f"missing artifact source: {relative_path}")
        if origin.is_symlink() or any(path.is_symlink() for path in origin.rglob("*")):
            fail(f"symbolic link in artifact source: {relative_path}")
        shutil.copytree(origin, output / relative_path, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

    for relative_path in TEMPLATE_PATHS:
        path = output / relative_path
        text = path.read_text()
        if TOKEN not in text:
            fail(f"template token missing from {relative_path}")
        path.write_text(text.replace(TOKEN, args.domain))

    files = {}
    for path in sorted(output.rglob("*")):
        if not path.is_file():
            continue
        text = path.read_text() if path.suffix in {".py", ".xml"} else ""
        if TOKEN in text or LEGACY_DOMAIN in text:
            fail(f"unrendered or legacy domain in {path.relative_to(output)}")
        files[str(path.relative_to(output))] = sha256(path)

    manifest = {
        "commit": args.commit,
        "domain": args.domain,
        "files": files,
    }
    (output / "artifact-manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    try:
        main()
    except ValueError as error:
        print(f"ARTIFACT FAILED: {error}", file=sys.stderr)
        raise SystemExit(1)
