# Round 30 diagnosis C — the two NEGATIVE-deficit members of Round 29's cluster A

Everything below is MEASURED on the landed core `06f0ba50` (R29-A landed) by this agent, in
`D:/Temp/r30diagC` (no repo file touched; verified `git status` clean at the end).

Harness: `python -X utf8 D:/Temp/r30diagC/r30.py run --arm=landed --list=list2.txt
--out=landed2.jsonl` (copy of `r29gate/r29.py`, ROOT moved to `D:/Temp/r30diagC`).

## 0. Did R29-A move either target?  NO — proven, not assumed

| target | landed-core reading (this agent) | shipped `site-packages/**OK.py` |
|---|---|---|
| `default_event_source.pyc :: <module>.DefaultEventSource.events` | `13/14`, mism `[['events', 510, 491, 2, 157]]` | product byte-identical to shipped file (sha `31b391283753`) |
| `matcher.pyc :: <module>.DefaultMatcher.match` | `16/17`, mism `[['match', 713, 689, 9, 524]]` | product byte-identical to shipped file (sha `a6e9dd453c81`) |

So the pre-R29-A numbers of the other agent (`510/491`, `713/689`) still hold verbatim and the
targets did NOT move. Consistent with G4 `SAME=401 IMPROVED=1`.

## 1. Per-target measured table (current landed bytes)

Strict ruler (`_r10_strict_check.py`, products staged next to a copy of the pyc in
`build_landed/`, so `check_pyc` resolves `…OK.py`):

| target | official (gate) | strict | strict kind |
|---|---|---|---|
| events | 510/491 (-19), jump 2 / true 157 | 512/493 (-19) | `seq_len` |
| match  | 713/689 (-24), jump 9 / true 524 | 715/689 (-26) | `seq_len` |

First-divergence hunks (`fd30.py` = `r29diagB/fdump29b.py` with an explicit OK.py argument) and
moved-vs-lost per hunk (`mv30.py` = `r29diagB/mv29.py`, same adaptation). Windows:
`fd_events.txt`, `fd_match.txt`.

### events (`<module>.DefaultEventSource.events`) — 4 non-equal blocks
| hunk | offsets | moved-vs-lost |
|---|---|---|
| `delete orig[352:367]` (15) | @2380..2472 | **MOVED** 15/15 → decomp idx 466 @3116 (the loop's tail slot) |
| `replace orig[481:483]` (2→8) | @3208..3212 | the back-edge/JUMP pair overwritten by the moved prologue |
| `replace orig[485:486]` (1→1) | @3238 `LOAD_CONST 15` → `LOAD_CONST 8` | epilogue statement clobbered by prologue statement |
| `replace orig[489:500]` (11→1) | @3252..3322 | **LOST**: `STORE_FAST dt \| Event(AFTER_TRADING_END) \| YIELD` collapses to 1 |

Byte-identical to the pre-R29-A reading. The 15 moved instructions are the `for day in
self._trading_dates:` body prologue (`date = day.to_pydatetime()`, `last_tick = None`,
`last_dt = None`, `dt_before_day_trading = date.replace(hour=8, minute=30)`); the run that
disappears is that loop's tail (`dt = date.replace(15,30)` + `yield Event(AFTER_TRADING_END…)`).

### match (`<module>.DefaultMatcher.match`) — 3 non-equal blocks
| hunk | offsets | moved-vs-lost |
|---|---|---|
| `delete orig[182:463]` (281) | @1322..3206 | **MOVED only 65/281** (contiguous run found at decomp idx 431 @3076) — the rest is scattered/rotated, ≥216 instructions do not re-appear as a run |
| `delete orig[575:579]` (4) | @3952..3966 | **MOVED** 4/4 → decomp idx 427 @3058 |
| `insert decomp[428:687]` (259) | @3060..4860 | **COPY** back into orig only 3/259 as a run ⇒ the deferred text is *rotated*, not merely moved |

Product evidence (`build_landed/…matcherOK.py` lines 189-207): an `else:` arm (line 189) is
followed, at the *outer* indent, by `elif order.asset.symbol[:3] == '300':` (line 191) — an
`elif` printed after the `else` of its own chain: the rotation is visible at source level, not
only in the alignment.

## 2. ONE SHAPE OR TWO — verdict: TWO, and only target 2 is in R29-A's family

The deciding measurement is the landed core's own ownership data (print-only stamp `A1`/`A2` on
mirror `mirr_p30e`, log `subA.err`, plus read-only structural probe `probe30.py` →
`probe_events.txt`, `probe_match.txt` which dumps `block_to_region` + every role list + the
region tree):

