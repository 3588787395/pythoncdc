# FIX_R21-92 - clock_worker's last unit: THREE region-data arms (D1 nest, D2 chained-compare fold, D3 no while/else return)

Engineer: r118a. Base: analyzer `996a1b1acf143458` + generator `558192ecf6d5f8a0`
(`[R21-90]`, banked, NOT installed). Mirror `D:/Temp/r118`, built as a copy of `D:/Temp/r117`.
Repo read-only throughout; no gate, no install, no `*OK.py` edits.

## 0. Mirror certification

| file | sha16 |
|---|---|
| `D:/Temp/r118/core/cfg/region_analyzer.py` | `996a1b1acf143458` (= `r116/backup/ana_F5_996a1b1acf143458.py`) |
| `D:/Temp/r118/core/cfg/region_ast_generator.py` | `558192ecf6d5f8a0` (= `r116/DELIVER/CANDIDATE_r2190_558192ecf6d5f8a0.py`) |

`r117` was verified byte-identical to the certified base before copying.

Base product reproduced byte-exact TWICE with the mirror pipeline:
`out/rt_base1.py` and `out/rt_base2.py`, both sha16 **`d622eb7060a3096b`** (364 lines, 21069 bytes).

## 1. Premise check - REQUIRED base reading reproduced exactly

`oracle_diff_r104.py out/rt_base1.py`:

```
[oracle-diff] unit=clock_worker ours=257 ORACLE=254 hunks_vs_ORACLE=8
[census] DELTAS     instrs=-2 back=+0 jsites=+0
[census] indeg-equal=False back-equal=True opseq-equal=False
[judge] ***<module>.RealtimeEventSource.clock_worker: Failure: Different control flow
[judge] [single] status=failure units=12/13
```

`block_diff_r118.py out/rt_base1.py`:

```
blocks orig=176 prod=175 instrs orig=1442 prod=1440
SIG-ONLY-ORIG=4 SIG-ONLY-PROD=3
```

Both match the brief verbatim -> proceed (no stop condition).

## 2. ARGUMENT-aware instrument (built here; the shipped one was a stale copy)

`D:/Temp/r118/instr/bcore_arg_r119.py` in `D:/Temp/mon` is **byte-identical** to
`bcore_r118.py` (`diff` empty) - the argument-aware change was never actually applied to it,
so `gold_map_arg_r119.py` silently ran the opname-only splitter. I built the real variant as
`D:/Temp/r118/instr/argdiff_r118a.py`: same partition/edge logic, signature
`i.opname + "#" + str(i.argval)[:30]` for `LOAD_* / STORE_* / COMPARE_OP / IMPORT_* / BINARY_OP`
and bare `opname` otherwise, and it now prints in/out degree per row (addendum 5's demand
that content and degree be compared together).

