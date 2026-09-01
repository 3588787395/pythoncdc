# R102 修复工程师报告

- 轮次: R102（round_102 / repair_engineer）
- 日期: 2026-08-25
- 基线: HEAD = e158b6d4（rcm-r101），索引 402 pyc / 290 ok / 112 partial / 0 failed，91.25%（4722/5175）
- 源码修改: 仅 `core/cfg/region_ast_generator.py`（+79 行，纯新增，3 个修复点）；未 git commit/push；所有 *OK.py 由 `pyc_batch_verify.py single` 自动生成

## 1. P0 — stock_account.pyc `update_account` 下标增广赋值缺陷（已修复）

### 现象
`frozen_amount[order.symbol] += order.unfilled_amount` 被发射为 `order.symbol[order.unfilled_amount] = frozen_amount`——增广语义退化为普通赋值且基址/索引对调。首差 idx52 `COPY(2)` → `LOAD_FAST 'order'`（true_diffs=28）。

### 根因
CPython 3.11 下标增广协议：`LOAD container, LOAD key, COPY n, COPY n, BINARY_SUBSCR, <value>, BINARY_OP(in-place, arg>=13), SWAP 3, SWAP 2, STORE_SUBSCR`。else 分支块经 `_build_effective_stmts` 处理时，其 STORE_SUBSCR 分支只走 `_split_subscr_operands` 的「净栈效应 +1 后缀」三段切分。SWAP 的净效应为 0 但重排栈值，切分把 `[COPY2, COPY2, BINARY_SUBSCR, LOAD order, LOAD_ATTR unfilled, BINARY_OP+=, SWAP3, SWAP2]` 整段误判为一个 index 操作数、把 `order.symbol` 判为 container、`frozen_amount` 判为 value。回边块路径与 `_generate_block_statements` 早已委托 `_build_subscript_assign`（识别 COPY(>=2) 复制 + in-place BINARY_OP 协议），唯独此路径缺失。

### 修复点（core/cfg/region_ast_generator.py，`_build_effective_stmts` STORE_SUBSCR 分支）
- 纯栈协议结构判据命中即委托既有 `_build_subscript_assign(expr_instrs + [instr])` 重建 `AugAssign(target=Subscript)`：
  1. 存在 in-place `BINARY_OP(arg >= 13)`；
  2. 其后继至少一条 `SWAP`（写回重排序）；
  3. 存在 `COPY(arg >= 2)`（目标复制）。
- 未命中或委托失败回落原 `_split_subscr_operands` 路径（零退化）。与回边块路径注释（原 R22 修复族）及 `_build_attr_assign`（R16 STORE_ATTR-first 族）保持同构。

### 算法依据
区域归约算法通用判据：栈效应/操作码协议结构特征，自底向上先归约 AugAssign 子表达式；每个操作数指令区间唯一归属（COPY 复制段归 target、BINARY_OP 后段归 value）。

## 2. P1 — fly_data_source.pyc `get_stock_info` BUILD_CONST_KEY_MAP 键值错位（已修复）

### 现象
三键字典 `'stock_name'/'listed_date'/'de_listed_date'` 的前两键配上错位值：`'stock_name'` 配 `data[stock]['listed_date'].strftime(...)`、`'listed_date'` 配裸 `data[stock]`。修复过程中还暴露第二层缺陷：内层 `for item in field:` 的 iter_setup 前驱块被二次归属，多发射一条 `data_trans = {}`（orig=128 vs decomp=130）。

### 根因 1（键值错位）
字典第三值为三元表达式，整条语句经 TernaryRegion 归约。`_generate_ternary` 的 cond_val_start 向后扫描栈效应表覆盖 `LOAD_/LOAD_ATTR/LOAD_METHOD/COMPARE_OP/BINARY_OP/BUILD_/CALL/UNARY_...` 但**缺 `BINARY_SUBSCR`**（按 0/0 计）。条件测试 `data[stock]['delisted_date'] > datetime.datetime.now()` 含两层下标链，扫描在测试内部提前满足 `needed<=0`（cond_val_start=17 而非 14），测试前缀 `data[stock]` 的 LOAD+BINARY_SUBSCR 被误并入 preload_exprs → initial_stack 多一项 → BUILD_CONST_KEY_MAP 按 initial_stack 尾部三项配对整体错位一格。姊妹实现 `_ternary_prefix_stack_effect`（供 `_extract_dict_prefix_values` 使用）本就按 `(1,2)` 建模 BINARY_SUBSCR，两模型不一致。

### 根因 2（重复空 Dict）
`_loop_generate_for → _loop_extract_for_iter_pre_stmts` 对 for_iter_setup 块抽取前缀赋值语句时，该块同时是已由父路径发射的三元 merge_block（共享基本块：`data_trans = {...}` 与 GET_ITER 同块）。独立重建 `[LOAD_CONST 键元组, BUILD_CONST_KEY_MAP]` 得到 keys=3/values=0 的空 Dict 并再次绑定 data_trans。

### 修复点（core/cfg/region_ast_generator.py）
1. `_generate_ternary` cond_val_start 扫描表补齐 `BINARY_SUBSCR = (push 1, pop 2)`，与 `_ternary_prefix_stack_effect` 完全对齐；docstring 按 4 节模板追加 `[R102 fix]` 段。
2. `_loop_generate_for` 前缀语句抽取处增加归属过滤：for_iter_setup 上存在 merge_block 同址、非 iter 上下文、且带 value_target 的 TernaryRegion 时，滤除目标名等于该 value_target 的前缀 Assign（纯结构判据，不依赖生成时序状态）；其余前缀语句照常发射，iter_expr 抽取不受影响。行内注释标注 [R102 fix]。

