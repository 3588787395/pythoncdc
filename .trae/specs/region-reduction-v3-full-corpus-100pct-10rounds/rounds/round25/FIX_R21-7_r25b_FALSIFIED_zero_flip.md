# FIX_R21-7 — broker dead-suite-after-terminator (engineer r25b)

Branch `rr-v3r01-f557fd`, repo HEAD read as `b741605a`. Owned file:
`core/cfg/region_ast_generator.py` ONLY. Victims:
`site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc`
`<module>.TradeLiveBroker._process_order` (delta=-465), `._process_cancel_order`
(delta=-293), `._sync_worker`. Appended live; status at each write is stated.

## 1. Mirror build proof

`cp -r /d/Temp/r25a/wt /d/Temp/r25b/wt` (+ `tools`, `pristine`), then re-verified
from scratch (repo had advanced since r25a was built):

* `diff -rq` of `core parsers utils bytecode scripts` + `pycdc.py` mirror vs repo
  → **zero differences** (mirror byte-identical to the repo tree, read-only repo).
* sha256 first-16 re-read inside the mirror:
  `region_ast_generator.py 5043790fbeaca162`, `region_analyzer.py b7f3076323813787`,
  `comprehension_generator.py 7d8acab92ccc7782`, `ast_generator_v2.py beeaf14435e22922`,
  `pycdc.py cf4e2705ab042732` → all four core files match the brief's sealed values
  (files over numbers: `git show HEAD:` hashes differ only because the working tree
  is CRLF-normalised on checkout; the *file* hashes are the sealed ones).
* `pristine/core/cfg/region_ast_generator.py` re-saved from the mirror and `cmp`
  byte-identical (sha16 `5043790fbeaca162`).
* r25a's `out/broker.UNPATCHED.py` re-verified against a fresh regeneration in MY
  mirror: `D:/Temp/r25b/out/broker.UNPATCHED.py`, 3068 lines, 5.3 s, sha16
  `58b4f095ddf4c191`. `cmp` differs **only in line endings** (r25a wrote with
  default newline translation → CRLF; my writer uses `newline=''` → LF);
  `str.splitlines()` equality → **identical content**. Product KEPT as a
  cross-check, but all my own judgments use my freshly generated LF products.
* Batteries present in the mirror at the same relative depth
  (`.trae/specs/region-reduction-v3-full-corpus-100pct-10rounds/rounds/round14/{repro,repro_arm,repro_ccneg}`,
  `round18/repro_retbreak`, `round19/repro_orderapi`, `round19/repro_tail`).

## 2. Stage 1 baseline (generator = MIRROR tree `D:/Temp/r25b/wt`; pyc + judge = repo tree)

Judge = `python -X utf8 scripts/pyc_verify.py single <pyc> --source <fresh mirror product>`
(`tools/panel.py`, strictly sequential, one heavy job at a time). Every number below
reproduces the brief:

| file | reading | expected |
|---|---|---|
| trade_live_broker.pyc | **119/128** (9 failing units) | 119/128 ✓ |
| fly/data/quote.pyc | **89/92** | 89/92 ✓ |
| IQCommon/strategy/wizard_quant_api.pyc | **57/58** | 57/58 ✓ |
| real_quote.pyc | **44/45** | 44/45 ✓ |
| IQCommon/api/klinedata.pyc | **63/64** | 63/64 ✓ |
| IQCommon/logger/handlers.pyc | **29/30** | 29/30 ✓ |
| IQCommon/util/trade_info_utils.pyc | **38/41** | 38/41 ✓ |
| IQData/api/api_base.pyc | **27/28** | 27/28 ✓ |
| strategy.pyc | **26/27** | 26/27 ✓ |
| realtime_event_source.pyc | **12/13** | 12/13 ✓ |
| plugin_system_risk_calculation/__init__.pyc | **42/43** | 42/43 ✓ |
| SENTINEL fly/data/quotation.pyc | **153/153** | 153/153 ✓ |
| SENTINEL matcher.pyc | **17/17** | 17/17 ✓ |
| SENTINEL fly_api/order_api.pyc | **37/37** | 37/37 ✓ |

Broker failing units named by the judge: `_process_order`, `_process_tick_order`,
`_process_cancel_order`, `_sync_worker`, `_trade_status_handle`, `etf_basket_order`,
`etf_purchase_redemption`, `ipo_stocks_order`, `get_ipo_stocks` (9, not 10).

## 3. Dead-suite census BEFORE any predicate

`D:/Temp/r25b/tools/census_dead_suite.py` (iterative `ast.parse` walk; `ast.parse`
keeps pre-DCE statements) on `out/broker.UNPATCHED.py`:

