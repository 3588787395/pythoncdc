# R74 · fix3（修复工程师）BRIEF — inside-try 子族 11 单元（按用户裁定的 try-except 归约路径）

## -1. 裁定与读数

用户裁定（R73 commit `b355043e`）：**剩余控制流失败的根因就是「嵌套 try-except 问题」**。
中心 R74 定量读数：77 失败单元中**首分歧在异常区内 11 个、区外 65 个**（`et_diff 27`、
`prod_deeper 0`）。**本批按裁定对这 11 个 inside-try 单元全力攻坚**；区外 65 个由 fix1/fix2 承担。

## 0. 使命与工作区

工作区：`D:/Temp/opencode/r74gate/fix3`；基线 HEAD = **`6bb9716a`**。
目标：在 try/except 归约路径上给出**可判据的修复**，mandate 候选 = `real_quote.pyc` 41/45 → 45/45。

## 1. 靶单（11，来自 `dump/crosstab74.txt`）

| 文件 :: 单元 | 家族 | 原 et | 备注 |
|---|---|---|---|
| `IQData/…/real_quote :: one_prod_to_ndarray` | F-ABSORB | 10 | mandate 路径 |
| `real_quote :: get_real_minute_kline` | F-ABSORB | 7 | 同上 |
| `real_quote :: get_cache_l2_data_by_one` | F-ABSORB | 5 | 同上 |
| `real_quote :: get_tick_direction` | F-ABSORB | 6 | **OUT**（第 4 个失败单元，必须一并修才成 success） |
| `fly/data/quote :: run_tick_socket` | F-PAD | 13 | 与 fix2 重叠，标注证据交中心 |
| `IQCommon/util/trade_info_utils :: trade_operation` | F-ABSORB | 18 | **R70 遗留 target_diff #94**（交接项） |
| `IQCommon/data/finance :: get_fields` | F-ABSORB | 8 | R73 记 IN-TRY k=18，strict `target_diff #19` |
| `IQCommon/util/email_utils :: send_email` | F-ABSORB | 5 | 首分歧在 handler 内 |
| `fly/common/flytools :: ProcessWrite.modify_batcktes_info` | F-PAD | 24 | 与 fix2 重叠 |
| `IQCommon/util/cgroup_utils :: set_cgroup_config` | F-ABSORB | — | |
| `IQEngine/…/realtime_event_source :: clock_worker` | F-ABSORB | — | |
| `IQEngine/…/strategy :: tick_worker_thread` | F-ABSORB | — | |

（`kill_trade_process` et=24、`query_trade_strategy_info` et=10、`query_strategy_id` et=9、
`get_trade_status` et=11 有异常表但首分歧在**区外** —— 作为对照组一起探，可给 fix2 参考。）

## 2. 必答问题（逐单元给可复现读数）

1. **产品 try 形 vs 原 pyc try 形**：`tryverdict73.txt` 显示多数单元 `nest=0` 但 `prodTryNest=1/2` ——
   查清该读数含义（是产品多建了 try 层，还是指标口径差异），并给出**原表 vs 产品表逐条 diff**
   （`exctable73.py` 已产 `dump/exctable_diff73.txt`，按单元解读）。
2. **三选一根因**（每单元定一个，附证据行）：
   a. **共享尾/merge 被 try 内臂吸收**（shared exit in try）；
   b. **handler 出口错位**（except 块落点/`reraise` 或 `return` 落点不同）；
   c. **try 内 boolop/elif 链归约**（与 F-ABSORB/PAD 判据同源，标注重叠交中心）。
3. `trade_operation`：给出 **target_diff #94** 的 JUMP 终点差异在哪条指令、try 归约如何导致。
4. 对照组：为什么 `et>0` 但首分歧在区外（说明 try 只是载体，或指标口径问题）。

## 3. 修复与拆臂

- 只允许在 **try/except 归约路径**上出 spec：`_process_try` / try 区识别与发射 /
  try 内共享尾吸收 / handler 出口；单臂单 edit（`specs/try7_<n>.json`），最后合并臂 `trym`。
- 闭环（每臂）：
  a. `mbuild74.py <arm> specs/<x>.json` 锚点断言全过；
  b. 官方 35 靶 `h62.py run --arm=<arm> --list=…` **逐项不回退**；
  c. mandated：11+4 靶逐支 `pyc_verify.py single --source build_<arm>/…`
     → **real_quote 4/4 转绿即 mandate**，其余失败单元减少且**零新增**；
  d. 金丝雀 4 支 sha16 == pin；`closeout69.py battery landed <arm>` worse=0；
  e. `sstrict67.py build_<arm> <75 缺陷名单> out` → 新增缺陷 0，`trade_operation` 的
     target_diff #94 若转正要在 FACTS 标明。
- synth：至少 1 条「try 内共享尾」最小复现 + 1 条真嵌套负例（负例 sha 必须与落地逐字节相同）。

## 4. 硬规则

不改 repo（`land74` 只 dry-run、禁 `--apply`）；不手改 `*OK.py`；每条命令 <300s；
ALLOWED = `region_analyzer.py` / `region_ast_generator.py` / `comprehension_generator.py`；
spec 三要素注释 + 同层结构身份判据（无函数名/文件名/偏移阈值/名字白名单/新 self 状态/
跨层 `region.entry in r.blocks`）；**任何他支回归即整件拒收**；h62 列表 LF 无 BOM；
产物名 `:` 走 `.replace(':','_')`。

## 5. 交付

`FACTS.md`（11 单元三选一根因表、et/首分歧口径解读、每臂 a–e 读数、与 fix1/fix2 重叠面）、
`specs/*.json`、`synth/`、`dump/` 原始读数。
