# FIX_R21-13 (LANDED, orchestrator-authored) — refuse the `and`-lift when the short-circuit exits disagree

**Why this document is written by me and not by the engineer.** All four round-29 engineers
(`r36a` R21-13, `r37a` R21-14, `r38a` R21-15, `r39a` R21-16) were killed mid-flight by
"You've reached your daily usage limit for Chat" after 78-119 tool uses each, before any of them
wrote a `DELIVER/FIX_*.md`. Their mirrors are the artefacts. `r36a`'s mirror contained a compiling,
non-reverted patch that I had already measured end-to-end myself, so the criterion is landed on **my
own measurements** and this file states plainly which parts of it are mine and which were the
engineer's un-finished work. No fire census from `r36a` exists — the 402-file gate is the only thing
that can certify the four panel files whose bytes changed without a count change.

## Provenance of the installed bytes
```
installed core/cfg/region_ast_generator.py  pre=ac8ec5aa2d5796ea post=e8e8a9b6b88080b9
git diff --numstat  ->  83  7  core/cfg/region_ast_generator.py      (one file, +83/-7)
py_compile OK
```
Source: `D:/Temp/r29/wt/core/cfg/region_ast_generator.py` (r36a's mirror, hash stable across ~7 min
before its process died). Whole-file install via `/d/Temp/r150/install_deliver.py`; sidecar backup
retained so this is revertible byte-exactly.

## The criterion as installed (read off the delivered hunks)
1. New method `_inline_and_chain_exits_agree(chain_blocks)` — for the blocks an
   `inline_boolop_chains[..] = {'op': 'and', ...}` record claims form a conjunction, it takes each
   leg's condition-jump target (`_cond_block_branch_targets`) and returns False as soon as the legs
   disagree. Its docstring's argument is the CPython fact I verified independently: `A and B` gives
   both legs the SAME false-exit (the "skip this arm" block), while `if A or B: arm` gives the legs
   the shared **arm entry** as true-exit — so "all leg targets equal" is a *necessary* condition of a
   real `and` chain. It reads jump targets only: it marks no `generated_blocks` and changes no block
   ownership, so it cannot move a block between regions.
2. `[R21-13 判据]` veto in `_if_generate_elif_chain`: when the analyzer record says `'and'` but
   `_inline_and_chain_exits_agree` is False, the record is discarded (`_inline_chain_info = None`)
   and the leg blocks are collected into `_r2113_legs_back`.
3. The consumption point: the arm body block list becomes
   `region.elif_bodies[0] + legs` sorted by `start_offset` (and a copy, not the original list, is
   passed to `_process_if_blocks`, with the comment noting that the no-leg case must preserve object
   identity because `_process_if_blocks` may mutate the block list in place).

Net effect: the or-chain's first leg is no longer raised into the enclosing `elif` test as a
conjunction, so the shared then-body keeps its own copy of `return None` and CPython no longer
threads that leg's exit onto a second implicit function-tail return. That is exactly the mechanism my
ticket predicted, confirmed at the instruction level before dispatch.

## Measurements I took myself, in a mirror proven to reproduce the sealed product
`D:/Temp/r30chk` (regenerated `plugin_system_risk_calculation/__init__OK.py` there was
`cmp`-IDENTICAL before any patch was installed), then whole-file candidate + `py_compile` OK:
```
wizard_quant_api  <module>.filter_desicion                     len orig=195 prod=195 delta=0 hunks=0 landings=0 judge_diff=False
real_quote        <module>.RealQuoteData.get_real_minute_kline  len orig=279 prod=279 delta=0 hunks=0 landings=0 judge_diff=False
[single] wizard_quant_api.pyc  status=success units=58/58   (was 57/58)  -> FILE FLIP
[single] real_quote.pyc        status=success units=45/45   (was 44/45)  -> FILE FLIP
quotation 153/153 | order_api 37/37 | matcher 17/17                       (unchanged, sentinel green)
api_base 27/28 | strategy 26/27 | handlers 29/30 | klinedata 63/64 | quote 91/92 |
trade_info_utils 38/41 | risk __init__ 42/43 | realtime_event_source 12/13 | broker 121/128  (all unchanged)
```
Four of those files (api_base, strategy, handlers, klinedata) change product BYTES while their unit
counts stay equal — the criterion is not byte-surgical, which is why the gate, not this panel, must
certify the other 388 files.

## Expected gate 29 reading (label 29 vs `rounds/round28/after`)
units `6598 -> 6600` of 6617, files `391 -> 393` of 402, residual `19 -> 17` units in `11 -> 9`
files, with `regen ok=402 bad=0`, `文件级回退=0`, `UNIT_REGRESSIONS=0`, `翻正单元=2`.

## GATE 29 RESULT — certified, exactly as predicted
```
[regen 合计] ok=402 bad=0        (312 s)   [verify rc=0] (180 s)
[units] 6598/6617 -> 6600/6617  (99.7431%)   [files] 391 -> 393
[gates] 文件级回退=0  UNIT_REGRESSIONS=0  新增失败单元=0  翻正单元=2
   FIXED IQCommon/strategy/wizard_quant_api.pyc <module>.filter_desicion
   FIXED IQData/plugins/plugin_system_realquote/real_quote.pyc <module>.RealQuoteData.get_real_minute_kline
   UNIT-UP wizard_quant_api 57 -> 58   |   UNIT-UP real_quote 44 -> 45
residual table rounds/round29/RESIDUAL_ROUND29.md: 单元 6600/6617 (99.7431%) 文件 393/402
残余文件 9 个 残余单元 17 条  UNREGISTERED 行数=0
```
Cheap stages vs gate 28: `quotation 153/153` (unchanged), `small34 units_success 1549 -> 1551`
(= the two flips), `selfcheck 153/153 Equal + both mutants caught`, `pytest 2 failed, 280 passed,
2 xpassed` — byte-for-byte the same reading as gate 28, so zero new failures.
Post-install batteries all reproduce their pre-install values: repro `RED=9/9`, arm `GREEN=0 RED=3/3`,
ccneg `GREEN=3 RED=1/4`, retbreak `GREEN=2 RED=2 DRIFT_VS_BASELINE=0/4` (its `r02_break_arm_control`
stays RED, as it must — this landing is not a terminator fix), orderapi `GREEN=5/5`, tail `GREEN=13/13`.
Only **two** products changed in the whole corpus (`git status --porcelain -- site-packages` =
`wizard_quant_apiOK.py`, `real_quoteOK.py`), so the criterion is byte-surgical; my earlier contrary
note was a `cmp`-against-checked-out EOL artifact and is corrected in `ADJUDICATION_R21-13_provisional.md`.
Session standing after eleven certified landings: **6586 -> 6600 units, files 390 -> 393**, every gate
reading `regen ok=402 bad=0` with zero file-level regressions.

## What happened to the other three tickets
- **R21-14** (`r37a`, risk_calculation `_save_testds_to_csv`): its mirror was reverted to sealed bytes
  at the moment it died; my 13:2x sample of its ablation (`_can_merge = True` at `:6917`, a +5-line
  experiment) had moved the victim `delta=-7 hunks=3 landings=3 -> hunks=2 landings=2` with
  `time.sleep(0.01)` still missing. No candidate. The `while True:` wrapper site is `:6917` and the
  ablation route is the one that found it — that is the reusable result.
- **R21-15** (`r38a`, klinedata loop exit) and **R21-16** (`r39a`, quote handler-suite theft):
  mirrors still pristine, no measurement to reclaim. Both tickets stay open with their byteprints.
