# FIX_R21-1 — clock_worker body swallowed inside loop (realtime_event_source 12/13 -> 13/13)

Engineer: `r21a`. Ticket owner brief: lead (measured 2026-10-10).
Mechanism scope: `core/cfg/region_ast_generator.py` ONLY.
`region_analyzer.py` and `ast_generator_v2.py` are READ-ONLY for this ticket.
Repo (read-only): `D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main`, branch `rr-v3r01-f557fd`, HEAD `2cb9a195`.

## Sections (this doc is appended live; criterion section must never be blank)
1. mirror build proof
2. Stage 1 baseline
3. signature re-verification (claim-site census)
4. 判据实现 (exact file:line + predicate)
5. stage readings
6. 负面证据
7. final declaration

## 1. mirror build proof

sealed core hashes re-read from repo (sha256 first-16):
```
4f295dfc6ebd2caa  core/cfg/region_ast_generator.py
beeaf14435e22922  core/cfg/ast_generator_v2.py
640d33a77dcb71c2  core/cfg/region_analyzer.py
```
(to be filled: per-file mirror-vs-repo cmp table, pristine/ copy, product regen cmp)

Mirror built at `D:/Temp/r21a/wt` from HEAD `2cb9a195`. Per-file sha256 first-16 repo vs mirror:

| file | repo | mirror | verdict |
|---|---|---|---|
| core/cfg/region_ast_generator.py | 4f295dfc6ebd2caa | 4f295dfc6ebd2caa | MATCH |
| core/cfg/ast_generator_v2.py | beeaf14435e22922 | beeaf14435e22922 | MATCH |
| core/cfg/region_analyzer.py | 640d33a77dcb71c2 | 640d33a77dcb71c2 | MATCH |
| core/cfg/cfg_builder.py | 2b1d8ad934c5b750 | 2b1d8ad934c5b750 | MATCH |
| pycdc.py | cf4e2705ab042732 | cf4e2705ab042732 | MATCH |
| scripts/pyc_verify.py | fe1902a90cebd4a1 | fe1902a90cebd4a1 | MATCH |

`diff -rq --exclude=__pycache__` over `core/` and `scripts/` = **tree-identical**.
Pristine copy kept at `D:/Temp/r21a/pristine/region_ast_generator.py`.
Six battery dirs + `unit_diff.py` copied with `cp --parents -r` at identical relative depth;
proof the depth is right: `run_repro.py` self-reports `ROOT=D:\Temp\r21a\wt` (not the live repo).
`site-packages/` (pyc inputs, taken from the repo) copied in so 7-level resolution lands on the mirror.

Committed-product regen proof: mirror-regenerated
`site-packages/IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc`
into `D:/Temp/r21a/out/base_realtime_event_source.py` (3.7 s) and `cmp` against the repo's
`realtime_event_sourceOK.py` -> **byte-identical** (`VICTIM_PRODUCT_MATCHES_REPO_OK`).
No product was ever written into the repo; all products live in `D:/Temp/r21a/out`.

## 2. Stage 1 baseline (UNPATCHED mirror)

Judged only with `python -X utf8 scripts/pyc_verify.py single <pyc> --source <fresh product>`.
Panel log: `D:/Temp/r21a/out/panel_base_stage1.log`.

| file | mirror Stage 1 | brief | drift |
|---|---|---|---|
| realtime_event_source | 12/13 | 12/13 | 0 |
| quote | 87/92 | 87/92 | 0 |
| klinedata | 63/64 | 63/64 | 0 |
| handlers | 29/30 | 29/30 | 0 |
| wizard_quant_api | 55/58 | 55/58 | 0 |
| trade_info_utils | 38/41 | 38/41 | 0 |
| api_base | 27/28 | 27/28 | 0 |
| real_quote | 43/45 | 43/45 | 0 |
| strategy | 26/27 | 26/27 | 0 |
| risk_calculation `__init__` | 42/43 | 42/43 | 0 |
| trade_live_broker | 118/128 | 118/128 | 0 |
| **sentinel** quotation | **153/153** | 153/153 | 0 |
| **sentinel** matcher | **17/17** | 17/17 | 0 |
| **sentinel** order_api | **37/37** | 37/37 | 0 |

