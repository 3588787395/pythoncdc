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


## Addendum 2 (orchestrator, 16:16) — my tightened rule is INERT, and the reason is now known

Three measured arms, all scored with `oracle_diff_r104.py` (base for comparison = landed `1471c92e`, whose
`clock_worker` is 244 lines / 4 hunks / `instrs=-112` / `jsites=-9` / `12/13`):

| arm | analyzer sha16 | product bytes | lines / hunks | instrs Δ | judge |
|---|---|---|---|---|---|
| landed base (reference) | `1471c92eca157e46` | 20555 | 244 / 4 | −112 | `12/13` |
| v1 loose rule | — | **16520** | 168 / 30 | −346 | **`11/13`** (breaks `clock_worker.check_handle_date`) |
| v2 = landed + ① ②(F and E both in `else_blocks`) ③ M backward-entered ④ ≥2 shared legs ⑤ | `746cd2f3cb60d581` | 20555 | 244 / 4 | −112 | `12/13` — **byte-identical to base: inert** |
| v3 = v2 with ③ replaced by "M outside the region's own blocks" | `e924b2b78f949951` | 20555 | 244 / 4 | −112 | `12/13` — **still inert** |

What the pair of inert results buys, stated as facts rather than guesses:

1. **Conjunct ③ as I wrote it cannot be satisfied here.** `@9194` is *not* entered by any jump from a larger
   offset — the jumps into it come from `@8980` and from the loop-tail blocks at smaller offsets, so "a
   predecessor with a greater start offset exists" is false for this loop re-entry. My v2 was therefore
   non-firing by construction, and its byte-identical product proves it (a rewrite that fires would move the text).
2. **Removing ③ (v3) is still inert**, so at least one further conjunct also rejects the target — the next hand should
   not assume ①/②/④/⑤ hold as I specified them. Concretely: the false-leg pair for `condition_block=@8948` is
   `F=@8976` (a pure `JUMP_FORWARD`) with `E=@9144`, and the dump shows `else_blocks=[8976, 9144]` — so ①/② *should*
   hold — which leaves ④ as the likely reject: my `_false_join` folding maps **@8904/@8926/@8964**'s false legs to
   `@9144` directly, but those blocks are in the *parent* `IfRegion@8904`'s block set, and `@8948`'s own block set
   contains only `@8948/@8964/@8974/@8976/@8980`, where the second conditional leg is `@8964` — whose **true** leg
   is taken and whose false leg is `@9144`, so `_n == 2` only if `@8964` is in `R.blocks` *and* the fold counts it.
   **The first thing the next attempt should do is print the per-conjunct verdict for the @8948 region** (a
   read-only diagnostic inside the pass, with a byte-identical-product check to certify the probe inert) instead of
   iterating whole predicates blind. My own attempt to add that print failed on an anchor assertion, so no
   measurement was made — recorded here so it is not counted as a result.
3. **Process incident, recorded because it is the kind of thing that silently corrupts a campaign:** my v2 script used
   the *relative* path `core/cfg/region_analyzer.py` while the shell's cwd had reset to the repo root, so it **wrote
   into the repository's production source** instead of my mirror. Nothing was committed and nothing was installed: I
   detected it while verifying why v2 reported a *smaller* file than the F5 base, backed the bytes out to
   `D:/Temp/r91m/v2_accidental_repo_write_746cd2f3cb60d581.py`, and restored `core/cfg/region_analyzer.py` from the
   banked landed copy — re-verified as `1471c92eca157e46` / 2,121,884 B with `git status --porcelain -- core/`
   **empty** and 0 dirty products. Lesson pinned to memory: patch scripts must use absolute paths, and every
   "patched the mirror" claim ends with a repo-cleanliness check.

Base for the next attempt is unchanged: **F5 `996a1b1acf143458`** (mirror restored to it), with the three still-open
facts (steps 3, 4, and the positive tail claim for `@7972..@8586`) plus step 6's merge declaration, whose loose form
(v1) is excluded, whose ③ form (v2/v3) is measured inert, and whose remaining blocker is now "print the conjunct
verdict before writing the next variant".


## Addendum 3 (orchestrator, 16:25) — the conjunct probe fired nothing useful because my premise was wrong: the fold data is already at the PARENT region

