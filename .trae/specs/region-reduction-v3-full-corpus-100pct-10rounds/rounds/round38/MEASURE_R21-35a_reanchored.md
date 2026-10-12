# R21-35 (round 38): the re-anchored `try`-body-continue half, measured on broker

Ticket `#87`. The round-37 candidate was built on gate-36 bytes (`37997bdac555b2e9`) and had to be
transplanted onto the gate-37 landed bytes before it could be judged at all — done with the validated
span-splice harness:

```
python -X utf8 merge_hunks.py \
  --base    D:/Temp/r37/pristine_landed_generator_37997bdac555b2e9.py \
  --candidate rounds/round37/CANDIDATE_r37_R21-35a_trybody_continue_BANKED_not_landed.py \
  --current D:/Temp/r30chk/core/cfg/region_ast_generator.py \
  --out     D:/Temp/r38/CAND_r35a_on_landed.py
```
The tool reported `FAIL: 1 residual block not explained` — inspected by hand rather than trusted: the
merged file contains the candidate's single NEW block **verbatim** (`base 30228..30227 +44 →
verbatim-in-merged=True`) and `diff(landed → merged)` is exactly one `insert landed[30339:30339]
merged[30339:30383] +44`. So the refusal is the harness's marker heuristic, not an unfaithful merge;
the one unexplained block is a line of gate-37's own `[R21-36]` arm-trim, which the candidate (built
before gate 37) cannot contain. **Merged sha16 `a8155727b47e3bea`**, banked as
`CANDIDATE_r35a_reanchored_BANKED_not_landed.py`.

## What it moves, measured on the panel product (not on the unit_diff filter)

`trade_live_broker.pyc` panel index 10, tag `r38w`, unit `_process_cancel_order` via
`rounds/round38/allwin_r63.py` (which prints the windows `unit_diff.py` hides when
`min(del,ins)==0 and max<3`):

| reading | landed bytes `20fa73b4e8231f0f` | with `a8155727b47e3bea` |
|---|---|---|
| `_process_cancel_order` | `orig=333 prod=332 delta=-1 hunks=3` | `orig=333 prod=331 delta=-2 hunks=2` |
| broker file | 125/128 | **125/128 (no flip)** |

Window by window, with the instructions:

1. landed had a **spurious `JUMP_BACKWARD` @1928 emitted after `COPY @1920 / POP_EXCEPT @1922 /
   RERAISE @1924`** — dead code after a re-raise, i.e. the product's `continue` sat *after* the
   `try/except` at the enclosing level, so the handler's path also jumped back. **This window is gone.**
   That is exactly the ticket's claim (the trailing `continue` belongs inside the `try` arm), now
   proved by a window disappearing rather than by prose.
2. Two windows survive, both one instruction each, both **a `JUMP_BACKWARD` the original emits and the
   product does not**: after `CALL @1810 / POP_TOP @1820 / JUMP_BACKWARD @1824` the original also has a
   **`JUMP_FORWARD` @1826** (product lacks it), and the second copy of the same `finally` tail
   `PRECALL @1980 / CALL @1984 / POP_TOP @1994` is followed by a **`JUMP_BACKWARD @1998`** the product
   lacks.

`delta` therefore reads `-1 → -2`: the count got *worse* while the shape got *simpler* (3 mixed
windows → 2 same-class windows). This is why the campaign judges by windows + a flip, never by
`abs(delta)`.

## Why it is not the whole unit, and what the remaining two instructions actually are

CPython 3.11 duplicates the `finally` suite per exit edge of the `try`. The original's two copies are
both followed by the arm's continuation (`JUMP_BACKWARD` = the `continue`), with a `JUMP_FORWARD`
skipping the second copy on the normal path; the product emits the continuation on one copy only. So
the residual is **per-exit-edge continuation threading**, which the AST cannot express: an emitted
suite ends where the source ends it, and jump operands do not exist in the tree (the standing finding
`[[pythoncdc-no-landing-channel-in-generator]]`, confirmed by three earlier tickets). Two candidate
routes remain and neither is measured yet:

* the generator emits only ONE copy of the `finally` suite while the original emits two ⇒ a
  duplication rule (the same face that `handlers._target` was disproved for —
  see `[[pythoncdc-falsified-residual-axes]]` §35 — so this must be *measured* as a per-edge copy,
  not assumed);
* the product's second copy is in a different suite, so its `continue` became fall-through.

## Decision

Not installed: `fires without flips` — broker stays 125/128 with two files' worth of units unchanged.
Kept as the **first half** of `_process_cancel_order`, because it eliminated the only window that was
a real control-flow inversion (the jump after `RERAISE`), and the remaining two windows are the same
class of single-instruction jump, which is the cheapest residual in the whole corpus: a flip of this
unit takes broker to 126/128 and the corpus to 6614/6617.

Blast radius of `a8155727b47e3bea` over the 20-file panel (tag `r38x`, all 20 regenerated from this
mirror after a `cmp`-proved restore to `20fa73b4e8231f0f`): **5 files CHANGED, 15 SAME, every unit
count held, zero flips.**

| file | product | units before | units after |
|---|---|---|---|
| `IQCommon/api/klinedata.pyc` | 102772 → **102872** | 64/64 | 64/64 |
| `IQCommon/logger/handlers.pyc` | 9030 → **9056** | 30/30 | 30/30 |
| `IQData/plugins/plugin_system_realquote/real_quote.pyc` | 53841 → **53923** | 45/45 | 45/45 |
| `IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | 179102 → **179132** | 125/128 | 125/128 |
| `IQEngine/plugins/plugin_system_risk_calculation/__init__.pyc` | 55531 → **55569** | 43/43 | 43/43 |

The six duplicated-module canaries (`arg_checker` 49/39/43, `profiler_func` 17/15/18) are byte-identical,
so the criterion does not reach the duplicated modules. Compare with `c4a934d595200c84` (P1+P2), which
changed **one** file: this half is 5× the blast radius for 0 flips, which is why neither is installed
and why a future gate must measure them **as a pair** before either is landed with the other
(`[[feedback-pair-interaction-suppression]]`).

