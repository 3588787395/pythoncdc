# R30-B diagnosis — source-level nesting attribution of an IfRegion join block

Scratch: `D:/Temp/r30diagB` (nothing in `F:\Downloads\pythoncdc-main` was modified; no git
write commands were run). Core read = landed commit `06f0ba50` (contains R29-A).
Harness: `D:/Temp/r30diagB/r30.py` (copy of `r29gate/r29.py`, ROOT moved). Tools written
here: `strict1.py` (strict ruler per arm/function), `fdump30.py`, `ddump30.py` (index/offset
windows, orig-vs-product in parallel), `odump30.py` (original bytecode window), `mv30.py`
(moved-vs-lost), `mkspec30.py` (candidate specs), `mkp30.py` / `mkp30b.py` / `mkp30c.py`
(stamp mirrors `mirr_p30a` / `p30b` / `p30c`), `mkrepro30.py` (synthetic battery),
`strictdiff.py`, `mkwindow.py`.

## 1. Measured table — both targets on the landed core

| target | official ruler | strict ruler | first divergence (aligned idx, real offsets) | moved-vs-lost |
|---|---|---|---|---|
| `site-packages/fly/dumpload/load_daily.pyc :: <module>` | `23/23`, `mism=[]` | file `clean=22/25 sigma=0 seqlen=0`; `<module>` **`target_diff` #596** `JUMP 终点 orig=('None','PUSH_NULL') decomp=("'filedump'","LOAD_CONST")` | no token divergence at all (`non-equal blocks: 0`, 913/913). The single differing slot is index **#596 @2454**: orig `JUMP_FORWARD 2478` vs product `JUMP_FORWARD 2562` (`ddump30 --i=586,606`) | neither: same instruction, same offset, same op — **jump-target attribution only**. The join body @2478..@2560 is emitted in the right order and at the right place in the sequence, but *inside* the `else:` arm, so the then-arm tail jump skips past it to 2562 |
| `test_repros/round29_arm_shared_join_claim/r29x_01_module_if_deficit_witness.pyc :: <module>` | `4/5`, `mism=[['<module>',142,138,2,122]]` | file `clean=4/5 sigma=6 seqlen=1`; `<module>` **`seq_len` 144/138** (strict filtered lengths; the official 142/138 is its unfiltered twin) | 3 non-equal blocks. H1 `replace orig[16:23] @32..44 → decomp[16:17] @32` = `LOAD_CONST 0 / STORE_NAME total / LOAD_NAME payload / JUMP_IF_TRUE_OR_POP 46 / LOAD_CONST 1 / LOAD_CONST 2 / BUILD_LIST 2` (7) collapsed to `LOAD_CONST None` (1) → **LOST, 6 instrs, only 1/7 of the run reappears** | H2/H3 `delete orig[76:82] @224..246` ↔ `insert decomp[114:120] @354..376`: `JUMP_FORWARD→248 / PUSH_NULL / LOAD_NAME print / LOAD_CONST 'ERROR: nothing to do' / CALL 1 / POP_TOP` → **MOVED 6/6, verbatim, to the end of the then arm** |

Landed-core strict rows for the other two functions of `load_daily`
(`api_get_from_zeromq #86`, `filter_abnormal_data #15`) are pre-existing, unrelated
target_diffs (they also carry `target_diff` on every candidate arm — see §4).

### Original CFG of the load_daily region (from `odump30`, offsets not names)
```
#228 @702 POP_JUMP_FORWARD_IF_FALSE ->740         # outer if (condition line 559)
     @704..@738  then body; @738 JUMP_FORWARD ->2562
#249 @740  else body begins (print 开始执行时间) … contains
#301 @952 POP_JUMP_FORWARD_IF_NONE ->2456         # *** our region: entry block = @740
     @954 … #657 @2454 JUMP_FORWARD ->2478        # THEN arm tail: unconditional jump INTO 2478
#658 @2456 print("ERROR:…")  #663 @2476 POP_TOP   # ELSE arm tail: FALLS THROUGH into 2478
#664 @2478 print('++++++结束更新的执行时间…')      # JOIN J, ends #681 @2560 POP_TOP
     @2562 JUMP_FORWARD ->2626                     # stub, ALSO the target of @738
     @2564 PUSH_EXC_INFO …                         # except handler (J's 2nd successor)
#709 @2626 continues                               # = the merge the region is built with
```

