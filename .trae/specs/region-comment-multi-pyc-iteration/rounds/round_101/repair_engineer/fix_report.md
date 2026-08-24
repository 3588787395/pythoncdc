# R101 修复工程师报告

- 轮次: R101（round_101 / repair_engineer）
- 日期: 2026-08-25
- 工作目录: F:\Downloads\pythoncdc-main（Python 3.11.7，Windows PowerShell）
- 目标: 将 site-packages/fly/data/quotation.pyc 从 partial 97.90%（140/143）恢复为 ok/1.0（143/143）
- 结果: **达成**。quotation.pyc = ok / 100.00% / 143/143；全局 290 ok / 112 partial / 91.25%

## 1. 根因分析

测试报告定位的两笔罪魁提交均属实。三个不一致函数对应三个独立的判据缺陷，
全部落在区域归约算法的「每块唯一归属」判据上。

### 1.1 isVaildDate（31 true_diffs，首差 idx11 JUMP_FORWARD→LOAD_CONST None）

- 罪魁提交: `41bfaea9`（dtc-r01），改动位于 core/cfg/region_analyzer.py
  `_identify_try_except_regions` 内 `_explicit_return_blocks_r21n1` 收集逻辑
  （当时行号 ~6725）：新增
  `if succ.start_offset >= try_end_for_blocks: continue`。
- 判据缺陷: 该排除的本意是把 try-except-else 的 else 块留给
  `_find_try_else_blocks` 识别（repro_09_try_except_else_return 场景）。
  但 CPython 对 try 体内部的「共享尾部常量 return」块同样会把它裁剪出异常表
  保护范围 [try_start, try_end)——因为 LOAD_CONST/RETURN_VALUE 不触发异常。
  isVaildDate 的字节码中 try 范围为 [4,62)，而共享尾部 `return True`
  块恰从 offset=62（== try_end）开始。两类块在「偏移 >= try_end」维度上
  **不可区分**，旧判据一刀切排除。
- 丢失路径: 块被排除出 try_blocks 后，也不会被任何 else 收集路径认领——
  `_find_try_else_blocks` 三段式、Pattern TE BFS、`_find_inner_else_blocks`
  全部带 `not self._is_pass_or_return_none_block(block)` 过滤，而该函数对
  `LOAD_CONST <任意常量> + RETURN_VALUE` 一律返回 True。于是该块无任何归属，
  成为孤儿 Region，最终 `return True` 整条丢失、函数恒返回 None。

### 1.2 change_his_to_backward（224 true_diffs，首差 idx305 POP_TOP→JUMP_FORWARD）

- 罪魁提交: `18c55e62`（Round 8），region_analyzer.py `_detect_break_continue`
  尾部（当时行号 ~5019-5028）：R8 新增 `_s_meaningful` 过滤——后继块含
  「有效用户代码」时不注册为 break 目标。
- 判据缺陷: break 落点块 `[POP_TOP(迭代器), EXTENDED_ARG, JUMP_FORWARD]`
  中 **EXTENDED_ARG 不在 NOISE_OPS / PURE_JUMP_OPS / 跳转集合的任何排除列表**
  里，被误计为用户代码 → 真 break 目标漏标 → `has_break=False` →
  for-else 判定失真 + `elif data[predataindex:curdataindex].empty:` 的
  break 分支退化为 pass。JUMP_FORWARD 目标 2594 > 255 正是必须携带
  EXTENDED_ARG 前缀的场景，故该函数必现。
- 连带效应: break 未注册导致 LoopRegion.else_blocks/结构塌陷，后续 224 条
  指令全部错位。

### 1.3 get_str_data（121 true_diffs，首差 idx169 LOAD_FAST j→stock_df）

- 罪魁提交: 同 `18c55e62`（R8 同一处判据），另一形态。
- 判据缺陷: 内层 `for j in range(len(is_all_nan))` 的 break 落点块为
  `[LOAD_FAST j, STORE_FAST not_nan_icount, POP_TOP, fall-through→exit]`。
  CPython 在「break 落点紧邻循环出口」时把尾随赋值语句与迭代器清理 POP_TOP
  合并进同一基本块且**不带显式跳转**。R8 判据看到 LOAD_FAST/STORE_FAST 即判为
  「含有效用户代码，不是纯 break 目标」→ 漏标。
