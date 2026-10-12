# FIX_R21-50 (r79a) — `trade_live_broker :: _sync_worker`: condition-context BoolOp **reclaim guard** + loop **back-edge fold** (the two co-requisites r71a named, measured as a 2×2)

Mirror: `D:/Temp/r79` (repo READ-ONLY). Landed bytes certified:
`core/cfg/region_ast_generator.py` sha16 `11324f276cce6d5b` (3846610 B),
`core/cfg/region_analyzer.py` sha16 `f7d849e974904492` (2104888 B) — the gate-38 bytes
(corpus 6614/6617 = 99.9547 %, 400/402 files). No banked base; plain landed bytes.

## §0 — premise check against TODAY's landed bytes (Rule 7: every claim re-measured)

All brief numbers **reproduced exactly**:

- base product `prod/broker_base.py` (fresh `pycdc.py --region`, old output deleted):
  `python -X utf8 scripts/pyc_verify.py single …/trade_live_broker.pyc --source prod/broker_base.py`
  → `status=failure units=126/128 success_rate=98.44%`, failures = `_process_order` + `_sync_worker`
  only ⇒ the four canaries (`ipo_stocks_order`, `_process_cancel_order`, `_trade_status_handle`,
  `etf_purchase_redemption`) are Equal at base.
- `work/allwin_r63.py` (unfiltered windows): `len orig=404 prod=401 delta=-3`, **hunks=5**:
  ```
  #1 replace orig[52..53 @362] prod[52..59]  del=1 ins=7   (POP_JUMP_FORWARD_IF_TRUE → IF_FALSE + time.sleep(60))
  #2 insert orig[70..70 @520] prod[76..113]  ins=37        (@560 RETURN_VALUE …)
  #3 insert orig[71..71 @522] prod[114..291] ins=177       (receive_*_response_flag body)
  #4 delete orig[90..151 @700..@1210]        del=61        (sleep + the whole tail re-test chain)
  #5 delete orig[235..397 @1890..@2884]      del=162       (pre<=t<post region)
  ```
- r71a's criterion re-derived and re-verified on today's bytes: see §2 census (FIRES=1, unique).

**Structural ground truth** (`work/orig_all.txt` = `dis.dis` of the original `_sync_worker`,
authoritative because CPython resolves the jump operands itself — my first hand-computed dump
`work/orig_loop.txt` had WRONG targets and was discarded; Rule 5 trap):

```
@230 NOP (source line 1376 `while True:`)
@232 A: int(datetime.now().strftime('%H%M')) < pre_before_trading   @362 POP_JUMP_FORWARD_IF_TRUE → @704
@364 B: int(...) >= int(post_after_trading)                         @520 POP_JUMP_FORWARD_IF_TRUE → @704
@522 C: holiday_sync_account == '0'                                 @542 POP_JUMP_FORWARD_IF_FALSE → @702
@544 D: not self.engine.data_proxy.is_trading_date(...)             @698 POP_JUMP_FORWARD_IF_TRUE → @1214
@700 JUMP_FORWARD → @704 (and-group true)      @702 JUMP_FORWARD → @1214 (condition false = loop exit)
@704 body: time.sleep(60) … (the block CONTAINS the first re-test leg A′: @874 POP_JUMP_BACKWARD_IF_TRUE → @704)
@876 B′: @1032 POP_JUMP_BACKWARD_IF_TRUE → @704     @1034 C′: @1054 POP_JUMP_FORWARD_IF_FALSE → @1212
@1056 D′: @1208 POP_JUMP_BACKWARD_IF_FALSE → @704   @1210 JUMP_FORWARD → @1214   @1212 NOP → @1214
@1214 exit (line 1392 …) … @2928 JUMP_BACKWARD → @232 (the `while True` back edge)
```
⇒ the source is `while True: while A or B or (C and D): time.sleep(60); …` and CPython 3.11
**duplicates the compound test**: @232/@364/@522/@544 = the entry guard copy,
@704(tail)/@876/@1034/@1056 = the re-test copy. Judge equality therefore requires the product to
emit ONE `while` statement whose compilation reproduces BOTH copies; the re-test legs must not be
emitted as statements (this is r71a's co-requisite 2), and the guard copy must be folded into the
loop test (r71a's co-requisite 1).

**Premise correction vs the brief (measured, `work/regions_base.txt`)**: the block memberships on
today's bytes are the *reverse* of what a "pure reclaim" story predicts. The compound while is
already its own `LoopRegion`:
```
LOOP cond=232 hdr=704 entry=232 back=704 nbody=5 blocks=[232, 704, 876, 1034, 1056, 1212, 2064, 2066, 2168]
LOOP cond=None hdr=232 entry=232 back=2886 (the enclosing `while True`) owns 364, 522, 544, 700, 702, 1210
```
So the loop region owns the **re-test legs** (876/1034/1056/1212) plus three *foreign* blocks
(2064/2066/2168 = the second while's chained-compare merge/POP_TOP tail), while the **guard-chain
legs 364/522/544 (+ connectors 700/702/1210) belong to the parent `while True` LoopRegion**. That
is exactly why the base product renders `while int(t) < pre_before_trading:` (only block 232 is the
loop's own condition) with the remaining guard legs spilled into the body as
`return int(t) >= int(post)` / `if holiday_sync_account == '0': continue` / `is_trading_date(…)`
(product lines 857–864), and the re-test legs as `while int(t) < pre: pass` +
`if holiday…: if not is_trading_date…: pass` (lines 884–888).

Consequence for the ticket: r71a's BoolOpRegion is not only *reclaimed* by the
`block_to_region.clear()` + priority rebuild (`region_analyzer.py:1871`, `:4119`); its operand
blocks are also **not members of the loop that owns the condition**, so the fold path needs the
guard *and* the loop's own chain membership. §2–§5 measure which of the two actually actuates.

## §1 — the two halves as designed

**A (r71a's identification criterion, re-derived today)** `_r2144_detect_while_condition_nested_or_and`
= structural mirror of the landed `[R7-B45]`, returns `[(232,'or'),(364,'or'),(522,'and'),(544,'and')]`.
Candidate sha16 `0d568cdd7fe0f167` reproduced byte-exactly from the landed bytes by
`build_cand_r79a_r2150.py` (asserts base sha16, each anchor exactly once, `py_compile` OK).

**B1 (reclaim guard, analyzer)** — mirror of the landed `elif_boolop_entry_blocks` clause that
already exists at BOTH rebuild sites (`:1879-1882`, `:4127-4130`). New set
`while_cond_boolop_entry_blocks`: for every `BoolOpRegion` whose `entry` is *declared* by some
`LoopRegion` as its `condition_block`, its `op_chain` blocks are condition-context operand blocks;
at the rebuild the BoolOpRegion keeps them (and an existing BoolOpRegion keeper is not displaced).
Judged purely by region data (`LoopRegion.condition_block`, `BoolOpRegion.entry`,
`BoolOpRegion.op_chain`) — no offsets, no names, no priority-table edit.

**B2 (back-edge fold)** — the loop's re-test legs must be consumed as the back edge. Measurement
target: with A+B1 the guard chain folds; what remains of the re-test emission is decided in §4.

## §2–§6 — census, 2×2, panel, verdict: APPENDED AS MEASURED (see below)
