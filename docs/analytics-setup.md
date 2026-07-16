# Traffic analytics setup — Umami on `stats.pacificaromania.space`

This site uses **Umami** (free, open-source, GitHub:
[umami-software/umami](https://github.com/umami-software/umami)) for traffic
analytics: visitor counts, **countries/regions**, referrers, real-time activity,
and **ad-campaign (UTM)** tracking — a privacy-friendly, cookieless alternative
to Google Analytics. No consent banner is required because Umami stores no
personal data and no raw IP addresses.

The tracking snippet and the Content-Security-Policy are managed by
`tools/build_seo.py`. Analytics is **OFF until you paste a Website ID** — the
steps below turn it on.

---

## 1. Deploy Umami (free)

Umami is a Node app that needs a PostgreSQL (or MySQL) database. Two free paths:

**A. Vercel + free Postgres (recommended, no server to manage)**
1. Create a free Postgres database — e.g. [Neon](https://neon.tech) or
   [Supabase](https://supabase.com) — and copy its connection string.
2. Fork `umami-software/umami`, then "Import Project" into
   [Vercel](https://vercel.com) (free Hobby plan).
3. Set env vars in Vercel:
   - `DATABASE_URL` = your Postgres connection string
   - `APP_SECRET` = any long random string
4. Deploy. Umami is now live at a `*.vercel.app` URL.

**B. Render / Fly.io / Railway** — each has a free or near-free tier and a
one-click Umami/Docker deploy. Same two env vars.

Default login after first deploy: user `admin`, password `umami` — **change the
password immediately**.

## 2. Point the subdomain at it

So the dashboard lives on your own domain:

1. In your DNS (Namecheap, for `pacificaromania.space`) add a **CNAME**:
   - Host: `stats`
   - Target: your Vercel/Render host (e.g. `cname.vercel-dns.com` or the host
     your provider gives you)
2. In the host's dashboard, add `stats.pacificaromania.space` as a custom
   domain and let it issue the TLS certificate.
3. Confirm `https://stats.pacificaromania.space` loads the Umami login.

> The main site stays on GitHub Pages (apex + `www`). Only this one subdomain
> points at the analytics host.

## 3. Create the website + copy the ID

1. Log into `https://stats.pacificaromania.space`.
2. **Settings → Websites → Add website**: name `PacificaRomania`, domain
   `pacificaromania.space`.
3. Open it and copy the **Website ID** (a UUID).

## 4. Switch analytics ON in the repo

1. Edit `tools/build_seo.py` and set:
   ```python
   UMAMI_WEBSITE_ID = "paste-the-uuid-here"
   ```
2. From the repo root run:
   ```bash
   python3 tools/build_seo.py   # injects the tracker + widens CSP for stats.*
   python3 tools/verify.py      # sanity check
   git add -A && git commit -m "Enable Umami analytics" && git push origin main
   ```
3. Visit the site, then check the Umami dashboard — you should see live traffic.

To turn analytics **off** again, blank out `UMAMI_WEBSITE_ID`, rerun
`build_seo.py` (it strips the tag and re-tightens the CSP), and push.

---

## Ad campaigns (UTM)

Tag every ad/campaign link so Umami's **Campaigns** report can attribute
traffic. Use the builder at **`/admin.html`** (Ad-campaign link builder), or add
params by hand:

```
https://pacificaromania.space/?utm_source=facebook&utm_medium=cpc&utm_campaign=spring_exhibition
```

Conventions (keep lowercase and consistent):
- `utm_source` — where the ad runs: `facebook`, `instagram`, `newsletter`
- `utm_medium` — type: `cpc`, `social`, `email`, `banner`
- `utm_campaign` — the campaign name: `spring_exhibition`
- `utm_content` / `utm_term` — optional (ad variant / paid keyword)

## The admin hub — `/admin.html`

A small monitoring hub on your own domain: a button to the Umami dashboard plus
the UTM link builder. It is `noindex` and disallowed in `robots.txt`, but note
it is still a **public** URL (GitHub Pages has no login) — keep no secrets on it.

## Alternatives considered (all free / open-source)

| Tool | Note |
|------|------|
| **Umami** (chosen) | Cookieless, country + campaigns, self-host free, clean dashboard |
| Matomo | Full GA replacement with per-visitor IP→city log; needs PHP+MySQL and a GDPR consent banner |
| Cloudflare Web Analytics | Zero-setup, aggregate only, no per-user detail |
| GoatCounter | Minimal, free hosted, country + campaigns |
| PostHog | Free cloud tier, per-visitor geo + session replay, heavier |