I added the read-only conjunct diagnostic the previous addendum called for (`_r2178dbg`, mounted at the same
identification-terminal point, writing to a text file), and **certified it inert first**: the probe's product is
byte-identical to the F5 base (`20190` bytes, sha16 `192ba0f09e81bbd7` both with and without the probe). Its verdict:

```
R@8948  cond=8948 merge=9194 els=[8976, 9144] falsejoin=8976 nlegs=2 Mpreds=[8306,8544,8588,8688,8852,8980,9144] blocks=[8948,8964,8974,8976,8980,9144]
R@8904  cond=8926 merge=9144 els=[]             falsejoin=9144 nlegs=3 Mpreds=[8904,8926,8964,8976]           blocks=[8904,8926,8948,8964,8974,8976,8980]
R@7164  cond=7164 merge=7216 els=[]             falsejoin=7216 nlegs=1 blocks=[7164,7186,7202,7212,7214,7248,…]
R@6322  cond=6322 merge=6374 els=[]             falsejoin=6374 nlegs=1
R@6496  cond=6496 merge=6548 els=[]             falsejoin=6548 nlegs=1
```

Three corrections to what I had written in §§1-2 of this ticket:

1. **Why v2/v3 were inert is now known and it is not the merge test.** `@8976` (the false-leg target) has
   successors `[9144, 9218]` — the second is the enclosing `TryExceptRegion@6`'s exception continuation — so
   "the stub's **unique** successor" can never hold inside a `try`. My v4 replaced it with a fall-through test and
   mis-took "next block by offset" (`@8980`), and v5 took the smallest forward successor (`9144`, correct) — and
   **v4 and v5 both still produce a byte-identical product**, so the re-election is not the lever at all.