Controls (all reproduced the ticket's rows verbatim):

| input | instrs | blocks (certified splitter) | GOLD-only | PROD-only |
|---|---|---|---|---|
| `GOLD_realtime_event_source_PROOF.py` vs itself | 1442/1442 | 176/176 | **0** | **0** |
| base product `[R21-90]` | 1442/1440 | 176/175 | **4** | **3** |

Block-count convention note: the ticket quotes `blocks 170/169` for the arg-aware proxy. The
certified `bcore_r118.blocks` splitter (the one `block_diff_r118.py`/`gold_map_r119.py` are
calibrated on, and which reproduces the ORIGINAL pyc element-for-element at 176 blocks) returns
176 for GOLD. I checked the two do not differ in kind, only in how the tail of an unconditional
jump is partitioned (a no-split-after-jump variant gives 172/171 on the same pair). The proxy
bar is **convention-independent**: `GOLD-only=0 PROD-only=0` means the two signature MULTISETS
are equal, which forces equal block counts and equal instruction counts under any fixed
splitter. I therefore report 0/0 together with the hard opname bar
(`SIG-ONLY 0/0`, `blocks 176/176`, `instrs 1442`), and never accept a smaller |instrs|.

## 3. The three sites, read off the ORIGINAL pyc (ground truth, reprinted not re-derived)

Block successors in the D1 window (analyzer data, `rig/regdump_r118a.py 6280 6800`):

```
@6548 succ=[6580, 6792, 9218]   preds=[6496, 6544, 6546]     <- outer if, merge=6792
@6690 succ=[6702, 6778, 9218]   preds=[6652, 6678]           <- holiday guard, merge=6778
@6702 succ=[6778, 9218]         preds=[6690]                 <- put(...) FALLS THROUGH to 6778
@6778 succ=[6792, 9218]         preds=[6690, 6702]           <- assign, FALLS THROUGH to 6792
@6792 succ=[5598, 9218]         preds=[6548, 6778]           <- sleep+continue, merge of @6548
```

so `assign@6778` is the merge of an if-without-else and `sleep@6792` is the merge of the
ENCLOSING if-without-else. Two distinct merges. The product renders ONE fused block
(`@6778+@6792`, 11 instructions) because it emits the holiday guard dedented one level -
out of `@6548`'s then suite - so the outer merge and the inner merge become the same text
position. **The else-body reading stays CLOSED-FALSE** (it adds a `JUMP_FORWARD` the original
lacks; confirmed independently by r117a probe B: `jsites +1`, SIG-ONLY 3/3).

## 4. Shape proof BEFORE any pipeline edit (scratch mutations, never installable)

`rig/mutshapes_r118a.py` applies the three shapes textually to a scratch copy of the base
product; scored by `instr/argdiff_r118a.py` and `instr/block_diff_r118.py`:

| shape | argdiff instrs | blocks | GOLD-only | PROD-only | opname SIG-ONLY O/P |
|---|---|---|---|---|---|
| base | 1442/1440 | 176/175 | 4 | 3 | 4 / 3 |
| D1 nest alone | 1442/1440 | 176/176 | 2 | 2 | (r117a probe A: 2/2) |
| D2 flat alone | 1442/1440 | 176/174 | 3 | 1 | - |
| D3 drop alone | 1442/1442 | 176/176 | 3 | 3 | - |
| D1+D2 | 1442/1440 | 176/175 | 1 | 0 | - |
| D1+D3 | 1442/1442 | 176/177 | 1 | 2 | - |
| D2+D3 | 1442/1442 | 176/175 | 2 | 1 | - |
| **D1+D2+D3** | **1442/1442** | **176/176** | **0** | **0** | **0 / 0** |

and the judge on the D1+D2+D3 scratch shape:

```
[single] 产物 D:/Temp/r118/mut/mut_D1_D2_D3.py
[single] status=success units=13/13 success_rate=100.00%
```

Conclusion: the three arms are individually necessary and jointly sufficient at the shape level.
The task is now purely to make the pipeline EMIT that shape from region data.

## 5. Arms to implement

* **D1 (nest / ancestor ownership)** - `@6690` and its merge `@6778` must be rendered INSIDE
  `IfRegion@6548`'s then suite, so `@6778` and `@6792` stay two blocks. Criterion must read
  region/block relations only (no names, no offsets as keys, no counters/thresholds).
* **D2 (chained-compare conjunct fold)** - the elif arm whose body is a single chained
  comparison test must fold that conjunct into the owning `elif` test at identification time.
  Population law already measured: 171 `elif`+nested-`if` sites in 51 products, of which
  exactly 1 has a chained-compare nested test. CFG-visible only because the chain carries an
  `else:` arm.
* **D3 (no while/else for the function-ending return)** - a `while` whose `else` clause body is
  only the function-ending `return None` must not be emitted; the loop falls through to the
  implicit return.

Status: implementation in progress; measurements appended below.

## 6. What each arm actually is (measured on my own bytes, before writing)

### D1 is an arm-window UNDER-DECLARATION inside an already-firing `[R21-88]` fold

The fold `region_ast_generator.py:_r2188_and_prefix_or_tail` DOES fire at `@6496` on these bytes
(verified by tracing, not assumed): it rebuilds `(A and B) or C`, marks the leg blocks, narrows
`region.then_blocks` and re-declares `region.merge_block`. What it narrows to is
`_arm_blocks = [b for b in region.then_blocks if arm <= b < E]` = `[6580, 6582, 6652]`, because
`IfRegion@6496.then_blocks` was built by the bottom-up reduction before the nested holiday guard
existed in it. The tail leg's OWN region `IfRegion@6548` declares the same statement:

```
IfRegion@6548 cond=6548 merge=6792 then=[6580, 6582, 6652, 6690, 6702, 6778] else=[] elifs=[]
IfRegion@6690 cond=6690 merge=6778 then=[6702]  else=[]      <- nested if-without-else
```

`_tr.condition_block is _t`, `_tr.merge_block is _e (6792)`, `6580 in _tr.then_blocks`, `_tr` has
no else and no elif - so two regions own one arm and the deeper declaration is the complete one.
Its `then` run adds `[6690, 6702, 6778]` strictly inside the window `[6580, 6792)`.

Arm: inherit `_tr`'s run for the window only. `6690` is then dispatched by that walk through the
existing `get_entry_region_for_block` nested-region route (`_process_if_blocks` already falls back
to it when `get_region_for_block` returns the enclosing TryExceptRegion - measured: it returns
`TryExceptRegion@6` for 6496/6518/6548/6690/6702/6778/6792 and `TryExceptRegion@6582` for
6580/6652). Nothing is newly claimed, so `@6778` and `@6792` stay two blocks, and the sleep merge
keeps exactly the one jump predecessor the original has - which is why this is the NEST reading
and not the (CLOSED-FALSE) else-body reading, and why `back` stays `+0`.

### D2 is a chained-compare conjunct lifted out of its own elif/if test

`elif now_date == self.before_trading_date and now_date > self.after_trading_date
        and delay_after_trading >= now_time >= after_trading:` compiles to an `and` short-circuit
chain `@8904 -> @8926` whose legs all jump IF_FALSE to the chain continuation `F=9144`, followed
by the chained comparison `@8948` (SWAP/COPY) + `@8964`, whose non-arm exits are
`@8948 -> @8976 -> 9144` (POP_TOP connector) and `@8964 -> 9144` directly, with the arm `@8980`
reached through the pure connector `@8974`. The reduction put that last conjunct in its own
`IfRegion@8948 (entry == condition_block == 8948, cc=[8964], else=[8976, 9144])`, and the renderer
emitted the nested `if`. Same false exit + same arm = same conjunct list, so the fold is a CFG
fact; the enclosing chain's `else:` arm is what makes it visible (addendum 1's measurement), which
is why I kept `F == region.merge_block` in the predicate.