* **events**: the mis-positioned text is NOT a block that any arm claims. Block decomposition
  says the prologue lives *inside a single basic block*: `blk @2378..2474 n=19 succ=[2476]
  term=NOP` — i.e. `STORE_FAST day` and the four prologue statements are one block, claimed
  exactly once, by `FOR_LOOP@2374.body_blocks`. Its placement at the loop tail is a split
  **inside** that block (the for-header eats instruction 2378, the remaining 15 instructions are
  emitted after the nested region), and the disappearance is a *second* mechanism: the outer
  for-loop's `back_edge_block` @3214 is simultaneously claimed as a **break block** of the
  nested `WHILE_LOOP@2476` (`@3214 → WHILE_LOOP@2476 break_blocks`, while `FOR_LOOP@2374`
  carries `back=3214` and lists 3214 in `body_blocks`). So: instruction-level leftover + a
  nested region stealing the parent loop's back-edge block. No arm-list double claim ⇒ **not**
  the R29-A shape.
* **match**: the mis-positioned text IS arm-list over-claim, and it is enormous: e.g.
  `IF_THEN entry=1324 then=[1372, 1444, … , 2460, 2464, 3210, 3226, …, 4960] merge=1384` and
  `IF_THEN entry=2468 then=[2484, 2526, 2606, 2846, 2888, 2968] merge=3208` — arms whose block
  lists run past the region's own `merge_block` (past its join), which is exactly the
  "join/post-join block absorbed by an arm" family R29-A was cut from; R29-A only removed the
  *intersection* of the two arms, so a post-join block claimed by one arm survives.

Decisive measurement, stated once: in events the offending text has **one owner and that owner
is a loop body list, and the loss sits in a `break_blocks` claim**; in match the offending text
has **owners in `then_blocks`/`else_blocks` that reach beyond the region's merge**. A single
arm-list predicate cannot address both, and the events mechanism cannot be reached from the
R29-A anchor at all.

## 3. Emission / attribution chain — BY STAMP, not by reading

Print-only stamps (byte-level line insertion; each mirror self-proves "delete every stamped
line == original bytes" and `compile()`s): `mkstamp30c.py`→`mirr_c30` (G1 region dump, G2 walk
order, G3 orphan release, A1 LoopRegion ctor), `mkstamp30c2.py`→`mirr_c30b` (H1..H6 loop-body
path), `mkstamp30c3.py`→`mirr_c30c` (P0 child-claim, P1 prefix registry), `mkstamp30c4.py`→
`mirr_c30d` (**690 stamps, one before *every* `self.generated_blocks.add(...)` site in the
file**, gated on the six watched blocks and on `cfg.name in ('events','match')`).
Logs: `stamp.err`, `stampb.err`, `stampc.err`, `stampd.err` (67 hits), `subA.err`.
`mirr_c30d` products are in `build_c30d/`; `stampd.jsonl` shows the run itself stayed green.

### 3a. events — the loss chain (all four links measured)

1. **Analyzer** — `core/cfg/region_analyzer.py:4098-4103`, the `verified_break_blocks` loop of
   the LoopRegion construction path. Block **@3214** passes
   `any(pred in _r102_reachable …)`, so it becomes a *break block of the nested
   `WHILE_LOOP@2476`* and, via `region_blocks.add(break_block)` (`:4103`), enters that region's
   block set. Measured ownership (`mkp30e.py`/`probe30.py`, `subA.err`, `P0`):
   `[P0] cfg=events parent-loop=2374 child=2476 child-body=[2476,…,3208,3210]
   CHILD-CLAIMS=[2476,…,3208,3210,3214]` — **@3214 is claimed by the child only through
   `region.blocks`; it is in no role list of the child, and it *is* `FOR_LOOP@2374`'s own
   `back_edge_block` and is in `FOR_LOOP@2374.body_blocks`.** One block, two owners ⇒ a direct
   violation of Principle 2 (unique ownership), which is exactly what the R29-A guard exists to
   catch — but R29-A only intersects `then_blocks`/`else_blocks`, so a *loop-role* double claim
   is invisible to it.