```
<module>.TradeLiveBroker._process_cancel_order   groups=2 dead=6
    While  body  Continue @528   idx 2/8 +5 rem=Assign,If,Try,Continue,Try
    While  body  Continue @564   idx 6/8 +1 rem=Try
<module>.TradeLiveBroker._sync_worker            groups=2 dead=7
    While  body  Return   @855   idx 1/6 +4 rem=Continue,If,Expr,Continue
    While  body  Continue @856   idx 2/6 +3 rem=If,Expr,Continue
<module>.TradeLiveBroker._process_order          groups=1 dead=2
    While  body  Break    @429   idx 1/4 +2 rem=Try,Try
UNITS_WITH_DEAD_SUITES=3 groups=5 dead_stmts=15
```

=> **REPRODUCED: 1/2/2 on exactly the three victims, 0 on the other six failing
units of the same file.** The brief's "other seven" reflects a 10-failure (pre
gate-25) roster; the file has 9 failures at 119/128. All 5 groups are
`While.body` suites — no If/Try/For/Except suite is affected.

## 4. Attribution (measured, not assumed)

Probe `tools/trace_sites.py` (line-event `settrace` restricted to a whitelist of
generator methods + watched units; **byte-proven inert**: `cmp out/broker.TRACE.py
out/broker.UNPATCHED.py` → identical, also for `_sync_worker` run). Records =
generator line numbers that CONSTRUCT a bare terminator dict, with the block
offset and the suite list at that moment:

```
_process_order        25709 _process_if_blocks blk=[44, 2912, 44]
_process_cancel_order 25709 _process_if_blocks blk=[922, 1930, 44]
_sync_worker          25709 _process_if_blocks blk=[1872, 1876, 1872]
```

The named host in the brief (`_generate_block_statements_body` ≈:52557 / role→Break
≈:53051, now 52640 / 53062-53165) is **NOT** the emitting site for these three units;
the emission is in `_process_if_blocks` at the `role in (BREAK, PURE_BREAK)` branch,
line **25709** (the "no meaningful instructions" path).

CFG facts (fresh `build_cfg` + `RegionAnalyzer(cfg).analyze()`, read-only):

```
_process_order       : LoopRegion entry=46 header=46 back=3128
                       break_blocks = [(44, ['NOP'], role=BREAK, successors=[46])]
                       continue block 360 ends JUMP_BACKWARD -> 44
_process_cancel_order: block @44 role=BREAK own=Loop@46 succ=[46], instructions=[NOP]
                       continue blocks @350 and @922 both JUMP_BACKWARD -> 44
```

i.e. the block that is *registered as the loop's break landing pad* is the pad the
`continue` back edge re-enters the loop through. Emitting `break` for it injects a
terminator into the middle of the loop-body suite; CPython's dead-code elimination
then deletes every statement the original really ran afterwards (465/293 instructions
in the two `_process_*` units).

## 5. 判据实现 (exact file:line + predicate text)

File: `core/cfg/region_ast_generator.py` (only file changed).
Site: `_process_if_blocks`, inside `if role in (BlockRole.BREAK, BlockRole.PURE_BREAK)`,
immediately **before** the pre-existing `stmts.append({'type': 'Break'})` at pristine
line **25709** (patched lines 25709-25748; the append stays at 25749).

Predicate (verbatim, comments omitted — the code):

```python
                _r25b_loop = self._current_loop
                if _r25b_loop is not None:
                    _r25b_succs = [s for s in block.successors
                                   if s not in (getattr(block, 'exception_successors',
                                                        None) or [])]
                    _r25b_hdr = _r25b_loop.header_block
                    _r25b_cond = _r25b_loop.condition_block
                    _r25b_back = _r25b_loop.back_edge_block
                    if (_r25b_succs
                            and all(s in _r25b_loop.blocks for s in _r25b_succs)
                            and any(s is _r25b_hdr or s is _r25b_cond or s is _r25b_back
                                    for s in _r25b_succs)):
                        _r25b_back_pred = False
                        for _r25b_p in block.predecessors:
                            _r25b_pl = _r25b_p.get_last_instruction()
                            if (_r25b_pl is not None
                                    and _r25b_pl.opname in (
                                        'JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT')
                                    and self.cfg.get_block_by_offset(_r25b_pl.argval)
                                    is block):
                                _r25b_back_pred = True
                                break
                        if _r25b_back_pred:
                            self.generated_blocks.add(block)
                            self.generated_offsets.add(block.start_offset)
                            continue
```

