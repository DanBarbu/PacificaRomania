---
name: site-admin
description: >-
  Maintain and extend the PacificaRomania (pacificaromania.space) bilingual
  static art-collection website. Use this when adding or editing curatorial
  essays, collection objects, or pages; when translating content between
  English and Romanian; and when applying SEO or security/cyber-hardening
  improvements. Covers the repo's conventions (EN/RO toggle, lightbox,
  Open Graph, CSP), the build/verify tooling under tools/, and the deploy
  workflow to GitHub Pages.
---

# PacificaRomania — Site Admin Skill

This is a hand-built **static** site (plain HTML + CSS + a little vanilla JS)
served by **GitHub Pages** from the `main` branch at
**https://pacificaromania.space**. There is no build framework and no server:
whatever HTML is committed is exactly what ships. Because Pages cannot set HTTP
headers, security is done with `<meta>` tags and static files.

Always finish an editing session by running the two tools in
[Verify & deploy](#verify--deploy) and committing to `main`.

## Repository map

```
index.html  about.html  collection.html  journal.html  contact.html  404.html
CNAME                      # custom domain: pacificaromania.space
robots.txt  sitemap.xml    # SEO — sitemap is generated, do not hand-edit
.nojekyll                  # tell Pages to serve files as-is (no Jekyll)
.well-known/security.txt   # security contact (securitytxt.org)
collection/                # region galleries: australia, melanesia, micronesia,
                           #   polynesia, island-southeast-asia (.html)
journal/                   # one .html per curatorial essay
privacy.html  legal.html   # bilingual GDPR/ePrivacy + Impressum/Terms pages
admin.html                 # private (noindex) admin hub: analytics + UTM builder
docs/analytics-setup.md    # how to deploy Matomo analytics + enable it
docs/eu-compliance.md      # EU legal checklist (GDPR/ePrivacy/DSA/NIS2/EAA)
assets/css/style.css       # the ONE shared stylesheet
assets/js/main.js          # nav toggle
assets/js/i18n.js          # EN/RO language switch
assets/js/analytics.js     # consent banner + consent-gated Matomo loader
assets/js/lightbox.js      # click-to-zoom on essay images
assets/images/{australia,melanesia,micronesia,polynesia}/  # catalogue photos
assets/images/folio/       # essay lead images + journal thumbnails
tools/build_seo.py         # (re)gen sitemap + inject SEO/CSP/analytics head tags
tools/verify.py            # pre-deploy link / tag / parity checker
```

## Core conventions (do not break these)

### 1. Bilingual EN/RO
Every visible string exists twice, wrapped so the language toggle can show one:

```html
<span data-l="en">Home</span><span data-l="ro">Acasă</span>
```

- `assets/js/i18n.js` toggles `class="lang-ro"` on `<html>` and stores the
  choice in `localStorage['pr-lang']`.
- CSS in `style.css` hides the inactive language.
- **Every page** must carry this no-flash snippet in `<head>` (before the
  stylesheet) so RO readers never see an EN flash on load:
  ```html
  <script>(function(){try{if(localStorage.getItem('pr-lang')==='ro')document.documentElement.className+=' lang-ro';}catch(e){}})();</script>
  ```
- For block-level bilingual content use two sibling divs, never a block inside
  an inline span:
  ```html
  <div data-l="en"> …English essay body… </div>
  <div data-l="ro"> …Romanian essay body… </div>
  ```
- **RO is required.** English-only additions are a regression. Object
  title/maker/medium lines are the one museum-convention exception (kept in the
  original language). `tools/verify.py` warns on EN/RO imbalance.

### 2. Translation register
Romanian must be **academic curatorial** prose, not literal MT: diacritics
always (ă â î ș ț), scholarly vocabulary (e.g. *hierofanie*, *illud tempus*,
*axis mundi*). Match the tone of the existing essays in `journal/`.

### 3. Shared head, header, footer
Copy an existing page of the same type as your template so the header nav,
language switcher, footer, and script tags stay identical. The footer of an
essay loads, in order: `main.js`, `i18n.js`, `lightbox.js`.

### 4. Images
- Essay lead + body images live in `assets/images/folio/`; `lightbox.js`
  auto-wires any `.essay-lead img` / `.essay-body img` for click-to-zoom.
- Resize new photos to ~1400px on the long edge, JPEG quality ~82.
- Every `<img>` needs a meaningful `alt` (SEO + accessibility). Decorative
  thumbnails may use `alt=""`.
- The Journal index row and the essay page should share the same folio image.

## How to add a new curatorial essay

1. Copy the closest existing file in `journal/` (e.g. `raja-bomoh.html`) to
   `journal/<slug>.html`. Use a short, hyphenated, lowercase slug.
2. Update, keeping EN+RO for each: `<title>`, meta description, the lead
   image + caption, `<h1>`, dek, and the essay body (two `data-l` divs).
3. Add the lead image to `assets/images/folio/<slug>.jpg`.
4. Add a row to `journal.html` (the index). Start the row with the thumbnail:
   ```html
   <img class="journal-thumb" src="assets/images/folio/<slug>.jpg" alt="" loading="lazy">
   ```
   and give the row bilingual title + dek.
5. Register the essay's share image in `tools/build_seo.py` → `ESSAY_IMG`
   (`"<slug>": "<slug>.jpg"`).
6. Run the [verify & deploy](#verify--deploy) steps.

## How to add a collection object / region page

- Object cards go in the relevant `collection/<region>.html` inside
  `.object-gallery`, following the existing `.object-card` markup (bilingual
  note in two `data-l` blocks; title/maker/medium may stay single-language).
- A brand-new region page = copy an existing `collection/*.html`, then add its
  card/link on `collection.html`. `tools/build_seo.py` will pick it up for the
  sitemap and head tags automatically on the next run.

## SEO — what every page must have

`tools/build_seo.py` maintains these; run it after adding pages. Each page
carries, in `<head>`:

- a real, unique `<title>` and `<meta name="description">` (write these by hand
  per page — the tool does **not** invent copy);
- `<link rel="canonical" href="https://pacificaromania.space/…">`;
- Open Graph (`og:type/title/description/url/image`, plus
  `og:locale` en + `og:locale:alternate` ro) and Twitter `summary_large_image`;
- the homepage additionally carries JSON-LD (`WebSite` + `Organization`).

Sitewide SEO files: `sitemap.xml` (generated), `robots.txt` (points at the
sitemap), and semantic HTML headings. After adding/removing pages:

```bash
python3 tools/build_seo.py     # rebuilds sitemap.xml, fills tags on new pages
```

When you add or meaningfully change a page, bump nothing by hand — just rerun
the tool so `sitemap.xml` `lastmod` refreshes.

## Security / cyber-hardening (static-site model)

GitHub Pages serves over HTTPS and cannot set response headers, so protection
is done in-page and by hygiene:

- **Content-Security-Policy meta** on every page (added by `build_seo.py`):
  `default-src 'self'`, no external scripts/styles/objects, `frame-src 'none'`,
  `upgrade-insecure-requests`. Keep the site self-hosted — do **not** add CDN
  scripts, remote fonts, analytics beacons, or embeds, or the CSP must be
  loosened (avoid). If you must embed, prefer `<img>`/`<a>` over `<script>`.
- **Referrer policy** meta: `strict-origin-when-cross-origin`.
- **External links**: any `target="_blank"` must include
  `rel="noopener noreferrer"`.
- **`.well-known/security.txt`**: keep the `Expires` date in the future
  (refresh yearly) and the `Contact` current.
- **No secrets, ever**: this repo is public and fully served. No API keys,
  tokens, `.env`, private addresses, or unpublished personal data in committed
  files. Before pushing, scan the diff.
- **Custom domain**: `CNAME` must stay `pacificaromania.space`; keep
  "Enforce HTTPS" enabled in the repo's Pages settings.
- **Dependencies**: there is no JS supply chain here (all first-party vanilla
  JS) — keep it that way; it is the site's strongest security property.

## Analytics, consent & ad campaigns

Traffic analytics use **Matomo** (free, open-source), self-hosted on
`stats.pacificaromania.space`, loaded **only after opt-in consent** because it
logs individual IPs. Admin hub at `/admin.html`. Deploy/DNS/enable steps are in
**`docs/analytics-setup.md`**; the EU legal checklist is in
**`docs/eu-compliance.md`**.

- **On/off is one variable**: `MATOMO_SITE_ID` in `tools/build_seo.py`. Empty =
  analytics OFF, CSP tight, no consent banner (the default committed state).
  Paste the numeric Site ID and rerun `build_seo.py` to inject the consent-gated
  loader on every content page and widen the CSP to allow the Matomo host in
  `script-src`, `img-src`, and `connect-src`. Blank it + rerun to fully remove.
- **Consent is mandatory** (GDPR + ePrivacy): `assets/js/analytics.js` shows a
  bilingual banner, loads Matomo only on "Accept", treats Do-Not-Track as a
  refusal, and exposes a persistent "Cookie settings" control. Don't bypass it.
- **Never hand-edit** the analytics tag, the CSP, the footer legal links, the
  JSON-LD structured-data blocks, or the About-page FAQ in the HTML —
  `build_seo.py` owns them all (marker comments `analytics:*`, `legal:*`,
  `jsonld:*`, `faq:*`) and will overwrite them. The FAQ's visible block and its
  FAQPage schema are both generated from the single `FAQ` list in
  `build_seo.py` — edit the copy there. Change the config constants / generator
  functions instead. The tool
  also regenerates `llms.txt` (the AI-agent site index) and `sitemap.xml` on
  every run, and `robots.txt` carries an explicit allow-list of AI crawlers
  (see `docs/ai-visibility-plan.md` for the policy and monthly routine).
- **Legal pages**: `privacy.html` (Privacy & Cookie Policy) and `legal.html`
  (Legal Notice/Impressum + Terms), bilingual, linked in every footer. If you
  add data collection, update `privacy.html`. The `[insert legal name…]`
  placeholders in both must be filled by the operator.
- **`admin.html`** is the monitoring hub (Matomo dashboard link + UTM builder).
  `noindex`, robots-disallowed, and **excluded from `build_seo.py`**
  (hand-maintained head). Still a public URL — keep no secrets on it.
- **Ad campaigns**: tag links with `utm_source/medium/campaign` (lowercase,
  consistent) so Matomo's Campaigns report attributes them; use the builder on
  `admin.html`.

## Verify & deploy

Run from the repo root every time before committing:

```bash
python3 tools/build_seo.py     # 1. refresh sitemap + head tags
python3 tools/verify.py        # 2. fail on broken links / malformed tags / missing SEO
```

`verify.py` exits non-zero on real errors (broken links, malformed nested
tags) and prints warnings for missing SEO tags or EN/RO imbalance. Fix errors
before deploying.

Optional visual check (Chromium is preinstalled at `/opt/pw-browsers/chromium`;
use `NODE_PATH=$(npm root -g)` if Playwright can't resolve):

```bash
NODE_PATH=$(npm root -g) node -e "…screenshot script…"
```

Then commit and push to `main` (Pages deploys from `main`):

```bash
git add -A
git commit -m "<clear description of the change>"
git push origin main
```

GitHub Pages redeploys automatically. Confirm the "pages build and deployment"
workflow succeeds. If a change "doesn't show", it is almost always browser
cache — hard-refresh (Ctrl/Cmd+Shift+R) or use a private window before
assuming a bug.

## Quick reference

| Task | Do this |
|------|---------|
| New essay | copy `journal/<x>.html`, add folio image, add index row, register in `build_seo.py`, run tools |
| New object | add `.object-card` in the region file (bilingual note) |
| New page | copy a same-type page, then `python3 tools/build_seo.py` |
| Any text edit | keep EN **and** RO in sync |
| SEO refresh | `python3 tools/build_seo.py` |
| Enable analytics | set `UMAMI_WEBSITE_ID` in `build_seo.py`, rerun it (see `docs/analytics-setup.md`) |
| Ad-campaign link | use the UTM builder on `/admin.html` |
| Before every push | `python3 tools/verify.py` (must pass), then commit to `main` |
| Never commit | secrets, external `<script>`/CDN, RO-less content |
