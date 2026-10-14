# MERGE RECORD — rr-v3r01-f557fd → main (integration branch `integration-main`)

Started 2026-10-14 05:15 UTC in an isolated worktree `D:/Temp/wt-merge-main`
(`git worktree add -b integration-main origin/main`), because `main` is checked out in the
user's own worktree `F:/Downloads/pythoncdc-main` — that tree and its contents were not touched.

## Topology measured before any write

| fact | value |
|---|---|
| merge-base | `088b0579a4` |
| `origin/main` | `91f8d27d` (v2 lineage, `adversarial-complete-forms-v2-10rounds`, rr-v2r03…r08) |
| branch to merge | `rr-v3r01-f557fd` `67c8cfa0` (v3 lineage, corpus 6617/6617) |
| ahead / behind | 573 ahead, 49 behind |
| conflicted files | 5 (`core/cfg/region_ast_generator.py` + 4 `*OK.py` products) |
| both-side edits of the generator | main +2839/−127, v3 +4552/−213 (since merge-base) |

`core/cfg/region_analyzer.py` auto-merged with **no** markers, as did `comprehension_generator.py`,
`pattern_parser.py`, `ast_converter.py`, `ast_generator_v2.py`. Both spec trees are present after the
merge (v2 `adversarial-complete-forms-v2-10rounds`, v3 `region-reduction-v3-full-corpus-100pct-10rounds`),
so neither 规范 was dropped.

## The four code conflicts and how each was resolved

