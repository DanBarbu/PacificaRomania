# Continuous integration (`.github/workflows/ci.yml`)

This static site has no server by design, but it does have an **always-on
execution environment on GitHub's infrastructure**: a GitHub Actions workflow
that validates and self-heals every change. It runs regardless of who made the
edit — a human, Claude, Gemini, or any other assistant — and does not depend on
any local container or expiring API token.

## What it does

| Trigger | Behaviour |
|---------|-----------|
| **Pull request → `main`** | Runs `tools/build_seo.py` then `tools/verify.py`. **Fails** if any link/tag is broken *or* if the generated files (`sitemap.xml`, `llms.txt`, injected head tags) are stale — i.e. the author forgot to run `build_seo.py`. This is the merge gate. |
| **Push to `main`** (and manual `workflow_dispatch`) | Runs the same build + verify, then **auto-commits** any regenerated SEO files with `chore(ci): sync generated SEO files [skip ci]`, so the deployed site is always in sync even if someone committed without rebuilding. |

Publishing is unchanged: **GitHub Pages still deploys from the `main` branch.**
This workflow only validates and keeps generated files current — it never
touches page content or the Pages configuration.

## Why the auto-commit is safe

- Pushes made with the built-in `GITHUB_TOKEN` do **not** re-trigger workflows,
  so there is no infinite loop.
- `verify.py` runs *before* the sync step, so a broken tree fails the job and is
  never pushed.
- The commit is authored by `pacificaromania-ci[bot]` and marked `[skip ci]`.

## Make the gate blocking (one-time repo setting)

The workflow always runs and shows a red ✗ on a bad PR, but to make that
**block merging**, enable branch protection once:

1. Repo → **Settings → Branches → Add branch protection rule** for `main`.
2. Tick **Require status checks to pass before merging**.
3. Select the **`build-verify`** check.

After that, no pull request with broken links, malformed tags, or un-rebuilt
SEO files can be merged into `main`.

## Running the same checks locally

```bash
python3 tools/build_seo.py     # rebuild sitemap + llms.txt + head tags
python3 tools/verify.py        # must print: No broken links or malformed tags. OK.
```

If `git status` is clean after those two commands, CI will be green.
