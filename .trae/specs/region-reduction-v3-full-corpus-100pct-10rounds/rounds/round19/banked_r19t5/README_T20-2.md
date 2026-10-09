# T20-2 — `IQCommon/logger/handlers.pyc :: <module>.TWHThreadController._target` (diagnosis only)

Mirror: `D:/Temp/r19t5/` (copies of `pycdc.py core parsers utils bytecode scripts`). Live repo read-only, never written; no
`sys.settrace`; no probe inside analyzer/generator code — all CFG/region readings come from
separate processes that build their own CFG and call `analyze()` once.
Pristine hashes (re-proved byte-equal after every ablation, see §2 footer):

```
region_ast_generator.py  5066b1367b6de3c703297461319a463f1ad4f126d1a7ca033908b25ede6502eb
region_analyzer.py       640d33a77dcb71c2bb6e86d8a05ca1e355306857045bf3820d3590e9a395a0c6
```

Baseline reproduction from the mirror: `pycdc.py handlers.pyc -o prod_baseline.py` → **byte-identical to
`site-packages/IQCommon/logger/handlersOK.py`** (9093 bytes, sha256 `65badb9485d3b8f3…`), and
`unit_diff … --all` → `len orig=199 prod=197 delta=-2  hunks=1 landings=3` (the ticket's numbers).

## §1 Ownership (built as `pycdc.py --region` builds it: `CFGBuilder().build(_target code)`,
`RegionASTGenerator(cfg, recursive=True, parent_code=TWHThreadController, top_level_code=<module>)`,
one `region_analyzer.analyze()`)

CFG has 44 blocks; the two pairs in question are **two distinct blocks** — this is the decisive fact:

| offset range | instructions | pred set (normal + exc) | succ set | owner region | role (`get_block_role`) | role in region |
|---|---|---|---|---|---|---|
| `@90..@102` (holds @102 `POP_JUMP_FORWARD_IF_FALSE -> @408`) | LOAD_FAST self / LOAD_ATTR running / cond-jump | `[@46]` (1) | `[@104, @408]`, exc `[]` | `LoopRegion@90` (WHILE_LOOP) | `LOOP_CONDITION` | `entry` **and** `condition_block`; `else_blocks=[@408]`, `header_block=@104`, `back_edge_block=@390`, `merge_block=None`, `exit=None` |
| `@404..@406` (kept pair) | LOAD_CONST None / RETURN_VALUE | `[@390]` (1; reached by **fall-through** of the back-edge test) | `[]`, exc `[]` | `LoopRegion@90` (member of `region.blocks`; **not** in `body_blocks`, **not** in `else_blocks`) | `IF_THEN` | not any named arm field — only a bare `blocks` member |
| `@408..@410` (lost-by-census pair) | LOAD_CONST None / RETURN_VALUE | `[@90]` (1; reached by the **condition block's false jump** @102) | `[]`, exc `[]` | `LoopRegion@90` | `LOOP_ELSE` | the loop's `else_blocks[0]` |
| `@412..@456` (next statement, src line 75) | sys.version_info test + cond-jump `-> @1012` | `[@0, @46]` (2) | `[@458, @1012]`, exc `[]` | `IfRegion@412` (IF_THEN_ELSE) | `IF_CONDITION` | `entry` + `condition_block`; `then=[458,504,1016,1020,658,1008]`, `else=[1012]` |
| `@390..@402` (tail test) | LOAD_FAST/LOAD_ATTR/`POP_JUMP_BACKWARD_IF_TRUE -> @104` | `[@212, @378]` | `[@104, @404]` | `LoopRegion@90` | `LOOP_BACK_EDGE` | `back_edge_block` |

Region chain of all three of @90/@404/@408: `LoopRegion@90(WHILE_LOOP) <- IfRegion@0(IF_THEN,
condition_block=@46, then_blocks=[@90,@408,@404], merge_block=@412)`. So **both** pure-return exits are
members of the loop region, both are also in the outer if's `then_blocks`, and their predecessor sets are
asymmetric exactly as §1b of `MEASURED_R19_3` said (@404 only by fall-through, @408 only by one jump).

**Source lines (new reading):** @390/@402, @404/@406 and @408/@410 are ALL tagged original **line 63**
(the `while` line); @412 is line 75. So neither pair carries the line of a `return` statement — they are
two per-exit-edge materializations of the same epilogue position, one edge = loop-entry test false, the
other edge = back-edge test fall-through. `handlers.pyc` magic `a70d0d0a` == local 3.11.7 magic, so this
is not a foreign-magic artefact.

## §2 Ablation table (each row = one stub applied to the mirror copy, whole file regenerated,
`unit_diff` on the ticket qualname, then restore in `finally`)

