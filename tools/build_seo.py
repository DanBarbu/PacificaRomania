#!/usr/bin/env python3
"""
build_seo.py — regenerate sitemap.xml and inject SEO + security head tags.

Run from the repository root:

    python3 tools/build_seo.py

It is idempotent and safe to re-run after adding new pages:
  * Adds <link rel="canonical">, Open Graph and Twitter card tags to any
    HTML page that does not already have them (keyed on 'og:title').
  * Adds a Content-Security-Policy + referrer meta to any page missing it.
  * Rebuilds sitemap.xml from the current set of pages.

Add a new essay's share image by extending ESSAY_IMG below.
"""
import os
import re
import html
import datetime

BASE = "https://pacificaromania.space/"
DEFAULT_IMG = "assets/images/folio/aboriginal-birds-in-space.jpg"

# Per-essay Open Graph image (slug -> file under assets/images/folio/).
ESSAY_IMG = {
    "aboriginal-birds-in-space": "aboriginal-birds-in-space.jpg",
    "nguzu-nguzu-and-the-tomoko": "nguzunguzu-shelf.jpg",
    "moyang-siamang": "moyang-siamang.jpg",
    "the-sacred-papot": "papot.jpg",
    "the-sacralization-of-measure": "chinthe-weights.jpg",
    "aloi-pilioko": "pilioko-nautical-rhythms.jpg",
    "eliade-and-the-masks-of-malaysia": "mah-meri-masks.jpg",
    "naga-morsarang": "naga-morsarang.jpg",
    "asaro-mudmen": "asaro-spirit-head.jpg",
    "raja-bomoh": "raja-bomoh.jpg",
}

CSP = (
    "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; "
    "script-src 'self' 'unsafe-inline'; font-src 'self'; object-src 'none'; "
    "base-uri 'self'; form-action 'self'; frame-src 'none'; upgrade-insecure-requests"
)

# Pages excluded from the sitemap (still get head tags where useful).
NO_INDEX = {"404.html"}


def html_pages():
    top = [f for f in os.listdir(".") if f.endswith(".html")]
    sub = []
    for d in ("collection", "journal"):
        if os.path.isdir(d):
            sub += [f"{d}/{f}" for f in os.listdir(d) if f.endswith(".html")]
    return sorted(top) + sorted(sub)


def canonical_for(rel):
    return BASE if rel == "index.html" else BASE + rel


def og_image_for(rel):
    slug = os.path.splitext(os.path.basename(rel))[0]
    if rel.startswith("journal/") and slug in ESSAY_IMG:
        return BASE + "assets/images/folio/" + ESSAY_IMG[slug]
    return BASE + DEFAULT_IMG


def inject_security(src):
    if "Content-Security-Policy" in src:
        return src, False
    m = re.search(r'<meta charset="utf-8">', src)
    if not m:
        return src, False
    block = (
        f'<meta http-equiv="Content-Security-Policy" content="{CSP}">\n'
        '<meta name="referrer" content="strict-origin-when-cross-origin">'
    )
    return src.replace(m.group(0), m.group(0) + "\n" + block, 1), True


def inject_seo(rel, src):
    if "og:title" in src:
        return src, False
    mt = re.search(r"<title>(.*?)</title>", src, re.S)
    md = re.search(r'<meta name="description" content="(.*?)">', src, re.S)
    if not mt or not md:
        return src, False
    title = html.escape(mt.group(1).strip(), quote=True)
    desc = html.escape(md.group(1).strip(), quote=True)
    canon = canonical_for(rel)
    img = og_image_for(rel)
    typ = "article" if rel.startswith("journal/") else "website"
    block = f'''<link rel="canonical" href="{canon}">
<meta property="og:type" content="{typ}">
<meta property="og:site_name" content="PacificaRomania">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{canon}">
<meta property="og:image" content="{img}">
<meta property="og:locale" content="en">
<meta property="og:locale:alternate" content="ro">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:image" content="{img}">'''
    return src.replace(md.group(0), md.group(0) + "\n" + block, 1), True


def write_sitemap(pages):
    today = datetime.date.today().isoformat()
    priority = {"index.html": "1.0", "collection.html": "0.9", "journal.html": "0.9"}
    freq = {"index.html": "monthly", "journal.html": "weekly"}
    out = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for rel in pages:
        if rel in NO_INDEX:
            continue
        pr = priority.get(rel, "0.8" if rel.startswith("collection/") else
                          "0.7" if rel.startswith("journal/") else "0.5")
        cf = freq.get(rel, "monthly")
        out += [
            "  <url>",
            f"    <loc>{canonical_for(rel)}</loc>",
            f"    <lastmod>{today}</lastmod>",
            f"    <changefreq>{cf}</changefreq>",
            f"    <priority>{pr}</priority>",
            "  </url>",
        ]
    out.append("</urlset>")
    with open("sitemap.xml", "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")


def main():
    if not os.path.exists("index.html"):
        raise SystemExit("Run this from the repository root (index.html not found).")
    pages = html_pages()
    seo_n = sec_n = 0
    for rel in pages:
        src = open(rel, encoding="utf-8").read()
        src, s1 = inject_security(src)
        if rel not in NO_INDEX:
            src, s2 = inject_seo(rel, src)
        else:
            s2 = False
        if s1 or s2:
            open(rel, "w", encoding="utf-8").write(src)
        seo_n += int(s2)
        sec_n += int(s1)
    write_sitemap(pages)
    print(f"SEO tags added to {seo_n} page(s); CSP/referrer added to {sec_n} page(s).")
    print(f"sitemap.xml rebuilt with {sum(1 for p in pages if p not in NO_INDEX)} URLs.")


if __name__ == "__main__":
    main()
