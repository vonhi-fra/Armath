# Armath — research notes

Research for a customizable mental-arithmetic trainer for quant/trading interviews
(Zetamac, Optiver 80-in-8) with a learning mode that detects weak spots and teaches tricks.
First written at project start; revised after the web version (step 3) with a code review,
deeper trick research and a design for the trick system.

## 1. Target test formats

### Zetamac (arithmetic.zetamac.com)
- Default: addition `(2..100) + (2..100)`, subtraction = addition reversed,
  multiplication `(2..12) × (2..100)`, division = multiplication reversed, 120 seconds.
- Typed answers, auto-advance as soon as the typed answer is correct (no Enter).
- Score = number of correct answers. ~50 is a baseline, 70+ is competitive; with ~30 min/day for a month
  people report going from 60–70 to 100+.
- Implications for tricks: multiplication is always *1–2-digit × up to 3-digit* and division always has a
  divisor 2..12 and an integer quotient 2..100. Subtraction minuends are at most 200.

### Optiver 80-in-8
- 80 questions, 8 minutes (~6 s/question), no calculator.
- Multiple choice, 4 options, no skipping, no going back.
- Scoring +1 correct / −1 wrong (older reports: −2). Net ~55 reported as pass line, 70+ competitive.
- Integers, decimals and fractions, all four operations; direct (`373 + 57 = ?`) and missing-operand
  (`66 × ? = 138.6`) shapes. Reported content: two-digit multiplication, decimals (`0.25 × 4000`),
  large clean division (`63000 / 700`), 3–4 digit addition/subtraction, fractions that cancel neatly,
  decimal divisors (`8 ÷ 0.4 = 20`).
- Advice: tables to 19×19, fraction↔decimal table, drill missing-operand; careful beats reckless.

## 2. Existing tools (what "better" means)

| Tool | What it has | What it lacks |
| --- | --- | --- |
| Zetamac | Custom ranges, fast keyboard flow | No history, no per-problem stats, no teaching |
| zetamac-tracker (static JS) | Per-question timing, history, heatmap, slowest problem types | No explanations or targeted drills |
| mentalmath.online, Quantercise, Mind Math Trainer | Adaptive weighting of weak operations / patterns, streaks, spaced repetition queues | Adapt *what* you practise, but don't teach *how* to solve it faster |
| 80-in-8 clones | 80Q/8min, MC, penalty scoring | Generic, little adaptivity |

**Our differentiator:** diagnose the slow/erroneous problems, explain *that specific problem* with the best
trick step by step, then drill the trick — first in isolation, then mixed with look-alikes so you learn
*when* to use it — and measure whether you actually got faster.

## 3. Tech stack (decided: Python + Pyodide)

All logic is Python (uv, pytest, ruff, mypy strict); the browser loads Pyodide (v314, Python 3.14) from
jsDelivr and our wheel; `armath.web.dom` is the only browser-specific module. Alternatives considered:
TypeScript app (drops Python), Python server (no GitHub Pages), Flet (heavy), PyScript+MicroPython
(missing stdlib). Cost: ~8 MB first load, cached afterwards.

## 4. Learning science that shapes the design

- **Strategy vs. retrieval.** Arithmetic develops from slow procedures to fast memory retrieval
  (Siegler). Small facts (7×8) should be *retrieved*; larger problems need a *procedure*. So the tool
  needs two kinds of practice: fact drills (spaced repetition of individual facts) and trick/strategy
  drills. Response times reveal which one is happening: retrieval is fast and flat, procedures grow with
  problem size ("problem-size effect").
- **Strategy choice.** People pick strategies by relative speed and accuracy (Adaptive Strategy Choice
  Model). A trick only helps once it is faster than your current method → measure before/after per trick.
- **Blocked → interleaved practice.** Blocked practice (all problems use one trick) is good for learning
  the steps, but interleaved practice (mixed problems) trains *recognising which trick applies* and gives
  much better test results (Rohrer et al. 2014, 2015, 2019 RCT). → A trick drill should end with a mixed
  round including look-alikes where the trick does *not* apply (e.g. ×11 mixed with ×12).
- **Worked examples with fading.** Novices learn procedures best from worked examples whose steps are
  gradually removed until they solve alone. → Explanations are step lists; the drill can show all steps,
  then only the first step as a hint, then nothing.
- **Desirable difficulties & spacing.** Spacing and retrieval improve retention; tricks and weak facts
  should come back in later sessions (Leitner boxes per trick/fact).

## 5. Detecting "which problems went worse"

Raw time misleads (47×83 is inherently slower than 3×4), so compare against an expectation:
1. Every attempt records the problem, total time, **time to first keystroke** (thinking vs. typing) and
   **corrections** (deletions — the only visible mistakes in Zetamac mode, where only correct answers are
   submitted). *Implemented after the review.*
