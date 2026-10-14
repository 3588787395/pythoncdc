# FIX_R21-86 — render-scoped claim with a recorded release (generator-only)

Candidate generator `59a405837c22a4cb` (3,873,983 B, BOM, 100 % CRLF, zero bare LF, zero CR CR LF,
`py_compile` clean), built from the landed `566ff5c502276e48` by `PATCH_R21-86_region_ast_generator.py`
(absolute paths, idempotent — re-run reproduces the same sha16).
**No analyzer half is required**: the `[R21-79]` bytes `3ad5ceaa23135334` were NOT used as a
co-requisite; they were measured as an optional pairing only and the rule does the same work on the
pinned F5 platform (`996a1b1acf143458`), where it is even slightly better (`instrs -6` vs `-7`).

## The rule, in one paragraph

A branch may mark consumed only the blocks it printed, and when it declines to print a block it must
say so where the owning sequence can hear it. In `_if_generate_normal`'s `[R23]` short-circuit-or
branch, when the else arm is produced by an elif chain **borrowed from a descendant region** (the
graft at `:22493-22496`, which fires only when this region had no `elif_conditions` of its own), the
trailing claim over `region.else_blocks` is render-scoped: a member is claimed if it lies inside the
block scope that `_if_generate_elif_chain` actually rendered (`elif_conditions` ∪ `elif_bodies` ∪
`elif_final_else`), and a member outside it is **released** — recorded once in the new resident
ledger `self._r2186_released_blocks` and left unclaimed — provided some region still on the
generation stack (`self._generating_regions`, i.e. an ancestor sequence that has not finished
walking its own arm lists) holds it as a `then_blocks`/`else_blocks` member, which is what guarantees
the block will be emitted exactly once rather than dropped. The dispatch-adjacent blanket claim in
`_process_if_blocks` (`:26908-26912`), which re-marked the whole child block set after the nested
region returned, honours that release: it skips exactly the blocks the child renderer released and,
crucially, **keeps claiming every other member of `_nr.blocks`** — which is why this does not
duplicate the child's emitted arm the way blanket un-marking does. For the victim the released set is
the 17 blocks `@7972 … @8588` (measured, `logs/claims_realtime_event_source.pyc.json`: site A fires
17 times, all at `IfRegion@7604`, all `new_transition=True`); the 6 `else_blocks` members that the
borrowed chain did print (`@7668 @7706 @7708 @7710 @7712 @7814`) never reach the claim at all because
the renderers inside the branch already marked them.

## The discriminator

Three conjuncts, all read from region/block data plus the in-flight stack — no function name, no file
name, no absolute offset, no counter, no magnitude comparison, no jump target:

1. **this branch borrowed the chain** — `_r2186_chain_borrowed`, set inside the `if not
   hasattr(region, 'elif_conditions') or not region.elif_conditions:` block, i.e. "the else arm I
   just rendered is not my own arm"; the `[R37-A]` ancestor exclusion at `:22480` already guarantees
   the lender is a descendant, not an ancestor;
2. **the block is outside the rendered arm's scope** — `b not in _r2186_rendered_else_scope(region)`
   (pure membership in `elif_conditions` / `elif_bodies` / `elif_final_else`);
3. **an in-flight owner will still reach it** — `_r2186_has_inflight_owner(self, region, b)`: some
   other region whose id is in `self._generating_regions` lists it in its own `then_blocks` or
   `else_blocks`. This is the safety clause, and it is proved to be *inert on the victim*
   (ablation `ac9628fa75faf64e`, predicate replaced by `True`, identical numbers), so it cannot be
   what carries the gain — it only refuses to release code that no remaining walk would print.
   Anything that fails all three falls back to the landed claim, so a shape that is not the graft
   shape is byte-for-byte the landed behaviour.

Measured selectivity: at site A no `else_blocks` member of the victim's own region passes the scope
test, so the release is exactly the 17-block run; at site B the ledger is empty in
`trade_live_broker` and `klinedata` (site A never fires there — 0 claim events), so the blanket claim
is untouched and both products are byte-identical to their committed bytes.

## Resident rulers reused (grep before minting)

* `self.generated_blocks` / `self.generated_offsets` — the claim set itself; I never discard from it
  (no un-mark-and-repair anywhere).
