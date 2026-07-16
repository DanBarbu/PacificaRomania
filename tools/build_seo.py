#!/usr/bin/env python3
"""
build_seo.py — regenerate sitemap.xml and inject SEO + security + analytics tags.

Run from the repository root:

    python3 tools/build_seo.py

It is idempotent and safe to re-run after adding new pages or after enabling
analytics:
  * Adds <link rel="canonical">, Open Graph and Twitter card tags to any
    HTML page that does not already have them (keyed on 'og:title').
  * Upserts a Content-Security-Policy + referrer meta on every page. The CSP is
    widened automatically to allow the analytics domain ONLY when analytics is
    enabled (see UMAMI_WEBSITE_ID below).
  * Upserts the Umami analytics snippet on every content page when enabled.
  * Rebuilds sitemap.xml from the current set of pages.

--- Analytics setup (Umami, self-hosted on stats.pacificaromania.space) -------
1. Deploy Umami and create a website for pacificaromania.space (see
   docs/analytics-setup.md).
2. Copy the generated "Website ID" (a UUID) into UMAMI_WEBSITE_ID below.
3. Run:  python3 tools/build_seo.py
   -> the tracker tag + widened CSP are written into every page.
Leaving UMAMI_WEBSITE_ID empty keeps analytics OFF and the CSP tight; nothing
loads from the stats subdomain. This is the safe default.
"""
import os
import re
import html
import datetime

BASE = "https://pacificaromania.space/"
DEFAULT_IMG = "assets/images/folio/aboriginal-birds-in-space.jpg"

# ---- Analytics (Umami) -------------------------------------------------------
# Self-hosted Umami dashboard. Point stats.pacificaromania.space DNS at your
# deployment (docs/analytics-setup.md). Paste the website UUID to switch on.
UMAMI_DOMAIN = "https://stats.pacificaromania.space"
UMAMI_SCRIPT = UMAMI_DOMAIN + "/script.js"
UMAMI_WEBSITE_ID = ""  # e.g. "0f2c...uuid..." — empty = analytics disabled
ANALYTICS_ON = bool(UMAMI_WEBSITE_ID.strip())

# Pages never tracked / never indexed / never SEO-tagged.
EXCLUDE = {"admin.html"}          # hand-maintained admin hub (noindex)
NO_INDEX = {"404.html"}           # kept out of the sitemap only

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


def compute_csp():
    script = "script-src 'self' 'unsafe-inline'"
    connect = "connect-src 'self'"
    if ANALYTICS_ON:
        script += " " + UMAMI_DOMAIN
        connect += " " + UMAMI_DOMAIN
    return (
        f"default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; "
        f"{script}; {connect}; font-src 'self'; object-src 'none'; "
        f"base-uri 'self'; form-action 'self'; frame-src 'none'; upgrade-insecure-requests"
    )


ANALYTICS_START = "<!-- analytics:start -->"
ANALYTICS_END = "<!-- analytics:end -->"


def analytics_block():
    if not ANALYTICS_ON:
        return ""
    return (
        f"{ANALYTICS_START}\n"
        f'<script defer src="{UMAMI_SCRIPT}" '
        f'data-website-id="{html.escape(UMAMI_WEBSITE_ID.strip(), quote=True)}"></script>\n'
        f"{ANALYTICS_END}"
    )


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


def upsert_security(src):
    """Ensure referrer meta exists and the CSP meta matches compute_csp()."""
    csp = compute_csp()
    changed = False
    if "Content-Security-Policy" in src:
        new = re.sub(
            r'(<meta http-equiv="Content-Security-Policy" content=")[^"]*(">)',
            lambda m: m.group(1) + csp + m.group(2),
            src, count=1,
        )
        if new != src:
            src, changed = new, True
    else:
        m = re.search(r'<meta charset="utf-8">', src)
        if m:
            block = (
                f'<meta http-equiv="Content-Security-Policy" content="{csp}">\n'
                '<meta name="referrer" content="strict-origin-when-cross-origin">'
            )
            src = src.replace(m.group(0), m.group(0) + "\n" + block, 1)
            changed = True
    return src, changed


def upsert_analytics(src):
    """Insert/replace/remove the Umami block to match ANALYTICS_ON."""
    existing = re.search(
        re.escape(ANALYTICS_START) + r".*?" + re.escape(ANALYTICS_END), src, re.S
    )
    block = analytics_block()
    if existing:
        if block:
            if existing.group(0) != block:
                return src[:existing.start()] + block + src[existing.end():], True
            return src, False
        # analytics turned off -> strip the block (and a trailing newline)
        new = src[:existing.start()] + src[existing.end():]
        new = new.replace("\n\n</head>", "\n</head>")
        return new, True
    if block:
        return src.replace("</head>", block + "\n</head>", 1), True
    return src, False


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
    n = 0
    for rel in pages:
        if rel in NO_INDEX or rel in EXCLUDE:
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
        n += 1
    out.append("</urlset>")
    with open("sitemap.xml", "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")
    return n


def main():
    if not os.path.exists("index.html"):
        raise SystemExit("Run this from the repository root (index.html not found).")
    pages = html_pages()
    seo_n = sec_n = an_n = 0
    for rel in pages:
        if rel in EXCLUDE:
            continue
        src = open(rel, encoding="utf-8").read()
        src, s1 = upsert_security(src)
        src, s3 = upsert_analytics(src)
        if rel not in NO_INDEX:
            src, s2 = inject_seo(rel, src)
        else:
            s2 = False
        if s1 or s2 or s3:
            open(rel, "w", encoding="utf-8").write(src)
        seo_n += int(s2)
        sec_n += int(s1)
        an_n += int(s3)
    n = write_sitemap(pages)
    state = "ON (" + UMAMI_WEBSITE_ID.strip() + ")" if ANALYTICS_ON else "OFF"
    print(f"Analytics: {state}")
    print(f"SEO tags added to {seo_n} page(s); CSP updated on {sec_n} page(s); "
          f"analytics tag changed on {an_n} page(s).")
    print(f"sitemap.xml rebuilt with {n} URLs.")


if __name__ == "__main__":
    main()
