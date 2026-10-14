# FIX R21-41 — the last broker unit is ONE BYTE from byte-identical (measured), and §49's cause is partly falsified

All readings taken in `D:/Temp/r30chk`, restored and `cmp`-proved to the landed bytes afterwards
(generator `20fa73b4e8231f0f`, analyzer `c069d359cbfe76b0`). Candidate under test: generator
**`1bdc3206451cef57`** = `c1eba55fb9900412` + `build_cand_r38_R21-41_tail_continue.py`
(E1 reworks the `[R8 fix]` Continue emission at `region_ast_generator.py:27286-27294`; E2 re-narrows the
shared-predecessor clause added by 40d), used with analyzer `f7d849e974904492`.

## Byte-level parity against the original code object

`_process_cancel_order` (`co_code` = 2044 bytes in both):

| configuration | differing `co_code` bytes | which operand |
|---|---|---|
| landed | 3 opcode-level windows, `delta=-1` | several statements/jumps |
| `c1eba55fb9900412` (40d) | **2** — offsets 1711 and 2043 | pass-arm `JUMP_FORWARD`; loop-tail `JUMP_BACKWARD` |
| `1bdc3206451cef57` (R21-41) | **1** — offset 1711, `orig 0x37` / `prod 0x39` | pass-arm `JUMP_FORWARD`: `@1712 + 55*2 = @1822` (orig) vs `+ 57*2 = @1826` (prod) |

Already equal, measured: `co_exceptiontable` (37 bytes, identical), `co_names`, `co_varnames`,
`co_consts` (24). Only `co_linetable` differs, and line attribution is not what the judge means by
control flow. So the unit is a single relative-jump operand away from being the *same code object*.

## How §49's named cause must be corrected

§49 claimed the loop-body-terminal `continue` (pre-E1 product line 575) was "the" remaining blocker.
E1 shows that was right about the **tail** and wrong about the **cause being spurious**:

* removing that `continue` does exactly what the `compile()` experiment predicted: the final byte at
  offset 2043 stops differing — our tail jump moves onto the original's `@46` (body start) instead of
  the continue re-entry `@44`;
* the same removal **creates** the surviving difference, because in the original the
  `elif … node_type == '7': pass` arm jumps **into** the shared continue block `@1822` — i.e. that
  chain-level trailing `continue` is real for arm B, not spurious;
* and E1 as written also removes a `JUMP_BACKWARD` that `ipo_stocks_order` needs (`@5582`, product
  1181 → 1180, broker 125 → **124/128**), so `[R8 fix]`'s header-landing condition is genuinely
  required for some loops and wrong for this one.

What is left is therefore not "which statements exist" (the streams are identical) but **which block
CPython picks as a jump target** — the standing no-landing-channel boundary, now demonstrated at
single-byte resolution instead of argued.

## Next steps, each decidable by `compile()` before any generator edit

1. **Narrow E1 by designation, not by landing**: suppress the Continue only when the block **is**
   `self._current_loop.back_edge_block` (which the [R21-40] analyzer fix now makes accurate: `@2000`,
   the sleep block), and leave `[R8 fix]` untouched for every other payload-carrying back-edge block.
   Check `ipo_stocks_order` FIRST — it is this family's canary, and a candidate that moves it is wrong
   regardless of what it does to the victim unit.
2. **Ask the layout question directly**: enumerate source shapes for the inner
   `if error_no == 0 / elif … '7': pass / else: error(…)` chain in which arm B's exit lands on the same
   block as arm C's fall-through (`@1822`) while arm A's exit lands past it (`@1826`), and the loop tail
   still lands on `@46`. If no source shape reproduces that combination, the unit is provably at the
   generator's expressiveness limit and the ticket must be re-filed against the analyzer's chain/merge
   declaration (which block is declared the chain's tail), not against the emitter.
3. Under (1) alone the expected best case is broker **125/128 held** with the victim unit at 1 byte —
   still zero flips, so a gate is only owed once the byte disappears.

## Ledger

Nothing installed this round: `git status --porcelain -- core/ site-packages/` = 0 lines, mirror
`cmp`-restored, corpus sealed at **6613/6617 units (99.9395%) · 400/402 files · residual 2 files / 4
units**, gate label **38** still owed to the first candidate that flips a unit. Banked here:
`CANDIDATE_r41_one_byte_BANKED_not_landed.py` — the closest any candidate in this campaign has come to
turning a unit green.
