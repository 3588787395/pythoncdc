# Round 13 结果记录（严格尺子口径）

## 一、结论（一句话）
本轮以「区域归约算法的判据必须在**识别时刻**成立」为准绳，落地 1 项真实修复
（`_loop_exit_is_implicit_return_none` 区域内部集边界）并回退 1 项错误细化
（A2 前缀提取判据从块级细化到指令级），官方 + 严格双口径同时前进，
**严格尺子全一致文件 321 → 325，函数严格一致 5970 → 5977，产物零回退**。

## 二、双口径数字（提交前实测）
| 口径 | 轮初 | 轮末 |
|---|---|---|
| 官方（loose，pyc_index） | 351 ok / 51 partial | 351 ok / 51 partial（本轮未改索引） |
| 严格（_r10_strict_check） | 321 全一致 / 81 有缺陷 | **325 全一致 / 77 有缺陷** |
| 函数级严格一致 | 5970 / 6204（96.23%） | **5977 / 6204（96.34%）** |

注：`baseline_strict_ok351.txt` 文件名里的 351 是**官方**口径数，该文件内
`OK` 行实为 321 条 —— 记录时勿混用两个尺子（本轮曾因此误判「掉了 26 个文件」）。

本轮翻正为 100% 的 pyc（4 个，均在同目录生成同名 +OK.py）：
- `IQEngine/plugins/plugin_system_control/__init__.pyc` 12/13 → **13/13**
- `IQCommon/util/backtest_info_utils.pyc` 9/10 → **10/10**
- `IQEngine/config/config.pyc` 10/11 → **11/11**
- `IQEngine/plugins/plugin_fly_data/fly_api/setting_api.pyc` 15/16 → **16/16**
另有 1 个文件净改善：`IQCommon/manager/instance.pyc` 29/33 → 31/33。

## 三、落地的修复（R13-W2-D）
`core/cfg/region_ast_generator.py::_loop_exit_is_implicit_return_none`：
- 识别条件：区域内部集 = `loop.blocks − else_blocks − init_blocks`；出口节点集
  = 内部集的非异常后继中不属于内部集者。for 区域按构造已含其出口块，不减
  `else_blocks` 会使出口集恒空、判据恒真。
- 归约方式：出口节点集含实际代码 ⇒ 函数区域在循环后仍有语句 ⇒ 终态 RETURN 块
  归约为**函数级终止抽象节点**，不得并入循环 merge 节点。
- AST 映射：歧义成立 → 允许 `Break`；否则 → 只能 `Return`。
- 验收：`test_repros/round13d/r13d_return_vs_break_probe.py` 10/10 PASS
  （期望列已从「缺陷指纹」改写为「修复后真值」，p5/p6 两项测量已固化为断言）；
  `test_repros/round13/run_all.py` 仍为 MISMATCH=15 / MATCH=10 / ERROR=0 / UNEXPECTED=0。

## 四、回退的错误细化（R13-A2，附实测证据）
A2 把 BoolOp/三元链「链首块前缀语句是否已发射」的判据从块级
（`first_chain_block in generated_blocks`）细化为指令级
（每条前缀指令偏移都在 `generated_offsets`）。实测后果：

- `generated_offsets` 只在个别路径零散登记 `start_offset`，并非完整发射账本，
  该 `all()` 测试对任何多指令块**恒为假** ⇒ 凡块被标记就重新提取整段前缀语句。
- 症状：整段语句重复发射。`IQEngine/account/order.pyc::create_order`
  orig=71 decomp=120（14 条语句被发两遍），另有
  `trade::create_trade`、`base_validator::_check_order`、`itn::authenticate`、
  `json_persistance::persist`、`quotation::change_future_real_date`。
- 两次补救均失败并已回退（判据回到块级）：
  (a) 改测块 `start_offset` 是否在 `generated_offsets`；
  (b) 新增 `statement_emitted_blocks` 权威台账（在 `_generate_block_statements`
      漏斗与 `_generate_block_statements_body` 入口各登记一次）。
  两者 6 处症状一字不变 ⇒ **create_order 的第一份语句并非经该漏斗产出**，
  任何「生成期标记集合」都不覆盖真实发射路径。
- 算法结论（写进识别方法注释留档）：前缀是否已发射必须在**区域归属**层面
  （谁拥有该块、该块的语句序列归哪个区域发射）决定，不能在生成期用标记弥补
  —— 这正是「一次正确」与「单向数据流」的要求。列为 Round 14 区域归属任务。
- 已知代价（回退后仍存在，Round 14 一并处理）：`repro_01` 第二臂
  `a2 = 2` 前缀被吞（generate() 入口 Ternary/BoolOp「被父消费」分支只标块）。
- 被回退的原始 hunk 已存档：`rounds/round13/r13_a2_reverted_hunk.diff`。

## 五、核心侧回退清单（产物已由 _r13_gate 自动保护，核心仍需修）
按配置 A/B 归属（每条都在 `D:/Temp/r13_ab*.log`、`D:/Temp/r13_imp_*.log` 可复现）：

| 文件 | 现状 | 归属 |
|---|---|---|
| `IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | 12 → 28 | HEAD 与 S1 同为 28 ⇒ 上一会话未提交改进在本轮编辑中被覆盖丢失，**无快照可恢复**（`git stash` 中两份均为更早基线） |
| `fly/data/quote.pyc` | 12 → 21 | 同上 |
| `plugin_system_persist/json_persistance.pyc` | 0 → 1 | region_analyzer 的 A3/R13c 未提交簇 |
| `plugin_system_risk_control/base_validator.pyc` | 0 → 1 | region_ast_generator 未提交簇（非 A2，非本轮 13-D） |
| `fly/data/quotation.pyc` | 2 → 3 | 同上（`change_future_real_date`） |
| klinedata / common_func / real_quote / plugin_fly_data`__init__` / history_api / flytools / market_time / quote_handler | 各 +1~3 | region_analyzer 的 A3/R13c 未提交簇 |

## 六、本轮工序（可复核）
1. 逐 hunk 反向应用工具 `D:/Temp/r13_revert.py`：先做**自检**（全部 hunk 反 apply ==
   `git show HEAD:` 逐行一致），再用于分组 A/B；每次换入换出都校验 sha256
   （`eb9e151888ebdd06` / `1f8b8dd4f9af98c1` 均已复原校验通过）。
2. 非侵入影响面体检 `D:/Temp/r13_impact2.py`：反编译落盘到 `D:/Temp/r13_impact2`，
   **绝不覆盖仓库 *OK.py**；402 文件全量一轮 ~250s。
   （旧脚本 `r13_impact_check.py` 用 basename 作临时文件名，跨包同名互相覆盖，
   已废弃；本轮两处数字均用新脚本重测确认。）
3. 产物门 `_r13_gate.py` 全量 402：CLEAN=320 FLIPPED-CLEAN=3 IMPROVED=1
   UNCHANGED=67 WORSENED(rolled back)=9 REGRESSION(rolled back)=2
   ⇒ 没有任何 +OK.py 被改差（11 个自动回滚）。
4. 严格尺子全量复验：`D:/Temp/r13_strict_after.log`（325 / 77，5977/6204），
   漂移比对 `D:/Temp/r13_drift.py` 输出 LOST=0 / GAINED=4。
