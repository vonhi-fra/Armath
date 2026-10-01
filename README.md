# Armath

Mental arithmetic trainer for quant and trading interviews (Zetamac, Optiver 80-in-8 and custom drills),
with a learning mode that finds your slow problems and teaches the tricks to solve them faster.

**Try it:** https://vonhi-fra.github.io/armath/

## Features

- **Practice** Zetamac-style (custom operations, ranges and duration) or take an **Optiver 80-in-8**
  test: 80 multiple-choice questions in 8 minutes with integers, decimals, fractions, percentages
  and missing numbers, scored +1/−1.
- **Learn:** after each session your slowest (and wrong) problems are explained step by step with
  the best of 47 mental-math tricks and general methods, e.g. 67 × 11 → 6 | 6+7 | 7 → 737.
  Wrong multiple-choice answers come with a quick check that would have ruled them out.
- **Drill a trick:** 10 problems with the rule as a hint, then 10 mixed with look-alikes so you
  learn when the trick applies.
- **Facts:** times tables to 12 and 19, squares and fraction↔decimal pairs with spaced repetition.
- **Progress:** score charts per mode, where you lose time and which trick would help most,
  recommendations on the home screen.
- Six themes including dark mode; no account needed, your data stays in your browser.
- **Works as a phone app:** install it from the browser and it runs offline, with an on-screen
  keypad for fractions and percentages.

The research behind it (test formats, learning science, trick catalogue) is in
[docs/research.md](docs/research.md).

### Install on Android

Open the site in Chrome, then menu ⋮ → **Add to Home screen** → **Install**. Armath gets its own
icon and window and works offline after the first visit. Phone and computer keep separate
histories; move them with **Progress → Your data** (backup / restore).

## Development

Requires [uv](https://docs.astral.sh/uv/).

```bash
uv sync                    # create .venv and install dev dependencies
uv run pytest              # run tests
uv run ruff check          # lint
uv run ruff format         # format
uv run mypy                # type check
uv run armath              # play in the terminal
uv run armath explain "858 / 11"   # step-by-step trick for a problem (--all for every trick)
uv run armath tricks       # list the trick catalogue
```

### Web version

The app runs entirely in the browser: Python is loaded with [Pyodide](https://pyodide.org)
and the UI is plain HTML/CSS, so the site can be hosted on GitHub Pages.

```bash
uv run python scripts/build_site.py   # assemble site/ (web/ files + fresh wheel)
uv run python scripts/serve.py        # http://localhost:8000 (correct MIME types on Windows)
uv run python scripts/make_icons.py   # re-render the app icons in web/icons/ (rarely needed)
```

A service worker (`web/sw.js`) caches the app and Pyodide, so the installed app works offline;
the build script stamps it with the list of files and a build id, so each deploy replaces the
old cache.

Every push to `main` runs the tests, builds the site and deploys it to GitHub Pages
(`.github/workflows/pages.yml`). One-time setup: repository **Settings → Pages → Source:
GitHub Actions**.

Your practice history lives only in your browser; use **Progress → Your data** to download a
backup or restore one.
