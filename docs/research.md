# Armath — research notes

Initial research for a customizable mental-arithmetic trainer for quant/trading interviews
(Zetamac, Optiver 80-in-8) with a learning mode that detects weak spots and teaches tricks.

## 1. Target test formats

### Zetamac (arithmetic.zetamac.com)
- Default: addition `(2–100) + (2–100)`, subtraction = addition reversed,
  multiplication `(2–12) × (2–100)`, division = multiplication reversed, 120 seconds.
- Typed answers, auto-advance as soon as the typed answer is correct (no Enter).
- Score = number of correct answers. ~50 is a baseline, 70+ is competitive for top firms.
- Fully customizable ranges per operation and duration.

### Optiver 80-in-8
- 80 questions, 8 minutes (~6 s/question), no calculator.
- Multiple choice, 4 options, no skipping, no going back.
- Scoring +1 correct / −1 wrong (some older reports: −2). Net ~55 reported as pass line, 70+ competitive.
- Integers, decimals and fractions, all four operations.
- Two shapes: direct (`373 + 57 = ?`) and missing-operand (`66 × ? = 138.6`).
- Advice from prep sites: tables up to 19×19, fraction↔decimal table (1/8 = 0.125, 3/8 = 0.375, 1/7 ≈ 0.143…),
  drill missing-operand until automatic; careful beats reckless because of the penalty.

## 2. Existing tools (what "better" means)

| Tool | What it has | What it lacks |
| --- | --- | --- |
| Zetamac | Custom ranges, fast keyboard flow | No history, no per-problem stats, no teaching |
| zetamac-tracker (GitHub, static JS + localStorage) | Per-question timing, score history, calendar heatmap, slowest problem types | No explanations, no targeted drills |
| Various 80-in-8 clones (quantvault, quantt, trademind, optiver80-in-8.com) | 80Q/8min, MC, penalty scoring | Generic; little adaptive practice |

**Our differentiators:** per-problem timing normalized by difficulty, weakness detection,
a trick/strategy engine that explains *this specific problem* step by step, trick-focused drill mode,
spaced repetition of slow/missed problems, progress charts, Zetamac + Optiver + custom presets, themes.

## 3. Tech stack options

Hard constraints: Python with **uv** + **pytest**, clean OOP/SOLID, and it should eventually run on
**GitHub Pages** (static hosting only — no server).

| Option | Pros | Cons |
| --- | --- | --- |
| **A. Python core in the browser via Pyodide** (chosen) | All logic in tested Python; static site → GitHub Pages; works offline | ~8 MB runtime download, ~2–3 s cold start (cached afterwards) |
| B. TypeScript app (Vite + Vitest) | Fastest load, most natural for the web | Drops uv/pytest/Python |
| C. Python server (FastAPI/HTMX, NiceGUI, Streamlit) | Nice Python DX | Needs a server; not GitHub Pages |
| D. Flet (`flet build web`) | Python UI, static output | Heavy bundle, less control over look/themes |
| E. PyScript + MicroPython | Tiny download | Missing stdlib (dataclasses, typing, fractions) → poor fit for clean OOP |

Plain Pyodide (loaded from CDN) is ~1 s faster than PyScript on top of it, so we'd use Pyodide directly with a
tiny JS bootstrap. Keystroke → Python call latency is negligible.

### Proposed architecture (option A)

Ports-and-adapters: the domain never imports browser code, so all of it runs under plain CPython + pytest.

```
src/armath/
  domain/        # value objects: Operation, Problem, Answer (exact Fraction), Attempt, SessionConfig
  generators/    # ProblemGenerator protocol; RangeGenerator (Zetamac), OptiverGenerator, TrickGenerator
  tricks/        # Trick base class + registry; one module per trick family
  modes/         # GameMode/Session, ScoringPolicy (count, ±1), timers, answer checking, MC distractors
  analytics/     # per-attempt features, baselines, weakness scores, recommender, spaced repetition
  persistence/   # repository ports + JSON (de)serialization, export/import
  ui/            # presenters (pure Python, tested with fake views)
  web/           # Pyodide adapters only: DOM views, localStorage repository, clock
web/             # index.html, CSS themes, bootstrap.js (loads Pyodide + our wheel)
tests/
```

