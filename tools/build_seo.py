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

# ---- Analytics (Matomo, consent-gated) --------------------------------------
# Self-hosted Matomo on stats.pacificaromania.space (docs/analytics-setup.md).
# Matomo logs individual visitor IPs, so it is loaded ONLY after opt-in consent
# (assets/js/analytics.js). Paste the numeric Site ID to switch on. Empty = OFF.
MATOMO_URL = "https://stats.pacificaromania.space/"   # trailing slash required
MATOMO_ORIGIN = MATOMO_URL.rstrip("/")
MATOMO_SITE_ID = ""   # e.g. "1" — empty = analytics disabled (safe default)
ANALYTICS_ON = bool(MATOMO_SITE_ID.strip())

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
    img = "img-src 'self' data:"
    script = "script-src 'self' 'unsafe-inline'"
    connect = "connect-src 'self'"
    if ANALYTICS_ON:
        img += " " + MATOMO_ORIGIN            # Matomo tracking pixel
        script += " " + MATOMO_ORIGIN         # matomo.js
        connect += " " + MATOMO_ORIGIN        # matomo.php beacon
    return (
        f"default-src 'self'; {img}; style-src 'self' 'unsafe-inline'; "
        f"{script}; {connect}; font-src 'self'; object-src 'none'; "
        f"base-uri 'self'; form-action 'self'; frame-src 'none'; upgrade-insecure-requests"
    )


ANALYTICS_START = "<!-- analytics:start -->"
ANALYTICS_END = "<!-- analytics:end -->"


def analytics_block(prefix):
    """Consent-gated Matomo loader. `prefix` is '' or '../' for the asset path."""
    if not ANALYTICS_ON:
        return ""
    sid = html.escape(MATOMO_SITE_ID.strip(), quote=True)
    return (
        f"{ANALYTICS_START}\n"
        f'<script>window.PR_MATOMO={{url:"{MATOMO_URL}",siteId:"{sid}"}};</script>\n'
        f'<script defer src="{prefix}assets/js/analytics.js"></script>\n'
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


def upsert_analytics(src, prefix):
    """Insert/replace/remove the Matomo block to match ANALYTICS_ON."""
    existing = re.search(
        re.escape(ANALYTICS_START) + r".*?" + re.escape(ANALYTICS_END), src, re.S
    )
    block = analytics_block(prefix)
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


LEGAL_START = "<!-- legal:start -->"
LEGAL_END = "<!-- legal:end -->"


def legal_links(prefix):
    """Bilingual Privacy / Legal footer links, depth-aware."""
    return (
        f'{LEGAL_START}<span class="footer-legal">'
        f'<a href="{prefix}privacy.html"><span data-l="en">Privacy &amp; Cookies</span>'
        f'<span data-l="ro">Confidențialitate &amp; Cookie</span></a> &middot; '
        f'<a href="{prefix}legal.html"><span data-l="en">Legal notice</span>'
        f'<span data-l="ro">Mențiuni legale</span></a>'
        f'</span>{LEGAL_END}'
    )


def upsert_legal_links(src, prefix):
    """Ensure the Privacy/Legal links sit inside .footer-bottom (idempotent)."""
    block = legal_links(prefix)
    existing = re.search(
        re.escape(LEGAL_START) + r".*?" + re.escape(LEGAL_END), src, re.S
    )
    if existing:
        if existing.group(0) != block:
            return src[:existing.start()] + block + src[existing.end():], True
        return src, False
    # insert as the first child of <div class="footer-bottom">
    m = re.search(r'(<div class="footer-bottom">)', src)
    if not m:
        return src, False
    return src[:m.end()] + "\n      " + block + src[m.end():], True


def inject_seo(rel, src):
    if "og:title" in src:
        return src, False
    mt = re.search(r"<title>(.*?)</title>", src, re.S)
    md = re.search(r'<meta name="description" content="(.*?)">', src, re.S)
    if not mt or not md:
        return src, False
    # Titles/descriptions may already contain entities (e.g. &amp;); normalise
    # first so we escape exactly once and never emit &amp;amp;.
    title = html.escape(html.unescape(mt.group(1).strip()), quote=True)
    desc = html.escape(html.unescape(md.group(1).strip()), quote=True)
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
    seo_n = sec_n = an_n = leg_n = 0
    for rel in pages:
        if rel in EXCLUDE:
            continue
        prefix = "../" if "/" in rel else ""
        src = open(rel, encoding="utf-8").read()
        src, s1 = upsert_security(src)
        src, s3 = upsert_analytics(src, prefix)
        src, s4 = upsert_legal_links(src, prefix)
        if rel not in NO_INDEX:
            src, s2 = inject_seo(rel, src)
        else:
            s2 = False
        if s1 or s2 or s3 or s4:
            open(rel, "w", encoding="utf-8").write(src)
        seo_n += int(s2)
        sec_n += int(s1)
        an_n += int(s3)
        leg_n += int(s4)
    n = write_sitemap(pages)
    state = "ON — Matomo site " + MATOMO_SITE_ID.strip() if ANALYTICS_ON else "OFF"
    print(f"Analytics: {state}")
    print(f"SEO tags added to {seo_n} page(s); CSP updated on {sec_n} page(s); "
          f"analytics tag changed on {an_n} page(s); legal links on {leg_n} page(s).")
    print(f"sitemap.xml rebuilt with {n} URLs.")


if __name__ == "__main__":
    main()
