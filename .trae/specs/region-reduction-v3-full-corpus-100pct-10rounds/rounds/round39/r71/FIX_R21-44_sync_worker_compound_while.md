# FIX_R21-44 (r71a) — `trade_live_broker :: _sync_worker` compound-while detector: **FIRES UNQIUELY, ZERO FLIPS → BANKED, not installed**

**Verdict: NOT flipped. Candidate delivered as a banked co-requisite, NOT installable.**
Broker stays **126/128**, `_sync_worker` stays `delta=-3 hunks=5` and is **byte-identical** to the
sealed gate-38 bytes when the candidate analyzer is installed. The identification criterion fires
exactly once across the 20-file panel (only on `_sync_worker`), builds the compound-while BoolOp
region, but that region is **reclaimed by the `block_to_region` priority rebuild** before the
generator runs, so the emitted product does not move. Even forcing the region to survive does not
flip: the generator rebuilds the compound *test* correctly but the loop's backward recheck is left
as a spurious `while False: pass`, **worsening `delta` from −3 to +19**, still `Different control
flow`. Per campaign Rule 3 (fires-without-flips ⇒ bank), nothing was installed; the repo is untouched
and the mirror is byte-clean at the landed generator `11324f276cce6d5b` / analyzer `f7d849e974904492`.

## §0 — premise check against the CURRENT landed bytes (Rule 6)

Mirror built from `core/ scripts/ parsers/ utils/ bytecode/ pycdc.py`; proven by hash:
`region_ast_generator.py = 11324f276cce6d5b`, `region_analyzer.py = f7d849e974904492` (gate-38 bytes).
Base regeneration reproduces the sealed broker product: judge
`pyc_verify single trade_live_broker.pyc --source prod/broker_base.py` → `units=126/128`, failures
`_process_order` and `_sync_worker` only; the four canaries `ipo_stocks_order`,
`_process_cancel_order`, `_trade_status_handle`, `etf_purchase_redemption` are Equal.

Re-derived `unit_diff.py '<module>.TradeLiveBroker._sync_worker'` on the landed bytes →
`len orig=404 prod=401 delta=-3`, 5 hunks, **exactly the dispatch table**:
```
== replace orig[52..53 @@362..@@362] prod[52..59]  del=1 ins=7
   - @362 POP_JUMP_FORWARD_IF_TRUE
   + @362 POP_JUMP_FORWARD_IF_FALSE / LOAD_GLOBAL NULL+time / LOAD_ATTR sleep / LOAD_CONST 60 / PRECALL / CALL / POP_TOP
== insert orig[70..70 @@520] prod[76..113] ins=37   (@560 RETURN_VALUE / @562 LOAD_FAST pre_before_trading / @564 LOAD_GLOBAL NULL+int ...)
== insert orig[71..71 @@522] prod[114..291] ins=177  (receive_trade_response_flag body material)
== delete orig[90..151 @@700..@@1210] del=61         (same sleep+strftime text, later)
== delete orig[235..397 @@1890..@@2884] del=162      (pre<=int<post region)
```
The dispatch's hunk-1 polarity reading is CORRECT but INCOMPLETE: @362 is not a standalone
polarity defect — it is the *rotated entry test* of one compound `while`.

**Structure confirmed by disassembling the ORIGINAL `_sync_worker`** (conditional jumps, this session):
the loop is `while A or B or (C and D): time.sleep(60)` where
A=`int(datetime...strftime('%H%M')) < pre_before_trading` (@362 IF_TRUE→body@704),
B=`int(datetime...strftime('%H%M')) >= int(post_after_trading)` (@520 IF_TRUE→body@704),
C=`holiday_sync_account == '0'` (@542 IF_FALSE→@702→exit@1214),
D=`not self.engine.data_proxy.is_trading_date(datetime...date())` (@698 IF_TRUE→exit@1214, fall-through→@700→body@704).
The backward re-test after the body (@874/@1032/@1054/@1208) is the same disjunction re-evaluated.

**compile() differential on 3.11.7** (`shape_r71.py`): this exact shape compiles to
`IF_TRUE→body, IF_TRUE→body, IF_FALSE→exit, IF_TRUE→exit, BACK_IF_TRUE→body, BACK_IF_TRUE→body, IF_FALSE→exit, BACK_IF_FALSE→body`
— a one-to-one match with the original jump table. The nested-while alternative the product emits
does not. This is the analyzer-side compound-while rebuild that `FIX_R21-39_r65a.md` recorded as the
route for this unit.

