# DIAG B137 — landing-only diff on `strategy.tick_worker_thread`

Status: IN PROGRESS (written incrementally; scratch `D:/Temp/r137/`).
Scope: diagnosis only. No edits under `core/`, no git writes, no 402-file gate.

Target: `site-packages/IQEngine/plugins/plugin_fly_data/strategy/strategy.pyc`
:: `<module>.Strategy.tick_worker_thread` (co_firstlineno 301, co_filename
`./fly_docker_py311/IQEngine/plugins/plugin_fly_data/strategy/strategy.py` — **no `.py`
source exists on disk anywhere in the repo**; only the product `strategyOK.py`, whose line
numbers are offset by −87 from the original's, so statement text below is quoted from the
product and block→line mapping is taken from the ORIGINAL code object's line table).

Live judge (compare-only) at the time of this run:
`python -X utf8 scripts/pyc_verify.py single site-packages/.../strategy.pyc`
⇒ `status=failure units=26/27 success_rate=96.30%`, sole failure line
`***<module>.Strategy.tick_worker_thread: Failure: Different control flow`.
⇒ **the file really is 26/27 and this really is its only failing unit** (brief confirmed).

## 1. Re-measurement of the brief's diff shape (my own instrument)

Instrument: `D:/Temp/r137/hunk137.py` — stdlib `dis` + `difflib`, jumps as `->@offset`,
nested code objects normalised to `<co NAME>`, pairing by FULL walk-path qualname with an
`assert len(cs)==1` copy-uniqueness check (prints `copies 1/1`). CPython here is
`3.11.7 (tags/v3.11.7:fa7a6f2, Dec 4 2023)` and `dis.get_instructions` already excludes
CACHE (verified: `total instr = 294`, `CACHE count = 0`, `NOP = 2`, `EXTENDED_ARG = 4`),
so "CACHE dropped" == the default listing.

Full log: `D:/Temp/r137/diff_cache.txt`.

```
len 294/294 net=+0  hunks=4 same-opcode-target-only=4 content=0 deleted=4 inserted=4
  HUNK 1 replace orig[73:74]=1 prod[73:74]=1   @522  L324  POP_JUMP_FORWARD_IF_TRUE ->@568 | ->@820
  HUNK 2 replace orig[77:78]=1 prod[77:78]=1   @534  L324  POP_JUMP_FORWARD_IF_TRUE ->@568 | ->@820
  HUNK 3 replace orig[185:186]=1 prod[185:186]=1 @992 L338 POP_JUMP_FORWARD_IF_TRUE ->@1038| ->@1286
  HUNK 4 replace orig[189:190]=1 prod[189:190]=1 @1004 L338 POP_JUMP_FORWARD_IF_TRUE ->@1038| ->@1286
```

⇒ **The brief's measurement stands exactly as recorded** (294/294, 4 hunks, all four
same-opcode target-only, zero content hunks). Both jump sites of each pair are
`POP_JUMP_FORWARD_IF_TRUE`, and each pair shares one target on each side, so there are only
**two distinct (original-target, emitted-target) pairs** behind four hunks.

## 1bis. What the four targets actually are (block → source statement)

