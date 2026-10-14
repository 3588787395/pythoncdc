# FIX_R21-72 - reconnect guard-chain region declaration (analyzer-side, `_sync_worker`)

Engineer: r100a. Round 40. File edited: `core/cfg/region_analyzer.py` ONLY (mirror
`D:/Temp/r100`). Generator untouched (`0f4c3898298e6f2e`). Ticket:
`rounds/round40/TICKET_R21-59_sync_worker_per_exit_edge_duplication.md` addendum 19 (plus 6-18).
Rule label: `[R21-72 …]`.

## 0. Base verification (before any measurement)

Mirror `D:/Temp/r100` copied from repo `core parsers bytecode utils scripts pycdc.py`. Pair
installed (sha256[:16], size, BOM + all-CRLF, 0 bare LF, 0 `\r\r\n`):

```
1471c92eca157e46 2121884  core/cfg/region_analyzer.py      (r93/region_analyzer_R21-64a_FINAL.py)  <- edited here
0f4c3898298e6f2e 3860104  core/cfg/region_ast_generator.py (r95/..._R21-66_0f4c3898298e6f2e.py)    untouched
```

`orchestrator/fastgate_r91m.py`, `gold_diff_r91m.py`, `win_r91.py`, `merge_measure_r91m.py` copied
to `D:/Temp/r100/orch/` (and `win_r91.py` at the mirror root, which is where the rig looks for it),
with their `M` constant repointed `D:/Temp/r91m -> D:/Temp/r100`. Round-14 battery copied to the
same relative depth so its `ROOT` (7 dirname steps from `__file__`) is `D:\Temp\r100` - the runner
echoes that root, verified in §5.

## 1. Reproduced orchestrator numbers (base = pair, BEFORE my edit)

```
[single] status=failure units=127/128 success_rate=99.22%
  ***<module>.TradeLiveBroker._sync_worker: Failure: Different control flow
orig instrs=412 prod instrs=408 delta=-4   windows=5
product = 178790 bytes
unit=_sync_worker ours=42 lines GOLD=45 lines  hunks_vs_GOLD=2
   @@ -18,0 +19,8 @@   @@ -37,5 +44,0 @@
```

All four brief numbers reproduced (`units=127/128`, sole failure `_sync_worker`, windows 5,
178,790 B, gold_diff 2). Logs: `logs/base_unit_ours.txt`, `logs/base_unit_gold.txt`,
`logs/dump_base_1200_1960.txt`.

## 2. Census BEFORE editing

Census rig `census_r100.py`: `build_cfg` + `RegionAnalyzer.analyze()`, then read-only conjunct
evaluation in its own process (judged products come from separate clean `pycdc.py` runs, so the
census cannot perturb a product; it reports non-zero evaluations on every file, so it is not a
silent rig).

Conjuncts (opcode class / jump-target class / region data / pred-succ relations only - no function
or file names, no absolute offsets, no counters, no thresholds):
① G0 ends in a forward conditional jump to T (T != G0); ② consecutive blocks (adjacent in CFG block
order) ending in conditional jumps to the SAME T, at least two guards; ③ arm = forward closure from
the last guard's non-T successor, every edge lands inside the arm or on T, none backwards of G0;
④ the site has exactly ONE successor-less block and it ends in `RETURN_VALUE`/`RETURN_CONST`
(measured: the arm's *highest-order* block is `@1876`, which falls through to T, so the ticket's
"last block terminates in RETURN_VALUE" is literally false; the data form that holds is "unique
sink is a return"); ⑤ T is a declared region entry (sibling-region entry class); ⑥ the arm contains
a declared region entry. Maximality per unit: a firing site whose block set is properly contained in
another firing site's is dropped (this removes the inner `@1524/@1638` sub-chain, which the
un-narrowed predicate also fired on).

| population | files | units | LoopRegions | sites evaluated | fires |
|---|---|---|---|---|---|
| PANEL_20files, before narrowing (①-⑤ + maximality) | 20 | 957 | 629 | 318 | **2** |
| PANEL_20files, narrowed (+⑥) | 20 | 957 | 629 | 318 | **1** |
| corpus 402 (`rounds/round40/r95/corpus402.txt`), narrowed | 402 | 6617 | 1766 | 681 | **1** |

Collateral evidence that forced the narrowing: the 20-file pre-narrowing second fire was
`IQCommon/strategy/wizard_quant_api.pyc :: check_factor` (guards `[10,62]`, arm `[108]`,
merge 114) - a currently-**Equal** file. Its arm is a single return block carrying no nested
declared region, so conjunct ⑥ excludes it (the defect is the ordering of an arm that already owns
nested regions). After narrowing the whole corpus fires exactly once:

```
FIRE site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc
     unit=_sync_worker entry=1214 merge=1890 guards=[1214,1370]
     arm=[1388,1502,1524,1638,1770,1872,1876] owner=LoopRegion@232
```
(`wizard_quant_api` still judges 58/58 under the candidate - §5.)

## 3. What the base data actually is (correction to addendum 19's wording)

