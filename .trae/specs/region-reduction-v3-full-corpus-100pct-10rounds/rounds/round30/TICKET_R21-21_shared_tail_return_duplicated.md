# TICKET R21-21 (round 30, banked — not dispatched) — the product duplicates a `return None` that the original shares as one tail

Owner file: `core/cfg/region_ast_generator.py` or `core/cfg/region_analyzer.py` — pick one after the
取证, and say which. Repo READ-ONLY `D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main`
(HEAD `502ea500`+), sealed `region_ast_generator.py = fd0e4c4d73cf5efc`,
`region_analyzer.py = 35e227ac3e7b25af`. Suggested mirror `D:/Temp/r39/wt`, products `D:/Temp/r39/out/`.

## 0. Prize
`IQCommon/util/trade_info_utils.pyc` is **38/41** with three failing units. Two of them are THIS one
mechanism, so the ticket is worth **+2 units** (6600 → 6602). It is deliberately NOT filed as a file
flip: the third unit (`kill_trade_process`, `hunks=0 landings=2`, a strict two-target swap) is a
different mechanism, so the file cannot go green from this work. Do not oversell it.

## 1. Measured shapes (17:39, current products)
```
<module>.query_trade_strategy_info   len orig=122 prod=122 delta=0  hunks=3 landings=1
   == replace orig[94..95 @478] prod[94..96]   - @478 JUMP_FORWARD   + @478 LOAD_CONST None / + @480 RETURN_VALUE
   == replace orig[113..114 @604] prod[114..116] - @604 JUMP_FORWARD + @606 LOAD_CONST None / + @608 RETURN_VALUE
   == delete orig[120..122 @618..@620]          - @618 LOAD_CONST None / - @620 RETURN_VALUE
<module>.query_strategy_id           len orig=117 prod=116 delta=-1 hunks=2 landings=0
   (same two shapes, one of them netting −1 because the shared tail pair is gone)
```
So in the ORIGINAL, two exits **jump forward to one shared** `LOAD_CONST None; RETURN_VALUE` tail; in
the PRODUCT each exit gets its **own inline** pair and the shared tail disappears. Instruction multiset
is otherwise identical (`delta=0`), so this is purely about whether the compiled function has one
tail-return that several edges reach, or N inline returns.

## 2. Already falsified for this family — do not re-test (all by `compile()` on 3.11.7, not by argument)
Reconstructing the source of `query_trade_strategy_info` from the emitted product and compiling it
gives `len=122` with only 93/122 rows matching the pyc, and these variants are **byte-identical to
that** — i.e. they cannot be the lever:
- `else: return None` appended to the last `if`; `else: pass`; no `else` at all (CPython threads a
  `return None` else-arm onto the implicit function tail and deletes the redundant block);
- inverting the `try`/`if` nesting (try-outer/if-inner): 86–87/122, i.e. WORSE than the product's own shape;
- a trailing function-level `return None`: gives `len=120`, wrong length.
The best shape found so far is `else: return None` **plus** a trailing `return None` at 97/122 — still
not exact, and its `if`-false exit still lands on the later copy rather than `@614`.
Conclusion: the required difference is in **which block is the function's terminal block**, i.e. the
block/region ownership around the `try/except` and its handler tail, not in any `return None` you can
add. Start from the two exits' owning regions: in the original the loop exit (`@478`) and the
try/except exit (`@604`) are edges of a shared block; find why the generator instead closes each scope
with its own return.

## 3. Method that works here
Ablation or the line-event tracer — never sampled line probes. `D:/Temp/t30/tracbreak.py` takes
(abs pyc, out path, log path, comma-separated line numbers), swallows `SystemExit`, prints a
positive-control count of module line events, and must be `cmp`-proved inert per target; the generator
holds 71 `'type': 'Break'` literals so a hand-picked 6-site probe reads zero fires and that is a broken
rig, not a negative. Decide every shape question by compiling candidate sources and comparing
instructions AND `dis`-resolved targets.

## 4. Acceptance
`unit_diff.py IQCommon/util/trade_info_utils.pyc "<module>.query_trade_strategy_info" --all` and
`…"<module>.query_strategy_id" --all` must each read `delta=0 hunks=0 landings=0 judge_diff=False`, and
`pyc_verify single --source` must print `Equal` for both (file 38/41 → **40/41**). One of the two is an
acceptable partial result — say which. Shrinks without `Equal` are measured negatives.

## 5. Anti-regression duties (identical to the round-29/30 tickets)
Fire census over the 14-file panel with `TOTAL_FIRES`, product comparison against
`git show HEAD:<path>` bytes with CR stripped (never `cmp` against checked-out files);
`quotation` 153/153; `order_api` 37/37; `matcher` 17/17; no count may drop on `klinedata` 63/64,
`handlers` 29/30, `wizard_quant_api` 58/58, `real_quote` 45/45, `api_base` 27/28, `strategy` 26/27,
`quote` 91/92, `broker` 121/128, `realtime_event_source` 12/13, `risk_calculation` 42/43; all six
batteries at their recorded values; judge by diff SHAPE.

## 6. Constraints
`python -X utf8`, never PYTHONIOENCODING; ≤300 s per command; CRLF-preserving textual patches only (a
byte-mode newline rewrite doubled `\r\n` → `\r\r\n` and broke `region_analyzer.py` at line 3281);
scratch by absolute Windows paths; `--source` mandatory for judge reads; no git writes; repo read-only.

## 7. Deliverable
`D:/Temp/r39/DELIVER/FIX_R21-21.md` (0-7 as usual) plus a whole-file `CANDIDATE_*.py` with its
`sha256sum | cut -c1-16` only if §4 is met with no panel regression.