- 丢失路径: ① `_detect_break_continue` 不注册 break；② 更早执行的
  `_find_loop_else` FOR 分支只认「JUMP_FORWARD/RETURN 收尾的后继」为
  break 证据（`_break_hits_for_iter_exit`），融合形态同样漏检 → 返回
  else_blocks=[146]（for_iter_exit 本身！）→ 反编译输出幻影
  `else: return found`，同时 `not_nan_icount = j; break` 与 continue 结构
  整体重排（repro_101_04 为其最小形）。

## 2. 修复点清单（全部在 core/cfg/region_analyzer.py，+180/-5 行）

| # | 方法 | 修复内容 | 算法依据 |
|---|---|---|---|
| F1 | `_identify_try_except_regions`（`_explicit_return_blocks_r21n1` 收集处） | 精化 dtc-r01 排除：return-None/pass 形态仍排除（隐式 return 由 Pattern B 处理）；非 None 常量 return 仅当**全部普通前驱完整位于 [try_start_min, try_end) 保护范围内**（只从 try 体进入，不来自 else 区）时收归 try_blocks | 原则 2（每块唯一归属）：该类块唯一可达入口来自 try 体（编译器仅因 RETURN_VALUE 不抛异常裁剪异常表范围），else 收集器又不可能认领它，唯一正确归属即 try body |
| F2a | `_find_loop_else` FOR 分支 | FORWARD_CONDITIONAL_JUMP 后继中新增融合 break 形态识别：后继以 POP_TOP 收尾 ∧ 末条指令 offset+2 == for_iter_exit.start_offset ∧ 全部前驱 ∈ body_set → 置 `_break_hits_for_iter_exit=True`（等价于 JUMP_FORWARD→exit 显式形态），返回 `(None, natural_exit)` | 原则 2：融合块只从循环体进入，是真正的 break 落点；与既有 `_break_hits_for_iter_exit` 证据通道同一语义 |
| F2b | `_detect_break_continue`（R8 判据处） | a) `_s_meaningful` 排除集合加入 `EXTENDED_ARG`（前缀噪声指令，无用户语义）；b) 含用户代码的后继若满足「全部前驱 ∈ body_set ∧（末条 JUMP_FORWARD/JUMP_ABSOLUTE 目标 == natural_exit ∨ 剥离 POP_TOP 清理尾部后 fall-through 紧邻 natural_exit，按原始末条 offset+2 判定）」→ 注册为 break 目标；其余含用户代码后继维持 R8 跳过语义 | 原则 2 + 原则 4：break 边是 CFG 边语义；EXTENDED_ARG 属噪声；不满足融合形态者（如 validate_data 的 print+return 分支）行为与 R8 完全一致 |

未 revert 任何提交；两笔罪魁提交的有效部分（dtc-r01 的 else 识别、R8 的
validate_data 修复 + LOOP_BACK_EDGE Continue 发射等）全部保留。

## 3. docstring 更新清单

| 方法 | 模板 | 追加 |
|---|---|---|
| `_identify_try_except_regions`（region_analyzer.py:6071） | 6 节 | `[R101 fix] 显式 return 块收集判据精化（isVaildDate 形态）` |
| `_find_loop_else`（region_analyzer.py:4268） | 4 节 | `[R101 fix] FOR 循环融合 break 识别（get_str_data 形态）` |
| `_detect_break_continue`（region_analyzer.py:4878） | 4 节 | `[R101 fix] R8 判据精化（两点）` |

行内注释均以 `[R101 fix]` 标注（共 6 处标记）。`_generate_*` 层无需改动
（三处根因均为 analyzer 侧归属判定缺失，AST 生成层既有 BREAK/try-body
发射路径本就正确）。

## 4. 验证结果

### 4.1 quotation.pyc（硬指标）

```
decompile_status:   ok          （修复前 partial）
total_functions:    143
matched_functions:  143         （修复前 140）
match_rate:         100.00%     （修复前 97.90%）
quotationOK.py 再生成: 是，py_compile 通过
pyc_index.json 条目: ok / bytecode_match_rate 1.0
```

### 4.2 复现实例（verify_repros.py）

14 个 repro 全部 MATCH：3 个 DEFECT-REPRO（01/03/04）全部转为 MATCH，
11 个 NO-DEFECT 控制组保持 MATCH（无回归）。汇总 `MATCH: 14`（修复前
DEFECT-REPRO: 3 / MATCH: 11）。

### 4.3 回归检查

