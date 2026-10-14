# NOTE_R21-27b (round 35) — why the pending-call wrapper refuses `strategy_log.info(_(f'…'))`, and what is already banked

Measured 2026-10-11 17:50-17:51 on the gate-34 sealed base (generator `065e4d77243190dc`). Repo untouched:
both edits below were applied only to the mirror `D:/Temp/r30chk`, which is restored to `065e4d77243190dc`
at the end of this note.

## 1. The refusal is one line, and it is a chain-length assumption

`_try_wrap_fstring_pending_call` (`region_ast_generator.py:50717`) ends its screening with

```python
        _rest = _tail[_j + 1:]
        while _rest and _rest[0].opname in ('CACHE', 'NOP'):
            _rest = _rest[1:]
        if not _rest or _rest[0].opname != 'POP_TOP':
            return None
```

For `etf_purchase_redemption` the merge block after `@2422 BUILD_STRING 7` is

```
@2424 PRECALL 1 / @2428 CALL 1     # _(f'…')            <- gettext wrapper call
@2438 PRECALL 1 / @2442 CALL 1     # strategy_log.info(…) <- outer call, its result is discarded
@2452 POP_TOP
```

so `_tail[_j]` is the **inner** `CALL` (arg 1, passes the check) and `_rest[0]` is the **second** `PRECALL`,
not `POP_TOP` → `return None` → the region degrades to `return f"…"`, losing both call statements and the
following `return order.order_id`. The wrapper models `x.m(f'…')` (exactly one enclosing call); the real
shape here is a two-call chain, which is the standard `gettext` idiom used all over this corpus.

Work for the next attempt, stated so it is not re-derived: consume successive `PRECALL?/KW_NAMES* → CALL`
pairs until a non-`PRECALL`/`CALL` instruction, require every consumed `CALL` to take exactly 1 positional
argument, and nest one `Call` per consumed pair, pairing them with the pending callee pushes taken from the
prefix in reverse (`LOAD_GLOBAL strategy_log` + `LOAD_ATTR info` outermost, `LOAD_GLOBAL _` innermost —
`_ternary_pending_callee` currently returns a single callee, so it needs the sibling that yields the chain).
`POP_TOP` must terminate the consumed run. Census duty: count regions corpus-wide whose `_rest[0]` is a second
`PRECALL` right after the first `CALL` — that population is what changes, and it is not one file.

## 2. Banked co-requisite (measured this round, NOT landed)

`CANDIDATE_r35_R21-27_prefix_window_bound_BANKED_NOT_LANDED.py` = `be5e52b1c5100dbc` (16 lines before
`:45045`, builder `build_cand_r35_R21-27.py`). It bounds the f-string prefix window at the last statement
boundary inside it, per NOTE_R21-27 §6.

Measured effect (20-file panel rig, broker only this round):
- emitted text improved decisively: the glued `list_info00orderstrresultentrust_no…` is **gone** (0 hits);
  line 1596 now reads `return f"strategy_log_生成订单，订单号：{order!s} …"` — only the two callee names
  remain, and they belong to §1's unwrapped calls;
- **diff shape unchanged**: `etf_purchase_redemption` stays `-12 / 5 hunks / 0 landings, judge_diff=True`,
  broker holds 123/128, and the other five units are byte-stable (`ipo_stocks_order 0/0/0` intact). Reason:
  a shorter literal is still one `LOAD_CONST`, so removing junk names cannot move the instruction diff —
  the 12 missing instructions are the lost calls and the lost `return order.order_id`.

Therefore it is a text-quality fix with **zero measured unit movement**, which is exactly the class this
campaign does not install (fires without flips). It is kept because §1's fix needs it: without the window
bound, the wrapped `Call` would still carry the junk prefix parts.

## 3. Acceptance bar for R21-27

`etf_purchase_redemption` → `delta=0 hunks=0 landings=0 judge_diff=False`, broker 123 → **124/128**;
report the other five broker units before/after and the 20-file panel; a shrink without a flip is a
measured negative again, not a candidate.