2. Features per problem: operation, digit counts, carries/borrows, decimal places, missing operand,
   answer length, and which tricks apply.
3. Expected time = your own recent median for the same feature bucket (with sensible priors while data is
   scarce); slowness = time ÷ expected. Medians/MAD, exponential decay so recent sessions count more.
   Exclude the first problem of a session (screen-switch reaction time).
4. Weakness per bucket and per trick = mix of slowness and correction rate, with a minimum sample size.
5. Recommender: rank tricks by (weakness on problems where the trick applies) × (how often such
   problems occur in the target test).

## 6. Trick catalogue v1

Each entry: **when it applies** (this becomes `applies_to`) → method → example. All examples were checked.
*Fallback* strategies apply to every problem of their operation, so every problem has an explanation.
Tags: **Z** = common in Zetamac defaults, **O** = Optiver-style.

### Addition
| # | Trick | Applies when | Method → example |
| --- | --- | --- | --- |
| A1 | Left to right *(fallback)* Z | always | tens, then units, type while computing: 67 + 58 → 110 + 15 = 125 |
| A2 | Round and compensate Z | an addend ends in 7, 8 or 9 | 47 + 38 = 47 + 40 − 2 = 85 |

### Subtraction
| # | Trick | Applies when | Method → example |
| --- | --- | --- | --- |
| S1 | Left to right *(fallback)* Z | always | 145 − 62 → 145 − 60 = 85, − 2 = 83 |
| S2 | Round and compensate Z | subtrahend ends in 7, 8 or 9 | 131 − 69 = 131 − 70 + 1 = 62 |
| S3 | Count up Z | the subtraction crosses a hundred (borrow) | 132 − 87: 87 → 100 is 13, + 32 = 45 |
| S4 | Complement ("all from 9, last from 10") O | minuend is a power of 10 | 1000 − 387 = 613 |

### Multiplication
| # | Trick | Applies when | Method → example |
| --- | --- | --- | --- |
| M1 | Split and add, left to right *(fallback)* Z | always | 7 × 68 = 420 + 56 = 476 |
| M2 | Round and compensate Z | multi-digit factor ends in 8 or 9 | 7 × 69 = 490 − 7 = 483 |
| M3 | ×5 = ×10 ÷ 2 Z | a factor is 5 | 5 × 68 = 680 ÷ 2 = 340 |
| M4 | ×25, ×50, ×125 via ÷4, ÷2, ÷8 O | a factor is 25, 50 or 125 | 36 × 25 = 3600 ÷ 4 = 900 |
| M5 | ×9 = ×10 − n, ×99 = ×100 − n Z | a factor is 9 or 99 | 9 × 74 = 740 − 74 = 666 |
| M6 | ×11: digit sum in the middle Z | a factor is 11, other is 2-digit | 67 × 11 = 6 (13) 7 → 737 |
| M7 | ×12 = ×10 + ×2 Z | a factor is 12 | 12 × 47 = 470 + 94 = 564 |
| M8 | Halve and double Z | one factor even, the other ends in 5 | 6 × 45 = 3 × 90 = 270 |
| M9 | Factor the multiplier Z | a factor splits into easy parts | 12 × 35 = 6 × 70 = 420 |
| M10 | Near-round multiplier O | a factor is 19, 21, 29, 31, 49, 51… | 19 × 23 = 460 − 23 = 437 |
| M11 | Difference of squares O | factors equidistant from a round number | 47 × 53 = 2500 − 9 = 2491 |
| M12 | Close together (Benjamin) O | both factors near the same round number | 43 × 48 = 40 × 51 + 3 × 8 = 2064 |
| M13 | Same tens, units sum to 10 O | 43 × 47 style | 4 × 5 = 20, 3 × 7 = 21 → 2021 |
| M14 | Base 100 (Vedic *Nikhilam*) O | both factors near 100 | 97 × 96 = (97 − 4) \| 3 × 4 = 9312 |
| M15 | Teens × teens O | both factors 11..19 | 13 × 17 = (13 + 7) × 10 + 21 = 221 |
| M16 | Squares ending in 5 O | square of n5 | 65² = 6 × 7 \| 25 = 4225 |
| M17 | Squares by up-and-down (Benjamin) O | any square | 47² = 50 × 44 + 3² = 2209 |
| M18 | Vertically and crosswise O | general 2-digit × 2-digit | 23 × 12: 2 \| 4 + 3 \| 6 → 276 |
| M19 | Decimals as integers O | a factor has decimals | 0.3 × 0.07 = 21 × 10⁻³ = 0.021 |

