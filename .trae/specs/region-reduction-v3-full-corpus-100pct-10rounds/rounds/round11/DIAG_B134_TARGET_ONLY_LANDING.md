# DIAG B134 — TARGET_ONLY landing: `bar._history_bars` + `strategy_universe._on_clear_de_listed`

Status: IN PROGRESS (writing incrementally; scratch `D:/Temp/r134/`).
Scope: diagnosis only. No edits under `core/`, no git writes, no 402-file gate.

## 0. Units under test (from sealed round-10 reports)

- `site-packages/IQEngine/core/bar.pyc :: <module>.BarData._history_bars` — 84/85, `Different control flow`
- `site-packages/IQEngine/core/strategy/strategy_universe.pyc :: <module>.StrategyUniverse._on_clear_de_listed` — 10/11, `Different control flow`

Both registered `TARGET_ONLY` in `rounds/round10/UNITMAP_R10.md` line 21 / 35.

## 1. Hunk lists (measured)

(pending)

## 2. Role census (measured on the real dispatch path)

(pending)

## 3. Host emitter/analyzer line

(pending)

## 4. Same site or separate?

(pending)

## 5. Suppression experiments (does the product move?)

(pending)

## 6. Minimal repro battery

(pending)

## 7. Falsifications of prior measurements

(pending)

