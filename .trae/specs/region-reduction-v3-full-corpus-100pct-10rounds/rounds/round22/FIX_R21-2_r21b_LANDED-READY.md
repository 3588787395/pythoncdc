# FIX_R21-2 — r21b (candidate file: core/cfg/comprehension_generator.py)

Campaign: Python bytecode decompiler, region reduction / "No More Gotos".
Branch `rr-v3r01-f557fd`, repo HEAD `f0741eb4`.
Repo (read-only for me): `D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main`
My mirror: `D:/Temp/r21b/wt` · out: `D:/Temp/r21b/out` · deliver: `D:/Temp/r21b/DELIVER`

## Forbidden files (owned by other engineers, measuring right now)
- `core/cfg/region_analyzer.py` (r20u, mirror `D:/Temp/r20u`) — NOT read, NOT patched.
- `core/cfg/region_ast_generator.py` (r21a, mirror `D:/Temp/r21a`) — NOT read, NOT patched.
- Directories `D:/Temp/r20u`, `D:/Temp/r21a` — not entered.

## Status: LANDED-READY (appended live through the whole run; final declaration in §7)








## 1. mirror proof  (LANDED, verified)
Built `D:/Temp/r21b/wt` fresh from repo working tree: `cp -r pycdc.py parsers utils bytecode scripts core`
+ `cp --parents -r` of the six battery dirs (round14/repro, round14/repro_arm, round14/repro_ccneg,
round18/repro_retbreak, round19/repro_orderapi, round19/repro_tail) at identical relative depth
(runners resolve root by 7 dirname levels: file->battery->roundNN->rounds->spec->specs->repo root).
All **33** `core/**/*.py` files sha256-compared mirror vs repo: **0 mismatches**.
Recorded (re-read myself, not from the brief), first-16:
  core/cfg/comprehension_generator.py  bbc73f9ebaede624
  core/cfg/region_ast_generator.py     4f295dfc6ebd2caa   (hash only; file never opened by me)
  core/cfg/region_analyzer.py          640d33a77dcb71c2   (hash only; file never opened by me)
  core/cfg/code_generator.py           28aba10bae133952
  core/cfg/ast_converter.py            097312b88270c461
  core/cfg/ast_generator_v2.py         (my second candidate host; verified identical to repo in the 33-file sweep)
Repo working tree vs HEAD `f0741eb4`: differ **only** by line ending (WT is 2675 CRLF / 0 LF, HEAD blob
2675 LF); `sha256(WT.replace(CRLF,LF)) == sha256(HEAD blob)` -> working tree IS the landed state, CRLF preserved.
`pristine/` holds byte copies of comprehension_generator.py (bbc73f9ebaede624), region_ast_generator.py,
region_analyzer.py.
**Pre-existing `D:/Temp/r21b/*` mirror from an earlier session was NOT reused**: its
`region_ast_generator.py` reads c7afe001f309ce4d != landed 4f295dfc6ebd2caa (stale); discarded, `wt` rebuilt.

**Product cmp proof (unpatched mirror)**: `pycdc.py --region wizard_quant_api.pyc -o out/wizard_quant_api_base.py`
(4.2 s) -> `cmp` vs repo `site-packages/IQCommon/strategy/wizard_quant_apiOK.py` = **BYTE-IDENTICAL**.

## 2. baseline reproduction
Judge (external, `scripts/pyc_verify.py single <pyc> --source <fresh product>`):
  `wizard_quant_api.pyc` fresh product = **status=failure units=55/58 (94.83%)** -- matches the brief.
  Failing units named by the judge: `<module>.filter_desicion: Different control flow`,
  `<module>.get_DMI.calculate_di.<genexpr>: Different control flow` x2.

## 3. the copy-pair measurement I reproduce (scripts/copyprobe.py, scripts/disgen.py)
Units note: the brief's "216 / 164" are `len(co_code)` BYTES; logical instruction counts are 64 / 50
(3.11 has 2-byte instructions + CACHE slots). Same defect, same shape either way.

