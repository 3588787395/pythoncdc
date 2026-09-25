# R67 diag2 FACTS (live log, appended as measured)

Workspace: D:/Temp/opencode/r67gate/diag2  · Repo read-only. Arm `landed` = current worktree (R66 bytes).

## 0. Baseline replay (--arm=landed)

**MATCHES BRIEF EXACTLY - no divergence, proceeded.**

| arm=landed list | reading | vs brief |
|---|---|---|
| targets.txt | quote 70/81 (11 OFF), common_func 23/24 ([handle_exrights,276,268,1,263]), matcher 16/17 ([match,715,715,10,517]) | IDENTICAL to targets.md, all 3 rows |
| battery.txt (31) | sum matched **115/127**, 12 defect fns | IDENTICAL, per-pyc mismatch rows byte-same |
| canary.txt | 143/143 sha=4d41187e356544e0; 10/10 af77224b34b203c4; 26/26 e711b8ea86d49a15; 25/25 9d09af09249da177 | all 4 shas unchanged |

Runtime: targets 5.3s, battery 2.1s → full-corpus 402 not needed (and not run, per brief).
Dumps: `dump/landed.jsonl`, `dump/landed_battery.jsonl`, `dump/landed_canary.jsonl`.

## 1. Normalized hunk tables (nhunks.py, J/CODEOBJ-normalized)

### 1a. `IQData/utils/common_func.pyc :: handle_exrights` — RESOLVED (brief's label corrected)

nhunks(ctx=0), landed: `orig=304 decomp=297 hunks=4`
```
HUNK insert   orig[2:2]@2(0)    decomp[2:3]@4(1)      EXTENDED_ARG (relocation noise)
HUNK replace  orig[6:15]@12(9)  decomp[7:8]@14(1)     alignment artifact
HUNK delete   orig[16:24]@64(8) decomp[9:9]@16(0)     8 instrs: LOAD fields;PJNF;LOAD real_data;
                                                       JUMP;LOAD real_data;LOAD fields;BINARY_SUBSCR;RETURN
HUNK insert   orig[304:304]@1542(0) decomp[289:297]@1474(8)  the SAME 8-instr shape at the product tail
```
**Correction to the brief / round66 OUTCOME §6 record.** `handle_exrights` is NOT a tail-relocation and NOT
"无可落地判据". The ORIG contains the ternary return **exactly once** (`disf.py`: offsets 64..86, source
line 458; the function then ends at 1540/1542 `return real_data_tmp`). The product contains it exactly once,
at its own tail (1474..1496). nhunks matched the two *different* occurrences against each other, which fakes
a relocation and makes the loss look like a move. Reconstructed ORIG source shape from `disf.py` 2..62:
```
2  LOAD_FAST tmp_dividends;  4 POP_JUMP_IF_FALSE  -> 64
6  LOAD symbol; 8 LOAD tmp_dividends; 10 CONTAINS_OP(not in); 12 POP_JUMP_IF_TRUE -> 64
14 LOAD_GLOBAL len; 26 LOAD tmp_dividends; 28 LOAD symbol; 30 BINARY_SUBSCR; 44 CALL;
   54 LOAD_CONST 0; 56 COMPARE_OP ==; 62 POP_JUMP_IF_FALSE -> 88
64..86  return real_data if fields is None else real_data[fields]     <- body of a 3-operand OR guard
88      dividends = tmp_dividends[symbol]   ...   1540/1542 return real_data_tmp
```
i.e. `if not tmp_dividends or symbol not in tmp_dividends or len(tmp_dividends[symbol]) == 0: return <ternary>`
— a **3-term short-circuit guard whose last operand CPython emits with inverted polarity**. Landed lost the
third operand and rendered `if tmp_dividends and symbol in tmp_dividends: <body>` + tail ternary.
Also corrected: the "twin" `IQCommon/util/common_func.pyc` does **not contain `handle_exrights`** at all
(built on landed this round: 21/21, `def handle_exrights` absent) — it is not evidence for this function.

### 1b. `IQEngine/.../matcher.pyc :: match` — relocation confirmed, untouched this round
`orig=800 decomp=809 substantive-hunks=4`:
```
HUNK insert orig[168:168]@1064(0) decomp[168:169]@1066(1)            EXTENDED_ARG noise
HUNK delete orig[207:519]@1320(312) decomp[208:208]@1320(0)         312 instrs absent in place
HUNK delete orig[644:648]@3952(4) decomp[333:333]@2062(0)
HUNK insert orig[798:798]@4962(0) decomp[483:807]@3060(324)         324 instrs at the product tail
```
Confirms the on-record emission-ORDER diagnosis (orig 1320..2460 -> decomp 3060..4900). New measurement for
the next round: region ownership is **complete** — 49 regions, exactly ONE top-level region
(`probe_r67.py`: `LoopRegion entry=6 parent=TOP`, blocks cover the whole function; every other region is
`parent=LoopRegion@6`). So there is no top-level flush order to fix; the mis-ordering is inside the
generator's child ordering / linearisation of that single loop body. C1 does not move matcher at all
(product bytes identical landed vs c1).