## 2. Emission / attribution chain, by stamp

Probe `mirr_p30a` = landed core + 3 structural stamps (P1 before the R29-A guard at
`region_analyzer.py:17890`, P2 after it, P3 before the per-arm sorted walk at
`region_ast_generator.py:20392`). Each mirror self-proves
`delete-stamps == worktree bytes` and compiles.

`load_daily :: <module>` — P1 fires exactly once in the whole 98-file window:
```
[R30P1]  cfg=<module> entry=740 merge=2626 shared=[2478, 2562]
         else=[2456, 2478, 2562]
         then=[954,1072,1116,1096,1112,1254,1278,1338,1442,1556,1702,2198,1932,2022,2478,2086,2176,2562]
[R30P1b] shared@2478 last=2478@POP_TOP->2560 preds=[2198, 2456] succs=[2562, 2564]
         predlasts=['2198@JUMP_FORWARD->2454', '2456@POP_TOP->2476']
```
Chain, line by line (probe `p30c` on `load_daily` gives the two bracketing readings):
```
[R30E0] ENTRY cfg=<module> entry=740 merge=2626 then=[954,…,2022,2478,2086,2176,2562] else=[2456, 2478, 2562]
[R30Q0] BASIC cfg=<module> entry=740 merge=2626 shared=[] then=[954,…,2022,2086,2176]  else=[2456, 2478, 2562]
       (E0 = first statement of _build_basic_if_region, :17511; Q0 = just before `region = IfRegion(`, :17903)
```
1. The double claim exists **at the input of `_build_basic_if_region`** (E0): 2478/2562 arrive
   already inside both lists, so no line of this function adds it — it is produced by
   `_collect_branch_blocks` in `_identify_conditional_regions` (same fact was reached at the
   construction side last round by probe `p29d`).
2. `region_analyzer.py:17661-17705` — the *existing* shared-block filter ("merge=None时的共有块
   过滤") is the only code in this function that removes a join from **both** arms and sets
   `merge = min(real_merge …)`. It is gated `if merge is None and then_blocks and else_blocks:`
   (17668) → here `merge=2626`, so it never runs. **This is the line that "keeps it there".**
3. `region_analyzer.py:17890-17893` (R29-A) prunes `then_blocks` only — by construction it
   cannot touch the `else_blocks` copy, so `else=[2456, 2478, 2562]` is what the region is
   built with (`p29d`'s D2 already showed the generator consumes the same sets unchanged).
4. `region_ast_generator.py:20392` `_process_if_blocks` walks the else arm sorted by
   `start_offset` → 2456, 2478, 2562 ⇒ the join statement is printed inside `else:` and the
   then-arm terminator jump is emitted to the *end of the else body* (2562) instead of the
   join (2478). That is exactly the `target_diff #596`.

`r29x_01 witness :: <module>` — **P1 never fires** (0 hits, and the probe is proven live: it
fires on `load_daily` in the same build and the ungated twin probe `p30c` fires on
`c30ctl_01`). Probe `mirr_p30c` (entry state + all three `region = IfRegion(` sites,
ungated) shows the witness's outer region is assembled *correctly*:
```
[R30E0] ENTRY cfg=<module> entry=0 merge=248 then=[32,40,46,48,50,196,64,88,160,100,124,128] else=[226]
[R30Q0] BASIC cfg=<module> entry=0 merge=248 shared=[] then=[32,48,196]              else=[226]
```
i.e. merge=248 *is* the join print, no arm shares a block, and the else arm is just [226].
Blocks 40/46 (`LOAD_NAME payload` + `JUMP_IF_TRUE_OR_POP`, the `for row in (payload or [1,2])`
short-circuit) are pruned out of the then arm *inside* `_build_basic_if_region` between the
entry state and the construction (they end up owned by a boolop/ternary absorption), and the
then-arm block @32 then generates as `for row in None:` with `total = 0` dropped. So the
witness's mis-nesting (its MOVED hunk) is a **downstream consequence of a different state**:
an or-chain absorbed out of a for-iter header, not an arm-shared join. R30-B does not touch
it (measured: §4).

## 3. Candidate R30-B (ranked, single recommendation)

**R30-B1 — arm-shared join block is claimed by neither arm** (removal-only).
* Anchor file:line: `core/cfg/region_analyzer.py:17890` (`if then_blocks and else_blocks:`),
  i.e. **the same line the landed R29-A sits on**, immediately above it; it therefore also
  sits beside the existing guards `if merge is None and not else_blocks and then_blocks and
  len(then_blocks) >= 2:` (17850, "IF_THEN merge 候选识别") and
  `if merge is None and then_blocks and else_blocks:` (17668, shared-block filter), which is
  the *merge-is-unknown* twin of this predicate — it already performs
  "drop from both arm lists + `merge = min(shared, key=start_offset)`".
* Predicate, structural only:
  `merge is not None` (the region already has an exit) AND both arm lists non-empty AND
  `J = { b : b ∈ set(then_blocks) ∩ set(else_blocks), b has ≥1 predecessor inside the then
  list, ≥1 predecessor inside the else list, and b is not a two-way conditional block
  (len(b.conditional_successors) != 2) }` is non-empty ⇒
  `then_blocks ∖= J`, `else_blocks ∖= J`. Block identity/ownership, successor/predecessor
  relations and terminal-op class only; `start_offset` is used only as an ordering key, as in
  the already-landed 17702.
* Kind: **removal-only**, no emission-side rule, no new region, no merge change.
* Fallback when it does not fire: today's behaviour byte-for-byte (R29-A still prunes the
  then arm; if `J` is empty nothing changes at all).
* Landing artifact: `D:/Temp/r30diagB/spec30b3.json` (build with `python -X utf8 r30.py build
  --spec=spec30b3.json --dst=b3` → `mirr_b3`, products in `build_b3/`; `spec30b1.json` /
  `spec30b2.json` are the looser variants). The measured patch is **+14 / −0** at
  `region_analyzer.py:17890`, CRLF preserved, no BOM in this file. **Land this form (R30-B3 =
  B1 + "both arms stay non-empty" self-protection):**

```python
        # R30-B3 = R30-B1 加「两臂摘后仍非空」的自保护：取消汇合块的双重认领不得把
        # 某条臂清空（清空会使 region_type 由 IF_THEN_ELSE 退化为 IF_THEN、`else:` 消失）。
        if merge is not None and then_blocks and else_blocks:
            _r30_then = set(then_blocks)
            _r30_else = set(else_blocks)
            _r30_join = {b for b in _r30_then & _r30_else
                         if any(p in _r30_then for p in b.predecessors)
                         and any(p in _r30_else for p in b.predecessors)
                         and len(b.conditional_successors) != 2}
            _r30_t_keep = [b for b in then_blocks if b not in _r30_join]
            _r30_e_keep = [b for b in else_blocks if b not in _r30_join]
            if _r30_join and _r30_t_keep and _r30_e_keep:
                then_blocks = _r30_t_keep
                else_blocks = _r30_e_keep
```

  Measured: B3's products are byte-identical to B1's on all 98 window files, i.e. the extra
  self-protection is inert here and costs nothing; without it a hypothetical region whose
  else arm *is* exactly the join would silently lose its `else:`. Nothing else in the mirror
  differs from the landed bytes.
* Measured effect (see §4): load_daily `<module>` `target_diff → CLEAN`, strict file
  `clean 22/25 → 23/25`, sigma 0 both sides, official `23/23` unchanged, and **exactly one
  line of the product changes** — the join print dedents out of `else:` to the parent level.

**Does the parent really emit a block that no arm claims?** Yes — *measured, not assumed*:
with the join dropped from both lists the region's product still holds all 913 filtered
instructions (`mism=[]`, official 23/23) and the strict ruler reports `<module>` **clean**,
which requires the join body `PUSH_NULL … CALL 1 … POP_TOP` at 2478..2560 to be present *and*
the then-arm terminator to be `JUMP_FORWARD → 2478` (`ddump30`: `d#596 @2454 JUMP_FORWARD 2478
== o#596`). The parent's sequential walk (`_process_if_blocks`/module sequence) picks the
unclaimed block up after the whole `if/else`.

**`merge_block` re-point is NOT needed.** R30-B2 = B1 + `merge := min(J by start_offset)`
was built and measured: over the whole 98-file window the two arms' products are **byte
identical** (`ab --a=win_b1 --b=win_b2` → `SAME=98 MOVED=0`). The arm-terminator target is
derived from the next emitted block, not from `merge_block`, so the re-point is inert here and
touches cross-region exit semantics. Land **B3 = B1 + the non-empty-arms guard** (B2 is kept
only as evidence that the merge pointer is not the lever).
(Round 29's arm-design chose "don't change merge" for the same reason.)

## 4. Trigger-surface sweep on a bounded window (no full-402 A/B)

Window = `anchors96.txt` (96) ∪ `reprobat38.txt` (38, all 38 are already inside the 96) ∪
`load_daily.pyc` ∪ `r29x_01…pyc` = **98 unique .pyc**. Baseline arm = `landed`
(`D:/Temp/r30diagB/win_landed.jsonl`), candidates `win_b1.jsonl`, `win_b2.jsonl`; logs
`win_*.log`, stamp log `win_p30a.err`.

| A/B | SAME | IMPROVED | REGRESSION | MOVED | ERR |
|---|---|---|---|---|---|
| landed → **B1** | 97 | 0 | **0** | 1 (`load_daily.pyc`, `gained=[] lost=[]`, both `23/23`) | 0 |
| landed → **B2** | 97 | 0 | 0 | 1 (same file) | 0 |
| landed → **B3** (recommended) | 97 | 0 | **0** | 1 (same file) | 0 |
| B1 → B2 | **98** | 0 | 0 | 0 | 0 |
| B1 → B3 | **98** | 0 | 0 | 0 | 0 |
| landed → B1 on the 11 new synthetics (`rp_landed.jsonl` / `rp_b1.jsonl`) | 11 | 0 | 0 | 0 | 0 |

Strict ruler over the same 98 files (`strict1_landed.json` / `strict1_b1.json`,
`strictdiff.py`): landed `funcs=346 clean=306 sigma=310 {target_diff 4, seq_len 34,
seq_diff 2}` → B1 `clean=307 sigma=310 {target_diff 3, …}`; **exactly one verdict changes**,
`load_daily.pyc :: <module> target_diff → CLEAN`, and no verdict worsens. So B1 is
official-neutral (the ruler is blind here by construction) and strictly *improving* on the
strict ruler, with a one-file footprint.
State-level trigger surface: `[R30P1]` (arms sharing a block at construction) fires **1 time
in 98 files** — the predicate's precondition is essentially unoccupied elsewhere.
Does it change the official reading anywhere? **No** (0 IMPROVED / 0 REGRESSION / 0 MOVED of
counts; `load_daily` was already 23/23 and stays 23/23).

## 5. Synthetic repro sketches + controls (compiled AND measured)

All 11 files were written and compiled in `D:/Temp/r30diagB/repro30/` (never in the repo),
decompiled with the landed core and with B1, and checked with BOTH rulers
(`rp_landed.jsonl`, `rp_b1.jsonl`, `strict1_landed.json` for the earlier run):

triggers tried: `v30a_01_try_outer_inner_join` (try/except + outer if/else + inner if/else +
post-if print — load_daily's exact skeleton), `v30a_02_no_try`, `v30a_03_inner_only`,
`v30a_04_func_ctx`, `v30a_05_join_is_call_and_store`, `v30a_06_join_is_loop`,
`v30a_07_else_arm_multi_block`.
controls: `c30ctl_01_plain_if_else_post`, `c30ctl_02_arm_ends_in_return`,
`c30ctl_03_shared_conditional_join` (two arms converging on a *conditional* block — the
`conditional_successors != 2` exclusion), `c30ctl_04_elif_chain_post_stmt`.

Honest result: **all 11 are official-clean AND strict-clean on the landed core
(`clean=N/N sigma=0`) and byte-identical under B1; the P1 state never fires for any of them.**
So a corpus-independent *positive* repro of this defect family was again **not obtained** —
consistent with Round 29's finding (the double claim arises from the *original* corpus
bytecode layout: a jump-stub block that is also a jump target from outside the region, plus
an exception edge, plus a long multi-block then arm; recompiling any source of mine yields a
layout the analyzer claims correctly). The value of these 11 is as **non-trigger anchors** for
the battery, in particular `c30ctl_03` (must keep matching: guards against widening the
predicate to conditional join blocks) and `v30a_01` (closest structural mimic: guards
against a future widening that would start pruning legitimate arm-tail blocks).
`r29x_01` is the only corpus-independent failing file, and §2 shows it fails for a *different*
state, so **no candidate in this line can flip it** — it belongs to the for-iter/or-chain
cluster (Round 28 family, cluster C of Round 29's line-B taxonomy).

## 6. measured vs inferred; rejected clusters

Measured in this session (mirrors + both rulers + stamps): §1 numbers for both targets, the
offset windows and the jump slot #596 (`ddump30`/`odump30`), the moved-vs-lost verdicts
(`mv30`), the P1/P1b state and its 1-in-98 trigger rate, the p30c entry-vs-construction lists
for the witness, B1/B2 builds and their 98-file + 11-synthetic A/B and strict tallies, the
one-line product diff, and the byte-identity of B1/B2.
Inferred (not measured): (a) *why* `_collect_branch_blocks` over-collects 2478/2562 upstream —
measured only that the state is already present at `_build_basic_if_region`'s first statement
(E0), not which line of the caller built it; (b) that the join print would survive in *every*
possible context (only the 98-file window + the 11 synthetics were walked, not the full 402);
(c) the exact filter that prunes the witness's blocks 40/46 — measured that ENTRY(12 blocks)
⊃ construction(3 blocks) inside `_build_basic_if_region`, so the pruning is in that function
(17782-17840 region), but the individual line was not stamped.
Rejected clusters — do not pick these for this residual:
1. **Widening the 17668 `merge is None` shared-block filter to `merge is not None`** (i.e.
   editing an existing landed guard in place). It also runs the `elif_candidates` branch and
   clears `merge` semantics for regions where the current merge is already right; the same
   effect on the witness target is obtained by the additive predicate above with a measured
   1-file footprint. Do not touch 17668.
2. **Setting `merge_block` to the join and relying on the merge exit** (R30-B2): measured
   inert (identical bytes), and it re-points a cross-region pointer — extra risk, zero gain.
3. **Emission-side fixes in `_process_if_blocks`** (e.g. "when a block in this arm is also the
   fall-through successor of the sibling arm's tail, defer it"). The analyzer's block lists
   would still double-claim, so every other consumer of `region.else_blocks`
   (`_if_generate_then_branch`, `_merge_block_is_then_exclusive`, the elif-chain paths) keeps
   the wrong view; the 20392 walk is only the last one to observe it. Also precedent
   (`_fis_skip_blocks`, "F-GET_ITER fix") shows this codebase already dislikes arm-list
   surgery at emission time.
4. **The `r29x_01` witness as "the same shape"**: measured not the same shape (P1 never
   fires; its outer region is built with merge=248 = the join, and its damage is the
   `for row in (payload or [1, 2])` header collapse `LOST 6` + the resulting relocation).
   Chasing it here will not flip it; it needs an or-chain/boolop-ownership predicate.
5. **The other load_daily strict target_diffs** (`api_get_from_zeromq #86`,
   `filter_abnormal_data #15`) and the three same-cluster corpus files from Round 29's A-cluster
   with non-neutral counts (`events 510/491`, `match 713/689`, `clock_worker 1275/1291`):
   they are different/overlapped shapes; B1 leaves all of them untouched (0 changed verdicts
   in the window).
6. **Exception-epilogue inlining** (Round 28 hand-off: `function.pyc 14/15`,
   `flytools.pyc 64/65`) — emission-side, unrelated to arm ownership.
