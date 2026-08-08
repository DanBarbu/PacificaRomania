#!/usr/bin/env python3
"""
manage_images.py — admin helper for images in PacificaRomania journal/collection pages.

It does three things well, so the site owner never has to hand-edit an <img>:

  * optimize  — resize any photo to the site's folio convention (progressive JPEG,
                ~1500px long edge) and drop it in assets/images/folio/.
  * replace   — swap the photo behind an existing figure IN PLACE. Because the
                filename stays the same, every page (and the essay's Open Graph
                image) keeps working; the tool also fixes the <img> width/height
                so the new aspect ratio doesn't distort the layout.
  * add       — insert a new bilingual <figure class="essay-figure"> (image +
                EN/RO caption) into a journal essay, right after a piece of text
                you point at.

Each command finishes by running tools/build_seo.py so sitemap/head tags stay in
sync (pass --no-build to skip). Always run tools/verify.py before committing.

Examples
--------
  # Replace the photo behind an existing folio image (keeps the same filename):
  python3 tools/manage_images.py replace lupul-rockhole-embassy-canberra.jpg /path/new.jpg

  # Just optimize a photo into the folio directory under a chosen name:
  python3 tools/manage_images.py optimize /path/photo.jpg naga-morsarang-plate5.jpg

  # Add a new captioned figure to an essay, after the paragraph that contains a phrase:
  python3 tools/manage_images.py add tiger-in-chains /path/detail.jpg \
      --name tiger-in-chains-detail.jpg \
      --after "the tiger in chains" \
      --alt "Detail of the carved tiger" \
      --cap-en "A detail of the tiger's chain." \
      --cap-ro "Un detaliu al lanțului tigrului."
"""
import argparse
import os
import re
import subprocess
import sys

try:
    from PIL import Image, ImageOps
except ImportError:
    sys.exit("Pillow is required: pip install Pillow")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FOLIO = os.path.join(ROOT, "assets", "images", "folio")
LONG_EDGE = 1500
QUALITY = 86


def optimize_into(src, folio_name, long_edge=LONG_EDGE, quality=QUALITY):
    """Resize/optimize `src` into assets/images/folio/<folio_name>. Returns (w, h)."""
    if not os.path.isfile(src):
        sys.exit(f"Source image not found: {src}")
    folio_name = os.path.basename(folio_name)
    if not folio_name.lower().endswith((".jpg", ".jpeg")):
        folio_name += ".jpg"
    im = Image.open(src)
    im = ImageOps.exif_transpose(im).convert("RGB")
    w, h = im.size
    if max(w, h) > long_edge:
        if w >= h:
            im = im.resize((long_edge, round(h * long_edge / w)), Image.LANCZOS)
        else:
            im = im.resize((round(w * long_edge / h), long_edge), Image.LANCZOS)
    os.makedirs(FOLIO, exist_ok=True)
    dst = os.path.join(FOLIO, folio_name)
    im.save(dst, "JPEG", quality=quality, optimize=True, progressive=True)
    print(f"  wrote {os.path.relpath(dst, ROOT)}  ({im.size[0]}x{im.size[1]})")
    return im.size


def iter_html():
    for base in (ROOT, os.path.join(ROOT, "journal"), os.path.join(ROOT, "collection")):
        if not os.path.isdir(base):
            continue
        for f in sorted(os.listdir(base)):
            if f.endswith(".html"):
                yield os.path.join(base, f)


def fix_dimensions(folio_name, w, h):
    """Update width/height on every <img> that references folio/<folio_name>."""
    folio_name = os.path.basename(folio_name)
    changed = []
    img_re = re.compile(r"<img\b[^>]*folio/" + re.escape(folio_name) + r"[^>]*>")
    for path in iter_html():
        s = open(path, encoding="utf-8").read()
        if "folio/" + folio_name not in s:
            continue
        new = s

        def _fix(m):
            tag = m.group(0)
            if 'width="' in tag:
                tag = re.sub(r'width="\d+"', f'width="{w}"', tag)
            if 'height="' in tag:
                tag = re.sub(r'height="\d+"', f'height="{h}"', tag)
            return tag

        new = img_re.sub(_fix, new)
        if new != s:
            open(path, "w", encoding="utf-8").write(new)
            changed.append(os.path.relpath(path, ROOT))
    for c in changed:
        print(f"  updated dimensions in {c}")
    return changed


