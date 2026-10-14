# TICKET R21-37 — `_process_order`: a ternary used as a call argument renders as an empty if-skeleton, and one f-string call statement is dropped entirely

Registered from measurements taken on the **gate-36 landed bytes** (generator
`37997bdac555b2e9`, analyzer `efd455859b69d8a1`). Victim:
`site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc`,
co-name `_process_order`, sealed shape after gate 36: `orig=519 prod=454 delta=-65/-68`,
17 alignment windows (`hunks=14` by `unit_diff`). Rig used: `D:/Temp/r36/align_unit.py`
(built because `unit_diff` prints counts without per-hunk detail for some units); raw
windows saved at `D:/Temp/r36/po_align.txt`. This ticket is written from those windows only —
nothing below is inferred from reading the decompiled source.

## Class (a) — ternary as a CALL argument loses both arms and the call

```
orig @2632 LOAD_CONST 'OPEN' / @2634 COMPARE_OP ==
     @2640 POP_JUMP_FORWARD_IF_FALSE to 2646
     @2642 LOAD_CONST '开仓'      / @2644 JUMP_FORWARD to 2648
     @2646 LOAD_CONST '平仓'
     @2648 LOAD_FAST order / @2650 LOAD_ATTR amount
     @2660 KW_NAMES / @2662 PRECALL / @2666 CALL / @2676 PRECALL / @2680 CALL / @2690 POP_TOP
prod @2316 LOAD_CONST 'OPEN' / @2318 COMPARE_OP ==
     @2324 POP_JUMP_FORWARD_IF_FALSE to 2328
     @2326 JUMP_FORWARD to 2330
     @2328 NOP                        ← the test survives, both arms and the call do not
```
The same signature recurs at `orig @2388..@2426` (`'非备兑类型委托'` / `'备兑类型委托'` +
`KW_NAMES/PRECALL/CALL`), and each recurrence is one of the 17 windows. What CPython produces
for an empty conditional expression — `POP_JUMP_IF_FALSE`, `JUMP_FORWARD`, `NOP` — is exactly
what is emitted, so the AST reaching `compile()` holds an `IfExp`/`If` whose arm values are
**absent**, not a wrong jump. That makes this an expression-assembly defect upstream of the call
builder, not a landing/threading defect.

Untested family hypothesis, stated as untested: gate 35 landed R21-27 for
`etf_purchase_redemption`, whose root was the f-string prefix window sweeping in preceding
statements and the gettext two-call idiom `_(f'…')` defeating `_try_wrap_fstring_pending_call`.
Here a `…(… if … else …, …)` call argument collapses the same way a pending-call wrapper would if
it declined and the caller then fabricated nothing. Do **not** book that as the cause: measure
which builder returns the empty arms (ablation or a line intersect, the way `R21-33`'s emitting
line was pinned at `13415` by `D:/Temp/r36/who_negates_r36.py`), then check whether the two cases
share it.

## Class (b) — one whole `strategy_log.info(f'…')` statement is dropped

```
orig @1634 LOAD_CONST '股票' / @1636 STORE_FAST type_str
     @1638 LOAD_GLOBAL NULL+strategy_log / @1650 LOAD_ATTR info / @1660 LOAD_GLOBAL NULL+_
     @1672 LOAD_CONST '生成订单，订单号：' / @1674 LOAD_FAST order / @1676 LOAD_ATTR order_id
     @1686 FORMAT_VALUE str / @1688 LOAD_CONST ' ' / @1690 LOAD_FAST type_str
     @1692 FORMAT_VALUE str / @1694 LOAD_CONST '代码：' / @1696 LOAD_FAST order
     @1698 LOAD_ATTR symbol / @1708 FORMAT_VALUE str / @1710 LOAD_CONST ' 数量：'
prod @1634 LOAD_CONST '股票' / @1636 STORE_FAST type_str
     @1638 LOAD_FAST order / @1640 LOAD_ATTR entrust_direction     ← 15 instructions gone
```
This is a `delete` window, i.e. the statement is not relocated, it is absent, and the surrounding
statements are in the right order. Whether the JoinedStr was destroyed at AST level (the R21-27
root, which produced a *glued literal* rather than a loss) or the statement was claimed by
another region and never emitted are two different mechanisms — the emitted product shows no glue
here, only absence, so they must be distinguished before editing.

## Why this ticket is queued, not dispatched

Neither class alone flips `_process_order`: 17 windows must all close for the unit to reach
`delta=0 hunks=0`, and the corpus rule I work under accepts fix tickets on **measured unit
flips**, not on shrinks — a byte-moving, non-flipping edit gets banked and reverted, which is
exactly what happened to `7344dcc566442e58` earlier in this round. So the next action on this
ticket is not "implement class (a)": it is to first measure, read-only, whether the same empty-arm
predicate fires in any unit that is **one window** from flipping. The units one window away right
now are `_process_cancel_order` (`-1/3`, live with engineer r60a) and, if r62a's arm-order rule
lands, `_sync_worker` (`-3/5`). If the predicate fires in none of them, class (a) is worth
implementing only as a co-requisite in a bundle that demonstrably flips `_process_order`
end-to-end, and that bundle has to close all 17 windows.

## Population duty before any edit

Count, corpus-wide and read-only, how many call arguments are conditional expressions with
constant arms, and how many products change when the arms are restored. A previous ticket on this
codebase claimed a family from one victim and the census returned a population of one; the six
duplicated-module canaries in the 20-file panel (`arg_checker`×3 = 49/39/43, `profiler_func`×3 =
17/15/18) are mandatory on any candidate here, because two over-firing criteria were caught by
those canaries and not by the residual-shaped panel.

## Census result (measured after writing the above) — no flip-adjacent target, so this stays queued

Ran `D:/Temp/r36/align_unit.py` on both units that are one window from flipping, on the same
gate-36 bytes:

| unit | shape | class-(a) empty-arm triples in its windows |
|---|---|---|
| `_sync_worker` | `orig=411 prod=409 delta=-2`, 17 windows, dominated by relocations (`delete orig[131..233]` = 102 instructions that reappear as `insert prod[265..400]`) | **0** |
| `_process_cancel_order` | `-1/3`, one missing `JUMP_BACKWARD` inside the try body | **0** |

So restoring the ternary arms cannot flip anything that is currently one window away; it is worth
implementing only inside a bundle that closes all 17 windows of `_process_order`, whose classes are
(a) empty ternary arms, (b) a dropped `strategy_log.info(f'…')` statement, and (c) the remaining
single-instruction `replace` windows that are jump-target offsets, not losses. `_sync_worker`'s own
windows are the relocation family already assigned to r62a's arm-order criterion, so the two
tickets must not be merged into one criterion on the strength of living in the same file.

