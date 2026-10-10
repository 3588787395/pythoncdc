# TICKET R21-15 (round 29) — the loop's fall-through to the next iteration is emitted as a loop exit (`JUMP_BACKWARD` -> `JUMP_FORWARD`)

Owner file (the ONLY file you may modify, and only inside your mirror):
`core/cfg/region_ast_generator.py`
Sealed hashes of the read-only twins: `region_analyzer.py = 35e227ac3e7b25af`,
`ast_generator_v2.py = beeaf14435e22922`, `region_ast_generator.py = ac8ec5aa2d5796ea`.
Repo (read-only): `D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main`, branch `rr-v3r01-f557fd`, HEAD `7d26442c`.
Mirror for your work: `D:/Temp/r31/wt`. Products: `D:/Temp/r31/out/<tag>/`. **No git writes.**
TWO other engineers are editing the same file in other mirrors (`r36a` ticket R21-13 in
`D:/Temp/r29`, `r37a` ticket R21-14 in `D:/Temp/r30`). Stay entirely inside `D:/Temp/r31` and
read nothing from those directories. All three of you start from HEAD `7d26442c` bytes.
Read R21-14's ticket first for family context:
`rounds/round29/TICKET_R21-14_while_true_wrapper_break.md` — there the generator rewrites a
function-level `return None` as `break`; here it turns a loop fall-through into a loop exit.
If you find the same insertion site serves both, say so explicitly in your report (that is a
useful finding even if it costs you the flip) but DO NOT fix the R21-14 case — one mechanism
per ticket, and the gate must be able to attribute the change.

## 0. Victim and the file flip it buys
`IQCommon/api/klinedata.pyc` :: `<module>.get_kline_by_count_new` — the file is 63/64 and this is
its ONLY failing unit, so the flip is `63/64 -> 64/64` = **whole-file flip 391 -> 392**.
Measured on the sealed product: `len orig=642 prod=642 delta=0 hunks=1 landings=2 judge_diff=True`.
(The old ledger entry claiming this unit "needs two sites" is STALE — after gates 22/25/26/27/28
the residual shrank to the single hunk below. Re-measure before you believe anything else in the
ledger about this file.)

## 1. The defect, measured for you (verify, then fix)
Instruction window (offset / opcode / resolved jump target):
```
ORIG idx553 @2886 LOAD_FAST symbol_four / idx555 CONTAINS_OP
ORIG idx556 @2892 POP_JUMP_FORWARD_IF_FALSE -> off2928 idx568     # `if symbol_four in dividends_stock:`
ORIG idx557-566        fields is None ? bars_ndarr : bars_ndarr[fields] ; history_data_dict[symbol] = ...
ORIG idx567 @2926 JUMP_BACKWARD  -> off1268                       # <-- falls through to the NEXT ITERATION
ORIG idx568 @2928 LOAD_FAST dividends_all ... (the else arm continues)

PROD idx556 @2892 POP_JUMP_FORWARD_IF_FALSE -> off2926 idx568      # same arm, shifted by 2 bytes
PROD idx567 @2924 JUMP_FORWARD   -> off3074                       # <-- EXITS the loop instead
```
So the then-arm of `if symbol_four in dividends_stock:` ends, and the original's control flows
back to the enclosing loop header `@1268` for the next iteration, while the product jumps forward
to `@3074` (after the loop). The emitted source therefore terminates that arm with a loop exit
(a `break`, or a re-nesting that makes the arm the last thing in the loop) where the original had
a plain fall-through. This is a real behavioural defect: at most one iteration performs that arm.

## 2. What to change
Locate the route that ends a loop-body arm with an exit where the CFG says the arm's successor is
the loop back-edge. Start from the loop emitters in `region_ast_generator.py`
(`_loop_handle_header`, `_generate_loop`, `_process_loop_*`, and every branch that constructs
`{'type': 'Break'}` — grep `'type': 'Break'` and count the construction sites; my memory of this
file says five branches emit a bare `{'type': 'Continue'}`, so expect a comparable small set for
`Break`). The criterion should be expressible as: an arm whose declared successor is the region's
back-edge/header must fall through (emit no terminator), never emit `Break`.
Reproduce the decision by compiling candidate source shapes on 3.11.7 before patching — `compile()`
is the only trustworthy oracle for which shape yields `JUMP_BACKWARD` vs `JUMP_FORWARD`.

## 3. Acceptance (hard, measured — quote literal rig output)
Rig: `python -X utf8 .trae/specs/region-reduction-v3-full-corpus-100pct-10rounds/unit_diff.py <pyc-rel> <qualname> --all`
- `get_kline_by_count_new` must read `len orig=642 prod=642 delta=0 hunks=0 landings=0 judge_diff=False`
  (the 2 remaining `landings=` today are 2-byte shift shadows of this same hunk; they must vanish with it).
- Judge: `python -X utf8 scripts/pyc_verify.py single <abs .pyc> --source <product>` prints `Equal`
  for that qualname and the file reads `64/64`.
- A shape that shrinks the hunk but does not flip the unit is a measured negative, not a candidate.

