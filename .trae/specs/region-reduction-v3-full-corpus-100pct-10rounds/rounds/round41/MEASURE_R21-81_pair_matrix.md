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
## Addendum 6 - stacking the neutering on the dispatch ledger: no victim gain, wider collateral (2026-10-14 01:30)

Stack built by text-substituting every bare `self.generated_blocks.add(b)` inside `_if_generate_normal` on the `[R21-81]` candidate (that method spans 22067 onward in its bytes; six statements hit at 22554, 22558, 22583, 22587, 22592, 22594 - one more than the five in addendum 5, because two extra arm-list loops exist there). Variant `23370fda7602da47`, 3,874,032 B, BOM intact, zero bare LF, zero CR CR LF, compile clean, analyzer arm `3ad5ceaa`, mirror platform restored and re-hashed in the same command.

- Victim: 20484 B with `instrs=-78`, `jsites=-3`, `back=+0`, `hunks_vs_ORACLE=3`, judge `12/13` - **byte-identical to the un-neutered pair**. The neutering buys nothing even where the ledger already recovered 37 instructions.
- Collateral: broker 180452, risk function 30087, quotation 185112, quote 93849, real_quote 54675 all differ from committed products (only `order_api` 34308 and `replace_utils` 13501 hold). So the wider neutering actively damages three more files.

Claim membership is therefore excluded as the suppressor in every combination tested - alone (addendum 5), on the analyzer-only arm, and stacked on the generator ledger. The only surviving reading is positional: after `_generate_try_body:30068` frees the six blocks nobody walks those offsets again, which is what task 158 and engineer r110a are censusing.
## Addendum 7 - r110a positional census lands, my 26911 follow-up is falsified, and the blocker moves back to the analyzer lists (2026-10-14 01:52)

r110a delivered `rounds/round41/r110/MEASURE_R21-84_walk_position.md` (206 lines, diagnosis only, probe inertness proven in four probe modes by re-hashing and product comparison). Headline findings, quoted from its sections:

- Section 1: every one of the 17 offsets in the run is **present in a walked list but skipped by a guard** - `:29937 to :29938`, `:8764 to :8765`, `:26775 to :26776` - and **iteration never stops early** (seq12 iterated all 161 blocks, seq233 all 100, seq304 all 50, seq313 all 42). `_generate_block_statements` was called for **0 of the 17** offsets in any walk.
- Section 1 also states the sharper half: the 14 run blocks are **never in any list that IfRegion@7604 else-arm walks** - the gap is list assembly, not iteration.
- Section 2: no later walk revisits them for emission and none ever did; the first thing that marks any of the 17 is `:22505`, inside the or-chain claim loop.
- Section 4 corrects my addendum 4 wording: the event I read as a DISCARD transition at `_generate_try_body:30068` is a **set operation, not a transition** - none of those blocks was in `generated_blocks` at that moment, so the r08 free is a no-op for this run. My addendum 4 sentence should be read as ordering of recorded operations, not of state changes.
- Section 5 explains the addendum 5 and 6 zero-gain results: the guards above fire regardless of claim membership, and a sixth claim site `:26911` also exists.

I tested that sixth site immediately on the R21-79 analyzer arm: neutering only `:26911` (variant `924604fc9cb25317`, 3,869,890 B, BOM intact, zero bare LF, zero CR CR LF, compile clean, platform restored and re-hashed in the same command) leaves the victim at 20078 B, `instrs=-115`, `jsites=-9`, 4 hunks, `12/13` - byte-identical to the un-neutered analyzer-only arm - while **broker (179758 vs 178823) and klinedata (103412) both change**. So claim membership is now excluded a seventh time, and with r110a section 1 in hand the reason is clear: the guard is not the suppressor, the missing list membership is.

Retarget recorded: the fix belongs in the analyzer arm-list assembly for `IfRegion@7604` else-arm (r110a section 6 phrases the requirement as (a) a branch may claim only blocks it renders and (b) residual `else_blocks` members with offset below the first grafted `elif_final_else` member - the 14 blocks, 112 instructions - must be reachable), which is ticket **R21-86** dispatched to r111a. Best-known arm is still `[R21-79]`+`[R21-81]` at `instrs=-78`, `jsites=-3`, `back=+0`, 3 hunks, `12/13`, with quote and real_quote regressions that an analyzer-side assembly fix must not be asked to mask.
## Addendum 8 - CONFIRMED: the suppressor is the conjunction of two claim sites, and un-marking both recovers 108 of the 112 instructions (2026-10-14 01:55)