def run_build_seo():
    print("  running tools/build_seo.py ...")
    subprocess.run([sys.executable, os.path.join(ROOT, "tools", "build_seo.py")],
                   cwd=ROOT, check=True)


def cmd_optimize(a):
    optimize_into(a.src, a.name, a.long, a.quality)
    if not a.no_build:
        run_build_seo()


def cmd_replace(a):
    folio_name = os.path.basename(a.folio_name)
    target = os.path.join(FOLIO, folio_name)
    if not os.path.isfile(target):
        sys.exit(f"No existing folio image named {folio_name}. Use `optimize` to add a new one, "
                 f"or check the filename (it must be the current <img src> basename).")
    print(f"Replacing {folio_name} in place:")
    w, h = optimize_into(a.src, folio_name, a.long, a.quality)
    fix_dimensions(folio_name, w, h)
    if not a.no_build:
        run_build_seo()
    print("Done. Review the caption (people/positions may have changed), run tools/verify.py, then commit.")


def cmd_add(a):
    slug = a.slug[:-5] if a.slug.endswith(".html") else a.slug
    page = os.path.join(ROOT, "journal", slug + ".html")
    if not os.path.isfile(page):
        sys.exit(f"Essay not found: journal/{slug}.html")
    folio_name = os.path.basename(a.name or (slug + "-figure.jpg"))
    print(f"Adding a figure to journal/{slug}.html:")
    w, h = optimize_into(a.src, folio_name, a.long, a.quality)
    s = open(page, encoding="utf-8").read()
    if a.after not in s:
        sys.exit(f"Anchor text not found in the essay: {a.after!r}. Pass --after with an exact phrase "
                 f"from the paragraph you want the figure to follow.")
    # Insert after the end of the line that contains the anchor text.
    idx = s.index(a.after)
    line_end = s.index("\n", idx)
    alt = a.alt or ""
    fig = (
        f'\n  <figure class="essay-figure"><img src="../assets/images/folio/{folio_name}" '
        f'alt="{alt}" width="{w}" height="{h}" loading="lazy">'
        f'<figcaption><span data-l="en">{a.cap_en}</span>'
        f'<span data-l="ro">{a.cap_ro}</span></figcaption></figure>'
    )
    s = s[:line_end + 1] + fig + s[line_end + 1:]
    open(page, "w", encoding="utf-8").write(s)
    print(f"  inserted figure after the line containing {a.after!r}")
    if not a.no_build:
        run_build_seo()
    print("Done. Run tools/verify.py, then commit.")


def main():
    p = argparse.ArgumentParser(description="Manage images in PacificaRomania journal/collection pages.")
    p.add_argument("--long", type=int, default=LONG_EDGE, help=f"long-edge px (default {LONG_EDGE})")
    p.add_argument("--quality", type=int, default=QUALITY, help=f"JPEG quality (default {QUALITY})")
    p.add_argument("--no-build", action="store_true", help="skip running build_seo.py")
    sub = p.add_subparsers(dest="cmd", required=True)

    o = sub.add_parser("optimize", help="optimize a photo into assets/images/folio/")
    o.add_argument("src")
    o.add_argument("name", help="destination folio filename, e.g. my-photo.jpg")
    o.set_defaults(func=cmd_optimize)

    r = sub.add_parser("replace", help="replace an existing folio image in place (keeps the filename)")
    r.add_argument("folio_name", help="current folio filename / <img src> basename, e.g. embassy.jpg")
    r.add_argument("src", help="path to the new photo")
    r.set_defaults(func=cmd_replace)

    ad = sub.add_parser("add", help="add a new bilingual figure to a journal essay")
    ad.add_argument("slug", help="essay slug, e.g. tiger-in-chains")
    ad.add_argument("src", help="path to the new photo")
    ad.add_argument("--name", help="folio filename to save as (default <slug>-figure.jpg)")
    ad.add_argument("--after", required=True, help="exact text the figure should follow")
    ad.add_argument("--alt", default="", help="img alt text")
    ad.add_argument("--cap-en", required=True, help="English caption")
    ad.add_argument("--cap-ro", required=True, help="Romanian caption")
    ad.set_defaults(func=cmd_add)

    a = p.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
