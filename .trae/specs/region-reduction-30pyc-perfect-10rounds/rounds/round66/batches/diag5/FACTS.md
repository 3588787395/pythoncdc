# Round 66 · diag5 · FACTS (read-only diagnosis)

Repo touched: **none** (reads only; `h62.py build` mirror==worktree assertion passed => no contamination).
All commands `python -X utf8`, no PYTHONIOENCODING, each < 300 s.

## Step 0 — baseline re-read on landed bytes: **ALL MATCH BRIEF**

`dump/landed.jsonl` / `dump/battery_landed.jsonl` / `dump/canary_landed.jsonl` (`--arm=landed`).

* targets 4 files: 38/40 · 12/14 · 43/45 · 51/53 with exactly the brief's mismatch lists
  (`get_trade_list 339/323 jd14 t148`, `trade_operation 304/302 jd2 t40`, `acquire 96/93 jd3 t52`,
  `write 637/637 jd4 t519`, `get_checked_time 106/106 jd0 t43`, `run_daily 77/71 jd0 t56`,
  `calculate_di 75/73 jd0 t45`, `params_analysis 133/126 jd1 t117`).
* battery 24 files: matched total **91/104**, every per-file mismatch list byte-identical to brief.
* canary 4 files: 143/143, 10/10, 26/26, 25/25 and shas
  `4d41187e356544e0 / af77224b34b203c4 / e711b8ea86d49a15 / 9d09af09249da177` — unchanged.

## Step 1 — normalized hunk tables (`nhunks.py <pyc> build_landed/<product> <fn> --ctx=3`)

### A. `scheduler::get_checked_time` 106/106 jd0 true43 — **pure relocation (missing `else:`)**
```
HUNK delete  orig[23:31]@130(8)  decomp[23:23]@128(0)     # hour,minute = divmod(minute_time,100)
HUNK insert  orig[71:71]@388(0)  decomp[63:71]@352(8)     # same 8 instrs re-emitted AFTER handlers
```
orig=122 decomp=122 instructions; only difference = the block at orig 130..166 is emitted after
the handler region instead of before it. Exception table (`dis._parse_exception_table`):
`6-128 -> 170`, `130-168 -> 436`, `170-376 -> 384`, `378-380 -> 436`, `384-432 -> 436`, …
=> the inner try's protected span **ends at 130** and block@130 is a *divmod + JUMP_FORWARD to 390*,
with handler block@378 (`POP_EXCEPT; JUMP_FORWARD to 390`) merging on the same target 390.
Verified against CPython 3.11.7 (local interpreter): `try/except/else` compiles exactly like this —
own synthetic `synth/hyp.py` gives `6 to 86 -> 128 / 88 to 126 -> 228 / …`, i.e. the **else body sits
between the protected-span end and the first handler entry** and jumps over the handlers.
Product (build_landed/IQEngine__utils__schedulerOK.py L144-160) has lost `else:` at L156.

### B. `wizard_quant_api::params_analysis` 133/126 jd1 true117 — **NOT the else family**
```
HUNK replace orig[10:11]@28(1)  decomp[10:12]@28(2)   # ORIG JUMP_FORWARD to 48  -> DECOMP LOAD_CONST None/RETURN_VALUE
HUNK replace orig[16:17]@40(1)  decomp[17:19]@42(2)   # ORIG JUMP_FORWARD to 48  -> DECOMP LOAD_CONST None/RETURN_VALUE
HUNK delete  orig[20:29]@48(9)  decomp[22:22]@50(0)   # the whole `return {dict}` merge block VANISHED
```
orig=144 decomp=137 → 7 instructions **missing**: the post-try merge block@48
(`return {'filter_type':…,'value':…,'ob_value':float(value_params)}`) is dropped and both normal
exits are materialized as `return None`. Probe: region `TryExceptRegion@12` has
`try_span=(10,28) handlers=[30]`, `else_blocks=[28]`, `_find_try_else_blocks -> [28]`,
`in_region_blocks=True` — the else machinery already fires (on the *bare jump* block, which yields
no statements); the defect is the ownership gap of block@48 (owner is the enclosing IfRegion, and
`_post_try_blocks` collection refuses foreign-owned blocks at L25385/25427). **Different predicate
needed; not covered by this round's candidate.** 候选：NONE (for this site).

### C. `fileio_utils::write` 637/637 jd4 true519 — **NOT the else family**
```
HUNK replace orig[47:56]@206(9)  decomp[47:49]@206(2)  # ORIG inline with-exit+return True -> DECOMP EXTENDED_ARG/JUMP_FORWARD to 778
HUNK insert  orig[178:178]@798   decomp[171:180]@776(9)#   … and a copy re-emitted at the end of the csv branch
HUNK replace orig[679:681]@2908(2) decomp[681:682]@2912(1)   # with-cleanup tail False/None shuffle
HUNK replace orig[692:693]@2934(1) decomp[693:694]@2936(1)
```
Probe: the single `TryExceptRegion@4` has `try_span=(0,2934) handlers=[2938]`,
`block@try_offset_end=2934`, `w11=False`; region blocks are `[…,178,208,230,…]` — there is **no CFG
block at 206/208 boundary of the shape the else rule needs** (208 is a plain body block, and it is
in_region_blocks=True). The defect is a `with`-exit/`return True` tail block hoisted to a forward
jump + duplicate, i.e. tail-block *scheduling/dedup* inside a with-region, not try-body-tail. 候选：NONE (for this site).

