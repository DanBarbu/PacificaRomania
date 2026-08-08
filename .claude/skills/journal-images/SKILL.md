---
name: journal-images
description: >-
  Format, replace, or add images in PacificaRomania (pacificaromania.space)
  journal essays and collection pages without hand-editing HTML. Use this when
  the owner wants to swap the photo behind a figure (e.g. "replace the embassy
  photo with this one"), add a new captioned image to an essay, or optimize a
  photo into the site's folio convention. Wraps tools/manage_images.py and keeps
  SEO/Open-Graph tags, image dimensions, and the bilingual caption in sync.
---

# PacificaRomania — Journal Images Skill

A small, safe way to change images on the site. The heavy lifting is done by
**`tools/manage_images.py`**, so you never hand-edit an `<img>` tag, guess a
size, or forget to rebuild SEO. Everything lands in `assets/images/folio/` and
is optimized to the house convention (progressive JPEG, ~1500 px long edge).

Only publish images that are **free / openly licensed or owned by the
collection** — the same rule as the rest of the site. Never add a copyrighted
image (film stills, stock, publisher covers).

## The three commands

Run from the repository root. Each command optimizes the photo and then runs
`tools/build_seo.py` automatically (add `--no-build` to skip).

### 1. Replace a photo in place (most common)
Swap the picture behind an **existing** figure while keeping its filename, so
every reference — the essay, any other page, and the Open Graph share image —
keeps working. The tool also rewrites the `<img>` `width`/`height` to the new
photo's aspect ratio so the layout doesn't distort.

```bash
python3 tools/manage_images.py replace <folio-filename> <path-to-new-photo>
```

`<folio-filename>` is the current `<img src>` basename. Find it by opening the
essay and reading the `src`, e.g. `…/folio/lupul-rockhole-embassy-canberra.jpg`
→ pass `lupul-rockhole-embassy-canberra.jpg`. This works for **lead (hero)
images and body figures alike** — both live in `folio/`.

Example (the request "replace the Governor-General embassy photo with this one"):
```bash
python3 tools/manage_images.py replace lupul-rockhole-embassy-canberra.jpg /path/new-embassy.jpg
```

> After a replace, **re-read the figure's caption**. Filenames stay the same but
> the *content* changed — if the caption names people or positions ("… on the
> left … on the right"), confirm they still match the new photo and edit the
> caption text by hand if not.

### 2. Add a new captioned figure to an essay
Insert a bilingual `<figure class="essay-figure">` (image + EN/RO caption)
directly after a phrase you point at.

```bash
python3 tools/manage_images.py add <essay-slug> <path-to-photo> \
    --name <folio-filename.jpg> \
    --after "an exact phrase from the paragraph it should follow" \
    --alt  "meaningful alt text" \
    --cap-en "English caption." \
    --cap-ro "Romanian caption."
```

The figure is placed right after the line containing `--after`. Keep the RO
caption in the academic-curatorial register of the other essays.

### 3. Just optimize a photo into the folio directory
For when you only need the file prepared (e.g. a new lead image you'll wire up
yourself, or a collection-page card image).

```bash
python3 tools/manage_images.py optimize <path-to-photo> <folio-filename.jpg>
```

Options for any command: `--long <px>` (default 1500), `--quality <n>` (default 86),
`--no-build`.

## Always finish with

```bash
python3 tools/verify.py     # must print: No broken links or malformed tags. OK.
git add -A
git commit -m "<clear description of the image change>"
git push origin main        # GitHub Pages redeploys automatically
```

## Notes & gotchas

- **Replace keeps the filename on purpose.** That is what makes it safe: no
  other page, and no `ESSAY_IMG` mapping in `build_seo.py`, needs touching. To
  introduce a genuinely new image with a new name, use `optimize` (or `add`).
- **Dimensions.** `replace` and `add` write correct `width`/`height`. If you ever
  hand-edit an `<img>`, set both so the browser reserves the right space.
- **Alt text.** Every meaningful image needs a real `alt`; decorative thumbnails
  may use `alt=""`.
- **Bilingual captions.** Body figures carry EN + RO in `<figcaption>`; `add`
  writes both. Never leave a caption English-only.
- **Third-party embeds** (Facebook posts/videos, YouTube, Kiri 3D) are a
  different mechanism — see `site-admin` and `embed_model.py` — not this skill.
- If a change "doesn't show" on the live site, it is almost always browser cache
  (hard-refresh) — or, if nothing new appears at all, the GitHub Pages custom
  domain needs re-asserting in the repo's Settings → Pages.
