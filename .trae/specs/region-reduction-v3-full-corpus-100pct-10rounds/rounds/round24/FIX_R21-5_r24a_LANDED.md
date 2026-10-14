# FIX_R21-5 — handler-body tuple-unpack collapse (`exc_type, exc_obj, exc_tb = sys.exc_info()`), not an `as`-binding loss
Engineer: r24a · branch rr-v3r01-f557fd · HEAD c4e790dd
Owned file: **core/cfg/region_ast_generator.py (ONLY)** · region_analyzer.py / ast_generator_v2.py / comprehension_generator.py untouched (read-only)
Victim unit: `site-packages/fly/data/quote.pyc` :: `<module>.Quote.get_real_from_zeromq`
All work done in the mirror `D:/Temp/r24a/wt`; **all products under `D:/Temp/r24a/out` only**; no repo file written, no `*OK.py` written into the repo, no gate run, no git write.

## 1. Mirror build proof
`cp -r pycdc.py core parsers utils bytecode scripts` + `cp --parents -r` of the six battery dirs (`rounds/round14/{repro,repro_arm,repro_ccneg}`, `rounds/round18/repro_retbreak`, `rounds/round19/{repro_orderapi,repro_tail}`) plus `unit_diff.py` at its own depth and `site-packages/` (inputs).
Self-certification script walked **98 copied `.pyc`-pipeline files** (core/parsers/utils/bytecode/scripts + pycdc.py): **0 mismatches** vs repo.
`region_ast_generator.py` mirror = `4f295dfc6ebd2caa` = repo = the hash quoted in the brief; `pristine/region_ast_generator.py` = same hash (content-addressed pristine copy kept).
Committed-product reproduction: mirror regen of `fly/data/quote.pyc` → `out/s1/fly_data_quote_OK.py` **`cmp` IDENTICAL to repo `site-packages/fly/data/quoteOK.py`**; later also `quotationOK.py` reproduced identically ⇒ the sealed products are FRESH vs the landed bytes (not stale).

## 2. Stage 1 baseline (UNPATCHED mirror, fresh product via `--source`)
`python -X utf8 panel.py s1` = per file: regen with mirror code → `pyc_verify.py single <pyc> --source <fresh product>`.
quote **88/92** · wizard_quant_api **57/58** · real_quote **44/45** · klinedata **63/64** · handlers **29/30** · trade_info_utils **38/41** · api_base **27/28** · strategy **26/27** · realtime_event_source **12/13** · risk_calculation `__init__` **42/43** · trade_live_broker **118/128** · sentinels quotation **153/153**, matcher **17/17**, order_api **37/37** — every value equals the recorded Stage-1 roster.
Shape reproduced exactly (`unit_diff.py "fly/data/quote.pyc" "<module>.Quote.get_real_from_zeromq" --prod out/s1/...`):
`len orig=782 prod=779 delta=-3 hunks=4 landings=0 judge_diff=True`, with the two one-line opcode rows
`- @3966 LOAD_FAST exc_tb / + @3958 LOAD_GLOBAL exc_tb` and `- @4044 LOAD_FAST exc_tb / + @4046 LOAD_GLOBAL exc_tb`.

