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

(pending — pipeline instrumentation in progress)

## 3. ANCHOR-label verdict

(pending — NOP census below is measured, prose pending)

## 4. Dispatch verification

(pending)

## 5. Cross-check with B134's two units

(pending)

## 6. Minimal repro

(pending)

## 7. Falsifications

* NONE against the brief so far: `294/294`, `4 hunks`, `4 target-only`, `0 content`
  all reproduced by my own instrument.