Batteries (all from the mirror): `repro` 9R/9 · `arm` 0G/3R · `ccneg` 3G/1R ·
`retbreak` 2G/2R `DRIFT_VS_BASELINE=0` · `orderapi` 5G/0R · `tail` 13G/0R (after `make_tail.py --run`).

**No drift anywhere — the unpatched mirror is a faithful Stage-1 baseline.**

## 3. signature re-verification (claim-site census)

Recording `generated_blocks` subclass (`RecordingSet(set)` overriding `add`, writer line = innermost
frame inside `region_ast_generator.py`), swapped into the generator instance whose `cfg.code.co_name ==
'clock_worker'`, driven in-process through the production path `pycdc.decompile_pyc(...)`.
Probe proven inert: `PRODUCT_LEN=20027` == the unpatched product string length, and after revert the
mirror-regenerated product is byte-identical to the repo's `realtime_event_sourceOK.py`.

- `TOTAL_CLAIM_ADDS = 1272` -> **matches the lead's census exactly (no drift)**.
- **`distinct_blocks_claimed = 191` and `CFG_BLOCKS = 191` -> EVERY block of this code object is
  claimed.** There is no membership gap at all; the defect is 100% emission-side.
- Victim claim-site census (how many sites claim each victim block):
  - `@6690` (IfRegion entry, `if holiday_not_do_before == '0'`) — **11 adds / 10 distinct sites**:
    `_generate_block_statements_body:53495`, `_process_if_blocks:25706`, `_process_if_blocks:26059`,
    `_loop_handle_child_region_entry:14040`, `_if_generate_normal:21181`,
    `_r58_collect_break_target_stmts:6572`, `_generate_loop:5378` (**twice**),
    `_loop_generate_body:8372`, `_generate_try_body:28578`, `_generate_try:31595`.
  - `@6702` (its then-body) — 6 adds / 6 sites: `56764, 26613, 6572, 5378, 28578, 31595`.
    Note the asymmetry: `@6702` is **not** claimed by `21181/_if_generate_normal` nor by `8372`.
  - `@6778` (`self.before_trading_date = now_date`, the IfRegion merge) — 5 adds: `56764, 26613, 5378, 28578, 31595`.
  - `@7270` / `@7980` (the other two hunks) — 7 and 8 adds respectively (`19366/14040/5378/8372/28578/31595`
    and `21303/25385(x3)/14040/5378/8372/28578/31595`).
  => Confirms the prior lesson: a victim block is claimed at the region site **and** at its callers,
  so un-marking anywhere is undone. Only emit-side mechanisms can matter here.

Region anatomy of this code object (`RegionAnalyzer(cfg).analyze()` -> 67 regions, read-only):
`LoopRegion entry=5598` is declared **twice**:
- `r2`: 100 blocks, `has_break=True`, `break_blocks=[6690]`, **29 children incl. IfRegion@6690/7972/8294** —
  the one the generator walks; `6690 in r2.blocks == True` but `6690 in r2.body_blocks == False`.
- `r3`: 103 blocks, `break_blocks=[9214]`, children `[r2]`, `condition_block=None`;
  `r3.blocks - r2.blocks == {6702, 6778, 9214}`.
`{6702, 6778}` are exactly the two blocks of the first swallowed hunk.

Source-line anatomy of the three content hunks (`co.co_lines()`, decisive):
- `@6690..@6776` = source lines **442/444/445** and `@6778..@6782` = line **449** — misplaced, not lost
  (re-emitted at hunk 4 `orig[1393..1395 @@9210] prod[1265..1282] del=2 ins=17`).
- `@7270..@7308` = source line **473** (`system_log.debug('获取重登信号量')`) — genuinely absent.
- `@7972..@8586` = source lines **498,499,500,501,502,504,507,508,509,511,512,515,516,517,518,519,520,521,522,524**
  — 20 **distinct** lines, i.e. real source, **NOT** CPython per-exit-edge duplication. Genuinely absent.

## 4. 判据实现 (exact file:line + predicate)

