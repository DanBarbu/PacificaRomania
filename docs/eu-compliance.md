# EU digital-compliance checklist — pacificaromania.space

Scope: a **non-commercial, static** cultural/curatorial website (GitHub Pages),
bilingual EN/RO, aimed at an EU (incl. Romanian) audience, using **self-hosted
Matomo** analytics behind opt-in consent. This maps the relevant EU legislation
to what the site already does (✅ built) and what **you, the operator, must do**
operationally (☐ action). It is guidance, not legal advice — for anything
consequential, confirm with a qualified adviser.

---

## 1. GDPR — Regulation (EU) 2016/679 (+ Romanian Law 190/2018)

| Requirement | Status |
|---|---|
| Privacy notice with Art. 13/14 disclosures (identity, purposes, legal bases, retention, recipients, transfers, rights, complaint route) | ✅ `privacy.html` (EN/RO) |
| Lawful basis for each processing (analytics = consent; email = legitimate interest/contract; security logs = legitimate interest) | ✅ documented |
| Consent that is freely given, specific, informed, unambiguous, and as easy to withdraw as to give | ✅ opt-in banner, "Reject" equal to "Accept", withdraw via "Cookie settings" |
| Data minimisation & privacy by design/default | ✅ analytics OFF by default; IP anonymisation; no ad trackers/profiling |
| Data-subject rights channel (access, erasure, objection, portability…) | ✅ email route in policy · ☐ **you must actually honour requests within 1 month** |
| International-transfer safeguards (GitHub = US) | ✅ SCC/adequacy noted in policy · ☐ keep Matomo in the EU |
| Records of processing (Art. 30) | ☐ **keep a short internal record** (what data, why, retention) — template below |
| Breach procedure (Art. 33/34, notify ANSPDCP within 72h) | ☐ **know the steps** (see §7) |
| DPO | Not required at this scale (no large-scale/special-category monitoring) |
| Name/address of controller in the notice | ✅ AlgorithmIntelligence SRL, Bucharest — set in `privacy.html` and `legal.html` |

## 2. ePrivacy Directive 2002/58/EC (+ Romanian Law 506/2004) — "cookie law"

| Requirement | Status |
|---|---|
| Prior opt-in consent before non-essential cookies/tracking | ✅ Matomo loads only after Accept |
| No pre-ticked boxes; reject as easy as accept; granular & informed | ✅ banner design |
| Essential cookies (language, consent choice) may run without consent | ✅ only `pr-lang`, `pr-consent` (local storage) |
| Cookie information (names, purpose, duration) | ✅ table in `privacy.html` |
| Withdraw consent anytime | ✅ persistent "Cookie settings" control |

## 3. Cybersecurity — GDPR Art. 32 "security of processing"

| Measure | Status |
|---|---|
| HTTPS everywhere | ✅ GitHub Pages TLS + `upgrade-insecure-requests`; ☐ keep "Enforce HTTPS" on |
| Content-Security-Policy (no external scripts except the Matomo host) | ✅ per-page CSP via `build_seo.py` |
| Referrer-Policy, `object-src 'none'`, `base-uri 'self'`, `frame-src 'none'` | ✅ CSP meta |
| No third-party/CDN JS supply chain (all first-party vanilla JS) | ✅ |
| No secrets in the public repo | ✅ verified; `.gitignore` in place |
| `security.txt` disclosure contact | ✅ `/.well-known/security.txt` (keep `Expires` future) |
| Response security headers Pages cannot set (HSTS, X-Content-Type-Options, X-Frame-Options, Permissions-Policy) | ☐ **set these on the Matomo host** (proxy config in §6); GitHub sends HSTS for the Pages domain |
| Matomo hardening | ☐ strong admin password, keep Matomo updated, restrict admin login, DB not publicly exposed |

## 4. NIS2 Directive (EU) 2022/2555

Out of scope — NIS2 targets medium/large "essential/important" entities in
listed sectors. A small cultural site is not in scope. GDPR Art. 32 (above)
still governs security. *No action beyond §3.*

## 5. Digital Services Act (EU) 2022/2065

Largely out of scope — the DSA targets intermediaries/hosting/marketplaces with
user-generated content. This is a static publisher with no user accounts,
uploads, comments, or marketplace. Clear provider **contact details are
provided** (`legal.html`), which is the relevant good-practice item. *No further
action.*

## 6. eCommerce Directive 2000/31/EC — provider identification ("Impressum")

| Requirement | Status |
|---|---|
| Name, geographic address, and quick contact (email) of the provider | ✅ `legal.html` · ☐ **fill name/address placeholder** |
| Identify the hosting provider | ✅ GitHub, Inc. named |

**Recommended headers to add on the Matomo host** (nginx/Caddy in front of
Matomo — Pages can't set these, but your own subdomain can):
```
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Content-Type-Options: nosniff
X-Frame-Options: SAMEORIGIN
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), microphone=(), camera=()
```

## 7. Accessibility — European Accessibility Act (Dir. 2019/882) / WCAG

The EAA (in force June 2025) binds certain private services (e-commerce,
banking, transport, e-books). A non-commercial cultural site is most likely
**not in scope**, but WCAG 2.1 AA is good practice and partly done:
- ✅ semantic HTML, alt text, keyboard-operable controls, colour contrast,
  responsive/zoomable layout, `lang` attributes, bilingual content.
- ☐ Optional: run a Lighthouse/axe accessibility pass and fix any AA gaps.

## 8. Copyright — DSM Directive 2019/790

- ☐ Ensure you hold rights or a valid basis (educational/cultural use with
  attribution) for the catalogue photographs; `legal.html` states attribution
  and non-commercial cultural purpose. Keep source records.

---

## Your operational to-do (the ☐ items, condensed)

1. **Controller identity** — ✅ done (AlgorithmIntelligence SRL, Casa14,
   14–18 Prevederii St, Sector 3, Bucharest). Update if it ever changes.
2. **Host Matomo in the EU**, enable IP anonymisation + 14-month log deletion +
   Do-Not-Track (see `docs/analytics-setup.md` §3).
3. **Add the security headers** (§6) on the Matomo subdomain; strong admin
   password; keep Matomo updated.
4. **Keep a one-page Record of Processing** (below).
5. **Honour data-subject/erasure requests** within one month via the policy
   email.
6. **Breach plan**: if personal data is exposed, assess risk and, if likely
   risky, notify **ANSPDCP** (dataprotection.ro) within 72 hours and affected
   people without undue delay.
7. Keep `.well-known/security.txt` `Expires` in the future.

### Record of Processing (Art. 30) — minimal template
```
Controller: AlgorithmIntelligence SRL, Casa14, 14-18 Prevederii St, Sector 3, Bucharest, Romania, danbarbu22@gmail.com
Processing 1: Website audience analytics
  Data: pages, referrer, anonymised IP, approx. country/region, device
  Purpose: understand traffic · Legal basis: consent
  Retention: 14 months · Processor: self-hosted Matomo (EU)
Processing 2: Email correspondence
  Data: email address, message · Purpose: reply
  Legal basis: legitimate interest/contract · Retention: until resolved
Processing 3: Hosting/security logs
  Data: IP, request metadata · Purpose: delivery & security
  Legal basis: legitimate interest · Processor: GitHub Pages (US, SCCs)
```