2. **Marking** — `_generate_loop` `core/cfg/region_ast_generator.py:4205-4216`: after the child
   loop renders, `for block in region.blocks: if block not in region.else_blocks: …
   self.generated_blocks.add(block)` marks @3214 generated. Measured:
   `[Q] L4216 3214 cfg=events` with stack
   `_generate_region:3073|_process_if_blocks:20754|_if_generate_elif_chain:15983|_if_generate_full_elif_chain:12400|_generate_if:11211|_generate_region:3075`.
   @3214 is additionally marked at `_loop_generate_body:6469` (the Round-08 child hand-over) and
   at `_process_if_blocks:20469` (bulk `_lr.blocks` claim) — three independent claims.
3. **Suppression** — `_loop_postprocess` `:10930-10933`:
   `for _src_blk, _src_count in back_edge_source_blocks: if _src_blk in self.generated_blocks:
   _offset += _src_count; continue`. The outer FOR loop therefore skips the whole instruction
   run of its own back-edge block: 17 instructions of `dt = date.replace(hour=15, minute=30)` /
   `yield Event(EventEnum.AFTER_TRADING_END, …)` are never emitted.
4. Nothing re-emits them: `top_level_regions`/orphan release (`:1502-1548`) is **not** involved —
   stamp G3 fired **0 times** on both targets.

### 3b. events — the mis-positioning chain (a second, independent mechanism)

The 15-instruction body prologue (`date = day.to_pydatetime()`, `last_tick = None`,
`last_dt = None`, `dt_before_day_trading = date.replace(...)`) is **inside** basic block @2378,
which the for-header consumes only up to its first instruction. Measured walk order:
`[H2] blk=2378 handled=False` → `[H3] DEFER blk=2378` (`:6569`
`body_blocks_no_header.append(block)`) → `[H5] leftovers=[2378]` (`:10922`) →
`[H6] TAIL-APPEND n_stmts=4` (`:10928` `body_stmts.extend(branch_stmts)`).
The reason the in-body pre-flush guard (`:6535-6562`, which exists precisely to render pending
plain blocks before a child region is appended) does not fire is positional: **the Round-08
nested-child hand-over at `:6437-6470` ends in `continue`, so the guard below it is never
reached on the very block that needs it.** This is the "ordering" half of the file and it is
count-neutral — hence a predicate for it alone can never flip the file (measured: arm `n2`,
`491` stays `491`).

### 3c. match — a different chain entirely