## 3. Signature re-verification — the brief's stated cause is FALSE; the observable is true
The brief reasoned "the generated `except ...:` handler lost its `as exc_tb` binding". Measured against the ORIGINAL bytecode of the unit:
`co_varnames = (..., 'x', 'sys', 'os', 'exc_type', 'exc_obj', 'exc_tb', 'fname')` and the handler is
`except BaseException as x:` (binds **`x`**, which the product emits correctly), while `exc_tb` is bound by a
**user-level tuple-unpack assignment**, not by the handler header:
```
@3884 LOAD_FAST sys   @3886 LOAD_METHOD exc_info  @3912 CALL  @3922 UNPACK_SEQUENCE 3
@3926 STORE_FAST exc_type  @3928 STORE_FAST exc_obj  @3930 STORE_FAST exc_tb
@3966 LOAD_FAST exc_tb ... @4044 LOAD_FAST exc_tb
```
So `name`/`exc_name` (set at `region_ast_generator.py:30629-30630` and `:30693`, consumed by
`ast_converter._convert_except_handler:1632` → `ASTExceptHandler(name=…)` → `code_generator._generate_except_handler:2077`)
is **not** involved: the `as x` binding round-trips fine. What the emitted source lost is the **multiple-target Assign**:
`out/s1/fly_data_quote_OK.py:1144` read `exc_type = sys.exc_info()` instead of `exc_type, exc_obj, exc_tb = sys.exc_info()`;
`exc_tb` therefore has no local binding in scope and `compile()` resolves it as a global ⇒ both LOAD_FAST→LOAD_GLOBAL rows.
The other **delta = −3** is the same single mechanism, measured not assumed: `UNPACK_SEQUENCE` + the 2 dropped `STORE_FAST`
(`exc_obj`, `exc_tb`) = exactly 3 instructions; after the fix `delta=0`. Nothing vanished at the handler exit, and no
`LOAD_CONST`/`DELETE_FAST`-class cleanup was involved (the as-var cleanup is still folded by the existing B84/repro_07 criteria).

Emission path proven by an **in-process monkeypatch probe in the same process that produced the artifact** (no subprocess
driver, no repo edit): `_generate_handler_body_statements(block@3744)` — the handler-body block, offsets 3744..4164 —
returned 8 statements including two plain `Assign`s and never delegated to `_generate_block_statements`, i.e. the block was
flushed at `region_ast_generator.py:32759` `if instr.opname in ('STORE_FAST','STORE_NAME','STORE_GLOBAL','STORE_DEREF'):`
→ `_build_store_statement(stmt_instrs + [instr])`, whose accumulated value slice still contained the `UNPACK_SEQUENCE`,
which `ExpressionReconstructor` skips ⇒ first target only, remaining stores silently dropped.
Probe inertness proved per target by `cmp`: `out/s1/*` (pre-probe) vs `out/c1/*` (post-probe, both pristine code) byte-identical
for quote / wizard_quant_api / real_quote / klinedata / handlers / trade_info_utils (6 files checked, 6 PROBE-INERT).
Regen determinism: `out/r2` vs `out/r3` (same patched bytes) `cmp` identical.

### Duplicated-decision-site census (the brief's "count before patching one")
27 call sites of `self._build_store_statement(` in this file, spread over **15 distinct functions**; **10 already carry an
UNPACK_SEQUENCE/UNPACK_EX state machine** (`generate`, `_loop_generate_while`, `_loop_extract_for_iter_pre_stmts`,
`_loop_extract_self_loop_stmts`, `_loop_process_header_instructions`, `_loop_extract_pre_stmts_from_instrs`,
`_if_extract_cond_instructions`, `_build_statements_from_instructions:33240/:33307`, `_generate_block_statements_body`,
`_generate_stmts_from_instrs:57661`); **5 do not**: `_reconstruct_await_block_stmts`, `_try_generate_conditional_break`,
`_try_generate_conditional_break_or_continue`, `_generate_try`, `_generate_handler_body_statements`.
I patched only the one that provably fires for a measured corpus defect (`_generate_handler_body_statements`); the other four
are reported as un-instrumented sites, NOT as fixed ones (no claim without a flip).

