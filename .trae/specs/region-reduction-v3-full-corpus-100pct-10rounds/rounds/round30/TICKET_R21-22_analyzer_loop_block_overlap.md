# R21-22 — analyzer lets two sibling LoopRegions declare the same body blocks

Status: **banked, not dispatched** (the generator-side workaround landed in gate 30 as part of R21-14;
this ticket removes the need for it).

## 0. The defect, stated as a spec violation

Region-reduction principle 2 says every block has **unique membership at every level**. For
`IQEngine/plugins/plugin_system_risk_calculation/__init__.pyc :: PluginRiskCalculation._save_testds_to_csv`
the analyzer declares

    LoopRegion@108  body/tail declaration includes blocks 292, 296, 350
    LoopRegion@262  body_blocks = 292, 296, 350

i.e. the earlier loop's declaration **swallows the following loop's body**. CPython 3.11 hoisted the
second loop's condition recheck into the first loop's exit path, so the two regions are adjacent in
offset and the analyzer's reach-based tail collection cannot tell "after me" from "owned by the loop
that comes after me".

Consequence at emission time: when the parent marks the whole child block set as generated, the
sibling's body blocks are consumed before the sibling is walked, and their statements
(`time.sleep(0.01)` and the recheck) vanish — measured `len orig=80 prod=73 delta=-7 hunks=3`
at sealed gate-29 bytes.

## 1. What landed instead (and why this ticket still owes work)

Gate 30's R21-14 candidate carries **two** generator halves, proven co-requisite by ablation of the
delivered file `sha16 203369154e43eb50`:

| build | `_save_testds_to_csv` reading | file |
|---|---|---|
| sealed | `delta=-7 hunks=3 landings=3` | 42/43 |
| wrapper rule only (`_r2114_wrapper_is_sequential_loops`) | `delta=-6 hunks=1 landings=1` | 42/43 |
| defer rule only (`_r2114_defer_to_unemitted_sibling_loop`) | `delta=-3 hunks=2 landings=1` | 42/43 |
| both | `delta=0 hunks=0 landings=0 judge_diff=False` | **43/43** |

The defer half decides, at the `for b in child.blocks: self.generated_blocks.add(b)` step, whether
`b` is part of `child`'s own emitted content (entry / header / condition / body / back edge); if it
is not, it scans `gen.regions` for an unemitted `LoopRegion` that lists `b` in its `body_blocks` and
skips the mark. That scan is a **cross-region read at generation time** — the one thing the reduction
rules forbid — and it exists only because the analyzer's declarations are not disjoint. The wrapper
half (`while True: loop1; loop2; break` is unwrapped to `loop1; loop2`) is legitimately local.

## 2. What this ticket must produce

An analyzer-side criterion so that the two loops' block sets are disjoint **at identification time**,
which then makes the generator's defer scan removable (the ablation table above is the acceptance
oracle: with the analyzer fixed, the wrapper-only build must reach `delta=0 hunks=0 landings=0` and the
defer helper must be deletable with `risk_calculation` staying 43/43).

Candidate shape (own-data only, no cross-region read): when collecting a `LoopRegion`'s tail/else
reaches, stop the walk at the first block that is itself a loop entry candidate (a block whose
successor set contains a backward jump to itself or to an earlier condition block) and leave that
block and everything it dominates to the following region. Prove the walk stops for
`LoopRegion@108` before touching the general collector — the same tail reach is used by more than one
region type, so a broad stop regresses the corpus (compare the falsified R20-4 stop-set patch: zero
flips and four regressions).

## 3. Acceptance bar

- `plugin_system_risk_calculation/__init__.pyc` stays **43/43** with the defer helper removed.
- `fly/data/quotation.pyc` stays 153/153; the 14-file panel counts do not drop
  (`klinedata 64/64`, `strategy 27/27`, `wizard_quant_api 58/58`, `real_quote 45/45`, `order_api 37/37`,
  `matcher 17/17`, `broker 121/128`, `handlers 29/30`, `trade_info_utils 38/41`, `api_base 27/28`,
  `quote 91/92`, `realtime_event_source 12/13`).
- Fire census over the panel with `cmp` against the sealed products; broad fires that move products
  without moving counts must be reported, not waved through.
- Only `core/cfg/region_analyzer.py` may change (the generator edit here is a *removal*, done in the
  same gate only if the oracle above is met).