No H3/H4 (loop defer/hand-over) hits at all, and G3=0. Instead @1696/@1820/@1830/@3210 are each
marked generated **4–9 times from at least three distinct bulk-claim sites inside the if-branch
machinery**, reached by re-entrant branch recursion:
`[Q] L20450 1696 cfg=match  stack=_process_if_blocks:21242|_if_generate_then_branch:14575|_if_generate_normal:17237|_generate_if:11357|_generate_region:3075|_process_if_blocks:21242`,
plus `L20942` (bulk `_region.blocks` claim), `L21265` (bulk `nested.blocks` claim for
Ternary/BoolOp), `L16811` (`_if_generate_normal`'s disjunct claim), `L33568`
(`_generate_ternary`'s chained-compare claim), `L10712`
(`_loop_handle_child_region_entry`'s `entry_region.blocks` claim).
The *last* claim wins and the text is rendered by a different branch instance than the one that
consumed it — which is what produces the 22 count-preserving backward jumps (rotation) measured
by `perm30.py`. That is an if-arm attribution defect (the R29-A/R27-B family, one level deeper:
post-merge blocks still surviving in a single arm list), not a loop-role defect, and it needs
its own predicate; the R30-C1 edit leaves `match` byte-identical (`f7821a793de7106b` on every
arm).

## 4. THE ONE RANKED CANDIDATE — R30-C1

**Anchor:** `core/cfg/region_analyzer.py:4098-4100` — the two lines
`if break_blocks:` / `for break_block in break_blocks:` and the test line
`if any(pred in _r102_reachable for pred in break_block.predecessors):` that follows them,
inside the LoopRegion construction path (the `_r102` block, ~4060-4130).
Spec as measured: `spec_c1.json` (1 edit, **+6 lines**), arm `mirr_c1`/`build_n1`, source
`mkspecs30.py`.

**Predicate, structural terms only:**
> A candidate break block of a loop region is a block that *leaves* that region. If the
> terminal instruction of the candidate is a member of the backward-jump class and its target
> block is not this region's own header block, then that terminal is a back edge belonging to
> an enclosing loop, and the candidate cannot be a break of this region: do not verify it, do
> not add it to the region's block set, do not let it reach `verified_break_blocks`.

No variable names, no constants, no offsets, no instruction counts, no successor index counts —
only (i) region role membership (candidate is being considered for this region's break role),
(ii) terminal-op class (backward jump), (iii) the jump-target/header identity relation.

**Which existing guard it sits beside:** the same code block already contains, 8 lines above
(`region_analyzer.py:4089-4091`), `_rl = _rb.get_last_instruction()` /
`if _rl and _rl.opname in BACKWARD_JUMP_OPS and _rs.start_offset == _rl.argval: continue` — the
*successor*-side mirror image of the same fact (a whose-terminal-jumps-back-to-itself successor
is a back edge, not an exit). R30-C1 uses the identical helper (`get_last_instruction`), the
identical op-class constant (`BACKWARD_JUMP_OPS`, imported at `:30`) and the identical relation
shape, just on the break-role side. It is the same author's idiom one loop further down, which
is why the patch is 6 lines and introduces no new vocabulary.

**Removal-only:** yes, strictly. It removes a membership (`verified_break_blocks.add` and the
`region_blocks.add` that follows at `:4103`) and therefore removes an ownership claim. It adds
no emission, no statement, no block. Everything that later appears was already owned by exactly
one region — the enclosing loop — and was merely being suppressed by the inner loop's bulk mark
at `region_ast_generator.py:4216`.

**Measured effect (all three levels):**

| subject | landed | + R30-C1 |
|---|---|---|
| events (official) | `['events',510,491,2,157]` | `['events',510,508,2,157]` |
| events (strict ruler) | 512/493 (−19), 4 non-equal hunks | 512/510 (−2), **2 hunks** |
| synthetic witness battery `repro30/r30c_w2.pyc` | 3/6: `w_a` 27/21, `w_b` 23/19, `w_e` 30/26 | **6/6, zero mismatches** |
| control battery `repro30/r30c_witness.pyc` | 6/6 | 6/6, **product hash identical** (`ef52a76276145780`) |
| 96 load-bearing anchors | — | 96 byte-identical |
| 38 repro-battery files | — | 38 byte-identical |

**Honest status: it does NOT flip `default_event_source.pyc`.** With C1 alone the file is
13/14 at −2. Adding the second, independent mechanism (R30-C2 below) makes the strict alignment
collapse to **exactly one** non-equal hunk: `delete orig[481:483]` = the 2-instruction pair
`JUMP_FORWARD <exit> / JUMP_BACKWARD <inner header>` at the end of the `while True:` body
(`fd_c12_events.txt`), and cuts the official `true_diffs` from 157 to 31 (jump_diffs 2→4).
So the pair C1+C2 is a −19 → −2 recovery with 0 collateral; the last −2 is a *third* shape.

**Fallback if C1 does not fire in the shipping gate** (i.e. it breaks a file the 98-file sweep
did not cover): narrow by one structural clause — "…and the target block of that backward jump
is a block this region *contains* or is enclosed by" (the enclosing-header identity is already
computable from `_r102_reachable`/`self.cfg.get_block_by_offset`); the narrowed form is only
reachable by blocks that genuinely carry an enclosing loop's back edge, which is the entire
witness population. Second fallback: keep the claim but exclude the block from the bulk
`generated_blocks.add` sweep at `region_ast_generator.py:4205-4216` — measured NOT to work
(`spec30c.json`, arm `candc`: TALLY SAME=2 IMPROVED=0) because @3214 is claimed by three
different sites, so an emission-side narrowing of one of them is defeated; **the fix has to be
the single analyzer-side claim.** That is the load-bearing negative result of this diagnosis.

### R30-C2 (ranked second, needed only if the −2 residual is chased)

Anchor `core/cfg/region_ast_generator.py:6458-6459` (`if _r08_nested_loop_child is not None:` /
`_nlc_id_r08 = id(_r08_nested_loop_child)`), spec `spec_c2.json` (+22 lines), arms
`mirr_n2`/`build_n2` and `mirr_c12`/`build_c12`. Predicate: *when a parent loop hands over a
direct child loop region at the child's entry (Principle 4) while plain body blocks that
precede the child in fall-through order are still pending, those pending blocks must be
rendered in place first* — i.e. extend the existing pre-dispatch flush invariant
(`:6535-6562`) to the hand-over path, reusing `_if_generate_branch_stmts` and the same
compound-terminal/leading-`Continue` trimming. It is **emission-side but not emission-adding**:
it repositions statements that were already emitted (count-neutral on both targets: events
stays 491 alone, 508 with C1). It is the only honest answer to "why is the 15-instruction
prologue printed after the loop instead of before it". Measured side effects: none in the
98-file sweep when combined with C1 (SAME=97, MOVED=1); alone it moves the same single file
(true_diffs 157→31).

**Preference note for the orchestrator:** the program's removal-only rule is satisfied by C1
and *not violated* by C2 (C2 adds no instruction emission), but C2 does add 22 source lines and
changes jump-slot placement (jump_diffs 2→4 on events). If a round must land exactly one
predicate, land C1; C2 is only worth it inside a round that also closes the last 2.

## 5. Trigger-surface sweep (NOT the 402 A/B)

List used: `sweep.txt` = the 96 anchors of `D:/Temp/r29gate/anchors96.txt` **plus**
`D:/Temp/r29gate/reprobat38.txt` (which is a subset of the 96 — verified: 38/38 covered) **plus**
the two targets = 98 files, all run on every arm; `list2.txt`/`two.txt` = the 2 targets.

| arm | jsonl | SAME | IMPROVED | REGRESSION | MOVED | ERR | fully-matched files |
|---|---|---|---|---|---|---|---|
| landed (baseline) | `sw_landed.jsonl` (= `sw_landed_0/1.jsonl`) | — | — | — | — | — | 68 |
| R30-C1 | `sw_n1.jsonl` (= `sw_n1_0/1.jsonl`) | 97 | 0 | **0** | 1 | 0 | 68 |
| R30-C1+C2 | `sw_c12.jsonl` (= `sw_c12_0/1.jsonl`) | 97 | 0 | **0** | 1 | 0 | 68 |
| C1 variant w/ raw last-instruction | `sw_c3.jsonl`, tally `ab_sweep_c3.txt` | 97 | 0 | 0 | 1 | 0 | 68 |
| R30-C2 alone | (targets only) `n2.jsonl` | 1 | 0 | 0 | 1 | 0 | — |
| first draft (emission-side claim narrowing) | `candc.jsonl` | 2 | 0 | 0 | 0 | 0 | — |

The single MOVED file in every arm is `default_event_source.pyc`, and it moved *only* in the
direction of the truth (491→508 of 510; true_diffs 157→31 with C2). 96/96 anchors and 38/38
repro-battery files are byte-identical; `matcher.pyc` is byte-identical on every arm. Zero
errors, no crash, no timeout on any of the 98×3 runs.

## 6. Synthetic repro

Compiled with the shipping interpreter (Python 3.11.7, `py_compile`) and **measured**:

* `repro30/r30c_w2.py` → `r30c_w2.pyc` — **witness battery, 5 shapes, 3 of which reproduce
  R30-C1's defect on the landed core** (`w_a_true_break_epilogue` 27/21, 
  `w_b_true_break_yield_epilogue` 23/19, `w_e_deep` 30/26; 3/6 functions matched) and **all
  three go to 0 mismatches (6/6) under R30-C1**. Product hash
  `d17b0ae28839af5e` → `82e204835d56eeed` (identical for `n1` and `c12`). The essential shape:
  an enclosing for-loop whose body ends with statements *after* a nested `while True:` that
  breaks — the block carrying those trailing statements ends in a backward jump to the for
  header and is simultaneously the inner loop's break exit. (My first attempt,
  `repro30/r30c_shapes.pyc`, reproduces a related shape but its two arms were measured against
  two different compilations of it, so its numbers are not comparable; `r30c_w2` supersedes it.)
* `repro30/r30c_witness.py` → `r30c_witness.pyc` — **CONTROL battery, 4 shapes** + module:
  `control_continue_target_self` (inner loop's own back edge: terminal jumps to *this* header),
  `control_break_forward` (a real break: terminal is a forward jump),
  `control_nested_for_break` (break out of a for nested in a for),
  `control_while_true_break` (while True whose body breaks with no region-exit block after it).
  All clean on the landed core (6/6) and **byte-identical products on `n1` and `c12`**
  (`ef52a76276145780`) — i.e. the predicate provably does not touch any of the four adjacent
  structural neighbourhoods.
* `w_c_for_break_yield` and `w_d_try_inside` were also expected to be defect witnesses on the
  landed core but measured clean (they matched 6/6→6/6): the for-in-for and try-wrapped variants
  do **not** reproduce the claim, so "any block after a nested loop" is too weak a rule of
  thumb; the backward-jump terminal is what matters. (compiled-and-measured, negative result)
* Inferred, not compiled: that `IQEngine`'s `events` tick branch is *only* the `while True:`
  variant of `w_a` plus the elif-chain context — the elif-chain part is measured separately in
  §3c/§7 and is not in the witness.

## 7. Measured vs inferred; rejected clusters

**Measured (byte-level, on landed 06f0ba50, reproducible from this directory):**
both target readings and their strict counterparts; the 4/3/2-hunk alignments
(`fd_events.txt`, `fd_match.txt`, `fd_c3_events.txt`, `fd_c12_events.txt`); the ownership of
@3214 (`[P0]`, `[Q] L4216/L6469/L20469`); the defer/tail-append path of @2378 (`[H2][H3][H5][H6]`);
G3=0; the rotation of `match` (`perm30.py`, `cov30.py`); every number in §4/§5/§6.

**Inferred (state as such):**
(a) that `_register_prefix_emitted` (`region_ast_generator.py:46425`, Round-15 A2 registry) is
not involved — stamp P1 produced 0 lines and I did **not** prove the stamp live on a positive
control, so "0 hits" is not proof of absence; (b) that the missing 2 instructions in the C1+C2
residual are the inner `while True:` body's exit pair and not a further ownership bug; (c) that
`match`'s fix belongs to the if-arm attribution layer (strong inference from the `[Q]` stacks,
not a patch attempt); (d) the exact source-level form of the original tick branch.

**Rejected clusters — do not pick these for these two targets, because:**
1. *"events/match belong to Round 29's cluster A (arm double-claim), fixable from
   `region_analyzer.py:17890-17893`."* False. @3214 is in **no** `then_blocks`/`else_blocks`
   list (measured `[P0]`), and R29-A as landed provably changed neither target
   (`landed.jsonl` == pre-R29-A readings; `stamp` G4 SAME=401/IMPROVED=1).
2. *"match's 281-instruction region is deferred to the function tail and rotated, so the fix is
   a tail-placement predicate."* The 281-run *is* present in the product (`cov30.py`: only 28
   tokens of the whole function are genuinely absent); the greedy prefix classifier's
   `MOVED n=65/281` is an artefact of rotation, not a loss. No deferral path fires
   (`[H3]/[H4]` = 0 hits, `leftovers=[]`).
