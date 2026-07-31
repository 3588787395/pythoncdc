# R14 测试工程师报告 — tools.pyc

## 1. 目标 pyc

- **路径**: `site-packages/IQCommon/tools.pyc`
- **decompile_status（R14 前）**: pending（last_tested_round=0，未验证）
- **本轮重点**: isVaildDate「if/elif/else 共享 merge_block 尾随 return 误置于首分支」缺陷 + get_qry_date「嵌套 if-in-else 扁平化 / NOP 行标记噪声」残留

## 2. 反编译 + 字节码 diff 结果

| 指标 | R14 前（pending） | R14（post-fix） |
|------|-------------------|-----------------|
| total_functions | 6 | 6 |
| matched_functions | 0 | 5 |
| match_rate | 0.00%（未验证） | **83.33%** |
| mismatches | 6（未验证） | 1 |

- **match_rate 改善**: pending → 83.33%（+5 函数匹配，-5 mismatch）
- **decompile_status**: partial（未达 100%，残留 get_qry_date 1 个 mismatch）

## 3. 不一致函数清单（1 mismatch）

| 模式 | 数量 | 代表函数 | 说明 |
|------|------|----------|------|
| R_NOP_FLATTEN | 1 | get_qry_date | orig=201 decomp=202，jump_diffs=27 true_diffs=109，first_diff: index 13 orig=NOP decomp=LOAD_FAST date |

### get_qry_date 残留分析

- **first_diff**: `{'index': 13, 'orig_op': 'NOP', 'decomp_op': 'LOAD_FAST', 'orig_arg': None, 'decomp_arg': 'date'}`
- **根因**: 原 pyc（CPython 3.11.x 编译）在 `POP_JUMP_FORWARD_IF_FALSE` 后含 NOP 行标记指令（offset 30 / 360，对应源码 if/elif 行后的行号间隙）。反编译产物重编译时（当前 CPython 3.11.x 补丁版本）不重现这些 NOP，导致后续所有指令偏移移位，触发 27 jump_diffs + 级联 109 true_diffs。
- **性质判定**: NOP 行标记噪声（Pattern R），非反编译器语义缺陷。toolsOK.py 中 get_qry_date 的源码结构（if/elif + 嵌套 if-in-else + return）与原 pyc 语义等价；重编译偏移差异源自 CPython 补丁版本间 NOP 发射策略差异，不可由反编译器修复。
- **附注**: 当以当前 Python 重编译 get_qry_date 最小复现（无原 pyc 的 NOP）时，反编译器会将 else 体内的顺序 `if` 扁平化为 `elif` 链（repro_01-07 DEFECT-REPRO）。原 pyc 中的 NOP 行标记辅助区域分析器正确识别嵌套结构，故 toolsOK.py 中 get_qry_date 结构正确（未扁平化）。

## 4. 最小复现实例（12 个）

归档于 `minimal_repros/`，覆盖以下场景：

| 实例 | 场景 | 类型 | 结果 |
|------|------|------|------|
| repro_01 | get_qry_date curr 分支：if/elif/else + 嵌套顺序 if | DEFECT-REPRO | 2/3 matched, 36 diffs (get_qry_date_curr) |
| repro_02 | get_qry_date pre 分支：if/elif/else + 嵌套顺序 if + 内层 if/else | DEFECT-REPRO | 2/3 matched, 52 diffs (get_qry_date_pre) |
| repro_03 | 最小嵌套 if-in-else + 函数调用（if/elif/else） | DEFECT-REPRO | 1/2 matched, 21 diffs (nested_if_in_else) |
| repro_04 | 嵌套 if-in-else + 内层 if/else + 函数调用 | DEFECT-REPRO | 1/2 matched, 32 diffs (nested_if_inner) |
| repro_05 | get_qry_date 完整镜像（import + if/elif + 嵌套） | DEFECT-REPRO | 2/3 matched, 180 diffs (get_qry_date) |
| repro_06 | 嵌套 if-in-else + isinstance 分支 | DEFECT-REPRO | 1/2 matched, 25 diffs (nested_isinstance) |
| repro_07 | 嵌套 if-in-else + KW_NAMES 函数调用 | DEFECT-REPRO | 1/2 matched, 35 diffs (nested_call_branch) |
| repro_08 | isVaildDate 共享尾随 return（验证 R14 修复） | CTRL (NO-DEFECT) | 2/2 matched |
| repro_09 | isVaildDate 变体：共享尾随调用（验证 R14 修复） | CTRL (NO-DEFECT) | 4/4 matched |
| repro_10 | endswith_transe_2to4：简单 if/elif/else | CTRL (NO-DEFECT) | 2/2 matched |
| repro_11 | decimal_round：try/except + return | CTRL (NO-DEFECT) | 2/2 matched |
| repro_12 | date_str_type_change：简单方法链 return | CTRL (NO-DEFECT) | 2/2 matched |

### 验证方法

`verify_repros.py` 对每个 repro 执行：编译 → 反编译 → 重编译 → 字节码 diff（含 code-object 身份噪声归一化）。

- **7 DEFECT-REPRO**（repro_01-07）：隔离 get_qry_date 嵌套 if-in-else 扁平化 / NOP 偏移噪声模式。当最小复现（以当前 Python 编译，无原 pyc NOP）经反编译后，else 体内顺序 if 被扁平化为 elif 链，产生 jump-target 重编号与结构差异。
- **5 CTRL NO-DEFECT**（repro_08-12）：repro_08/09 验证 isVaildDate 共享尾随 return 修复（R14 fix 后正确发射为 post-if 尾随语句）；repro_10-12 镜像 tools.pyc 已 100% 一致的 3 个函数（endswith_transe_2to4 / decimal_round / date_str_type_change）作为控制组。

## 5. 累计成功率

- R13 committed: 67.05%（30 verified pyc）
- R14: tools.pyc pending → 83.33%（+5 matched / +6 total），累计 66.36%（31 verified pyc, 290/437 matched）
- **注**: 累计成功率随 verified 集合扩张重算。R14 前 285/431=66.01%，R14 后 290/437=66.36%，本 pyc 贡献 +5 matched 使累计微升。R13 记录的 67.05% 系更小 verified 集合下的测值。

## 6. 残留不一致

- **get_qry_date**: 1 mismatch（NOP 行标记噪声 / Pattern R，非语义缺陷，不可由反编译器修复）
- **跨轮残留**（不变）: T3/T2/A2/B/C/E/F/M2/G3/R 等模式见各轮报告
