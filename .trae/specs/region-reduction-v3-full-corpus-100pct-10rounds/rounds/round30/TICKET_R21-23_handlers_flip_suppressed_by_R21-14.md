# R21-23 — handlers `_target` has a working flip, but R21-14 (gate 30) suppresses it

## 0. Measured facts, not hypotheses

`IQCommon/logger/handlers.pyc :: TWHThreadController._target` is the file's only failing unit
(`delta=-2 hunks=1 landings=3` sealed; still `29/30` at gate 30).

Engineer r44a delivered a generator-only criterion at `region_ast_generator.py:1963` (+67/−0, whole-file
candidate sha16 `691e5aa4f57065d8`, banked as `CANDIDATE_r44a_region_ast_generator.py`, report
`FIX_R21-20_r44a_NOT_LANDED.md`). I re-measured it in my own mirror:

    unit_diff … handlers.pyc _target --prod <r44a product> --all
    len orig=199 prod=199 delta=0 / hunks=0 landings=0 judge_diff=False
    [single] status=success units=30/30

It works **alone**. It does not survive pairing with gate 30's R21-14 half:

| build (merged by base-line coordinates, all hunks disjoint) | `handlers` |
|---|---|
| r44a alone | **30/30** |
| r44a + r43a (`p3744`) | 30/30 |
| r44a + r41a (`p4144`) | 30/30 |
| r44a + r42a/R21-14 (`p3644`) | **29/30** ← the blocker |
| all four (`a304ab6887f71dfc`) | 29/30 (so the quad bought nothing over the triple) |

## 1. What to find out

R21-14 changed two things in the `while`/else emission: `_r2114_wrapper_is_sequential_loops` (a
`while True: loop1; loop2; break` wrapper is now unwrapped) and the sibling-defer mark. `_target`
contains a `while` inside two sibling condition ifs, and r44a's precondition reads exactly the
sibling-IfRegion relationship (`merge_block == next top-level IfRegion's condition/entry`, empty
`orelse`/`elif_*`, then-tail `return None` a single-pred `pure-none` non-join landing).

So one of the two R21-14 halves re-shapes `_target`'s region data before r44a's rule sees it. Determine
which, by running these four builds over `handlers.pyc` only (the pair table above shows r43a/r41a are
innocent, so two builds suffice if you stub the other half as I did in `D:/Temp/t30/out/g36_A.py` /
`g36_B.py`):

1. R21-14 wrapper-half only + r44a
2. R21-14 defer-half only + r44a

Then read `_target`'s region census under the culprit build: dump for the two top-level IfRegions
`entry / cond_block / merge_block / then_blocks / else_blocks / elif_*` and the role of the tail block,
and state in writing which precondition fails and why. Only then choose:

- (i) narrow R21-14 so `_target`'s shape is untouched (preferred — it keeps the landed risk flip), or
- (ii) broaden r44a's criterion to the new shape (only if you can show the new shape is what the
  original source means; a broadening that fires corpus-wide and moves products without moving counts
  is a red flag, see the falsified R20-4 stop-set patch).

## 2. Acceptance bar (unchanged from the round convention)

- `handlers.pyc` reads **30/30** *in the presence of the gate-30 bytes* (`fd… → 7d336164eff5bf65` is now
  HEAD's generator; do not revert it to make your criterion fire).
- `risk_calculation/__init__.pyc` stays **43/43**, `klinedata.pyc` **64/64**, `strategy.pyc` **27/27**,
  `wizard_quant_api.pyc` **58/58**, `real_quote.pyc` **45/45**, `order_api.pyc` **37/37**,
  `matcher.pyc` **17/17**, `quotation.pyc` **153/153**; `trade_info_utils 38/41`, `api_base 27/28`,
  `quote 91/92`, `realtime_event_source 12/13`, `trade_live_broker 121/128` must not decrease.
- Fire census over the 14-file panel with `cmp` against the gate-30 sealed products, reported per file.
- Judge by diff SHAPE (`delta/hunks/landings`), and prove product freshness by delete → regen → `cmp`.

## 3. Constraints

Repo read-only for measurement mirrors; only `core/cfg/region_ast_generator.py` may change;
byte-level CRLF-preserving patches; `python -X utf8`, never `PYTHONIOENCODING`; no command over 300 s;
scratch under `D:/Temp/r31/`; deliver a whole file plus `FIX_R21-23.md` (0 as-received, 1 mirror + sealed
hash proof, 2 baseline, 3 取证 with the region census under both builds, 4 criterion, 5 post-patch
readings + census, 6 negative evidence, 7 declaration).
