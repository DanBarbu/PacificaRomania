# AI Visibility Phase 3 — external entity work (needs your accounts)

Phases 1–2 (site structure, JSON-LD, llms.txt, FAQ) are shipped. Phase 3 is the
off-site work that AI systems weight most heavily for *recommendation
confidence*. It's free, but each step needs an account only you can create.
This is the ready-to-use kit; work top to bottom.

---

## 1. Wikidata item — highest-leverage free move

A Wikidata item feeds Google's Knowledge Graph and is a primary grounding
source for AI assistants. Anyone can create one free.

**Steps**
1. Create a free account at <https://www.wikidata.org> and log in.
2. Left menu → **Create a new Item**.
3. Fill **Label / Description / Aliases**, then add the **Statements** below.
   For each statement, Wikidata will autocomplete the property (P…) and, where
   the value is another item, its Q-id. The confident Q-ids are given; for the
   two marked "search", pick the top autocomplete match.

**Label (en):** `PacificaRomania`
**Label (ro):** `PacificaRomania`
**Description (en):** `art collection of Pacific and Island Southeast Asian art`
**Description (ro):** `colecție de artă din Pacific și Asia de Sud-Est insulară`
**Also known as (en):** `PacificaRomania Collection`

**Statements**

| Property | Value |
|---|---|
| **instance of** (P31) | `art collection` — search (fallback: `private collection`, Q768717) |
| **country** (P17) | `Romania` (Q218) |
| **official website** (P856) | `https://pacificaromania.space` |
| **inception** (P571) | `2019` |
| **operator** (P137) | `AlgorithmIntelligence SRL` — search; if no item exists, skip or add as a qualifier string |
| **main subject** (P921) | `Oceanian art` — search; add `Pacific art`, `Aboriginal Australian art` as extra values |
| **has part(s) / relates** — via P921 also add | `Mircea Eliade` (Q41590), `Constantin Brâncuși` (Q153048) |
| **described at URL** (P973) | `https://pacificaromania.space/about.html` |

Optional but good: add a statement **significant event** (P793) = `exhibition`,
with qualifiers **location** = Embassy of Romania, Canberra and **point in
time** = 2019–2020.

4. **Save.** Then, so search engines connect the dots both ways, keep the
   homepage's `sameAs` (already live in the JSON-LD via `build_seo.py`) — once
   the item exists you can add its Q-id to the `ORG["sameAs"]` list in
   `tools/build_seo.py` (e.g. `"https://www.wikidata.org/wiki/Q…"`), rerun the
   tool, and push.

## 2. Google Search Console (URL-prefix property)

1. <https://search.google.com/search-console> → **Add property** →
   **URL prefix** → `https://pacificaromania.space/`.
2. Choose the **HTML tag** verification method. Copy the token — the value
   inside `content="…"` of the `google-site-verification` meta.
3. Paste it into `tools/build_seo.py`:
   ```python
   GSC_VERIFICATION = "paste-token-here"
   ```
4. `python3 tools/build_seo.py` (injects the tag on the homepage only),
   `python3 tools/verify.py`, then commit & push. After the deploy, click
   **Verify** in Search Console.
5. In Search Console → **Sitemaps**, submit `sitemap.xml`.

## 3. Bing Webmaster Tools (grounds Copilot & ChatGPT search)

1. <https://www.bing.com/webmasters> → add site `https://pacificaromania.space/`.
   You can **import from Google Search Console** (fastest) or verify separately.
2. If verifying separately, use the **meta tag** method and paste its token:
   ```python
   BING_VERIFICATION = "paste-token-here"
   ```
   then rerun `build_seo.py`, commit & push, and click Verify.
3. Submit `sitemap.xml` under **Sitemaps**.

> Both tokens are OFF by default. Empty = no tag injected; the homepage is
> unchanged. Setting either one adds a single `<meta>` to the homepage `<head>`
> on the next build — nothing else moves.

## 4. Directories & citations (spread over time, optional)

Each independent mention raises AI recommendation confidence:
- Romanian cultural-institute / diaspora cultural listings.
- Oceanic / tribal-art and Pacific-studies resource pages.
- The Facebook page kept consistent with the site (same name + description).

---

## After Phase 3 — the monthly routine (from the plan §7)
Ask ChatGPT / Perplexity / Gemini / Copilot the fixed test prompts, check
Matomo for AI referrers, review Search Console/Bing queries, and scan for new AI
crawler user-agents. 30 minutes/month, $0.
