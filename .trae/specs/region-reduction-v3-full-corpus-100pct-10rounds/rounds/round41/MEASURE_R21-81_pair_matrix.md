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
## Addendum 2 - the ledger-completion hypothesis is falsified twice, so the drop is not missing records at the bypass sites (2026-10-14 01:20)

I ran the second expressible shape myself after r109a showed no writes for 50 minutes: record POST-EMISSION at each caller, only where the produced source is known non-empty. Method: parse the candidate with ast, take every Assign whose value is a direct call to `_generate_if`/`_generate_try`/`_generate_loop`/`_generate_with`/`_generate_match` outside the funnel (16 sites), and insert `if <target>: self._r2181_note_emitted(getattr(<region arg>, "entry", None))` after the statement, indented from the statement START line (my first attempt indented from the statement end line and died with an unexpected indent at line 4451, which is a rig bug, not a result).

Variant `2a8b1158cf21a201`, 3,875,760 B, BOM intact, zero bare LF, zero CR CR LF, compile clean, analyzer arm 3ad5ceaa as the co-requisite, platform restored and re-hashed in the same command:

| reading | R21-79 + R21-81 pair | pair + caller-side records |
|---|---|---|
| realtime product | 20484 | 19494 |
| instrs / jsites / back | -78 / -3 / +0 | **-78 / -3 / +0** (unchanged) |
| hunks_vs_ORACLE | 3 | 3 |
| judge | 12/13 | 12/13 |
| broker / quote / real_quote vs committed | unmeasured | **all three CHANGED** |

Two conclusions, both negative and both load-bearing:

1. Recording at the 16 bypass call sites buys the victim **nothing**: instruction gap, jump-site gap and back-edge count are identical to the pair, and the judge line is unchanged. Whatever refuses to render the `@7972..@8586` entries is not the absence of a ledger record at those calls.
2. It widens collateral instead (broker now differs from its committed product, on top of the quote and real_quote regressions r108a measured), so this variant is falsified for install on both counts.

The completion hypothesis is therefore closed in both directions - pre-claim at the four methods (addendum, -485 / 10-of-13 / three files changed) and post-claim at the callers (this addendum, no victim movement / three files changed). What remains unexplained is the walk itself: the six entries are registered in `_nested_if_entry_generate`, they are in `LoopRegion@5598.body_blocks`, the `generated_blocks` gate at `region_ast_generator.py:26775` refuses them and the registered dispatch at `:26864` is unreachable, yet making the ledger complete does not make the dispatch reachable either. So the next attempt must instrument **which list the arm walk iterates and whether those entries are in it at all**, before writing any further rule about ledgers. Task 157 is rewritten accordingly.
## Addendum 3 - the entries ARE handed to the walk: runtime monkeypatch census on unpatched bytes (2026-10-14 01:22)

The probe patched nothing on disk. It imported the mirror module (analyzer 996a1b1acf143458 + landed generator 566ff5c502276e48, both re-hashed after the run and unchanged), wrapped RegionASTGenerator._process_if_blocks to collect every BasicBlock passed in any positional or keyword argument, then exec-ed pycdc.py in-process on realtime_event_source.pyc.

```
RegionASTGenerator calls=95 target-offsets-seen=[7582, 7604, 7634, 7706, 7712, 7972, 8186, 8294, 8350, 8354, 8400, 8450]
  arglen=50 hits=all twelve      arglen=42 hits=all twelve
  arglen=27 hits=ten             arglen=1  hits=[7712]
TARGET not seen anywhere: []
```

That kills the premise I wrote in addendum 2 - the block lists are not the problem. All twelve entries, including the whole dropped run 7972 / 8294 / 8350 / 8354 / 8400 / 8450, are handed to _process_if_blocks inside lists of 50 and 42 blocks, and again in a list of 27. So the walk receives them and declines them for a reason *inside* the walk - the generated_blocks gate at region_ast_generator.py:26775 reports them as already generated, which means some earlier code path marked them consumed without producing statements for them. That is the same consumption-versus-emission conflation r108a named, now localized: the suspect is whoever inserts into generated_blocks for these six blocks, not the ledger and not the list contents.

Next instrumented step, in one command: log every write to generated_blocks with the inserting method name and the block offset, over this same unit, and compare the six offsets against the emission census - if a block is marked generated by a path that emits nothing for it, that path is the defect, and the rule to write is about that path, not about dispatch reachability.
## Addendum 4 - the drop is a post-render over-claim in the or-chain branch of _if_generate_normal, and it unifies ladder steps 1 and 3 (2026-10-14 01:25)

Same in-process monkeypatch as addendum 3, now recording the caller chain for every ADD and DISCARD of the six offsets, then reading the two named sites from the landed bytes. No file was edited; mirror hashes re-verified unchanged. The event order is identical for all six offsets:

```
first DISCARD for @7972 @8294 @8350 @8354 @8400 @8450  =  _generate_try_body:30068  (inside _generate_try:31866)
first ADD     for @7972 @8294 @8350 @8354 @8400 @8450  =  _if_generate_normal:22505 (inside _generate_if:15220)
```

The discard is legitimate and even cooperative: the try-body emitter frees a nested child region so that it can be re-rendered there.

