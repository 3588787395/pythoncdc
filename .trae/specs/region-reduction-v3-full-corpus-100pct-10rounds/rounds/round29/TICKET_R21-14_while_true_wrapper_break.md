# TICKET R21-14 (round 29) — the `while True:` wrapper route must not turn a `return None` into a `break`

Owner file (the ONLY file you may modify, and only inside your mirror):
`core/cfg/region_ast_generator.py`
Sealed hashes of the read-only twins: `region_analyzer.py = 35e227ac3e7b25af`,
`ast_generator_v2.py = beeaf14435e22922`, `region_ast_generator.py = ac8ec5aa2d5796ea`.
Repo (read-only): `D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main`, branch `rr-v3r01-f557fd`, HEAD `d3b4279b`.
Mirror for your work: `D:/Temp/r30/wt`. Products: `D:/Temp/r30/out/<tag>/`. **No git writes.**
NOTE another engineer (`r36a`, ticket R21-13) is working the same *file* in a different
mirror `D:/Temp/r29`. Do not read, write or copy anything under `D:/Temp/r29`, and do not be
surprised if its products differ from yours — you both start from HEAD `d3b4279b` bytes.

## 0. The victim and the file flip it buys
`IQEngine/plugins/plugin_system_risk_calculation/__init__.pyc` ::
`<module>.PluginRiskCalculation._save_testds_to_csv` — the file is 42/43 and this is its ONLY
remaining failing unit, so the flip is `42/43 -> 43/43` = **whole-file flip 391 -> 392**.
Measured on the sealed product: `len orig=80 prod=73 delta=-7 hunks=3 landings=3 judge_diff=True`.

## 1. What is wrong, already measured (do not re-derive; verify then fix)
The product (`__init__OK.py:536-554`) emits:
```python
        while True:                                    # 539  <- there is NO such enclosing loop
            while not self._stop_save_csv_thread:      # 540
                try: ...
                except Empty: continue
                csv_writer(daily_result, is_end)
                if is_end: break                       # 547
            else:
                return None                            # 549  <- HUNK A: pair inserted @264 (orig has none)
            while not self._stop_save_csv_thread:      # 550
                from ...function import THREAD_STATUS
                if THREAD_STATUS:
                    break                              # 553  <- HUNK B: orig emits LOAD_CONST None;RETURN_VALUE
                    # time.sleep(0.01)                 #        AND CPython dead-code-eliminates the
                                                       #        following 6 instructions that orig has
            break                                      # 554
```
The original's tail (dis of the pyc, idx48..79) is two **sequential** `while not self._stop_save_csv_thread:`
loops with no enclosing `while True:`:
```
idx48 LOAD_FAST is_end / idx49 POP_JUMP_FORWARD_IF_FALSE->idx51 / idx50 JUMP_FORWARD->idx54   # `if is_end: break`
idx51 LOAD_FAST self._stop_save_csv_thread / idx53 POP_JUMP_BACKWARD_IF_FALSE -> off122       # 1st loop bottom test
idx54 LOAD_FAST self._stop / idx56 POP_JUMP_FORWARD_IF_TRUE -> idx78                          # 2nd loop top test
idx57..62  from ... import THREAD_STATUS
idx63 LOAD_FAST THREAD_STATUS / idx64 POP_JUMP_FORWARD_IF_FALSE -> idx67
idx65 LOAD_CONST None / idx66 RETURN_VALUE                     <-- `return None`, NOT a break
idx67..72  time.sleep(0.01)   <-- present in orig, ABSENT in prod (dead-code eliminated by the break)
idx73 LOAD_FAST self._stop / idx75 POP_JUMP_BACKWARD_IF_FALSE -> off276                        # 2nd loop bottom test
idx76 LOAD_CONST None / idx77 RETURN_VALUE ; idx78 LOAD_CONST None / idx79 RETURN_VALUE
```
So the emission defect is the wrapper decision that wraps a straight-line pair of loops in
`while True:` and then rewrites the function-level `return None` inside the loop body as a
`break`, which (a) changes the exit kind and (b) makes CPython ≥3.10 dead-code-eliminate every
statement that follows it in the same suite — here `time.sleep(0.01)`, i.e. a real behavioural
loss, not just a layout difference.

## 1b. Codegen proof I ran myself (so you do not repeat it — but do extend it)
Compiled both shapes on this interpreter (3.11.7) and compared against the pyc's instruction list
(offset, opname, argrepr):
- the product's emitted shape (`while True:` wrapper, `else: return None`, `if THREAD_STATUS: break`,
  no `time.sleep`) -> **73 instructions**, exactly `len prod=73`.
- my reconstruction (two **sequential** `while not self._stop_save_csv_thread:` loops,
  `if THREAD_STATUS: return None` followed by `time.sleep(0.01)`) -> **80 instructions**, exactly
  `len orig=80`, with the first 56 rows positionally identical and 66/80 rows matching overall.
So the wrapper is definitively the defect and the plain shape is definitively close to correct.
The rows still open are from idx56 on: the 2nd loop's top-test target is `to 366` in my
reconstruction vs the original's tail landing, i.e. something about the loop-exit ordering after
`time.sleep(0.01)` is not yet reproduced. Your first job is to close those remaining rows by
compiling candidate shapes (that is cheap and it is the only trustworthy oracle here) BEFORE
touching the generator, then make the generator emit the shape that matches. Script to reuse:
`D:/Temp/t29/risk.py` (read-only copy for you: put your own version under `D:/Temp/r30/`).

