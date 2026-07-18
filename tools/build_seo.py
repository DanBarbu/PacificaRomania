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
import json
import datetime

BASE = "https://pacificaromania.space/"
DEFAULT_IMG = "assets/images/folio/aboriginal-birds-in-space.jpg"

# ---- Analytics (Matomo, consent-gated) --------------------------------------
# Self-hosted Matomo on stats.pacificaromania.space (docs/analytics-setup.md).
# Matomo logs individual visitor IPs, so it is loaded ONLY after opt-in consent
# (assets/js/analytics.js). Paste the numeric Site ID to switch on. Empty = OFF.
# BEFORE setting MATOMO_SITE_ID, enable in the Matomo server admin
# (Administration -> Privacy -> Anonymize data): IP anonymisation = 2 bytes,
# support for Do Not Track, and 14-month log deletion. See
# docs/analytics-setup.md section 3. IP anonymisation is a Matomo-server
# setting; it cannot be enforced from this repo.
MATOMO_URL = "https://stats.pacificaromania.space/"   # trailing slash required
MATOMO_ORIGIN = MATOMO_URL.rstrip("/")
MATOMO_SITE_ID = ""   # e.g. "1" — empty = analytics disabled (safe default)
ANALYTICS_ON = bool(MATOMO_SITE_ID.strip())

# ---- Search-engine verification (AI visibility Phase 3) ----------------------
# Paste the HTML-tag token from Google Search Console (URL-prefix property) and
# Bing Webmaster Tools, then rerun this tool. Empty = no tag injected. The tag
# goes on the homepage only. See docs/phase3-external.md.
GSC_VERIFICATION = ""   # google-site-verification content value
BING_VERIFICATION = ""  # msvalidate.01 content value

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
    "tiger-in-chains": "tiger-in-chains.jpg",
    # Australia collection — per-artefact essays (images under assets/images/australia/)
    "frog-and-kangaroo-dreaming": "australia/frog-and-kangaroo-dreaming.jpg",
    "ngarlu-love-story": "australia/ngarlu-love-story.jpg",
    "seven-sisters": "australia/seven-sisters.jpg",
    "yuelamu-honey-ant-dreaming": "australia/yuelamu-honey-ant-dreaming.jpg",
    "bush-medicine-leaves": "australia/bush-medicine-leaves.jpg",
    "mountain-devil-lizard": "australia/mountain-devil-lizard.jpg",
    "bush-banana": "australia/bush-banana.jpg",
    "waltitjata": "australia/waltitjata.jpg",
    "tingari": "australia/tingari.jpg",
    "nine-mimis-and-rainbow-serpent": "australia/nine-mimis-and-rainbow-serpent.jpg",
    "body-paint": "australia/body-paint.jpg",
    "freshwater-crocodile": "australia/freshwater-crocodile.jpg",
    "water-goanna": "australia/water-goanna.jpg",
    "water-dreaming": "australia/my-country-water-dreaming.jpg",
    "ghost-gums": "australia/ghost-gums.jpg",
    "central-australian-landscape": "australia/central-australian-landscape.jpg",
    "witch-doctor-and-the-windmill": "australia/witch-doctor-and-the-windmill.jpg",
    "the-missionaries": "australia/the-missionaries.jpg",
    "dhari-headdress": "australia/dhari-headdress.jpg",
    "larrakitj-ezariah-kelly": "australia/larrakitj-ezariah-kelly.jpg",
    "larrakitj-napunda-marawili": "australia/larrakitj-napunda-marawili.jpg",
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
        val = ESSAY_IMG[slug]
        sub = val if "/" in val else "folio/" + val
        return BASE + "assets/images/" + sub
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