### D3 is a duplicate of the function-ending return being spelled as a while/else

`LoopRegion@5598 else_blocks=[9214]`, `has_trailing_return_none=True`, parent `TryExceptRegion@6`,
and `@9214` = `LOAD_CONST None; RETURN_VALUE`, no successors, its ONLY predecessor is `@5598`.
The loop's other exit already has its own copy: `@9194` (the tail re-test) falls through to
`@9210` = `LOAD_CONST None; RETURN_VALUE`, no successors. So the function's ending return exists
twice, once per loop exit edge - CPython jump-threading, not a source-level `else:`. The shipped
filter that recognizes exactly this (`_other_return_none_blocks > 0` => drop the else, emit no
return) was gated on `region.parent is None`; I widened it with a predicate instead of removing
the gate.

## 7. Why the broad D3 form was rejected before shipping

Dropping `region.parent is None` unconditionally enters **14 sites in 9 panel files** (quotation 2,
quote 2, klinedata 3, handlers 3, trade_info_utils 2, broker 9, matcher 1, risk 5, arg_checker 3/2/3,
profiler_func 1/1/1 - 49 candidate rows counting repeated code objects), and those files are
currently green with `else: return None` in their committed products (trade_info_utils R21-21 is
literally that landed mechanism). The "the body already holds a DIFFERENT block of the same
terminating shape" conjunct reduces it to 1 newly-reachable site corpus-wide.

## 8. Deliverables

```
DELIVER/FIX_R21-92_three_arms.md
DELIVER/MEASURE_R21-92.md
DELIVER/CANDIDATE_r2192_a981db88af309d32.py            (byte-different product ec1b13cb31437222, 13/13)
DELIVER/ABL/ABLATION_r2192_D1.py       318b438f59b68e53
DELIVER/ABL/ABLATION_r2192_D2.py       4c8de5eb1b5edd10
DELIVER/ABL/ABLATION_r2192_D3.py       a6509837ec1b1417
DELIVER/ABL/ABLATION_r2192_D1_D2.py    f4fd4ddb2e48f62f
DELIVER/ABL/ABLATION_r2192_D1_D3.py    d1497feb8734f3fd
DELIVER/ABL/ABLATION_r2192_D2_D3.py    d79dcedd43c758fa
instr/argdiff_r118a.py                 (the ARGUMENT-aware proxy, newly built)
rig/census_r118a.py                    (population census: panel + 402-roster, 3 predicates)
rig/patch_r2192.py                     (BOM/CRLF-safe, arm-selectable, idempotent)
rig/panel20_r118a.py, rig/sweep402_r118a.py, rig/abl_r118a.sh, rig/regdump_r118a.py,
rig/eliftrace_r118a.py, rig/mutshapes_r118a.py
```

Every arm was built and measured separately, so none of the six single/pair variants is a
byte-identical product: all seven rows in MEASURE section 1 carry distinct product sha16s.

## 9. Verdict: LANDED-READY

- Bar 1: arg-aware `GOLD-only=0 PROD-only=0` (blocks 176/176, instrs 1442/1442) and opname
  `SIG-ONLY-ORIG=0 SIG-ONLY-PROD=0`, `blocks 176/176`, `instrs 1442`. `indeg-equal=True`,
  `opseq-equal=True`, `instrs=+0` - parity by identity, not cancellation.
- Bar 2: judge `pyc_verify single --source <fresh product>` -> **units=13/13** (was 12/13).
- Bar 3: 20-file panel - 19 rows keep counts AND `BYTES=SAME`; 402 sweep
  `files_compared=402 MISSING/FAIL=0 CHANGED={realtime_event_source.pyc}` only.
- Census: each arm fires at exactly one actionable site in all 402 files.
- Mirror restored to base hashes and re-proved after delivery (see MEASURE section 7).

Repo was never written, no `*OK.py` touched, `gate_chain.py` not run, nothing installed.