### 1c. `fly/data/quote.pyc` — hunk classification of all 11 official-OFF functions (ctx=0, landed)
| function | hunks | key hunk(s) | class |
|---|---|---|---|
| build_current_period_df | 2 | replace orig[109:121]@516(12->2); delete orig[3:4]@14(1) | 缺语句 (tail) |
| check_frequency | 2 | replace (2->1)@456; insert (0->2)@562 | 多语句 +2 |
| check_limit | 1 | delete orig[54:76]@286(22) | 缺语句 22 instrs |
| get_individual_data | 4 | delete orig[178:206]@968(28) + insert decomp[325:350]@1730(25) | **纯换位** 28->25 |
| get_price | 1 | replace orig[66:67]@326(1->3) | 多语句 +2 |
| get_real_from_zeromq | 8 | delete (24)@192; delete orig[161:191]@872(30) + insert decomp[737:767]@3924(30); 4 small | 换位 30 + 缺语句 24 + 碎片 |
| initImagedata | 1 | delete orig[38:60]@204(22) | 缺语句 22 instrs |
| load_bars_from_hundsun | 1 | insert orig[49:49]@256(0->7) | 多语句 +7 (过冲; = R66 §7.3 os.path.exists 裸表达式) |
| load_get_price | 1 | replace (1->1)@282 | 终点/常量槽 (strict #53) |
| run_individual_transform | 11 | deletes 7@640, 8@686, 21@1130, 22@2204; insert 9@1304; 4 replaces | 混合，主体缺语句 |
| run_tick_socket | 4 | delete orig[93:117]@528(24) + insert decomp[205:230]@1120(25) | **纯换位** 24->25 |

Two quote functions (`get_individual_data`, `run_tick_socket`) and one `get_real_from_zeromq` fragment carry
the *same* "equal-size block deleted early / re-inserted later" signature as matcher::match — i.e. 3 more
relocation witnesses for whoever picks up the linearisation channel. The pure-loss families
(`check_limit` 22, `initImagedata` 22, `run_individual_transform` 7+8+21+22, `get_real_from_zeromq` 24) are
NOT the C1 shape: C1 leaves quote byte-identical (measured, both rulers).
Strict-only residuals (official-blind, all unchanged under c1): `change_his_to_backward #213`,
`change_his_to_forward #241` (R25 canary-class residual — deliberately not touched),
`check_industry_code #159`, `load_get_price #53`, `run_tick_transform #135`.

## 2. Attribution on LANDED bytes (re-grepped this round; R66 line numbers not reused)

`core/cfg/region_analyzer.py` (27763 lines), inside `_identify_conditional_regions` (def **L15757**),
candidate loop `for block in blocks_in_reverse:` (reverse start_offset order, per its own Step-1 docstring):

* **L16376** `if isinstance(block_region, BoolOpRegion) and block_region.entry == block:` — the arm block@0
  takes. At **L16448-16451** it sets `condition_block = block_region.op_chain[-1][0]` and
  `chain_blocks = set(b for b, _ in block_region.op_chain)` — the if-condition is rebuilt from the
  BoolOpRegion's `op_chain`, which for this guard holds only 2 of the 3 short-circuit links.
* Because `chain_blocks` is then non-empty, the whole **L16495 `if not chain_blocks:`** section — which
  contains the Round-33/R13c or-short-circuit chain walk (**L16610-16740**; DBG prints at 16705/16715) —
  is never reached for this block. Measured: block@0's trace runs 16440..16451 then jumps to 16791.
* **L16521-16606** (inside `if not chain_blocks:`) is the R13c "or-chain member" test. block@14 reaches
  **L16601** `if _or_walk_has_false_tail:` -> `continue` at **L16606**: it is skipped *because* it is claimed
  to be a chain member the head will reduce — its own docstring at L16518 says exactly that
  ("由链首块的 or 链检测统一归约（chain_blocks 覆盖，每块唯一归属）").
* Net: the third test block is skipped as somebody else's member while the head's `op_chain` never absorbed
  it, so 每块唯一归属 fails in the losing direction; the guard's third operand is dropped, and
  `TernaryRegion@64` (the guard body) stays `parent=TOP` and is flushed after `IfRegion@0`, which
  coincidentally re-uses the correct else slot and hid the loss behind a fake relocation.

Evidence (all <5 s, reproducible): `probe_r67.py <pyc> <fn>` (parentage), `dbg_r67.py <pyc> <fn> 14`
(sys.settrace line trace over `_identify_conditional_regions`), and the analyzer's pre-existing
`DBG_OR` env hook (set inside my own probe process only — no repo write, no PYTHONIOENCODING):
```
[DBG_OR] boolop chain start skipped (or member): block=14 last=POP_JUMP_FORWARD_IF_FALSE
[DBG_OR] or-chain member skip: block=14 last=POP_JUMP_FORWARD_IF_FALSE pred_ft=64
[DBG_OR] region-build: cond=0 condition_block=6 then_succ=14 else_succ=64 merge=64 then=[14,88,160,162,176] else=[] chain=[0, 6]
[DBG_OR] region-built: type=IfRegion rt=RegionType.IF_THEN then=[14,88,160,176] else=[] cond=[]
```
Landed parentage (`probe_r67.py handle_exrights`, and identically on the synthetic):
`IfRegion@0 parent=TOP blocks=[0,14,88,...]` , `BoolOpRegion@0 parent=IfRegion@0 blocks=[0,6]`,
`Region@14 parent=IfRegion@0 blocks=[14]`, `TernaryRegion@64 parent=TOP blocks=[64,68,72,86]`.

## 3. Synthetic repro (step 3) — `synth/r67_guard_tern.py`, list `synth/r67_guard_tern.txt`
```python
def f(d, k, v):
    if not d or k not in d or len(d[k]) == 0:
        return v if k is None else v[k]
    acc = d[k]
    for i in range(len(acc)):
        acc = acc + i
    return acc
```
8 lines. `disf.py` offsets 2..86 are structurally identical to the real prologue (2,4,6,8,10,12,14,26,28,
30,40,44,54,56,62,64,66,68,70,72,74,76,86 — same opcodes, same jump targets). Landed reading:
`1/2 [['f', 42, 34, 1, 35]]` — same signature as `handle_exrights [276,268,1,263]` (8-instr shortfall,
1 hunk); landed product = `if d and k in d:` + tail ternary, third operand lost; landed parentage identical
to the target's (`Region@14` + top-level `TernaryRegion@64`).
NEGATIVE CONTROL (worth recording): the 7-line first attempt modelled the same source as *nested* ifs
(`if d and k in d:` / `if len(d[k]) == 0: return <ternary>`) decompiled **cleanly 2/2** on landed. The
**flat 3-term `or` guard** is essential to the repro.

## 4. Candidate spec — `specs/cand_r67_orchain_tail.json` (arm `c1`)
One file, `core/cfg/region_analyzer.py`, `edits` length 1. Anchor = `cand/a1.txt`, the 3 landed lines at
L16448-16451; verified `count==1` in the LF-normalised landed bytes (also asserted by `h62.py build`).
Replacement = `cand/r1.txt` = those 3 lines + a block-level extension that undoes the redirect when the
link's fall-through is the chain's **inverted-polarity tail operand**:
* 识别条件 (same-level block fields only): let `L` = `op_chain` 末段 (= new `condition_block`), `X` = the
  offset in `L`'s trailing conditional jump (the chain's shared short-circuit exit). Walk `L`'s normal
  successors (excluding `exception_successors`, excluding `X`) to `T`. Fire iff (a) `T not in chain_blocks`,
  (b) `T`'s last instruction is a conditional jump whose opname contains IF_FALSE with non-None argval,
  (c) that argval != `X`, (d) `T`'s own normal fall-through successor (same exclusion) starts exactly at
  `X`. Nested `if A and B: if C:` cannot fire: the inner test's fall-through is the then body, not `X`.