| 套件 | 修复前（HEAD 基线实测） | 修复后 | 结论 |
|---|---|---|---|
| round_100 verify_repros.py | 10/10 | **10/10** | 持平 |
| round_15 minimal_repros | 10/12 | **10/12** | 持平（2 个 boolop 缺陷为基线遗留） |
| round_19 minimal_repros | 11/11 | **11/11** | 持平 |
| round_94 / 95 / 96 / 97 | 2/2, 19/20, 9/10, 9/10 | **同左** | 持平 |
| dtc round_01 (21 repros) | 17/21 | **17/21** | 持平（dtc-r01 场景无回归） |
| dtc round_02 (12 repros) | 10/12 | **11/12** | **+1 改善**（repro_r2_10_try_wrap_for_else_break 转 MATCH） |
| dtc round_11 / round_12 | 7/10, 3/10 | **同左** | 持平 |
| spf round_07~16 minimal_repros（8 轮） | 12/12, 11/12*, 13/13, 12/12, 13/13, 12/12, 13/13, 12/12 | **同左** | 持平（*round_09 repro_07 经 git stash 对照确认为 HEAD 既有失败） |
| spf round_08 test_repros.py（R8 提交主场） | 35/35 PASS | **35/35 PASS** | 无回归 |

模块导入检查：`import core.cfg.region_analyzer / region_ast_generator /
code_generator` 通过。

### 4.4 代表性 pyc 抽查（16 个，single 实测）

| pyc | 修复前状态 | 修复后实测 |
|---|---|---|
| IQCommon/trade_schedule.pyc | ok | ok 6/6 100% |
| IQCommon/backtest/backtest.pyc | ok | ok 2/2 100% |
| IQEngine/main.pyc | ok | ok 3/3 100% |
| IQCommon/api/check_strategy.pyc | ok | ok 2/2 100% |
| IQData/api/get_block_stocks.pyc（R8 目标文件） | ok | ok 2/2 100% |
| IQCommon/api/wrapper.pyc | ok | ok 4/4 100% |
| IQEngine/plugins/plugin_system_risk_control/price_validator.pyc | ok | ok 5/5 100% |
| IQEngine/utils/record_store.pyc | ok | ok 5/5 100% |
| fly/common/inform_info.pyc | ok | ok 4/4 100% |
| IQEngine/plugins/plugin_fly_api/empty_api_backtest.pyc | ok | ok 62/62 100% |
| IQEngine/const.pyc | ok | ok 38/38 100% |
| fly/simtradding/pboxAccount_jupyterhub.pyc | ok | ok 4/4 100% |
| IQEngine/utils/report.pyc | ok | ok 5/5 100% |
| IQCommon/util/wrapper_utils.pyc | ok | ok 14/14 100% |
| IQData/utils/trade_schedule.pyc | ok | ok 4/4 100% |
| IQEngine/account/order.pyc | partial 98.08% (51/52) | partial 98.08% (51/52)，不低于原状态 |

### 4.5 全局累计统计（pyc_batch_verify.py stats）

| 指标 | R101 修复前 | 修复后 | 要求 |
|---|---|---|---|
| ok_pyc | 289 | **290** | ≥289 ✓（恢复 R100 水平） |
| partial_pyc | 113 | **112** | — |
| failed_pyc | 0 | **0** | — |
| matched_functions | 4719/5175 | **4722/5175** | +3（quotation 三函数） |
| cumulative_match_rate | 91.19% | **91.25%** | ≥91.19% ✓ |

注：相对 R100 报告值 91.27%/4723 仍差 1 个函数，为测试报告已记载的
const.pyc `<module>` 计数口径问题（历史 function_count 不含 `<module>`，
fresh 重测计入所致），与本轮修复无关且未被本轮触碰。

## 5. 残留不一致

- quotation.pyc：**0 个**（143/143）。
- 已知但未列入本轮目标：while 循环 NOP-break 变体（`found=i; break` 落点为
  NOP 的 while 形态）仍会产生 `while False` 幻影（自建探针 while_variant，
  HEAD 基线即为 DEFECT、本轮前后签名一致，非本轮引入）；order.pyc `fill`、
  const.pyc `<module>`/`format_engine`、strategy_context.pyc `<module>` 等
  维持原状。

## 6. 附注

- 仅修改 core/cfg/region_analyzer.py（185 行 diff）；未 commit/push；
  未手工编辑任何 *OK.py（OK.py 与 pyc_index.json 由验证工具自动再生成）；
  未回滚任何无关更改。
