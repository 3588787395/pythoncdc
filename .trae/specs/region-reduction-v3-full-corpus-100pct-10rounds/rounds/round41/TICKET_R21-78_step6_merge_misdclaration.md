# TICKET R21-78 — the step-6 obstacle, now diagnosed from block data (orchestrator, 16:04)

r105a died on the Chat daily-quota cap (23 tool uses, no deliverable). I read the site myself on the F5 base
(`996a1b1acf143458` + `566ff5c502276e48`, which I verified reproduces broker `128/128`, panel unchanged,
battery `RED=8/9`, realtime still `12/13`), and the obstacle r104a described is now fully specified.

## The chain as it actually exists in `clock_worker` (`@8904..@8980`, owner `TryExceptRegion@6`)

```
@8904 succ=[8926, 9144, 9218]  tail=POP_JUMP_FORWARD_IF_FALSE   preds=[8592]
@8926 succ=[8948, 9144, 9218]  tail=POP_JUMP_FORWARD_IF_FALSE   preds=[8904]
@8948 succ=[8964, 8976, 9218]  tail=POP_JUMP_FORWARD_IF_FALSE   preds=[8926]
@8964 succ=[8974, 9144, 9218]  tail=POP_JUMP_FORWARD_IF_FALSE   preds=[8948]
@8974 succ=[8980, 9218]         tail=JUMP_FORWARD               preds=[8964]   (arm 0 "body" jump block)
@8976 succ=[9144, 9218]         tail=JUMP_FORWARD               preds=[8948]   (false leg of @8948)
@8980 succ=[9194, 9218] n=22   tail=JUMP_FORWARD               preds=[8974]   (the real arm body)
```

Four consecutive `POP_JUMP_FORWARD_IF_FALSE` guards whose **false legs all land on `@9144`** — `@8904`, `@8926`,
`@8964` jump to `@9144` directly and `@8948` reaches it through `@8976`. That is an `and` chain with a shared
false join at `@9144`. The arm body `@8980` exits to the loop re-entry `@9194` (and `@9218`, the exception/exit
target). The oracle needs exactly one of those links folded:
`elif <@8948 test> and <@8964 chained comparison>:` — which is the varE→varF diff that flips the judge.

## Why the pipeline cannot see it: the merge is mis-declared

```
IfRegion@8948  cond=8948  merge=9194   then=[8974, 8980]  else=[8976, 9144]
IfRegion@8904  cond=8926  merge=9144   then=[8948, 8964, 8974, 8976, 8980]   else=[]
BoolOpRegion@8904                      merge=9144
```

`IfRegion@8948` declares **`merge_block = 9194`** — the *arm body's* back-edge target — and consequently treats
`@9144` as one of its `else_blocks`. The real join of its conditional false legs is `@9144`. Every
exit-agreement test that could fold `@8964` into `@8948`'s condition (`_inline_and_chain_exits_agree`,
`all_same_target`, `interrupts_boolop_forward_chain`) compares the candidate leg's false target against
**the region's merge**, so with `merge=9194` the comparison fails by construction. That is precisely r104a's
sentence "`IF_THEN_ELSE @8948` declares the back edge `@9194` as its merge, so the chain-continuation reading is
not available from region data" — now with the edge evidence.

## The rule to implement (region/block data only; no names, offsets-as-keys, counters)

For an `IfRegion` R with `condition_block` C: let `F` be the false target of C's own conditional jump.
If R's `merge_block` M is **not** reachable as any false-leg target of the guard run that starts at C, but is
reachable from R's *then-arm* terminal block only (i.e. M is the arm's continuation/back edge), and R's
`else_blocks` contain a block E that equals F, then **re-elect `merge_block = F`** and drop E from the else list.
Under the corrected merge, the existing fold criteria are re-asked for the leg block (`@8964`) whose conditional
false target is again F, and the `and`-fold emits `elif <C's test> and <leg test>:`.

Note the constraint that makes this a declaration fix rather than a text fix: the fold must be re-decided at
identification (or in an identification-terminal pass like F5's), never by rewriting emitted text.

## Other three facts still open (unchanged from R21-77 addendum 4)
* step 3 `@7164` or-chain + the `system_log.debug` that currently sits inside **another region's merge**;
* step 4 `@6322`/`@6496` `is_holiday` or-chains (same rule as step 3);
* step 1's remaining half: the 112-instruction `@7972..@8586` block needs a **positive** sequential-tail
  declaration — refusing the `elif_final_else` absorption alone collapses the unit (`+2 → −269`).

Scoring stays `rounds/round41/oracle_diff_r104.py <product>`: oracle `0 hunks / all-equal / 13/13`,
F5 base `4 hunks / instrs=-114 jsites=-9 / indeg-equal=False / 12/13`. Step 6 is exactly the fact that moves
`indeg` from `7→@9194, 2→@9144` to the original's `6, 4`.


## Addendum 1 (orchestrator, 16:07) — my first implementation of the rule is a MEASURED FALSIFICATION

I implemented the re-election in `analyze()` (mounted before `_b50_fix_try_hosted_ternary_normal_copies`,
method `_r2178_reelect_guard_false_join_merge`) on the F5 base, and scored the regenerated product with
`oracle_diff_r104.py`:

| arm | product bytes | `clock_worker` lines / hunks vs oracle | instrs Δ | judge |
|---|---|---|---|---|
| F5 base | 20190 | 241 / 4 | −114 | `12/13` |
| my v1 (loose rule) | **16520** | 168 / **30** | **−346** | **`11/13`** — `clock_worker` *and* `clock_worker.check_handle_date: Failure: Missing bytecode` |

So the merge re-election keyed **only** on "condition block's false-leg join sits in `else_blocks` and the current
merge is reachable from the then-arm" is wildly over-broad: that shape is the ordinary `if/else` case, and it
destroyed whole nested code objects (−3.7 KB, a second unit broken). Reverted byte-exactly; the mirror is back at
F5 `996a1b1acf143458`.

Two things the next attempt must therefore add, and one trap to avoid:
1. require the *whole guard run*, not a single condition block: ≥2 consecutive conditional-jump legs whose false
   targets reach the **same** block (r100a's `_r2172_find_statement_guard_chain` already encodes exactly this
   adjacency+shared-target shape — reuse it rather than re-deriving);
2. require the current merge to be a **loop re-entry** (a block at a greater offset jumps backward into it) *and*
   that the region's arm body contains no sequential statement of its own after the arm — otherwise an ordinary
   post-if join is what gets elected;
3. **do not assume `Cfg.get_block_by_offset` / `get_predecessors` exist by analogy** — my second edit aborted on a
   non-unique anchor assertion before measuring, and the API probe above shows what the module actually exposes;
   re-read the region-builder's own helper names, and prove collateral on the panel (my v1 would have failed the
   panel at `11/13`) before ever reaching a sweep.

Net: step 6 remains open, now with the loose form of the rule *measured and excluded*, which is the third time this
campaign that an over-fire was caught by the panel rather than by a gate.