## 2. What to change
Find the site that produces the enclosing `while True:` (and its `else: return None` /
trailing `break` compensations) for this region — the loop-emission route in
`region_ast_generator.py` (`_loop_handle_header`, `_generate_loop`, whatever builds
`{'type':'While','test':Constant(True)}` plus the `Break` rewrite; grep for
`'type': 'Break'` / `'type': 'Continue'` branches and for the `While` node construction).
The rule to implement: **a terminating `Return` (including `return None`) that belongs to the
enclosing function must be emitted as `Return`, never as `Break`, whenever the loop suite has
any statement after the terminating block** (those statements are otherwise dead-code
eliminated). Prefer narrowing the *wrapper* decision over special-casing the return: the
wrapper is itself unexplained here, because the original has no back-edge into it anywhere in
the 80-instruction body.

## 3. Acceptance (hard, measured — quote the literal rig lines)
Rig: `python -X utf8 .trae/specs/region-reduction-v3-full-corpus-100pct-10rounds/unit_diff.py <pyc-rel> <qualname> --all`
- `_save_testds_to_csv` must read `len orig=80 prod=80 delta=0 hunks=0 landings=0 judge_diff=False`,
  which requires at minimum: `time.sleep(0.01)` present in the product text, and the
  `if THREAD_STATUS:` arm terminating in `return None`.
- Judge: `python -X utf8 scripts/pyc_verify.py single <abs pyc> --source <your product>` must print
  `Equal` for that qualname, and the file must read `43/43`.
- If you can only remove ONE of the three hunks, report the shape honestly; a partial
  `delta=-7 -> -2` with no flip is a measured negative, not a candidate.

## 4. Anti-regression duties (all mandatory, BEFORE you deliver)
1. **Fire census** over the 14-file panel (`fly/data/quotation.pyc`,
   `IQCommon/{api/klinedata,logger/handlers,strategy/wizard_quant_api,util/trade_info_utils}.pyc`,
   `IQData/api/api_base.pyc`, `IQData/plugins/plugin_system_realquote/real_quote.pyc`,
   `IQEngine/plugins/plugin_fly_data/{strategy/strategy,fly_api/order_api}.pyc`,
   `IQEngine/plugins/plugin_system_{trade/trade_live_broker,matcher/matcher,event_source/realtime_event_source}.pyc`,
   plus your own `__init__.pyc`): report `TOTAL_FIRES` and, per file, whether the regenerated
   product `cmp`-matches the repo's sealed product. Broad fires + changed products = narrow it
   or report the census as negative evidence (a broad relax once cost this campaign −20 units).
2. `fly/data/quotation.pyc` must stay 153/153.
3. No regression on: `handlers` 29/30, `klinedata` 63/64, `wizard_quant_api` 57/58,
   `trade_info_utils` 38/41, `api_base` 27/28, `real_quote` 44/45, `strategy` 26/27,
   `order_api` 37/37, `matcher` 17/17, `broker` 121/128, `quote` 91/92.
4. Probes must be `cmp`-proved inert per target or the reading is VOID; an empty probe log is
   SUSPECT (log the exception; never wrap the probe body in a bare `except`). Prefer ablation:
   monkeypatch candidate builders to `return None` in the SAME process that produces the artifact.
5. Decide codegen questions by **compiling candidate sources** on this interpreter (3.11.7), not
   by argument. E.g. confirm by `compile()` that `if C: break` in a suite followed by more
   statements really deletes those statements, and that `if C: return None` does not.

## 5. Hard constraints
- Repo read-only: no writes, no git writes at all.
- 300 s per command max. `python -X utf8`, NEVER PYTHONIOENCODING. Byte-level patches preserving
  the file's existing mixed CRLF/LF (split keepends on `\n` and rebuild; never re-normalise the
  whole file). All scratch/logs by absolute path under `D:/Temp/r30/`.
- Mirror proof before any measurement: copy `pycdc.py core parsers utils bytecode scripts`,
  verify the three sealed hashes above (`sha256sum | cut -c1-16`), regenerate this victim's
  product and `cmp` it against the repo's `__init__OK.py` — must be IDENTICAL, else your mirror
  is void.
- Only `core/cfg/region_ast_generator.py` may change. If the true fix is in
  `region_analyzer.py`, DO NOT edit it — state the finding with evidence as the next ticket.

## 6. Deliverable
`D:/Temp/r30/DELIVER/FIX_R21-14.md` — sections: (0) ticket as received, (1) mirror + sealed-hash +
cmp proof, (2) baseline readings (victim + 14 panel), (3) 取证: the wrapper/`Break` site with
file:line and the code you read, (4) criterion as implemented, (5) post-patch readings + fire
census + quotation + panel table, (6) negative evidence, (7) final declaration:
`CANDIDATE READY (file flip: __init__.pyc 43/43)` or `FALSIFIED — <what was measured, what the
next ticket must be>`. Plus `D:/Temp/r30/DELIVER/CANDIDATE_region_ast_generator.py` (whole file,
never a diff) with its `sha256sum | cut -c1-16`, ONLY if acceptance is met with no panel
regression. Report numbers exactly as measured; a precise negative is valuable, a vague
positive is worthless.
