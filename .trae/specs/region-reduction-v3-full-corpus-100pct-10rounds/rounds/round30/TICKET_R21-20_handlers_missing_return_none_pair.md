# TICKET R21-20 (round 30) — `handlers._target` is missing ONE `return None` pair; treat it as an UNDER-EMISSION, the four other framings are already falsified

Owner file: `core/cfg/region_ast_generator.py`. Sealed bytes: `region_ast_generator.py = fd0e4c4d73cf5efc`,
`region_analyzer.py = 35e227ac3e7b25af`, `ast_generator_v2.py = beeaf14435e22922`.
Repo READ-ONLY `D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main` (HEAD `54f4d655`, branch
`rr-v3r01-f557fd`); mirror `D:/Temp/r38/wt`, products `D:/Temp/r38/out/`; no git writes.
Five siblings run in `D:/Temp/r34|35|36|37` — do not read or write there.

## 0. Victim and the flip
`IQCommon/logger/handlers.pyc` :: `<module>.TWHThreadController._target` — the file's ONLY failing unit
(29/30) ⇒ flip = whole-file **30/30**. Measured today on the gate-29 bytes:
```
len orig=199 prod=197  delta=-2  hunks=1  landings=3  judge_diff=True
== delete orig[73..75 @404..@406] prod[73..73] del=2 ins=0
   - @404  LOAD_CONST  None
   - @406  RETURN_VALUE
   ~ orig[83] @456 POP_JUMP_FORWARD_IF_FALSE -> idx193 | prod[81] @452 -> idx195   (2-byte shift shadows)
   ~ orig[90] @502 ... -> idx195 | prod[88] @496 -> idx191
   ~ orig[93] @516 ... -> idx197 | prod[91] @510 -> idx193
```
One deleted pair, and the three landings move by exactly the ±2 bytes that pair would have occupied —
i.e. **the whole unit hinges on one missing `return None` statement.** Confirm that reading before
inventing another: if you restore that pair in the emitted source, the three landings must vanish by
themselves (they are shift shadows, not independent defects).

## 1. Framings ALREADY FALSIFIED — do not spend your run on them
1. "The two adjacent `LOAD_CONST None; RETURN_VALUE` pairs in the original are one statement the
   product folded" — **disproved**: CPython duplicates per exit edge; there is no emission fold (round
   19 ticket #46/T20-2, r19t5 BLOCKED).
2. "A guard/terminator predicate near the loop exits decides it" — three guards were falsified **by
   ablation**, and the emitted source already contains a `return None` for the function (so the text is
   not literally missing a `return None` *somewhere* — the missing copy is the one at `@404`, inside the
   loop region).
3. "Drop the `else:` when the then-arm returns" / "rewrite `not x is not None` as `x is None`" / "add or
   remove a trailing `else: return None`" — all four combinations **compile byte-identically** on this
   3.11.7, so none can change the emitted layout. Proved by `compile()`, not by argument.
4. "No arrangement of `return None` statements can materialise a tail copy" — also proved: `else:
   return None`, `else: pass` and no-`else` give a byte-identical layout because CPython threads a
   `return None` else-arm onto the implicit function tail; a trailing function-level `return None`
   *shortens* the code instead. So the required shape is a **nesting/scope** difference, not a
   `return None` you can add.
Context you may use: the two original blocks `@404..@406` and `@408..@410` sit immediately after a
`POP_JUMP_BACKWARD_IF_TRUE -> off104` at `@402` (a while-loop bottom test) and before
`@412 LOAD_GLOBAL sys` — i.e. the loop's natural exit and the function tail are two consecutive copies
there, and the product emits only one.

## 2. Method that works here
Ablation or container-watch, never sampled line probes: the file holds 71 `'type': 'Break'` literals and
hand-picked line probes read zero fires (a broken rig, not a negative). Use the proven-inert line-event
tracer `D:/Temp/t30/tracbreak.py` (abs pyc, out path, log path, comma-separated line numbers; swallows
`SystemExit`; prints a positive-control count; must be `cmp`-proved inert per target), or wrap candidate
builder methods to log their return in the SAME process that produces the artifact. Decide every shape
question by compiling candidate sources and comparing instructions AND resolved jump targets
(`dis`'s `i.argval`; do not compute targets by hand).

## 3. Acceptance
`unit_diff.py IQCommon/logger/handlers.pyc "<module>.TWHThreadController._target" --all` must read
`len orig=199 prod=199 delta=0 hunks=0 landings=0 judge_diff=False` and `pyc_verify single --source`
must print `Equal`, file **30/30**. Any shrink without the flip is a measured negative — report the shape.

## 4. Anti-regression duties
1. Fire census over the 14-file panel (`fly/data/quotation.pyc`, `fly/data/quote.pyc`,
   `IQCommon/{api/klinedata,logger/handlers,strategy/wizard_quant_api,util/trade_info_utils}.pyc`,
   `IQData/api/api_base.pyc`, `IQData/plugins/plugin_system_realquote/real_quote.pyc`,
   `IQEngine/plugins/plugin_fly_data/{strategy/strategy,fly_api/order_api}.pyc`,
   `IQEngine/plugins/plugin_system_{trade/trade_live_broker,matcher/matcher,event_source/realtime_event_source}.pyc`,
   `IQEngine/plugins/plugin_system_risk_calculation/__init__.pyc`): `TOTAL_FIRES` + per file whether its
   product changed, comparing against `git show HEAD:<path>` bytes with CR stripped — NEVER `cmp` against
   the checked-out file (checkout is CRLF, the decompiler writes LF).
2. `quotation` stays 153/153; `order_api` 37/37; `matcher` 17/17.
3. No count may drop: `klinedata` 63/64, `wizard_quant_api` 58/58, `real_quote` 45/45, `trade_info_utils`
   38/41, `api_base` 27/28, `strategy` 26/27, `quote` 91/92, `broker` 121/128,
   `realtime_event_source` 12/13, `risk_calculation` 42/43.
4. All six batteries at recorded values (repro 9R/9, arm 0G/3R, ccneg 3G/1R, retbreak 2G/2R DRIFT=0,
   orderapi 5G/0R, tail 13G/0R); runners live at the mirror's same relative depth under `rounds/`.
5. The generator has no jump-operand channel: express the fix as a source shape.

## 5. Constraints
`python -X utf8`, never PYTHONIOENCODING; ≤300 s per command; CRLF-preserving textual patches only (a
byte-mode newline rewrite doubled `\r\n` into `\r\r\n` today and broke a file with an
IndentationError at line 3281); scratch by absolute Windows paths under `D:/Temp/r38/`; `--source` is
mandatory for judge reads; `region_analyzer.py` is owned by a sibling — do not edit it.

## 6. Deliverable
`D:/Temp/r38/DELIVER/FIX_R21-20.md` (0 ticket, 1 mirror+hash+cmp proof, 2 baseline, 3 取证 naming the
emitter of the loop-exit tail with file:line and code read, 4 criterion, 5 post-patch + fire census +
panel + batteries, 6 negative evidence, 7 declaration `CANDIDATE READY (file flip: handlers 30/30)` or
`FALSIFIED — <facts + next ticket>`) plus `D:/Temp/r38/DELIVER/CANDIDATE_region_ast_generator.py`
(whole file + `sha256sum | cut -c1-16`) only if §3 is met with no panel regression.