3. *"the orphan release at `region_ast_generator.py:1502-1548` (top-level `_basic_region`
   append) is the mechanism."* Stamp G3 fired 0 times on both targets.
4. *"narrow the Round-08 hand-over marking at `:6468` to renderable role sets (plus the
   descendant-skip guard at `:6474-6502`)"* — my first R30-C draft. Measured dead:
   `candc.jsonl` SAME=2, no change on either target, because the same block is claimed by
   `_generate_loop:4216` and `_process_if_blocks:20469` regardless. Emission-side claim
   narrowing cannot win where there are three claimers; the analyzer-side single claim can.
5. *"the ordering fix alone (C2) is worth a gate slot."* Count-neutral by measurement
   (491→491); it can only be shipped with C1.
6. *"events is a −19 block-loss family member (Round 24 line D)."* It is two mechanisms
   (17 lost + 15 mis-rotated) plus a 2-instruction third shape; no single block-loss predicate
   covers it.
7. *"fix the last −2 with an extra jump emission."* Not attempted, and I warn against it: the
   pair `JUMP_FORWARD exit / JUMP_BACKWARD header` is what CPython leaves behind at the end of a
   `while True:` body whose last statement breaks; if the original's dead back edge cannot be
   regenerated from *any* faithful source, then `events` has a −2 floor and chasing it is a
   dead end. That question needs its own round (R30-D), not a shipping-gate slot here.
