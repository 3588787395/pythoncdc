# TICKET R21-19 (round 30) — a short-circuit chain's shared true-exit lands on the wrong block (api_base + strategy, both one unit from green)

Owner file: pick ONE and state it — `core/cfg/region_ast_generator.py` is the expected site (chain test
assembly), `core/cfg/region_analyzer.py` if your measurement lands on a declaration.
Repo (READ-ONLY): `D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main`, branch `rr-v3r01-f557fd`, HEAD `544b81fb`.
Sealed bytes: `region_ast_generator.py = fd0e4c4d73cf5efc`, `region_analyzer.py = 35e227ac3e7b25af`,
`ast_generator_v2.py = beeaf14435e22922`, `comprehension_generator.py = 7d8acab92ccc7782`.
Mirror `D:/Temp/r37/wt`, products `D:/Temp/r37/out/`. No git writes, no repo writes.
Three siblings are running (`r40a` analyzer, `r41a`+`r42a` generator) in `D:/Temp/r34|35|36` — do not
read or write there; you all start from the same HEAD bytes.

## 0. Two victims, each the ONLY failing unit in its file ⇒ each flip is a whole-file flip
```
IQEngine/plugins/plugin_fly_data/strategy/strategy.pyc  :: <module>.Strategy.tick_worker_thread   file 26/27 -> 27/27
   len orig=288 prod=288 delta=0 hunks=0 landings=4 judge_diff=True
IQData/api/api_base.pyc                                 :: <module>.get_history_df                  file 27/28 -> 28/28
   len orig=1881 prod=1881 delta=0 hunks=0 landings=2 judge_diff=True
```
ZERO content difference — every instruction matches, only jump TARGETS differ. That is why the cheap
"content" axes do not apply here and why nothing has landed on these two in five attempts.

## 1. Measured signature (my own readings, 17:27)
strategy, the `or` chain around the time-window test (all four diffs):
```
orig idx69 @516 COMPARE_OP >            (dt_strf > '15:15:00')
orig idx70 @522 POP_JUMP_FORWARD_IF_TRUE -> off568 idx87      | prod -> off820 idx153
orig idx73 @528 COMPARE_OP <            (dt_strf < '08:30:00')
orig idx74 @534 POP_JUMP_FORWARD_IF_TRUE -> off568 idx87      | prod -> off820 idx153
orig idx180 @992 / idx184 @1004  same pair, both -> idx197 in orig, both -> idx263 in prod
```
api_base:
```
orig idx193 @994 POP_JUMP_FORWARD_IF_TRUE -> idx219 | prod -> idx254
orig idx197 @1006 POP_JUMP_FORWARD_IF_TRUE -> idx210 | prod -> idx254
```
Read it precisely: the chain's legs agree with each other in BOTH builds (strategy: both legs share one
target; api_base: prod merges two targets into one) but the shared target moved LATER, past a block the
original ran first — and in api_base the original's two legs land on **two different** blocks
(idx219 vs idx210) while the product sends both to one (idx254). So the emitted source reorders or
merges what CPython had as separate, interleaved exits: the original body between `@568` and `@820`
(strategy) is on the chain's true path, the product put it elsewhere while keeping the instruction
sequence identical.

## 2. What to find
Which shape reproduces the original? Compile candidate sources on 3.11.7 and compare the instruction
list AND the resolved targets (this is the only trustworthy oracle here — a chain written as
`if A or B: body` vs `if A: body elif B: body` vs nested ifs produces different targets with the same
multiset). My landed gate-29 criterion in `_if_generate_elif_chain`
(`_inline_and_chain_exits_agree`, refusing an `and`-lift when the legs' exits disagree) is the
neighbouring mechanism and may be the wrong way round for these two regions: check whether the chain
these units carry is an `or` whose legs' exits are currently being *merged* (api_base shows exactly that
merge, 219/210 → 254), and whether refusing the merge restores two distinct targets.