### Division
| # | Trick | Applies when | Method → example |
| --- | --- | --- | --- |
| D1 | Missing factor, chunking *(fallback)* Z | always | 648 ÷ 12: 12 × 50 = 600, 48 = 12 × 4 → 54 |
| D2 | ÷5 = ×2 ÷ 10 Z | divisor 5 | 345 ÷ 5 = 690 ÷ 10 = 69 |
| D3 | Halve both Z | both even | 432 ÷ 12 = 216 ÷ 6 = 36 |
| D4 | ÷11 from the outer digits Z | divisor 11, 2-digit quotient | 858 ÷ 11: 8 > 5 so 8 − 1 = 7, then 8 → 78 |
| D5 | ÷9 digit rule Z | divisor 9, quotient not ending in 0 | 423 ÷ 9: 42 ÷ 9 → 4, 10 − 3 = 7 → 47 |
| D6 | Double both (divisor ends in 5) O | divisor 15, 25, 35… | 315 ÷ 35 = 630 ÷ 70 = 9 |
| D7 | ÷25, ÷125 via ×4, ×8 O | divisor 25 or 125 | 900 ÷ 25 = 36 |
| D8 | Shift the decimal point O | decimal divisor | 8 ÷ 0.4 = 80 ÷ 4 = 20 |
| D9 | Cancel zeros O | both end in zeros | 63000 ÷ 700 = 630 ÷ 7 = 90 |

Why D4 works: 11 × (10a + b) is `a | a+b | b`, with a carry into the hundreds when a + b ≥ 10 — which is
exactly when the hundreds digit exceeds the middle digit. Why D5 works: 9 × (10t + u) = 90t + 9u, and
9u ends in 10 − u while the rest is 9t + (u − 1) < 9(t + 1).

### Fractions, decimals, percentages (Optiver)
F1 fraction↔decimal table (n/8, n/16, thirds, sixths, sevenths); F2 percentage swap (24% of 50 = 50% of 24);
F3 missing operand → inverse operation plus magnitude estimate; F4 cancel before multiplying fractions;
F5 dividing by a fraction = multiplying by its reciprocal (÷0.25 = ×4).

### Multiple-choice elimination (Optiver)
E1 last digit (units digit of a product = product of units digits); E2 magnitude (round to one
significant figure); E3 digit sum / casting out nines; E4 parity.

### Facts to memorise (drilled by retrieval, not explained by tricks)
Tables to 12 × 12 (Zetamac) and ideally 19 × 19 (Optiver); squares to 25; common fraction↔decimal pairs.

## 7. Trick system design (next step)

```
tricks/
  base.py          # Trick (ABC) + metadata
  explanation.py   # Step, Explanation
  registry.py      # TrickRegistry: all(), get(id), applicable(problem), best(problem)
  addition.py, subtraction.py, multiplication.py, division.py   # one class per trick
```
- **`Trick`** (abstract, Open/Closed — adding a trick never changes existing code):
  - metadata: `id`, `name`, `summary` (the rule in one line), `operation`, `priority`, `fallback`;
  - `applies_to(problem) -> bool` — precise, cheap predicate;
  - `explain(problem) -> Explanation` — steps templated on the real numbers, each step carrying the
    intermediate value, ending at the answer;
  - `generator(...) -> ProblemGenerator` — problems where the trick applies (plugs straight into
    `SessionPlan`, so trick drills are just another plan).
- **Choosing the best trick:** highest-priority applicable trick; fallbacks have the lowest priority.
  Later: a per-user cost model (measured speed per trick) instead of fixed priorities.
- **Verification by property tests over the registry:** for every trick and many generated problems —
  `applies_to` holds, the explanation's final value equals the answer, every step's arithmetic is exact,
  and every problem of an operation has a fallback. This keeps a growing catalogue correct.
- **Learning loop (step 6):** results screen → "why was this slow?" shows the best trick's worked steps →
  "Practise this trick" → blocked drill with hints fading → mixed round with look-alikes →
  before/after comparison; tricks come back later via spaced repetition.

## 8. Review findings and improvement backlog

Fixed during the review:
- Zetamac-mode accuracy was always 100% (wrong answers are never submitted) → attempts now record
  corrections and time to first keystroke; accuracy is now "first try" (correct without deleting).
- Durations used the wall clock (a clock adjustment mid-game could crash it) → monotonic clock.
- CI now also runs on Python 3.14, which is what Pyodide uses in the browser.

Backlog (not urgent):
- Store the structured session configuration in each record (not only the mode name) so scores can be
  filtered and compared reliably.
