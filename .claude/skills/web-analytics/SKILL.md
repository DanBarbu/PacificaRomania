---
name: web-analytics
description: >-
  Add Google Analytics 4 (GA4 / gtag.js) website-traffic monitoring to any
  website — static multi-page sites, templated/build-step sites, or SPAs. Use
  this when the user wants to "add Google Analytics", "track website traffic",
  "set up GA4", "add the gtag", or check why analytics isn't recording hits.
  Covers getting a Measurement ID, injecting the tag into every page's <head>,
  the Content-Security-Policy allowances GA needs (the #1 silent-failure cause),
  privacy/consent, and how to verify hits are landing. Provider-agnostic notes
  for Plausible/Matomo are included at the end.
---

# Web Analytics (Google Analytics 4)

Add aggregate traffic monitoring — page views, sessions, referrers, geography —
to a website with Google Analytics 4. The whole job is three things done right:
**(1)** the tag on every page, **(2)** the Content-Security-Policy allowing it,
**(3)** verification that hits actually land. Most "GA isn't working" reports are
CSP silently blocking the tag.

## 0. Get a Measurement ID

The user needs a GA4 **Measurement ID** — format `G-XXXXXXXXXX`.
In [analytics.google.com](https://analytics.google.com): **Admin → Data Streams
→ Web → (create or open the stream) →** copy the Measurement ID. If they already
have GA on another property, reuse that ID only if they want the traffic counted
together; otherwise make a new Web data stream. Ask the user for the ID — never
invent one.

## 1. The canonical gtag snippet

Goes in `<head>`, as high as practical, on **every** page. Replace the ID:

```html
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-XXXXXXXXXX');
</script>
```

That's the entire tag. GA4 records a `page_view` automatically on load and
anonymises IP addresses by default.

## 2. Put it on every page — by architecture

Pick the approach that matches the site; the goal is that **no page ships
without the tag** and that adding a page later doesn't silently drop it.

- **Build step / templating (best).** If the site has a generator, template
  partial, shared header include (SSI, Jekyll `_includes`, Eleventy, Hugo
  `partials/head.html`, PHP `include`), or a post-processing script, put the
  snippet there once. This repo does it in a Python post-processor —
  see the worked example below. A single source of truth can't drift.
- **Static multi-page, no build.** Add the snippet to each page's `<head>`.
  Prefer a scripted edit that inserts it right after `<head>` (or before
  `</head>`) on every `*.html`, and is idempotent (skip files that already
  contain the Measurement ID) so re-runs don't duplicate it.
- **SPA (React / Vue / Angular / Next / Nuxt).** Put the loader in the single
  `index.html` `<head>` (or the framework's document head). Because the SPA
  doesn't reload between routes, GA only auto-fires one `page_view`. Send one
  on each route change:
  ```js
  // on every route change:
  gtag('event', 'page_view', { page_path: location.pathname + location.search });
  ```
  Framework helpers (`next/third-parties` `<GoogleAnalytics>`, `vue-gtag`,
  `@analytics/google-analytics`) wrap this — prefer them in those stacks.

**Exclude internal pages** (admin panels, dashboards, staging-only pages) from
tracking unless the user wants them counted.

## 3. Content-Security-Policy — the silent killer

If the site sends a CSP — as a `<meta http-equiv="Content-Security-Policy">` tag
**or** an HTTP header — GA is blocked unless the policy allows Google's hosts.
The failure is silent: no error dialog, just zero data. Add these sources to the
existing directives (don't drop what's already there):

| Directive     | Add                                                            | Why |
|---------------|---------------------------------------------------------------|-----|
| `script-src`  | `https://www.googletagmanager.com`                            | loads `gtag.js` |
| `img-src`     | `https://www.googletagmanager.com https://*.google-analytics.com` | collect pixel |
| `connect-src` | `https://*.google-analytics.com https://*.googletagmanager.com`   | GA4 `fetch`/beacon hits |

Also: the inline init `<script>` needs `script-src` to permit inline JS —
either `'unsafe-inline'`, or a per-request **nonce** (`<script nonce="…">` +
`script-src 'nonce-…'`), or move the four init lines into an external `.js` file
served from `'self'`. Prefer a nonce over `'unsafe-inline'` on security-sensitive
sites.

If the CSP lives in an HTTP header (nginx/Apache/Cloudflare/`_headers`/hosting
config) rather than a meta tag, edit it there — grep the repo and server config
for `Content-Security-Policy` so you change the real source, not a stale copy.

## 4. Privacy & consent

GA4 sets cookies and processes visitor data. Do the responsible minimum:

- Ensure the site has a **privacy / cookie policy** that mentions Google
  Analytics; add a line if missing.
- For visitors in the **EU/UK/EEA**, consent is generally required before
  loading analytics. Use **Google Consent Mode v2**: load gtag but set
  `gtag('consent', 'default', { analytics_storage: 'denied' })` first, then
  flip to `granted` when the user accepts in a cookie banner. Or gate the whole
  tag behind an opt-in (load it only after consent). Ask the user which they
  want; don't assume.
- GA4 anonymises IPs by default; you can also shorten data-retention in
  **Admin → Data Settings → Data Retention**.

A consent-gated pattern (load nothing until opt-in):

```html
<script>
  function loadGA(){
    if (window.__gaLoaded) return; window.__gaLoaded = true;
    var s=document.createElement('script'); s.async=true;
    s.src='https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX';
    document.head.appendChild(s);
    window.dataLayer=window.dataLayer||[];
    function gtag(){dataLayer.push(arguments);}
    gtag('js',new Date()); gtag('config','G-XXXXXXXXXX');
  }
  // call loadGA() from your cookie-banner "Accept" handler
</script>
```

## 5. Verify it works — always do this

1. **GA Realtime.** Open the site, then GA4 → **Reports → Realtime**; you should
   appear within seconds. This is the definitive check.
2. **Network tab.** DevTools → Network, filter `collect` (or `g/collect`); a
   `page_view` request returning **204/200** means the hit sent.
3. **Console.** A `Refused to load … Content Security Policy` error means step 3
   is incomplete — fix the CSP.
4. **DebugView.** GA4 → Admin → **DebugView** (with the GA Debugger extension or
   `?_dbg=1`) for event-level confirmation.

## Common pitfalls

- **CSP blocking the tag** — the most common cause of "no data"; see §3.
- **Ad / tracking blockers** — uBlock, Brave, Firefox ETP block GA; test in a
  clean profile before concluding the tag is broken.
- **ID typo / wrong stream** — `G-` (GA4) vs `UA-` (dead Universal Analytics) vs
  `GT-`/`AW-`; confirm it's the Web data stream's `G-` ID.
- **Snippet in `<body>` or added late** — keep it in `<head>`.
- **SPA firing once** — send `page_view` on route change (§2).
- **Duplicate tags** — two snippets double-count; make injection idempotent.
- **HTTP-header CSP overriding the meta tag** — the header wins; edit the header.

## Worked example — build-step injection (this repo)

`tools/build_seo.py` owns the `<head>` metadata **and the CSP**, so GA is wired
in there rather than pasted into pages (a paste would be CSP-blocked and
overwritten on the next build). The pattern generalises to any post-processor:

- A config constant `GA_MEASUREMENT_ID = "G-XXXXXXXXXX"` (empty = OFF) and
  `GA_ON = bool(GA_MEASUREMENT_ID.strip())`.
- `compute_csp()` appends the §3 sources to `img/script/connect` when `GA_ON`,
  so every rebuilt page's CSP allows Google.
- `analytics_block()` emits the §1 snippet between `<!-- analytics:start -->` /
  `<!-- analytics:end -->` markers; the injector inserts/updates/removes that
  block in each `<head>` idempotently, and skips excluded pages (e.g.
  `admin.html`).
- Run `python3 tools/build_seo.py` to apply to all pages, then
  `python3 tools/verify.py`. Turn analytics off by blanking the ID and
  rebuilding — the block and CSP entries are removed automatically.

To reuse this skill on a **different** website, keep §§1–5; only §"Worked
example" is repo-specific. If the other site has no build step, use the static
multi-page approach in §2 and hand-edit its CSP per §3.

## Turning it off

Blank the Measurement ID (or remove the snippet from the template) and rebuild;
on a hand-edited site, delete the snippet from every `<head>` and drop the
Google hosts from the CSP.

## Non-GA alternatives (mention if the user prefers privacy-first)

- **Plausible / Fathom** — cookieless, no consent banner needed, tiny script;
  CSP: allow the script host and its `connect-src` (e.g. `plausible.io`).
- **Matomo** — self-hostable, you own the data; can be consent-gated. CSP: allow
  your Matomo origin in `script/img/connect-src`.

Same three-part job in every case: tag on every page, CSP allowances, verify.