## §1 — the criterion (identification-time, structural, [R7-B45] mirror)

`region_analyzer.py` new method `_r2144_detect_while_condition_nested_or_and(cond_block, loop)`,
called from `_detect_while_condition_boolop_chain` after the `[R7-B45]` nested detector, returns
`or_run + and_group` = `[(232,'or'),(364,'or'),(522,'and'),(544,'and')]`.
It is the **structural mirror of the landed [R7-B45]** `while A and (B or C)` detector, for the
opposite shape `while (A or B or …) or (C and D …)`:

- ① cond_block ends in a FORWARD conditional jump `POP_JUMP_FORWARD_IF_TRUE` whose target is the loop
  body entry `true_exit`; fall-through continues the or-run.
- ② forward walk of the or-run: every member ends `IF_TRUE→true_exit`, ≥2 members.
- ③ the or-run tail's false edge opens a bracketed **and-group**: every and-member ends `IF_?→false_exit`
  (a single shared false exit ≠ true_exit), ≥2 members, and the last member's fall-through (following
  pure `JUMP_FORWARD` connector blocks, ≤4 hops) reaches `true_exit`.
  `true_exit ≠ false_exit` is exactly why the flat `all_same_target` check (:28110+) structurally rejects
  `or…or (C and D)` — the reason r65a said an "or-headed / and-tailed sibling is needed".

No function names, no absolute offsets, no counters, no magic thresholds, no cross-region/cross-level
heuristics, no retrospective repair: only block-level last-instruction opcode class, successor
identity, `region_data` (`loop.body_blocks/header_block/entry/condition_block`). Like [R21-40]/[R21-36]
the predicate reads region data + opcode classes + successor structure.

## §2 — population census BEFORE editing (Rule 2), and probe inertness

`census_r71_or_and.py` (independent reimplementation of the predicate; edits nothing) over the 20-file
panel (`PANEL_20files.txt`):
```
head_ok=1  or_run2=1  and_ok=1  FIRES=1     TOTAL across all 20 files
only fire: trade_live_broker :: _sync_worker  cond@232 chain=[(232,'or'),(364,'or'),(522,'and'),(544,'and')]
other 19 files: head_ok=0 (predicate never reaches conjunct ②, so they are structurally inert)
```
So the criterion is **corpus-unique**: 1 evaluation of the full shape, 1 fire, 0 collateral. This is
the "1-of-N actionable signature" pattern the campaign requires before claiming a fix (cf. R21-B4,
R21-B2, R21-43 each `TOTAL_FIRES=1`).

**Probe inertness proven:** installing the candidate analyzer (`measure_r71.py analyzer`) and
regenerating broker gives a product **byte-identical** to the landed base (`cmp` identical; judge still
126/128). The instrumentation itself moves no bytes because the region it produces is discarded (§3).

## §3 — why it does not flip (the exact break point), and the 2×2 half measurement (Rule 4)

With the candidate analyzer installed, Step 5 (`_detect_while_condition_boolop_chain` →
`_create_boolop_region_from_chain`) DOES build the BoolOpRegion `entry@232 blocks=[232,364,522,544]`
(traced). But `analyze()` then runs
`self.block_to_region.clear()` + a priority rebuild at `region_analyzer.py:1871` (again at `:4119`),
which re-owns the operand blocks to the enclosing `while True` **LoopRegion** (BoolOp priority 20 <
the loop/sequence Region that claims @232 as its condition_block). Traced reclaim stack
(`probe_r71_reclaim.py`):
```
[create] BoolOpRegion entry@232 blocks=[232,364,522,544]
[reclaim] block232 -> Region   (via _identify_sequence_regions :32167)
[reclaim] block232 -> LoopRegion  (:1877 rebuild)
[reclaim] block232 -> LoopRegion  (:4125 _annotate_all_roles)
final: my region NOT in regions; block_to_region[232..544] = LoopRegion
```
So the generator sees the compound-while loop with **no** consuming BoolOp child
(`iter_descendants(BoolOpRegion)` yields nothing whose op_chain contains cond 232), falls back to the
non-fold path, and the product is unchanged. **Shrinking is not even observed** — the delta stays −3,
5 hunks, identical to base.

**2×2 (Rule 4):**