### D. `scheduler::run_daily` 77/71 jd0 true56 — one check only (per brief)
`nhunks` cannot even align it (`AssertionError: [72, 255]` — two `run_daily` code objects in the pyc,
so the name-keyed metric compares `run_daily@255`, 92 instrs, whose nested `func_wrapper@262` has
`co_freevars=('execution_phase','func','hour','minute','self')`). R65's cellvar/closure judgement
stands: no try-body-tail shape, and the candidate leaves it exactly as-is (unchanged in A/B). 候选：NONE.

### E. Others (`get_trade_list` 339/323 jd14, `trade_operation` 304/302 jd2, `acquire` 96/93 jd3, `calculate_di` 75/73 jd0)
Probe readings (`probe_else.py`, real line numbers of landed bytes cited in step 2):
* `get_trade_list`: two try regions, `else_blocks=[484]` / `[1734]` already detected and
  `in_region_blocks=True` → else machinery already active; residual defect is a 16-instruction
  count loss (339 vs 323) + 14 jump diffs, unrelated shape.
* `trade_operation`: single try region `entry@350 try_span=(348,1522)`, `block@1522 in_region=True w11=**False**`.
* `calculate_di`: probe produced **no TryExceptRegion output at all** (no try region) → shape cannot
  be try-body-tail; 候选：NONE.