### 算法依据
栈效应判据（条件表达式起点 = 从块尾反扫 needed 归零处，下标消费必须计入）+ 每块唯一归属（merge_block 前缀归 TernaryRegion，GET_ITER 后缀归 LoopRegion）。

## 3. docstring / 注释更新清单

| 方法 | 类型 | 更新 |
|---|---|---|
| `_build_effective_stmts` | _build_* | STORE_SUBSCR 分支行内注释 [R102 fix]（增广协议判据 + 委托说明） |
| `_generate_ternary` | _generate_* | docstring 追加 `[R102 fix]:` 段（4 节模板后追加，含根因/判据/一致性说明） |
| `_loop_generate_for` | _loop_* | 前缀过滤行内注释 [R102 fix]（每块唯一归属说明） |

本轮未修改任何 `_identify_*_regions` 方法，无需 6 节模板追加。

## 4. P2 簿记结果表

| pyc | 动作前索引 | single 实测 | 动作后索引 |
|---|---|---|---|
| IQCommon/profiler_func.pyc | partial (ltr=92.31%) | ok 14/14 | ok |
| IQCommon/util/docker_info_utils.pyc | partial (83.33%) | ok 7/7 | ok |
| IQData/modules/WEBCLIENT/gtn_client.pyc | partial (80.00%) | ok 11/11 | ok |
| IQEngine/core/strategy/strategy_universe.pyc | partial (66.67%) | ok 11/11 | ok |
| IQEngine/utils/cache_storage.pyc | ok（脏记录，fc=18 自相矛盾） | partial 95.24% (20/21)，func_wrapper true_diffs=203 | partial（如实降级） |
| IQEngine/data/data_proxy.pyc | ok（脏记录 rate=87.5% 自相矛盾） | partial 88.89% (8/9)，DataProxy 类定义发射错位 | partial（如实降级） |

## 5. 复现实例验证

| 文件 | 修复前 | 修复后 |
|---|---|---|
| repro_102_01_dict_key_order_rich_values.py | MATCH | MATCH |
| repro_102_02_dict_key_order_alpha_control.py | MATCH | MATCH |
| repro_102_03_subscript_augassign_in_loop.py | MATCH | MATCH |
| repro_102_04_subscript_plain_assign_control.py | MATCH | MATCH |
| repro_102_05_const_key_map_in_try_for_if.py | **DEFECT-REPRO** | **MATCH** |
| repro_102_06_subscript_augassign_rich_branches.py | **DEFECT-REPRO** | **MATCH** |

汇总：6/6 MATCH（P0/P1 两缺陷均闭环，4 控制组无扰动）。

## 6. 目标文件终态

| pyc | 修复前 | 修复后 |
|---|---|---|
| site-packages/IQEngine/plugins/plugin_system_accounts/account_model/stock_account.pyc | partial（update_account true_diffs=28） | **ok / 25/25 / rate=1.0** |
| site-packages/IQEngine/plugins/plugin_fly_data_source/fly_data_source.pyc | partial（get_stock_info true_diffs=30） | **ok / 70/70 / rate=1.0** |

## 7. 回归数字

- import 冒烟：`python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator; import core.cfg.code_generator"` 通过
- round_102 verify_repros：**6/6 MATCH**
- round_101 verify_repros：**14/14 MATCH**
- round_100 verify_repros：**10/10 MATCH**

抽查 single（全部保持 ok 且 rate 不降，共 12 个 ≥ 要求的 8 个）：

| pyc | 结果 |
|---|---|
| fly/data/quotation.pyc（必查） | ok 143/143 |
| IQData/utils/trade_schedule.pyc | ok 4/4 |
| IQCommon/backtest/backtest.pyc | ok 2/2 |
| IQEngine/main.pyc | ok 3/3 |
| IQCommon/api/check_strategy.pyc | ok 2/2 |
| IQCommon/api/wrapper.pyc | ok 4/4 |
| IQEngine/plugins/plugin_system_risk_control/price_validator.pyc | ok 5/5 |
| IQEngine/utils/record_store.pyc | ok 5/5 |
| IQCommon/data/api_data.pyc | partial 14/10（与 R102 实测基线逐字一致，非回归） |
| IQCommon/util/common_func.pyc | partial 21/15（同上一致） |
| fly/simtradding/flyAccount.pyc | partial 23/17（同上一致） |
| IQEngine/interface.pyc | partial 105/89（同上一致） |

## 8. 最终全局统计（pyc_batch_verify.py stats）

```
total_pyc:             402
verified_pyc:          402
ok_pyc:                294   （≥292 ✓）
partial_pyc:           108
failed_pyc:            0
total_functions:       5175
matched_functions:     4725
cumulative_match_rate: 91.30%（>91.25% ✓）
```

相对基线：ok +4（294 vs 290）、matched +3（4725 vs 4722）、rate +0.05pp。matched 增量小于报告情景 B 推算值（4737），原因是本次抽查对 api_data/common_func/flyAccount/interface 等 partial 也执行了 single，按新 total 口径如实重录了这些条目的 matched 数（测试工程师第 2.2 节已裁定该批为历史口径差异而非回归）；ok 数口径不受影响。

## 9. 残留事项（移交 R103 建议）

1. cache_storage.func_wrapper（true_diffs=203，包装器体约 30 条指令丢弃重排）与 data_proxy.DataProxy（类定义发射错位）为存量缺陷，本轮仅诚实簿记未修复。
2. interface.pyc 等 11 个「历史 fc 口径」条目建议统一重录基线（调度者动作），避免每次实测都表现为虚假下降。
3. `_split_subscr_operands` 对含 SWAP 序列的缓冲仍会错位切分；本次以协议判据前置分流规避，若后续出现非增广形态的 SWAP 缓冲可考虑在该方法内引入 SWAP 感知切分。