| axis | _sync_worker delta | hunks | judge | broker units |
|---|---|---|---|---|
| landed (neither half) | −3 | 5 | Different | 126/128 |
| analyzer detector half ALONE (installed candidate) | −3 | 5 | Different | 126/128 (byte-identical to landed) |
| generator half ALONE | *not measurable* — no region survives to the generator without the analyzer half | — | — | — |
| forced retention (analyzer region + `analyze()` re-attach hack, no reclaim) | **+19 (WORSE)** | 4 | Different | 126/128 |

Forced-retention product (`PRODUCT_r71a_broker_FORCED_retention_probe.py`) shows the generator DOES
rebuild the compound test correctly —
`while int(...)<pre or int(...)>=int(post) or holiday_sync_account=='0' and not is_trading_date(...)`
— proving `or_groups` in `_build_boolop_expression_inner` needs no new mirror builder. But the loop's
backward recheck blocks (@876/@1034/@1056/@1212) are emitted as a spurious `while False: pass` inside
the body, because forming the compound condition leaves those re-test blocks orphaned; the fold is
therefore **not sufficient** — the flip needs the whole compound-while loop re-formed (back-edge fold),
a much deeper analyzer loop-reconstruction change with a large regression surface.

## §4 — canaries and target verdicts (Rule 3, side-by-side)

Instruction-level (candidate installed): `_sync_worker delta −3 → −3` (NO progress, byte-identical).
Unit-level verdicts: unchanged (126/128). Canaries all remain **Equal**:
`ipo_stocks_order`, `_process_cancel_order`, `_trade_status_handle`, `etf_purchase_redemption` (they
are Equal at base and the candidate moves nothing). **0 unit flips on the target and on the whole
panel.** Broker does NOT go 126/128 → 127/128.

## §5 — the exact judge line(s)

Base (landed): `python -X utf8 scripts/pyc_verify.py single site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc --source D:/Temp/r71/prod/broker_base.py`
→ `[single] status=failure units=126/128 success_rate=98.44%` (`_process_order`, `_sync_worker` Different).

Candidate analyzer installed: `... --source D:/Temp/r71/DELIVER/PRODUCT_r71a_broker.py`
→ `status=failure units=126/128` — byte-identical to base, `_sync_worker` NOT flipped.

Forced retention probe: `... --source D:/Temp/r71/DELIVER/PRODUCT_r71a_broker_FORCED_retention_probe.py`
→ `status=failure units=126/128`, `_sync_worker` delta +19 (worse).

## §6 — co-requisite for whoever reopens (what actually must close)

1. **Ownership survival (analyzer).** The compound-while BoolOpRegion created at Step 5 must not be
   reclaimed by the `block_to_region.clear()`+priority rebuild at `:1871`/`:4119` — the same ownership
   family [R21-40] addressed for the sibling `while True` back-edge. Likely a guard in the rebuild that
   keeps a condition-context BoolOpRegion owning its operand blocks when the enclosing loop's
   `condition_block` is that chain head.
2. **Back-edge fold (analyzer loop-form).** After the fold, the body's re-test blocks (@876/@1034/@1056/@1212)
   must be consumed as the loop back-edge (the `while … : sleep(60)` recheck) rather than emitted as
   `while False: pass`. Without this the delta grows (−3 → +19). This is a loop-region formation change,
   not a generator change.

## §7 — files (all in D:/Temp/r71/DELIVER, repo untouched)

- `build_cand_r71a_r2144.py` — reconstructs `CANDIDATE_r71a_region_analyzer.py` byte-exactly from the
  landed analyzer (asserts base sha16 `f7d849e974904492`, each anchor exactly once, `py_compile` OK);
  candidate sha16 `0d568cdd7fe0f167`, BOM + all-CRLF preserved.
- `CANDIDATE_r71a_region_analyzer.py` — the measured candidate (BANKED, not installed).
- `PRODUCT_r71a_broker.py` — broker regenerated with the candidate (byte-identical to landed base).
- `PRODUCT_r71a_broker_FORCED_retention_probe.py` — forced-retention probe product (delta +19 evidence).
- `census_r71_fire.txt` — 20-file population census.
- `panel_base_units.txt` — per-file units (base == candidate; changed_files=0).
- `probe_r71_{regions,blocks,reclaim}.py`, `measure_r71*.py`, `shape_r71.py`, `panel_r71.py` — tools.
