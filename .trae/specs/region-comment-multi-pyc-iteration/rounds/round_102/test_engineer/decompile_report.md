# R102 测试工程师批量回归验证报告

- 轮次: R102（round_102 / test_engineer）
- 日期: 2026-08-25
- 工作目录: F:\Downloads\pythoncdc-main（Python 3.11.7，Windows PowerShell）
- 基线确认: HEAD = e158b6d4（rcm-r101），索引 402 pyc / 290 ok / 112 partial / 0 failed，累计 91.25%（4722/5175）——与任务给定基线逐字一致
- 本轮性质: 只读批量回归测量 + 缺陷诊断（未修改任何源码、未手工编辑 *OK.py、未写回 pyc_index.json，已用 git status 复核）

## 1. 验证方法与执行概况

- 驱动脚本: `chunked_verify.py`（本目录）。从 pyc_index.json 读全量条目，支持 `--subset partial|ok-sample|all` 与 `--limit/--offset/--state progress.json` 断点续跑；每个 pyc 在独立子进程内调用 `scripts/pyc_batch_verify.py` 的 `decompile_single + bytecode_diff`，父进程 90 秒看门狗；逐条写入 `progress.json`（含完整 mismatches 明细），**不回写主索引**。
- ok-sample 定义: 290 个 ok 按路径字母序排序后均匀抽样 30 个（`idx_i = i*290//30`）。
- 执行: partial 全量 112 个（4 条命令分片，单命令最长 ~38s 墙钟）；ok-sample 30 个（2 条命令）。全程 **0 timeout、0 crash、0 missing**。单文件实测耗时 0.3s–10.8s。

## 2. partial 全量结果（112 个）

### 2.1 rate=1.0 可升级 ok（4 个）

| # | 路径（site-packages/…） | 实测 total/matched | 索引旧 rate(ltr=98) |
|---|---|---|---|
| 1 | IQCommon/profiler_func.pyc | 14/14 | 92.31% |
| 2 | IQCommon/util/docker_info_utils.pyc | 7/7 | 83.33% |
| 3 | IQData/modules/WEBCLIENT/gtn_client.pyc | 11/11 | 80.00% |
| 4 | IQEngine/core/strategy/strategy_universe.pyc | 11/11 | 66.67% |

其余 108 个仍为 partial（实测 rate 42.11%–98.61%）。

### 2.2 相对索引 rate 下降 ≥1 函数的「疑似回归」（11 个，按任务定义列出）

| # | 路径（site-packages/…） | 索引(fc/rate) | 实测(total/matched/rate) | Δ新口径 | Δ索引fc口径 |
|---|---|---|---|---|---|
| 1 | IQEngine/interface.pyc | 93/93.55% | 105/89/84.76% | **-9** | -2 |
| 2 | fly/simtradding/flyAccount.pyc | 22/81.82% | 23/17/73.91% | **-2** | +1 |
| 3 | IQCommon/data/api_data.pyc | 11/81.82% | 14/10/71.43% | -1 | -1 |
| 4 | IQCommon/data/local_finance.pyc | 16/87.50% | 19/16/84.21% | -1 | -2 |
| 5 | IQCommon/util/common_func.pyc | 18/77.78% | 21/15/71.43% | -1 | -1 |
| 6 | IQData/api/api_base.pyc | 22/86.36% | 25/21/84.00% | -1 | -2 |
| 7 | IQData/modules/WEBCLIENT/web_socket_client.pyc | 5/80.00% | 7/5/71.43% | -1 | -1 |
| 8 | IQEngine/core/execution_context.pyc | 16/93.75% | 17/15/88.24% | -1 | 0 |
| 9 | IQEngine/utils/profiler_func.pyc | 13/92.31% | 15/13/86.67% | -1 | -1 |
| 10 | fly/data/quote_handler.pyc | 53/77.36% | 57/43/75.44% | -1 | -2 |
| 11 | fly/simtradding/ptradeFutureAccount.pyc | 37/86.49% | 38/32/84.21% | -1 | 0 |