* 归约方式: reset `condition_block = block` / `chain_blocks = set()` so the existing single or-chain walk
  reduces `[head..L..T]` into ONE BoolOp abstract node and redirects condition_block to the real branch
  point (restores 每块唯一归属; no new emitter, no suppression, no second pass).
* AST 映射: `If(test=BoolOp(Or,[seg1,...,tail]), body, [])`, tail operand keeps CPython's inverted-polarity
  last-operand emission (`COMPARE_OP` + `POP_JUMP_IF_FALSE` -> continuation).
No function/file names, no offsets, no thresholds in the predicate; no `region.entry in r.blocks`
cross-region containment input; frame-local `_r67_*` names only (no new `self` state). One `DBG_OR`-guarded
print is included, matching the 12 pre-existing DBG_OR sites in the same function (inert unless env set).

## 5. Measurements (`--arm=c1` vs `--arm=landed`)
`h62.py build --spec=specs/cand_r67_orchain_tail.json --dst=c1` -> "mirrors built: head pristine == worktree
bytes, cand patched (1 edits, core/cfg/region_analyzer.py, BOM=False, nl=CRLF)".

| list | ab tally landed->c1 |
|---|---|
| targets.txt (3) | **IMPROVED=1 SAME=2 REGRESSION=0 MOVED=0 ERR=0**; files fully matched a=0 **b=1** |
| battery.txt (31) | **SAME=31 IMPROVED=0 REGRESSION=0 MOVED=0 ERR=0**; fully matched a=24 b=24; total **115/127 unchanged** |
| canary.txt (4) | **SAME=4 REGRESSION=0**; all 4 shas byte-identical (4d41187e356544e0 / af77224b34b203c4 / e711b8ea86d49a15 / 9d09af09249da177) |
| wit.txt (quote + klinedata, mandated BoolOp witnesses) | **SAME=2 REGRESSION=0 MOVED=0** |