r110a final report: 0 OUT flips out of 157 at `_generate_try_body:30068`, so that discard is a set operation, not a transition, and the run was never freed - my addendum 4 wording is superseded by addendum 7. Its un-claim experiment predicted that the suppressor is the pair. I tested it within minutes, all arms paired with analyzer `3ad5ceaa` (`[R21-79]`) in `D:/Temp/r91m`, platform restored and re-hashed every time:

| generator arm | victim | instrs | jsites | back | hunks | judge | collateral vs committed |
|---|---|---|---|---|---|---|---|
| neuter the five in-method claims only | 20078 / 241 lines | -115 | -9 | +0 | 4 | 12/13 | none |
| neuter `:26911` only (`924604fc`) | 20078 / 241 | -115 | -9 | +0 | 4 | 12/13 | broker, klinedata CHANGED |
| **neuter `:22505` AND `:26911` (`71c6863e`)** | **21588 / 262 lines** | **-7** | **+2** | **+0** | 5 | 12/13 | broker 179758, klinedata 103412 CHANGED |
| the pair plus four more in-method claims (`413c6130`)** | 21588 / 262 | -7 | +2 | +0 | 5 | 12/13 | same two files |

The claim pair is the suppressor: neither site alone changes the victim, and both together move the instruction gap from -115 to **-7**, the first time this campaign has recovered essentially the whole dropped run. Two problems remain, both measured, and both are why nothing is installed:

1. **Over-emission**: the unit is now 262 lines against the oracle 254 and `jsites` has flipped sign from -9 to **+2**, so part of the run prints twice. The two claim sites are what prevent the second print, so a blunt un-mark trades a drop for a duplicate.
2. **Collateral**: `trade_live_broker` and `klinedata` products both change, expected because `:22502-22505` sits in the gate-29 or-chain branch and is not victim-unique.

The rule therefore has to be render-scoped rather than removal-scoped: each claim may mark only the blocks the branch actually rendered - which for `IfRegion@7604` is the 8-block grafted `elif_final_else` arm (r110a measured zero of the 14 run targets inside it) - and every other member of `then_blocks` / `else_blocks` must stay unclaimed for the owning parent sequence. That is ticket **R21-86**, dispatched to r111a with this table as its baseline to narrow, the design constraints (region data only, no offsets, no thresholds), and the acceptance order: `instrs` and `jsites` to 0 from below without overshoot, then the 10-file collateral table with broker back at 178823 and klinedata unmoved, then the 20-file panel, then the ROOT-joined 402 sweep, then the judge.

Both measured generator variants are banked at `rounds/round41/r111/` together with `build_and_measure_claim_pair.py`, which rebuilds and re-scores them from the landed bytes. Corpus still 6616/6617 (99.9849 percent), 401/402 files, gate label 41 unconsumed, repo `core/` at landed bytes.
## Addendum 9 - render-scoping the claims by list membership is safe but inert: the truncation is inside the arm renderer (2026-10-14 01:12)

Three more arms built by me from the landed bytes, all paired with analyzer 3ad5ceaa, each with the mirror platform restored and re-hashed inside the same command. Build scripts committed at `rounds/round41/r111/` (`build_and_measure_claim_pair.py`, `render_scoped_r2187.py`, `render_scoped_r2188.py`).

| arm | what it changes | victim | instrs | jsites | hunks | judge | collateral (10-file smoke) |
|---|---|---|---|---|---|---|---|
| A dd3c0afa | claims 22500/22504 restricted to the rendered set (elif_conditions, elif_bodies, elif_final_else, chained_compare_blocks, the three or operands) | 241 lines | -115 | -9 | 4 | 12/13 | none |
| B 4d75cf87 | A plus un-marking 26911 | 262 | -7 | +2 | 5 | 12/13 | broker, klinedata |
| C 97ad4d9d | A plus the same render-scoped restriction at 26911 (claim only blocks inside the dispatched region own arm lists) | 241 | -115 | -9 | 4 | 12/13 | none |

A and C are safe (zero collateral; the nine smoke files byte-identical to their committed products) and buy nothing. B buys 108 instructions and pays duplication plus two changed files.

Reading of C: restricting the 26911 claim to the dispatched region own arm lists does **not** free the run, because the fourteen blocks really are members of that region arm lists - the dispatched region is `IfRegion@7634` and the run sits in its `then_blocks`, exactly as r107a measured for the tail release. So a render-scoped claim cannot be computed from list membership at all.

