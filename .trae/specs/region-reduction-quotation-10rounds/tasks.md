# Tasks

## 预备阶段（建立基线）

- [x] T0-1 建立 quotation.pyc 原始字节码基线（`baseline/original_bytecode.txt`，复用 quotation-pyc-iteration 的 133 函数 dis 输出）
- [x] T0-2 建立区域归约路径反编译基线：用 `_identify_*_regions` 路径反编译 quotation.pyc，记录一致函数数 / 总函数数 / 成功率到 `baseline/region_baseline.txt`
  - 基线结果：total=150, matched=141, mismatched=9, missing=0, success_rate=94.00%, compile_ok=True
  - 9 个不一致函数：<module>, one_prod_to_dataframe, fill_minute_or_day_blank, build_future_fill_time, load_bars_from_hundsun, load_get_price, get_str_data, change_his_to_backward, get_date_and_count
- [x] T0-3 创建 10 轮目录骨架 `rounds/round_01..round_10/{test_engineer,repair_engineer}/`

## 轮 1 (Round 1)

- [x] T1-1 测试工程师：反编译 quotation.pyc + 字节码 diff，输出 `rounds/round_01/test_engineer/decompile_report.md`（含一致函数数、成功率、缺陷分类）
  - [x] T1-1a 编写 `decompile_quotation.py`（走区域归约路径，输出到 `/tmp/r1_decompiled.py`）
  - [x] T1-1b 编写 `exact_match_stats.py`（精确字节码 + 指令级匹配，统计一致函数数 / 总函数数）
  - [x] T1-1c 编写 `diff_detail.py`（按函数输出不一致指令 diff）
- [x] T1-2 测试工程师：从不一致函数提取 ≥10 个最小复现实例到 `rounds/round_01/test_engineer/minimal_repros/`，每个 repro 可独立 `py_compile` 且能复现缺陷（15 个 repro，10 个复现缺陷）
- [x] T1-3 修复工程师：根据 repro + decompile_report.md 定位根因到 `_identify_*_regions` / `_generate_*` 方法
- [x] T1-4 修复工程师：按区域归约算法 4 原则修复，同步更新方法 docstring（6 节模板）
  - 修复 `_detect_boolop_conditional_chain`（region_analyzer.py）— 长 and→or 混合 BoolOp 链首边界合法性验证
  - 修复 `_process_if_blocks`（region_ast_generator.py）— `_nested_if_skip` 块不再过早标记 generated_blocks
  - docstring 6 节模板更新（2 方法）
- [x] T1-5 修复工程师：回归测试（10 repro 通过 + 既有区域测试矩阵无退化）
  - repro 10→8（repro_06/09 通过）；既有矩阵 0 退化
- [x] T1-6 修复工程师：输出 `rounds/round_01/repair_engineer/fix_report.md`
- [x] T1-7 验证一致函数数 ≥ 基线，成功率单调递增（141→141，无退化）
- [x] T1-8 commit + push `rr-r01:` 到 origin/main（ec8ca39..21507b7）

## 轮 2 (Round 2)

- [x] T2-1 测试工程师：反编译 + diff（同 T1-1，输出到 round_02）
  - 141/150 = 94.00%，compile_ok=True，9 个不一致函数（与 R1 基线一致，无退化）
- [x] T2-2 测试工程师：≥10 最小复现实例
  - 21 个 repro，13 个复现缺陷（repro_01/02/03/05/06/08/09/15/16/17/19/20/21）
- [x] T2-3 修复工程师：根因分析
  - P0-1：循环体内 STORE_SUBSCR 固定指令数切分 + 循环变量重赋值被吞并
  - P0-2：三元条件链块未提取前序 STORE_* 赋值 + _detect_ternary_context 误判前序 LOAD_METHOD
- [x] T2-4 修复工程师：按算法修复 + docstring 更新
  - 修复点 1：新增 `_split_subscr_operands`（栈效应切分）+ 更新 4 处 STORE_SUBSCR 处理（region_ast_generator.py）
  - 修复点 2：`_generate_block_statements` 循环变量重赋值仅当无前序表达式时跳过（region_ast_generator.py）
  - 修复点 3：`_build_ternary_boolop_condition` 新增 pre_stmts 参数提取前序赋值（region_ast_generator.py）
  - 修复点 4：`_detect_ternary_context` 前序 STORE_* 跳过 LOAD_METHOD 扫描（region_analyzer.py）
  - docstring 更新：`_identify_ternary_regions` / `_generate_loop` / `_split_subscr_operands` + 内部注释标注 R2-P0
- [x] T2-5 修复工程师：回归测试
  - repro 13→4（repro_01/05/06/08/16/17/19/20/21 通过，9 个修复）；既有矩阵 0 退化
