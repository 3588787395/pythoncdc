# MEASURE R21-79 — clock_worker's 112-instruction drop is an over-absorption, not a membership gap

Read-only localisation performed by the orchestrator at 2026-10-14 00:43–00:45 while r106a (chain
walkers, `D:/Temp/r106`) and r107a (this axis, `D:/Temp/r107`) are live. Nothing was installed; the
repo's `core/` stayed at landed bytes. Probe scripts: `D:/Temp/r91m/dump_tail.py <lo> <hi>` and
`D:/Temp/r91m/dump_fe.py`, run against my mirror `D:/Temp/r91m` whose platform is
`region_analyzer.py = 996a1b1acf143458` (**[R21-77-F5]**) + `region_ast_generator.py = 566ff5c502276e48`
(landed, untouched). The probe process never generates a product, so it cannot perturb one.

## 1. Every block in the dropped span is owned

Census over `@7582..@8600` (block, instruction count, tail opcode, owner, successors, predecessors):
**zero `UNOWNED` blocks.** The span `@7972..@8586` holds **112 instructions** (`instrs_in_span=112`),
which is exactly the drop `DELTAS instrs=-114` attributes to step 1's second half. So the loss is
claim/absorption-side, never a missing region — the round-40 warning about riding a fake membership
gap applies again.

Shape of the run (excerpt):

```
@7582 n=5  POP_JUMP_FORWARD_IF_FALSE  succ=[7604,7634,9218]  preds=[7216, 7492]
@7634 n=7  POP_JUMP_FORWARD_IF_FALSE  succ=[7668,8592,9218]  preds=[7582,7630,7632]
@7706 n=1  FOR_ITER                   succ=[7708,7972,9218]  preds=[7668,7960]
@7972 n=4  POP_JUMP_FORWARD_IF_FALSE  succ=[7980,8170,9218]  preds=[7706,7814]
@7980 n=25 POP_TOP                    succ=[8166,9218]       preds=[7972]
@8166 n=2  RETURN_VALUE               succ=[]                preds=[7980]
@8294 n=4  POP_JUMP_FORWARD_IF_FALSE  succ=[8306,8350,9218]  preds=[8256,8282]
@8306 n=7  JUMP_FORWARD               succ=[9194,9218]       preds=[8294]
@8544 n=2  JUMP_FORWARD               succ=[9194,9218]       preds=[8450,8504]
@8588 n=2  JUMP_FORWARD               succ=[9194,9218]       preds=[8350,8354,8548]
```

## 2. The absorbing region, measured

```
Chain IfRegion@7186  cond=7186  merge=7216  nblk=48
  elif_conditions = [7248]        elif_bodies = [[2 blocks]]
  elif_final_else = 42 blocks:
    7492 7582 7604 7620 7630 7632 7634 7668 7706 7708 7710 7712 7814 7972 7980 8166 8170 8184 8186 8256
    8294 8306 8350 8354 8400 8450 8504 8544 8548 8588 8592 8666 8688 8852 8904 8926 8948 8964 8974 8976 8980 9144
  of which 15 are the ENTRY of another declared region:
    7582(IfRegion) 7604(IfRegion) 7634(IfRegion) 7706(LoopRegion) 7712(TryExceptRegion) 7972(IfRegion)
    8186(TryExceptRegion) 8294(IfRegion) 8350(IfRegion) 8354(IfRegion) 8400(IfRegion) 8450(IfRegion)
    8666(IfRegion) 8904(BoolOpRegion+IfRegion) 8948(IfRegion)
Second chain, same disease one level down:
  Chain IfRegion@7634  merge=7634... elif_conditions=[8592]  elif_final_else = 8 blocks
    = [8904 8926 8948 8964 8974 8976 8980 9144]   (2 of them region entries)
```

The edge data that separates genuine else-arm content from the sequential tail:

- `@7492` (`n=13`, `tail=STORE_ATTR`) has predecessors `[7248, 7270]`, both **inside** the chain — it is
  real else-arm code.
- `@7582` has predecessors `[7216, 7492]`, and `7216` **is the chain's own declared merge**. Everything
  from `@7582` onward is entered from the merge or by fall-through from a block that is: `@7634` preds
  `[7582,7630,7632]`, `@7706` preds `[7668,7960(back edge)]`, `@7972` preds `[7706,7814]`, `@8294` preds
  `[8256,8282]`, `@9144` has no predecessor outside the absorbed set at all.
- The tail arms land on `@9194` (the loop back edge) and the run's only terminal sink is `@8166`
  (`RETURN_VALUE`, no successors).

So the positive claim available from region data alone is: **a block whose entry edges come from the
chain's merge (or only transitively from such a block) is code after the whole `if/elif` statement and
may not be mounted as the chain's final-else body.**

## 3. Excluded premise (delivered to r107a as forbidden)

"Drop from `elif_final_else` any block that is another region's entry" is **not** the rule: a legitimate
`else: if a: …` keeps its nested `IfRegion` entry in the else body, so that predicate would gut correct
chains corpus-wide. Entry-status is a symptom (15/42 here), edge boundedness is the cause.

## 4. Consequences for the round

- Step 1's remaining half now has a named, edge-decidable mechanism, which is what addendum 4 of
  `TICKET_R21-77` said was missing ("needs a positive tail claim instead of a narrower refusal").
- `@9144` (the loop-tail statement) is swallowed by **two** different chains' final-else sets
  (`@7186` and `@7634`), so a single-site refusal cannot release it; the claim must apply at every
  chain assembly, which is why it is dispatched as a rule and not as a patch to one branch.
- Acceptance for this axis is unchanged: `hunks_vs_ORACLE < 4` with `instrs` moving toward 0, panel
  rows unmoved (broker must stay `128/128`), sweep `CHANGED={realtime_event_source.pyc}` with
  `files_compared=402 MISSING/FAIL=0`, and only a judge `13/13` flips the unit. Zero flip ⇒ banked.
- r106a's axis (`inline_boolop_chains` mount for steps 3/4/6) is disjoint in code (short-circuit chain
  walkers vs the nested-elif expander at `:21543`/`:22173`/`:22768-22790`) but **same file**, so the two
  deliverables must be merged by re-applying both anchored patch scripts onto `996a1b1acf143458` and
  the merged pair, not either half alone, is what gets gated.

Evidence logs: `$TEMP/mon/tail_004318.log` (block census 7582..8600),
`$TEMP/mon/fe_004408.log` (full final-else sets with entry flags).