**The operative defect is one level deeper than either claim: the else-arm rendering of `IfRegion@7634` stops at the nested `LoopRegion@7706` and never continues with the remaining members of its own `then_blocks`, while the claim loops mark the whole list consumed.** A fix therefore has two coupled halves: (a) the arm renderer must continue past a dispatched child region to the rest of the same arm, and (b) the claim must cover exactly the emitted set. Half (b) alone is proven inert here (A and C); half (a) approximated by brute un-marking is what produces the duplication and the two collateral files in B.

That is the sharpest statement of the last-unit defect produced in 41 rounds, and it is what ticket R21-86 (r111a, live) has to implement. Status unchanged: corpus 6616/6617 (99.9849 percent), 401/402 files, gate label 41 unconsumed, landed bytes unmoved, nothing installed.

## Addendum 10 - two more arms: entry-owner discrimination is destructive, and un-marking on top of the ledger overshoots into over-emission (2026-10-14 01:26)

Same rig style, same platform discipline (built from landed or banked bytes, installed only in D:/Temp/r91m, restored and re-hashed in the same command, analyzer arm 3ad5ceaa).

| arm | what it changes | victim | instrs | jsites | back | hunks | judge | collateral |
|---|---|---|---|---|---|---|---|---|
| D f46945ef | A plus skip the nested-dispatch claim when the block is the entry of some other region | 4 lines | -1439 | -123 | back -4 | 1 | 9/13 | broker, klinedata, quote, real_quote all CHANGED |
| E 0a8099a4 | the R21-81 ledger plus un-marking its three claim statements (22558, 22587, 26983) | 266 lines | **+17** | +5 | back +0 | 5 | 12/13 | broker, klinedata, quote, real_quote |

D was my attempt at a principled discriminator at the nested-dispatch claim: skip claiming a block that is the ENTRY of a different region (principles 2 and 4 reading). It collapses the unit to 4 lines, 1439 instructions short with back edges broken and four files changed, so entry-ownership as computed from block_to_region is not a usable discriminator here - the same trap the round-40 census warned about when a symptom is turned into a rule.

E answers the question I actually needed: does the R21-81 emitted-entry ledger remove the duplication that addendum 8 measured? No. Un-marking the three claim statements on top of the ledger takes the unit from 262 lines (the blunt pair) to 266 against the oracle 254, and the instruction gap crosses zero from -7 to **+17**: the run is now printed more than once. So the ledger does not act as a single-owner gate for these blocks, and the residual requirement is sharpened to: un-mark must be paired with **an explicit single owner** for the freed run (either the arm that contains it or the parent sequential list), not with a general emitted-entry ledger.

Numbers for the next hand, all on analyzer 3ad5ceaa: blunt pair 262 lines, -7, 5 hunks; ledger plus un-mark 266 lines, +17, 5 hunks; render-scoped claims 241 lines, -115, zero collateral. The oracle is 254 lines and 13/13, so the target of the fix is a single emission of the run with the arm terminating where the oracle does.

Still nothing installed. Corpus 6616/6617 (99.9849 percent), 401/402 files, gate label 41 unconsumed, landed bytes unmoved, repo core/ clean, r111a (ticket R21-86) still live on the arm-continuation half.
## Addendum 11 - r111a delivers R21-86: instruction gap closed to -6 with ZERO collateral, still 12/13, so banked as the new best-known arm (2026-10-14 01:34)

Candidate generator `59a405837c22a4cb` (3,873,983 B, BOM intact, 100 percent CRLF, zero bare LF, zero CR CR LF, compile clean, idempotent patch), **generator-only on the pinned F5 analyzer** - the R21-79 analyzer half is NOT a co-requisite and measurably hurts when paired.

| arm | ours (oracle 254) | instrs | back | jsites | hunks | judge |
|---|---|---|---|---|---|---|
| F5 base | 241 | -114 | +0 | -9 | 4 | 12/13 |
| my blunt pair 71c6863e | 262 | -7 | +0 | +2 | 5 | 12/13 |
| **R21-86 rule alone on F5** | **262** | **-6** | **+0** | **+2** | **4** | **12/13** |
| R21-86 rule + R21-79 analyzer | 262 | -7 | +0 | +2 | 5 | 12/13 |

Ablations r111a ran (all recorded): release without the 26911 honour returns base, honour without release returns base, so the conjunction is now carried by **one rule with two load-bearing halves**; extending the release to then_blocks buys nothing and was rejected. I independently scored the candidate myself at 01:33 and reproduced -6 with zero collateral.