Key design points:
- **`Trick` is the unit of extension (Open/Closed).** Each trick class provides:
  `applies_to(problem)`, `explain(problem) -> list[Step]` (templated on the real numbers),
  `generate(rng) -> Problem` (only problems where the trick applies), plus metadata (name, category, difficulty).
  Adding a trick = one new class + registration + tests; nothing else changes.
- **Exact arithmetic:** answers stored as `fractions.Fraction` (so `138.6` is exact); parser accepts `0.125`, `.125`, `1/8`.
- **Injected `Clock` and `random.Random`** → deterministic tests.
- **Strategy objects** for scoring (Zetamac count vs Optiver ±1), answer input (typed vs multiple choice) and
  distractor generation (misplaced decimal, off-by-one digit, ±10, wrong carry).
- **Repository protocol** for attempts/sessions: in-memory (tests), localStorage (web), JSON export/import (backup).
- **Presenters (MVP)** hold UI logic in Python and talk to a `View` protocol; the DOM view is a thin adapter.

### Tooling
uv (project + lockfile), pytest (+ pytest-cov), Hypothesis for property tests
(every generated problem's answer is correct; every trick's `explain` ends at the right answer; `generate` output
satisfies `applies_to`), ruff (lint + format), mypy or pyright (strict).
GitHub Actions: test → `uv build` wheel → assemble `web/` + wheel → deploy to Pages.
Later: Playwright end-to-end tests against the static site.

## 4. Detecting "which problems went worse"

Raw time is misleading (47×83 is inherently slower than 3×4), so compare against an expectation:
1. Every attempt records: problem, features (operation, operand digit counts, carries/borrows, decimal places,
   missing-operand, which tricks apply), response time, correctness, mode.
2. Normalize time: subtract an estimated typing cost per answer digit (answers auto-submit in Zetamac style).
3. Expected time = your own recent median for the same feature bucket (e.g. "1-digit × 2-digit, 1 carry");
   slowness = time / expected. Use medians/MAD (robust to outliers) and exponential decay so recent sessions count more.
4. Weakness score per bucket and per trick = weighted mix of slowness and error rate, with a minimum sample size.
5. Recommender: rank tricks by (weakness of problems where the trick applies) × (how common those problems are in the
   target test). Show "You averaged 6.2 s on ×11 problems vs 2.1 s typical → here's the trick → drill it".
6. Spaced repetition (Leitner boxes) re-queues specific slow/missed problems in learning mode.

## 5. Trick catalogue v0 (to be refined and verified per trick)

Every problem must always have at least one applicable strategy — general methods act as fallbacks.

**Addition / subtraction**
1. Left-to-right addition (hundreds, then tens, then units) — general fallback.
2. Round and compensate: 47 + 38 = 47 + 40 − 2; 523 − 198 = 523 − 200 + 2.
3. Complements to 100/1000 ("all from 9, last from 10"): 1000 − 387 = 613.
4. Subtract by counting up: 82 − 57 → 57→60→82 = 3 + 22 = 25.
5. Make pairs of 10/100 when summing several numbers.