| stub (site) | hunks | landings | prod len / pair idx | product bytes vs landed |
|---|---|---|---|---|
| none (baseline) | 1 | 3 | 197 / [73,121,189,191,193,195] | 0 |
| `_is_return_none_join_block` → `return True` (def :3096, **3 call sites** :1821 / :28713 / :51920) | 1 | 3 | 197 / same | 0 |
| `_is_return_none_join_block` → `return False` | 1 | 3 | 197 / same | 0 |
| `_mark_shared_return_explicit` → no-op (def :51718) | 1 | 3 | 197 / same | 0 |
| `_r8_b121_scope_return_sink_kind` → `return None` (def :51758) | 1 | 3 | 197 / same | 0 |
| `[R5-B119 loopsink]` funnel guard off — `region_ast_generator.py:52045` | 1 | **0** | 197 / same | −40 |
| same via analyzer side — `region_analyzer._loop_tail_exit_sink_pair` (:28390) → `return set()` | 1 | **0** | 197 / same | −40 |
| loop member-claim sweep `:5371-5378` (`[r11-b159-fact]`) no-claim | 1 | 3 | 197 / same | 0 |
| both claim sites off (`:5378` **and** `:25300-25302` `[R2-B107]`) | 1 | 3 | 197 / same | 0 |
| both claims + sink guard off | 1 | 0 | 197 / same | −40 |
| `_loop_generate_while` trailing-return block off (`:8016` `has_trailing_return_none` gate) | 1 | 3 | 197 / same | 0 |
| try-body terminating tail off (`:28713` `_is_other_region_merge and …`) | 1 | 3 | 197 / same | 0 |
| while-arm tail stripper off (`:15915 while then_stmts and _is_implicit_return_none(…)`) | 1 | 3 | 197 / same | 0 |
| `_strip_implicit_return_none` (`:21545`, nested) → identity | 1 | 3 | 197 / same | 0 |
| `_nested_merge_return_skip` consumer off (`:25305`) | 1 | 3 | 197 / same | 0 |

The two `pyc_verify single --source` readings of the only moving stubs stay **29/30 (status=failure)** —
`landings 3→0` is a re-alignment of the shadows, not a flip.

Call-site census of the predicates that matter (guard duplication):
`_is_return_none_join_block` = 1 def + 3 consumers; `_loop_tail_exit_sink_pair` = 1 def
(analyzer `:28390`) + **1** consumer (generator `:52045`, the single funnel); `_r8_b121_implicit_tail_landing_sinks`
= 1 def + 1 consumer (`:52057`); blocks @404 is registered as generated by **two** sites (`:5378`, `:25301`).

Direct readings that falsify the ticket's assumed mechanism (`sink_membership.py`, standalone):

```
_loop_tail_exit_sink_pair()            -> {@1016, @1020}     (the SECOND branch's pair, NOT {@404,@408})
_r8_b121_implicit_tail_landing_sinks() -> {}                  (whole-or-nothing gate breaks on G4b)
block @404: in sink_pair=False  in b121_sinks=False  join=False  trailing_return_none=True
   _generate_block_statements(@404) -> [{'type':'Return','_explicit_return':True,'value':Constant None}]
block @408: same set readings; the emitted arm `return None` is produced from **@408**, not @404
```

