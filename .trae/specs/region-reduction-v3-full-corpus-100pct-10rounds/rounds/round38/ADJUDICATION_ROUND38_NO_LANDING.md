# Round 38 — no landing: the three r63a/r65a candidates measured and banked

Sealed corpus state is unchanged from gate 37: **6613/6617 units (99.9395%), 400/402 files**, residual
2 files / 4 units (`rounds/round37/RESIDUAL_ROUND37.md`). Repo `core/` and `site-packages/` are
byte-clean (`git status --porcelain -- core/ site-packages/` = 0 lines; generator `20fa73b4e8231f0f`,
analyzer `c069d359cbfe76b0` in both the repo and the mirror `D:/Temp/r30chk`, `cmp`-proved). No gate
was run this round because nothing was installed — a zero-flip candidate does not consume a gate
label (rule since gate 36).

## 1. R21-38 clock_worker — [R21-24-M1] re-anchored + P1 + P2 : measured partial, banked

`CANDIDATE_r38_P1P2_onto_landed_BANKED_not_landed.py` = sha16 **c4a934d595200c84**
(= landed `20fa73b4e8231f0f` + M1 hunk re-anchored onto it + P1 dominance arm choice + P2
`_r63a_break_landing_is_inner_flow` at its four sites). Built by
`build_p2_onto_landed.py` (hunk-by-hunk transplant of P2 from r63a's `90fb8ccce90da574`, each NEW
block verified present verbatim, `py_compile` OK); M1+P1 came from r63a's own
`DELIVER/CANDIDATE_onto_landed.py` (`258c7d714f4b80e3`).

| measurement | landed bytes | this candidate |
|---|---|---|
| `clock_worker` instructions | orig 1424 / prod 1311, **delta −113, hunks 7** | orig 1424 / prod 1418, **delta −6, hunks 5** |
| `realtime_event_source.pyc` | 12/13 | 12/13 (no flip) |
| panel (20 files, tag `r38r`) | — | **19 byte-identical (SAME), 1 CHANGED, 0 files decreased, 0 flips** |

Fires without flips ⇒ per the standing rule it is banked, not installed. The panel is the
important part: P1+P2 is the first clock_worker candidate in this campaign that changes exactly one
file corpus-wide among the 20 probes (including the six duplicated-module canaries `arg_checker`×3 =
49/39/43 and `profiler_func`×3 = 17/15/18, all SAME).

### The −6 residual is two named losses (allwin_r63.py, no small-window filter)

```
#1 insert orig[904..904 @6496] prod[904..905]          del=0 ins=1   (+JUMP_FORWARD)
#2 delete orig[963..966 @6778..@6782]                  del=3 ins=0   self.before_trading_date = now_date
#3 insert orig[1046..1046 @7248] prod[1044..1045]      del=0 ins=1   (+JUMP_FORWARD)
#4 delete orig[1051..1057 @7270..@7308]                del=6 ins=0   system_log.debug('获取重登信号量')
#5 replace orig[1393..1395 @9210] prod[1386..1389]     del=2 ins=3   same statement re-paired at the loop tail
```

* **(A) window #4** — the debug statement lives at the head of the 17-instruction block
  `@7270..@7370`, which the landed analyzer declares as an IfRegion **condition** block
  (`IfRegion condition_block=@7270..@7370(17) then=[7372,7488] else=[7492] merge=@7582..@7602`,
  census_clock_r63.py on landed bytes). CPython fused `system_log.debug(...)` and the following test
  into one maximal straight-line block; the whole block is registered as generated while its six
  leading instructions are emitted by nobody. `_split_block_condition_prefix` has only three
  consumers today (AssertRegion :643, LoopRegion R23-B :7654, ternary :43118/:43533/:43599) —
  **the IfRegion path has none**. The landed `guard_clause_prefix_end` exception does not apply: it
  is written by the analyzer only when a BoolOpRegion owns the block, and this test is
  `login_semaphore.acquire(...) is False` (a plain Compare).
* **(B) windows #2 + #5** — `self.before_trading_date = now_date` (@6778..@6782) is the **merge
  block** of `IfRegion condition_block=@6690..@6700(4) then=[6702] else=[] merge=@6778..@6782(3)`.
  It is emitted once, but in the loop's post-exit sequence (product `@9170`, after the
  `while self.active` test) instead of at the region's join. #1/#3 are the two `JUMP_FORWARD`s that
  `pass`-rendered empty arms cost; both disappear if #2/#4 close.

