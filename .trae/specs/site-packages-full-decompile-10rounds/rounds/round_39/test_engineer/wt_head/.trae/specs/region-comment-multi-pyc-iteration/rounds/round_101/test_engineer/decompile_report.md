# R101 测试工程师反编译报告

- 轮次: R101（round_101 / test_engineer）
- 日期: 2026-08-25
- 工作目录: F:\Downloads\pythoncdc-main（Python 3.11.7，Windows PowerShell）
- 本轮性质: 回归验证 + 缺陷诊断 + partial 候选提名（未修改任何源码）

## 1. quotation.pyc 回归验证结果（本轮核心）

命令：`python scripts/pyc_batch_verify.py single site-packages/fly/data/quotation.pyc`

| 指标 | R98 基线（HEAD，git 确认） | R101 实测 | 变化 |
|---|---|---|---|
| decompile_status | **ok** | **partial** | 恶化 |
| match_rate | 100.00% | **97.90%** | -2.10pp |
| matched / total_functions | 143/143* | **140 / 143** | -3 函数 |
| quotationOK.py 再生成 | 是 | 是（与 HEAD 版差异 284+/175- 行） | 内容变化 |
| py_compile | 通过 | 通过 | — |

\* 索引中 `function_count=140` 为历史扫描值；`bytecode_match_rate=1.0` 要求 matched==total，故 R98 实际为全匹配。git diff 确认本次运行将 pyc_index.json 该条目从 ok/1.0 改写为 partial/0.979 —— **回归属实、可稳定复现**。

### 不一致函数清单（3 个，全部列出）

| # | 函数名 | orig/decomp 指令数 | jump_diffs | true_diffs | 首个差异指令 | 缺陷模式 |
|---|---|---|---|---|---|---|
| 1 | change_his_to_backward | 529 / 528 | 3 | **224** | idx305 `POP_TOP` → `JUMP_FORWARD(2556)` | while+if/elif 链中 `break; break` 双 break 被降级为 `pass`（HEAD 版输出保留两个 break），后续指令全部错位 |
| 2 | get_str_data | 297 / 296 | 4 | **121** | idx169 `LOAD_FAST j` → `LOAD_FAST stock_df` | for 内 `if{...continue}` 后的 `not_nan_icount = j` + `break` 结构丢失，continue 被抑制后语句重排 |
| 3 | isVaildDate | 41 / 42 | 1 | **31** | idx11 `JUMP_FORWARD` → `LOAD_CONST None` | try 内 if/else 共享尾部 `return True` 整条丢失，反编译产物恒返回 None（**语义破坏**） |

### 回归归因（只读二分探针，git archive 至临时目录逐提交实测）

以 HEAD 比较器为固定基准、仅切换各提交的 core/ 反编译器，对 quotation.pyc 探测：

| 提交 | 结果 | 说明 |
|---|---|---|
| 67adb113 rcm-r98（R98 基线） | **143/143 ✓** | 锚点确认 HEAD 比较器无罪 |
| 41bfaea9 dtc-r01（try-except-else-finally else 块识别修复） | 142/143 | **引入 isVaildDate 破坏**（true_diffs=31 与今日完全一致） |
| bd7f1d82 dtc-r03 | 125/143 | 波及面扩大至 17 个函数 |
| 18c55e62 Round 8（LOOP_BACK_EDGE continue 修复） | 123/143 | **引入 change_his_to_backward + get_str_data 破坏** |
| 96495e74 round06 之后至 HEAD | 140/143 | 中期破坏被陆续修复，唯余上述 3 个函数至今未恢复 |

结论：当前 3 个不一致是 R98 之后两笔修复的遗留副作用；中期最差 123/143，后续修复收敛到 140/143 后冻结。比较器 [R100]/[R101] 归一化规则经锚点实验排除嫌疑。

## 2. 全局累计统计（R101 实测，`pyc_batch_verify.py stats`）

| 指标 | 数值 |
|---|---|
| total_pyc / verified_pyc | 402 / 402 |
| ok_pyc | **289** |
| partial_pyc | **113** |
| failed_pyc | **0** |
| total_functions | 5175 |
| matched_functions | **4719** |
| cumulative_match_rate | **91.19%** |

