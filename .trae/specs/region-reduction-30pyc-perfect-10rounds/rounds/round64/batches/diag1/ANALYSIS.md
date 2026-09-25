# Round 64 · batch diag1 · ANALYSIS

Scope: the four `my4.txt` targets, measured with the official matcher only.
Rules are stated in the project's mandatory three-element form
(识别条件 / 归约方式 / AST 映射), 识别条件 restricted to pure structural predicates.

---

## A. `quote_handler.pyc :: get_kline_binary [129, 128, 3, 58]` — **CLOSED** (Job 2)

### A.1 original statements (bytecode evidence, `logs/disf_kbin.txt`)

```
   0 LOAD_FAST typet / 4 LOAD_CONST 6 / 6 COMPARE_OP == / 12 POP_JUMP_IF_FALSE ->24
  14..20 columns = ['open',...,'unlimited']        (11 names)     -> 22 JUMP_FORWARD 32
  24..30 columns = ['open',...,'is_open']          (7 names)
  32..72 stocks = stock.split('.')
  74..120  if stocks[1]=='SS': stock = stocks[0]+'.XSHG'   (120 JUMP_FORWARD 168)
 122..166  elif stocks[1]=='SZ': stock = stocks[0]+'.XSHE'
 168 NOP
 170..256  try:  kline_loader = PyKLine() ; data = kline_loader.query(stock,start,end,typet,BinaryDIR)
 258 LOAD_FAST data / 260 POP_JUMP_FORWARD_IF_NONE ->346         \  operand 1 of the test
 262 LOAD_FAST data / 264 LOAD_ATTR empty / 274 POP_JUMP_IF_TRUE ->346 /  operand 2 (negative)
 276 LOAD_FAST typet / 278 LOAD_CONST 6 / 280 COMPARE_OP == / 286 POP_JUMP_IF_FALSE ->310
                                                                ^ NESTED `if c == 6`
 288..306 default_dataframe = data[[11 m_ names]] / 308 JUMP_FORWARD 330
 310..328 default_dataframe = data[[7 m_ names]]
 330..344 default_dataframe.columns = columns      / 344 JUMP_FORWARD 426 (end of try)
 346..424 else: default_dataframe = pandas.DataFrame(columns=…, index=DatetimeIndex([])) / 426 JUMP 618
 428..616 except BaseException as e: system_log.error(get_traceback_message(e));
            default_dataframe = pandas.DataFrame(...)
 618 LOAD_FAST default_dataframe / 620 RETURN_VALUE
```

The true source is `if data is not None and not data.empty:` whose then-branch is itself
`if typet == 6 / else / default_dataframe.columns = columns`, whose else is the
`pandas.DataFrame(...)` assignment.

### A.2 what landed emits instead (`build_c3/fly__data__quote_handlerOK.py`)

```python
if data is not None and data.empty or typet == 6:      # fused + polarity flipped
    default_dataframe = data[[11 names]]
    default_dataframe.columns = columns
else:
    default_dataframe = pandas.DataFrame(...)
default_dataframe = data[[7 names]]                    # orphaned nested-else statement
```

So the original statements that move are: (i) `not data.empty` loses its `not`;
(ii) the nested `if typet == 6:` disappears as a statement; (iii) `data[[7 m_ names]]`
is hoisted **out after** the whole if/else instead of being its else-branch.
`logs/align_clockworker`-style alignment of this function
(`align.py quote_handler.pyc build_c3/…OK.py get_kline_binary`) reports the missing
`else` as one `delete` of 7 instructions at @308 plus a `replace` at @344/@426 — the
official matcher sees 58 differing positions and 3 jump-target diffs because everything
after the fusion shifts.

### A.3 the ONE blocking site

`core/cfg/region_analyzer.py`, `RegionAnalyzer._detect_boolop_conditional_chain`,
**landed line 25558** (`if len(chain) >= 2:` — the extension-consistency guard, CRLF copy).

`logs/trace_kbin.txt` + `probe_chain.py` output:

```
CHAIN [170, 262, 276] ops=['or', 'or', 'and']
   blk@170  POP_JUMP_FORWARD_IF_NONE  jt=346  succs=[262,346]
   blk@262  POP_JUMP_FORWARD_IF_TRUE  jt=346  succs=[276,346]
   blk@276  POP_JUMP_FORWARD_IF_FALSE jt=310  succs=[288,310]      <- nested if condition
   -> BoolOpRegion merge=310 blocks=[262,276,170]
IfRegion entry=170 blocks=[288,330,170,346] merge=426 then=[288,330] else=[346]
```