| copy (qualname chain)              | orig bytes | prod bytes | orig instrs | prod instrs | delta | POP_JUMP_IF_FALSE orig | prod |
|------------------------------------|-----------|-----------|-------------|-------------|-------|------------------------|------|
| calculate_di.<genexpr>  (#0)       | 0         | 0         | 46          | 46          | 0     | 0 | 0 |
| calculate_di.<genexpr>#1           | 216       | 164       | 64          | 50          | -14   | 2 | 1 |
| calculate_di.<genexpr>#2           | 216       | 164       | 64          | 50          | -14   | 2 | 1 |

argcount/freevars/varnames/consts-types identical per pair (free=('high','low'), varn=('.0','i'),
consts=(int,int,NoneType)) -> not a pairing/ordering artifact.

**Reading of the shape (disgen.py, copy #1) -- corrects the brief's "nested/chained ternary" guess.**
The original element is NOT `a if c1 else b if c2 else d`; it is a single IfExp whose *test* is an
`and` BoolOp whose two legs share one false exit:
```
14..58   A = high[-i]-high[-(i+1)] ; LOAD_CONST 0 ; COMPARE_OP >
64       POP_JUMP_FORWARD_IF_FALSE to 202      <- leg 1 false exit
66..150  A ; B = low[-(i+1)]-low[-i] ; COMPARE_OP >
156      POP_JUMP_FORWARD_IF_FALSE to 202      <- leg 2 false exit (SAME target)
158..196 A (Then value) ; 200 JUMP_FORWARD to 204 (merge)
202      LOAD_CONST 0 (Else value) ; 204 YIELD_VALUE
```
i.e. source `A if A > 0 and A > B else 0`. The product emits `A if A > B else 0` -- the FIRST leg
(`A > 0`), its `LOAD_CONST 0 / COMPARE_OP` and its false-exit jump are dropped; the false exit is not
"the middle alternative of a ternary chain", it is the shared short-circuit target. Copy #2 is the
mirror-image (`B if B > 0 and B > A else 0` -> `B if B > B>A else 0`).

Why the existing `[R67-fix2]` rule (comprehension_generator.py:2253-2302, 2361-2365) does not fix it:
its own docstring promises "共享假出口的连续条件跳转即在表达式重建器中折叠为 BoolOp" -- **that fold does
not exist**. Measured offline (`scripts/ternprobe.py`, `scripts/ternprobe2.py`, no pipeline involved):
the chain rule FIRES (cond slice = 37 instrs, offsets 14..150, contains `POP_JUMP_FORWARD_IF_FALSE@64`),
and `ExpressionReconstructor.reconstruct` (core/cfg/ast_generator_v2.py:203) returns a **single
`Compare`** (`A > B`) for that slice -- leg 1 silently dropped, no BoolOp, no error.

## 4. 判据实现 (exact file:line + predicate)
**Host = `core/cfg/comprehension_generator.py` (my designated candidate file). NOT the two forbidden files.**
Post-patch line numbers (patched mirror file, 2747 lines):
* `comprehension_generator.py:2510` new method `_r21_fold_boolop_test_chain(self, all_instrs, seg_start, cond_jump_idx, false_target_offset)`
* `comprehension_generator.py:2437` call site inside `_detect_comp_ternary` (was `:2434-2437`, the single
  `cond_expr = self.expr_reconstructor.reconstruct(cond_instrs)` statement; the old statement is kept verbatim
  as the fallback at `:2440`).
* `_detect_comp_ternary` itself is `:2226`; the `[R67-fix2]` chain identifier `_r67_boolop_chain_end` stays
  untouched at `:2274-2302` / called at `:2363`.

PREDICATE (identification side, all reads are same-level structural facts of the inner comprehension
instruction stream -- no names, no filenames, no offset magic):
```
tail = all_instrs[cond_jump_idx]
tail.opname in CONDITIONAL_JUMP_OPS  and  ('IF_FALSE' in tail.opname or 'IF_NONE' in tail.opname)
cuts = [ k for k in [seg_start, cond_jump_idx) if all_instrs[k].opname in CONDITIONAL_JUMP_OPS ]
        -> must all be: not BACKWARD, false-exit class (IF_FALSE|IF_NONE), argval == false_target_offset
        (any BACKWARD / any IF_TRUE / any other target  => return None : impure chain, old path)
cuts != []                              # >=1 intermediate shared false exit == the and-chain fired
segments = split(all_instrs[seg_start:cond_jump_idx]) at each cut (cut instr itself consumed, yields no value)
each segment non-empty and expr_reconstructor.reconstruct(segment) is not None   (else return None)
=> {'type':'BoolOp','op':'and','values':[seg1, seg2, ...]}   (len(values) >= 2)
```
REDUCTION: each leg is a straight-line operand sequence, reconstructed through the *same* channel the
single-operand case already uses, then combined into one BoolOp -- the shape `_extract_comp_ifs` already
uses for filters (`:1995-1998` per-segment `reconstruct(cond_instrs)` + `:2090-2116` BoolOp merge), so this
criterion does not invent a second reduction mechanism, it supplies the missing half of `[R67-fix2]`.
AST MAPPING: `IfExp(test=BoolOp(and,[Compare,Compare]), body=Then, orelse=Else)`; BoolOp dict is emitted by
existing `ast_converter._convert_boolop_full` (`core/cfg/ast_converter.py:1195`, accepts lowercase `and` and
unwraps <2 values) and `code_generator.py:5252 / :5327` (dict-based BoolOp + precedence/parens).
C3 (strictly additive): no intermediate shared false exit => `cuts == []` => None => byte-identical old path.

### SET vs DECISION census (done BEFORE patching, as required)
SET (opcode lists) -- reused, not re-declared:
* `CONDITIONAL_JUMP_OPS` imported once at `comprehension_generator.py:5` from `region_analyzer`
  (read-only import of the landed constant; region_analyzer.py NOT opened/patched).
* false-exit polarity class `{IF_FALSE, IF_NONE}`: **2 copies** in this file -- `:2283`
  (`if 'IF_FALSE' not in op0 and 'IF_NONE' not in op0`, the `[R67-fix2]` rule ② test) and my new
  `_FALSE_EXIT` tuple at `:2529`. Verified they have identical membership, so the new copy cannot diverge
  in behaviour from the identification it complements. I did not add a third.
DECISION -- "reconstruct(cond_instrs) on a ternary-test region sliced from the whole condition": **3 copies**
of the same statement in the pristine file:
| site | method | can its slice contain an intermediate conditional jump? | action |
|---|---|---|---|
| `:1998` | `_extract_comp_ifs` | No -- it already splits per segment (`segments`), folds to BoolOp at `:2090-2116` | untouched (already correct; my fold would be dead code there) |
| `:2435` | `_detect_comp_ternary` | **Yes** -- `[R67-fix2]` extends `cond_jump_idx` to the chain tail, so the region keeps its intermediate false exits | **PATCHED** (fold added) |
| `:2601` | `_detect_comp_ternary_as_filter` | No -- its own scan breaks at the FIRST forward conditional jump (`:2542-2551`, no chain extension), so `[last_filter_end+1, cond_jump_idx)` is jump-free by construction | untouched, no failing unit implicates it (see 负面证据) |
Method-level duplication of the patched decision: `_detect_comp_ternary` is ONE method with **3 call sites**
(pristine `:1207` single-for, `:1490` multi-for, `:2460` nested-orelse recursion) -- patching the method body
covers all three; no per-copy patching was needed and none was skipped.

## 5. stage readings (complete)
* unpatched mirror product == repo sealed product (`cmp` byte-identical) -- mirror proof.
* patched product `out/wizard_quant_api_r21b.py` (34538 B, was 34472 B): exactly ONE 2-line hunk
  (lines 263-264), both sibling genexprs, now
  `dmp = sum((A if A > 0 and A > B else 0 for i in range(1, n1 + 1)))` and the mirrored `dmm`.
* copyprobe after patch: `#1` orig 64 / prod 64, pj 2/2; `#2` orig 64 / prod 64, pj 2/2;
  `total_abs_instr_delta=0` (was 28).
* judge (`pyc_verify.py single ... --source`): **55/58 -> 57/58**, both
  `<module>.get_DMI.calculate_di.<genexpr>` now Equal; only `<module>.filter_desicion` (Different control
  flow, a different family) remains. `py_compile` of the patched module: OK.

### panel (patched mirror; every product freshly regenerated in `out/patched/`, judged with `--source`)
```
wizard_quant_api: cur=57/58 base=55/58  FLIP+  sealed_cmp=DIFFERS  17s
quote: cur=87/92 base=87/92  same  sealed_cmp=BYTE-IDENTICAL  32s
klinedata: cur=63/64 base=63/64  same  sealed_cmp=BYTE-IDENTICAL  26s
handlers: cur=29/30 base=29/30  same  sealed_cmp=BYTE-IDENTICAL  8s
trade_info_utils: cur=38/41 base=38/41  same  sealed_cmp=BYTE-IDENTICAL  20s
api_base: cur=27/28 base=27/28  same  sealed_cmp=BYTE-IDENTICAL  15s
real_quote: cur=43/45 base=43/45  same  sealed_cmp=DIFFERS  16s
strategy: cur=26/27 base=26/27  same  sealed_cmp=BYTE-IDENTICAL  8s
realtime_event_source: cur=12/13 base=12/13  same  sealed_cmp=BYTE-IDENTICAL  12s
__init__: cur=42/43 base=42/43  same  sealed_cmp=BYTE-IDENTICAL  15s
trade_live_broker: cur=118/128 base=118/128  same  sealed_cmp=BYTE-IDENTICAL  35s
matcher: cur=17/17 base=17/17  same  sealed_cmp=BYTE-IDENTICAL  7s
quotation: cur=153/153 base=153/153  same  sealed_cmp=BYTE-IDENTICAL  34s
order_api: cur=37/37 base=37/37  same  sealed_cmp=BYTE-IDENTICAL  8s
```
Zero decreases; sentinels `quotation 153/153`, `matcher 17/17`, `order_api 37/37` intact; one flip
`wizard_quant_api 55/58 -> 57/58`. **11 of the 14 panel products are BYTE-IDENTICAL to the repo sealed
product**, i.e. the criterion is strictly additive: it moves bytes only in the target file.

### six batteries (patched mirror, at the recorded relative depth, ROOT=D:\Temp
21b\wt)
```
repro     RED=9 / 9                 (expect 9R/9)          -> recorded value
arm       GREEN=0 RED=3 / 3         (expect 0G/3R)         -> recorded value
ccneg     GREEN=3 RED=1 / 4         (expect 3G/1R)         -> recorded value
retbreak  GREEN=2 RED=2 DRIFT_VS_BASELINE=0 / 4 (2G/2R DRIFT=0) -> recorded value
orderapi  GREEN=5 RED=0 / 5         (expect 5G/0R)         -> recorded value
tail      GREEN=13 RED=0 / 13       (expect 13G/0R)        -> recorded value
```
full log: `D:/Temp/r21b/out/batteries_patched.log`

## 6. 负面证据 (negative evidence)
1. **The brief's shape diagnosis is wrong, my measurement replaces it**: the lost middle is NOT the
   `else`-of-`if` arm of a chained ternary; the original element is one IfExp whose *test* is
   `A > 0 and A > B`, both legs sharing the single false exit at offset 202 (disgen.py: `POP_JUMP_FORWARD_IF_FALSE@64`
   and `@156`, `argval` equal). A criterion written for "nested ternary orelse" (the existing recursion at
   pristine `:2448-2462`) would not fire here: the false region is one `LOAD_CONST 0`, jump-free.
2. **The landed `[R67-fix2]` docstring claim is false on the landed bytes.** It states that the shared-false-exit
   chain "folds into BoolOp in the expression reconstructor". Measured offline (no pipeline, no probe in the
   generator): the chain rule FIRES and hands `ExpressionReconstructor.reconstruct`
   (`core/cfg/ast_generator_v2.py:203`) a 37-instruction slice spanning offsets 14..150 that *contains*
   `POP_JUMP_FORWARD_IF_FALSE@64`; the reconstructor returns a single `Compare` (`A > B`) -- leg 1 plus its
   false-exit jump silently dropped, no error, no None. So the defect was **identification-side-completion
   inside comprehension_generator.py, not the analyzer and not region_ast_generator.py**: no BLOCKED-BY-FILE-OWNERSHIP.
3. **`_detect_comp_ternary_as_filter` (pristine `:2601`) is NOT a second copy of the unfixed decision** -- proved
   by construction, not by hope: its own scan (`:2542-2551`) `break`s at the FIRST forward conditional jump and
   never calls `_r67_boolop_chain_end`, so its `cond_instrs = all_instrs[last_filter_end+1:cond_jump_idx]`
   cannot contain a conditional jump; adding my fold there would be dead code. It therefore has a *different*
   (unextended, and here unmeasured) limitation: a ternary-used-as-filter with an `and` test would truncate at
   leg 1 instead of losing leg 1. No failing unit on the panel exhibits that shape, so I did not touch it
   (no speculative second patch).
   `_extract_comp_ifs:1998` already does per-segment reconstruct + BoolOp merge (`:2090-2116`): the correct
   implementation of the same idea, which my patch now mirrors for the ternary test.
4. **The repo's sealed `real_quoteOK.py` is stale w.r.t. the landed bytes.** The panel flagged
   `sealed_cmp=DIFFERS` for `real_quote` (43/45, count unchanged). Control run (pristine file installed, product
   regenerated, patched file restored with sha proof): pristine product == patched product **byte-identical**
   (53896 B), and both differ from sealed by 2 hunks (`if/elif` inside `else:` flattened to top-level `elif`
   chain, `get_real_from_zeromq` region, lines 990-995) -- an elif-flattening decision outside comprehension
   territory, i.e. pre-existing and NOT caused by my patch. Consequence for measurement semantics: a
   sealed-product `cmp` is not a valid inertness test for that one file; the pristine-vs-patched product cmp is.
5. `wizard_quant_api.filter_desicion` is still `Different control flow` (the 3rd failing unit; the round-19
   `repro_tail` README assigns it to the shared-tail/implicit-`return None` family). Untouched by this criterion
   -- 57/58, not 58/58.
6. Probes: none were installed into the pipeline. `scripts/ternprobe.py` / `ternprobe2.py` replicate
   `CFGBuilder.build(code_obj)` + the detector offline, so they cannot perturb any product (no VOID labels
   needed); the recording reconstructor was a local object passed to `ComprehensionGenerator`, never the
   pipeline's. Baseline fidelity was proven instead by `cmp` of the unpatched mirror product against the
   sealed product (byte-identical for wizard).
7. Not run (out of scope by instruction): `gate_round.py` / `gate_chain.py` 402-file gate; no `*OK.py` written
   into the repo; no `git` writes; repo `core/` verified clean (`git status --short -- core/` empty,
   `comprehension_generator.py` still bbc73f9ebaede624 there). Whether the fold fires on corpus files outside
   the 14-file panel is therefore **unmeasured**.

## 7. final declaration
**LANDED-READY** (candidate file only; no forbidden file touched; repo untouched -- the patch lives in my mirror).

* changed file: `core/cfg/comprehension_generator.py` (my designated candidate; NOT `region_analyzer.py`,
  NOT `region_ast_generator.py`, both never opened by me -- only hashed).
* delivered WHOLE file: `D:/Temp/r21b/DELIVER/comprehension_generator.py`
  sha256 first-16 = **`7d8acab92ccc7782`** (= mirror file byte-identical; pristine bbc73f9ebaede624)
* changed lines vs pristine: **+73 / -1** (net +72 lines; 2675 -> 2747 logical lines), single new method at
  `:2510` + call-site block at `:2437-2440`; CRLF preserved (2747 CRLF, 0 LF-only).
* `py_compile`: **OK** (`python -X utf8 -m py_compile DELIVER/comprehension_generator.py`, and the mirror copy).
* measurement: per-copy instrs 64/50 -> **64/64**, POP_JUMP_FORWARD_IF_FALSE 2/1 -> **2/2** for BOTH sibling
  `<genexpr>` copies (`total_abs_instr_delta` 28 -> 0); external judge `--source` on a fresh product:
  **55/58 -> 57/58**, both named units Equal; panel 14 files zero decreases; sentinels 153/153, 17/17, 37/37;
  six batteries all at recorded values.
* **Bar met**: two named unit flips (`get_DMI.calculate_di.<genexpr>` x2) from the external judge, not merely
  matching instruction counts. Not FALSIFIED, not BLOCKED.
* revert (mirror only):
  `cp /d/Temp/r21b/pristine/comprehension_generator.py /d/Temp/r21b/wt/core/cfg/comprehension_generator.py`
  then `sha256sum` must read `bbc73f9ebaede624...`; repo needs no revert (never modified).
  re-apply: `python -X utf8 /d/Temp/r21b/scripts/patch_r21_2.py` (asserts anchors at 2434-2437 and 2505).