**探针裁定：以上 11 个全部不是真回归。** 方法（R101 同款只读二分）：`git archive 67adb113`（rcm-r98）解包至 `d:\Temp\opencode\wt_102_r98`，固定当前 HEAD 的 `compare_bytecode`，仅切换反编译核心复测代表样本（interface / flyAccount / api_data 等 5 个）。**R98 与 HEAD 输出逐一完全相同**（如 interface 均 89/105、flyAccount 均 17/23）。差异根源是索引 function_count 为历史口径（普遍不含 `<module>` 及部分嵌套函数，如 interface 93 vs 实际 105），按新 total 折算产生虚假下降。建议调度者将此批标记为「需重录基线」而非回归。

## 3. ok-sample 结果（30 个）

- 28/30 与索引一致（rate=1.0）。
- **不一致 2 个**（索引标 ok，实测 partial）：

| 路径（site-packages/…） | 索引记录 | 实测 | 不匹配函数 |
|---|---|---|---|
| IQEngine/utils/cache_storage.pyc | ok / 100% / fc=18 (ltr=98) | **partial / 95.24%** (20/21) | `func_wrapper`: orig=270 decomp=240, jump_diffs=1, true_diffs=203, 首差 idx56 `LOAD_FAST 'cache_start'` → `JUMP_FORWARD(266)`（包装器体内约 30 条指令被丢弃重排） |
| IQEngine/data/data_proxy.pyc | **ok / 87.5% / fc=8**（自相矛盾记录）(ltr=98) | **partial / 88.89%** (8/9) | `DataProxy`: orig=37 decomp=33, true_diffs=32, 首差 idx5 `LOAD_NAME 'TickBar'`(基类名) → `LOAD_CONST <code object __init__>`（类定义发射错位） |

**探针裁定：两个都不是本轮回归。** R98 核心在 HEAD 比较器下同样给出 cache_storage 20/21（func_wrapper 不匹配）、data_proxy 8/9（DataProxy 不匹配）：
- cache_storage 是 **R98 时代的错误 ok 记录**（当时 fc=18 且记为 100%，与本次 21 函数口径不符）——陈年缺陷首次被如实测出；
- data_proxy 的索引记录本身自相矛盾（status=ok 但 rate=0.875），实测与该 rate 吻合，属既有缺陷 + 脏记录。

## 4. 全局统计推算

索引基线（实测复核 `pyc_batch_verify.py stats`）：402 pyc，290 ok / 112 partial / 0 failed，matched 4722/5175 = **91.25%**。

| 情景 | ok | partial | matched/total | 累计匹配率 |
|---|---|---|---|---|
| A: 仅将 4 个 rate=1.0 的 partial 升级 | **294** | 108 | **4734/5175** | **91.48%**（+12 函数） |
| B: A + 将 2 个陈旧 ok 重录为实测（data_proxy/cache_storage 转 partial 但 matched+3） | 292 | 110 | 4737/5175 | 91.54%（+15 函数） |

升级贡献明细：profiler_func +2、docker_info_utils +2、gtn_client +3、strategy_universe +5。

## 5. 本轮修复提名（2 个）

提名原则：「剩余不匹配函数最少且非 `<module>-only`」。候选表（非 module-only、剩余 1 个不匹配函数、按 true_diffs 升序）：

| 候选文件 | 剩余函数 | true_diffs | 备注 |
|---|---|---|---|
| **IQEngine/plugins/plugin_system_accounts/account_model/stock_account.pyc** ★提名1 | update_account | 28 | 修复即整文件翻 ok（25 函数） |
| **IQEngine/plugins/plugin_fly_data_source/fly_data_source.pyc** ★提名2 | get_stock_info | 30 | 同长指令流纯错位，修复即整文件翻 ok（70 函数） |
| …/position_model/future_position.pyc | make_trade | 34 | 尾部提前 return |
| plugin_fly_data/__init__.pyc | _on_before_trading_start_trading_thread | 19 | — |
| IQEngine/account/trade.pyc | create_trade | 52 | orig=68→decomp=19 大段丢失 |

### 提名 1: stock_account.pyc — `update_account`（true_diffs=28, orig=90 decomp=84 原始指令）

