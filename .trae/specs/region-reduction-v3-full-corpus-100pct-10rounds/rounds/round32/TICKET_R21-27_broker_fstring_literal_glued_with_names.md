# R21-27 — broker `etf_purchase_redemption`: identifier names glued INTO the f-string literal

This is the unit the ledger carried as "#24 f-string literal fragments assembled with foreign identifiers,
1 unit, mechanism newly proven" but never located. It now has a product line, a disassembly window, and two
candidate root sites. Do not re-derive those.

Victim: `site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc`, co-name
`etf_purchase_redemption`. Sealed shape (gate 31 bytes): `len orig=426 prod=414 delta=-12 hunks=5 landings=0
judge_diff=True`. The file is 121/128 and this is one of its seven independent mechanisms, so a fix here is
a **unit flip (121→122/128)**, not a file flip. Note engineer r54a is working another unit of this same file
(`get_ipo_stocks`, `landings=1`) — different mechanism, do not merge the two into one criterion.

## 0. The defect, straight out of the emitted file

`site-packages/IQEngine/plugins/plugin_system_trade/trade_live_brokerOK.py:1596` emits

    return f"list_info00orderstrresultentrust_noselforderorderselfstrorderselforderselforderstrategy_log_生成订单，订单号：{order!s} 代码：{order!s} 数量：order{...}"

The literal prefix is a run of **variable names** (`list_info`, `order`, `str`, `result`, `entrust_no`,
`self`, `strategy_log`, …) glued into the constant, and a second constant is polluted the same way
(`' 数量：order'`). The original has none of that:

    - @2274 LOAD_GLOBAL  NULL + strategy_log     (so the statement is strategy_log.info(f'…'), not a `return`)
    - @2286 LOAD_ATTR    info
    - @2296 LOAD_GLOBAL  NULL + _
    - @2308 LOAD_CONST   '生成订单，订单号：'
    - @2312 LOAD_ATTR    order_id                 (one of three lost attribute loads)
    - @2328 LOAD_ATTR    symbol
    - @2340 LOAD_CONST   ' 数量：'
    - @2424 PRECALL / @2428 CALL / @2438 PRECALL / @2442 CALL / @2452 POP_TOP
    - @2454 LOAD_FAST order / @2456 LOAD_ATTR order_id

The five hunks are: `replace` @2274..@2308 (four instructions → the one glued constant), two `delete`
hunks of one `LOAD_ATTR` each (`order_id`, `symbol`), one `replace` where the constant absorbs `order`, and
a `delete` of seven instructions (two `PRECALL/CALL` pairs + `POP_TOP` + `LOAD_FAST/LOAD_ATTR`). So within
one unit there are at least two distinguishable defects: **the literal assembly** and **lost call
expressions**. Separate them, say which one your criterion closes, and report the remaining hunks honestly.

## 1. Candidate root sites (current sealed bytes, `37d9fecb893704ac`)

- `region_ast_generator.py:50309` `_fstring_parts_from_segment(self, seg, fv_instr=None)` — assembles literal
  + value parts; the name-glue most plausibly comes from a fragment loop that appends operand `argrepr`
  (names) as well as real literal text.
- `region_ast_generator.py:50869` — "Build JoinedStr from chained ternaries + literal parts".
- `region_ast_generator.py:50490` `_try_wrap_fstring_pending_call(...)` — the pending-call wrapper, the other
  half if the lost `PRECALL/CALL` pairs are the same route.
Downstream conversion exists in `ast_converter.py:1461 _convert_joined_str_full` /
`code_generator.py:4795 _generate_joined_str`; verify where the corruption is introduced rather than
assuming — the emitted *source text* already contains it, so the defect is upstream of `code_generator`.

## 2. Census duty

`grep -rl "selforderorderself" site-packages --include=*.py` returns exactly **one file**. So do not claim a
family from this unit; measure the *predicate's* population (how many regions corpus-wide satisfy your
criterion) and how many products change. If the predicate fires in files whose output is currently correct,
narrow it or report it as negative evidence.

## 3. Method requirements

- Prove the emission site by ablation, not by reading: stub the candidate builder so it returns `None` in the
  process that produces the artifact and show which stub removes the glued constant. Line-print markers miss
  multi-line dict literals in this file.
- Any probe must be `cmp`-proved inert per target; an empty probe log means the rig is broken.
- Decide what the correct shape is by `compile()`-ing candidate source on 3.11.7 and comparing the
  instruction table against `@2274..@2456`.
- `break`/`continue`/`return` inserted into a suite makes CPython ≥3.10 dead-code-eliminate the rest of it —
  verify emitted bytes.

## 4. Acceptance bar

- `etf_purchase_redemption` reaches `delta=0 hunks=0 landings=0 judge_diff=False` and the judge names it
  Equal → broker **122/128**. If only the literal half closes, report the residual hunks with their shapes
  and declare honestly; a shrink with no flip is a measured negative, not a candidate.
- 20-file pre-gate panel with zero decreases — `python -X utf8 D:/Temp/t30/panel14.py <root> <tag> 0 20`
  (quotation 153/153, quote 91/92, klinedata 64/64, handlers 29/30, wizard 58/58, trade_info_utils 40/41,
  api_base 28/28, real_quote 45/45, strategy 27/27, order_api 37/37, broker 121/128→122/128, matcher 17/17,
  realtime_event_source 12/13, risk 43/43, canaries `arg_checker`×3 = 49/39/43, `profiler_func`×3 =
  17/15/18). The six canaries are mandatory: a −6-unit merge passed a 14-file panel at gate 31 and only the
  gate saw it.
- The other six broker units' shapes must be reported before/after (`_process_order −465/4/1`,
  `_process_cancel_order −293/3/0`, `_sync_worker −3/5/6`, `_trade_status_handle −3/3/2`,
  `ipo_stocks_order −1/1/3`, `get_ipo_stocks 0/0/1`) — perturbing them is a regression even if counts hold.

## 5. Constraints

Base = generator `37d9fecb893704ac`, analyzer `35e227ac3e7b25af`; UTF-8 BOM + mixed CRLF/LF → read
`utf-8-sig`, patch byte level, never re-encode. Repo READ-ONLY, no git write commands. `python -X utf8`,
never `PYTHONIOENCODING`. Nothing over 300 s. Scratch `D:/Temp/r56/`. Only
`core/cfg/region_ast_generator.py` may change; if the fix belongs in `ast_converter.py` /
`code_generator.py`, write that up as the next ticket instead of editing them. Deliver a whole
`CANDIDATE_region_ast_generator.py` with its `sha256sum | cut -c1-16` plus `FIX_R21-27.md` (sections 0–7;
section 5 must include the panel table, the corpus byte census, and the six other broker units unchanged).