Per-target:
* `IQData/utils/common_func.pyc` official **23/24 -> 24/24**, strict **26/27 -> 27/27** (missing=0 extra=0)
  => **FULL OK ON BOTH RULERS** (round-closing condition met). Defect list now empty on both scales.
* `fly/data/quote.pyc` official 70/81 -> 70/81, strict 74/89 -> 74/89, product bytes identical.
* `.../matcher.pyc` official 16/17 -> 16/17, strict 16/17 -> 16/17, product bytes identical.
* synthetic `f` official **1/2 -> 2/2**; product text now equals the source form
  `if not d or k not in d or len(d[k]) == 0: return v if k is None else v[k]` (no spurious `else`).
* `IQCommon/api/klinedata.pyc` official 42/45 -> 42/45, strict **56/63 -> 56/63** — the historical
  BoolOp-chain-pop klinedata -2 cost is NOT incurred; `quote` witness strict 74/89 unchanged, official
  70/81 unchanged.
* Byte-level closure: of the 40 product files present in both `build_landed` and `build_c1`, exactly **2**
  differ (`...synth__r67_guard_ternOK.py`, `IQData__utils__common_funcOK.py`); the other 38 corpus
  products are byte-identical, which is a stronger statement than any per-ruler tally.

Tool note for the centre: `cstrict.py` cannot read **test_repros** products — it builds the product name
with `p.split('site-packages/')[-1]` while `h62.py` names those files `F___Downloads__...OK.py`, so
`cstrict.py build_<arm> battery.txt` returns 31 `no product` rows on BOTH arms (identical, so it never
falsifies anything). Battery strict equality was therefore proven by the byte comparison above instead of
by the strict ruler. Not a candidate issue.

## 6. Per-target verdicts

### 6.1 `IQData/utils/common_func.pyc :: handle_exrights` — **候选：C1 (`specs/cand_r67_orchain_tail.json`)** — MEASURED FULL OK
Official 23/24 -> **24/24**, strict 26/27 -> **27/27**, zero regressions anywhere, canary shas byte-identical,
quote + klinedata BoolOp witnesses byte-identical on both rulers. This is the round-closing result
(one pyc full OK on both rulers) and it is also a strict corpus improvement with zero regressions
(IMPROVED=1, REGRESSION=0, MOVED=0 over 38 corpus products of which 38-1 stayed byte-identical).

### 6.2 `IQEngine/plugins/plugin_system_matcher/matcher.pyc :: match` — **候选：NONE this round**
Measured readings that show why:
1. It is an emission-ORDER defect, already proven and re-confirmed by nhunks (312-instr delete @orig 1320
   paired with a 324-instr insert @decomp 3060, product length equal-ish, official counts 715/715).
2. **Ownership is not the problem** — `probe_r67.py` measured 49 regions with exactly ONE top-level region
   (`LoopRegion@6`) whose block set covers the function; there is no orphan and no second top-level region,
   so the only "ordering" lever the analyzer offers (top-level region order / flush) is empty. The brief's
   instruction not to re-litigate ownership is therefore *confirmed*, not merely assumed.
