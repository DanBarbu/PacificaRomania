# Traffic analytics setup — Matomo (self-hosted, consent-gated)

This site uses **Matomo** (free, open-source, GitHub:
[matomo-org/matomo](https://github.com/matomo-org/matomo)) — the closest
self-hosted equivalent of Google Analytics. It gives a per-visit log with
**IP-based geolocation (country/region/city)**, referrers, real-time visitors,
and **ad-campaign (UTM) reports**.

Because Matomo processes individual IP addresses, EU law (GDPR + ePrivacy)
requires **opt-in consent**. The site already ships a compliant consent banner
(`assets/js/analytics.js`) that loads Matomo **only after the visitor accepts**,
treats Do-Not-Track as a refusal, and lets the visitor withdraw consent. The
tracking tag and the Content-Security-Policy are managed by `tools/build_seo.py`
and stay **OFF until you paste a Site ID**.

> Matomo the software is free. Hosting needs a PHP + MySQL server. To keep it
> genuinely free, use an always-free VM (below). Host it **in the EU** to keep
> data-protection simple.

---

## 1. Deploy Matomo (free, EU-hosted)

**Recommended free path — Oracle Cloud "Always Free" VM + Docker**
1. Create an [Oracle Cloud Always Free](https://www.oracle.com/cloud/free/) VM
   in an **EU region** (e.g. Frankfurt). The Ampere/AMD micro instances are free
   for life.
2. Install Docker, then run Matomo + MariaDB (official images):
   ```bash
   docker network create matomo
   docker run -d --name db --network matomo -e MARIADB_DATABASE=matomo \
     -e MARIADB_USER=matomo -e MARIADB_PASSWORD=CHANGE_ME \
     -e MARIADB_ROOT_PASSWORD=CHANGE_ME_ROOT -v db:/var/lib/mysql mariadb:11
   docker run -d --name matomo --network matomo -p 80:80 \
     -v matomo:/var/www/html matomo:latest
   ```
3. Put a TLS reverse proxy in front (Caddy or nginx) so it serves HTTPS.

Alternatives: any low-cost EU VPS (Hetzner ~€4/mo), or a PaaS that offers
PHP + MySQL. Avoid free PHP hosts that forbid analytics/cron.

## 2. Point the subdomain at it

1. In your DNS (Namecheap, `pacificaromania.space`) add an **A record**:
   - Host `stats` → your VM's public IP  (or a CNAME to your proxy host)
2. Issue a TLS certificate for `stats.pacificaromania.space` (Caddy does this
   automatically; or use certbot).
3. Confirm `https://stats.pacificaromania.space` shows Matomo.

## 3. Install + privacy configuration (required for EU compliance)

1. Finish the Matomo web installer; add website `pacificaromania.space`.
2. **Administration → Privacy → Anonymize data**:
   - Anonymize visitors' IP: **at least 2 bytes** (country/region geolocation
     still works; this reduces the data-protection footprint).
   - Enable **"also anonymise before geolocation"** only if city-level is not
     needed. For country-by-user, 2-byte anonymisation keeps country accurate.
   - Enable **support for Do Not Track**.
3. **Privacy → Anonymize/Delete old visitor logs**: schedule deletion of raw
   logs after **14 months** (matches the Privacy Policy).
4. **Geolocation**: install the free DB-IP / GeoLite2 database so country/region
   is resolved.
5. Change the default `admin` password.

> Consent is handled client-side by this site (`requireConsent`), so Matomo will
> not track or set cookies until the visitor clicks **Accept**.

## 4. Copy the Site ID and switch analytics ON

1. In Matomo, the website's **Site ID** is a number (e.g. `1`).
2. Edit `tools/build_seo.py`:
   ```python
   MATOMO_URL     = "https://stats.pacificaromania.space/"   # keep the slash
   MATOMO_SITE_ID = "1"                                       # your Site ID
   ```
3. From the repo root:
   ```bash
   python3 tools/build_seo.py    # injects the consent-gated tag + widens CSP
   python3 tools/verify.py       # sanity check
   git add -A && git commit -m "Enable Matomo analytics" && git push origin main
   ```
4. Visit the site → the consent banner appears; after **Accept**, live visits
   show up in Matomo.

To turn analytics **off**: blank `MATOMO_SITE_ID`, rerun `build_seo.py` (removes
the tag, re-tightens the CSP, drops the banner), and push.

---

## Ad campaigns (UTM)

Tag every ad link so Matomo's **Acquisition → Campaigns** report attributes it.
Build links with the UTM builder on **`/admin.html`**, or by hand:

```
https://pacificaromania.space/?utm_source=facebook&utm_medium=cpc&utm_campaign=spring_exhibition
```

Matomo reads the standard `utm_*` parameters out of the box (lowercase, keep
`source`/`medium`/`campaign` consistent).

## Why Matomo (vs. the alternatives)

| Tool | Per-visitor IP→geo | Free hosting | EU-consent needed |
|------|:---:|:---:|:---:|
| **Matomo** (chosen) | ✅ country/region/city | self-host (free VM) | yes — handled by our banner |
| Umami | country only, IP hashed | free tier | no (cookieless) |
| Cloudflare Web Analytics | aggregate only | ✅ | no |
| Plausible / GoatCounter | aggregate/country | self-host / free tier | no |

See `docs/eu-compliance.md` for the full legal checklist.
