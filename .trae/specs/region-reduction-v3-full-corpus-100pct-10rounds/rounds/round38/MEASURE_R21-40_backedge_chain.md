# Round 38 late session — the `_process_cancel_order` mechanism chain, measured to one instruction

No landing. Repo byte-clean at gate-37 bytes (generator `20fa73b4e8231f0f`, analyzer
`c069d359cbfe76b0`; `git status --porcelain -- core/ site-packages/` = 0 lines; mirror
`D:/Temp/r30chk` restored and `cmp`-proved for BOTH files after every measurement). Corpus unchanged:
**6613/6617 (99.9395%), 400/402 files, residual 2 files / 4 units.** No gate label consumed.

## 1. A real analyzer defect was found and measured — `back_edge_block` mis-designation

`census_backedge_r38.py` + `probe_r39b_r38.py` (read-only; the campaign's "measure the blocking site
before editing" rule) on `trade_live_broker._process_cancel_order`:

| fact | value |
|---|---|
| loop header block | `@46`, ends `POP_JUMP_FORWARD_IF_FALSE` (the header **is** the test) |
| region `condition_block` | `None` ⇒ the landed pre-header exclusion at `region_analyzer.py:4960` (`if condition_block == header:`) is **skipped** |
| designated `back_edge_block` | `@1930..@1998` — an 11-instruction `else: strategy_log.error(…); continue` arm whose operand lands on `@44` |
| `@44` | 1-instruction `NOP`, single successor `@46` = CPython 3.11's **continue re-entry** block |
| true body tail | `@2000..@2042` = `time.sleep(0.001)` + `JUMP_BACKWARD -> @46` (lands exactly on the header) — role `CONTINUE`, *not* the back edge |

Every other source `continue` in the unit (`@350`, `@922`, `@1822`) also lands on `@44`, so the
designation is decided by `@4992`'s key, which prefers the block with **more body instructions** — the
fat `else` arm beats the thin tail. Census over 11 of the 20 panel files (393 LoopRegions):
**42** loops have a test-carrying header with `condition_block is not header` (guard skipped), **67**
designated back edges do not land on their header, and **14** designations would move, among them
`_process_order` (@360→@44, better @3128), `_process_cancel_order` (@1930→@44, better @2000) and the
**currently green** `_trade_status_handle` (@186→@44, better @830) — hence panel-before-gate.

`build_cand_r38_R21-40_backedge_header.py` → analyzer **`f7d849e974904492`**: purely additive, reuses
the landed guard's own predicate (pure-noise single-successor predecessor of the header), applies it
only in the case the guard misses, and keeps the pool when the filter would empty it. Measured panel
(20 files, tag `r38y`): **1 file CHANGED (broker), 19 SAME, every unit count held (125/128), 0 flips**
— despite 14 designation changes, only broker's product moved, because the comprehension-loop changes
are inert (`_process_cancel_order` shape `delta=-1 → 0`, `hunks=2`: the outer-else `continue` @1998
appears and the spurious jump after `COPY/POP_EXCEPT/RERAISE` disappears).

## 2. The measured progression of `_process_cancel_order`

| configuration | generator | analyzer | shape | windows left |
|---|---|---|---|---|
| landed | `20fa73b4e8231f0f` | `c069d359cbfe76b0` | `delta=-1 hunks=3` | spurious jump after `RERAISE`, `@1824`, `@1998` |
| + [R21-35a] | `a8155727b47e3bea` | landed | `delta=-2 hunks=2` | `@1826`, `@1998` |
| + [R21-40] | landed | `f7d849e974904492` | `delta= 0 hunks=2` | `@1824`, extra jump after `RERAISE` |
| **[R21-40] + [R21-35a] (pair)** | `a8155727b47e3bea` | `f7d849e974904492` | **`delta=-1 hunks=1`** | **`@1826 JUMP_FORWARD` only** |
| + 40c then-arm placement | `ccd97ff680b7434c` | `f7d849e974904492` | **`delta=-1 hunks=1`** | **`@1998 JUMP_BACKWARD` only** |

So the unit sits **one instruction from Equal** in two different ways, and the two variants each fix a
different arm. Product hashes of the panel runs are recorded in the tables of
`MEASURE_R21-35a_reanchored.md` (pair, tag `r38z`) and here (40c, tag `r39c`).

## 3. Why 40a and 40b are inert, proven by a conjunct probe rather than by reading

`build_cand_r38_R21-40a_arm_continue.py` (**`e845b06fc515c221`**) and
`build_cand_r38_R21-40b_r39b_reentry.py` (**`8b56ad6dfd874c01`**) both produced broker products
**byte-identical to the pair** (md5 `bcaeb54d65e5`, size 179228 for all three) ⇒ neither fired. The
probe (247 records, `PROBE_R39B_conjuncts_sample.txt`) names the blocking conjunct for 40b:

```
[R39BPROBE] T@1822 tail=1712 Tgen=False Tinblocks=False Tinreg=False Tinbe=False
            Tpreds=[1710, 1712] pay=['JUMP_BACKWARD'] Llast=POP_TOP
            Tlast=JUMP_BACKWARD land=44 hdr=46 reentry=True
```

Everything the widened rule needs is true — payload is one backward jump after dropping
`EXTENDED_ARG` (the noise convention this file itself uses at `:27226`), the landing is the pure-noise
continue re-entry block (`reentry=True`) — **except** `len(T.predecessors) == 1`: the block has TWO
predecessors (`@1710` the `pass` arm's jump and `@1712` the else arm's fall-through). That is not a
flaw in the rule's arm-privacy test (its own comment forbids claiming shared blocks); it says the
source `continue` is the **chain's shared tail**, which is what 40c then exploited: hand the Continue to
the then-suite of the `If` the try body ends with (`not orelse` as the structural signature), which
restores `@1826` — the body's normal-completion edge — and moves the loss to `@1998`.

## 4. The next attempt, stated as one rule

`@1998` is the outer `else` arm's own `continue`, and under 40c it is the only loss left. The rule that
emitted it under the pair was 35a's body-tail append; 40c replaced that append. So the closure is:
**keep 40c's then-arm placement AND let the arm-tail rule claim a chain-shared continue block when the
shared block is entered only from arms of the same chain** — i.e. relax `[R39-B]`'s
`len(_r39_Tpreds) == 1` to "all predecessors are members of the same region's arm/then-else block sets"
(measure the population of that relaxation first; `PROBE_R39B` already prints the fields needed, so the
census is a filter over its log). Acceptance bar, unchanged: `_process_cancel_order` `delta=0 hunks=0`,
judge `Equal`, broker **125/128 → 126/128**, corpus 6613 → **6614/6617**, no file's count decreased.

## 5. r66a's clock_worker census and candidate (banked, delivered this session)

`CENSUS_R21-38A_r66a.md` + `CANDIDATE_r66a_ibc_prefix_guard_BANKED_not_landed.py` (**`07ff9a163b07140a`**),
built on `c4a934d595200c84`. Probes proven inert (product byte-identical 22322 = 22322). Verdicts:
`IfRegion@7270` is **never dispatched** — the arm is rendered inside
`_generate_if(7186) → _if_generate_full_elif_chain → _if_generate_elif_chain`, at the first-elif-arm
`inline_boolop_chains` consumption site (analyzer recorded `chain@7186.inline_boolop_chains[id(block@7248)] =
{'blocks':[7248,7270]}`), which explains my fully-inert hook B. The fold filters `POP_TOP` as noise, the
reconstructor silently drops the non-expression CALL prefix, and `for _cb in _chain_blocks[1:]:
generated_blocks.add(_cb)` marks `@7270` whole; `prefix_emitted_upto[@7270]` is `None`, the cutter was
never asked. Ablation positive control: stubbing `_if_generate_elif_chain` only for entry 7186 removes
the fused line and brings the debug call back (−4125 bytes, debug=1).
The delivered candidate is a **refusal-only** guard (existing cutter + existing ledger, emits nothing,
so double-emission is impossible by construction) at both fold sites: `delta −6 → 0` and the six `@7270`
instructions reappear, 20-file panel 19 SAME / 1 CHANGED / 0 regressions / **0 flips** — they re-land at
the chain tail (a 17-instruction move window, `hunks 5 → 6`), so closing it fully needs a nested-`If`
injection ahead of `elif_bodies`, which r66a flags as beyond a fourth-consumer ticket.

## 6. Also still open

`_sync_worker` (analyzer compound-while rebuild, `FIX_R21-39_r65a.md`), `_process_order` (−68/14,
`TICKET_R21-37`), and r67a's merge-block census (clock_worker (B)) which was still running when this was
written. Next gate label remains **38** against `rounds/round37/after`, and it is only owed once a
candidate flips a unit.