The chain is not undeclared: `IfRegion@1214` already exists with
`blocks=[1214,1370,1388,1502,1524,1638,1770,1872,1876]`, `then=[1388..1876]`, `merge_block=@1890`.
What is missing is **ownership and hierarchy**: all nine blocks stay `block_to_region`-owned by the
host `LoopRegion@232` and stay in the host's `body_blocks`; the chain's IfRegions hang off the
*sibling* loop `LoopRegion@232(hdr=704)`, whose `condition_chain_blocks` claims `@1214` and `@1890`;
and `@1370` is no region of its own at all (it is `@1214`'s `condition_block`, folded by
`BoolOpRegion@1214`).

## 4. The rule implemented

`_r2172_declare_statement_guard_chain_regions()`, mounted at the end of `analyze()` (identification
time, before the generator reads anything), helpers `_r2172_cond_jump_target` and
`_r2172_find_statement_guard_chain`. Per fired site:

* (a) declare one statement-level `IfRegion` per guard (`entry=condition_block=Gi`,
  `merge_block=T`, `then_blocks=[G(i+1)]`, innermost guard's then = the whole arm) - `@1370`
  becomes a region;
* (b) detach only the fold whose **entry is a guard block** (`BoolOpRegion@1214`). The arm's real
  value chain `BoolOpRegion@1388` must survive: measured, detaching every fold whose blocks lie in
  the site degraded the condition (`date == first and time < 900 or date != first` collapsed to
  `date != first`);
* (c) register canonical `block_to_region` ownership for each site block (innermost claimer wins)
  and shrink the host's `body_blocks`/`blocks` down to the chain entry;
* (c2) evict cross-sibling double claims: another loop's `condition_chain_blocks`, `blocks` and
  `else_blocks` entries that belong to the merge sibling's region and are not that loop's own
  structural blocks (measured double claim: loop1 held `@2064/@2066/@2168`, all inside
  `LoopRegion@1890`);
* (d) re-parent: chain head becomes a direct child of the host; deeper guards nest by block-set
  containment; arm regions re-attach under their containing chain region.

Byte discipline: `install_r2172.py` splits on `b'\r\n'`, asserts every anchor unique, refuses to
install over an already-patched file, asserts no `\r\r\n` and no bare LF, and `py_compile`s.
Final candidate **`9ba2d8afe9e96fc1`** (2 141 338 B), reproduced byte-exactly from `1471c92eca157e46`
by that builder (re-verified after the doc was written, §6).

## 5. Measurements under the candidate

Target (pair generator untouched):

```
product 178982 B                      (base 178790)
[single] status=failure units=127/128 success_rate=99.22%   (unchanged, no new failing unit)
orig instrs=412 prod instrs=408 delta=-4  windows=5         (unchanged)
unit=_sync_worker ours=48 lines GOLD=45 lines hunks_vs_GOLD=2
   @@ -18,0 +19,8 @@   @@ -37,11 +44,0 @@
```

**gold_diff did NOT go 2 -> 0 and the judge did NOT reach 128/128**: the reconnect chain is still
printed after loop 2. What did change: the arm now renders as `if is_trading_date(...) and
reconnect_flag is False:` + nested inner ifs, and its terminator comes from the arm's own
`RETURN_VALUE` block (`return None` + `else: self.reconnect_flag = True`) instead of `break`.

No-regression panel (fresh mirror products, always `--source`; `ana=9ba2d8af gen=0f4c3898`):

```
[repro mechanism A]     <module>.sync_worker: Different bytecode / units=1/2   (allowed; not my subject)
[battery no-regression] RED=8 / 9  ROOT=D:\Temp\r100                            (cap 8/9 held)
realtime_event_source 12/13 (sole fail clock_worker)   function 15/15   replace_utils 9/9
quote 92/92   quotation 153/153   order_api 37/37   matcher 17/17   strategy 27/27
api_base 28/28   real_quote 45/45   handlers 30/30   klinedata 64/64   risk/__init__ 43/43
wizard_quant_api 58/58   trade_info_utils 41/41
arg_checker 49/49 | 39/39 | 43/43        profiler_func 17/17 | 15/15 | 18/18
trade_live_broker 127/128 - sole failure _sync_worker, i.e. _process_order,
  _process_cancel_order, ipo_stocks_order, etf_purchase_redemption all stay Equal
```

Mandatory 402-file collateral sweep (regenerate all 402 products in the mirror; compare
CR-stripped against `git -C repo archive HEAD site-packages | tar -x` extracted to `headtp/`;
scope `site-packages`, never `cmp` against checked-out files):

```
files=402  SAME=401  CHANGED=1  REGEN-FAIL=0  NO-BASELINE=0
CHANGED = { site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc }
          ours=175926 base=176226 delta=-300  (CR-stripped)
```
Freshness: the swept broker product is byte-identical to the product I judged, and judging that
file again reads 127/128. Expected `CHANGED = {trade_live_broker}` - met.

## 6. Ownership proof (declaration achieved, no double claim)

`ownproof_r100.py` reads the target unit after `analyze()`; full text in
`logs/ownproof_BEFORE.txt` / `logs/ownproof_AFTER.txt`:

```
BEFORE  @1214..@1876: owner=LoopRegion@232 for all 9;  9 still in host.body_blocks; host-owned=9
AFTER   @1214 IfRegion@1214 | @1370 IfRegion@1370 | @1388 BoolOpRegion@1388 |
        @1502,@1524 IfRegion@1214 | @1638 IfRegion@1638 | @1770 IfRegion@1770 |
        @1872,@1876 IfRegion@1214        -> host/none-owned = 0
        host.body_blocks keeps @1214 only (1370..1876 withdrawn)
        sibling LoopRegion@232(hdr704) claims of site/merge blocks: []  (cc/blocks/else pruned)
        hierarchy: IfRegion@1214 (parent LoopRegion@232, merge@1890, then=[1370])
                   -> IfRegion@1370 (merge@1890) -> {IfRegion@1388, @1638, @1770, BoolOpRegion@1388}
```

Post-dump region listing (`logs/dump_final_1200_1900.txt`) shows the same: `@1890` still owns its
own region, `@1210/@1212` stay loop-owned, everything in between is chain-owned.

## 7. Measured negative - the conjunct the analyzer cannot supply

The chain CAN be declared from block data alone (done, §4/§6, collateral-free, 1 fire in 402
files), but the *position* is actuated generator-side and no block/region datum of the shape this
ticket describes moves it. Evidence from `probe_gen_r100.py` (scratch process; wraps generator
methods only, ships no bytes; generator hash stays `0f4c3898298e6f2e`, printed by the rig):

```
[GEN >>> LoopRegion@232] depth=0    host loop generation begins
[GEN >>> LoopRegion@232] depth=1    r08 path emits loop 1
[GEN >>> LoopRegion@1890] depth=2   loop 2 generated INSIDE loop 1's pass
[AFTER  blk@700]   body=[While(or-chain), While(chained-compare)]   both loops already emitted
[BEFORE blk@1214]  body=[While, While]                              host walk only now reaches @1214
[GEN >>> IfRegion@1214 -> @1370 -> @1388 -> @1638 -> @1770]         chain nests correctly
[AFTER  blk@1214]  body=[While, While, If]                          appended after loop 2
```

Three successive analyzer-side arms were tried against this route and measured inert for ORDER
(products 178734 / 178734 / 178982, chain after loop 2 in all three): pruning `@1214/@1890` out of
the sibling loop's `condition_chain_blocks`; pruning the sibling's `blocks` double claim on
`@2064/@2168`; pruning its `else_blocks` claim on `@2066`. The data the generator consumes for
dispatch (`get_entry_region_for_block(@1214) -> IfRegion@1214`, `@1214` a direct child entry of the
host, unique ownership) is correct after the declaration, yet the emission point is fixed by the
host loop's nested-loop pre-pass (`region_ast_generator.py:8762-8832` r08 path plus
`_loop_postprocess` at `region_ast_generator.py:14704`), which renders sibling `LoopRegion`s before
the body walk reaches the chain entry.

