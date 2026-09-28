# R75 · fix3（修复工程师）BRIEF —— inside-try 9 单元（按用户裁定走 try/except 归约路径）

## -1. 裁定与读数

用户裁定（R73 `b355043e`，R74 已定量复核）：**剩余控制流失败的根因就是「嵌套 try-except 问题」**。
R75 基线读数（`center/dump/{crosstab75,tryverdict75,exctable_diff75,firstdiv75}.txt`）：
71 失败单元中 **首分歧在异常区内 9 个、区外 62 个**；原 pyc `with_et=36 且 nest=0`（原表无嵌套），
产品 `product_nested_try=67`（深度≥2 者 30）。
**本批按裁定对 9 个 inside-try 单元全力攻坚**；区外 62 个由 fix1/fix2 承担。

## 0. 使命与工作区

工作区：`D:/Temp/opencode/r75gate/fix3`；基线 HEAD = **`982cd398`**。
目标：在 try/except 归约路径上给出**可判据的修复**并补齐 R74 缺失的交付闭环
（`FACTS.md` + 合并臂 `trym`），mandate 候选 = `real_quote.pyc` 43/45 → **45/45**
（`get_real_minute_kline` 为 IN 单元，`get_tick_direction` 为 OUT 单元，两者都过才成 success）。

## 1. 靶单元（9，来自 `dump/crosstab75.txt`）

| 文件 :: 单元 | 家族 | et | 备注 |
|---|---|---|---|
| `IQData/…/real_quote :: get_real_minute_kline` | F-ABSORB | 7 | **mandate 路径 IN 单元** |
| `fly/data/quote :: run_tick_socket` | F-PAD | 13 | 与 fix2 重叠，标注证据交中心 |
| `IQCommon/util/trade_info_utils :: trade_operation` | F-ABSORB | 18 | **R70 遗留 target_diff #94** |
| `IQCommon/data/finance :: get_fields` | F-ABSORB | 8 | strict `target_diff #19` 关联 |
| `IQCommon/util/email_utils :: send_email` | F-ABSORB | 5 | 首分歧在 handler 出口 |
| `fly/common/flytools :: ProcessWrite.modify_batcktes_info` | F-PAD | 22 | 与 fix2 重叠 |
| `IQCommon/util/cgroup_utils :: set_cgroup_config` | F-ABSORB | — | |
| `IQEngine/…/realtime_event_source :: clock_worker` | F-ABSORB | 24 | 表条目 24=24 但 DIFF |
| `IQEngine/…/strategy :: tick_worker_thread` | F-ABSORB | — | |

对照组（`et>0` 但首分歧在**区外**，说明 try 只是载体或口径差异）：
`klinedata.get_kline_by_count_new`(et=8)、`trade_info_utils.kill_trade_process`(et=24)、
`get_trade_status`(et=11)、`quote.check_frequency`(et=2)、`run_individual_transform`(et=13)、
`ptradeAccount.order_response_order_update`(et=8) —— 一并探，产出证据供 fix1/fix2 参考。

## 2. 必答问题（逐单元给可复现读数）

1. **原表 vs 产品表逐条 diff**：`exctable75.txt` 已给 `origEnts/prodEnts/origNest/prodNest/SAME|DIFF`。
   对每个 IN 单元给出：条目数差异在哪几条（start/end/handler 偏移），是**多发 try 层**还是**范围平移**。
2. **三选一根因**（每单元定一个，附证据行）：
   a. **共享尾在 try 内被吸收**（shared exit in try）；
   b. **handler 出口错位**（except 块落到 reraise / return 落点不同）；
   c. **try 内 boolop/elif 链归约**（与 F-ABSORB/PAD 判据同源 → 标注重叠交中心）。
3. `trade_operation`：**target_diff #94** 的 JUMP 终点差异在哪条指令、try 归约如何导致。
4. **对照组问题**：为什么 `et>0` 但首分歧在区外？给出口径解释（try 只是载体 / 判据口径）。
5. `real_quote.get_tick_direction`（OUT，R74 拒收点）：作为 mandate 前置，说明它与 IN 单元
   `get_real_minute_kline` 是否同一 region 链、修复会不会再次触发 `hunks_norm 2→3`。

## 3. 修复与拆分

- 只允许在 **try/except 归约路径**上出 spec：`_process_try` / try 区识别与发射 / try 内共享尾吸收 /
  handler 出口。单臂单 edit（`specs/try8_<n>.json`），最后**合并臂 `trym`**（R74 欠交付，本轮必须交）。
- 闭环（每臂）：
  a. `mbuild75.py <arm> specs/<x>.json` 锚点断言全过；
  b. 官方 41 靶 `h62.py run --arm=<arm> --list=list41.txt` **逐项不回退**；
  c. mandated focus（`real_quote`/`trade_info_utils`/`finance`/`email_utils`/`cgroup_utils`/`quote`/
     `strategy`/`realtime_event_source`/`flytools` 逐支 `pyc_verify.py single --source build_<arm>/…`）
     → **real_quote 43/45→45/45（mandate）**，其余 IN 单元减少且**零新生失败**；
  d. 金丝雀 4 支 sha16 == pin；`closeout69.py battery landed <arm>` worse=0；
  e. `sstrict67.py build_<arm> <缺陷名单> out` 新增缺陷 0，`trade_operation` 的 target_diff #94
     若转正要在 `FACTS.md` 标明。
- synth：≥1 条「try 内共享尾」最小复现 + 1 条真嵌套负例（负例 sha 必须与落地逐字节相同）。

## 4. 硬规则

不改 repo（`land75` 只 dry-run、禁 `--apply`）；不手改 `*OK.py`；每条命令 <300s；
ALLOWED = `region_analyzer.py` / `region_ast_generator.py` / `comprehension_generator.py`；
spec 三要素注释 + 同层结构身份判据（无函数名/文件名/偏移阈值/名字白名单/新增 self 状态/
跨层 `region.entry in r.blocks`）；**任何他支回归即整件拒收**；h62 列表 LF 无 BOM；产物名 `:` → `_`。

## 5. 交付

`FACTS.md`（9 单元三选一根因表、et/首分歧口径解读、对照组解释、每臂 a–e 读数、与 fix1/fix2 重叠面）、
`specs/*.json` + **`specs/trym.json` 合并臂**、`synth/`、`dump/` 原始读数。
