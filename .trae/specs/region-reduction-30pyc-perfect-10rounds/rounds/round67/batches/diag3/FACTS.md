# Round 67 · diag3 · FACTS (read-only diagnose agent)

Workspace: `D:/Temp/opencode/r67gate/diag3`. Repo `F:/Downloads/pythoncdc-main` untouched.
All commands `python -X utf8`, no PYTHONIOENCODING.

## Step 0 — baseline replay (`--arm=landed`)  ✅ ALL THREE MATCH BRIEF

* `python -X utf8 h62.py run --arm=landed --list=targets.txt --out=dump/landed_targets.jsonl`
  (re-ran into `dump/landed.jsonl`) — 6.0 s wall, 3 files:
  - `IQCommon/api/klinedata.pyc` **42/45** `[['get_all_real_daily_kline',188,187,3,26],['get_multiminute_his_data',479,478,3,16],['kline_datetime_list',389,389,9,228]]`
  - `fly/simtradding/flyAccount.pyc` **21/23** `[['_do_request',436,443,2,384],['init_connection',42,41,0,25]]`
  - `IQData/api/api_base.pyc` **24/25** `[['get_history_df',1742,1719,14,1277]]`
  ⇒ **byte-for-byte identical to `targets.md`**. No discrepancy to stop on.
* battery (31 items) — 3.1 s: per-file readings identical to the brief's table; total matched
  **115/127**, defect functions **12**. dump `dump/landed_battery.jsonl`.
* canary (4) — 13.8 s: `quotation 143/143 sha=4d41187e356544e0`, `market_time 10/10 sha=af77224b34b203c4`,
  `IQCommon/util/datetime_func 26/26 sha=e711b8ea86d49a15`, `IQData/utils/datetime_func 25/25 sha=9d09af09249da177`.
  ⇒ **all four shas equal the brief**. dump `dump/landed_canary.jsonl`.
* strict ruler `cstrict.py build_landed targets.txt dump/landed_strict.json` — 6.3 s:
  klinedata **56/63** (7 defects), flyAccount **21/23** (2 defects: `_do_request [seq_len] 436/445`,
  `init_connection [seq_len] 42/41`), api_base **26/27** (1 defect). missing=0 extra=0 everywhere.
  ⇒ identical to `targets.md`.
* NOTE (correction/clarification of the brief): the official mismatch tuple is
  `[name, orig_count, decomp_count, jump_diffs, true_diffs]` — the 4th column is *jump diffs*,
  not "hunks". `init_connection` therefore has `jump_diffs=0, true_diffs=25` i.e. a pure
  instruction-count/ordering defect, no branch-target error.
* NOTE: battery item `round63_b5/r63b5_w1.pyc` carries the **identical** reading
  `['init_connection', 42, 41, 0, 25]` as the flyAccount defect ⇒ an accepted synthetic repro for
  that shape already exists in the battery (file `test_repros/round63_b5/r63b5_w1.pyc`).

## Step 1 — normalized hunk tables (`nhunks.py`, jump args→`J`, nested consts→`CODEOBJ`)

Tool: `python -X utf8 nhunks.py <pyc> build_landed/<OK>.py <func>`. Full detail dumps in
`dump/step1_*.txt`. `nhunks` counts differ from the official ruler because it walks *all*
code objects with that name and normalises jump args; the hunk **shape** is what matters.

| # | function | file | orig | decomp | hunks | classification |
|---|----------|------|------|--------|-------|----------------|
| 1 | `get_all_real_daily_kline` | klinedata | 216 | 214 | **1** | **MISSING** — 2 instrs absent |
| 2 | `get_multiminute_his_data` | klinedata | 535 | 536 | **2** | EXTRA +1 jump, then 1-instr displacement |
| 3 | `kline_datetime_list` | klinedata | 413 | 417 | **7** | EXTRA (4 inserts +1/+2/+4) + 2 order/cond inversions |
| 4 | `_do_request` | flyAccount | 471 | 480 | **21** | 7 × "extra 2-instr pair" + 6 × "missing const-key dict" + tail |
| 5 | `init_connection` | flyAccount | 45 | 44 | **3** | cond inversion + 4-instr missing block + 2-instr extra block |
| 6 | `get_history_df` | api_base | 1900 | 1873 | **8** | 24-instr MISSING block (dominant) |

Key literal readings (all on `--arm=landed`):