So the missing conjunct is generator-side: the host must not emit a later sibling `LoopRegion`
from an earlier nested loop's pass while a direct-child region with smaller entry order is still
unemitted. That is `region_ast_generator.py`, which belongs to r99a, not to this ticket's file.
This candidate is offered for **banking** (declaration + unique ownership + arm-derived
terminator; no unit lost, no collateral), not as an installable flip.

Variant history (all measured on the untouched pair generator):
`12e2cfe6d4901430` inert (predicate never fired - missing `_guards.append`);
`ebd3b45a0b45bdab` fired, detach too broad (condition leg lost);
`b0691bcc6e7c4cdb` + cc eviction (same product); `a72944ff87ff6028` + blocks eviction (same);
`027b635db401ccc1` narrower detach (178982); `343a6dab0330b252` + else_blocks eviction (same product);
`2dc8a10ca5a4ca46` fold retained (178371, statements lost - rejected);
**`9ba2d8afe9e96fc1` delivered** (same product as `027b635d`/`343a6dab`, with the house-style notes).

## 8. Deliver (`D:/Temp/r100/DELIVER`)

FIX doc; `region_analyzer_R21-72_9ba2d8afe9e96fc1.py` (full candidate, sha16 recorded);
`install_r2172.py` (builder: regenerates it byte-exactly from `1471c92eca157e46`);
`ownproof_r100.py` + before/after proofs; `dump_r100.py` + before/after dumps;
`census_r100.py` + panel/402 census json+logs; `probe_gen_r100.py` + traces;
`panel_r100.py` + panel rows; `sweep_r100.py` + `logs/sweep_*.log`; fastgate/battery/judge logs;
`MANIFEST.sha256`. Nothing was installed into the repo; the repo bytes are untouched.

Campaign not complete: gate 40 unconsumed, `_sync_worker` remains 1 of the 2 failing units.