Reading: a BREAK/PURE_BREAK-role block that (a) carries no meaningful instruction
(already established by the enclosing branch — this is the empty-pad path),
(b) lies inside the *current* loop and whose every non-exception successor is
inside that same loop with at least one of them being the loop's
header/condition/back-edge block, and (c) has a predecessor whose last
instruction is an unconditional `JUMP_BACKWARD` landing on it, is the **continue
re-entry pad**, not a loop exit. It therefore contributes **no statement**; the
back edge is already regenerated by the predecessor's `Continue`, and the
remaining arm blocks keep their identification order (the remainder is emitted
instead of after a phantom terminator). Nothing is deleted from the remainder,
no post-hoc pass over finished output, no sibling/parent-region read.

## 6. Stage readings (patched mirror = `446c82d884448ecf`)

Products: `out/broker.PATCHED.py` (3067 lines) regenerated in the patched mirror;
shape readings from the REPO rig
(`.trae/specs/…/unit_diff.py … --prod D:/Temp/r25b/out/broker.<tag>.py --all`)
— pyc input = repo tree, product = mirror tree (stated per rule).

Dead-suite census (`tools/census_dead_suite.py`), before → after:

| unit | before | after |
|---|---|---|
| `_process_order` | 1 group / 2 dead (While body, `Break` idx 1/4) | **0 / 0** |
| `_process_cancel_order` | 2 groups / 6 dead (While body `Continue` idx 2/8 + 6/8) | **1 group / 1 dead** (If body `Continue` idx 3/8 — no longer a loop-body fold) |
| `_sync_worker` | 2 groups / 7 dead (While body `Return` idx 1/6, `Continue` idx 2/6) | 2 groups / 7 dead — **unchanged, different site** |
| file total | 3 units / 5 groups / 15 dead stmts | 2 units / 3 groups / 8 dead stmts |

Shape per victim, before → after (`--all`, judge with `--source`):

```
_process_order         UNPATCHED len orig=507 prod=42  delta=-465 hunks=4  landings=1
_process_order         PATCHED   len orig=507 prod=448 delta=-59  hunks=20 landings=14
_process_cancel_order  UNPATCHED len orig=333 prod=40  delta=-293 hunks=3  landings=0
_process_cancel_order  PATCHED   len orig=333 prod=303 delta=-30  hunks=6  landings=3
_sync_worker           UNPATCHED len orig=404 prod=401 delta=-3   hunks=5  landings=6
_sync_worker           PATCHED   len orig=404 prod=401 delta=-3   hunks=5  landings=6
```

Verbatim emitted-source evidence (`_process_order` while body): the phantom
`break` is gone and the two `try:` suites that follow the `continue`-guard are
live; in `_process_cancel_order` the arm renders as
`if order in self.orders: entrust_no = order.entrust_no; …` instead of
`if order in self.orders: break` + dead remainder.

Panel (all 14, judge `--source` on fresh mirror products, tag=PATCHED):
`broker 119/128 · quote 89/92 · wizard 57/58 · real_quote 44/45 · klinedata 63/64 ·
handlers 29/30 · trade_info_utils 38/41 · api_base 27/28 · strategy 26/27 ·
event_source 12/13 · risk_init 42/43` — **identical to Stage 1: zero decreases**.
Sentinels `quotation 153/153 · matcher 17/17 · order_api 37/37` — held.

Batteries (run inside the mirror, so ROOT = `D:\Temp\r25b\wt`; recorded values):

```
repro     RED=9  / 9      (recorded 9R/9)    ✓
arm       GREEN=0 RED=3/3 (recorded 0G/3R)   ✓
ccneg     GREEN=3 RED=1/4 (recorded 3G/1R)   ✓
retbreak  GREEN=2 RED=2 DRIFT_VS_BASELINE=0  ✓
orderapi  GREEN=5 RED=0/5 (recorded 5G/0R)   ✓
tail      GREEN=13 RED=0/13 (--run)          ✓
```

## 7. 负面证据 (measured)

1. **No unit flip.** All three victims still `Failure: Different control flow`;
   broker stays **119/128**. So the landing bar (≥1 named victim flip,
   `_process_cancel_order` ⇒ 120/128) is **not** met: this is
   FALSIFIED-BUT-SUPPORTING, not LANDED-READY.
2. **The criterion fires nowhere else.** `cmp out/<slug>.UNPATCHED.py
   out/<slug>.PATCHED.py` over the 14 panel products: only `broker` differs
   (87 changed lines); the other 13 products are **byte-identical**. Narrow
   blast radius is measured, not claimed.
