# Gate 34 adjudication and landing record

Landed file: `core/cfg/region_ast_generator.py` `pre=fcf2b870f0fb71b3` → **`065e4d77243190dc`**
(R21-28: one 19-line hunk at 13252..13270 inside `_is_loop_tail_convergence_block`, byte-level build
`build_cand_r34b.py`, BOM + all-CRLF preserved, 0 bare LF, `py_compile OK`). **Three** products moved
corpus-wide (`git diff --numstat`): `trade_live_brokerOK.py` +1 (the flip's `continue`),
`fly/common/flytoolsOK.py` +1 (`process_filter @1236`, a qualifying site whose unit was already Equal), and
`trade_info_utilsOK.py` +2/−1 — in `get_trade_list` the arm gained a second, already-unreachable `continue`
and the following `elif` was re-rendered as a plain `if`. Its units held 41/41, so the compiled stream is
unchanged, but the emitted text is redundant and is registered here instead of being passed off as clean.

## 1. Certified numbers (`gate_chain.py 34 33`, all four stages rc=0)

- regen `ok=402 bad=0` (259 s), verify (161 s)
- report: **units 6609 → 6610 /6617 (99.8942%), files 399 → 399**,
  `文件级回退=0 UNIT_REGRESSIONS=0 新增失败单元=0 翻正单元=1`
  - FIXED `trade_live_broker.pyc <module>.TradeLiveBroker.ipo_stocks_order` → **122 → 123/128**
- checks (99 s): quotation **153/153**, small34 `units_success 1561 / success 31` (+1 unit, moved by
  exactly the flip count), ruler selfcheck OK (both mutation arms caught 1/153),
  pytest `2 failed, 282 passed, 2 xpassed` (the two registered residents)
- sealed residual: **3 files / 7 units**, `UNREGISTERED 行数=0` (`RESIDUAL_ROUND34.md`)

## 2. The defect, in one line

`ipo_stocks_order` was `delta=-1 / 1 hunk / 1 landing`: the arm

```python
if stock_type == 'Y':
    if submarket_type in ('4', []):
        strategy_log.error('账户无可转债交易权限，代码【%s】无法进行新股申购业务' % stock_code)
    continue                      # ← dropped
```

lost its arm-tail `continue`. The bytecode proves the `continue` is a real source statement, not a
jump-threading artifact, by the asymmetry of the nested condition's three exits: `stock_type != 'Y'`
leaves the whole chain (`@3512 → @3576 → @3640`) while `submarket_type not in ('4', [])` lands directly
on the back-edge (`@3524 → @3572`), and no `and`-chain can compile that way. Inserting the one line into a
copy of the sealed product measured `delta=0 hunks=0 landings=0 judge_diff=False`, which fixed the target
shape before any generator was touched.

## 3. Why the shipped rule dropped it

`_is_loop_tail_convergence_block` (P1-3b, "显式 Continue 冗余抑制") suppresses the `Continue` whenever a
back-edge block has ≥2 in-body predecessors. The hand-off comment at the call site
(`region_ast_generator.py:26886-26887`) states the load-bearing assumption:
"真显式 continue 块只有 FOR_ITER 单前驱，不会被它误伤". The victim is an explicit `continue` with **two**
predecessors — `@3514` (the nested if's false edge) and `@3526` (its then-body fall-through) — because the
continue block doubles as the nested region's merge. The assumption is false, so the statement vanished.

## 4. The criterion, and the measurement that shaped it

v1 (**interior-only** conjunct, `724f1843f9522fec`) was built, panelled and **rejected on measurement**:
broker 122→123 but `quote.pyc` 91→**90** and `real_quote.pyc` 45→**44** — net −1 unit. Both damages are
blocks that **carry statements** before their back-edge (`quote @1818` = `index.append(temp_time)` + jump);
adding `continue` there makes the instructions after it unreachable and CPython deletes them
(compiled unit measured `518 → 504`). That is the gate-31 over-fire mode repeating, and the panel caught it
before the gate.

v2 (`065e4d77243190dc`, installed) denies the suppression only when the block has **none** of the three
facts that let a recompiled loop regenerate the jump itself:

1. it is not the enclosing `LoopRegion`'s declared `back_edge_block` / member of `back_edge_blocks`;
2. it is not the loop body's terminal block in offset order;
3. it carries no statement payload (`EXTENDED_ARG` is an operand-width prefix — the victim block is
   exactly `[EXTENDED_ARG, JUMP_BACKWARD]`).

All three read only the block's own instructions and this loop region's own fields: no cross-region scan,
no name/file/offset literal, no counter state.

Population (read-only census `census_r34_loop_tail.py` over the verification face):
`543 convergence hits → 479 terminal → 64 interior → 41 interior-payload-free → 24 qualifying`.
Controls on the 24: victim `broker @3572` **in**; `quote @1818`, `real_quote @1464`, `handlers._target @200`
**out**. Forensics for both sides are in `FIX_R21-28_r34.md` §3 and `forensics_r34.py`.

## 5. Panel before the gate (20 files, `PANEL_R34.md`)

Exactly one file gained units (broker +1) and none decreased; `trade_info_utils.pyc` changed bytes while
holding 41/41 (six of its blocks qualify; the inserted continues compile to the same instruction stream).
`quote`, `real_quote`, `quotation`, `klinedata`, `handlers` and all six duplicated-module canaries came back
byte-identical. Recorded rather than smoothed over, because a product that moves without a unit change is
the shape that turns into a regression the next time the criterion is widened.

## 6. Banked, not landed, entering gate 35

- M1 `01970a924b74afb4` (clock_worker −113→−10, needs re-anchor onto this base), M2 `36dea812a1f9c180`
  (measured worse alone; re-measure on the merged base still open), M3b `3aa27a55eff25a80`
  (+23 lines at :19918, unmeasured).
- r58a `8a6272f9bdae6ec4` (panel-clean falsified-for-flips) with the named R58B analyzer re-parent follow-on.
- r46a's quote analyzer half (`delta −52→0`, hunks 3→2, still 91/92).

## 7. Next gate

Label **35** against `rounds/round34/after`. **7 units in 3 files**: `trade_live_broker` 5
(`_process_order`, `_process_cancel_order`, `_trade_status_handle`, `_sync_worker` — NOTE_R21-31 relocation
with polarity flip + call migration, `etf_purchase_redemption` — R21-27 f-string name-gluing with three
named root sites), `realtime_event_source.clock_worker` 1, `quote.run_individual_transform` 1.
Session arc: gate 30 6603 → 31 6606 → 32 6608 → 33 6609 → **gate 34 6610 / 6617 (99.8942%)**, 399 green files.