**Collateral: none.** Ten-file CR-stripped smoke: broker back at its committed 178823, klinedata 100737, quote, real_quote, quotation, order_api, replace_utils, function, handlers all byte-identical; only the victim differs, which is intended. Site A fires 17 times in the victim (all IfRegion@7604) and zero times in broker and klinedata, which is exactly why the blunt un-mark in addendum 8 damaged those two files and this rule does not.

**Panel 20 by index: zero regression.** Rows 00-11 and 13-19 all success and byte-same (quotation 153/153, quote 92/92, klinedata 64/64, handlers 30/30, wizard 58/58, trade_info_utils 41/41, api_base 28/28, real_quote 45/45, strategy 27/27, order_api 37/37, broker 128/128, matcher 17/17, risk init 43/43, arg_checker 49/39/43, profiler 17/15/18); row 12 is the victim at 12/13. **Sweep: ROOT-joined, length asserted 402, sharded 100/100/100/102, MISSING/FAIL 0 in every shard, CHANGED_COUNT 1 = the victim only.**

What still blocks the flip, stated by r111a and consistent with my own reads: the unit overshoots to 262 lines not from duplication (every run marker appears exactly once in both gold and product) but from eight lines of pre-existing step-3 and step-4 or-chain scaffolding in the base. So the instruction gap is now -6 and the surviving axis is the position of that scaffolding, which is addendum 9 half (a), the renderer position, not claims.

Status: still no flip, so R21-86 is **banked, not installed**, and gate label 41 stays unconsumed. It is the best-known arm in the campaign by a wide margin - from -114 to -6 instructions with zero collateral, panel-clean and sweep-clean. Artifacts: rounds/round41/r111/ (candidate, patch, FIX, MEASURE) plus this table. Corpus 6616/6617 (99.9849 percent), 401/402 files, landed bytes unmoved, repo core/ clean.
## Addendum 12 - [R21-87] is collateral-clean but proves the [R21-86] reading of -6 instructions was parity by cancellation (2026-10-14 04:05)

r112a built a positive-polarity single-leg or-chain fold on top of [R21-86] and shipped generator ed07b60b970e545d. I re-scored it in my own mirror at 04:02 on analyzer 996a1b1acf143458: ours=257 (base 262, oracle 254), instrs=-26, back=+0, jsites=-2, hunks_vs_ORACLE=6, indeg-equal=False, judge 12/13, and all nine collateral files byte-identical (broker, klinedata, quote, real_quote, quotation, order_api, replace_utils, function, handlers). Panel 20 by index: 19 rows byte-same with unchanged units, row 12 the victim at 12/13. ROOT-joined 402 sweep: files_compared=402, MISSING/FAIL=0, CHANGED_COUNT=1 = the victim only. So the arm is collateral-clean and still does not flip, and by its own bar (instrs must move toward 0) it fails: it moves away.

The informative part is the ablation table, because it redefines what the [R21-86] reading meant:

| arm | ours | instrs | back | jsites | hunks |
|---|---|---|---|---|---|
| [R21-86] base | 262 | -6 | +0 | +2 | 4 |
| fold only | 256 | -27 | +0 | -4 | 8 |
| fold plus narrow, no guard | 212 | -282 | -1 | -33 | 6 |
| guard applied after the marks | 262 | -6 | +0 | +2 | 4 (inert, base bytes) |
| shipped fold with pre-mutation guard | 257 | -26 | +0 | -2 | 6 |

Reading: the [R21-86] figure of -6 is scaffolding-masked parity, not near-parity. The nesting it introduces double-pays for the tests, so the deficit it hides is roughly -26 in the 7582 to 9194 tail, and correcting the text with the fold removes the mask and lets the true gap appear. That is the same asymmetry recorded in the standing rule that a text change is not unit movement, now in the opposite direction: a shorter oracle diff can accompany a worse unit, which is why the judge is the criterion and why instrs and jsites must be read together rather than as separate wins.

Next axis, from r112a diagnosis plus my own reading of the same table: the 7164 chain owns the whole loop tail, so step-3 refuses the fold. That tail-ownership claim is the remaining mechanism, and it was measured destructive once before in the [R21-48] family, so it needs a new discriminator rather than a re-attempt. Ticket R21-88 is dispatched to r113a on the [R21-86] base (not on [R21-87], which is banked), with the requirement that instrs and jsites both move toward 0 together and that the [R21-86] base arm stays byte-reproducible.

Still nothing installed. Corpus 6616/6617 (99.9849 percent), 401/402 files, gate label 41 unconsumed, landed bytes unmoved, repo core/ clean.
