# NONE.md — round64_diag1 repro attempts that did NOT reproduce

## 1. `r64d1b_sibdispatch_attempt.py` / `.pyc` — c1's sibling merge-entry dispatch (cp1 family)

**Attempt.** Three hand-written shapes intended to make an upstream `BoolOpRegion`'s
`merge_block` be the `entry` of a *same-level sibling* region which the landed
`_downstream_region_entry` dispatch refuses to release (the c1 mechanism, which on
`quote_handler.pyc :: get_kline_local` collapses
`end_time = int(end[0:8] + (end[8:12] or '1530'))` to a bare string-constant statement):

* `sib_a` — two consecutive value-context short-circuit assignments `x = t or u` / `y = v or w`;
* `sib_b` — a short-circuit assignment followed by a second one embedded in a call argument;
* `sib_c` — a short-circuit assignment whose result feeds a slice-or-default expression
  (`(e[0:8] or '1530')` then `int(...)`), the closest 3-line analogue of the real call site.

**Result — no repro:**

| arm | matched/total | defects |
|---|---|---|
| landed | 4/4 | none |
| c1 | 4/4 | none |
| c3k | 4/4 | none |

`python -X utf8 h62.py run --arm=landed --list=repro2.txt --out=dump/repro2_landed.jsonl`
(and `--arm=c1`, `--arm=c3k`), rows in `D:/Temp/opencode/r64gate/diag1/dump/repro2_*.jsonl`.

**Why it is not faked.** The landed defect needs the shared merge block `M` to be claimed by
`U` *and* to be the entry of a region that the parent's block-driven scan
(`_process_if_blocks`) subsequently skips because `M in generated_blocks`. That requires a
nested `if / elif` chain (the real site has five `elif` arms) so the parent has more than one
dispatch channel — a flat top-level function of ≤15 lines does not build that state. Producing
a "repro" here would mean copying an existing corpus file, which the 15-line limit forbids.
The real evidence for c1 remains the corpus measurement:
`get_kline_local [760,682,12,547]` present on landed, absent on c1/c3 (see `FACTS.md` §3).
A proper c1 repro is a next-round task; the shape to try is `if/elif/elif` where each arm
body opens with `x = A or B` immediately followed by a call whose argument re-tests the same
operand shape.

## 2. `realtime_event_source :: clock_worker [1275,1286,10,481]` — no repro offered

No candidate edit was authored this round (see `ANALYSIS.md` §E), therefore a repro would be
unmeasurable. New evidence gathered instead: the decompilation emits the
`elif check_trading_time(...)` arm **twice**
(`build_c3k/IQEngine__plugins__plugin_system_event_source__realtime_event_sourceOK.py`
lines 275 and 312) where the original code object has exactly one call site
(`check_trading_time` @8594, `check_handle_date` @8668) — a duplicated elif-arm emission of
~110 instructions, offset by a ~100-instruction deletion at @6690. The owning layer is the
elif-chain dispatch in `_if_generate_normal` / the R61 elif channel, i.e. a duplicate-emission
problem, not a missing-statement problem.