Original side (line numbers from the original code object's line table; `orig_dump.txt`):

| pair | jump site (orig) | ORIG target | statement at the ORIG target | PROD target | statement at the PROD target |
|---|---|---|---|---|---|
| 1+2 | `@522` (`dt_strf > '15:15:00'`), `@534` (`dt_strf < '08:30:00'`), both orig L324 | **@568** (L325) = `LOAD_GLOBAL NULL+time / LOAD_ATTR sleep / LOAD_CONST 60 / CALL` | the **body of the L324 test**: `time.sleep(60)` | **@820** (no line) = `JUMP_FORWARD ->@1286` | the **merge of the whole L324–L330 if/elif chain**, an unconditional jump to the loop continue-point @1286 |
| 3+4 | `@992` (`dt_strf > '15:00:00'`), `@1004` (`dt_strf < '09:00:00'`), both orig L338 | **@1038** (L339) = `LOAD_GLOBAL NULL+time / … / LOAD_CONST 60 / CALL` | the **body of the L338 test**: `time.sleep(60)` | **@1286** (L308) = `EXTENDED_ARG / JUMP_BACKWARD ->@50` | the **outer `while True:` back-edge / merge** block |

The two test chains are structurally identical in the original (three-operand `or`):

```
@512 LOAD_FAST dt_strf ; @514 LOAD_CONST '15:15:00' ; @516 COMPARE_OP >
@522 POP_JUMP_FORWARD_IF_TRUE ->@568          <-- operand A true  -> BODY
@524 LOAD_FAST dt_strf ; @526 LOAD_CONST '08:30:00' ; @528 COMPARE_OP <
@534 POP_JUMP_FORWARD_IF_TRUE ->@568          <-- operand B true  -> BODY
@536..@566  chained compare  '11:30:00' < dt_strf < '12:30:00'   (SWAP/COPY/COMPARE_OP pattern)
@562 JUMP_FORWARD ->@568                      <-- operand C true  -> BODY  (UNCHANGED in prod)
@566 JUMP_FORWARD ->@612                      <-- chain false     -> elif L326
@568 (L325) time.sleep(60) ; @610 JUMP_FORWARD ->@1286
```

Because operand C's true edge (`@562`) still lands on @568 in BOTH sides and only A and B's
edges moved, the product cannot be rendering `A or B or C`. Reading the product source
(`strategyOK.py:231-237`, and `:241-246` for the second pair) it renders:

```python
231:  elif not (dt_strf > '15:15:00' or dt_strf < '08:30:00'):
232:      if '11:30:00' < dt_strf < '12:30:00':
233:          time.sleep(60)
234:      elif '08:30:00' <= dt_strf < '08:59:00' or '12:30:00' <= dt_strf < '12:59:00':
...
241:  elif not (dt_strf > '15:00:00' or dt_strf < '09:00:00'):
242:      if '11:30:00' < dt_strf < '12:30:00':
243:          time.sleep(60)
```

`if A or B or C: BODY else: REST` and `if not (A or B): if C: BODY else: REST` emit **the
same opcode sequence** and differ only in where A's and B's `POP_JUMP_IF_TRUE` land —
which is precisely the 4-hunk target-only shape measured. (The decompiler's own
`is_future_tradetime_now`/`is_stock_tradetime_now` helper bodies at `strategyOK.py:204-213`
show the corpus has the `a <= x <= b or c <= x <= d` chained-compare style elsewhere, so the
`elif not (...)` split is not a rendering accident of the printer but a **region/edge
assignment**.)

In-edges (measured from the original disassembly, `orig_dump.txt` grep for `->@`):
* `@568` (ORIG landing): in-edges = `@522 PJT`, `@534 PJT`, `@562 JF`; **no fall-through**
  (`@566` jumps away). Three edges, all from the same test chain, all to the same body.
* `@820` (PROD landing): in-edges = `@772 POP_JUMP_IF_FALSE` + fall-through from `@818 POP_TOP`
  (last body of the chain) ⇒ a genuine **region-merge** block, one unconditional
  `JUMP_FORWARD ->@1286`.
* `@1038` (ORIG landing): in-edges = `@992 PJT`, `@1004 PJT`, `@1032 JF`; no fall-through.
* `@1286` (PROD landing): the loop's continue/merge point — targets of `@510, @610, @716,
  @778, @980, @1078, @1182, @1238, @1244` (every arm's tail) and the origin of the
  `JUMP_BACKWARD` to the loop head.

## 2. Host emitter line

Dispatch first (see §4 for the instrument): the target is generated by the **real**
`pycdc.py --region` path (`build_cfg` → `RegionASTGenerator(cfg, top_level_code=code)
.generate()` → `CFGASTConverter` → `CFGCodeGenerator`), whose product is byte-identical to
the sealed `strategyOK.py` except the 3-line `# Source Generated with Decompyle++` header
(`diff D:/Temp/r137/probe2_out.py D:/Temp/r137/out_now.py` = only that header). So every
event below is on the dispatched path, not a hand-built `analyze()` census.

Role census measured on the live generator (`D:/Temp/r137/probe2.log`):

```
BoolOpRegion entry=512  merge_block=568
   op_chain [(512,'or', tail POP_JUMP_FORWARD_IF_TRUE->@568),
             (524,'or', tail POP_JUMP_FORWARD_IF_TRUE->@568)]     <- only 2 members
   member@512 succ=[524,568,1290] cond_succ=[524,568]
   member@524 succ=[536,568,1290] cond_succ=[536,568]             <- fall-through is @536, a TEST block
BoolOpRegion entry=982  merge_block=1038   (mirror image, members 982/994, fall-through @1006)
IfRegion entry=512 cond=524  merge_block=568  then_blocks=[536,552,562,564,612,…,820]
IfRegion entry=982 cond=994  merge_block=1038 then_blocks=[1006,1022,1032,1034,1080,…,1286]
IfRegion entry=1006 cond=1006 merge_block=1038 then_blocks=[1032] else_blocks=[1034,1080,…]
                                          chained_compare_blocks=[1022]
block_to_region[@568] = block_to_region[@820] = TryExceptRegion entry=48   (no per-IfRegion owner)
```

The single line that turns the two `IF_TRUE` edges away from the block the analyzer recorded
as the chain's own `merge_block` (@568 / @1038) is the **whole-chain negation latch**:

* **host A (all four jumps)** — `core/cfg/region_ast_generator.py:
  _if_extract_condition_from_instructions:23998` (`_boolop_negate = True`), *applied* at
  `:24027` (`boolop_expr = _negate_expr(boolop_expr)`).
  Line-level trace (`probe2.log`, `==== decision-line hits ====`): for `cond_block@524` and
  `cond_block@994` the sequence `23986 → 23996 → 23998 → (23999 latch True) → 24027 →
  24042` executes and the expression changes from `BoolOp('or',[A,B])` to
  `UnaryOp('not', BoolOp('or',[A,B]))`; `_wrap_boolop_with_merge_compare` (:24042/37241)
  is a pass-through here (in == out). No other code object in this file fires the latch
  (`pipe.py --arm none` ⇒ `cond_blocks_with_negation=[524, 994]` only).
  Stated basis in whitelisted facts only — the guard reads:
    – block-tail opcode: `_last_cb.get_last_instruction().opname in
      FORWARD_CONDITIONAL_JUMP_OPS` ∧ `'TRUE' in opname` (`:23988-23989`);
    – chain-wide tail identity + uniform-target identity: `:23966-23985`
      (`_w14_tgts` all the *same block object*; `_w14_all_true` True ⇒ `_w14_uniform_and`
      stays False);
    – predecessor/successor identity: `:23996` `_boolop_mixed_polarity_or_chain(...) is None`
      — that predicate itself documents (`:38353-38356`) "*uniform target = S ⇒ positive
      or-chain; uniform target = F (the merge) ⇒ negated whole chain*" and returns None for
      both, so **the latch at :23998 negates unconditionally, without ever comparing the
      uniform target against the region's false entry.**
  The falsifying fact is in the same census: the uniform target @568/@1038 **is** the
  BoolOpRegion's own `merge_block`, and the last member's non-jump conditional successor
  (@524→@536, @994→@1006) is itself a test block whose jump *re-enters that same target*
  (`@562 JUMP_FORWARD ->@568`, `@1032 JUMP_FORWARD ->@1038`), while the emitted landing
  @820/@1286 is reached by the *false* edge of a later arm (`@772 PJF->@820`,
  `@1238 PJF->@1286`). Per the algorithm's own stated semantics that makes @568/@1038 the
  **true entry S**, so the whole-chain negation is unlicensed here.

* **host B (the reason a fix is not just "don't negate")** — identification side:
  `BoolOpRegion@512.op_chain` is a *prefix* `[512, 524]` of the real three-operand
  `or` chain; the chained-compare member `@536…@562` (tail `POP_JUMP_FORWARD_IF_FALSE->@612`,
  true side `@562 JUMP_FORWARD->@568`) was put in `IfRegion@512.then_blocks` instead, so no
  canonical "last member ends IF_FALSE→F" member exists for the consumer to see. That
  membership decision is in `core/cfg/region_analyzer.py`
  (`_detect_boolop_conditional_chain`, named as the identification counterpart by the
  docstring at `region_ast_generator.py:38370`); exact line pending in §2bis.

Single host vs multiple: **the target for all four jumps is decided by ONE line
(`region_ast_generator.py:_if_extract_condition_from_instructions:23998`, applied at
`:24027`)** — but that line is only *reachable* because of a second, independent
membership decision on the analyzer side; see §5 (suppression) — removing the negation alone
moves the error, it does not remove it.

## 2bis. Suppression channels (each proved to move bytes or not)

All arms = in-process monkeypatch on the real pipeline, product into scratch, measured with
`hunk137.py --prod` and `pyc_verify single … --source`:

| arm | what is suppressed | hunk shape | judge |
|---|---|---|---|
| `none` | — (control, reproduces sealed bytes) | 294/294, 4 hunks, **4 target-only**, 0 content | 26/27 |
| `negate-guard` | only the `:23996` call ⇒ latch at `:23998` cannot fire | 294/294, 4 hunks, **2 target-only + 2 CONTENT** (`POP_JUMP_FORWARD_IF_TRUE@534` became `POP_JUMP_FORWARD_IF_FALSE->@820`) | 26/27 |
| `inner-38744` | only the `:38744` call (inside `_build_boolop_expression_inner`) | 294/294, 4 hunks, **4 target-only — byte-identical to control** | 26/27 |
| `negate-expr` | module global `_negate_expr` = identity (all appliers) | 294/294, **5 hunks**, 2 target-only + 3 content | **23/27** |

⇒ host A (`:23998`/`:24027`) **is** an operative channel for this unit (bytes move);
⇒ the `:38744` call site is **not** a channel for this unit (suppressing it changes nothing);
⇒ a global `_negate_expr` suppression is far too broad (3 other units regress) — the fix
must be a predicate at the latch, not the removal of the negation machinery;
⇒ the `negate-guard` arm emits `elif A or B:` + nested `if C` (product line
`elif dt_strf > '15:15:00' or dt_strf < '08:30:00':`) which lands A's true edge on `@536`
and flips B's tail to `IF_FALSE→@820` — i.e. the *pair* `A,B` is now compiled as a
2-operand positive or-chain whose merge is `@820`. This is the direct measurement that
**the or-chain membership (host B) is a second, independent defect**: the original is a
3-operand chain `[512, 524, 536…562]` with `S=@568`, `F=@612`.

## 3. ANCHOR-label verdict

**The "ANCHOR" label in the residual ledger is wrong for all four jumps.** Measured:

* the whole unit contains exactly **2 NOPs**, both at the top (`ORIG NOP@46 line=307`,
  `NOP@48 line=308`; `PROD NOP@46 line=220`, `NOP@48 line=221`) — the `try:`/`while True:`
  line anchors, untouched by every hunk (`@46/@48` are also the `JUMP_BACKWARD->@48`
  continue-anchor of L313, which is emitted correctly on both sides);
* all four **original** targets are real instructions, not padding: `@568` and `@1038` are
  `LOAD_GLOBAL NULL+time` (line anchors 325 / 339) — `nop_at_target=False`, `padding=[]`;
* all four **emitted** targets are real instructions too: `@820` = `JUMP_FORWARD`,
  `@1286` = `EXTENDED_ARG/JUMP_BACKWARD` — `nop_at_target=False`, `padding=[]`;
* NOP count and NOP offsets are **identical on both sides** (2/2, same offsets), so no
  anchor was added, dropped, or shifted; and no hunk's target differs from the other side
  by "anchor vs next real instruction" — the two sides differ by *which arm block* is
  named (body vs merge).

⇒ not one of the four is an anchor-placement defect; there is no "anchor vs next real
instruction" split among them. The label (which came from the ticket, §一 row 7 of
`TICKETS_ROUND11.md`, and was already flagged there as unconfirmed) must be replaced:
this unit belongs to the `#14` **TARGET_ONLY / landing** family, and it is the
**whole-chain-negation polarity of a multi-operand `or` condition** sub-form, i.e. the
same family as B134's U2 (see §5).


## 4. Dispatch verification

(pending)

## 5. Cross-check with B134's two units

(pending)

## 6. Minimal repro

(pending)

## 7. Falsifications

* NONE against the brief so far: `294/294`, `4 hunks`, `4 target-only`, `0 content`
  all reproduced by my own instrument.