# ---- Structured data (JSON-LD) -----------------------------------------------
# Owned by this tool via the jsonld markers: never hand-edit the blocks in the
# HTML. Entity anchors tie the site into knowledge graphs AI systems trust.
FACEBOOK_URL = "https://www.facebook.com/profile.php?id=61574158391297"
ORG_NAME = "PacificaRomania Collection"
ORG = {
    "@type": "Organization",
    "@id": BASE + "#collection",
    "name": ORG_NAME,
    "url": BASE,
    "logo": BASE + DEFAULT_IMG,
    "email": "danbarbu22@gmail.com",
    "sameAs": [FACEBOOK_URL],
}
PERSONS = [
    {
        "@type": "Person",
        "name": "Mircea Eliade",
        "sameAs": [
            "https://www.wikidata.org/wiki/Q41590",
            "https://en.wikipedia.org/wiki/Mircea_Eliade",
        ],
    },
    {
        "@type": "Person",
        "name": "Constantin Brâncuși",
        "sameAs": [
            "https://www.wikidata.org/wiki/Q153048",
            "https://en.wikipedia.org/wiki/Constantin_Br%C3%A2ncu%C8%99i",
        ],
    },
]

VERIFY_START = "<!-- verify:start -->"
VERIFY_END = "<!-- verify:end -->"


def verification_block():
    metas = []
    if GSC_VERIFICATION.strip():
        metas.append('<meta name="google-site-verification" content="'
                     + html.escape(GSC_VERIFICATION.strip(), quote=True) + '">')
    if BING_VERIFICATION.strip():
        metas.append('<meta name="msvalidate.01" content="'
                     + html.escape(BING_VERIFICATION.strip(), quote=True) + '">')
    if not metas:
        return ""
    return VERIFY_START + "\n" + "\n".join(metas) + "\n" + VERIFY_END


def upsert_verification(src, rel):
    """Search-engine verification meta tags — homepage only, off until set."""
    if rel != "index.html":
        return src, False
    block = verification_block()
    existing = re.search(
        re.escape(VERIFY_START) + r".*?" + re.escape(VERIFY_END), src, re.S
    )
    if existing:
        if block:
            if existing.group(0) != block:
                return src[:existing.start()] + block + src[existing.end():], True
            return src, False
        new = src[:existing.start()] + src[existing.end():]
        new = new.replace('\n\n<link rel="stylesheet"', '\n<link rel="stylesheet"')
        return new, True
    if block:
        return src.replace('<link rel="stylesheet"', block + '\n<link rel="stylesheet"', 1), True
    return src, False