So (a) the surviving statement in the product (line 40 `return None`) is @408's, (b) the abstract node that
disappears is **@404**, (c) the repository comment at `region_ast_generator.py:5364-5366` ("该块属隐式尾声族：
`_generate_block_statements` 被直接请求时返回空列表 … 改登记/改顺序/改归属都动不了它") is **false for the current
bytes**: the funnel returns a complete `Return` node for @404; the second half of that sentence (claim/order/
ownership edits are byte-inert) is confirmed by the K2/K5 rows.

Text-side control (`shapes_full.py`, surgery on the landed product text, recompiled with the same 3.11.7):

| arm-tail text | len | pairs | head-test @102 lands on |
|---|---|---|---|
| as landed (one `return None`) | 197 | 6 | @404 (the pair) |
| `return None` deleted | 195 | 5 | @404 |
| two / three sequential `return None` | 197 | 6 | @404 (extra copies dropped as dead code) |
| `while …: … else: return None` | 197 | 6 | @404 |
| `else: return None` **and** arm `return None` | 197 | 6 | @404 |
| original pyc | 199 | 7 | @408 (its own copy; @412 follows it) |

Five minimal kernels (`kernels.py`: while+return with plain body / try-except-else body / nested-if body /
no return / while-True+break+return) all show the same thing: CPython 3.11.7 gives the loop's two exit edges
**one shared** epilogue copy; the original's duplicated copy is not reachable by any statement sequence at
that position.

## §3 Criterion (identification side) — and why it cannot be written for this unit as briefed

The briefed axis ("two adjacent pure-return blocks with asymmetric predecessor sets ⇒ keep them as two
abstract nodes") is the *right structural description of the CFG* (§1: preds `[@390 fall-through]` vs
`[@90 jump]`, both terminal, both 2-instruction pure-None, both members of the same `LoopRegion`) — but the
ablation battery shows no emission decision is made on that axis: @404 is not swallowed by any of the
return/sink/claim guards, and when both nodes are handed statements the recompilation still emits one pair.
The asymmetry that the fix would have to exploit is already visible in the region table and needs no new
predicate: the loop's `else_blocks=[@408]` is emitted (as `_sequential_after_loop`, generator `:8241-8247`)
while the sibling post-loop member `@404` is a bare `region.blocks` member with no arm field — the
`_loop_generate_while`/`[r11-b159-fact]` sweep at `:5371-5378` is exactly the "member but never emitted"
hole. The helper whose vocabulary already covers this shape, and which any fix must **reuse rather than
duplicate**, is `RegionAnalyzer._loop_tail_exit_sink_pair` (`region_analyzer.py:28390`, single consumer at
`region_ast_generator.py:52045`) together with its own primitives `_check_block_has_trailing_return_none`
and `block_to_region` membership — never `_is_return_none_join_block` (3 consumers) and never a new
adjacency/predecessor count predicate.

## Verdict

BLOCKED: no emission-side branch in `region_ast_generator.py`/`region_analyzer.py` writes this fold. The
reading I could not obtain is a stub whose removal (or a source shape whose addition) makes the second
`LOAD_CONST None / RETURN_VALUE` pair appear — 15 ablations (all byte-restored) leave `hunks=1`/`len=197`
unchanged, only `[R5-B119 loopsink]` moves bytes at all and it moves the *other* pair (`@1016/@1020`,
`landings 3→0`, still 29/30); and the lost node @404 is *already* emitted correctly when reached
(`_generate_block_statements(@404)` returns a full `Return`), while 0/1/2/3 arm returns, `while…else` and
five minimal kernels all recompile to the shared single epilogue. The −2 is CPython's per-exit-edge
duplication of one epilogue position (both pairs tagged original line 63), which no statement text at that
position reproduces — so the ticket's premise "the two exits were folded by a guard" does not hold, and
`handlers._target` should be booked as a codegen-shape residual, not landed as a fold-prevention fix.

Rigs in `D:/Temp/r19t5/`: `census_handlers.py` (§1), `sink_membership.py`, `ablate_handlers.py` (§2, restores
both mirror files in `finally`), `shapes_full.py` + `kernels.py` (text controls), `lines.py`, `pairs.py`,
`who_registers.py` (recording-set probe, self-certified inert: probed AST == control AST, 11531 bytes each).