The exact conjunct that fails is in the guard at 25562:

```python
if op_type == prev_op and first_jump_target and cur_jump_target and first_jump_target != cur_jump_target:
```

`op_type` (=the run started by 276, `'and'`) is compared with `prev_op` (=262's op, `'or'`).
They differ, so the whole exit-consistency test — including the R53-A same-run fallback at
25658-25673 — is **short-circuited and never evaluated**. Block 276 is appended, the chain
no longer has a uniform target, and the W14 "same-target ⇒ normalise to `and`" pass at
25742 is also disabled, which is why the negative operand 262 is emitted un-negated.
Note the pre-existing `else`-branch of this guard is precisely `_is_valid_2elem_mixed_chain`
territory, but that helper returns early for `len(chain) != 2`.

### A.4 mechanism, in one sentence

The `and` run `170 ∧ ¬262` is *closed* (both operands short-circuit to the same else block
346), and the chain walker keeps walking the fall-through edge of the last operand into the
then-branch, where the first statement happens to be another conditional block; the only
guard that could stop it is gated on "same operator as the previous operand", which is false
exactly when the swallowed block *starts a new operator run*.

### A.5 candidate + measurement

`specs/cand_r64d1b_kbin.json` (1 edit on `core/cfg/region_analyzer.py`, anchor = the two
lines `if len(chain) >= 2:` + `first_jump_target = …chain[0][0]…`, unique, +35 lines).
Measured as **c3k = c3 + this edit**: `quote_handler.pyc 56/57 -> 57/57` (file fully OK),
my4 `242 -> 243`, battery `36/48` unchanged, canary `204/204` unchanged,
`REGRESSION=0 MOVED=0` on all three lists. Repro
`test_repros/round64_diag1/r64d1b_closed_exit_prefix.pyc`: `kbin_repro [34,29,3,15]` on
landed **and** on c3, `2/2` on c3k.

### A.6 rule, three elements

**识别条件 (pure structural).** At BoolOp-chain extension time, with `chain` already
containing `current`: (1) `len(chain) >= 3`; (2) every member of the accepted *prefix*
`chain[:-1]` ends in a conditional jump whose target resolves (via
`cfg.get_block_by_offset`) to one and the same block `T` — the run is *closed* on a shared
exit; (3) `T is not current`; (4) `current`'s own jump-target block is not `T` **and**
`current`'s fall-through successor is not `T`. No offsets, no block counts, no instruction
thresholds, no function/file names, no opcode literals beyond what the existing walk already
uses; nothing is read from `self` except the CFG accessor `self.cfg.get_block_by_offset`.

**归约方式.** Pop `current` from the chain and stop walking: the closed prefix reduces as
the complete BoolOp test (which the existing W14 pass then normalises to a uniform-`and`
run and restores the negative operand's polarity from the jump direction), and `current`
stays unclaimed so the parent `IfRegion` picks it up as the first statement of its
then-branch — region-reduction principle 2 (one owner per block at this level) and
principle 3 (a nested `if` is an abstract node, never an operand).

**AST 映射.** `ast.If(test=ast.BoolOp(op=And, values=[…, ast.UnaryOp(Not, …)]), body=[
ast.If(test=…, body=[…], orelse=[…]), …], orelse=[…])` — i.e. `if A and not B:`
containing `if C: X else: Y`, rather than the fused `if A and B or C:` with a trailing
orphaned `Y`.

### A.7 conservative narrowing, and the shapes checked by hand

`T is not current` deliberately disables the guard for the `elif` entry shape
(`if A and B: … elif C: …`, where the swallowed block's target *is* the next condition
block) so that existing elif/else dispatch is untouched — that path is already handled
elsewhere and this round does not perturb it. Re-checked by construction against:
long `a and b and c` (all targets = `T` → inert), `(a or b) and c` and
`a and (b or c)` (prefix targets differ → inert), Cluster-5 `not (a or b …)` with distinct
trivial exits (prefix not uniform → inert), loop-condition chains via
`skip_claimed_check=True` (prefix targets `loopend` vs `body` → inert).

---

## B. c1 — `quote_handler :: get_kline_local [760, 682, 12, 547]` (previous agent's arm; re-measured only)

Cleared on c1 and on c3 (760 -> 0, file 55 -> 56/57). The five `elif` arms each lost the
statement `end_time = int(end[0:8] + (end[8:12] or '1530'))` and were flattened to a bare
string-constant expression.

**Rule (from `specs/cand_r64b1_sibdispatch.json`, one generator edit):**
*识别条件* — (1) upstream `BoolOpRegion` `U`'s `merge_block` `M` is simultaneously the
`entry` of a downstream region `D` found by `_downstream_region_entry` (which already
requires entry-is-`M`, extension beyond `M`, non-ownership by `block_to_region[M]`, and
not-yet-generated); (2) `D.parent is U.parent` (or both parentless), i.e. **same level,
same parent**.
*归约方式* — `U` dispatches `D` inside the same call: emit `U`'s own `Assign`, then append
`D`'s reduction in source order and register `D`'s member blocks and `D` itself as
generated. The old predicate only yielded when `D.parent is None`, on the theory that a
parented `D` would be dispatched by the parent's `boolop_children` channel; that theory
fails because `_process_if_blocks` skips `M` once `M in generated_blocks`.
*AST 映射* — `U -> ast.Assign(targets=[Name(U.value_target)], value=BoolOp)` followed by
`D`'s product, here `ast.Assign(targets=[Name('end_time')], value=Call(int, …))`.

---

## C. c2 — `trade_live_broker :: fund_transfer [123, 123, 0, 6]` and battery `r63_ft` / `r63_ft2`

Instruction counts already agreed (`123,123` / `65,65` / `109,109`) and only 6 `true_diffs`
moved — the classic **mangled/duplicated f-string family: expression-emission layer, NOT
region ownership**. c2 clears `fund_transfer` (104 -> 105) and both `r63_ft`/`r63_ft2`
battery files (34 -> 36).

**Rule (from `specs/cand_r64b1_fvconv.json`, five generator edits):**
*识别条件* — an instruction with `opname == 'FORMAT_VALUE'` that consumes the result of the
`_idx`-th ternary of an f-string ternary chain; its operand flags carry `flags & 3` =
conversion (0/1/2/3 = none/`!s`/`!r`/`!a`) and `flags & 4` = has-format-spec. If bit 2 is
set the helper returns 0 and behaviour is byte-identical to landed (the surrounding path
does not rebuild `format_spec` yet).
*归约方式* — reserve a per-ternary `FormattedValue` slot dict while walking the chain, then
**back-fill** `conversion` from the consuming `FORMAT_VALUE` instruction found later in the
merge-block / chain-tail instruction stream; the decode table is the same one already used
by the expression reconstructor and `ast_generator_v2` (Round 6-12/13/14) — no new shape
assumption is introduced.
*AST 映射* — `ast.FormattedValue(value=…, conversion=<flags & 3>, format_spec=None)`,
which the code generator's `conv_map` renders as `{x!s}` / `{x!r}` / `{x!a}` / `{x}`.

**Classification note:** every `quote.pyc` defect that is count-neutral with a handful of
`true_diffs` (`load_bars_from_hundsun [477,470,0,464]` etc.) belongs to this same
expression-emission family. It is recorded as classified-and-stopped; **no same-level
region guard was proposed for it** in this batch.

---

## D. c3 — merged arm (c1 + c2)

`specs/cand_r64b1_both.json` is the 6-edit concatenation in file order
(c1 edit 0, then c2 edits 0-4); `mbuild.py` refuses two specs for one core file, so the
merge is required by the instrument, and it applied cleanly with all 6 anchors unique →
**no collision**. Its rule is exactly "B ∧ C": the two predicates touch disjoint
call sites (`_downstream_region_entry` dispatch vs `_fstring_parts_from_segment` /
f-string ternary assembly) and no edit's anchor falls inside another edit's replacement.
Measured additive on every list: 242/269 with both improvements retained, battery 36/48,
canary 204/204.

## D.1 Forbidden-shape audit of the three rules

Scanned all `repl` code lines (comments excluded) of c1, c2 and c3k's kbin edit:

* `region.entry in r.blocks` / any cross-region or cross-level containment: **absent**.
  c1 uses parent *identity* between two siblings (`_downstream_r35.parent is region.parent`)
  — same-level, not containment. kbin compares blocks inside one chain plus their CFG
  successors — same chain, one level.
* `self.*` used as frame state: **absent** — zero occurrences of `self._x = …` in all three
  specs. c2 calls `self._r64b1_fv_conversion(fv_instr)`, a pure helper taking its state as
  an argument; kbin calls `self.cfg.get_block_by_offset`, an idempotent CFG lookup.
* offsets / function names / file names / magic thresholds in any 识别条件: **absent**.
  The only literals are the existing f-string flag bit masks (`& 3`, `& 4`), which are
  instruction semantics, and `len(chain) >= 3`, which is "the prefix has at least two
  accepted operands" — a structural arity fact, not a tuned threshold.
* One genuine risk worth flagging for the round: **c1's `region.parent is None` disjunct
  makes the sibling-dispatch path fire for top-level regions too**. It is corpus-neutral on
  my4/battery/canary, but it is the broadest of the three predicates.

---

## E. `realtime_event_source :: clock_worker [1275, 1286, 10, 481]` — **NOT closed** (Job 3)

Banked from Rounds 22/23 and re-confirmed: R23-A/R23-B restored the dropped
`dt = datetime.datetime.now()`; the function is now an **overshoot**, not a loss.
This arm is byte-identical on landed, c1, c2, c3 and c3k (`SAME` in every A/B), i.e. none
of this batch's rules touch it — no attempt was made to force an edit.

New evidence gathered this session (`logs/align_clockworker.txt`,
`align.py realtime_event_source.pyc build_c3k/…realtime_event_sourceOK.py clock_worker`,
raw non-CACHE sequences 1442 orig vs 1458 decomp):

* The dominant single edit in the alignment is
  `insert orig[1192:1192]@- decomp[1170:1280]@7796` — a **110-instruction insertion**, and it
  begins with `EXTENDED_ARG; JUMP_FORWARD to 8402` followed by a whole
  `check_trading_time(am_open, am_close, pm_open, pm_close, pm_over,
  self._engine.config.strategy.frequency, now_time)` test plus its
  `check_handle_date(now_date)` / `set_current_stage(EventEnum.HANDLE_DATA)` /
  `event_queue.put((dt, EventEnum.HANDLE_DATA))` body.
* The original code object contains that call site **exactly once**
  (`check_trading_time` at offset 8594, `check_handle_date` at 8668), while the decompiled
  source contains **two** `elif check_trading_time(...)` arms —
  `build_c3k/…realtime_event_sourceOK.py` lines **275 and 312**. So this is a
  **duplicated elif-arm emission**, not merely the "+16 D2 over-emission" recorded in R23.
* A second, opposite-signed block exists: `delete orig[959:976]@6690` (17 instructions
  present in the original, absent from the decomp) around the
  `if now_date > self.before_trading_date:` region — the R23-D3 transposition area.
  Net official delta is therefore small (+11) while the raw structure is +110 / −~100:
  **do not read the sign of `decomp_count - orig_count` as "over-emission" here**; track
  Σ|orig−decomp| per file, as banked.
* Conclusion for the next round: the owning layer is the elif-chain dispatch in
  `_if_generate_normal` / the R61 elif channel (one chain arm reduced twice — once in the
  preceding arm's `orelse`, once in its own right), and it should be diagnosed as a
  **duplicate-emission** problem with an entry-ownership probe, not as a missing-statement
  problem. No candidate spec is offered this round.

---

## F. Tally of Σ|orig − decomp| on landed (deficit depth, per file)

| file | functions defective | Σ|orig−decomp| | Σ jump_diffs | Σ true_diffs |
|---|---|---|---|---|
| trade_live_broker | 15 | 145 | 69 | 2012 |
| fly/data/quote | 11 | 197 | 14 | 2636 |
| quote_handler | 2 | 79 | 15 | 605 |
| realtime_event_source | 1 | 11 | 10 | 481 |

After c3k (`dump/c3k.jsonl`): quote_handler drops out entirely (0 / 0 / 0 / 0),
trade 14 defective (145 / 69 / **2006** — only `true_diffs` moved, `fund_transfer`'s 6),
quote unchanged (197 / 14 / 2636), realtime_event_source unchanged (11 / 10 / 481).