2. **The fold information already exists one level up.** `IfRegion@8904` already declares `merge_block=9144` with
   `else_blocks=[]` and **three** conditional legs reaching `9144`, and its block set already contains
   `@8948/@8964/@8976/@8980`. So the parent is correctly declared, and the child `@8948` is a *re-declaration of a
   sub-chain inside it*. Step 6 is therefore about the **parent/child duplication of the same guard run** (the child
   re-owns `@8964`, whose chained comparison the oracle wants ANDed into the parent's test), not about the child's
   merge election. That also matches the numbers: `@8948`'s `nlegs=2` versus `@8904`'s `nlegs=3`.
3. **Steps 3 and 4 are untouched by this rule**: `@7164`, `@6322`, `@6496` each report `else_blocks=[]`,
   `merge ==` their own false target and `nlegs=1`. Nothing to re-elect there — their obstacle is the *missing
   short-circuit tests* (3 declared `BOOL_OP` regions where ≥5 are needed) and the swallowed `system_log.debug`,
   exactly as R21-77 addendum 4 said. My time would not have been better spent here; the axis needs a different
   lever (chain-leg **population** at identification, per r93a's duplicated-test work), and this ticket should stop
   pursuing merge re-election after five arms (`v1` destructive, `v2-v5` byte-inert).

Net for the next hand: attack step 6 as "one guard run declared twice, parent and child", using the parent
`IfRegion@8904`'s already-correct merge and 3 legs, and drop the merge-reelection idea. F5 base unchanged
(`996a1b1acf143458`); my mirror is restored to it; the probe file lives at `D:/Temp/r91m/out/r2178dbg.txt`.


## Addendum 4 (orchestrator, 16:27) — the parent/child duplication is real, but dropping the child is destructive

Acting on addendum 3, I implemented the de-duplication (`_r2179_drop_duplicated_guard_chain_child_regions`: drop an
`IfRegion` whose entry **and** condition block both lie in a parent `IfRegion`'s block set, where the parent has
`else_blocks == []` and a different merge, re-assigning `block_to_region` and the parent's `children`). Unlike every
earlier arm it **fires**:

| arm | product bytes | `clock_worker` lines / hunks vs oracle 254 | instrs Δ | jsites Δ | judge |
|---|---|---|---|---|---|
| F5 base | 20190 | 241 / 4 | −114 | −9 | `12/13` |
| v6 (drop the child chain region) | **21373** | **264 / 5** | **−203** | −19 | `12/13` |

So the child is *not* redundant in the generator's eyes: deleting it adds lines while **losing** 89 more instructions
than before and adding an extra hunk — it removes arms, not a duplicate. Conclusion: the parent's `nlegs=3` chain and
the child's `nlegs=2` sub-chain are **both needed** (the parent folds the guard `and`-test, the child supplies the
`elif`/nested structure), and step 6's lever is neither the child's merge nor the child's existence. Remaining
candidates for the next hand, in the order the data suggests: (a) the child's **test assembly** — get the generator to
AND the chained comparison into the parent's condition by way of the parent's `inline_boolop_chains` (the parent
already has the right merge and three legs, so the operand list is the only missing datum); (b) leg **population** at
identification, which is also what steps 3 and 4 need (`@7164/@6322/@6496` each show `nlegs=1` where the oracle needs
more short-circuit tests). Six arms are now excluded on this axis: v1 destructive (`11/13`), v2–v5 byte-inert merge
re-elections, v6 destructive de-duplication. F5 base unchanged and the mirror is restored to `996a1b1acf143458`.


## Addendum 5 (orchestrator, 16:29) — one measurement explains ALL FOUR open facts: the short-circuit chain mount stops at pure-jump stubs

Second inert-certified probe (product sha16 `192ba0f09e81bbd7` with and without it, i.e. byte-identical), now
counting legs **after folding a pure-jump false-leg stub into its fall-through target**, plus what is actually
mounted in `inline_boolop_chains`:

```
IfR@8904 merge=9144 nblocks=7  n_cond_jumps=4  n_legs_to_merge=1   inline_boolop_chains={ blocks:[@8904-8924, @8926-8946], op:'and' }
IfR@8948 merge=9194 nblocks=6  n_cond_jumps=2  n_legs_to_merge=1   inline_boolop_chains={}
IfR@7164 merge=7216 nblocks=51 n_cond_jumps=21 n_legs_to_merge=2   inline_boolop_chains={}
IfR@6496 merge=6548 nblocks=8  n_cond_jumps=3  n_legs_to_merge=2   inline_boolop_chains={}
IfR@6322 merge=6374 nblocks=6  n_cond_jumps=3  n_legs_to_merge=2   inline_boolop_chains={}
```

This is the single datum that ties steps 3, 4 and 6 together, and it retires my v2–v6 framing:

* At `@8904` the guard run has **four** conditional jumps but `inline_boolop_chains` holds exactly **two** legs
  (`@8904`, `@8926`) — so the fold the oracle needs (`… and <@8948 test> and <@8964 chained comparison>`) never
  happens because **the chain walk stops at `@8948`**, whose own conditional jump targets the stub `@8976`
  (`@8976 → @9144 → and @9218` as the try continuation). The walk compares raw jump operands against the merge,
  so a leg that reaches the merge *through a pure-jump stub* is not recognised as part of the chain.
* The same signature — `n_cond_jumps` far above the mounted legs, `inline_boolop_chains` empty — is present at
  `@7164` (21 conditional jumps, 2 legs after folding), `@6322` and `@6496`: **the identical defect** at the three
  or-chain sites of steps 3 and 4.

**Rule to write (general, region-data only, one predicate):** *when extending a short-circuit chain, treat a leg's
conditional false target as the join `J` if the target block is a pure-jump stub whose single forward successor is
`J`* — i.e. compare joins after stub folding instead of after raw operands. The existing helpers to change are the
chain walkers (`_detect_while_boolop_forward_chain` / `_detect_while_condition_boolop_chain` /
`_inline_and_chain_exits_agree` and `_r2172_cond_jump_target` in the banked `9ba2d8af` lineage), which all ask
"does this leg jump to the merge/next block?" in the raw form.

Caveat for whoever implements it: this broadens a **landed** family of predicates, so the fire census must run over
all 402 files before any edit, and the panel must include `quote`, `risk_calculation/__init__` and the
`arg_checker`/`profiler_func` duplicated canaries — the files that caught every over-fire in this campaign so far.

Six arms on the ownership framing are excluded (v1 destructive `11/13`, v2–v5 inert merge re-elections, v6
destructive de-duplication). The axis is now chain-mount leg recognition, not ownership. F5 base
`996a1b1acf143458` unchanged; mirror restored; nothing installed.
