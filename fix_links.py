#!/usr/bin/env python3
"""Rewrite root-relative href="/foo" links to relative when target exists in site/.

This makes the site portable across any base path (e.g. github.io/ceci-portfolio/).
"""
import re
from pathlib import Path

ROOT = Path(__file__).parent
SITE = ROOT / "site"

def main():
    # Build set of existing top-level slug pages
    existing_slugs = set()
    for d in SITE.iterdir():
        if d.is_dir() and (d / "index.html").exists():
            existing_slugs.add(d.name)

    files = list(SITE.rglob("*.html"))
    print(f"Scanning {len(files)} files for root-relative links…")

    pattern = re.compile(r'href="(/[A-Za-z0-9_\-]+)/?"')

    for f in sorted(files):
        rel_to_site = f.relative_to(SITE)
        depth = len(rel_to_site.parts) - 1  # depth from site root
        prefix = "../" * depth if depth > 0 else "./"

        html = f.read_text(errors="replace")
        changes = 0

        def replace(m):
            nonlocal changes
            target = m.group(1).lstrip("/")
            if target in existing_slugs:
                changes += 1
                return f'href="{prefix}{target}/"'
            # Unknown link — strip dead /vbid-* placeholders pointing nowhere
            if target.startswith("vbid-"):
                changes += 1
                return f'href="{prefix}"'
            return m.group(0)

        new_html = pattern.sub(replace, html)
        if changes:
            f.write_text(new_html)
            print(f"  ✓ {rel_to_site}: {changes} link(s) rewritten")

if __name__ == "__main__":
    main()
