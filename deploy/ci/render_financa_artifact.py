#!/usr/bin/env python3
"""Render one Financa deployment artifact without changing the checkout.

The addon and the Odoo deployment checks ship the ``__FINANCA_DOMAIN__`` token
instead of a hostname, so one revision can serve every environment. This script
copies both into a fresh directory and replaces the token with the hostname of
exactly one environment:

* ``staging`` renders ``https://staging.financa.mx`` and nothing else;
* ``production`` renders the hostname supplied by the pipeline. No production
  hostname is stored in this repository, and the staging host is refused so a
  copy-pasted pipeline variable cannot publish a production artifact that
  targets staging.

The rendered output is then scanned: the token must be gone, and the only
absolute host left in any Python or XML file must be the target one. That is
what catches a leftover literal from another environment (for example the
historical ``https://financa-mx``) in a file the token never reached.
"""

import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path


STAGING_DOMAIN = "https://staging.financa.mx"
TOKEN = "__FINANCA_DOMAIN__"
ENVIRONMENTS = ("staging", "production")
DOMAIN_PATTERN = re.compile(r"https://[A-Za-z0-9.-]+")
HOST_PATTERN = re.compile(r"https?://[A-Za-z0-9._-]+(?::\d+)?")
TEMPLATE_PATHS = (
    "financa_website/data/redirects.xml",
    "financa_website/views/homepage.xml",
    "financa_website/views/legal.xml",
    "financa_website/views/thank_you.xml",
    "deploy/odoo/preflight_financa.py",
)
COPIED_PATHS = ("financa_website", "deploy/odoo")
SCANNED_SUFFIXES = frozenset({".py", ".xml"})


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
    parser.add_argument("--environment", choices=ENVIRONMENTS, required=True)
    parser.add_argument("--domain", required=True)
    return parser.parse_args()


def check_domain(environment, domain):
    """Accept only the hostname that belongs to the requested environment."""
    if not DOMAIN_PATTERN.fullmatch(domain):
        fail(f"domain must be one https hostname without path, query or port: {domain!r}")
    if environment == "staging" and domain != STAGING_DOMAIN:
        fail(f"only {STAGING_DOMAIN} is valid for staging")
    if environment == "production" and domain == STAGING_DOMAIN:
        fail(f"{STAGING_DOMAIN} is the staging host; pass the production domain explicitly")


def copy_sources(source, output):
    for relative_path in COPIED_PATHS:
        origin = source / relative_path
        if not origin.is_dir():
            fail(f"missing artifact source: {relative_path}")
        if origin.is_symlink() or any(path.is_symlink() for path in origin.rglob("*")):
            fail(f"symbolic link in artifact source: {relative_path}")
        shutil.copytree(origin, output / relative_path, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))


def render_templates(output, domain):
    for relative_path in TEMPLATE_PATHS:
        path = output / relative_path
        text = path.read_text()
        if TOKEN not in text:
            fail(f"template token missing from {relative_path}")
        path.write_text(text.replace(TOKEN, domain))


def scan_rendered(output, domain):
    """Reject a surviving token or any host that is not the target domain."""
    for path in sorted(output.rglob("*")):
        if not path.is_file() or path.suffix not in SCANNED_SUFFIXES:
            continue
        relative_path = path.relative_to(output)
        text = path.read_text()
        if TOKEN in text:
            fail(f"unrendered domain token in {relative_path}")
        for host in HOST_PATTERN.findall(text):
            if host.lower() != domain.lower():
                fail(f"unexpected absolute host {host} in {relative_path}: only {domain} may remain")


def main():
    args = parse_args()
    source = args.source.resolve()
    output = args.output.resolve()
    check_domain(args.environment, args.domain)
    if not re.fullmatch(r"[A-Za-z0-9._-]+", args.commit):
        fail("commit contains unsupported characters")
    if output.exists():
        fail(f"output already exists: {output}")
    if not source.is_dir():
        fail(f"source is not a directory: {source}")

    copy_sources(source, output)
    render_templates(output, args.domain)
    scan_rendered(output, args.domain)

    files = {}
    for path in sorted(output.rglob("*")):
        if path.is_file():
            files[str(path.relative_to(output))] = sha256(path)

    manifest = {
        "commit": args.commit,
        "domain": args.domain,
        "environment": args.environment,
        "files": files,
    }
    (output / "artifact-manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(f"Rendered {args.environment} artifact for {args.domain} at commit {args.commit}")


if __name__ == "__main__":
    try:
        main()
    except ValueError as error:
        print(f"ARTIFACT FAILED: {error}", file=sys.stderr)
        raise SystemExit(1)