# FAQ — single source of truth for the visible block (About page) AND the
# FAQPage JSON-LD. Answers are plain text (no markup): safe in JSON and HTML.
FAQ = [
    {
        "q_en": "What is PacificaRomania?",
        "q_ro": "Ce este PacificaRomania?",
        "a_en": "PacificaRomania is a cultural art collection of over 150 works of "
                "Pacific and Island Southeast Asian art — painted Dreamings, war "
                "canoes, carved ancestors and sacred vessels — read through the "
                "comparative history of religion of Mircea Eliade and the sculptural "
                "cosmology of Constantin Brâncuși.",
        "a_ro": "PacificaRomania este o colecție de artă culturală cu peste 150 de "
                "lucrări de artă din Pacific și Asia de Sud-Est insulară — picturi "
                "Dreaming, canoe de război, strămoși sculptați și vase sacre — citite "
                "prin istoria comparată a religiilor a lui Mircea Eliade și cosmologia "
                "sculpturală a lui Constantin Brâncuși.",
    },
    {
        "q_en": "Where was the collection first exhibited?",
        "q_ro": "Unde a fost expusă colecția pentru prima dată?",
        "a_en": "It was first exhibited at the Embassy of Romania in Canberra, "
                "Australia, in 2019–2020, as a cultural-diplomacy project linking "
                "Romania and the Pacific.",
        "a_ro": "A fost expusă pentru prima dată la Ambasada României la Canberra, "
                "Australia, în 2019–2020, ca proiect de diplomație culturală care "
                "leagă România de Pacific.",
    },
    {
        "q_en": "What regions and cultures does the collection cover?",
        "q_ro": "Ce regiuni și culturi acoperă colecția?",
        "a_en": "Five regions: Aboriginal Australia, Melanesia, Micronesia, Polynesia "
                "and Island Southeast Asia — spanning Western Desert painting, Sepik "
                "and Solomon Islands sculpture, Marshallese navigation, Māori and "
                "Polynesian taonga, and Batak, Orang Asli, Dayak and Burmese art.",
        "a_ro": "Cinci regiuni: Australia aborigină, Melanezia, Micronezia, Polinezia "
                "și Asia de Sud-Est insulară — de la pictura din Deșertul de Vest și "
                "sculptura din Sepik și Insulele Solomon la navigația marshalleză, "
                "taonga maori și polineziene, și arta batak, orang asli, dayak și "
                "birmaneză.",
    },
    {
        "q_en": "How does the collection relate to Mircea Eliade and Constantin Brâncuși?",
        "q_ro": "Cum se raportează colecția la Mircea Eliade și Constantin Brâncuși?",
        "a_en": "The collection reads Pacific and Southeast Asian objects through "
                "Eliade's ideas of the sacred — hierophany, axis mundi, the eternal "
                "return — and sets them beside Brâncuși's pursuit of essential, "
                "originating form, treating each work as a living cosmology rather "
                "than an ethnographic artifact.",
        "a_ro": "Colecția citește obiectele din Pacific și Asia de Sud-Est prin ideile "
                "lui Eliade despre sacru — hierofanie, axis mundi, eterna reîntoarcere "
                "— și le așază alături de căutarea de către Brâncuși a formei "
                "esențiale, originare, tratând fiecare lucrare ca pe o cosmologie vie, "
                "nu ca pe un artefact etnografic.",
    },
    {
        "q_en": "Can the collection be visited, and how do I get in touch?",
        "q_ro": "Poate fi vizitată colecția și cum vă pot contacta?",
        "a_en": "PacificaRomania is presented online at pacificaromania.space, with "
                "curatorial essays in the Journal. For enquiries — including research, "
                "loans or exhibitions — contact danbarbu22@gmail.com.",
        "a_ro": "PacificaRomania este prezentată online la pacificaromania.space, cu "
                "eseuri curatoriale în Jurnal. Pentru solicitări — inclusiv cercetare, "
                "împrumuturi sau expoziții — scrieți la danbarbu22@gmail.com.",
    },
    {
        "q_en": "Who owns and operates PacificaRomania?",
        "q_ro": "Cine deține și administrează PacificaRomania?",
        "a_en": "The collection is operated by AlgorithmIntelligence SRL, based in "
                "Bucharest, Romania.",
        "a_ro": "Colecția este administrată de AlgorithmIntelligence SRL, cu sediul în "
                "București, România.",
    },
]

FAQ_START = "<!-- faq:start -->"
FAQ_END = "<!-- faq:end -->"


def faq_page_ld():
    return {
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": item["q_en"],
                "acceptedAnswer": {"@type": "Answer", "text": item["a_en"]},
            }
            for item in FAQ
        ],
    }


def faq_html():
    def esc(t):
        return html.escape(t, quote=False)
    items = []
    for it in FAQ:
        items.append(
            '<div class="faq-item">'
            f'<h3><span data-l="en">{esc(it["q_en"])}</span>'
            f'<span data-l="ro">{esc(it["q_ro"])}</span></h3>'
            f'<p><span data-l="en">{esc(it["a_en"])}</span>'
            f'<span data-l="ro">{esc(it["a_ro"])}</span></p>'
            '</div>'
        )
    body = "\n      ".join(items)
    return (
        f'{FAQ_START}\n<section class="faq-section">\n  <div class="wrap">\n'
        '    <div class="section-head"><div>\n'
        '      <span class="eyebrow"><span data-l="en">Questions</span>'
        '<span data-l="ro">Întrebări</span></span>\n'
        '      <h2><span data-l="en">Frequently asked questions</span>'
        '<span data-l="ro">Întrebări frecvente</span></h2>\n'
        '    </div></div>\n'
        f'    <div class="faq-list">\n      {body}\n    </div>\n'
        f'  </div>\n</section>\n{FAQ_END}'
    )


def upsert_faq(src, rel):
    if rel != "about.html":
        return src, False
    block = faq_html()
    existing = re.search(
        re.escape(FAQ_START) + r".*?" + re.escape(FAQ_END), src, re.S
    )
    if existing:
        if existing.group(0) != block:
            return src[:existing.start()] + block + src[existing.end():], True
        return src, False
    m = re.search(r"(\n[ \t]*)(<footer)", src)
    if not m:
        return src, False
    return src[:m.start()] + m.group(1) + block + m.group(1) + m.group(2) + src[m.end():], True