3. **The analyzer's child order is already correct** — measured: `LoopRegion@6.children` has 48 entries,
   **0 inversions** against ascending `entry.start_offset` ([10,114,546,...,3968]). So the reversal is
   introduced downstream, inside `RegionASTGenerator`'s statement assembly for that one loop body, not in
   `region_analyzer`.
4. The relocated span is exactly the CFG range ORIG jumps *over*: ORIG `1320 EXTENDED_ARG /
   1322 JUMP_FORWARD -> 2464`, and `IfRegion@1068.blocks` skips from 1320 straight to 2464, while
   `IfRegion@1324 blocks=[1324,1372,...]` .. through 2460 are separate siblings of the loop. So CPython
   laid the chunk out of flow order and the generator re-serialises it last.
5. C1 does not move it (product bytes identical landed vs c1, official 16/17, strict 16/17 unchanged), and
   a second spec is out of scope for this agent ("交一份 spec"), so no candidate is submitted for matcher.
   Next-round entry point named: the loop-body statement linearisation in
   `core/cfg/region_ast_generator.py` that consumes `LoopRegion.children`, not the analyzer.

### 6.3 `fly/data/quote.pyc` — **候选：NONE this round** (per-function classes measured in §1c)
1. 11 official-OFF + 4 strict-only residuals; C1 leaves every one of them **byte-identical** (official
   70/81 -> 70/81, strict 74/89 -> 74/89), so no residual on this file is the short-circuit-tail shape.
2. The residuals split into three unrelated families, each needing its own predicate, none of which fits in
   one spec: (i) pure statement LOSS — `check_limit` -22, `initImagedata` -22, `build_current_period_df`
   -12@516, `get_real_from_zeromq` -24@192, `run_individual_transform` -7/-8/-21/-22; (ii) pure OVERSHOOT —
   `load_bars_from_hundsun` +7@256 (this is the R66 §7.3 `os.path.exists(DumploadDailyFile)` bare-expression
   overshoot, confirming P4's earlier fix now over-fires), `get_price` +2@326, `check_frequency` +2@562;
   (iii) RELOCATION — `get_individual_data` 28->25, `run_tick_socket` 24->25, `get_real_from_zeromq` 30->30,
   i.e. three further witnesses for the same linearisation channel that blocks matcher.
3. Strict-only jump-target/constant-slot residuals (`check_industry_code #159`, `load_get_price #53`,
   `change_his_to_backward #213`, `change_his_to_forward #241`, `run_tick_transform #135`) are a 4th family;
   `change_his_to_forward #241` is the R25-registered canary-class residual and was deliberately left alone —
   measured still exactly at the baseline reading under c1 (quote bytes identical), so it was not broken.

## 7. Repo / discipline attestation
* `F:/Downloads/pythoncdc-main` written **zero** times: `h62.py build` asserts
  `io.open(head,'rb').read() == io.open(worktree,'rb').read()` and this was re-run *after* all measurements
  (last run above) -> "head pristine == worktree bytes". No `core/`, `*OK.py`, `pyc_index.json`, `.trae/`,
  `test_repros/` write.
* 402 full-corpus sweep NOT run (per brief). Longest single command well under 300 s (targets 5.3 s).
* Every command used `python -X utf8`; `PYTHONIOENCODING` never set (the `DBG_OR` env var used is the
  analyzer's own pre-existing debug switch, set only inside my probe process).
* Turn count at completion: ~57 of 150.

## 8. Artifacts
* `FACTS.md` (this file) — steps 0..6 complete and replayable.
* `specs/cand_r67_orchain_tail.json` — 1 file, 1 edit, anchor unique (`cand/a1.txt` 3 lines at L16448-16451),
  three-element comment present (识别条件 / 归约方式 / AST 映射), no forbidden predicate input.
* `synth/r67_guard_tern.py` + compiled `synth/r67_guard_tern.pyc` + own list `synth/r67_guard_tern.txt`
  (8 lines; reproduces on landed 1/2 -> 2/2 under c1).
* Probes (read-only): `probe_r67.py` (region parentage), `dbg_r67.py` (sys.settrace line trace),
  `mk_cand.py` (spec builder with anchor-uniqueness assert against landed bytes).
* Dumps: `dump/landed{,_battery,_canary,_wit}.jsonl`, `dump/c1_{targets,synth,battery,canary,wit}.jsonl`,
  strict JSONs `dump/{landed,c1}_{strict,wit_strict}.json`, logs `logs/r67_hex_dump.txt`,
  `logs/r67_match_parent.txt`.
* Arm name for the centre: **`c1`** (`python -X utf8 h62.py build --spec=specs/cand_r67_orchain_tail.json --dst=c1`).