### 与上一轮对比（任务给定基线：R100 时 290 ok / 112 partial / 91.27%，4723/5175）

- ok: 290 → **289**（-1，全部因 quotation.pyc ok→partial）
- partial: 112 → **113**（+1）
- failed: 0 → 0（持平）
- 累计匹配率: 91.27% → **91.19%**（-0.08pp，-4 个函数：quotation -3、const.pyc 复测时 `<module>` 新计入不匹配 -1）
- 判定：**未持平，出现真实回归**（非测量噪声；已由 git diff + 双次运行复现确认）
- 数据质量备注：索引部分条目的 function_count 为不含 `<module>` 的历史值（如 quotation 140 vs 实际 143、const 42 vs 实际 44），跨轮对比时应以 single 实测为准。

## 3. partial 候选表（113 个 partial 中按「剩余函数数升序 + 匹配率降序」取前 8）

| # | 路径（site-packages/…） | total | matched | rate | 剩余数 |
|---|---|---|---|---|---|
| 1 | IQEngine/account/order.pyc | 50* | 49 | 98.00% | 1 |
| 2 | IQCommon/const.pyc | 42* | 41 | 97.62% | 1 |
| 3 | IQEngine/core/strategy/strategy_context.pyc | 30* | 29 | 96.67% | 1 |
| 4 | IQData/plugins/plugin_system_db_tools/db_base.pyc | 28 | 27 | 96.43% | 1 |
| 5 | IQEngine/plugins/plugin_system_accounts/account_model/stock_account.pyc | 23 | 22 | 95.65% | 1 |
| 6 | IQEngine/account/trade.pyc | 22 | 21 | 95.45% | 1 |
| 7 | IQEngine/plugins/plugin_fly_data/__init__.pyc | 18 | 17 | 94.44% | 1 |
| 8 | IQCommon/logger/handlers.pyc | 17 | 16 | 94.12% | 1 |

\* 索引历史值（不含 `<module>`）；fresh 实测见下。

### 前 3 名 fresh 实测（R101 单独运行 `single`）

| 候选 | 实测 total/matched/rate/status | 剩余不一致明细 |
|---|---|---|
| order.pyc | **52 / 51 / 98.08% / partial** | `fill`: orig=69 decomp=51, true_diffs=68, 首差 idx1 `LOAD_FAST 'trade'`→`LOAD_FAST 'self'`；decomp 丢失 `amount = trade.amount` 局部别名赋值且 varnames 缺 `amount`，退化为 `LOAD_GLOBAL 'amount'`（语义破坏） |
| const.pyc | **44 / 42 / 95.45% / partial**（较索引记录恶化） | `<module>`: orig=2256 decomp=2254, true_diffs=2212, 首差 idx10 `LOAD_CONST ('Enum',)`→`LOAD_CONST None`（from-import 发射形状错误）；`format_engine`: orig=40 decomp=42, true_diffs=8, 首差 idx29 `POP_EXCEPT`→`JUMP_FORWARD` |
| strategy_context.pyc | **31 / 30 / 96.77% / partial** | `<module>`: orig=65 decomp=56, true_diffs=40, 首差 idx24；整条 `from IQEngine.utils.logger import utils, logger` import 语句被丢弃（orig instrs 24–31 共 9 条无对应），其余模块代码完全对齐 |

## 4. 本轮修复提名

**提名：site-packages/IQEngine/core/strategy/strategy_context.pyc**

理由：
1. **剩余不一致最少（并列 1）且体量最小**（31 函数），唯一不一致点为 `<module>` 的单条 import 丢弃，无级联错位（除缺失 9 条指令外两侧完全对齐），修复路径清晰。
2. **缺陷模式有代表性且可放大收益**：「多名字 from-import 整条丢弃」与 const.pyc `<module>` 的 `('Enum',)` 元组发射异常同属模块级 import 发射缺陷族——修复该族有望一次翻转 **2 个 pyc**（strategy_context + const），并降低其他 111 个 partial 中同类风险。
3. 相比 order.pyc `fill`（需动函数签名/varnames/default-args 重建，波及面大），import 发射属局部生成逻辑，回归风险更低。