JSONLD_START = "<!-- jsonld:start -->"
JSONLD_END = "<!-- jsonld:end -->"


def page_title_desc(src):
    mt = re.search(r"<title>(.*?)</title>", src, re.S)
    md = re.search(r'<meta name="description" content="(.*?)">', src, re.S)
    if not mt or not md:
        return None, None
    title = html.unescape(mt.group(1).strip())
    # strip the site suffix ("… — PacificaRomania", "… — PacificaRomania Journal")
    title = re.sub(r"\s+—\s+PacificaRomania.*$", "", title)
    desc = html.unescape(md.group(1).strip())
    return title, desc


def breadcrumb_ld(rel, title):
    items = [("Home", BASE)]
    if rel.startswith("journal/"):
        items.append(("Journal", BASE + "journal.html"))
    elif rel.startswith("collection/"):
        items.append(("Collection", BASE + "collection.html"))
    items.append((title, canonical_for(rel)))
    return {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": n, "item": u}
            for i, (n, u) in enumerate(items)
        ],
    }


def jsonld_for(rel, src):
    """Return the page's JSON-LD graph (list of nodes), or None to skip."""
    title, desc = page_title_desc(src)
    if not title:
        return None
    canon = canonical_for(rel)

    if rel == "index.html":
        return [
            {
                "@type": "WebSite",
                "@id": BASE + "#website",
                "url": BASE,
                "name": "PacificaRomania",
                "description": desc,
                "inLanguage": ["en", "ro"],
                "publisher": {"@id": BASE + "#collection"},
                "about": PERSONS,
            },
            ORG,
        ]
    if rel.startswith("journal/"):
        return [
            {
                "@type": "Article",
                "headline": title,
                "description": desc,
                "image": og_image_for(rel),
                "url": canon,
                "inLanguage": ["en", "ro"],
                "author": {"@type": "Organization", "name": ORG_NAME, "url": BASE},
                "publisher": {"@type": "Organization", "name": ORG_NAME,
                              "url": BASE, "logo": {"@type": "ImageObject",
                                                    "url": BASE + DEFAULT_IMG}},
                "mentions": PERSONS,
                "isPartOf": {"@id": BASE + "#website"},
            },
            breadcrumb_ld(rel, title),
        ]
    if rel.startswith("collection/") or rel == "collection.html":
        return [
            {
                "@type": "CollectionPage",
                "name": title,
                "description": desc,
                "url": canon,
                "inLanguage": ["en", "ro"],
                "isPartOf": {"@id": BASE + "#website"},
            },
            breadcrumb_ld(rel, title),
        ]
    if rel == "journal.html":
        return [
            {
                "@type": "Blog",
                "name": title,
                "description": desc,
                "url": canon,
                "inLanguage": ["en", "ro"],
                "publisher": {"@type": "Organization", "name": ORG_NAME, "url": BASE},
            },
            breadcrumb_ld(rel, title),
        ]
    if rel in ("about.html", "contact.html"):
        typ = "AboutPage" if rel == "about.html" else "ContactPage"
        node = {
            "@type": typ,
            "name": title,
            "description": desc,
            "url": canon,
            "inLanguage": ["en", "ro"],
            "isPartOf": {"@id": BASE + "#website"},
        }
        if rel == "about.html":
            node["about"] = PERSONS
            return [node, faq_page_ld(), breadcrumb_ld(rel, title)]
        return [node, breadcrumb_ld(rel, title)]
    return None  # privacy, legal, 404: skip


def upsert_jsonld(src, rel):
    graph = jsonld_for(rel, src)
    if graph is None:
        return src, False
    payload = json.dumps({"@context": "https://schema.org", "@graph": graph},
                         ensure_ascii=False, indent=1)
    block = (f'{JSONLD_START}\n<script type="application/ld+json">\n'
             f"{payload}\n</script>\n{JSONLD_END}")
    existing = re.search(
        re.escape(JSONLD_START) + r".*?" + re.escape(JSONLD_END), src, re.S
    )
    if existing:
        if existing.group(0) != block:
            return src[:existing.start()] + block + src[existing.end():], True
        return src, False
    return src.replace("</head>", block + "\n</head>", 1), True


