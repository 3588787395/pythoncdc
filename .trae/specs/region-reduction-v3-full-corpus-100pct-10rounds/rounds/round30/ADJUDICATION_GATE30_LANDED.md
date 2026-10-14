# Gate 30 adjudication and landing record (orchestrator-measured)

Landed file: `core/cfg/region_ast_generator.py` — `pre=fd0e4c4d73cf5efc` → `post=7d336164eff5bf65`
(+296 lines, 13 additive hunks, installed byte-level with `install_deliver.py`, `py_compile OK`).

## 0. What was installed and why it is three criteria, not one

Four engineers produced four generator candidates this round. I measured every one of them **in my own
mirrors** (`D:/Temp/r30chk`, `D:/Temp/r30chkB`, both re-proven to reproduce the sealed products before
use) and never took an engineer's word for a reading:

| cand | author | sha16 | hunks (base lines) | victim reading alone | panel alone |
|---|---|---|---|---|---|
| A | r42a (turn-capped, no report) | `203369154e43eb50` | 308, 6912, 7992, 7994, 8006, 8013, 8372 | `risk _save_testds_to_csv` `delta=0 hunks=0 landings=0 judge_diff=False` → **43/43** | quotation 153/153; handlers/real_quote byte-shift, counts held |
| B | r43a | `83d1441666664dd7` | 18907, 24248 | `strategy Strategy.tick_worker_thread` `0/0/0` → **27/27** | only strategy changed, 13 products byte-identical |
| C | r41a | `535b1d0dcb54791c` | 21961, 25951, 25957 | `klinedata get_kline_by_count_new` `0/0/0` → **64/64** | its own census: klinedata + broker (same shapes) |
| D | r44a | `691e5aa4f57065d8` | 1963 | `handlers TWHThreadController._target` `0/0/0` → **30/30** | 1/14 changed |

A, B, C, D have **pairwise disjoint base line ranges**, so I merged by base coordinates
(`D:/Temp/t30/mkmix.py`, asserts on overlap) instead of serializing four gates. The A+B merge and the
A+B+C merge were each panelled before installation; both were clean.

## 1. The measured negative that decided the landing set: D collides with A

`REJECTED_GATE30_quad_region_ast_generator.py` (`a304ab6887f71dfc`) = A+B+C+D. Its 14-file panel read
`handlers 29/30`, i.e. **D's flip is suppressed when A is present**. Pair probes isolate the conflict:

| build | `handlers` |
|---|---|
| D alone | **30/30** |
| B + D (`p3744`) | 30/30 |
| C + D (`p4144`) | 30/30 |
| A + D (`p3644`) | **29/30** |

So A's change to the `while`/else emission alters the CFG facts D's precondition reads (`merge_block ==
next top-level IfRegion's condition/entry` plus the single-pred `pure-none` per-edge landing test at
`region_ast_generator.py:1963`), and D stops firing. Landing the quad would therefore buy **exactly the
same three flips as the triple** while carrying 67 lines that no longer actuate — so the triple landed
and D is banked with the collision recorded (`FIX_R21-20_r44a_NOT_LANDED.md`,
`TICKET_R21-23_handlers_flip_suppressed_by_R21-14.md`).

## 2. R21-14 (risk) — ablation proves two co-requisite halves, and one is a spec deviation

Candidate A alone flips the file; each half alone does not:

| build | `_save_testds_to_csv` | file |
|---|---|---|
| sealed (gate 29) | `delta=-7 hunks=3 landings=3` | 42/43 |
| wrapper rule only (`_r2114_wrapper_is_sequential_loops`, `:6973`) | `delta=-6 hunks=1 landings=1` | 42/43 |
| defer rule only (`_r2114_defer_to_unemitted_sibling_loop`, `:8451`) | `delta=-3 hunks=2 landings=1` | 42/43 |
| both | `delta=0 hunks=0 landings=0 judge_diff=False` | **43/43** |

Registered deviation: the defer half decides by scanning `gen.regions` for an unemitted sibling
`LoopRegion` that lists the block in its `body_blocks` — a **cross-region read at generation time**,
which the reduction rules forbid. It exists only because the analyzer over-claims
(`LoopRegion@108` declares 292/296/350, which are `LoopRegion@262`'s body), violating "each block unique
membership". That root cause is filed as **R21-22** with this ablation table as its acceptance oracle.

## 3. Gate 30 numbers (the only certifying measurement)

`gate_chain.py 30 29` — all four stages rc=0:

- regen `ok=402 bad=0` (8 shards, 231 s)
- verify (159 s): shard ratios 785/786, 465/469, 538/538, 887/887, 855/855, 998/999, 794/801, 1281/1282
- report: **units 6600 → 6603 /6617 (99.7884%), files 393 → 396**,
  `文件级回退=0 UNIT_REGRESSIONS=0 新增失败单元=0 翻正单元=3`;
  FIXED = `klinedata.get_kline_by_count_new`, `strategy.Strategy.tick_worker_thread`,
  `plugin_system_risk_calculation._save_testds_to_csv`
- checks (104 s): quotation **153/153**, small34 `units_success 1554 / success 28`, ruler selfcheck OK,
  pytest `2 failed, 280 passed, 2 xpassed`

The two pytest reds are the long-registered residents, named from my own re-run of the same seven
suites: `tests/test_algorithm_correctness.py::TestDominanceFrontierIf::test_B01_simple_if_then_else_merge`
and `tests/test_deep_nesting_pressure.py::TestBoundaryConditions::test_BOUNDARY_02_large_function`
(both appear in `rounds/round1/FIX_*.md` and `rounds/round10/VERIFICATION.md` as pre-existing).
No third red, no new red. (My first attempt at naming them ran bare `pytest tests`, which dies on the
`tests/nook` collection errors — a broken rig, not a result.)

Sealed residual table: `RESIDUAL_ROUND30.md` — **6 files / 14 units**, `UNREGISTERED 行数=0`.
Corpus files whose product bytes changed while counts held: `handlers`, `real_quote`, `trade_live_broker`.

## 4. Next gate

Label **31** against `rounds/round30/after`. Remaining 14 units in 6 files:
`quote.run_individual_transform` (1), `realtime_event_source.clock_worker` (1), `api_base.get_history_df` (1),
`handlers._target` (1), `trade_info_utils` (3), `trade_live_broker` (7).
Banked, un-dispatched: R21-21 (trade_info_utils +2 units, not a file flip), R21-22 (analyzer loop overlap),
R21-23 (handlers flip suppressed by R21-14), and r43a's pre-digested api_base shape
(`if not include and (test2 or test3): B` **with** `else: <T chain>` → `0/0/0`; variants measured and
rejected: sibling-T `delta=-1`, or-merge-only `landings=1`).