1. `get_all_real_daily_kline` — **one** hunk, `HUNK delete orig[185:187]@898(2) decomp[185:185]@896(0)`:
   the original emits an **adjacent duplicated backward jump pair**
   `EXTENDED_ARG; JUMP_BACKWARD to 86` at 894/896 **and again** at 898/900, immediately before
   `PUSH_EXC_INFO`. Verified independently by `dupback.py`:
   `get_all_real_daily_kline n=211 adj-dup-backward-jumps=[(896, 900, 'to 86')]` and
   `get_multiminute_his_data n=529 adj-dup-backward-jumps=[]` ⇒ the shape is unique to this
   function inside klinedata. Counts differ by exactly 2 ⇒ **counts unequal ⇒ real instruction loss**,
   per the brief's rule 1 this is NOT an emission-order case.
2. `get_multiminute_his_data` — `HUNK replace orig[518:519]@2708(1) decomp[518:520]@2708(2)` (decomp
   adds `JUMP_FORWARD to 2758` after the loop back edge `JUMP_BACKWARD to 1468`) plus
   `orig[533:534]@2758(1) decomp[534:535]@2760(1)` (`LOAD_FAST his_data_dict` displaced against
   `RETURN_VALUE`). `dupback.py` finds no dup-jump shape here ⇒ different root cause from #1.
   NOTE: the strict ruler sees the *opposite* sign — `[seq_len] orig=481 decomp=482` (+1) — because
   strict counts only the outermost code object. Both agree the defect is one superfluous edge.
3. `kline_datetime_list` — **counts already equal** (389/389 official, 413/417 normalised) with
   9 official `jump_diffs` and 7 substantive hunks ⇒ per the brief this is the
   **emission-order** family, not a missing attribution predicate. Signatures:
   `orig[133:133]@556(0) decomp[133:134]@558(1)` (`EXTENDED_ARG`), three further `insert(1)`/
   `insert(4)` extras, and two `replace` pairs where the original is
   `POP_JUMP_FORWARD_IF_TRUE to X | JUMP_FORWARD to X+4 | POP_TOP` and the decomp instead emits
   `POP_JUMP_FORWARD_IF_TRUE to X | <body>` — i.e. landed hoisted the `time_count -= 1` /
   `max_len_real_data -= 1` **if-body** above the `store` that the original keeps after the join
   (`orig[330:335]@1362(5) decomp[330:331]@1360(1)`, `orig[160:165]@654(5) decomp[163:165]@660(2)`).
   I attempted 13 synthetic shapes to reproduce the double-back-edge of #1 *and* this order flip
   (`synth/r67d3_lost_continue.py` c1..c4 → **all 5/5 matched on landed**, so a plain
   `while`+`if … continue` does NOT reproduce it; dump `dump/` + `scratch_cont.txt`). No repro ⇒
   no spec (rule 3).
4. `init_connection` — the whole defect is the guard inversion + tail merge, see Step 4.
5. `get_history_df` — `HUNK delete orig[1039:1063]@4982(24) decomp[1036:1036]@4970(0)`: an entire
   24-instruction block is absent, beginning
   `EXTENDED_ARG; POP_JUMP_FORWARD_IF_FALSE to 6896 | LOAD_FAST engine_obj |
   LOAD_ATTR basic_data_handler | LOAD_METHOD get_dividend | LOAD_FAST symbol | LOAD_CONST None |
   PRECALL | CALL | STORE_FAST tmp_dividends | LOAD_FAST tmp_dividends | POP_JUMP…`
   ⇒ a whole missing `if <cond>: tmp_dividends = engine_obj.basic_data_handler.get_dividend(symbol, None)`
   guard arm. Consequence: 3 further hunks are `LOAD_FAST`→`LOAD_GLOBAL` misattributions.

## Step 2 — attribution to landed bytes (re-grepped, line numbers from `--arm=landed` worktree)

* `core/cfg/region_ast_generator.py` = 50626 lines in the landed worktree. Merge-consumer sink
  block: **L35860–L35911**, the decisive 4 lines are **L35905–L35911**
  (`if _has_return_sink:` / `Return` / `else:` / `Expr`). `_has_return_sink` is computed only from
  (a) `region.merge_block` tail op and (b) a scan of `region.merge_extra_blocks` — it never
  consults `merge_block.successors`, which is the hole used by #4.
* `_apply_r23n6_return_promotion` **L47853–L47914**, its single call site **L46355**
  (`UNPACK_SEQUENCE` path), `POP_TOP` bail **L47899**; inline twin **L47787–L47848**.
  **BRIEF CORRECTION**: the brief's lead for `_do_request` ("return promotion not firing") is
  **falsified by measurement**. `probe_promo.py` wraps the method with a `sys.settrace`-free
  counter over the flyAccount run ⇒ **0 calls** on all three targets, so no repair channel exists
  through that function and any predicate there is dead code.
