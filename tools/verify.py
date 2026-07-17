#!/usr/bin/env python3
"""
verify.py — pre-deploy integrity check for pacificaromania.space.

Run from the repository root:

    python3 tools/verify.py

Checks every HTML page for:
  * broken internal links (href/src to files that do not exist)
  * missing local images
  * malformed nested tags (a recurring bilingual-edit bug)
  * required SEO/security head tags (canonical, og:title, CSP)
  * language parity: every data-l="en" block region also offers data-l="ro"

Exit code is non-zero if any error is found, so it can gate a commit.
"""
import os
import re
import sys

ROOT = "."
errors = []
warnings = []


def html_pages():
    top = [f for f in os.listdir(ROOT) if f.endswith(".html")]
    sub = []
    for d in ("collection", "journal"):
        if os.path.isdir(d):
            sub += [f"{d}/{f}" for f in os.listdir(d) if f.endswith(".html")]
    return sorted(top) + sorted(sub)


def resolve(rel, target):
    # strip query/fragment and protocol-relative / absolute URLs
    t = target.split("#")[0].split("?")[0]
    if not t or t.startswith(("http://", "https://", "mailto:", "tel:", "data:", "//")):
        return None
    base = os.path.dirname(rel)
    return os.path.normpath(os.path.join(base, t))


def check_page(rel):
    src = open(rel, encoding="utf-8").read()

    # internal links + local resources
    for attr in ("href", "src"):
        for m in re.finditer(rf'{attr}="([^"]+)"', src):
            p = resolve(rel, m.group(1))
            if p is None:
                continue
            if p.endswith("/"):
                p += "index.html"
            if not os.path.exists(p):
                errors.append(f"{rel}: broken {attr} -> {m.group(1)}")

    # malformed nested tags
    for m in re.finditer(r"<[a-z0-9]+<span|content=\"<span", src):
        errors.append(f"{rel}: malformed tag near {m.group(0)!r}")

    # required head tags. Pages that opt out of indexing (404, admin hub) only
    # need the CSP meta — canonical/OG are irrelevant for them.
    noindex = 'name="robots" content="noindex' in src or rel == "404.html"
    for needle, label in (
        ('rel="canonical"', "canonical link"),
        ("og:title", "Open Graph tags"),
        ("Content-Security-Policy", "CSP meta"),
    ):
        if noindex and needle != "Content-Security-Policy":
            continue
        if needle not in src:
            warnings.append(f"{rel}: missing {label}")

    # bilingual parity (rough): count EN vs RO spans/divs
    en = len(re.findall(r'data-l="en"', src))
    ro = len(re.findall(r'data-l="ro"', src))
    if en and abs(en - ro) > max(2, en * 0.25):
        warnings.append(f"{rel}: EN/RO parity off (en={en}, ro={ro})")


def main():
    if not os.path.exists("index.html"):
        raise SystemExit("Run this from the repository root (index.html not found).")
    pages = html_pages()
    for rel in pages:
        check_page(rel)

    # referenced files that should exist
    for f in ("sitemap.xml", "robots.txt", "llms.txt", ".well-known/security.txt"):
        if not os.path.exists(f):
            warnings.append(f"missing site file: {f}")

    print(f"Checked {len(pages)} pages.")
    if warnings:
        print(f"\n{len(warnings)} warning(s):")
        for w in warnings:
            print("  ! " + w)
    if errors:
        print(f"\n{len(errors)} ERROR(s):")
        for e in errors:
            print("  x " + e)
        sys.exit(1)
    print("\nNo broken links or malformed tags. OK.")


if __name__ == "__main__":
    main()
