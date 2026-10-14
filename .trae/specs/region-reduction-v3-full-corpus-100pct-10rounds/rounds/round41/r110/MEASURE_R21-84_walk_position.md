# MEASURE_R21-84 — walk position census for `clock_worker` @7972..@8588

Mirror `D:/Temp/r110` (layout copied from `D:/Temp/r108`; `r91m/r106/r107/r108/r109` untouched).
**Diagnosis only: no candidate written, no repo `core/` or `site-packages/` file touched, no git
write command run.** All instrumentation is runtime monkeypatch + `sys.settrace` line tracing.

## Platform pin (proved before and after every run)

| file | required sha16 | re-hashed after all probes |
|---|---|---|
| `D:/Temp/r110/core/cfg/region_analyzer.py` | `996a1b1acf143458` | `996a1b1acf143458` (2129303 B) |
| `D:/Temp/r110/core/cfg/region_ast_generator.py` | `566ff5c502276e48` | `566ff5c502276e48` (3869919 B) |

Repo check: `git status --porcelain -- core/` → **0 lines**.

## Probe inertness (the campaign's required proof, run for each of the 4 probe modes)

Un-probed baseline reproduced: `20190 B / 192ba0f09e81bbd7`, `[oracle-diff] hunks_vs_ORACLE=4`,
`[census] DELTAS instrs=-114 back=+0 jsites=-9`, `[judge] 12/13 Different control flow` — exactly
the briefed F5 base row.

| probe mode | product with probe installed | verdict |
|---|---|---|
| `--trace` (call census + line trace) | CR-strip identical to base | inert |
| `--trace --flip` (+ membership sampling) | identical | inert |
| `--trace --claims` (5 claim sites) | identical | inert |
| `--trace --flip --unclaim 7604` (mutation arm, see §5) | identical to base (19843 B CR-stripped, **0 diff hunks**) | arm is a no-op on bytes, probe inert |

Runs cost 1.2–7.2 s each (all << 300 s). `sys.settrace` is restricted to
`co_filename == core/cfg/region_ast_generator.py` **and** `co_name ∈ {5 walks}` **and** the call's
block/region list contains one of the 15 offsets, so 19 frames / 91 813 line events were recorded
and nothing else was traced. An empty log was in fact hit once (a real bug: `os.path.abspath`
converted `D:/Temp/...` to backslashes and the filename test never matched) — fixed, then 19 frames.

## The emission descent, as measured (call `seq` = chronological nesting order)

```
seq12  _generate_try_body      TryExceptRegion@6   walk 29936 for block in sorted(_try_blocks_eff)   161 blocks
 └ block @5598 → 30068 discard(_r08_loop_child.blocks) [NO-OP, see §4] → 30069 _generate_region(child)
seq233 _loop_generate_body     LoopRegion@5598     walk  8763 for block in region.body_blocks          100 blocks
 └ block @7164 → 8941 _loop_dispatch_block → seq300 _generate_region(IfRegion@7164)
seq302 _if_generate_normal     IfRegion@7164       22657 → seq303 _if_generate_then_branch 19038
seq304 _process_if_blocks      IfRegion@7164  then   arg = then_blocks   n=50  (holds 14 of 15)
 └ block @7186 → 26869 _generate_region → IfRegion@7186
seq306 _if_generate_elif_chain IfRegion@7186       21042 _process_if_blocks(region.elif_final_else,'else')
seq313 _process_if_blocks      IfRegion@7186  else   arg = 42 blocks    (holds 14 of 15)
 └ block @7582 → 26869 → IfRegion@7582  → seq319 _process_if_blocks then arg = 27 blocks (holds 14)
 └ block @7604 → 26869 → IfRegion@7604 → seq322 _if_generate_normal
        22485 `if _or_elif_ir is not None:` → 22493-22496 GRAFT @7634's elif arms onto @7604
        22497 else_stmts = _if_generate_elif_chain(region) → 21042 → seq353 else arg = 8 blocks (holds 0)
        22502-22505 CLAIM `for b in region.else_blocks` (23 members, ALL 14 targets)  ← first mark
   back in seq319: 26908-26912 CLAIM `for _nb in _nr.blocks` (26 members, ALL 14)  ← second mark
   ... unwind: seq319 → seq313 → seq304 → seq233 → seq12 each reach @7972.. and decline
```