* Chained-container dict branch **L42195–L42275** (`_const_keys` vs `len(ternary_chain)` mixed
  mode); prefix extractor `_extract_dict_prefix_values` **L41315+**; prefix segmenter
  `_ternary_prefix_stack_effect` **L41406–L41440** (generic `if op.startswith('BUILD_'):
  return 1, instr.arg or 0` at **L41434**); the *same* generic branch also exists at **L38931** in
  `_stack_effect` (L38903–L38938) — an anchor there is ambiguous (`count==2`) unless widened.
* Field evidence for #4 via `regdump.py` + `probe_recon.py`
  (`ExpressionReconstructor.reconstruct` entry log). At the first defect site the reconstructor
  receives the slice
  `LOAD_CONST -1 | LOAD_CONST 'm' | LOAD_CONST ('error_no','error_info') | BUILD_CONST_KEY_MAP 2`
  with `initial_stack` short by one and returns `Dict(keys=2, values=1)` — the *first* value is
  clipped, so the key tuple is dropped and `BUILD_CONST_KEY_MAP` degrades to `BUILD_MAP`.
  ⇒ the fault is in **merge-consumer operand accounting**, not in the prefix segmenter.

## Step 3 — synthetic repros (≤15 lines, own list files, all measured on landed)

| repro | lines | landed reading | shape proven |
|-------|-------|----------------|--------------|
| `synth/r67d3_return_sink.py` (`probe`) | 10 | `1/2  [['probe', 38, 41, 2, 29]]`, hunks=**4** | **#4 both halves**: 7-style lost `return` AND const-key dict collapse |
| `synth/r67d3_lostreturn.py` (t1,t2) | 14 | `38/41` t1 = lost return + dict collapse; t2 (no `try`) = dict collapse only (26/25) | separates the two #4 families |
| `synth/r67d3_return_tern.py` (s1..s6) | — | `5/7`, `s2`/`s5` at −1 | self-contained const-key dict collapse |
| `synth/r67d3_lost_continue.py` (c1..c4) | — | **5/5 all matched** | **negative result**: does not reproduce #1/#3 |