## 4. 判据实现 (exact file:line + predicate)
File: `core/cfg/region_ast_generator.py`, function `_generate_handler_body_statements` (handler/finally 体单块语句发射).
Delivered (patched) line numbers:
- `:32039` `_hb_unpack_info = None` — state slot declared next to `stmts`/`stmt_instrs` (pristine `:32026-32027`).
- `:32775` `if instr.opname in ('UNPACK_SEQUENCE', 'UNPACK_EX'):` — **识别入口 + 前瞻认领**:
  `_hb_n = instr.arg`（UNPACK_SEQUENCE）或 `(argval&0xFF)+1+((argval>>8)&0xFF)`（UNPACK_EX）；谓词
  `_hb_ok = _hb_n >= 2` 且 `block.instructions` 中紧随其后的 N 条非噪声指令（噪声 = `RESUME/NOP/CACHE/PUSH_NULL/EXTENDED_ARG`）
  **全部** ∈ `('STORE_FAST','STORE_NAME','STORE_GLOBAL','STORE_DEREF')`（`:32788`–`:32804`，任一不满足 ⇒ `_hb_ok=False` ⇒
  `stmt_instrs.append(instr); continue`，即原行为完全保留，属性/下标目标、链式 COPY 一律不认领）。
  认领时把已累积的 `stmt_instrs` 重建为 value 表达式（`self.expr_reconstructor.reconstruct`），清空累积，`:32812` 存
  `{'value','targets':[],'count','is_starred','starred_idx'}`。
- `:32820` `if _hb_unpack_info is not None:` — 位于 STORE 分支最前（pristine `:32759` 之后、`has_copy` 之前），逐个收集 N 个
  目标名（starred 位插 `Starred(Name,ctx='Store')`），`len(targets)==count` 时发射**单一**
  `{'type':'Assign','targets':[{'type':'Tuple','elts':targets,'ctx':'Store'}],'value':…}` 并复位状态；
  形态与 `_build_statements_from_instructions:33319-33327` 逐字段同构（同一字节码事实在两条重建路径同语义）。
Patch shape: **83 lines inserted, 0 lines changed/deleted** (`splitlines(True)` + rebuild, file is 100 % CRLF — verified
59 559 CRLF / 0 bare-LF; anchor content **and** index asserted: `:32026/:32027` and `:32758/:32759/:32760` before writing).
No region-membership read, no `block.successors` read, no offset/name whitelist — pure opcode/oparg structural facts.

## 5. Stage readings (patched mirror, sha16 `5043790fbeaca162`)
Victim unit: `len orig=782 prod=782 delta=0` / **`hunks=0 landings=0 judge_diff=False`** (was `delta=-3 hunks=4 judge_diff=True`)
⇒ unit **Equal**; judge on a fresh product: `[single] ... quote.pyc status=failure units=89/92` (was 88/92) ⇒ **named unit flip, +1 file unit**.
Emitted source before → after (line 1144 of the quote product, handler at 1139 `except BaseException as x:` unchanged):
```
-            exc_type = sys.exc_info()
+            exc_type, exc_obj, exc_tb = sys.exc_info()
   fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
```
Panel (all 14 files, fresh product + `--source`, `out/results_s2.txt`):
quote **89/92** (+1) · wizard_quant_api 57/58 · real_quote 44/45 · klinedata 63/64 · handlers 29/30 · trade_info_utils 38/41 ·
api_base 27/28 · strategy 26/27 · realtime_event_source 12/13 · risk_calculation 42/43 · trade_live_broker 118/128 ⇒ **zero decreases**;
sentinels quotation **153/153**, matcher **17/17**, order_api **37/37** ⇒ all at recorded values.
Batteries (`out/batteries_s2.log`): repro **RED=9/9** · arm **GREEN=0 RED=3/3** · ccneg **GREEN=3 RED=1/4** ·
retbreak **GREEN=2 RED=2, DRIFT_VS_BASELINE=0** · orderapi **GREEN=5 RED=0/5** · tail **GREEN=13 RED=0/13** ⇒ all six at recorded values.
Not bundled: the remaining 3 red units of quote.pyc (`check_frequency`, `run_individual_transform`, `run_tick_socket`) are
untouched control-flow residuals; quote stayed 89/92, no other quote unit changed.
Independence check on a third fresh product (`out/r3`, `cmp`-identical to `out/r2`, same patched bytes):
`pyc_verify single ... --source out/r3/... → units=89/92`, and `get_real_from_zeromq` no longer appears in the per-unit
failure list at all (the other 3 failures are the pre-named control-flow residuals).