File: `core/cfg/region_ast_generator.py` (only). Site: `_r58_collect_break_target_stmts`, guard at
**`:6546-6547`** (the `if bb in body_set or bb.start_offset in processed: continue` line; verified
**unique in the whole 59559-line file** — duplicate-count = 1).

Predicate installed (5 added lines, anchor content + index asserted before write, CRLF preserved):

```python
            # [R21-1] membership-is-inside: a break target that is a member block of
            # this loop is emitted INSIDE the loop node (unique membership), never
            # hoisted into the post-loop sequential tail.
            if bb in region.blocks:
                continue
```

Rationale (same-region, same-level fact; one-way; no retrospective repair; no cross-region/cross-level
read): `region.break_blocks` contains `@6690`, `@6690 in region.blocks` is True, yet `body_blocks`
(97 of the 100 members) excludes it, so the r58 collector hoists the whole `IfRegion@6690` — plus the
`_r58` successor walk over `@6702/@6778` — into the statement list appended **after** the loop node
(claim site `:6572`, i.e. `for b in bb_region.blocks: self.generated_blocks.add(b)`).
Probing `_generate_region` confirms it is called for `IfRegion entry=6690` **from
`_r58_collect_break_target_stmts:6564`** and from nowhere else.

**Status: NOT landed — the predicate does not flip the unit and makes delta worse (-113 -> -117).
Reverted; the delivered file is byte-identical to the sealed bytes.** See sections 5 and 6.

## 5. stage readings

Baseline (Stage 1) — see section 2, all 14 panel files and 6 batteries at recorded values, zero drift.

Candidate `v1` (`:6546` membership guard), mirror, victim only:

| metric | pristine | candidate v1 |
|---|---|---|
| `len orig/prod` | 1424 / 1311 | 1424 / 1307 |
| `delta` | **-113** | **-117** |
| `hunks (--all)` | 7 | 7 |
| hunk1 `@@6690 del=17` | present | present, unchanged |
| last hunk `del=2 ins=17` | ins=**17** | ins=**13** |
| judge | 12/13 | 12/13 (no flip) |

Product bytes changed (`cmp` differs at byte 17838 / line 291), so the probe was not inert-free of
effect — the 4-instruction **decrease** proves the hoisted content is partially lost, not relocated.

Post-revert certification of the mirror (must equal Stage 1 exactly):
`region_ast_generator.py` sha16 back to `4f295dfc6ebd2caa`; regenerated victim product
`cmp`-identical to the repo's `realtime_event_sourceOK.py`; judge with `--source`:
victim **12/13**, sentinel `quotation` **153/153**.

## 6. 负面证据

1. **No membership gap is possible as an axis**: all 191 CFG blocks are claimed (`distinct_blocks_claimed
   = 191 = CFG_BLOCKS`), 1272 adds. Any "block is in no region" premise for this unit is dead.
2. **The tail-jump/merge axis is dead for a fourth time**: `r2.break_blocks == [6690]` while
   `6690 ∉ r2.body_blocks` and `r3.blocks - r2.blocks == {6702, 6778, 9214}` — the duplication of
   `LoopRegion@5598` is an analyzer-side declaration, unreachable from the generator, and
   `region_analyzer.py` is out of scope for this ticket.
3. **Neutralizing the r58 hoist loses content instead of relocating it** (delta -113 -> -117):
   `@6690` is inside `region.blocks` but outside `region.body_blocks`, and the loop-body renderer walks
   `body_blocks`, so once r58 declines, no emitter ever reaches `@6690`. Emit-the-remainder at this site
   requires the body renderer to be membership-complete — a second mechanism.
4. **The dominant hunk never reaches the region generator at all.** Wrapping `_generate_region` and
   logging the victim entries yields calls only for entries
   `6582, 6548, 7706, 8666, 7582, 7164, 6690, 5598(x2)`. Entries **`7972, 8294, 8350, 8400, 8450, 8186,
   7270, 7216, 7634` are never passed** — although `IfRegion@7972`, `IfRegion@8294`, `TryExceptRegion@8186`
   are declared children of `r2`. So hunks 2 (6 instrs, line 473) and 3 (109 instrs, lines 498-524) are a
   branch-arm / elif-chain reachability defect in `_process_if_blocks`, independent of hunk 1.
