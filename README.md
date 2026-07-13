# PacificaRomania

A static website for the PacificaRomania art collection — a curatorial project
reading Pacific and Southeast Asian art through the comparative lens of
Mircea Eliade and Constantin Brâncuși.

No build step: plain HTML/CSS/JS. Open `index.html` directly, or serve the
folder with any static server, e.g.:

```
python3 -m http.server 8000
```

## Structure

```
index.html          Home
collection.html      Collection, organised by region
journal.html          Journal index
journal/*.html        Individual curatorial essays
about.html
contact.html
404.html
assets/css/style.css  Shared styles
assets/js/main.js      Mobile nav toggle
CNAME                  GitHub Pages custom-domain file
netlify.toml           Netlify build/redirect config
```

## Deploying to `www.pacificaromania.space`

The domain is registered with Spaceship. Pick **one** of the two hosts below
(both are free for a static site like this one).

### Option A — GitHub Pages

1. In the repo: **Settings → Pages → Build and deployment → Source**, choose
   `Deploy from a branch`, branch `main` (or whichever branch this is merged
   into), folder `/ (root)`.
2. The `CNAME` file in this repo already points Pages at
   `www.pacificaromania.space` — GitHub will pick it up automatically once
   Pages is enabled.
3. In Spaceship's DNS settings for `pacificaromania.space`, add:
   - a `CNAME` record: host `www` → value `<your-github-username>.github.io`
   - for the bare/apex domain (`pacificaromania.space` with no `www`), add
     `A` records pointing at GitHub Pages' IPs:
     `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
     (or an `ALIAS`/`ANAME` record at `<your-github-username>.github.io` if
     Spaceship supports one, instead of the four `A` records).
4. Back in **Settings → Pages**, tick **Enforce HTTPS** once DNS has
   propagated (can take up to a few hours).

### Option B — Netlify

1. In Netlify: **Add new site → Import an existing project**, connect this
   GitHub repo. `netlify.toml` already sets the publish directory to `.`
   (no build command needed).
2. In **Site settings → Domain management**, add a custom domain:
   `www.pacificaromania.space`.
3. In Spaceship's DNS settings, add the `CNAME` record Netlify shows you
   (typically `www` → `<your-site-name>.netlify.app`), plus Netlify's
   recommended apex-domain redirect if you also want the bare domain to work.
4. Netlify issues and renews the HTTPS certificate automatically once DNS
   verifies.

If you host on GitHub Pages, delete `netlify.toml`; if you host on Netlify,
you can leave `CNAME` in place — it's simply ignored by Netlify.

## Content

Journal essays and collection entries are adapted from PacificaRomania's own
research and social posts. Photographs from the collection are not yet
included in this build — drop images into `assets/images/` and reference
them from the relevant page/essay when available.
