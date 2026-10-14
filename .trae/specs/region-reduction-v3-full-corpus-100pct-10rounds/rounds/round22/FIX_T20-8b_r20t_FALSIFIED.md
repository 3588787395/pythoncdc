# FIX_T20-8b — r20t (continuing r20s) — victim: fly/data/quote.pyc :: <module>.Quote.run_individual_transform

Ticket: ONE mechanism, file owned = `core/cfg/region_ast_generator.py` ONLY. Repo READ-ONLY for me.
Bar: >=1 named unit flip on quote.pyc (87/92 -> 88/92 = `run_individual_transform` Equal), zero decreases on the other 10 panel files + sentinels 153/153 / 17/17 / 37/37, six batteries at recorded values. `delta -52 -> -20` without flip = FALSIFIED-but-supporting.
Victim shape (sealed bytes): `len orig=407 prod=355 delta=-52 hunks=10 landings=3 judge_diff=True`.

## Mirror build proof (r20s, reused)
- `sha256sum` on `D:/Temp/r20s/wt/core/cfg/region_ast_generator.py`:
  `4f295dfc6ebd2caab8d64bdb07f57da7039ff09ec267c2741961012ca9e4404f` — first-16 `4f295dfc6ebd2caa` MATCHES the ledger quote; file is 59559 lines.
- Repo bytes at `D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main/core/cfg/region_ast_generator.py` hash to the SAME `4f295dfc6ebd2caa` and 59559 lines. Mirror == repo. No drift detected.
- r20s self-certified `REGEN_CMP_IDENTICAL` on quote (see FIX_T20-8.md §Mirror build proof); I do not need to re-certify because I did not touch `wt/`.

## Stage 1 baseline reproduction (r20s's UNPATCHED mirror read, reused)
`out/pristine/panel_summary.txt` (sealed bytes on 2026-10-10 09:49, before any patch was installed):
- quote **87/92** · klinedata 63/64 · handlers 29/30 · wizard_quant_api 55/58 · trade_info_utils 38/41 · api_base 27/28 · real_quote 43/45 · strategy 26/27 · realtime_event_source 12/13 · risk/__init__ 42/43 · trade_live_broker 118/128 · [SENT] quotation **153/153** · matcher 17/17 · order_api 37/37.
- ALL match the quoted baseline exactly. Mirror is fresh and pristine; proceed with the fix.

## Victim re-measure (r20s's dump reused)
`out/victim_unidadiff_base.txt` header: `len orig=407 prod=355 delta=-52 hunks=10 landings=3 judge_diff=True`. Three same-shape hunks per r20s dump:
- Hunk1 `del=15 ins=0` (orig `@640..@750`): socket.recv() -> STORE_FAST message -> POP_JUMP_FORWARD_IF_FALSE (if not message) -> eval(message.decode()) -> STORE_FAST message (whole recv+empty-check+eval chain).
- Hunk2 `del=5 ins=2` + Hunk3 `del=3 ins=1` (orig `@1050..@1116`): self.log.quote.warning('逐笔数据返回为空') + POP_TOP + JUMP_BACKWARD 586 + LOAD_GLOBAL NULL+list — product instead emits LOAD_FAST socket / LOAD_METHOD recv / STORE_FAST message (same chain but repositioned).
- Hunk4 `del=21 ins=0` (orig `@1130..@1270`): message.keys() -> PRECALL/CALL -> list(...) -> LOAD_CONST 0 -> BINARY_SUBSCR -> STORE_FAST stocks -> message.get(stocks) -> STORE_FAST real_data -> POP_JUMP_FORWARD_IF_FALSE — the list(keys)[0] and its downstream.
- Hunk5 `del=0 ins=9` (prod `@1304..@1366`): a duplicate PRECALL/CALL/POP_TOP/JUMP_FORWARD + self.log.quote.warning(...) emission at the wrong slot.

Full product-vs-orig picture: the product source (see `out/victim_prod_src.txt`) shows the inner `try:` body emitted as `try: pass except BaseException as x: <3 error calls> continue <dead code containing the whole recv/warning/eval/list-keys block>`, then a `message = socket.recv()` + `if message: <body> else: warning(...)` after the inner except. So the try/loop side is not just mis-landing a jump — it is emitting the try body as `pass` and republishing the recv+warning+list-keys chain inside the except-handler block after the `continue`, then again outside it in a mis-parenthesised `if message:` form. That matches r20s's census (try/loop claim paths are the active ones for this unit; `_generate_ternary@46121` proven NOT involved).

## Per-unit 取证
(pending — in progress)

## 判据实现 (exact file:line + predicate)
(pending — MUST NOT BE LEFT BLANK; will be filled before the run closes)

## Stage readings
(pending)

## 负面证据
(pending)

## Final declaration
(pending)