## §1 Census table — offset × walk × present/consumed × deciding line

Per-block line sets are taken from the live `f_locals['block']` at each line event (an earlier
grouping keyed on the `for`-header line was off by one and is superseded — `rig/block_walk2.py`).

| offset | seq12 `_generate_try_body` @29936 | seq233 `_loop_generate_body` @8763 | seq304 then[50] | seq313 else[42] | seq319 then[27] | seq323/344/353 @7604 | seq374 standalone[4] |
|---|---|---|---|---|---|---|---|
| 7972 | present, **skip guard 29937→29938** (2 lines) | present, **skip 8764→8765** | present, **skip 26775→26776** | present, **skip 26775** | present, **skip 26775** | absent | absent |
| 7980 | present, skip 29937 | present, skip 8764 | skip 26775 | skip 26775 | skip 26775 | absent | absent |
| 8166 | present, skip 29937 | present, skip 8764 | skip 26775 | skip 26775 | skip 26775 | absent | absent |
| 8170 | present, skip 29937 | present, skip 8764 | skip 26775 | skip 26775 | skip 26775 | absent | absent |
| 8186 | **absent** (`_try_blocks_eff` excludes it) | present, skip 8764 | skip 26775 | skip 26775 | skip 26775 | absent | absent |
| 8256 | absent | present, skip 8764 | skip 26775 | skip 26775 | skip 26775 | absent | absent |
| 8282 | absent | present, **WALKED 64 lines**: 8941 dispatch → `handled=False` → **8947** defer → postprocess → 1 stmt | absent | absent | absent | absent | present, walked 64 lines to 28174 (successor absorption), 1 stmt |
| 8294 | present, skip 29937 | present, skip 8764 | skip 26775 | skip 26775 | skip 26775 | absent | absent |
| 8306 | present, skip 29937 | present, skip 8764 | skip 26775 | skip 26775 | skip 26775 | absent | absent |
| 8350 | present, skip 29937 | present, skip 8764 | skip 26775 | skip 26775 | skip 26775 | absent | absent |
| 8354 | present, skip 29937 | present, skip 8764 | skip 26775 | skip 26775 | skip 26775 | absent | absent |
| 8400 | present, skip 29937 | present, skip 8764 | skip 26775 | skip 26775 | skip 26775 | absent | absent |
| 8450 | present, skip 29937 | present, skip 8764 | skip 26775 | skip 26775 | skip 26775 | absent | absent |
| 8544 | present, skip 29937 | present, skip 8764 | skip 26775 | skip 26775 | skip 26775 | absent | absent |
| 8588 | present, skip 29937 | present, skip 8764 | skip 26775 | skip 26775 | **walked 30 lines, ends at 28287 (walk's final claim), 0 stmts** | absent | absent |

**Consumption count:** `_generate_block_statements` was called for **0 of the 15** offsets in any
walk (no target-bearing `_generate_block_statements` record exists in the census; `emitted=False`
in every traced frame). Only `@8282` yields a statement, via the loop-postprocess deferral path.
**Iteration never stops early:** seq12 iterated all 161, seq233 all 100, seq304 all 50, seq313 all
42, seq319 all 27, seq353 all 8. There is no `break`/early `return`; every decline is a per-block
`continue` at a membership guard.

"D in the list but skipped by a guard" vs "never in any list at that stage":
* skipped by guard: all 15 except `@8186/@8256/@8282` in seq12, and `@8282` in seq304/313/319.
* never in any list **at the owning stage**: the 14 run blocks are **never in any list that IfRegion@7604
  renders as statements**. Its `then_blocks` = 1 (`@7630`), and its *rendered* else list =
  `elif_final_else` = 8 (`@8904,@8926,@8948,@8964,@8974,@8976,@8980,@9144`, **zero targets**).
  Confirmed twice: runtime claim-site sample (`else_n=23, then_n=1, efe_n=8, efe_hits=[]`) and the
  static analyzer dump — where `IfRegion@7604.elif_final_else` is in fact **`n=0`** and `n=8`
  belongs to `IfRegion@7634`.

## §2 Answer to the one question (one paragraph)

**No later walk revisits them for emission, and none ever did.** The try-body emitter never
"freed" them at all (`§4`): at `30068` their membership was already `False`, so the discard is a
no-op; the first thing that ever marks any of the 15 is `region_ast_generator.py:22505` inside
`_if_generate_normal(IfRegion@7604)` — and the mark is made over `region.else_blocks` (23 members,
holding all 14) by a loop whose *only* purpose is bookkeeping, while the statements for that same
else arm were produced one line earlier at `22497 → _if_generate_elif_chain → 21042` from
`region.elif_final_else`, i.e. the **8-member elif arm grafted off the descendant `IfRegion@7634` at
`22493-22496`**, which contains none of them. So the run's blocks are marked consumed by a list
that is never walked, and walked only by lists (`then[50]`, `else[42]`, `then[27]`,
`body_blocks[100]`, `_try_blocks_eff[161]`) that all decline them at their
`generated_blocks` guard — `26775/26776`, `8764/8765`, `29937/29938` — because in every one of
those walks the dispatching block (`@7164`, `@7186`, `@7582`, `@7604`) has a **smaller offset than
`@7972`** and so the claim always completes before the reach (measured per walk (`rig/idx_check.py`): seq313 dispatches @7582 at
iteration index 1 and first reaches @7972 at index 13; seq304 dispatches @7186 at index 0 vs
first reach index 21; seq319 dispatches @7604 at index 0 vs first reach index 10). The walk that
owns the position the run should have been printed at is therefore
**`_if_generate_elif_chain(IfRegion@7604)` at `:21042` — i.e. IfRegion@7604's else arm — and the
deciding lines are `22485` (branch taken), `22493-22496` (the descendant's `elif_conditions /
elif_bodies / elif_final_else` overwrite @7604's own), `22497` (else arm rendered from the borrowed
chain), `22502-22505` (the 23-member `else_blocks` claim that hides the residue), plus the
independent second claim at `26908-26912`.**

## §3 The single first decliner, named

Earliest *reach* with nothing produced: **seq319 `_process_if_blocks(IfRegion@7582, branch='then',
27 blocks)`** — it is the innermost walk still iterating when the claim returns; `@7972` is its
first target, and its per-block line set is exactly `{26771, 26775, 26776}`. The guard that decides
it is `if block in self.generated_blocks: continue` at `26775-26776` (documented in the
`[r11-b159-fact]` comment at `26773`). But the walk that *should* have printed them, and had them
in a list it owns, is `seq353`'s caller at `:21042`, which was handed the wrong list.

## §4 Two refinements of briefed facts (measured, not re-derived)

1. **"first DISCARD at `_generate_try_body:30068`" is a set *operation*, not a transition.** The
   membership sampler recorded **0 `OUT` flips out of 157 flips** for the 15 offsets: at `30068`
   none of them was in `generated_blocks`, so the r08 free is a no-op for this run. The first
   *transition* is `IN` at `30069`'s subtree = `22505`.
2. **`_if_generate_normal:22505` is correctly sited** (the closure `_detect_or_short_circuit` at
   `22435` ends at `22466`; `22467-22541` is the method body itself — verified by nearest
   indent-4 `def`).

## §5 Why the r109 neutering was zero-gain — reproduced and explained

I ran a surgical in-process **un-claim**: after `_generate_region(IfRegion@7604)` returns, discard
exactly the 14 targets from `generated_blocks` (`--unclaim 7604`, one event logged, all 14
un-marked). Result: **product byte-identical to base, 0 diff hunks**, and the walks skip them at
the *same* guards (`29937 / 8764 / 26775`) as before. Cause, from the same flip timeline under that
arm: the innermost `IN` moves to **`_process_if_blocks:26911`** (`for _nb in _nr.blocks: …
self.generated_blocks.add(_nb)`, the post-dispatch claim of the child region's whole block set),
which re-marks all 14 before any ancestor walk reaches them. So the suppressor is the **pair**
(`22505 ∧ 26911`); removing either is byte-neutral because the other is sufficient, and removing
both still emits nothing because no walk ever renders `IfRegion@7604.else_blocks`.

## §6 What a fix would have to assert (not implemented)

A fix must make the **else arm of `IfRegion@7604` render its own `else_blocks` address-prefix that
`_if_generate_elif_chain` did not consume**, i.e. at `_if_generate_normal:22485-22505` (and its
twin at `22506-22534`): (a) the `else_blocks` claim at `22502-22505` may mark only blocks the
rendered arm actually reached (`set(elif_final_else)` minus `_r23_or_*` and minus
`chained_compare_blocks`) — never a superset of it; and (b) the residual `else_blocks` members with
offset **below** the first grafted `elif_final_else` member (`@7972…@8588`, 14 blocks / 112
instructions) must be emitted as sequential statements at that position — after the elif-chain
substitution at `22493-22496`, since @7604's analyzer `elif_final_else` is empty and the 8-member
list is borrowed from descendant @7634. Because `26908-26912` in `_process_if_blocks` re-claims
`_nr.blocks` unconditionally after any child dispatch, **both** claim sites must be narrowed in
the same arm (measured: one alone is byte-neutral), and neither narrowing alone is sufficient —
emission, not un-marking, is the missing act. The predicate must be structural (the rendered else
list is a *strict subset* of `else_blocks` whose members all have offsets above some unrendered
members), not a membership test, and must not read jump targets (AST has no jump operands).

Rules in / out among the five falsified shapes:
1. **Analyzer `elif_final_else` tail release — ruled out as sufficient, and my finding explains it.**
   It frees blocks into a set that is then re-marked by `22505 ∧ 26911`, and no renderer walks
   `@7604.else_blocks`; "both renderers decline" is exactly the guard behaviour measured in §1.
   Also predicts its `region.blocks 48→7` / `arm 42→1` reads are on the borrowed list, not @7604's own.
2. **Analyzer stub-folded join — not addressed** (different axis, orthogonal).
3. **Generator pre-claim ledger at the four `_generate_if/_try/_loop/_match` methods — ruled out as
   the site.** Neither `22505` (`_if_generate_normal`) nor `26911` (`_process_if_blocks`) is one of
   those four, so that arm could not touch the suppressor; its `-485 / 10-of-13` damage is expected.
4. **Generator caller-side post-claim ledger at the 16 non-funnel call sites — closest, still ruled
   out as measured.** `26908-26912` *is* a caller-side post-claim, but my §5 arm shows that
   un-marking alone changes nothing; a post-claim ledger needs the paired emission clause (a) above
   or it is inert (and its broker collateral shows the ledger form over-fires elsewhere).
5. **The r109 five-site neutering — ruled out as the suppressor, now with a mechanism** (§5): the
   sixth claim site `26911` was never neutered, and it is individually sufficient.

## §7 Artifacts (absolute, re-runnable)

| path | role |
|---|---|
| `D:/Temp/r110/rig/walk_census_r110.py` | the census probe; modes `--trace`, `--trace --flip`, `--trace --claims`, `--trace --flip --unclaim <entry>` |
| `D:/Temp/r110/rig/census_table.py` | per-call / per-offset list-and-index rendering (`logs/table1.txt`) |
| `D:/Temp/r110/rig/block_walk2.py` | correct per-block line attribution → the §1 table |
| `D:/Temp/r110/rig/flip_time.py` | chronological claim/free timeline with deciding lines |
| `D:/Temp/r110/rig/region_lists.py` | read-only analyzer member lists (§1 "never in a list") |
| `D:/Temp/r110/rig/dump.py` | encoding-safe source dumper |
| `D:/Temp/r110/logs/{census_base,lines_base,block_walk_base,flips,walk2_base,table1,walk_unclaim}.json|.txt` | raw evidence |
| `D:/Temp/r110/out/{base_r110,probe_product,probe_product_unclaim}.py` | byte-level inertness proof |

Reproduce: `cd D:/Temp/r110 && python -X utf8 rig/walk_census_r110.py --trace --flip`
(≈7 s) then `python -X utf8 rig/block_walk2.py logs/lines_r110.json logs/census_r110_traced.json`.

## §8 Untrusted-text note

I saw no instruction-looking text in tool output that changed my target. Two things were treated
as data only: harness chrome (a skills `<system-reminder>`, a `<tool_use_error>` note, a
"file was modified since last read" banner), and long Chinese advisory comment blocks **inside
committed source** — notably `[r11-b159-fact]` at `region_ast_generator.py:26773-26774`, which
lists four previously falsified re-dispatch forms. I read those as prior engineering evidence
about the very guard named in §3 and designed the census against them, not as instructions to
stop or switch.