## 6. 负面证据
1. **The ticket's stated cause is disproved by the original bytecode**: no handler ever lost an `as exc_tb` binding — the
   original handler binds `x`, and `exc_tb` came from `exc_type, exc_obj, exc_tb = sys.exc_info()`; `ExceptHandler.name`
   (`:30629/:30693` → `ast_converter:1632`) is not on this path. The LOAD_FAST→LOAD_GLOBAL rows are *symptoms of an
   unbound read after a collapsed unpack assign*, so a fix at the handler-header `name` field would have scored 0.
2. **The −3 vanished instructions are the same mechanism, not a cleanup**: `UNPACK_SEQUENCE` + 2 dropped stores; post-fix
   `delta=0`, and no `LOAD_CONST`/`DELETE_FAST` handler-exit statement moved independently.
3. **Census = 1 unit, corpus-wide within the measured set (a negative census)**: `census.py` walks each product's compiled
   code objects paired by qualname against the original and flags names that the original binds+reads as locals
   (`LOAD_FAST`) but the product reads via `LOAD_GLOBAL` (i.e. emitted without a local binding in that scope).
   Over all **11 residual + 3 sentinel files** with PRISTINE products (`out/c1`):
   `TOTAL_UNITS_WITH_LOST_BINDING=1`, `TOTAL_LOST_NAMES=1` → exactly `fly/data/quote.pyc :: .<module>.Quote.get_real_from_zeromq ['exc_tb']`.
   Same rig on the PATCHED products (`out/s2`): **0/0** ⇒ the criterion's population on this panel is one unit, and the fix
   consumes all of it. Rig non-vacuity is demonstrated by that 1→0 transition (a hand-picked example would not score).
   `exc_obj` is *not* counted because the original never reads it, so no LOAD survives to differ; that is why the raw
   `delta=-3` exceeds the 2 visible rows.
   Scope note: a file that the gate reports green cannot carry this defect (a collapsed unpack always changes bytecode),
   so the mechanism does not warrant an analyzer-level or multi-file criterion — **fix it once here**.
4. `landings=0` before and after: this unit never had a jump-operand residual, so no landing criterion is needed (consistent
   with the "no landing channel in the generator" finding).
5. The other 4 store-flush sites lacking the machine (`_reconstruct_await_block_stmts`, `_try_generate_conditional_break`,
   `_try_generate_conditional_break_or_continue`, `_generate_try`) are **not** claimed: the census shows no measured unit
   that requires them, and patching them would be an un-instrumented bundle.

## 7. Final declaration
**LANDED-READY.**
Deliverable: `D:/Temp/r24a/DELIVER/region_ast_generator.py` (whole changed file, mirror patches do not `git apply` here)
· sha256 first-16 **`5043790fbeaca162`** (3 749 415 bytes, 59 642 lines) · pristine sealed bytes **`4f295dfc6ebd2caa`**
(3 744 157 bytes, 59 559 lines) · changed-line count vs pristine: **+83 inserted, 0 modified, 0 deleted**, first diff at line 32028 ·
`py_compile` proof: both the in-mirror file and the DELIVER file compile (`py_compile.compile(..., doraise=True)` → OK).
Revert (byte-exact, no git):
`cp /d/Temp/r24a/wt/pristine/region_ast_generator.py "<repo>/core/cfg/region_ast_generator.py"` and assert
`python -c "import hashlib;print(hashlib.sha256(open(r'<repo>/core/cfg/region_ast_generator.py','rb').read()).hexdigest()[:16])"` == `4f295dfc6ebd2caa`.
Certifying read left to the gate owner (the 402-file gate was NOT run by me).
