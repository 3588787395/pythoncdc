# MEASURE R21-81 - the analyzer tail-release and the generator dispatch ledger are ADDITIVE (first sub-4-hunk arm in 41 rounds)

All arms measured by the orchestrator in `D:/Temp/r91m` on the pinned platform, analyzer/generator restored and re-hashed after each arm.

| arm | analyzer | generator | product | instrs | jsites | back | hunks_vs_ORACLE | judge |
|---|---|---|---|---|---|---|---|---|
| F5 base | `996a1b1acf143458` | `566ff5c502276e48` | 20190 `192ba0f09e81bbd7` | -114 | -9 | +0 | 4 | 12/13 |
| [R21-79] tail release (analyzer) | `3ad5ceaa23135334` | landed | 20078 `25730af90ed6d1db` | -115 | -9 | +0 | 4 | 12/13 |
| [R21-80] stub-folded join (analyzer) | `7e8350f7d52fe9a3` | landed | 20190 `192ba0f09e81bbd7` | -114 | -9 | +0 | 4 | 12/13 (inert) |
| [R21-79]+[R21-80] pair | `890a1593abfcfb6b` | landed | 20078 `25730af90ed6d1db` | -115 | -9 | +0 | 4 | 12/13 (superseded) |
| **[R21-81] dispatch ledger (generator)** | `996a1b1acf143458` | `8da14b53a94e07c3` | 20628 `7f3d1796815eb4f5` | **-77** | -3 | **+0** | 4 | 12/13 |
| **[R21-79] + [R21-81] PAIR** | `3ad5ceaa23135334` | `8da14b53a94e07c3` | 20484 | **-78** | -3 | **+0** | **3** | 12/13 |


Reading of the last two rows:

- `[R21-81]` is the **first arm in the campaign to move the named fact positively**: 37 of the 112 dropped instructions come back, the unit body grows 241 -> 248 lines against the oracle 254, `jsites` closes from -9 to -3 and `back` stays `+0`. Its own diagnosis (probes in `D:/Temp/r108/rig/`): the child entries `7972/8294/8350/8354/8400/8450` report `nig=True` (registered in `_nested_if_entry_generate`) *and* `gen=True` at the arm scan in `_process_if_blocks`, so the registered dispatch at `region_ast_generator.py:26864` is unreachable behind the `generated_blocks` gate at `:26775`. Block consumption and region emission were being conflated - ownership was never the gap (zero `UNOWNED` in `7582..8600`, all in `LoopRegion@5598.body_blocks`).
- The mechanism is a third ledger, `_r2181_emitted_entries`, written only at the funnel `_generate_region`. That is also its defect: **4/8/2/8 direct `_generate_if/_try/_loop/_match` calls bypass the funnel**, so ancestor arms re-offer entries whose emission was never recorded, and the smoke arm regresses `quote 92/92 -> 89/92` and `real_quote 45/45 -> 42/45`. Not installable as-is.
- **The pair goes below 4 oracle hunks for the first time (3)** while `instrs` sits at -78, i.e. the analyzer tail-release and the generator dispatch ledger are additive rather than redundant - unlike every two-analyzer-half merge measured so far (`[R21-79]+[R21-80]` was byte-identical to one half, the fifth such supersession).

Consequence: the flip path is now a *completed* generator ledger (write the ledger at every emission site) plus the proven-collateral-free `[R21-79]` analyzer half. Distance after the pair: 6 text lines, 78 instructions, 3 hunks, and `indeg-equal=False` (the judge still sees a different CFG, so a zero-hunk text diff would not even be sufficient yet).

Ticket **R21-82** is dispatched to r109a on exactly that: build on r108a's delivered bytes, extend `_r2181_emitted_entries` to all structural emission sites, prove `quote 92/92` and `real_quote 45/45` are restored, then panel 20 + ROOT-joined 402 sweep + judge. Nothing installed here; corpus unchanged at **6616/6617 (99.9849 %), 401/402 files**, gate label **41 unconsumed**, repo `core/` clean at landed bytes (`1471c92eca157e46` + `566ff5c502276e48`).

Artifacts: `r108/CANDIDATE_r2181_8da14b53a94e07c3.py`, `r108/PATCH_R21-81_region_ast_generator.py`, `r108/FIX_R21-81_*.md`, `r108/MEASURE_R21-81.md`, and the analyzer halves `CANDIDATE_r2179_3ad5ceaa23135334.py` / `CANDIDATE_r2179pair_890a1593abfcfb6b.py` in this directory.

## Addendum - the naive completion of R21-81 is falsified: the ledger must be written POST-EMISSION, not at method entry (2026-10-14 01:19)

r109a showed no writes for 40 minutes and no python process, so I ran the obvious completion myself in D:/Temp/r91m and measured it.

Mechanism tried: keep r108a gate and funnel write, and additionally call the recorder at the start of each of the four structural generators, using ast to locate each method body end-of-docstring line (_generate_loop 5501, _generate_if 15087, _generate_try 31539, _generate_match 37900). Candidate bytes 52255f5938bcc387, 3,874,443 B, BOM intact, zero bare LF, zero CR CR LF, compile clean, analyzer arm = R21-79 3ad5ceaa as intended co-requisite, platform restored and re-hashed after the arm.

| arm | realtime product | instrs | back | jsites | hunks | judge | broker / quote / real_quote vs committed |
|---|---|---|---|---|---|---|---|
| R21-81 alone (funnel only) | 20628 | -77 | +0 | -3 | 4 | 12/13 | unchanged per r108a smoke except quote 89/92, real_quote 42/45 |
| R21-79 + R21-81 | 20484 | -78 | +0 | -3 | 3 | 12/13 | unmeasured |
| **entry-claim variant (mine)** | **15106** | **-485** | **-4** | **-59** | 2 | **10/13** | **all three CHANGED** |

Verdict: pre-claiming emission is destructive, not merely imprecise - it suppresses 408 more instructions than the funnel-only arm, breaks the loop back edge count (back -4) and drops the judge from 12/13 to 10/13, i.e. it manufactures two new failing units in the victim file itself and moves three currently-green corpus files. The hunks number falls to 2 only because the product collapsed to 198 lines.

The reason is structural and it is the constraint the next attempt must respect: a structural generator can be entered and then bail (or return a Pass skeleton), so recording at entry asserts an emission that never happened, and the gate at region_ast_generator.py:26775 then refuses to render the block anywhere. Therefore the ledger may only be written where the non-emptiness of the produced source is known - the funnel knows it, the direct call sites must be fixed by recording at each CALLER after the result is inspected (the four/five/six/eight bypass call sites r108a counted), not by touching the four methods.

Falsified shapes on this axis, all measured: entry-claim at the four methods (this addendum, -485/10-13); funnel-only (quote 89/92, real_quote 42/45, r108a); and before that the analyzer-only tail release and folded join. The remaining expressible shape is caller-side recording, which is exactly ticket R21-82 and task 157.