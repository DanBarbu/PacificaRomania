#!/usr/bin/env python3
"""Embed (or update) a Kiri Engine 3D-model viewer at the end of an essay.

Inserts the site's standard, responsive, lazy-loaded `.model-embed` block just
after the essay's `</article>`. Re-running with a new model URL updates the
existing block in place (idempotent). The per-page CSP frame-src is widened to
the Kiri Engine host by `build_seo.py`, which this script runs for you.

Usage:
    python3 tools/embed_model.py <essay> <model-url-or-id> [--label "…"] [--label-ro "…"] [--no-build]

  <essay>          slug (e.g. naga-morsarang) or path (journal/naga-morsarang.html)
  <model-url-or-id> full share URL or just the model id
  --label / --label-ro  object name used in the caption ("A 3D scan of <label>.")
  --no-build       skip running build_seo.py afterwards

Examples:
    python3 tools/embed_model.py naga-morsarang \\
        https://www.kiriengine.app/share/shareModel/8e150b0275c14b3e8138bac4d67adb95 \\
        --label "the naga morsarang" --label-ro "a vasului naga morsarang"
"""
import os
import re
import sys
import argparse
import subprocess

HOST = "https://www.kiriengine.app"
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def model_id(url_or_id):
    m = re.search(r"shareModel/([0-9A-Za-z]+)", url_or_id)
    if m:
        return m.group(1)
    tail = url_or_id.rstrip("/").split("/")[-1]
    if not re.fullmatch(r"[0-9A-Za-z]+", tail):
        sys.exit(f"Could not parse a model id from: {url_or_id}")
    return tail


def resolve_path(essay):
    if essay.endswith(".html"):
        p = essay if os.path.isabs(essay) else os.path.join(ROOT, essay)
    else:
        p = os.path.join(ROOT, "journal", essay + ".html")
    if not os.path.isfile(p):
        sys.exit(f"Essay not found: {p}")
    return p


def block(mid, label_en, label_ro):
    obj_en = f"A 3D scan of {label_en}." if label_en else "A 3D scan of the object in this essay."
    obj_ro = f"O scanare 3D {label_ro}." if label_ro else "O scanare 3D a obiectului din acest eseu."
    return f'''<figure class="model-embed wrap">
  <h3><span data-l="en">Explore in 3D</span><span data-l="ro">Explorează în 3D</span></h3>
  <div class="model-frame">
    <iframe
      src="{HOST}/share/shareModel/{mid}"
      title="3D model"
      loading="lazy"
      allow="autoplay; fullscreen; xr-spatial-tracking"
      allowvr="yes"
      allowfullscreen="true"
      mozallowfullscreen="true"
      webkitallowfullscreen="true"></iframe>
  </div>
  <figcaption><span data-l="en">{obj_en} Drag to rotate; scroll to zoom; use the viewer&rsquo;s controls for full-screen. Model hosted on Kiri Engine.</span><span data-l="ro">{obj_ro} Trageți pentru a roti; derulați pentru zoom; folosiți comenzile vizualizatorului pentru ecran complet. Model găzduit pe Kiri Engine.</span></figcaption>
</figure>'''


def main():
    ap = argparse.ArgumentParser(description="Embed a Kiri Engine 3D model at the end of an essay.")
    ap.add_argument("essay")
    ap.add_argument("model")
    ap.add_argument("--label", default="")
    ap.add_argument("--label-ro", dest="label_ro", default="")
    ap.add_argument("--no-build", action="store_true")
    a = ap.parse_args()

    path = resolve_path(a.essay)
    mid = model_id(a.model)
    src = open(path, encoding="utf-8").read()
    new_block = block(mid, a.label, a.label_ro)

    if 'class="model-embed' in src:
        # Update existing block in place.
        src2 = re.sub(
            r'<figure class="model-embed wrap">.*?</figure>',
            lambda _m: new_block, src, count=1, flags=re.S,
        )
        action = "updated"
    else:
        # Insert after the first </article>.
        if "</article>" not in src:
            sys.exit("No </article> found; cannot place the embed.")
        src2 = src.replace("</article>", "</article>\n\n" + new_block, 1)
        action = "inserted"

    if src2 == src:
        print("No change (block already up to date).")
    else:
        open(path, "w", encoding="utf-8").write(src2)
        print(f"{action} 3D embed ({mid}) in {os.path.relpath(path, ROOT)}")

    if not a.no_build:
        subprocess.run([sys.executable, os.path.join(HERE, "build_seo.py")], cwd=ROOT, check=True)
        print("Ran build_seo.py — CSP frame-src widened on pages that embed a viewer.")


if __name__ == "__main__":
    main()