def write_llms(pages):
    """Generate /llms.txt — a markdown index of the site for AI agents."""
    out = [
        "# PacificaRomania",
        "",
        "> PacificaRomania is a cultural art collection of over 150 works of "
        "Pacific and Island Southeast Asian art — painted Dreamings, war canoes, "
        "carved ancestors, and sacred vessels — first exhibited at the Embassy of "
        "Romania in Canberra (2019–2020) and read through the comparative history "
        "of religion of Mircea Eliade and the sculptural cosmology of Constantin "
        "Brâncuși.",
        "",
        "Operated by AlgorithmIntelligence SRL, Bucharest, Romania. "
        "Contact: danbarbu22@gmail.com. All pages are bilingual (English and "
        "Romanian, both languages present in the same HTML).",
        "",
    ]
    sections = [("Collection", lambda r: r.startswith("collection")),
                ("Journal (curatorial essays)", lambda r: r.startswith("journal")),
                ("About", lambda r: r in ("index.html", "about.html", "contact.html"))]
    for label, match in sections:
        out.append(f"## {label}")
        out.append("")
        for rel in pages:
            if rel in NO_INDEX or rel in EXCLUDE or not match(rel):
                continue
            src = open(rel, encoding="utf-8").read()
            title, desc = page_title_desc(src)
            if not title:
                continue
            out.append(f"- [{title}]({canonical_for(rel)}): {desc}")
        out.append("")
    with open("llms.txt", "w", encoding="utf-8") as fh:
        fh.write("\n".join(out))


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

    if "og:title" in src:
        # Already tagged — re-sync the title/description-derived fields so
        # editing <title> or the meta description propagates to social cards.
        new = src
        for pat, val in (
            (r'(<meta property="og:title" content=")[^"]*(">)', title),
            (r'(<meta property="og:description" content=")[^"]*(">)', desc),
            (r'(<meta property="og:image" content=")[^"]*(">)', img),
            (r'(<meta name="twitter:title" content=")[^"]*(">)', title),
            (r'(<meta name="twitter:description" content=")[^"]*(">)', desc),
            (r'(<meta name="twitter:image" content=")[^"]*(">)', img),
        ):
            new = re.sub(pat, lambda m, v=val: m.group(1) + v + m.group(2), new, count=1)
        return new, (new != src)

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
    seo_n = sec_n = an_n = leg_n = ld_n = 0
    for rel in pages:
        if rel in EXCLUDE:
            continue
        prefix = "../" if "/" in rel else ""
        src = open(rel, encoding="utf-8").read()
        src, s1 = upsert_security(src)
        src, s3 = upsert_analytics(src, prefix)
        src, s4 = upsert_legal_links(src, prefix)
        src, s6 = upsert_faq(src, rel)
        src, s7 = upsert_verification(src, rel)
        src, s5 = upsert_jsonld(src, rel)
        if rel not in NO_INDEX:
            src, s2 = inject_seo(rel, src)
        else:
            s2 = False
        if s1 or s2 or s3 or s4 or s5 or s6 or s7:
            open(rel, "w", encoding="utf-8").write(src)
        seo_n += int(s2)
        sec_n += int(s1)
        an_n += int(s3)
        leg_n += int(s4)
        ld_n += int(s5)
    n = write_sitemap(pages)
    write_llms(pages)
    state = "ON — Matomo site " + MATOMO_SITE_ID.strip() if ANALYTICS_ON else "OFF"
    print(f"Analytics: {state}")
    print(f"SEO tags added to {seo_n} page(s); CSP updated on {sec_n} page(s); "
          f"analytics tag changed on {an_n} page(s); legal links on {leg_n} page(s); "
          f"JSON-LD updated on {ld_n} page(s).")
    print(f"sitemap.xml rebuilt with {n} URLs; llms.txt regenerated.")


if __name__ == "__main__":
    main()
