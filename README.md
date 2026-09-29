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
```
