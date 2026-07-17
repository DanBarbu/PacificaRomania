# AI Visibility (AEO/GEO) Plan — pacificaromania.space

**Goal:** make PacificaRomania the site that AI assistants (ChatGPT, Gemini,
Perplexity, Copilot, Claude) find, read, and cite when people ask about
Pacific/Oceanic art collections, Eliade and Brâncuși comparative readings, or
Romanian cultural diplomacy in the Pacific — executed **in-house and free**,
the same way the site's SEO is done.

This plan decodes a commercial "AI visibility" agency pitch (upserv.ai deck:
$1,000–$10,000 setup + $150–500/month) into its underlying technical work,
audits what this site already has, and lays out a phased in-house execution
with effort estimates.

---

## 1. What the brochure actually sells, decoded

The deck's three products map to well-understood practices:

| Brochure language | What it technically means | In-house feasibility |
|---|---|---|
| "AI-ready website — structured so every AI platform can read, understand, and cite you" | Crawlable clean HTML, structured data (JSON-LD), entity clarity, answer-shaped copy, AI-crawler access in robots.txt | ✅ Fully in-house; mostly **already done** here |
| "AI chatbot trained on your business" | An embedded RAG chatbot widget | ⚠️ Possible but low value for a cultural archive; conflicts with our strict CSP (see §6) |
| "Monthly optimization" | Periodic re-testing of AI answers, content updates, schema upkeep | ✅ A 30-minute monthly routine (see §7) |

Marketing claims to discount: "93% of businesses are invisible to AI" is an
unsourced scare figure, and the deck is a template (placeholders like
"[your service] near me"). The *underlying* practices are real; the price is
for labour you can do yourself.

**Cost comparison:** upserv "Basic" = $1,000 + $150/mo ≈ **$2,800/first year**.
The equivalent scope below = **$0** and roughly **1–2 days of one-off work plus
30 min/month**, using Claude Code as the in-house executor — the same model
already used for the site's SEO, security, and compliance work.

## 2. Where the site already stands (audit, July 2026)

Already in place — this covers most of the "Basic" tier:

- ✅ **All content in raw HTML** — no JavaScript rendering required. This is the
  single most important AI-crawler property (most AI bots do not execute JS).
- ✅ robots.txt allows all crawlers (`User-agent: *` / `Allow: /`) + sitemap.
- ✅ sitemap.xml, canonical URLs, unique titles/meta descriptions on all pages.
- ✅ Open Graph + Twitter cards sitewide; JSON-LD (WebSite + Organization) on
  the homepage.
- ✅ Semantic structure: sequential headings, alt text, breadcrumbs, internal
  cross-links (essays ↔ regions), bilingual EN/RO content.
- ✅ Definitional, answer-shaped copy: "PacificaRomania is a cultural art
  collection…" (exactly the sentence pattern AI answers lift).
- ✅ HTTPS, fast static pages, no third-party scripts.

Gaps (the actual work):

- ❌ No JSON-LD beyond the homepage (essays, regions, breadcrumbs unstructured).
- ❌ No explicit per-bot robots.txt policy (works, but implicit).
- ❌ No llms.txt.
- ❌ Not registered in Google Search Console / Bing Webmaster Tools.
- ❌ No external entity anchors (Wikidata, directories) — AI confidence comes
  heavily from third-party corroboration.
- ❌ No FAQ/Q&A content block.
- ❌ No monitoring of what AI engines currently say about the collection.

## 3. Phase 1 — Technical substrate (½ day, $0)

1. **Explicit AI-crawler policy in robots.txt.** Current implicit allow-all
   works, but naming the bots documents intent and survives future edits.
   Allow (they index/cite — this is the visibility channel):
   `OAI-SearchBot`, `ChatGPT-User`, `GPTBot`, `ClaudeBot`, `Claude-SearchBot`,
   `PerplexityBot`, `Perplexity-User`, `Google-Extended`, `Bingbot`,
   `Amazonbot`, `Applebot-Extended`, `Meta-ExternalAgent`, `CCBot`.
   *Policy decision:* for a cultural-diplomacy site, being included in training
   data and answer indexes is the mission — allow everything. (A commercial
   site might block training-only bots; we should not.) New AI bots appear a
   few times a year — reviewed in the §7 routine.
2. **Structured data expansion** (via `tools/build_seo.py`, same pattern as OG):
   - `Article` JSON-LD on all 10 essays (headline, image, inLanguage en+ro,
     author/publisher = PacificaRomania Collection / AlgorithmIntelligence SRL).
   - `CollectionPage` JSON-LD on the five region pages.
   - `BreadcrumbList` JSON-LD mirroring the visible breadcrumbs.
   - `sameAs` on the Organization (Facebook page; Wikidata once §5 is done).
   - Persons as entities: mention Mircea Eliade and Constantin Brâncuși with
     `about`/`mentions` referencing their Wikipedia/Wikidata IDs — this ties
     the site into knowledge graphs AI systems already trust.
3. **llms.txt** — a markdown index of the site for AI agents. Honest research
   note: adoption is ~8.7% of top-1,000 sites (June 2026) and major AI search
   crawlers still mostly skip it; studies show little direct traffic effect.
   But it costs ~30 minutes, is fetched by agent tooling (Claude Code, Cursor
   etc.), and is the standard "machine-readable front door." Cheap bet: do it,
   expect nothing from it short-term.

## 4. Phase 2 — Answer-shaped content (½–1 day, $0)

AI engines quote passages that *look like answers*. Additions:

1. **FAQ section on the About page** (+ `FAQPage` JSON-LD), bilingual. Target
   the questions people actually ask an assistant:
   - What is PacificaRomania? · Where was the collection exhibited? · What
     regions does it cover? · How does it relate to Mircea Eliade and
     Constantin Brâncuși? · Can the collection be visited or contacted? · Who
     operates it? (AlgorithmIntelligence SRL, Bucharest)