- Exclude or soften the first problem's time (includes reacting to the screen change), or add a 3-2-1 start.
- Self-host the fonts (privacy/GDPR for a public site, works offline).
- Warn when browser storage is unavailable or full; JSON export/import as a backup.
- iOS numeric keyboards (`inputmode="decimal"`) have no minus key — matters for Optiver negatives.
- GitHub Pages deploy workflow; optional service worker for offline use.

## 9. Roadmap

1. ~~Scaffold~~ 2. ~~Domain, Zetamac generator, sessions, CLI~~ 3. ~~Web version~~
4. ~~**Trick engine:** base, registry, explanations, property tests; first tricks for Zetamac ranges
   (A1–A2, S1–S3, M1–M9, D1–D5).~~ Done, except that M9 became "×4 and ×8 by doubling" (the
   factoring idea is covered by halve-and-double) and D3 "halve both" requires a quotient above 12.
5. ~~**Learning mode:** explanations on the results screen, trick drills (blocked → interleaved),
   trick library screen.~~ Done: drills are 10 focused problems (rule shown as a hint) + 10 mixed
   (half look-alikes: same-operation Zetamac problems the trick doesn't fit), `?` reveals the
   steps, and the results show per-round times. Possible refinement: per-trick look-alikes that
   share a surface feature (×11 vs ×12, ÷9 on multiples of 90) for sharper discrimination practice.
6. ~~**Analytics:** feature buckets, baselines, weakness scores, recommender, progress screen.~~
   Done, simplified from §5: the yardstick is your own median time over recent practice
   (drills and each session's first problem excluded); seconds above it are "time lost",
   credited to each problem's best trick → recommendations on the home screen. Progress screen:
   score chart per mode, per-trick table with older-vs-newer trend, per-problem-kind table.
   Later: per-kind expected times as the yardstick, multiplication heatmap.
7. ~~**Optiver 80-in-8:** decimals/fractions, missing operand, MC with distractors, ±1 scoring,
   O-tricks.~~ Done: `generators/optiver.py` (integers, decimals, fractions, 25% missing operand),
   `modes/choices.py` (close distractors + one decimal-point slip), preset `optiver()`.
   New tricks: general methods for decimals (incl. long division like 39 ÷ 2 = 19.5), fractions and
   missing operands (undo, then the best trick for the rewritten problem), M11, M16, D8 (= decimal
   division method), D9 cancel zeros, M4/F5 as "decimal as a fraction". Not yet: M12 close
   together, M13, M14 base 100, M15 teens, M17–M18, percentages (F2), MC elimination (E1–E4).
8. **Polish:** facts mode with spaced repetition, backlog items, GitHub Pages deploy.

(Tricks moved ahead of analytics: the learning loop can start from "your slowest problems" right away,
and weakness detection then has trick applicability to aggregate by.)

## Sources
- [Optiver 80 in 8 — quantvault](https://quantvault.org/optiver-80-in-8.html)
- [Optiver test — JobTestPrep](https://www.jobtestprep.com/optiver-test)
- [Zetamac practice — quantvault](https://quantvault.org/zetamac-practice.html)
- [Zetamac strategies — Geoffrey Lee](https://www.geoffreylee.me/zetamac)
- [zetamac-tracker (GitHub)](https://github.com/MatthewC141/zetamac-tracker)
- [Mental Math Trainer (mentalmath.online)](https://www.mentalmath.online/), [Quantercise](https://quantercise.com/mental-math), [Mind Math Trainer (GitHub)](https://github.com/shubhamsingh-007/mentalmathtrainer)
- [Mental math tips and tricks — tradinginterview.com](https://www.tradinginterview.com/courses/mental-arithmetic/lessons/mental-math-tips-and-tricks-for-quick-calculations/)
- [Quant mental math questions — quantt](https://www.quantt.co.uk/resources/quant-mental-math-questions)
- A. Benjamin & M. Shermer, *Secrets of Mental Math* (close-together, factoring, up-and-down squaring)
- [Nuggets from Vedic Mathematics — UCSD](https://cseweb.ucsd.edu//~gupta/vedic.html)
- [Rohrer et al. 2015, Interleaved Practice Improves Mathematics Learning](http://uweb.cas.usf.edu/~drohrer/pdfs/Rohrer_et_al_2015JEdPsych.pdf); [2019 RCT](https://gwern.net/doc/psychology/spaced-repetition/2019-rohrer.pdf)
- [Siegler, Strategy choice procedures and multiplication skill](https://www.researchgate.net/publication/20184024_Strategy_Choice_Procedures_and_the_Development_of_Multiplication_Skill)
- [Renkl et al., Fading worked-out solution steps](https://www.academia.edu/1126007/From_studying_examples_to_solving_problems_Fading_worked_out_solution_steps_helps_learning)
- [PyScript page load time — John Hanley](https://www.jhanley.com/blog/pyscript-page-load-time/)