5. **Hunk 3 is not a duplication fold**: its instructions span 20 distinct source lines
   (498-524), so the "CPython per-exit-edge duplication" explanation (already disproved for
   `handlers._target`) does not cover it either — the source text is genuinely missing.
6. Three mutually independent emission defects (misplaced r58 hoist, `body_blocks`-completeness,
   `_process_if_blocks` arm reachability) must all close for `clock_worker` to be Equal. One ticket,
   one mechanism cannot flip it; consistent with the ledger note that T12-11's -113 -> -6 also did not flip.

## 7. final declaration

**NO LANDING. The delivered `region_ast_generator.py` is byte-identical to the sealed bytes**
(`4f295dfc6ebd2caa`, equal to `core/cfg/region_ast_generator.py` at HEAD, `cmp` clean).
Verdict for R21-1: **FALSIFIED-but-supporting** — `clock_worker` stays at `delta=-113` and
`realtime_event_source.pyc` stays at **12/13**; my criterion did not close the hunk chain
(it moved `-113 -> -117`, i.e. strictly worse, with zero flips), so the ticket's bar is not met
and nothing is installed.

- Deliverable: `D:/Temp/r21a/DELIVER/region_ast_generator.py`
  sha256 first-16 `4f295dfc6ebd2caa` — identical to the sealed baseline;
  `diff` changed-line count vs pristine = **0** (the tested candidate is banked separately at
  `D:/Temp/r21a/out/CANDIDATE_r21a_v1_region_ast_generator.py`, changed-line count vs pristine = **5**).
- `py_compile` proof: `python -X utf8 -m py_compile DELIVER/region_ast_generator.py` -> OK (and the
  patched candidate compiled OK before revert, so the -117 reading is a valid measurement, not a crash).
- Revert command actually used (byte-exact, already in effect):
  `cp /d/Temp/r21a/pristine/region_ast_generator.py /d/Temp/r21a/wt/core/cfg/region_ast_generator.py`
  then `rm -rf /d/Temp/r21a/wt/core/cfg/__pycache__`.
- Post-revert certified: victim product `cmp` == repo `realtime_event_sourceOK.py`; judge (with
  `--source`) victim **12/13**, sentinel `quotation` **153/153**. Panel/batteries unchanged from Stage 1
  because the mirror file is byte-identical to the Stage-1 file.
- Repo integrity: no `git` writes, no `*OK.py` written into the repo, the 402-file gate was never run.
  `git status --short core/` shows only `M core/cfg/region_analyzer.py`, which is **another engineer's
  (r20u) in-flight work, not mine**; my scoped file `core/cfg/region_ast_generator.py` is clean.

### Drift noticed (reported as instructed)
- HEAD moved during this session from `2cb9a195` to `d380960c3adf7508` ("round22: land r20u's F2/F1
  analyzer fix (+1 unit) and certify gate 22"); the sealed `region_ast_generator.py` hash is unchanged
  (`4f295dfc6ebd2caa`), so my baseline and mirror stay valid. `region_analyzer.py` is dirty in the tree;
  it is read-only for this ticket and I never touched it.
- Every number quoted in the brief re-measured with **zero drift**: `claim-adds=1272`,
  `len orig=1424 prod=1311 delta=-113`, first hunk 17 instrs at `@6690`, `_generate_ternary:46121`
  absent from all victim claim sets, all 14 panel readings and all 6 batteries.

### Next-ticket pointer (from section 6, evidence-based, not a proposal I tested)
The 109-instruction hunk (source lines 498-524) is the dominant term and its owning regions
(`IfRegion@7972`, `IfRegion@8294`, `TryExceptRegion@8186`) are **declared children of `LoopRegion@5598`
(r2) but are never passed to `_generate_region`** — the arm renderer in `_process_if_blocks` resumes at
`IfRegion@8666` after the inner `for` loop. That is one reachability defect inside `_process_if_blocks`
covering hunks 2 and 3 (115 of the 113 net missing instructions); the `-113 -> -6` partial win of
T12-11 is consistent with someone having already touched the smaller one.