3. **Residual is a second, different mechanism, and it is NOT a dead suite.**
   For both `_process_order` and `_process_cancel_order` the largest surviving
   hunk is `delete orig[15..48 @@98..@@316] del=33 ins=0`: the
   lock-`try/finally` (`self.lock.acquire(); account, order =
   self.open_orders.pop(0)` / `… release`) is emitted **last** in the loop body
   although its blocks `@96/@98` are the lowest-offset body blocks, and its text
   *is* present in the product (line 490 PATCHED) — the loss is positional, not
   DCE. Its sibling unit `_process_tick_order` (0 dead suites, still failing)
   shows the correct source order (`try: lock…` first, then
   `if self.trade_status…`). Correcting it means re-ordering a child
   `TryExceptRegion` entry against the loop's `body_blocks_no_header`/
   `_loop_postprocess` flush — i.e. reordering across a region boundary, which
   this ticket forbids me to smuggle in. I did not attempt it.
4. `_sync_worker` (delta=-3) is untouched by this criterion: its dead suite is a
   phantom `Return`/`Continue` pair produced at `_generate_block_statements_body:53497`
   and `_if_generate_then_branch:18366` (trace records), not at the BREAK-role
   pad site 25709 — a different mechanism, consistent with the brief's warning
   that this file needs seven distinct mechanisms and that 128/128 is out of
   reach for this bucket.
5. `landings` rose (`_process_order` 1 → 14) as the suite became live: the
   14 are same-offset/other-position jump-target differences of code that was
   previously deleted, not new content losses (content `delta` fell −465 → −59).
6. Probe hygiene: `tools/probe_terms.py` and `tools/trace_sites.py` were each
   `cmp`-proved byte-identical to `out/broker.UNPATCHED.py` (3 runs); a naive
   full-file `settrace` was **not** usable (RecursionError at the default limit;
   whitelisting the traced functions + `setrecursionlimit(20000)` restored
   byte-identity). No stub was left in any deliverable.
7. Brief numbers corrected by measurement: the brief's `_generate_block_statements_body`
   ≈:52557 / role→Break ≈:53051 host is not the emitter for these units (the
   emitter is `_process_if_blocks` 25709); repo HEAD read as `b741605a`; the
   failing-unit roster is 9 (not 10), so the untouched-by-this-defect group is
   six units, not seven.

## 8. Final declaration

**FALSIFIED-BUT-SUPPORTING — NOT landed; do not install as a landing.**
Zero flips (broker stays 119/128); the mechanism is real, measured and inert-clean
(13/14 panel products byte-identical, all six batteries at recorded values), and it
removes the dead-suite emission fold on 1 of the 3 victims completely
(`_process_order` 1→0 groups, delta −465→−59) and partly on a second
(`_process_cancel_order` 2→1 groups, delta −293→−30); `_sync_worker` is a
different site (unchanged).

* Delivered file: `D:/Temp/r25b/DELIVER/region_ast_generator.py`
  (the WHOLE changed file, 59684 lines, 3 752 426 bytes, pure CRLF, 0 bare LF).
* sha256 first-16: **`446c82d884448ecf`** (pristine sealed bytes:
  `5043790fbeaca162`).
* diff vs pristine: `25708a25709,25750` → **42 added lines, 0 removed = 42
  changed lines** (`out/gen_diff.txt`).
* `py_compile` proof: `py_compile.compile(r'D:\Temp\r25b\DELIVER\region_ast_generator.py',
  cfile=r'D:\Temp\r25b\out\deliver_compile_check.pyc', doraise=True)` → OK,
  2 544 025-byte pyc written.
* The repo was never written to (`diff -rq core parsers utils bytecode scripts
  pycdc.py` vs the mirror shows the mirror == repo; no mutating git command was
  run; the 402-file gate was not run).
* Determinism: a second regeneration from the patched mirror
  (`out/broker.PATCHED2.py`) is byte-identical to `out/broker.PATCHED.py`
  (`cmp` clean, 3067 lines / 175 553 bytes); mirror generator still
  `446c82d884448ecf`.
* Revert (mirror scratch, if the certifier wants the tree back at sealed bytes):
  `cp /d/Temp/r25b/pristine/core/cfg/region_ast_generator.py /d/Temp/r25b/wt/core/cfg/region_ast_generator.py`
  — verify with
  `python -c "import hashlib;print(hashlib.sha256(open(r'D:/Temp/r25b/wt/core/cfg/region_ast_generator.py','rb').read()).hexdigest()[:16])"`
  → `5043790fbeaca162`. As delivered, the mirror is left **patched**
  (`446c82d884448ecf`) so the readings above are reproducible.