```python
# _generate_try_body 30063-30074
if _r08_loop_child is not None:
    _lc_id_r08 = id(_r08_loop_child)
    if (_lc_id_r08 not in self._generated_regions and _lc_id_r08 not in self._generating_regions):
        for b in _r08_loop_child.blocks:
            self.generated_blocks.discard(b)          # 30068 frees the child for re-render
        nested_ast = self._generate_region(_r08_loop_child)
```

The add is the defect. In the [R23] short-circuit-or branch of _if_generate_normal, after the fold has consumed its operands, the code claims the whole arm lists of the region, excluding only the three operand blocks:

```python
# _if_generate_normal 22498-22505
for b in region.then_blocks:
    if b is not _r23_or_then and b is not _r23_or_else and b is not _r23_or_rhs:
        if b not in self.generated_blocks and b not in (region.chained_compare_blocks or []):
            self.generated_blocks.add(b)              # 22501
for b in region.else_blocks:
    if b is not _r23_or_then and b is not _r23_or_else and b is not _r23_or_rhs:
        if b not in self.generated_blocks:
            self.generated_blocks.add(b)              # 22505
```

Sequence consequence: the try path frees the six blocks precisely so they can be printed, the or-fold then marks them generated while printing only its three operands, the gate at :26775 correctly refuses every block already in generated_blocks, and the registered dispatch at :26864 is never reached. That is the entire 112-instruction drop. It also explains addenda 1 and 2: completing the emitted-entry ledger cannot help when a different mechanism is the one claiming the blocks.

**Rule to write** (one site, region data only): the post-fold claim must cover only the blocks the fold actually consumed as operands. A member of then_blocks or else_blocks that is not an operand and is not rendered by this branch must stay unclaimed so the owning parent sequence prints it.

Population caveat before editing: this site lives in the or-chain branch landed by gate 29, so it is not victim-unique. Count how often the two claim loops fire per file on the 20-file panel and on the 402 roster, narrow by the operand set, and re-prove quote 92/92, real_quote 45/45 and broker 128/128 unchanged before any sweep is believed.

Synthesis for the round: step 1 of the six-fact ladder (the 112-instruction drop) and step 3 (the @7164 or-chain that swallowed the system_log.debug call) are the same over-claiming site. That is why two analyzer halves moved nothing while the generator dispatch ledger recovered 37 instructions - the residual was never about which legs are mounted, it is about who is allowed to print the blocks.
## Addendum 5 - the named over-claim is safe to neutralize but buys nothing: sixth exclusion, and the drop is downstream of claim order (2026-10-14 01:27)

I built the experiment directly from addendum 4. Using ast to find every loop inside `_if_generate_normal` (method spans 22014-23645) that iterates `region.then_blocks` or `region.else_blocks` and writes `generated_blocks`, six loops were found at 22498, 22502, 22527, 22531, 22538 and 22813, and five claim statements at 22501, 22505, 22530, 22534, 22539 were replaced by `pass` (indentation preserved, so the enclosing if statements keep valid bodies - my first attempt deleted whole loops and died with an expected-indented-block error at 22522, which is a rig bug, not a result). Variant `64d05383cbe48394`, 3,869,799 B, BOM intact, zero bare LF, zero CR CR LF, compile clean, paired with the `[R21-79]` analyzer 3ad5ceaa, mirror platform restored and re-hashed in the same command.

| file | committed bytes | variant bytes | verdict |
|---|---|---|---|
| trade_live_broker | 178823 | 178823 | IDENTICAL |
| plugin_system_risk_calculation/function | 30095 | 30095 | IDENTICAL |
| fly/data/quote | 93018 | 93018 | IDENTICAL |
| real_quote | 53841 | 53841 | IDENTICAL |
| replace_utils | 13501 | 13501 | IDENTICAL |
| realtime_event_source | (R21-79 arm) 20078 | 20078 | unchanged by the neutering |

Victim readings with the neutering: `ours=241`, `hunks_vs_ORACLE=4`, `DELTAS instrs=-115`, `jsites=-9`, `back=+0`, judge `12/13` - byte-identical to the `[R21-79]` half alone. In other words the or-fold claim is **not** the mechanism that suppresses the six blocks: leaving them unclaimed changes nothing, while provably changing nothing else in the corpus either.

That is a useful pair of facts to hand over. (1) The five claim statements are dead weight for this unit - neutralizing them is zero-collateral, which is itself a candidate co-requisite but not a fix, so it is recorded and not installed. (2) The drop must therefore be positional: after the try-body frees the blocks, no *later* walk revisits those offsets - the parent body sequence has already passed them. Claim order and walk order, not claim membership, are what the next rule has to address, which means instrumenting the parent walk itself (which list it is on, what index it is at, and what it skips) rather than any ledger.

Exclusions now on this single unit, all measured this session: analyzer tail-release (correct, zero collateral, zero flip), analyzer folded-join (destructive then inert then redundant), generator pre-claim ledger (-485, 10/13), generator caller-side post-claim ledger (no victim movement, collateral widened), generator claim neutering (no victim movement, zero collateral). The best-known arm is still the `[R21-79]` + `[R21-81]` pair at `instrs=-78`, `jsites=-3`, `back=+0`, 3 hunks, 12/13.