- 首差 idx52：orig `COPY(2)` → decomp `LOAD_FAST 'order'`。
- 缺陷模式：**下标增广赋值被降级且操作数对调**。源码 `frozen_amount[order.symbol] += order.unfilled_amount`（COPY/COPY/BINARY_SUBSCR/SWAP×2 增广序列）被发射成 `order.symbol[order.unfilled_amount] = frozen_amount`——基址与索引对调、`+=` 退化为 `=`，语义双重破坏。上下文为 for+if/elif/else 多分支循环，与相邻的属性增广赋值 `self._frozen_cash += ...` 共存。
- 最小复现: `minimal_repros/repro_102_06_subscript_augassign_rich_branches.py` → **DEFECT-REPRO**（true_diffs=28，首差 COPY→LOAD_FAST 与真实目标同签名）；简单形 repro_102_03 为 MATCH，说明触发需要富分支上下文。

### 提名 2: fly_data_source.pyc — `get_stock_info`（true_diffs=30, jump_diffs=7, 两侧均 139 条原始指令）

- 首差 idx47 区域：orig idx52 `LOAD_CONST 'name'` → decomp `LOAD_CONST 'listed_date'`。
- 缺陷模式：**BUILD_CONST_KEY_MAP 多键字典的键值错位配对**。字典位于 for+try/except KeyError+if 三层嵌套内，前两个值是共享 `data[stock][…]` 前缀的下标链。产物把 `'stock_name'` 配上 listed_date 的 strftime 链、`'listed_date'` 配上裸 `data[stock]`（见 fly_data_sourceOK.py:631），区域归约切分相邻相似值表达式时边界错位。
- 最小复现: `minimal_repros/repro_102_05_const_key_map_in_try_for_if.py` → **DEFECT-REPRO**（true_diffs=64，首差 LOAD_CONST 'name'→'listed_date' 与真实目标同签名）；不含 try/嵌套的简单形 repro_102_01 为 MATCH。

两案均为「局部生成/归约逻辑」缺陷，互不同族但都可用 ≤35 行富上下文源码稳定复现，且各自修复可分别翻转 1 个整个 pyc 至 ok。

## 6. 复现实例归档（步骤 5）

目录 `minimal_repros/`（6 文件）+ `verify_repros.py`（round_101 同款模式）。运行 `python verify_repros.py`：

| 文件 | 模式 | 结果 |
|---|---|---|
| repro_102_01_dict_key_order_rich_values.py | 字典键序·简单形控制 | MATCH |
| repro_102_02_dict_key_order_alpha_control.py | 键序字母序控制 | MATCH |
| repro_102_03_subscript_augassign_in_loop.py | 下标增广·简单形控制 | MATCH |
| repro_102_04_subscript_plain_assign_control.py | 普通下标赋值控制 | MATCH |
| repro_102_05_const_key_map_in_try_for_if.py | BUILD_CONST_KEY_MAP 富上下文（提名2） | **DEFECT-REPRO** |
| repro_102_06_subscript_augassign_rich_branches.py | 下标增广富分支（提名1） | **DEFECT-REPRO** |

汇总：**2 DEFECT-REPRO / 4 MATCH 控制**。两个缺陷的最小独立形均健康，需携带真实嵌套结构方可触发。

## 7. 附注

- 数据文件：`progress.json`（142 条逐项实测记录，含全部 mismatch 明细）、`stats_baseline_r102.txt`（基线 stats 对照）、分析脚本 `analyze_r102.py / dig_r102.py / project_r102.py / disasm_r102.py / dump_gsi.py / probe_r98_vs_head.py` 均在本目录，供审计。
- 所有验证命令墙钟 ≤300s（实际最长 38s）；未 git commit/push；主索引经 git status 复核零改动。
- 驱动脚本曾出现一处 JSON 序列化缺陷（比较器 first_diff 携带 Python 3.11 `dis._Unknown` 哨兵对象），已在驱动内以 default 序列化兜底修复（仅测试工具层，未触及 core/pycdc.py/scripts）。