2. **One-sentence definitional openers** on every region page (mostly done via
   the new intros) — first sentence should stand alone as a quotable answer.
3. **Stable factual block** in the footer or About: name, operator, city,
   contact — consistent entity facts everywhere (AI cross-checks consistency).

## 5. Phase 3 — External corroboration (2–4 hours spread over weeks, $0)

AI recommendation confidence is mostly *off-site*. Free, legitimate moves:

1. **Wikidata item** for the PacificaRomania collection (free, anyone can
   create; cite the Canberra exhibition). This is the single highest-leverage
   free action — Wikidata feeds Google's Knowledge Graph and most AI grounding.
2. **Google Search Console + Bing Webmaster Tools** registration (free
   accounts; Bing matters because Copilot and ChatGPT search ground on Bing's
   index). Submit the sitemap in both.
3. **Directories & citations:** Romanian cultural institute listings, Oceanic
   art / tribal-art directories, university Pacific-studies resource lists,
   the Embassy/DFAT cultural-diplomacy write-ups if any exist — each
   independent mention is a trust signal.
4. **Facebook page → site consistency:** same name, same description sentence.

## 6. The chatbot — honest recommendation: skip (for now)

What upserv charges $5,000+ for is an embedded RAG widget. For this site:

- **Value is low:** the site is an archive with ~24 pages of curated prose; a
  visitor's questions are answered by the essays themselves and the FAQ.
- **Cost is real:** a hosted widget (Chatbase etc. free tiers) injects
  third-party JS — which our CSP and privacy posture deliberately forbid; a
  self-hosted one needs a server + an LLM API key (no longer $0).
- **Free alternative with 90% of the value:** the llms.txt + clean HTML mean
  any visitor can paste the site into ChatGPT/Claude and get perfect answers
  already.

Revisit only if the collection starts selling/loaning works or handling volume
enquiries. (If wanted later: a small RAG service could ride on the same free
Oracle VM planned for Matomo, keeping cost at $0.)

## 7. Ongoing "monthly optimization" — the 30-minute in-house routine

The $150–500/month line item, replaced by a checklist (add to a monthly
calendar reminder, or ask Claude Code to run it):

1. Ask ChatGPT, Perplexity, Gemini and Copilot 3 fixed test prompts, e.g.:
   - "Romanian art collection of Pacific and Oceanic art"
   - "collections connecting Mircea Eliade and Brâncuși to Pacific art"
   - "PacificaRomania collection — what is it?"
   Log: are we mentioned? cited? linked? (keep a dated row per month).
2. Check Matomo (once live) for AI referrers: `chatgpt.com`, `perplexity.ai`,
   `gemini.google.com`, `copilot.microsoft.com` — this is the ground truth of
   AI-driven visits.
3. Search Console/Bing: any new queries containing "pacificaromania", Eliade,
   Brâncuși + Pacific terms.
4. Scan for newly announced AI crawler user-agents (2–4/yr); update robots.txt.
5. After adding any essay/page: rerun `tools/build_seo.py` (which will also
   maintain the JSON-LD once Phase 1 lands) and refresh llms.txt.

## 8. Resources & cost summary

| Item | Agency price | In-house |
|---|---|---|
| AI-ready structure (Phase 1) | in $1,000 setup | ~½ day, $0 |
| Answer content + FAQ (Phase 2) | in $1,000–5,000 | ~½–1 day, $0 |
| External entity work (Phase 3) | rarely included | 2–4 h, $0 |
| Chatbot | $5,000 + $300/mo | skipped (see §6) |
| Monthly optimization | $150–500/mo | 30 min/mo, $0 |
| **First-year total** | **$2,800–$16,000** | **≈2 days + 6 h/yr, $0** |

Skills needed: none beyond this repo's existing toolchain (Python generator,
Claude Code as executor, the `site-admin` skill). Free accounts to create:
Google Search Console, Bing Webmaster Tools, Wikidata.

## 9. Execution order (recommended)

1. Phase 1 (robots policy, JSON-LD expansion, llms.txt) — one session.
   **✅ SHIPPED 2026-07-17:** explicit AI-crawler allow-list in robots.txt;
   JSON-LD on 20 pages (WebSite+Organization with sameAs, Article on all 10
   essays, CollectionPage on regions, Blog on the journal index,
   About/ContactPage, BreadcrumbList everywhere; Eliade Q41590 and Brâncuși
   Q153048 entity anchors) — all generated and owned by `tools/build_seo.py`;
   `llms.txt` auto-generated from the live page list on every build.
2. Phase 2 (FAQ + FAQPage schema) — one session.
   **✅ SHIPPED 2026-07-17:** bilingual six-question FAQ on the About page
   (What is it / where exhibited / regions / Eliade & Brâncuși / how to visit &
   contact / who operates it), generated from a single `FAQ` list in
   `build_seo.py` that produces both the visible block and the `FAQPage`
   JSON-LD (validated, 6 questions). Region intros already supply the
   definitional openers; operator facts already sitewide (footer/legal/FAQ).
3. Phase 3 (Wikidata + webmaster registrations) — needs **your** accounts.
   **PREPARED:** ready-to-use kit in **`docs/phase3-external.md`** (a
   fill-in-the-blanks Wikidata item with confident Q-ids, plus Google Search
   Console and Bing steps). The site-side hook is wired: paste a token into
   `GSC_VERIFICATION` / `BING_VERIFICATION` in `tools/build_seo.py`, rerun it,
   and the verification `<meta>` is injected on the homepage (off until set).
4. Routine (§7) starts the month after Phases 1–2 ship.