- [x] T2-6 修复工程师：fix_report.md（`rounds/round_02/repair_engineer/fix_report.md`）
- [x] T2-7 验证一致函数数 ≥ 轮 1（141→141，无退化；fill_minute_or_day_blank +12、get_str_data +5 指令恢复）
- [x] T2-8 commit + push `rr-r02:`（已执行）

## 轮 3 (Round 3)

- [x] T3-1 测试工程师：反编译 + diff
  - 141/150 = 94.00%，compile_ok=True，9 个不一致函数（与 R2 基线一致，无退化）
  - 产物：`rounds/round_03/test_engineer/{decompile_quotation.py, exact_match_stats.py, diff_detail.py, bc_results.json, diff_detail.txt, decompile_report.md}`
- [x] T3-2 测试工程师：≥10 最小复现实例
  - 12 个 repro，12/12 复现缺陷（覆盖 FOR_ITER 边界 / 长 or 链 / listcomp 跳转目标 / 循环后构造 / 模块级 NOP）
- [x] T3-3 修复工程师：根因分析
  - P0-B：长 or 链 `A and (B or C or ... or D)` 被 `_is_valid_2elem_mixed_chain` 误判为嵌套 if-else 而拒绝 BoolOp 链（违反原则 4 入口引用语义）；BoolOpRegion 内部块被 IfRegion all_condition_blocks 吞并（违反原则 2 每块唯一归属）
- [x] T3-4 修复工程师：按算法修复 + docstring 更新
  - 修复点 1：`_detect_boolop_conditional_chain` and(or-chain) 入口引用语义判定（A 与末 or 跳转目标相等性）
  - 修复点 2：`_identify_conditional_regions` BoolOpRegion 内部块从 all_condition_blocks 移除
  - docstring：`_detect_boolop_conditional_chain` 第 4 节 + `_identify_conditional_regions` 第 3 节新增 `[Round 3 fix P0-B]` 段
- [x] T3-5 修复工程师：回归测试
  - repro 0/12 完全通过（repro_03 +1 / repro_10 +2 指令数收窄，部分改善）；既有矩阵 0 退化（IF 73/4 BOOLOP 79/0 TERNARY 64/5 LOOP 77/3 TRY 71/9 SEQ 80/0）
- [x] T3-6 修复工程师：fix_report.md（`rounds/round_03/repair_engineer/fix_report.md`）
- [x] T3-7 验证一致函数数 ≥ 轮 2（141→141，无退化；R3 修复改变长 or 链 repro 行为但原始 quotation.pyc CFG 路径未触达，diff 不变）
- [x] T3-8 commit + push `rr-r03:`（已执行）

## 轮 4 (Round 4)

- [x] T4-1 测试工程师：反编译 + diff
  - 141/150 = 94.00%，compile_ok=True，9 个不一致函数（与 R3 基线一致，无退化）
  - 产物：`rounds/round_04/test_engineer/{decompile_quotation.py, exact_match_stats.py, diff_detail.py, bc_results.json, diff_detail.txt, decompile_report.md, closest_targets.md}`
- [x] T4-2 测试工程师：≥10 最小复现实例
  - 15 个 repro，10 个复现缺陷（repro_01/02/05/06/08/11/12/13/14/15），镜像实际 CFG 结构
- [x] T4-3 修复工程师：根因分析
  - P0-A：one_prod_to_dataframe 的 `i == 0 and len(v) == N` elif 链分裂；BoolOp 链检测被 FOR_LOOP 区域抢占块；_sb_has_body 误判前置 STORE_FAST 为 body
- [x] T4-4 修复工程师：按算法修复 + docstring 更新
  - 修复尝试：扩展 _cond_start_offset 回溯到 COMPARE_OP/IS_OP/CONTAINS_OP + _compare_op_backtrack 标志
  - 结果：导致退化（141→140，get_option_info -26），且未修复 one_prod_to_dataframe（FOR_LOOP 抢占未解决）
  - 依据 spec"若某轮出现退化，修复工程师必须先回退退化"执行回退，region_analyzer.py 恢复 R3 状态
- [x] T4-5 修复工程师：回归测试
  - quotation.pyc 141/150 无退化；既有矩阵 0 退化（IF 73/4 BOOLOP 79/0 TERNARY 64/5 LOOP 77/3 TRY 71/9 SEQ 80/0）
- [x] T4-6 修复工程师：fix_report.md（`rounds/round_04/repair_engineer/fix_report.md`）
- [x] T4-7 验证一致函数数 ≥ 轮 3（141→141，无退化；+1 目标未达成，修复尝试已回退）
- [x] T4-8 反模式自检 + 编译通过（0 新增反模式；COMPILE OK）
- [ ] T4-9 commit + push `rr-r04:`

