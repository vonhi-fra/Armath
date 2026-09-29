# Armath

Mental arithmetic trainer for quant and trading interviews (Zetamac, Optiver 80-in-8 and custom drills),
with a learning mode that finds your slow problems and teaches the tricks to solve them faster.

Work in progress — see [docs/research.md](docs/research.md) for the plan.

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
uv run python scripts/serve.py        # http://localhost:8000
```
