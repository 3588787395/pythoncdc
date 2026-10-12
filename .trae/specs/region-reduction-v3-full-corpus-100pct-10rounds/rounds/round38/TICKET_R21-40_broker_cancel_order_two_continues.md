# TICKET R21-40 — `_process_cancel_order` needs two arm-level continuations, not one (broker 125/128)

Written from `dump_finally_r38.py` (committed here; prints the neighbourhood with jump operands
resolved, which the aligner blanks) — not from the earlier prose premise. It **replaces** the
round-37 claim in `FIX_R21-35a_r37.md` that "the trailing `continue` belongs inside the `Try` body":
that hunk is half right, and this file says which half.

## The original's shape, read off the bytecode

`_process_cancel_order`, @1746..@2042 (orig 333 instructions, `while True:` test at @44/@46):

| orig | instruction | reading |
|---|---|---|
| @1746..@1820 | `error(_('后端服务 撤单失败，错误原因：%s' % …))` + `POP_TOP` | the **inner `else` arm** of `if error_no == 0 / elif … node_type=='7' / else` inside the `try` body |
| @1824 | `JUMP_BACKWARD -> @44` | that inner `else` arm ends with **`continue`** (its own suite) |
| @1826 | `JUMP_FORWARD -> @2000` | the `try` body's **normal-completion** edge (the `pass` arm and the `error_no==0` arm reach it) landing on `time.sleep` |
| @1828..@1928 | `PUSH_EXC_INFO … BaseException … POP_EXCEPT / JUMP_FORWARD -> @2000 / RERAISE …` | the handler; ends without a jump |
| @1930..@1994 | `error(_('当前订单状态不支持撤单'))` + `POP_TOP` | the **outer `else` arm** of `if order in self.orders: … else:` |
| @1998 | `JUMP_BACKWARD -> @44` | that outer `else` arm also ends with **`continue`** |
| @2000..@2042 | `time.sleep(0.001)` + `JUMP_BACKWARD -> @46` | body tail |

So the source is:

```
if order in self.orders:
    entrust_no = order.entrust_no
    if entrust_no is None: …; continue
    try:
        if business_type in ('future','rzrq'):
            if error_no == 0: …
            elif error_no == T2SDK_RTNPACK_EMPTY and node_type == '7': pass
            else: strategy_log.error(_('…错误原因…')); continue     # ← continue is IN this arm
    except BaseException:
        strategy_log.error('…错误信息：%s' % get_traceback_message())
else:
    strategy_log.error(_('当前订单状态不支持撤单'))
    continue                                                        # ← and IN this arm
```

Nothing follows the `try` statement inside the `if order in self.orders:` arm — the `continue` is not
an arm tail, it belongs to two individual arms.

## What each candidate does, measured

* landed `20fa73b4e8231f0f`: `delta=-1 hunks=3` — the product hoists the inner-else `continue` to
  **after** the whole `try/except` (committed product `…OK.py:568`), which is why a `JUMP_BACKWARD`
  appears after `COPY/POP_EXCEPT/RERAISE` (dead code after a re-raise) and why the inner `else` arm's
  own back edge and the body's normal-completion edge are both missing.
* banked `a8155727b47e3bea` ([R21-35a] re-anchored, 44 lines inside `_generate_try`): the spurious
  jump after `RERAISE` disappears and the inner `else` arm's back edge appears at @1824 ⇒ `delta=-2
  hunks=2`. But the `continue` is placed at the **end of the `Try` body**, so the `pass` arm and the
  `error_no==0` arm now jump back too (product `@1710 JUMP_FORWARD -> @1822` lands on that
  `continue`) and the body's own `JUMP_FORWARD -> sleep` (@1826) is never emitted.
* therefore exactly two instructions remain, and they are two different arm-membership facts.

## The two work items, in order, each with its acceptance measurement

1. **[R21-40a] Attach the trailing `continue` to the arm that owns it, not to the `Try` body tail.**
   Site: the hunk in `a8155727b47e3bea` at `region_ast_generator.py:30339+` (inside `_generate_try`) —
   the statement list it extends is the body, and the arm it should extend is the last arm of the
   inner `if/elif/else` chain. Structural discriminator (no names, no offsets): the arm whose **own**
   normal-completion edge is absent from the region's merge set while the enclosing `try` body still
   has a normal-completion edge — i.e. the back edge belongs to the arm, and the body-end edge must
   survive separately. Acceptance: `allwin_r63.py` on `_process_cancel_order` loses the `@1826`
   window, `hunks` 2 → 1, broker holds 125/128 or rises.
2. **[R21-40b] Emit the outer `else` arm's trailing `continue`.** Same family as the closed
   `#83` (`ipo_stocks_order` arm-tail continue swallowed by the P1-3b suppression) and as the landed
   `[R21-36]` continue-arm hoisting — this one is an `else` arm whose body ends in a statement and
   whose fall-through successor is the enclosing body tail. Acceptance: the `@1998`
   `JUMP_BACKWARD` appears ⇒ `_process_cancel_order` `hunks=0 delta=0`, judge `Equal`,
   broker **125/128 → 126/128**, corpus 6613 → **6614/6617**.
   Measure the population first: how many `else` arms in the 20 panel files end in a statement whose
   block's fall-through is a `JUMP_BACKWARD` in the original but not in the product (the suppression
   that ate it is a rule with several call sites — count them before patching one).

Do **not** attempt a "duplicate the `finally` suite per exit edge" rule: the product already emits
both copies (they are the two `PRECALL/CALL/POP_TOP` pairs at @1810 and @1980); the difference is one
`continue` and one body-end edge. The `AST has no jump operands` limit does not bind either item,
because both choose a suite, not a target.

Both items must land together to flip the unit; each alone is a banked co-requisite under the
fires-without-flips rule, so measure `1`, then `1+2`, and gate only the pair.
