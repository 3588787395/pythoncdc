# TICKET R21-16 (round 29, banked) — the suite following an inner `try/except` is emitted INSIDE the handler, after the handler's `continue`

Owner file (the ONLY file you may modify, and only inside your mirror):
`core/cfg/region_ast_generator.py` (handler-suite / try assembly). If your measurement shows the
root is an analyzer *ownership* declaration, do not edit `core/cfg/region_analyzer.py` — write it
up as the next ticket with evidence and deliver the generator-side result you actually have.
Sealed hashes of the read-only twins: `region_analyzer.py = 35e227ac3e7b25af`,
`ast_generator_v2.py = beeaf14435e22922`, `region_ast_generator.py = ac8ec5aa2d5796ea`
(re-verify against HEAD before you copy; sibling landings this round may have moved the generator hash).
Repo (read-only): `D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main`, branch `rr-v3r01-f557fd`.
Use mirror `D:/Temp/r32/wt`, products `D:/Temp/r32/out/<tag>/`. **No git writes.**
Sibling tickets in flight on the same file: R21-13 (`D:/Temp/r29`), R21-14 (`D:/Temp/r30`),
R21-15 (`D:/Temp/r31`) — stay inside `D:/Temp/r32`, read nothing from the others.

## 0. Victim and the file flip it buys
`fly/data/quote.pyc` :: `<module>.Quote.run_individual_transform`. The file is 91/92 and this is its
ONLY remaining failing unit, so the flip is `91/92 -> 92/92` = whole-file flip.
Measured today on the sealed product: `len orig=407 prod=355 delta=-52 hunks>=3 landings=? judge_diff=True`,
first hunk = **15 consecutive original instructions deleted** (`@640..@750`):
```
LOAD_FAST socket / LOAD_METHOD recv / PRECALL / CALL / STORE_FAST message
LOAD_FAST message / POP_JUMP_FORWARD_IF_FALSE / LOAD_GLOBAL eval / LOAD_FAST message /
LOAD_METHOD decode / PRECALL / CALL / PRECALL / CALL / STORE_FAST message
```
i.e. `message = socket.recv()` and `if message: message = eval(message.decode())` are gone.

## 1. Why they are gone — read the emitted source, `quoteOK.py:1326-1347`
```python
        while self.individual_subscribe.isSet():
            try:
                try:
                    pass                                  # 1329 <- the inner try body was STOLEN
                except BaseException as x:
                    self.log.quote.error('eval转化逐笔数据异常')
                    self.log.quote.error('数据内容：' + str(message))
                    self.log.quote.error('异常内容:' + str(x))
                    continue                                # 1334
                    if self.individual_subscribe.isSet():   # 1335 <- belongs AFTER the try statement
                        pass
                    else:
                        socket.close(); context.term(); ...
                    message = socket.recv()                 # 1342 <- the 15 deleted instructions
                    if message:
                        pass                                # 1344 <- then-body also stolen
                    else:
                        self.log.quote.warning('逐笔数据返回为空')
                    stocks = list(message.keys())[0]
```
Everything from line 1335 onward sits in the handler suite **after a `continue`**, so CPython >= 3.10
dead-code-eliminates it on `compile()` — that is exactly the 52-instruction loss. The generator
appended the blocks that follow the `Try` node into the handler's body instead of after it, and
hollowed the vacated bodies out to `pass`. Same family as the two landed fixes in this area
(`_generate_try` arm-tail ownership, gate 27; else-arm remainder, gate 28) but in the opposite
direction, and it is NOT the same criterion — do not re-run those.

## 2. What to change
Find where the handler suite is assembled (`_generate_handler_body_statements`, and whatever
appends post-`Try` blocks to it) and stop claiming blocks that lie beyond the handler's own
terminator: once a handler's declared arm ends in `Continue`/`Break`/`Return`/`Raise`, the
remaining blocks of the enclosing loop body must be emitted as siblings AFTER the `Try` node, not
inside the handler. Reproduce the decision with `compile()` on 3.11.7 first: confirm that a
statement after `continue` in the same suite really disappears from the bytecode, and that the
sibling placement restores it.

## 3. Acceptance (hard, measured — quote literal rig output)
Rig: `python -X utf8 .trae/specs/region-reduction-v3-full-corpus-100pct-10rounds/unit_diff.py <pyc-rel> <qualname> --all`
- `run_individual_transform` must read `len orig=407 prod=407 delta=0 hunks=0 landings=0 judge_diff=False`
  and `scripts/pyc_verify.py single <abs .pyc> --source <product>` must print `Equal`, file `92/92`.
- Minimum content proof in the emitted text: `message = socket.recv()` reachable (NOT after a
  `continue` inside a handler) and the inner `try` body not `pass`.
- Shrink-without-flip is a measured negative; report it as one.

## 4. Anti-regression duties (all mandatory before delivering a candidate)
1. Fire census over the 14-file panel used this round (`fly/data/quotation.pyc`, `fly/data/quote.pyc`,
   `IQCommon/{api/klinedata,logger/handlers,strategy/wizard_quant_api,util/trade_info_utils}.pyc`,
   `IQData/api/api_base.pyc`, `IQData/plugins/plugin_system_realquote/real_quote.pyc`,
   `IQEngine/plugins/plugin_fly_data/{strategy/strategy,fly_api/order_api}.pyc`,
   `IQEngine/plugins/plugin_system_{trade/trade_live_broker,matcher/matcher,event_source/realtime_event_source}.pyc`,
   `IQEngine/plugins/plugin_system_risk_calculation/__init__.pyc`): report `TOTAL_FIRES` and per-file
   `cmp` vs the sealed product. Broad fires that change products = narrow it or report as negative.
2. `fly/data/quotation.pyc` must stay 153/153.
3. No regression: `klinedata` 63/64, `handlers` 29/30, `wizard_quant_api` 57/58, `trade_info_utils`
   38/41, `api_base` 27/28, `real_quote` 44/45, `strategy` 26/27, `order_api` 37/37, `matcher` 17/17,
   `broker` 121/128, `risk_calculation __init__` 42/43, `realtime_event_source` 12/13.
4. Probes must be `cmp`-proved inert per target else VOID; empty probe log = SUSPECT (log the
   exception; no bare `except`). Prefer in-process ablation of the candidate handler/try builders.
5. Judge by diff SHAPE, not by failing-unit names.

## 5. Hard constraints
Repo read-only, no git writes; no command over 300 s; `python -X utf8`, never PYTHONIOENCODING;
byte-level patching preserving mixed CRLF/LF; scratch/logs by absolute path under `D:/Temp/r32/`;
mirror proof = 3 sealed hashes + regenerate this victim's product and `cmp` it against the repo's
committed `quoteOK.py` before any measurement.

## 6. Deliverable
`D:/Temp/r32/DELIVER/FIX_R21-16.md` — (0) ticket as received, (1) mirror + hash + cmp proof,
(2) baseline readings, (3) 取证 with file:line, (4) criterion implemented, (5) post-patch readings +
fire census + quotation + panel table, (6) negative evidence, (7) final declaration:
`CANDIDATE READY (file flip: quote 92/92)` or `FALSIFIED — <measured facts + next ticket>`.
Plus `D:/Temp/r32/DELIVER/CANDIDATE_region_ast_generator.py` (whole file) with its
`sha256sum | cut -c1-16` only if acceptance is met with no panel regression.