## 3. Acceptance (quote literal rig output; `unit_diff.py <rig>` with `--all`)
- `strategy.tick_worker_thread` → `len orig=288 prod=288 delta=0 hunks=0 landings=0 judge_diff=False`, judge `Equal`, file **27/27**.
- `api_base.get_history_df` → `len orig=1881 prod=1881 delta=0 hunks=0 landings=0 judge_diff=False`, judge `Equal`, file **28/28**.
Landing ONE of the two is enough for a candidate (one file flip); say which. Landing neither is a
measured negative — deliver the 取证, which is the point of this ticket.

## 4. Anti-regression duties (mandatory before any candidate)
1. Fire census of your criterion over the 14-file panel used in round 29 (`fly/data/quotation.pyc`,
   `fly/data/quote.pyc`, `IQCommon/{api/klinedata,logger/handlers,strategy/wizard_quant_api,util/trade_info_utils}.pyc`,
   `IQData/api/api_base.pyc`, `IQData/plugins/plugin_system_realquote/real_quote.pyc`,
   `IQEngine/plugins/plugin_fly_data/{strategy/strategy,fly_api/order_api}.pyc`,
   `IQEngine/plugins/plugin_system_{trade/trade_live_broker,matcher/matcher,event_source/realtime_event_source}.pyc`,
   `IQEngine/plugins/plugin_system_risk_calculation/__init__.pyc`): report `TOTAL_FIRES` and per file
   whether its product changed — compare against `git show HEAD:<path>` bytes with CR stripped, NEVER
   against the checked-out file (checkout is CRLF, the decompiler writes LF: a `cmp` there reads DIFF on
   everything and produced a false claim in round 29).
2. `fly/data/quotation.pyc` stays 153/153; `order_api` 37/37; `matcher` 17/17.
3. No count may drop: `klinedata` 63/64, `handlers` 29/30, `wizard_quant_api` 58/58, `real_quote` 45/45,
   `trade_info_utils` 38/41, `quote` 91/92, `broker` 121/128, `realtime_event_source` 12/13,
   `risk_calculation` 42/43.
4. The generator has **no jump-operand channel** (it emits AST/source) — a criterion that "sets the tail
   jump to the declared merge" is structurally unexecutable there (three tickets proved it: see
   `rounds/round20/ADJUDICATION_R20_MERGE_LANDING_FALSIFIED.md`). Express everything as a source shape or
   an analyzer declaration, and prove it with `compile()`.
5. Probes: `cmp`-prove each probe inert per target or the reading is VOID; an empty log = broken rig
   (this file holds 71 `'type': 'Break'` literals, so sampled line probes read zero fires). Use the
   proven-inert line tracer `D:/Temp/t30/tracbreak.py` or ablation in the producing process.
6. Judge by diff SHAPE; `delta=0` with `landings>0` is still a failure.

## 5. Known walls, do not spend the run on them
The identification-order wall: `_identify_conditional_regions` walks `get_blocks_in_order()` ascending,
so parents are identified before children and there is no cross-IfRegion claim set (round 20 write-up
`rounds/round20/NOTE_T20_ORDERING_WALL.md`); a stop-set patch there gave zero flips and four
regressions. And this pair has already absorbed r20d's explicit-edge criterion (fires, zero byte change).

## 6. Deliverable
`D:/Temp/r37/DELIVER/FIX_R21-19.md` (0 ticket, 1 mirror+hash+cmp proof, 2 baseline, 3 取证 naming the
function that assembles these chain exits with file:line and the code you read, 4 criterion, 5 post-patch
+ fire census + quotation + panel, 6 negative evidence, 7 declaration) plus
`D:/Temp/r37/DELIVER/CANDIDATE_<file>.py` (whole file, its `sha256sum | cut -c1-16`) only if §3 is met
with no panel regression. `python -X utf8`, never PYTHONIOENCODING, ≤300 s per command, scratch by
absolute Windows paths, CRLF-preserving textual patches only.