## 4. Anti-regression duties (all mandatory, BEFORE you deliver)
1. **Fire census** over the 14-file panel (`fly/data/quotation.pyc`, `fly/data/quote.pyc`,
   `IQCommon/{logger/handlers,strategy/wizard_quant_api,util/trade_info_utils}.pyc`,
   `IQData/api/api_base.pyc`, `IQData/plugins/plugin_system_realquote/real_quote.pyc`,
   `IQEngine/plugins/plugin_fly_data/{strategy/strategy,fly_api/order_api}.pyc`,
   `IQEngine/plugins/plugin_system_{trade/trade_live_broker,matcher/matcher,event_source/realtime_event_source}.pyc`,
   `IQEngine/plugins/plugin_system_risk_calculation/__init__.pyc`, plus your own `klinedata.pyc`):
   report `TOTAL_FIRES` and per file whether the regenerated product `cmp`-matches the repo's
   sealed product. Broad fires that change products = narrow it or report as negative evidence.
2. `fly/data/quotation.pyc` must stay 153/153.
3. No regression: `handlers` 29/30, `wizard_quant_api` 57/58, `trade_info_utils` 38/41,
   `api_base` 27/28, `real_quote` 44/45, `strategy` 26/27, `order_api` 37/37, `matcher` 17/17,
   `broker` 121/128, `quote` 91/92, `risk_calculation __init__` 42/43.
4. Probes must be `cmp`-proved inert per target else VOID; an empty probe log is SUSPECT (log the
   exception text; never wrap the probe in a bare `except`). Prefer ablation: monkeypatch the
   candidate `Break`-constructing methods to `return None` in the SAME process that produces the
   artifact and watch which stub removes the forward jump.
5. Judge by diff SHAPE (`delta/hunks/landings`), never by the list of failing unit names.

## 5. Hard constraints
- Repo read-only: no writes there, NO git write commands at all.
- Mirror proof before any measurement: copy `pycdc.py core parsers utils bytecode scripts`
  (exclude `__pycache__`), verify the three sealed hashes with `sha256sum | cut -c1-16`, copy
  `unit_diff.py` to the SAME relative depth, regenerate `klinedataOK.py` and `cmp` it against the
  repo's committed product — IDENTICAL or your mirror is void.
- No command over 300 s. `python -X utf8`; NEVER PYTHONIOENCODING. Byte-level patches preserving
  existing mixed CRLF/LF. Scratch/logs by absolute path under `D:/Temp/r31/`.
- Only `core/cfg/region_ast_generator.py` may change. If the fix belongs in
  `core/cfg/region_analyzer.py`, do NOT edit it — write the finding up as the next ticket.

## 5b. ADDENDUM from the orchestrator, 12:36 (use it only if your own measurement agrees)
A sibling engineer ablating the `while True:` wrapper at `region_ast_generator.py:6917` (`_can_merge`)
prompted me to census every `{'type': 'Break'}` construction in that file against sealed bytes
`ac8ec5aa2d5796ea`. The candidates most likely to be YOUR site, with the code I actually read:
- `:12100-12112` — an elif fall-through block whose role is `IF_THEN/BREAK/PURE_BREAK` and whose
  **last instruction is `RETURN_VALUE`/`RETURN_CONST`** is emitted as `_then_stmts = [{'type':'Break'}]`,
  i.e. a return-terminated arm rendered as a loop break. This is a terminator-kind substitution and it
  is the shape your victim shows (fall-through-to-back-edge replaced by a forward loop exit).
- `:12188-12228` — `if then_succ in region.break_blocks:` emits `If(test, body=[Break])`, with the
  comment at `:12188` admitting an earlier bug ("此前代码检测到 LOAD_CONST 就生成 Return(None)，但实际应为 Break").
  Your criterion may be the mirror-image condition: the successor is the loop **header/back-edge**,
  not a break block.
- `:9780-9792` and `:11955-11970` — more `body=[{'type':'Break'}]` / `_orelse_stmts=[{'type':'Break'}]`
  sites gated on successor `BlockRole` being BREAK/PURE_BREAK/RETURN/RETURN_NONE, i.e. role-driven, and
  therefore sensitive to a mis-declared role.
- `:6155-6161` (`else_stmts = [{'type':'Break'}]` for a for-else that breaks an ANCESTOR loop) and
  `:8500-8506` (`_child_has_break_to_outer` appends a trailing `Break` to the body).
Note the file has more than eight such sites, so count the sites that actually FIRE for your region
before editing one of them — a single-site fix on a duplicated predicate is only a partial fix.

## 6. Deliverable
`D:/Temp/r31/DELIVER/FIX_R21-15.md` — (0) ticket as received, (1) mirror + sealed-hash + cmp proof,
(2) baseline readings (victim + panel), (3) 取证 with file:line of the `Break`/exit construction and
the region data you used, (4) criterion as implemented, (5) post-patch readings + fire census +
quotation + panel table, (6) negative evidence, (7) final declaration:
`CANDIDATE READY (file flip: klinedata 64/64)` or `FALSIFIED — <measured facts + what the next
ticket must be>`. Plus `D:/Temp/r31/DELIVER/CANDIDATE_region_ast_generator.py` (whole file, never a
diff) with its `sha256sum | cut -c1-16`, only if acceptance is met with no panel regression.