* `acquire`: `TryExceptRegion@304 try_span=(302,354) handlers=[356]` → `block@try_offset_end=354`,
  `in_region_blocks=False`, `w11=True` — nominally the same *field* shape as A, but block@354 is a
  **bare `JUMP_FORWARD to 502`** (the try body's own tail jump, 0 statements) so the candidate's
  `_r66_estmts` is empty and nothing changes (measured: `acquire 96/93` identical in A/B).
  Its real defect is `time.sleep(self.delay)` emitted twice/elsewhere:
  `HUNK insert decomp[48:56]@302(8)` + `HUNK delete orig[87:99]@532(12)`. 候选：NONE for this round.

## Step 2 — attribution on the CURRENT landed bytes (`grep -n` measured)

* `core/cfg/region_analyzer.py`
  * `TryExceptRegion.try_offset_end` L764, `handler_entry_blocks` L765 (exception-table facts).
  * `_w11_unprotected_else_candidate` **L10360-10403** — the existing same-level structural
    identity for "CPython 3.11 unprotected try/except/else body": (1) `block.start >= try_offset_end`,
    (2) block ends with `JUMP_FORWARD` and holds no exception-framework op, (3) some handler block of
    the same try jumps to the identical target. Its docstring already states the layout fact.
  * `_find_try_else_blocks` **L10474** (called from L8695, assignment `else_blocks` L8695) — enumerates
    **only blocks already inside the region** (`try_region.blocks` / `except_handlers`), so a block at
    `try_offset_end` that the *enclosing* try claims is invisible to it. Measured: for
    `get_checked_time`'s inner `TryExceptRegion@6`, `try_offset_end=130`,
    `_w11_unprotected_else_candidate(region@6, block@130) = True` while
    `block@130 in region.blocks = False` and `_find_try_else_blocks -> []`.
* `core/cfg/region_ast_generator.py`
  * `_generate_try_body` L23558 (parent's ordered body emitter; body loop skips
    `self.generated_blocks` at L23862, `region.blocks`-based `_try_blocks_eff` build at L23808).
  * `_generate_try` L25130; `orelse_stmts = None` L25948; the existing
    `else_blocks → Try.orelse` gate L25964 + `self.generated_blocks.add(eb)` L26105;
    `try_ast` build L26382-26392; `[R65-diag1-A try-body-tail-return-none]` **L26483** (code
    L26508-26555, appends the block to `try_ast['body']`, restricted to a single-block
    `has_trailing_return_none` sibling region); post-try statement queue built L25335-25432 with the
    "每块唯一归属" foreign-owner guard at L25385/L25427/L25482 and emission L26419-26481.
  * Defect site: R65-diag1-A's identification domain (sibling BASIC region + trailing `return None`)
    is the narrow subset; the general try/except/else tail block is never claimed, so the parent's
    body loop (L23808/L23861) emits it *after* the child Try node → relocation defect of A.

## Step 3 — synthetic repro (**required, PASSED**)

`synth/r66_else.py` → `synth/r66_else.pyc` (local CPython 3.11.7), list `synth_r66.txt`:
`inner_only` = plain try/except/else (already perfect on landed), `wrapped` = the same try nested in
an outer try (the `get_checked_time` shape, 22 lines→ same as the real one).

```
landed : r66_else.pyc  2/3  [['wrapped', 43, 43, 0, 17]]     <- same signature as get_checked_time (equal counts, jd0, true-N)
cand   : r66_else.pyc  3/3  []
```
Landed product loses the `else:` (`v = v * 2` promoted to a body sibling after `except:`);
candidate product restores `else: v = v * 2`. `synth/hyp.py` holds the CPython-layout evidence.

## Step 4 — ONE spec: `specs/cand_r66_trytail_else.json`

single file `core/cfg/region_ast_generator.py`, single anchor (occurrences = **1** in the
LF-normalized text, asserted by `h62.py build`), 52 inserted lines, marker
`[R66-diag5-B try-tail-unprotected-else]`, three-part comment 识别条件/归约方式/AST 映射 present.
Predicate (same-level structural identity only): region's own `try_offset_end < min(handler_entry_blocks)`,
`Try` node with handlers and no `orelse`/`finalbody`, the CFG block whose `start_offset ==
try_offset_end` passes the analyzer's existing `_w11_unprotected_else_candidate`, block not already
generated and not in the post-try queue → statements go to `ast.Try.orelse`, block registered in
`generated_blocks` so the enclosing sequence stops re-emitting it. No name/offset/threshold match, no
`region.entry in r.blocks` containment, no emission suppression (the block's statements are emitted,
one slot earlier and inside the right node). Disjoint from R65-diag1-A by construction (that rule needs
a trailing `return None`; this one needs a `JUMP_FORWARD` terminator).

## Step 5 — measured A/B (`logs/ab_r66.txt`)

| arm | targets | battery | canary |
|---|---|---|---|
| landed | 38/40, 12/14, **43/45**, 51/53 | 91/104 | 4 files all matched |
| cand   | 38/40, 12/14, **44/45**, 51/53 | 91/104 | 4 files all matched |

```
targets AB : TALLY SAME=3 IMPROVED=1 REGRESSION=0 MOVED=0 ERR=0   (scheduler 43/45 -> 44/45,
             get_checked_time leaves the mismatch list)
battery AB : TALLY SAME=24 IMPROVED=0 REGRESSION=0 MOVED=0 ERR=0  (17 fully matched files both arms)
canary  AB : TALLY SAME=4  …  shas identical per line: 4d41187e356544e0 af77224b34b203c4
             e711b8ea86d49a15 9d09af09249da177  -> 逐支不变
```

## Step 6 — 402 full sweep (`D:/Temp/opencode/r65gate/all402.txt`, `--nshard=4 --shard=0..3`, both arms) — **MEASURED, COMPLETE**

`dump/all402_landed.jsonl` = 402 records, `dump/all402_cand.jsonl` = 402 records, per-shard logs
`logs/402_landed.log` / `logs/402_cand.log` (4 shards each, every command < 200 s).

```
python -X utf8 h62.py ab --a=dump/all402_landed.jsonl --b=dump/all402_cand.jsonl   (logs/ab_402.txt)
IMPROVED F:/…/site-packages/IQEngine/utils/scheduler.pyc  43/45 -> 44/45
TALLY SAME=401 IMPROVED=1 REGRESSION=0 MOVED=0 ERR=0  (unpaired lists=0)
files fully matched: a=385 b=385
aggregate function score: landed 5693/5746  ->  cand 5694/5746   (0 error records on either arm)
```

## Step 7 — coverage / verdict

* **Family claim from R65 is only 1/3 true (measured).** The rule covers
  `scheduler::get_checked_time` (106/106 jd0 true43 → **gone**, scheduler 43/45 → 44/45).
  `fileio_utils::write` and `wizard_quant_api::params_analysis` are **not** the try-body-tail shape
  (§1B/§1C readings: `write` has one `TryExceptRegion@4` with `try_offset_end=2934`, `w11=False`, and
  a 7-instruction *deletion* of the post-try merge block@48 in `params_analysis`; both leave the
  candidate unchanged, and no region of either file satisfies condition (1)+(2) at the defect offset).
  候选 for those two: **NONE this round** (exclusion evidence above; they need a merge-block-ownership
  predicate, not an else predicate).
* Side-effect radius on the corpus: **exactly one function changed in 402 files / 5746 functions**,
  battery 24/24 SAME, canary 4/4 sha-identical, zero regressions, zero MOVED, zero ERR.
* Also unaffected (deliberately): `fileio_utils::acquire` nominally hits the same field shape but its
  block@try_offset_end is a bare `JUMP_FORWARD` (0 statements) → the `_r66_estmts` non-empty guard
  declines, which is the correct behavior (that block is the try body's own tail jump, not an else).

## Deliverables
`FACTS.md` · `specs/cand_r66_trytail_else.json` (1 spec, 1 file, 1 anchor, occ=1) ·
`dump/{landed,battery_landed,canary_landed,cand,battery_cand,canary_cand,synth_landed,synth_cand,all402_landed,all402_cand}.jsonl` ·
`logs/{ab_r66.txt,ab_402.txt,hunks_landed.txt,probe_*.txt,402_landed.log,402_cand.log}` ·
`synth/{r66_else.py,r66_else.pyc,hyp.py}` + `synth_r66.txt` · probes `probe_else.py`.
Repo integrity: `git status --porcelain | grep -c '^ M'` = **0** (no tracked file modified; only
pre-existing untracked artifacts from earlier rounds).