## 轮 5 (Round 5)

- [ ] T5-1 测试工程师：反编译 + diff
- [ ] T5-2 测试工程师：≥10 最小复现实例
- [ ] T5-3 修复工程师：根因分析
- [ ] T5-4 修复工程师：按算法修复 + docstring 更新
- [ ] T5-5 修复工程师：回归测试
- [ ] T5-6 修复工程师：fix_report.md
- [ ] T5-7 验证一致函数数 ≥ 轮 4
- [ ] T5-8 commit + push `rr-r05:`

## 轮 6 (Round 6)

- [ ] T6-1 测试工程师：反编译 + diff
- [ ] T6-2 测试工程师：≥10 最小复现实例
- [ ] T6-3 修复工程师：根因分析
- [ ] T6-4 修复工程师：按算法修复 + docstring 更新
- [ ] T6-5 修复工程师：回归测试
- [ ] T6-6 修复工程师：fix_report.md
- [ ] T6-7 验证一致函数数 ≥ 轮 5
- [ ] T6-8 commit + push `rr-r06:`

## 轮 7 (Round 7)

- [ ] T7-1 测试工程师：反编译 + diff
- [ ] T7-2 测试工程师：≥10 最小复现实例
- [ ] T7-3 修复工程师：根因分析
- [ ] T7-4 修复工程师：按算法修复 + docstring 更新
- [ ] T7-5 修复工程师：回归测试
- [ ] T7-6 修复工程师：fix_report.md
- [ ] T7-7 验证一致函数数 ≥ 轮 6
- [ ] T7-8 commit + push `rr-r07:`

## 轮 8 (Round 8)

- [ ] T8-1 测试工程师：反编译 + diff
- [ ] T8-2 测试工程师：≥10 最小复现实例
- [ ] T8-3 修复工程师：根因分析
- [ ] T8-4 修复工程师：按算法修复 + docstring 更新
- [ ] T8-5 修复工程师：回归测试
- [ ] T8-6 修复工程师：fix_report.md
- [ ] T8-7 验证一致函数数 ≥ 轮 7
- [ ] T8-8 commit + push `rr-r08:`

## 轮 9 (Round 9)

- [ ] T9-1 测试工程师：反编译 + diff
- [ ] T9-2 测试工程师：≥10 最小复现实例
- [ ] T9-3 修复工程师：根因分析
- [ ] T9-4 修复工程师：按算法修复 + docstring 更新
- [ ] T9-5 修复工程师：回归测试
- [ ] T9-6 修复工程师：fix_report.md
- [ ] T9-7 验证一致函数数 ≥ 轮 8
- [ ] T9-8 commit + push `rr-r09:`

## 轮 10 (Round 10)

- [ ] T10-1 测试工程师：反编译 + diff
- [ ] T10-2 测试工程师：≥10 最小复现实例（若残留 < 10 则记录为已达成退出条件）
- [ ] T10-3 修复工程师：根因分析
- [ ] T10-4 修复工程师：按算法修复 + docstring 更新
- [ ] T10-5 修复工程师：回归测试
- [ ] T10-6 修复工程师：fix_report.md
- [ ] T10-7 验证一致函数数 ≥ 轮 9，目标 100%
- [ ] T10-8 commit + push `rr-r10:`

## 最终验证

- [ ] TF-1 共 10 次 commit + push 完成（`git log --grep="rr-r"` 计数 ≥ 10）
- [ ] TF-2 quotation.pyc 字节码一致函数数 = 总函数数（100%），或残留不一致清单写入 `final_residual.md`
- [ ] TF-3 既有区域测试矩阵无退化（IF/LOOP/TRY/WITH/MATCH/BOOLOP/TERNARY/CC/SEQ/ASSERT）
- [ ] TF-4 算法 4 原则 FULLY COMPLIANT
- [ ] TF-5 无反模式残留
- [ ] TF-6 `python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"` 编译通过
- [ ] TF-7 所有涉及的 `_identify_*_regions` / `_generate_*` 方法 docstring 已按 6 节模板更新

# Task Dependencies

- 所有轮次按 N → N+1 顺序执行（轮 N 的修复结果决定轮 N+1 的基线）
- 每轮内：测试工程师（T_N-1, T_N-2）→ 修复工程师（T_N-3..T_N-6）→ 验证 + 提交（T_N-7, T_N-8）
- T0-1..T0-3 必须在轮 1 之前完成
- 轮间无并行；轮内测试工程师与修复工程师串行