## 2. R21-38d IfRegion condition-prefix (fix for (A)) : two arms, both rejected as delivered

`build_cand_r38_R21-38d_if_cond_prefix.py` installs the helper `_r38_if_cond_prefix_stmts`
(existing cutter + existing `prefix_emitted_upto` ledger, no new predicate) plus two dispatch hooks.

| arm | sha16 | product size | units | verdict |
|---|---|---|---|---|
| both hooks | `50397af2773eb726` | 23980 (+1658) | **11/13** | regresses a previously green unit |
| hook A only (dispatcher `:4423`) | `e1a984048121243b` | 23980 (+1658) | **11/13** | same regression — the over-fire is entirely hook A |
| hook B only (arm renderer `:28864`) | `7135610877add4f1` | 22322 (= P1+P2) | 12/13 | **inert**: `clock_worker` shape byte-for-byte the same 5 windows |

So the dual-role block @7270 is **not** reached by either hook as installed: hook B never fires for
it, and hook A fires broadly elsewhere (prefixes that other paths already emit → double emission,
+1658 bytes, one unit lost). The axis is not closed; it needs the *dispatch census* first — which
method actually renders `IfRegion@7270` — before a fourth consumer can be placed. Ablation/print
markers are the tools that worked for the R21-27 f-string chain (`ablate-builders-to-locate-emission-site`);
a line-based marker search will miss multi-line dict literals again.

## 3. R21-39 `_sync_worker` (r65a) : analyzer-side, delivered as a measured negative

`rounds/round37/FIX_R21-39_r65a.md` + battery row `G_or_headed_and_tailled_while_condition`
(`D:/Temp/r65/DELIVER/G_shape_r65_battery_row.py`). Numbers r65a established on the landed bytes:
broker holds **125/128** and `_sync_worker` **delta −3 / hunks 5**; the target is a compound while
condition `while A or B or (C and D): time.sleep(60)` whose flat `compile()` shape reproduces the
original jump pattern one-to-one, while the product's nested-while form does not; `sys.settrace`
intersect records **zero hits** at the landed fast loop `region_ast_generator.py:13440-13442` for
this unit, so the assigned polarity mechanism is the wrong route; the break point is
`region_analyzer.py:28058-28060` (the OR operand was pre-claimed as a nested LoopRegion and
`interrupts_boolop_forward_chain` refuses absorption) plus `:27181-27192` (length-1 chain dropped)
and the flat `all_same_target` check `:28092-28103`, which cannot express `or … or (C and D)` —
the same structural reason the landed `[R7-B45]` `(and or)` sibling exists. **Population was not
counted**; r65a installed nothing, which is the correct outcome under the fires-without-flips rule.
This is a cross-layer analyzer ticket (detection + ownership + a nested BoolOp rebuild the flat
`_build_boolop_expression` :39815 does not support) and its regression face is every
`while X or Y` unit in the corpus.

## 4. Consequence for the next round

Neither remaining unit count moves without **two** independent closures on clock_worker (A)+(B), and
`_sync_worker` needs a rebuild the generator cannot express. The dispatchable next units of work,
each with the measurement that defines it:

1. **Dispatch census for `IfRegion@7270`** (ablate the candidate builders; the answer decides where
   the fourth consumer of `_split_block_condition_prefix` belongs). Acceptance: a census that names
   the method emitting this region's test, plus the hook that is provably not reached.
2. **(B) merge-block statements** — the criterion is that a region's `merge_block` carrying
   non-noise instructions must emit them at the join, not in a later suite; measure the population
   of merge-blocks-with-statements corpus-wide before writing it (`@6778..@6782` is one instance).
3. **`_process_order` (−68/14) and `_process_cancel_order` (−1/3)** — `rounds/round37`
   `TICKET_R21-37`/`FIX_R21-35a_r37` remain open with banked halves
   (`CANDIDATE_r64a_R21-37_ternary_join_BANKED_not_landed.py`,
   `CANDIDATE_r37_R21-35a_trybody_continue_BANKED_not_landed.py`); neither flips alone (measured
   −42/11 and −2/2 respectively).