Canonical C1 repro (this is the spec's designated repro):

```python
def probe(src, is_async, func, is_dict):
    try:
        if is_async:
            if func:
                return src, ({} if is_dict else [])
            return {'error_no': -1, 'error_info': 'm'}, ({} if is_dict else [])
        return 0
    except Exception:
        return None
```
compiled with `python -X utf8 mkpyc.py synth/r67d3_return_sink.py`, list
`synth/r67d3_return_sink.txt`.

## Step 4 — candidate C1 `specs/cand_r67_bare_return_sink.json` (single spec, single edit)

**Anchor** (`count==1` in LF-normalised landed text, verified with `slice.py`):

```
                    if _has_return_sink:
                        results.append({'type': 'Return', 'value': _merge_consumer_expr})
                    else:
                        results.append({'type': 'Expr', 'value': _merge_consumer_expr})
```

**识别条件** — `merge_ctx is None`, the region has no `value_target`, `merge_block` exists, the
ordinary `_has_return_sink` scan came back False, and `merge_block` has exactly **one** non-exception
successor `_r67_succ` whose *only* non-`RESUME/NOP/CACHE/PUSH_NULL` instruction is a
`RETURN_VALUE` **at that block's own start offset**, with `len(_r67_succ.predecessors) == 1` and
that single predecessor being `region.merge_block` itself; and `merge_block`'s own last core
instruction is neither a store, a jump, nor a return (it leaves the value on the stack).
**归约方式** — the bare `RETURN_VALUE` block is CPython's mandatory tail for a function that also
falls off the end; it is the *sink* of the predecessor's stack top, so the reduce step folds that
sink into `merge_block` instead of treating it as a separate statement block, and marks it
generated (`generated_blocks` / `generated_offsets`) so the normal walk cannot re-emit it.
**AST 映射** — the merged consumer expression becomes `Return(value=<merged expr>)` instead of
`Expr(<merged expr>)`; identical to the existing `_has_return_sink=True` branch, so no new AST
shape is introduced.

Prohibited inputs avoided: no function/file names, no offsets, no thresholds, no
`region.entry in r.blocks` cross-level containment, no new `self` state (only the pre-existing
`generated_blocks`/`generated_offsets` registries), and it never suppresses output — it only
re-types an already-emitted expression.

**Why the C2 family is not the fix (all measured inert, so the dict-collapse predicate stays
`候选：NONE`)** — `specs/cand_r67_bckm_stack_effect.json` (C2: `BUILD_CONST_KEY_MAP` pops `arg+1`
in `_ternary_prefix_stack_effect`), `cand_r67_c2b_only.json` (C2b: same fix in `_stack_effect`),
`cand_r67_all3.json`:

| arm | edit(s) | `_do_request` official | hunks | battery | canary |
|-----|---------|------------------------|-------|---------|--------|
| landed | — | `[436,443,2,384]` | 21 | 115/127 | 4 shas ok |
| **c1** | C1 | `[436,429,1,380]` | **14** | 115/127 | 4 shas ok |
| c2 | C2 | `[436,443,2,384]` | 21 | 115/127 | 4 shas ok |
| c5 | C2 variant 2 | `[436,443,2,384]` | 21 | 115/127 | 4 shas ok |
| c6 | C2 variant 3 | `[436,443,2,384]` | 21 | 115/127 | 4 shas ok |
| c4 | **C1+C2 pair** | `[436,429,1,380]` | 14 | 115/127 | 4 shas ok |

⇒ **alone/paired answer required by the brief**: C1 alone = `[436,429,1,380]`; C1 **paired** with
C2 = byte-identical to C1 alone (`c4` ≡ `c1` on targets, battery, canary and on all three synth
lists). C2 contributes **nothing** — the overshoot was never a stack-effect bug. Both
`_do_request` sub-defects are independent, and only the return half is fixable.

Residual after C1 (arm c1, `nhunks _do_request`: `orig=471 decomp=466 hunks=14`) is now **13
pure `BUILD_CONST_KEY_MAP` collapses + 1 tail extra**, e.g.
`HUNK replace orig[63:65]@300(2) decomp[63:64]@300(1)` over
`LOAD_CONST -1 | LOAD_CONST '异步发送失败…' | LOAD_CONST ('error_no','error_info') |
BUILD_CONST_KEY_MAP` and `HUNK insert orig[462:462]@2176(0) decomp[456:457]@2156(1)`
(`LOAD_CONST None` before the except-tail `RETURN_VALUE`). All 7 lost-`return` sites
(`POP_TOP` + `LOAD_CONST None`, 14 instrs, `orig[60:60]@292`, `orig[71:71]@314`,
`orig[257:257]@1284`, `orig[279:279]@1354`, `orig[370:370]@1798`, `orig[414:414]@2010`,
`orig[425:425]@2032`) are **gone** on c1 — that is the 21→14 delta, and it is exactly 7×2.

## Step 5 — measurements for C1 (`h62.py ab` + `cstrict.py`), three groups

* targets: `MOVED flyAccount [436,443,2,384] -> [436,429,1,380]`
  **TALLY SAME=2 IMPROVED=0 REGRESSION=0 MOVED=1 ERR=0**
  (`klinedata` and `api_base` byte-identical to landed ⇒ C1 inert on them, as intended.)
* battery (31 items): **SAME=31**, `files fully matched a=24 b=24` — no regression, no gain.
* canary (4): **SAME=4**, shas byte-identical to the Step-0 list.
* strict ruler `cstrict.py build_c1 targets.txt`: flyAccount still **21/23** but the defect
  magnitude shrinks — `_do_request [seq_len] orig=436 decomp=431` (landed: `decomp=445`);
  klinedata **56/63**, api_base **26/27** unchanged.
* synthetic repro `synth/r67d3_return_sink.txt`: landed `1/2 [['probe',38,41,2,29]]` hunks=4 →
  **c1 `1/2 [['probe',38,37,1,24]]` hunks=2**, and the two surviving hunks are
  `orig[14:15]@28(1)` and `orig[16:18]@32(2) decomp[16:17]@32(1)` — **both** const-key dict
  collapses. So the repro shows C1 erasing the return half completely and leaving only the
  unfixable half.
* Honesty note: `_do_request` **overshoots before, undershoots after** (443→429 vs orig 436), so
  the official ruler still flags it — C1 is a *MOVED* not an *IMPROVED* on the file count. It does
  strictly improve the diagnostic signal (hunks 21→14, `jump_diffs` 2→1, strict magnitude 9→5)
  with **zero** battery/canary movement, which is the landing bar the brief sets for a
  no-regression candidate; it does **not** by itself close flyAccount to full OK.

## Step 6 — per-target verdicts

1. **`IQCommon/api/klinedata.pyc` — 候选：NONE.**
   `get_all_real_daily_kline` residual is *one* missing adjacent-duplicate
   `EXTENDED_ARG; JUMP_BACKWARD to 86` pair (orig 894/896 **and** 898/900, directly before
   `PUSH_EXC_INFO`), proven by `dupback.py`. No source-level construct in `while`/`if`/`continue`/
   `try` produces it in 13 attempts (`synth/r67d3_lost_continue.py` all 5/5 clean on landed).
   CPython emits the pair only when a loop's implicit fallthrough and its explicit back edge
   collapse onto the same target inside an exception landing pad; expressing that as a
   same-level structural identity needs `PUSH_EXC_INFO` block provenance, i.e. cross-level
   containment, which is a forbidden input. ⇒ **no repro ⇒ no spec**.
   `get_multiminute_his_data` (extra `JUMP_FORWARD` after a back edge) and `kline_datetime_list`
   (equal counts, 7 order/inversion hunks) likewise resisted every shape tried; for
   `kline_datetime_list` the brief's own rule-1 note applies in reverse — counts equal but the
   surviving evidence points at an emission order decided *above* the region being reduced, and I
   could not localise a same-level predicate for it.
2. **`fly/simtradding/flyAccount.pyc` — `specs/cand_r67_bare_return_sink.json` (C1) submitted.**
   `_do_request`: returns half fixed (7/7 sites, hunks 21→14, `jump_diffs` 2→1), dict half
   **候选：NONE** — 4 predicates tried (`BUILD_CONST_KEY_MAP` stack effect in `_ternary_prefix_stack_effect`
   alone, in `_stack_effect` alone, in both, plus `c2b` variant; all inert, table in Step 4) and
   `probe_recon.py` localises the loss inside `ExpressionReconstructor.reconstruct`'s incoming
   slice, i.e. upstream of any same-level region identity.
   `init_connection`: 4-way hypothetical test on the *source* (variants A/B/C/D via `hypdiff.py`)
   shows landed output = variant **A**, and only variant **D** is byte-equal to the pyc. A→D
   requires suppressing **both** the guard/`else: break` inversion **and** the tail merge at the
   same time (A→B still 44/45, A→C still 44/45) ⇒ not expressible as one same-level predicate.
   **候选：NONE** for `init_connection`, with the note that battery item `r63b5_w1.pyc` already
   carries the identical reading, so this is a known-open shape, not a new regression.
   Net for this file: **21/23 stays 21/23**; the official gap for `_do_request` moves from +7 to −7
   while the last 14 hunks are all dict-collapse sites.
3. **`IQData/api/api_base.pyc` — 候选：NONE**, corroborating round66. The dominant defect is a
   **whole missing 24-instruction guard arm** (`… POP_JUMP_FORWARD_IF_FALSE to 6896 |
   LOAD_FAST engine_obj | LOAD_ATTR basic_data_handler | LOAD_METHOD get_dividend |
   LOAD_FAST symbol | LOAD_CONST None | PRECALL | CALL | STORE_FAST tmp_dividends | …`),
   `HUNK delete orig[1039:1063]@4982(24) decomp[1036:1036]@4970(0)`; every following
   `LOAD_FAST`→`LOAD_GLOBAL` hunk is a consequence of the dropped bindings. A "block that
   disappears entirely" cannot be repaired by a same-level identity inside the generator without
   naming the region, and the missing arm is *inside* a `while` body nested 2 levels deep ⇒
   cross-level containment (forbidden).

## Files produced (all inside the workspace; repo untouched)

`FACTS.md`, `specs/cand_r67_bare_return_sink.json` (C1, **the submission**),
`specs/cand_r67_bckm_stack_effect.json`, `specs/cand_r67_pair.json`, `specs/cand_r67_c2b_only.json`,
`specs/cand_r67_c1_c2b.json`, `specs/cand_r67_all3.json` (the latter five = measured-inert records),
`synth/r67d3_return_sink.py|.pyc|.txt` (**C1's repro**),
`synth/r67d3_lostreturn.*`, `synth/r67d3_return_tern.*`, `synth/r67d3_lost_continue.*`,
`dump/step1_{doreq_c1,initconn_landed,gmhd_landed,kdl_landed,ghdf_landed}.txt`,
`hypdiff.py`, `dupback.py`, `probe_promo.py`, `probe_recon.py`, `mkpyc.py`, `slice.py`.

