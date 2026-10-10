# TICKET R21-16 (round 30) — quote.run_individual_transform needs TWO fixes; fix #1 is already written and measured

Owner file (the ONLY file you may modify, and only inside your mirror): **`core/cfg/region_analyzer.py`**
Sealed bytes right now (re-verify in your mirror at copy time; `git show HEAD:<path>` is LF while the
working tree is CRLF — compare after stripping CR):
`region_ast_generator.py = fd0e4c4d73cf5efc` (gate 29 landed), `region_analyzer.py = 35e227ac3e7b25af`,
`ast_generator_v2.py = beeaf14435e22922`, `comprehension_generator.py = 7d8acab92ccc7782`.
Repo (READ-ONLY): `D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main`, branch `rr-v3r01-f557fd`, HEAD `ce2f8b85`.
Mirror `D:/Temp/r34/wt`, products `D:/Temp/r34/out/`. **No git writes, no repo writes.**
Read first: `rounds/round30/NOTE_R21-14_attempt_falsified.md` (four addenda — the root cause, the
census, and Variants A/B/C/D all measured by me).

## 0. Victim and the flip it buys
`fly/data/quote.pyc` :: `<module>.Quote.run_individual_transform`. File is **91/92** and this is its
ONLY failing unit ⇒ flip = whole-file **92/92**. Today: `len orig=407 prod=355 delta=-52 hunks=10 landings=3`.

## 1. Fix #1 is DONE — apply it, do not re-derive it
`D:/Temp/t30/VARIANT_D_region_analyzer.py` is a complete, compiling, **measured** patch
(`+29/-1` lines in `core/cfg/region_analyzer.py`) that splits
`_extract_except_handler._collect_body` into `_collect_body_raw(entry, _r2116_pe_stop=False)` plus a
wrapper that re-walks with the `POP_EXCEPT`-cleanup cut **only** when the first walk swallowed a block
preceding the handler entry. Measured on `fly/data/quote.pyc`:
```
run_individual_transform  delta -52 -> -3   hunks=3 landings=2      (the try body is restored)
run_tick_socket           stays Equal       file stays 91/92        (no regression; Variant A had broken it)
```
Why it works: the analyzer declared `TryExceptRegion@686` with `try_blocks=[]` and a 23-block handler
body containing offsets 586/638/640/684 that precede the handler entry 754 — the emitted text is
`try: pass` with the whole loop body dumped behind the handler's own `continue`, and CPython ≥3.10
dead-code-eliminates it. Copy that file over your mirror's `core/cfg/region_analyzer.py`, or re-implement
the same rule; either way **report the per-unit shape before you start** so I can attribute the two halves.

## 2. Fix #2 is YOUR work — the residual `delta=-3`
After D the unit reads `len orig=407 prod=404 delta=-3 hunks=3 landings=2`. That is the
**return-`None` threading family** (`rounds/round29/RESIDUAL_ROUND29.md` rows for `trade_info_utils`
and the `#15` register entries): the product materialises an inline `LOAD_CONST None; RETURN_VALUE`
where the original jumps to a shared tail, or vice versa. Two things I already proved about this
family, so do not spend your run on them:
- No arrangement of `return None` **statements** changes the layout: `else: return None`, `else: pass`,
  and no-`else` all compile byte-identically on this interpreter (3.11.7), because CPython threads a
  `return None` else-arm onto the function's implicit tail. A trailing function-level `return None`
  shortens the code instead. Decide every shape question by **compiling candidate sources**.
- The generator cannot write a jump target (AST has no jump operands); only the analyzer's
  *declaration* or a different **nesting** can change which copy an exit lands on.
So: dump the unit's diff hunks after D (`unit_diff.py … --all`), identify each remaining hunk's owning
region and block role, and find the emission/declaration that produces the extra/missing tail copy.
Note this file also contains a second, still-correct handler shape (`run_tick_socket`) — treat it as
your sentinel: any change that makes it leave `Equal` is a regression, not progress.

## 3. Acceptance (quote literal rig output)
- `run_individual_transform` → `len orig=407 prod=407 delta=0 hunks=0 landings=0 judge_diff=False`
  and `scripts/pyc_verify.py single <abs pyc> --source <product>` → `Equal`, file `92/92`.
- If you can only land D (fix #1) with the unit still at `delta=-3`, that is a **measured partial**,
  not a candidate: say so plainly, and report the shape. Do not present it as a fix.

## 4. Anti-regression duties before delivering
1. Fire census of your criterion over the 14-file panel used in round 29 (`fly/data/quotation.pyc`,
   `fly/data/quote.pyc`, `IQCommon/{api/klinedata,logger/handlers,strategy/wizard_quant_api,util/trade_info_utils}.pyc`,
   `IQData/api/api_base.pyc`, `IQData/plugins/plugin_system_realquote/real_quote.pyc`,
   `IQEngine/plugins/plugin_fly_data/{strategy/strategy,fly_api/order_api}.pyc`,
   `IQEngine/plugins/plugin_system_{trade/trade_live_broker,matcher/matcher,event_source/realtime_event_source}.pyc`,
   `IQEngine/plugins/plugin_system_risk_calculation/__init__.pyc`) reporting `TOTAL_FIRES` and, per
   file, whether its product changed — compare against `git show HEAD:<path>` bytes or `cmp` after
   normalising CR, **never** against the checked-out file with mixed EOL (that artifact produced a
   false "four files changed bytes" claim in round 29).
2. `fly/data/quotation.pyc` must stay 153/153; `order_api` 37/37, `matcher` 17/17.
3. No count may drop: `klinedata` 63/64, `handlers` 29/30, `wizard_quant_api` 58/58, `real_quote` 45/45,
   `trade_info_utils` 38/41, `api_base` 27/28, `strategy` 26/27, `broker` 121/128,
   `realtime_event_source` 12/13, `risk_calculation` 42/43.
4. Probes must be `cmp`-proved inert per target; a byte-mode whole-file CRLF rewrite corrupts
   `region_analyzer.py` (it turned existing `\r\n` into `\r\r\n` and produced an IndentationError at
   line 3281 — use the Edit-style textual replacement, or read with `newline=''` and write with
   `newline='\n'` after decoding). Prefer the proven-inert line-event tracer
   (`D:/Temp/t30/tracbreak.py`) or return-value wrapper probes over hand-picked line probes; an empty
   log means a broken rig, not a negative.
5. Judge by diff SHAPE, not by failing-unit names.

## 5. Deliverable
`D:/Temp/r34/DELIVER/FIX_R21-16.md` (0 ticket as received, 1 mirror + sealed-hash + cmp proof,
2 baseline, 3 取证 of the residual hunks with region/role data, 4 criterion, 5 post-patch + fire census +
panel, 6 negative evidence, 7 declaration) plus `D:/Temp/r34/DELIVER/CANDIDATE_region_analyzer.py`
(whole file, never a diff, with its `sha256sum | cut -c1-16`) only if §3 acceptance is met with no
panel regression. Repo read-only; no command over 300 s; `python -X utf8`, never PYTHONIOENCODING;
scratch by absolute Windows path under `D:/Temp/r34/`.
