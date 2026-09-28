# R75 · fix1（修复工程师）BRIEF —— F-ABSORB 61 单元（残留最大族）

## 0. 使命与工作区

工作区：`D:/Temp/opencode/r75gate/fix1`；基线 HEAD = **`982cd398`**（R74 落地 m74）。
目标：在**同层次结构身份判据**上给出可判据的吸收（absorb）类修复，mandate 候选 =
`klinedata` 61/64→64/64（3 单元）、`wizard_quant_api` 55/58→58/58（3）、`order_api` 34/37→37/37（3）、
`jq_trans_module` 63/65→65/65（2）、`real_quote` 43/45→**45/45**（2）。

## 1. 靶单元（61，来自 `center/fam75.json`；按文件聚合见 `dump/fail_units75.txt`）

- trade_live_broker 11（`on_pre_before_trading_start`、`_process_order`、`_process_tick_order`、
  `_process_cancel_order`、`_trade_status_handle`、`rzrq_credit_order`、`ipo_stocks_order`、
  `get_ipo_stocks`、`on_order_response_list_handle`、`on_trade_response_list_handle`、`etf_purchase_redemption`(bytecode)）
- quote 8（`build_current_period_df`*、`load_bars_from_hundsun`*、`change_his_to_forward`、
  `change_his_to_backward`、`get_price`、`get_real_from_zeromq`、`run_individual_transform`、`get_individual_data`；* = Different bytecode）
- klinedata 3、wizard_quant_api 3（`filter_desicion` + 2×`<genexpr>`）、order_api 3
  （`base_order`/`future_order`/`option_order`）；
- trade_info_utils 2（`trade_operation`[IN]、`get_trade_status`）、jq 2（2×`replace_args`）、
  real_quote 2（`get_real_minute_kline`[IN]、`get_tick_direction`[OUT]）、risk_calculation 2、
  future_contract_info 2、ptradeAccount 2；其余 21 支各 1。

## 2. 必答问题（逐单元给可复现读数）

1. **首分歧定性**：`dump/firstdiv75.txt` 每行给了 `idx/off/origTryDepth/prodTryDepth`，`fam75.json` 给了
   `lenA/lenB/firstA/firstB/lineA/lineB`。逐单元判定属于哪一类子机理：
   a. **共享尾/共享 else 被吸收进上层 region**（absorb shared exit）；
   b. **孤儿子块未发射**（orphan child region，R74 已修一类：`and region.entry in _ft3_rr.blocks`）；
   c. **跳转目标指令不同**（target 落在不同 instr：多为 region 边界/布尔短路归约差）；
   d. **纯位移**（target 相同、仅 offset 平移 → 必须 Σ|Δ| 不升）；
   e. **bytecode-only**（`EXTENDED_ARG`/`NOP` 差，不涉 region 归约 → 交中心判是否 ADR-1 外）。
2. **`real_quote.get_tick_direction`（R74 拒收点）**：给出 `hunks_norm 2→3` 的第 3 个 hunk 具体是什么、
   为什么 absjt/absj9 会多出它、本批如何避免（必须在自测中证明 `hunks_norm` 不升）。
3. **`trade_operation` target_diff #94**：JUMP 终点差异在哪条指令、属于 a–e 哪类。

## 3. 修复与拆分

- 只允许在 **F-ABSORB 判据**上出 spec：`region_analyzer` 的区域识别/归约、
  `region_ast_generator` 的子块与共享尾发射。单臂单 edit（`specs/abs8_<n>.json`），最后合并臂 `abs8m`。
- 闭环（每臂）：
  a. `mbuild75.py <arm> specs/<x>.json` 锚点断言全过；
  b. 官方 41 靶 `h62.py run --arm=<arm> --list=list41.txt` **逐项不回退**；
  c. mandated focus（`klinedata`/`wizard`/`order_api`/`jq`/`real_quote` 逐支
     `pyc_verify.py single --source build_<arm>/…`）：**至少 1 支 failure→success（mandate）**，其余单元
     只减不增、**零新生失败**；
  d. 金丝雀 4 支 sha16 == pin；`closeout69.py battery landed <arm>` worse=0；
  e. `sstrict67.py build_<arm> <dump/fail_units75 对应缺陷名单> out` 新增缺陷 0。
- synth：每类子机理 ≥1 条最小复现 + 1 条负例（负例 sha 必须与落地逐字节相同）。

## 4. 硬规则

不改 repo（`land75` 只 dry-run）；不手改 `*OK.py`；每条命令 <300s；
ALLOWED = `region_analyzer.py` / `region_ast_generator.py` / `comprehension_generator.py`；
spec 三要素注释 + 同层结构身份判据（无函数名/文件名/偏移阈值/名字白名单/新增 self 状态/
跨层 `region.entry in r.blocks`）；**任何他支回归即整件拒收**；h62 列表 LF 无 BOM；产物名 `:` → `_`。

## 5. 交付

`FACTS.md`（61 单元 a–e 子机理归属表、每项 a–e 读数、与 fix2/fix3 重叠面、`get_tick_direction` 解剖）、
`specs/*.json`、`synth/`、`dump/` 原始读数。