* `self._generating_regions` / `self._generated_regions` — the in-flight/finished region stacks; used
  as the "ancestor sequence still walking" test. The same two sets are what the resident
  `_r2114_defer_to_unemitted_sibling_loop` reads, and its docstring states this exact defect for loop
  children ("when the parent marks the whole child block set as generated, those blocks are consumed
  before the owner walks them and their statements vanish"). I reused its **criterion shape**
  (defer to an owner that has not been emitted yet, never defer a block that is part of the child's
  own content) for the if-child case, and reused the `[R64-B2]` `child_entries` exclusion already
  sitting in the same loop, which is the same principle applied to entry blocks.
* `region.elif_conditions` / `elif_bodies` / `elif_final_else` / `chained_compare_blocks` /
  `then_blocks` / `else_blocks` — arm membership lists; `region_lists.py` (r110a's rig) is what gave
  the member lists the scope test is defined on.
* `_if_generate_elif_chain` — the renderer whose input lists define the rendered scope; `_process_if_blocks`
  — the walk whose `generated_blocks` guard (`:26775`) is the thing the release unblocks.
New mints: the ledger attribute `self._r2186_released_blocks` (one line next to `generated_blocks`
at `:466`) and the two helpers above. No name-based, offset-based or counter-based ruler is used.

## Excluded-premise reconciliation (why this is not a repeat)

Against `rounds/round41/MEASURE_R21-81_pair_matrix.md` addenda 1-7:

1. **addendum (1) — entry-claim ledger at the four `_generate_if/_try/_loop/_match` methods**
   (`-485`, 10-of-13). Not this shape: I add no ledger at any method entry and touch none of those
   four methods; the only writes are inside an existing claim loop that already runs post-render.
2. **addendum 2 — caller-side post-claim ledger at the 16 non-funnel call sites** (no victim
   movement, three files changed). Not this shape: my record is not a set of *emitted entries*
   reconstructed by callers; it is the renderer's own negative statement (blocks it did not print),
   written at the site that has the rendered scope in hand, and read at exactly one existing claim.
3. **addendum 3 — "the entries are handed to the walk already"** — my mechanism is consistent with
   it and uses it: the blocks stay in the ancestor's list and the walk reaches them; only the
   `generated_blocks` guard at `:26775` refused them, and that refusal is what the release removes.
   No re-dispatch, no new dispatch route.
4. **addendum 4 — the or-chain post-render over-claim is the suppressor** — this rule is the
   render-scoped form of exactly that claim, not a new site.
5. **addendum 5 — neutering the five in-method claims bought nothing** (`64d05383`): my ablation
   `8aa2595869e67954` (scope narrowed, nothing released) and `6c212c813c0c51fc` (released, but the
   `:26911` skip removed) both reproduce the base (`241 / -115 / -9 / 4`), i.e. the narrowing alone is
   inert exactly as addendum 5 found; the gain needs the *paired* honour, which addendum 5's arm
   never had. Conversely the honour without the narrowing is the `924604fc` row (no victim gain,
   broker+klinedata collateral). So the operative actuator is the conjunction expressed as one rule,
   which is a different object from either neutering.
6. **addendum 6 — stacking neutering on the `[R21-81]` dispatch ledger** (no gain, wider collateral):
   I do not stack on, or depend on, the `[R21-81]` ledger at all; the candidate is built from landed
   bytes and its collateral is *narrower than landed-baseline noise* (9/9 smoke files byte-identical,
   402-file sweep `CHANGED = {realtime_event_source}`).
7. **addendum 7 — r110a's positional census, and my own `:26911`-only follow-up falsified**: I use the
   positional fact only as the *relation* "an in-flight ancestor still lists this block as arm
   member", never as an offset comparison; the `:26911` follow-up failed because it un-marked
   everything — this rule un-marks nothing and simply does not claim what the child disclaimed.

Against **addendum 9** (the lead's own render-scoping arms, the closest prior shapes):

* arm **A `dd3c0afa`** — claims at `:22500/:22504` restricted to the rendered set: safe and inert,
  because `:26911` re-marks. My rule is A **plus the release record plus the `:26911` skip**, which is
  the missing half, and I prove the pairing by ablation (`6c212c81` = A with the skip removed → inert,
  exactly reproducing A).
* arm **B `4d75cf87`** — A plus blanket un-marking of `:26911`: buys the 108 instructions and pays
  duplication plus two collateral files. My rule differs at the second site by one thing: B claims
  *nothing* after the child dispatch, mine claims *everything except the released blocks*. The 9
  non-released `_nr.blocks` members stay consumed, which is precisely what prevents the second print;
  and because the skip is keyed on a record that only the graft shape writes, the collateral files
  (where site A never fires) are byte-identical.
* arm **C `97ad4d9d`** — A plus a membership-computed render scope at `:26911`: inert, and the lead's
  reading of why is right (the run *is* a member of the dispatched region's own arm lists, so
  membership cannot exclude it). **My rule is not C**: the parent-side exclusion is not computed from
  the child's arm membership at all, it reads the child's own release record, so arm membership of the
  run does not re-suppress it. That is the whole difference between an inert render-scope and an
  operative one.

## What this rule does *not* claim

It does not reach judge `13/13` and I did not try to repair that here: the run is emitted **once**
(`jsites` stays `+2`, `back +0`, no content line of the run occurs twice — verified by marker counts:
`broker_persist = None`, `persist_flag = False`, `jsonpickle.decode`, `获取持久化对象异常`,
`set_trade_stop_status`, `server_restart_not_do_before`, `put_before_trading_start`,
`on_before_trading_start_time`, `EventEnum.HANDLE_DATA`, `AFTER_TRADING_END`, `check_trading_time` are
`gold=prod` in every case), but it is emitted where the *ancestor* sequence reaches it, i.e. after the
whole `if` statement and one indent level deeper than the oracle, because our rendering of the
enclosing `[R23]` or-chain (ladder steps 3 and 4) is still a nested if/elif cascade where the oracle
text is a flat `if (A and B) or C:`. That is why `ours=262` sits above the oracle's 254 while the
instruction gap closes from `-114` to `-6`: the base product is already `254 - 21 (missing run) + 8
(step-3/4 scaffolding) = 241`, so the +8 is pre-existing in the base and is not produced by this rule.
Addendum 9's half (a) — "the arm renderer must continue past a dispatched child region to the rest of
the same arm" — is the remaining axis, and it is a renderer-position change, not a claim change; my
rule is the safe, zero-collateral form of half (b) that addendum 9 asked for.