**Multiplication**
6. Distributive split (general fallback, the core Zetamac skill): 7 × 68 = 420 + 56.
7. ×5 = ×10 ÷ 2; ×25 = ×100 ÷ 4; ×50 = ×100 ÷ 2; ×125 = ×1000 ÷ 8.
8. ×9 = ×10 − n; ×99 = ×100 − n; ×11 = ×10 + n.
9. ×11 for two-digit numbers: put the digit sum in the middle (carry if ≥ 10): 35 × 11 = 385, 67 × 11 = 737.
10. Near-round multiplier: ×19 = ×20 − n, ×21 = ×20 + n, ×15 = ×10 + half.
11. Doubling and halving: 16 × 35 = 8 × 70 = 560.
12. Factorization / regrouping: 36 × 25 = 9 × 4 × 25 = 900.
13. Difference of squares: 47 × 53 = 50² − 3² = 2491.
14. Squares ending in 5: n5² = n(n+1) | 25 → 65² = 4225.
15. Squares near 50: (50 + k)² = (25 + k) hundreds + k² → 53² = 2809.
16. Squares near 100 / products near 100 (base method): 97 × 96 = (97 − 4) | 3 × 4 = 9312.
17. Same tens digit, units summing to 10: 43 × 47 = 4 × 5 | 3 × 7 = 2021.
18. Teens × teens: 13 × 17 = (13 + 7) × 10 + 3 × 7 = 221.
19. Cross-multiplication for general 2-digit × 2-digit.
20. Squares via (a ± b)² and memorized squares to 25–30.
21. Decimals: multiply as integers, then place the decimal point (0.3 × 0.07 = 21 × 10⁻³).

**Division**
22. ÷5 = ×2 ÷ 10; ÷25 = ×4 ÷ 100; ÷125 = ×8 ÷ 1000.
23. Division as a missing factor with chunking: 648 ÷ 12 → 12 × 50 = 600, 48 = 12 × 4 → 54.
24. Simplify first by a common factor: 168 ÷ 24 = 21 ÷ 3 = 7.
25. Repeated halving for ÷4, ÷8.
26. Decimal divisors: shift both decimal points to make the divisor an integer.

**Fractions / decimals / percentages (Optiver)**
27. Fraction↔decimal table: 1/2…1/12, n/8, 1/16, sevenths (1/7 = 0.142857…).
28. Percentage swap: x% of y = y% of x (24% of 50 = 50% of 24).
29. Missing operand → inverse operation plus magnitude estimate: 66 × ? = 138.6 → 2.1.
30. Fraction add/sub via common denominator: a/b + c/d = (ad + bc)/bd, then simplify.

**Multiple-choice elimination (Optiver)**
31. Last-digit check: units digit of a product = product of units digits (mod 10).
32. Magnitude check: round to 1 significant figure to discard wrong options.
33. Digit-sum / casting out nines and parity checks.

## 6. Proposed roadmap

1. Scaffold: uv project, pytest, ruff, type checker, CI.
2. Domain + Zetamac-style generator + session/scoring (CLI adapter for quick manual testing).
3. Web shell: Pyodide bootstrap, game screen, themes (light, dark, + a few more), localStorage persistence.
4. Attempt features + analytics + progress screen (history, per-category times, multiplication heatmap).
5. Trick engine: base class, registry, first ~10 tricks with explanations and generators.
6. Learning mode: post-session review of slowest problems → explanation → trick drill; spaced repetition.
7. Optiver 80-in-8 mode: decimals/fractions, missing operand, MC with distractors, ±1 scoring.
8. Polish: presets, settings, export/import, PWA/offline, GitHub Pages deploy.

## Sources
- [Optiver 80 in 8 — quantvault](https://quantvault.org/optiver-80-in-8.html)
- [Zetamac practice — quantvault](https://quantvault.org/zetamac-practice.html)
- [zetamac-tracker (GitHub)](https://github.com/MatthewC141/zetamac-tracker)
- [Mental math tips and tricks — tradinginterview.com](https://www.tradinginterview.com/courses/mental-arithmetic/lessons/mental-math-tips-and-tricks-for-quick-calculations/)
- [Quant mental math questions — quantt](https://www.quantt.co.uk/resources/quant-mental-math-questions)
- [PyScript page load time — John Hanley](https://www.jhanley.com/blog/pyscript-page-load-time/)
