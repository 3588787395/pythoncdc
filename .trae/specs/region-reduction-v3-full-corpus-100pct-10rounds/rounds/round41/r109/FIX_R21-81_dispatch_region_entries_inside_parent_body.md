# FIX_R21-81 — dispatch nested-region entries that sit inside a parent region's body block list

## The rule (one paragraph)

The refusing renderer is the **if-arm scanner** `RegionASTGenerator._process_if_blocks`
(`core/cfg/region_ast_generator.py`): its pre-pass correctly registers every arm block that is
the entry of a nested structural region into `_nested_if_entry_generate` / `_try_entry_generate`
/ `_loop_entry_generate` / `_r2_b107_child_generate`, but the address-ordered scan then hits
`if block in self.generated_blocks: continue` **before** reaching those dispatch sites, so a
registered entry whose block was already *consumed* by some other walk is never *emitted* and
its whole statement run disappears (`@7972/@8294/@8350/@8354/@8400/@8450` for `clock_worker`).
After R21-81, dispatch is decided by a third ledger rather than by block consumption alone:
`_r2181_emitted_entries`, written only at the central dispatch funnel `_generate_region` when a
structural region returns a non-empty result, records the region **entry block** that actually
became source. The gate now skips a generated block unless it is a registered dispatch target
in this same arm *and* that target region has never been emitted by the funnel — i.e. the
predicate reads only stack/ledger shape, opcode-free region data and region membership
(`region.entry`, `region.blocks`, the arm's own registries), never a function name, file name,
absolute offset key, counter, threshold or magnitude comparison, and it is correct at
identification time (no retrospective text repair, no reordering, no re-emitting strings).
Principled because principle 2 (unique block membership) and principle 4 (parent references the
child *by entry*) are genuinely different facts that the base conflated: `generated_blocks`
proves a block was consumed, not that its region was rendered — which is exactly the ambiguity
the in-file `[r11-b159-fact]` note named as the prerequisite ("先建立可判别的『已发射区域入口』
集合"). Re-dispatch is bounded because every dispatch site already adds `id(region)` to
`_generated_regions`, which the pre-pass consults, so an entry can be re-offered at most once
per region.

## Excluded-premise reconciliation (R21-79 / R21-80)

I read the four-arm table before designing. F5 base and `[R21-80]` produce byte-identical
products (`20190 / 192ba0f09e81bbd7`, `instrs=-114`), and the `[R21-79]` tail-release *worsens*
the text (`instrs=-115`), while the PAIR is superseded by the R21-79 half. That table proves no
analyzer-side variant of the tail-release or chain-walk criteria can flip the unit: the 112
instructions in `@7972..@8586` are already **owned** (they sit in `LoopRegion@5598.blocks` and
`TryExceptRegion@6.blocks`, zero `UNOWNED` in `7582..8600`) yet never printed, so the loss is
purely emission/dispatch-side. My mechanism is therefore not a repeat of either ticket: it
touches no analyzer criterion, it is not a tail release and not a chain-walk fold; it adds a
missing *emission* fact (which region entries have been turned into source) and consumes it at
the one gate that refused the entries. Empirically it is also visibly different in kind — it is
the first arm that moves the needle in the right direction (`instrs -114 -> -77`,
`jsites -9 -> -3`, product `20190 -> 20628` bytes, unit lines `241 -> 248` of 254), whereas both
prior arms moved it negative or not at all.

## Verdict

**BANK, do not install.** The direction is right but the flip was not reached (judge stays
`12/13`, `hunks_vs_ORACLE=4`, `indeg-equal=False`) and the half regresses currently-`Equal`
units (`fly/data/quote.pyc 92/92 -> 89/92`, `plugin_system_realquote/real_quote.pyc 45/45 ->
42/45`), so it fails the install bar on two independent counts. See `MEASURE_R21-81.md`.

## Residual gap to close in a follow-up

The re-dispatch recovers ~37 of the 112 dropped instructions; the remaining loss is the tail of
the `@8294` guard chain. The regressions share one shape: an entry re-offered from an **ancestor**
arm after a **descendant** arm already consumed its blocks but where the descendant's emission
did not go through `_generate_region` (some paths call `_generate_if` / `_generate_try`
directly, bypassing the funnel ledger). A complete R21-81 needs the ledger written at every
structural emission site (or the direct calls routed through the funnel), not only at
`_generate_region`'s five type-dispatch returns.