建议修复工程师排查方向：AST 生成层 `_generate_import`/import 语句收集逻辑（多别名 from-import 被 drop 的条件），以及 `IMPORT_FROM ... SWAP(2) POP_TOP ... IMPORT_FROM` 序列（即 `from X import a, b` 且含 as 重绑定形态）的区域归约覆盖。

## 5. 最小复现实例（步骤 4）

归档位置：`.trae/specs/region-comment-multi-pyc-iteration/rounds/round_101/test_engineer/minimal_repros/`（14 个文件）
验证脚本：`.trae/specs/region-comment-multi-pyc-iteration/rounds/round_101/test_engineer/verify_repros.py`
运行方式：`python verify_repros.py`（MAGIC_NUMBER+12×b'\x00' 头临时 pyc → pycdc.decompile_pyc → compare_bytecode 逐函数比对）

| # | 文件 | 模式 | 结果 |
|---|---|---|---|
| 01 | repro_101_01_try_ifelse_shared_return_true.py | A-core: try+if/else 共享尾部 return True 丢失（isVaildDate 同型，首差同为 JUMP_FORWARD→LOAD_CONST None） | **DEFECT-REPRO**（true_diffs=25） |
| 02 | repro_101_02_ifelse_shared_return_no_try.py | A 控制: 无 try 同形 | MATCH |
| 03 | repro_101_03_try_elif_shared_return_false.py | A 变体: try+if/elif/else 共享尾部 return False 丢失 | **DEFECT-REPRO**（true_diffs=17） |
| 04 | repro_101_04_for_if_continue_assign_break.py | B-core: for+if{嵌套if,continue}+assign+break（get_str_data 同型，j→found 变量错位） | **DEFECT-REPRO**（true_diffs=5） |
| 05 | repro_101_05_for_if_continue_multi_tail.py | B 控制: continue+多尾部语句 | MATCH |
| 06 | repro_101_06_while_elif_double_break.py | C: while+elif 双 break（独立最小形不触发） | MATCH |
| 07 | repro_101_07_while_elif_single_break.py | C 控制: 单 break | MATCH |
| 08 | repro_101_08_for_if_double_break.py | C 变体: for 内双 break | MATCH |
| 09 | repro_101_09_for_else_continue_body.py | E: for-else 体尾 continue（get_exrights_data 同型独立不触发） | MATCH |
| 10 | repro_101_10_try_unreachable_second_return.py | D: try 内不可达第二 return | MATCH |
| 11 | repro_101_11_module_after_func_control.py | D 控制: 模块级函数间（while False 幻影发射未复现） | MATCH |
| 12 | repro_101_12_try_branch_returns_control.py | A 控制: 分支各自 return | MATCH |
| 13 | repro_101_13_for_if_continue_simple_control.py | B 控制: R100 已修简单 continue 形态仍健康 | MATCH |
| 14 | repro_101_14_for_while_double_break_rich.py | C 富上下文尝试（for>while>链+后继语句）仍未触发 | MATCH |

汇总：**3 DEFECT-REPRO / 11 NO-DEFECT 控制组**。

模式结论：
- 模式 A（try 内共享尾部常量 return 丢失）与模式 B（for-if-continue 尾随语句重排）可用 ≤20 行源码稳定复现，是 isVaildDate/get_str_data 的直接根因载体；
- 模式 C（双 break→pass）与模式 D（幻影 `while False: pass` 发射，新 OK.py 中出现 19+ 处）仅在 quotation.pyc 的完整上下文（深层嵌套/特定模块布局）下出现，最小独立形均健康，需携带更大上下文片段方可复现，列为待跟进项。

## 6. 附注

- 本轮所有验证命令均 ≤300s；未修改任何源码与 *OK.py（OK.py 由工具自动再生成）。
- 未执行 git commit/push。
- 二分探针方法：`git archive <commit>` 解包至 d:\Temp\opencode\wt\<commit>，固定使用工作区 HEAD 的 compare_bytecode，仅切换被测提交的反编译核心，共 25 个探测点。