| # | site | v2 side | v3 side | resolution |
|---|---|---|---|---|
| H1 | chained-compare `while` condition build (~8505) | `[B104-R2a]` mixed condition (chained-compare + `and` operand) composed into `ast.BoolOp` | `[R21-66]` latch-copy SEG identity set | **union** (independent definitions, both needed downstream) |
| H2 | back-edge recheck suppression (~8649) | `[B104-R2a]` widened `_is_recheck` + multi-segment STORE-boundary extractor | `[R21-66]` narrowed firing to genuine latch copies | **composed dual-route predicate, shared extractor** (see below) |
| H3 | if-branch reduction (~24121) | `[B117]` back-edge absorption guard, then plain `_if_generate_then_branch` | `[R21-15 HOIST]` + `[R21-36 r62a]` arm-tail hoist deciding the same call | **guard first, then hoist decision; the branch call kept exactly once** (v2's now-duplicated plain call dropped — not a lost improvement, it is the same call) |
| H4 | nested-region block claim (~28712) | `[B117]` do not claim a suspended loop back-edge block | `[R21-86]` do not re-claim released else-blocks | **union** (two `continue` guards in series) |

Byte discipline kept throughout: UTF-8 BOM, split on `\r\n`, every anchor asserted before writing,
`py_compile` clean, zero bare LF, zero `\r\r\n`, sha16 printed before/after
(`6654f4ca764e2d43 → 8c8edbb9f0c24279 → dd82f3d3b1251b94 → 86a1d703e5e0e53b`).

## Verification that the merge is not silently wrong

The four conflicted `*OK.py` are pipeline artifacts, so they are resolved by **regeneration**, never by
hand-merging text. After clearing markers, a no-marker scan over all 2452 staged files found 0
conflict markers, and the `.pyc` corpus inputs had to be copied into the fresh worktree
(404 copied, 405 current-magic present) because they are not materialized by `git worktree add`.

First smoke on the merged tree (merged pipeline, real judge):

| file | v3 tip | merged, first composition | merged, after H2 recompute |
|---|---|---|---|
| realtime_event_source.pyc | 13/13 | **13/13** | 13/13 |
| quote_handler.pyc | 78/79 (v2 baseline) | **79/79** | 79/79 |
| api_base.pyc | 28/28 | 28/28 | 28/28 |
| quotation.pyc | 153/153 | 153/153 | 153/153 |
| matcher.pyc | 17/17 | 16/17 ✗ | pending |
| trade_live_broker.pyc | 128/128 | 127/128 ✗ | pending |

`matcher` and `_sync_worker` were the two regressions, and a one-file-at-a-time ablation attributed
them to different sides (this is the part a textual merge review would miss):

```
arm X  merged generator + v3-tip analyzer  -> matcher 17/17 OK,   broker 127/128 STILL BROKEN
arm Y  merged analyzer + v3-tip generator  -> matcher 16/17 BROKEN, broker 128/128 OK
```

So: the **auto-merged analyzer** breaks `DefaultMatcher.match`, and the **merged generator** breaks
`TradeLiveBroker._sync_worker`. Neither is a marker-level conflict — both are semantic interactions
between v2's B-family code and v3's R21-family code.

The first H2 composition (`if _is_recheck:` / `elif latch-copy`) was measured insufficient: v2's branch
swallowed v3's narrowing, so `_sync_worker` stayed broken; the recomposed version splits the predicate
into route A (`_is_recheck` only via v2's `[B104-R2a]` operand-sequence equality) and route B
(base COPY/COMPARE test true AND tail is this loop's latch copy AND boundary is the last STORE),
sharing v2's multi-segment extractor because it generalizes v3's single-store case.

## Region bisection to name the exact interacting hunks

Differing regions vs the v3 tip: generator 125, analyzer 95. A prefix-bisection probe
(`D:/Temp/mon/bisect_merge_r125.py`, restores the merged bytes after every probe and re-hashes to
prove it) walks the region list to the smallest reverted prefix that restores each unit. Results are
appended below as measured — the two culprits are then reconciled explicitly rather than dropped, and
the merged tree is re-certified with both 规范's verification sequences (v3 gate over 402 files plus
v2's 六步: 34-集, 402 八分片 compare REGRESSIONS=0, quotation, tests 六套件, IV.2 self-check).

## Regression-detection baseline for the merged tree (measured, not assumed)

`D:/Temp/mon/v3_tip_expect_402.json` rebuilt from the sealed gate-41 shards: **402 files,
6617/6617 units, 0 non-success files**. The merged gate will be diffed against this table per file, so
every regression is named — not only the two a 6-file smoke happened to sample.

v2-side assets kept for the combined-effect validation (present in the merged tree, untouched):
`rounds/round4..round8/final_verify_run.py`, `rXvX_compare_regress.py`, `rXvX_attack.py`,
`*_full_oldface_a.json` station baselines, plus the six shared `tests/` suites (27 entries under
`tests/`), so 两规范 each get their own verification face on the same merged bytes.

## Measured reconciliation of the generator side (done) and the analyzer side (in progress)

Region-level A/B (each probe regenerates and judges, then restores the merged bytes and re-hashes):

```
revert R18 only ([B104] chain-segment suppression)  -> broker 127  => R18 is NOT the culprit
revert {[B104-R2a]} = R12,R13,R14,R15              -> broker 128  => the family is in this group
revert R12 / R13 / R14 individually                -> broker 127 each
revert R15 (the H2 conflict hunk)                  -> broker 128  => the H2 composition itself
revert [B117]                                      -> broker 127 AND quote_handler 79 -> 77
```

Two conclusions that the code alone would invite disagreement on:
* `[B117]` is **load-bearing for the merged tree** - dropping it loses two `quote_handler` units, so it
  stays (this is why "take one side" is not an option here).
* My first three compositions of the H2 hunk were each measured and each failed (`if/elif`, dual-route
  with v2's splitter, boundary conjunct, then a conditional-jump-count conjunct: all still 127/128).
  The product diff then showed the actual failure: the composition rebuilt the block as STORE segments
  and collapsed an inner `if` -

```
  time_difference = abs((datetime.datetime.now() - self.sync_account_time).total_seconds())
  if time_difference > sync_max_time:
      sync_data_flag = 1
```
  into a single unconditional `sync_data_flag = 1`.

Final composition, generator `f81a931ffe641ccd`: v3's hunk restored **verbatim** from the v3 tip
(10 lines), and v2's `[B104-R2a]` route appended as a strictly additive `elif` that (i) is evaluated
only when v3's branch did not fire, (ii) keeps v2's own `_cc_mixed_tails or _cc_mixed_leads`
precondition, (iii) computes a local sequence-equality boolean instead of assigning `_is_recheck`, and
(iv) keeps v2's multi-segment extractor for the shapes only v2 recognised. Measured after the change:
`trade_live_broker 128/128`, `realtime_event_source 13/13`, `quotation 153/153`,
`quote_handler 79/79`, `klinedata 64/64`. Only `matcher` (16/17) remains, and it is an analyzer-side
interaction: the merged analyzer hoists three assignments out of the nested block where v3 emits them
in place (`stock_listed_date / next_trading_date / is_first_five_trading_days`), so that hunk is being
localized by the same region A/B over the analyzer's 95 v2 hunks.

Byte discipline held for every step: BOM present, `bareLF=0`, `CRCRLF=0`, `py_compile` clean, and the
chain of generator hashes is `6654f4ca -> 8c8edbb9 -> dd82f3d3 -> 86a1d703 -> 84d9c474 -> aaec80a2 ->
7d7c22d4 -> f81a931f`.

## Measured reconciliation of the analyzer side (done)

The matcher casualty was a **two-hunk** interaction, not one hunk. Diff-region numbering is against the
v3 tip analyzer `996a1b1acf143458` (95 differing regions); the behavior carriers were region **81**
(v2 `[B99 fix]`, the ternary refusal at `_identify_ternary_regions`) and regions **72/73/74** (v2
`[B104]`, the `protected` narrowing in `_identify_chained_compare_regions`; 70/71/75 are docstring-only).

Four-arm truth table on `matcher.pyc` (target 17 units), `ana_ab3_r137.py`:

| `[B99 fix]` | `[B104]` | matcher | product loss (diff vs the 17/17 arm) |
|---|---|---|---|
| merged (narrowed) | merged (released) | 16/17 | 3 assignments hoisted out of the loop body |
| v3 tip (absent) | merged (released) | 16/17 | same hoist |
| merged (narrowed) | v3 tip (blanket) | 16/17 | `if symbol[:3] == '300' and ...:` + its two arms dropped |
| v3 tip | v3 tip | **17/17** | — |

So **each** v2 hunk alone costs the unit; reverting both equals the v3 tip and discards v2's work.

Whether v2's hunks are load-bearing was decided by a battery on the shapes v2's own comments name
(`nested_battery_r140.py`, 4 sources x 4 arms, judge = `pyc_verify single --source <fresh product>`):
`nb_for` (for-body `if 0 < i < 10 < i*2:`) 1/2 under blanket, 2/2 under released; `nb_with` (with-body
chain in an `if` test) 1/2 → 2/2; `nb_b99` (loop-body `return self.a or self.b`) 3/4 without the guard,
4/4 with it. Both hunks are therefore kept. `nb_while` (`while 0 < x < n < 100:`) reads 1/2 in **every**
arm, so it is not merge-caused — registered as an uncovered form, not a regression.

Discriminator found by census (`cc_census_r141.py`, read-only wrapper around
`_build_chained_compare_region`): matcher's new chain head `@1696` ends `JUMP_IF_FALSE_OR_POP`
(i.e. `SHORT_CIRCUIT_JUMP_OPS` = **value** context), while `nb_for @34` / `nb_with @32` end
`POP_JUMP_FORWARD_IF_FALSE` (**condition** context). This is exactly the pre-existing `[Round4-04]`
law in this file: a value-context chained compare belongs to the host statement's
`_generate_value_context_chain_compare_assign` route, not to a standalone chained-compare region.

Two gates, each reusing an existing criterion rather than minting a new one:

1. `[B104-R3]` (`region_analyzer.py`, in `_identify_chained_compare_regions`): a `released` set is built
   as the *difference* the narrowing newly opens (for/async-for body blocks minus that region's
   structural boundary members, plus `WithRegion.with_blocks`). A chain head inside `released` whose
   last instruction is in `SHORT_CIRCUIT_JUMP_OPS` is skipped. Blocks outside `released` keep v3's
   behavior bit-for-bit, and condition-position heads keep v2's coverage.
2. `[B99 fix]` narrowed to the two preconditions its own comment states: the owning BoolOpRegion must
   be value-context (`not getattr(region, 'is_condition_context', True)`, same idiom as the file's
   `[B99 残]` / `[Phase 7]` clauses) **and** the block must not be a chained-compare header
   (`_is_chained_compare_header`). Counterfactual `cf_b99_r143.py`: deleting the guard gives
   matcher 17/17 but `nb_b99` 3/4, so it was narrowed, not dropped. The value-context conjunct alone
   measured 16/17 (matcher's chain head is itself registered into a value-context BoolOpRegion — the
   mis-registration `[Round4-04]` documents), which is why the second conjunct is required.

Readings after both gates: matcher 17/17, broker 128/128, realtime_event_source 13/13, quote_handler
79/79, quotation 153/153, and the v2 target battery `nb_for` 2/2, `nb_with` 2/2, `nb_b99` 4/4.
Analyzer hash chain: `c26ee206af0e2a0d -> 129bb0332df3601e -> b4fb55ad2b663f96 -> 3bf5f401614fa8e0`.

## Gate 42: the merged tree certified against BOTH specs' faces

Regenerated all 402 products from the merged bytes with the pipeline itself (`gate_round.py 42 41
--stage regen` → `ok=402 bad=0`), then judged them (`--stage verify`). 7 products changed versus the
v3 tip's committed bytes; none lost a unit.

| face | reading |
|---|---|
| v3 gate 42 vs round41 | units 6617 → **6617/6617 (100.0000 %)**, files 402 → **402**, 文件级回退=0, UNIT_REGRESSIONS=0, 新增失败单元=0 |
| residual table (`residual_report.py 42 41`) | 残余文件 0、残余单元 0、UNREGISTERED=0 |
| v2 baseline (`baseline_snapshot.md` 6554/6617、369/402) | units 6554 → **6617**, files-success 369 → **402**, **REGRESSIONS=0**, 33 files improved (join overlap 402/402 verified first — an all-MISS join would have read as zero) |
| quotation | 153/153 (v2 baseline was 152/153) |
| small34 | units 1568/1568, 34/34 files success (v2 baseline 1505/1568) |
| ruler selfcheck | 153/153 Equal, deform arms bite 1/153 (常量 and 极性) → judge not softened |
| pytest 7 suites | 2 failed / 282 passed / 2 xpassed, failing names verified BY NAME = `test_B01_simple_if_then_else_merge`, `test_BOUNDARY_02_large_function` = the registered baseline roster ⇒ 0 new failures |

## v2's own round-8 variant battery re-run on the merged pipeline

`test_repros/round8/*.pyc` are gitignored, so the probe sources were re-compiled with the same
interpreter (3.11.7) and judged with `pyc_verify single --source <fresh product>`
(`D:/Temp/mon/v2_battery_r145.py`):

- `b105_walrus` 5/5, `b107_iso` 5/5, `b107_iso2` 4/4, `b107_mtarget3` 6/6, `bmatch_v3` 2/2,
  `bmatch_or3iso` 5/5, `bmatch_v1` 2/2 (size 266), `bmatch_v4` 2/2 (size 222) — identical to v2's
  recorded readings, including the product byte sizes.
- `bmatch_guards_battery` / `bmatch_nestnoguard` hang the regenerator; v2's own evidence
  (`r8v8rev3_battery_rerun_bmatch.json`) already records them as `REGEN_TIMEOUT(>120s) HANG`, so this
  reproduces v2's state rather than adding to it.
- **`b104_chain4_battery` 4/6 where v2 recorded 6/6.** The two red units are `<module>.v2`
  (`while 0 < x < 10 and flag:`) and `<module>.v4` (`while 0 < x < 10 < x*2 < 100:`). Attributed:
  the v3 tip pipeline reads **2/6** on the same probe (it also loses `v1` and `v5`), so the merge
  restores 2 of the 6; and my two reconciliation gates are provably inert here — four arms
  (both on / each off / both off) produced the *same* product sha `fe532cc741fb`
  (`attrib_r148.py`; the first attempt `attrib_r146.py` was VOID because its labels contained `:`
  so no product file was written and every arm re-graded a stale artifact).
  Mechanism, read off the product: the while-condition chain's back-edge recheck copy is emitted as
  a body statement (`if 0 < x < 10:` / `if 0 < x and 10 < True and x*2 < True: ... elif 10 < True
  and x*2 < True:`) instead of being suppressed as a pure recheck. This is the while-host
  chained-compare family (`[B104]`'s `while 条件位` note routes it to `_identify_loop_regions`'s
  pre-loop chain backtrace plus the generator's recheck suppression, both of which v3 reworked in
  `[R21-65]`/`[R21-66]`). Registered as the merge's one open residual on v2's syntax face; the
  402-file corpus does not exercise it, and no v2 rule was deleted to obtain the current readings.
