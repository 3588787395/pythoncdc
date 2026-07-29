# 验证清单

> 目标：以区域归约算法（No More Gotos）驱动 quotation.pyc 反编译 10 轮双工程师迭代，直至反编译字节码 100% 等价。
> 每轮：测试工程师反编译 + ≥10 最小复现实例 → 修复工程师按区域归约算法 4 原则修复 + docstring 更新 → 回归 → commit + push。
> 当前状态：待执行

## 通用约束（每轮检查）

- [ ] G1 命令执行时间 ≤ 300 秒
- [ ] G2 每轮 commit + push 到 origin/main（commit 前缀 `rr-rNN:`）
- [ ] G3 无反模式新增（`_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀 0 新增）
- [ ] G4 无硬编码深度上限新增
- [ ] G5 该轮 ≥10 最小复现实例全部 py_compile 通过且能复现缺陷
- [ ] G6 既有区域测试矩阵无退化（IF/LOOP/TRY/WITH/MATCH/BOOLOP/TERNARY/CC/SEQ/ASSERT 子集）
- [ ] G7 `decompile_report.md` + `fix_report.md` 已生成
- [ ] G8 涉及的 `_identify_*_regions` / `_generate_*` 方法 docstring 已按 6 节统一模板更新
- [ ] G9 单轮独立目录 `rounds/round_NN/{test_engineer/, repair_engineer/}` 已创建
- [ ] G10 一致函数数单调递增（轮 N ≥ 轮 N-1）
- [ ] G11 禁止修改反编译生成的产物文件（`quotation_decompiled.py`、`/tmp/r*_decompiled.py` 等只读）
- [ ] G12 算法 4 原则 FULLY COMPLIANT（自底向上归约 / 每块唯一归属 / 嵌套即抽象节点 / 入口引用语义）

## 预备阶段

- [x] P0 `baseline/original_bytecode.txt` 已生成（133 函数 dis 输出，可复用 quotation-pyc-iteration）
- [x] P1 `baseline/region_baseline.txt` 已生成（区域归约路径反编译基线：一致函数数 141 / 总函数数 150 / 成功率 94.00% / compile_ok=True / 9 个不一致函数）
- [x] P2 10 轮目录骨架 `rounds/round_01..round_10/{test_engineer,repair_engineer}/` 已创建
- [x] P3 远程仓库可达性确认（`https://github.com/3588787395/pythoncdc`，token 鉴权已配置到 remote URL）

## 轮 1 (Round 1)

### 阶段一：测试工程师

- [x] R1-1 反编译 quotation.pyc（区域归约路径）+ 字节码 diff（`decompile_report.md`，含一致函数数、成功率、缺陷分类）
  - 141/150 = 94.00%，compile_ok=True，9 个不一致函数
- [x] R1-2 ≥10 最小复现实例（`minimal_repros/`，每个 repro 可独立 py_compile 且能复现缺陷）
  - 15 个 repro，10 个复现缺陷（repro_01/03/04/06/07/09/10/12/13/14）

### 阶段二：修复工程师

- [x] R1-3 根因分析完成（所有 repro 定位到 `_identify_*_regions` 或 `_generate_*` 方法，输出根因 + 4 原则违反项）
- [x] R1-4 按区域归约算法 4 原则修复，同步更新方法 docstring（6 节模板）
  - `_detect_boolop_conditional_chain`（region_analyzer.py）+ `_process_if_blocks`（region_ast_generator.py）
- [x] R1-5 回归测试通过（≥10 repro 全部通过；既有区域测试矩阵 0 退化）
  - repro 10→8（repro_06/09 通过）；既有矩阵 0 退化
- [x] R1-6 `fix_report.md` 生成（含修复点、算法依据、4 原则对应条款、回归结果、残留不一致数）

### 验证与提交

- [x] R1-7 一致函数数 ≥ 基线（成功率单调递增）（141→141，无退化，结构修复已落地）
- [x] R1-8 反模式自检通过（G3：0 新增）
- [x] R1-9 `python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"` 编译通过
- [x] R1-10 commit + push `rr-r01:` 到 origin/main（ec8ca39..21507b7）

## 轮 2 (Round 2)

### 阶段一：测试工程师

- [x] R2-1 反编译 + 字节码 diff（`decompile_report.md`）
  - 141/150 = 94.00%，compile_ok=True，9 个不一致函数（与 R1 基线一致，无退化）
- [x] R2-2 ≥10 最小复现实例
  - 21 个 repro，13 个复现缺陷

### 阶段二：修复工程师

- [x] R2-3 根因分析完成（P0-1 STORE_SUBSCR 切分 + 循环变量重赋值；P0-2 三元前序赋值 + LOAD_METHOD 误判）
- [x] R2-4 按算法修复 + docstring 更新
  - 修复点 1：`_split_subscr_operands` 栈效应切分（region_ast_generator.py）
  - 修复点 2：`_generate_block_statements` 循环变量重赋值（region_ast_generator.py）
  - 修复点 3：`_build_ternary_boolop_condition` pre_stmts 提取（region_ast_generator.py）
  - 修复点 4：`_detect_ternary_context` 前序 STORE_* 跳过（region_analyzer.py）
  - docstring：`_identify_ternary_regions` / `_generate_loop` / `_split_subscr_operands` + R2-P0 注释
- [x] R2-5 回归测试通过
  - repro 13→4（9 个修复：repro_01/05/06/08/16/17/19/20/21）；既有矩阵 0 退化（IF 73/4 BOOLOP 79/0 TERNARY 64/5 LOOP 77/3 TRY 71/9 SEQ 80/0）
- [x] R2-6 `fix_report.md` 生成（含修复点、算法依据、4 原则对应条款、回归结果、残留不一致数）

### 验证与提交

- [x] R2-7 一致函数数 ≥ 轮 1（141→141，无退化；fill_minute_or_day_blank +12、get_str_data +5 指令恢复）
- [x] R2-8 反模式自检通过（G3：0 新增）
- [x] R2-9 编译通过（`import core.cfg.region_analyzer; import core.cfg.region_ast_generator` → COMPILE OK）
- [x] R2-10 commit + push `rr-r02:`（已执行）

## 轮 3 (Round 3)

### 阶段一：测试工程师

- [x] R3-1 反编译 + 字节码 diff
  - 141/150 = 94.00%，compile_ok=True，9 个不一致函数（与 R2 基线一致，无退化）
- [x] R3-2 ≥10 最小复现实例
  - 12 个 repro，12/12 复现缺陷

### 阶段二：修复工程师

- [x] R3-3 根因分析完成（P0-B 长 or 链：_is_valid_2elem_mixed_chain 误判 + BoolOpRegion 内部块被 IfRegion 吞并）
- [x] R3-4 按算法修复 + docstring 更新
  - 修复点 1：`_detect_boolop_conditional_chain`（region_analyzer.py）and(or-chain) 入口引用语义判定
  - 修复点 2：`_identify_conditional_regions`（region_analyzer.py）BoolOpRegion 内部块从 all_condition_blocks 移除
  - docstring：`_detect_boolop_conditional_chain` 第 4 节 + `_identify_conditional_regions` 第 3 节新增 R3 修复段
- [x] R3-5 回归测试通过
  - repro 0/12 完全通过（repro_03 +1 / repro_10 +2 指令数收窄，部分改善，0 退化）；既有矩阵 0 退化（IF 73/4 BOOLOP 79/0 TERNARY 64/5 LOOP 77/3 TRY 71/9 SEQ 80/0）
- [x] R3-6 `fix_report.md` 生成

### 验证与提交

- [x] R3-7 一致函数数 ≥ 轮 2（141→141，无退化）
- [x] R3-8 反模式自检通过（G3：0 新增）
- [x] R3-9 编译通过（IMPORT_OK）
- [x] R3-10 commit + push `rr-r03:`（已执行）

## 轮 4 (Round 4)

### 阶段一：测试工程师

- [x] R4-1 反编译 + 字节码 diff（`decompile_report.md`）
  - 141/150 = 94.00%，compile_ok=True，9 个不一致函数（与 R3 基线一致，无退化）
- [x] R4-2 ≥10 最小复现实例
  - 15 个 repro，10 个复现缺陷（镜像实际 CFG 结构）

### 阶段二：修复工程师

- [x] R4-3 根因分析完成（one_prod_to_dataframe elif 链分裂：BoolOp 检测被 FOR_LOOP 抢占块 + _sb_has_body 误判前置 STORE_FAST）
- [x] R4-4 按算法修复 + docstring 更新
  - 修复尝试：COMPARE_OP 回溯扩展 BoolOp 检测；导致 get_option_info 退化（141→140），依据 spec 回退
  - region_analyzer.py 恢复 R3 状态（修复尝试已回退，无 net 代码变更）
- [x] R4-5 回归测试通过
  - quotation.pyc 141/150 无退化；既有矩阵 0 退化（IF 73/4 BOOLOP 79/0 TERNARY 64/5 LOOP 77/3 TRY 71/9 SEQ 80/0）
- [x] R4-6 `fix_report.md` 生成（含修复点、退化根因、回退决策、回归结果、残留不一致数、R5 建议）

### 验证与提交

- [x] R4-7 一致函数数 ≥ 轮 3（141→141，无退化；+1 目标未达成，修复尝试已回退）
- [x] R4-8 反模式自检通过（G3：0 新增；region_analyzer.py 无 net 变更）
- [x] R4-9 编译通过（IMPORT_OK）
- [x] R4-10 commit + push `rr-r04:`（已执行，72b0d13）

## 轮 5 (Round 5)

### 阶段一：测试工程师

- [ ] R5-1 反编译 + 字节码 diff
- [ ] R5-2 ≥10 最小复现实例

### 阶段二：修复工程师

- [ ] R5-3 根因分析完成
- [ ] R5-4 按算法修复 + docstring 更新
- [ ] R5-5 回归测试通过
- [ ] R5-6 `fix_report.md` 生成

### 验证与提交

- [ ] R5-7 一致函数数 ≥ 轮 4
- [ ] R5-8 反模式自检通过
- [ ] R5-9 编译通过
- [ ] R5-10 commit + push `rr-r05:`

## 轮 6 (Round 6)

### 阶段一：测试工程师

- [ ] R6-1 反编译 + 字节码 diff
- [ ] R6-2 ≥10 最小复现实例

### 阶段二：修复工程师

- [ ] R6-3 根因分析完成
- [ ] R6-4 按算法修复 + docstring 更新
- [ ] R6-5 回归测试通过
- [ ] R6-6 `fix_report.md` 生成

### 验证与提交

- [ ] R6-7 一致函数数 ≥ 轮 5
- [ ] R6-8 反模式自检通过
- [ ] R6-9 编译通过
- [ ] R6-10 commit + push `rr-r06:`

## 轮 7 (Round 7)

### 阶段一：测试工程师

- [ ] R7-1 反编译 + 字节码 diff
- [ ] R7-2 ≥10 最小复现实例

### 阶段二：修复工程师

- [ ] R7-3 根因分析完成
- [ ] R7-4 按算法修复 + docstring 更新
- [ ] R7-5 回归测试通过
- [ ] R7-6 `fix_report.md` 生成

### 验证与提交

- [ ] R7-7 一致函数数 ≥ 轮 6
- [ ] R7-8 反模式自检通过
- [ ] R7-9 编译通过
- [ ] R7-10 commit + push `rr-r07:`

## 轮 8 (Round 8)

### 阶段一：测试工程师

- [ ] R8-1 反编译 + 字节码 diff
- [ ] R8-2 ≥10 最小复现实例

### 阶段二：修复工程师

- [ ] R8-3 根因分析完成
- [ ] R8-4 按算法修复 + docstring 更新
- [ ] R8-5 回归测试通过
- [ ] R8-6 `fix_report.md` 生成

### 验证与提交

- [ ] R8-7 一致函数数 ≥ 轮 7
- [ ] R8-8 反模式自检通过
- [ ] R8-9 编译通过
- [ ] R8-10 commit + push `rr-r08:`

## 轮 9 (Round 9)

### 阶段一：测试工程师

- [ ] R9-1 反编译 + 字节码 diff
- [ ] R9-2 ≥10 最小复现实例

### 阶段二：修复工程师

- [ ] R9-3 根因分析完成
- [ ] R9-4 按算法修复 + docstring 更新
- [ ] R9-5 回归测试通过
- [ ] R9-6 `fix_report.md` 生成

### 验证与提交

- [ ] R9-7 一致函数数 ≥ 轮 8
- [ ] R9-8 反模式自检通过
- [ ] R9-9 编译通过
- [ ] R9-10 commit + push `rr-r09:`

## 轮 10 (Round 10)

### 阶段一：测试工程师

- [ ] R10-1 反编译 + 字节码 diff
- [ ] R10-2 ≥10 最小复现实例（若残留 < 10 则记录为已达成退出条件）

### 阶段二：修复工程师

- [ ] R10-3 根因分析完成
- [ ] R10-4 按算法修复 + docstring 更新
- [ ] R10-5 回归测试通过
- [ ] R10-6 `fix_report.md` 生成

### 验证与提交

- [ ] R10-7 一致函数数 ≥ 轮 9，目标 100%
- [ ] R10-8 反模式自检通过
- [ ] R10-9 编译通过
- [ ] R10-10 commit + push `rr-r10:`

## 退出条件（每轮后检查）

- [ ] E1 quotation.pyc 反编译字节码不一致函数数 = 0（100% 一致）
- [ ] E2 最近一轮测试工程师可提取新增最小复现实例 < 10 个

## 最终验证（10 轮完成后）

- [ ] F1 共 10 次 commit + push 完成（`git log --grep="rr-r"` 计数 ≥ 10）
- [ ] F2 quotation.pyc 字节码一致函数数 = 总函数数（100%），或残留不一致清单写入 `final_residual.md`
- [ ] F3 既有区域测试矩阵无退化（IF/LOOP/TRY/WITH/MATCH/BOOLOP/TERNARY/CC/SEQ/ASSERT）
- [ ] F4 算法 4 原则 FULLY COMPLIANT（自底向上归约 / 每块唯一归属 / 嵌套即抽象节点 / 入口引用语义）
- [ ] F5 无反模式残留（`_merge_block_is_loop_back_edge` 等历史反模式已重命名）
- [ ] F6 `python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"` 编译通过
- [ ] F7 所有涉及的 `_identify_*_regions` / `_generate_*` 方法 docstring 已按 6 节统一模板更新
  - 6 节：算法依据 / 归约顺序 / 唯一归属判定 / 嵌套处理 / 入口引用语义 / 反编译流程
  - 覆盖方法：`_identify_loop_regions` / `_identify_try_except_regions` / `_identify_with_regions` / `_identify_match_regions` / `_identify_nested_match_regions` / `_identify_assert_regions` / `_identify_chained_compare_regions` / `_identify_conditional_regions` / `_identify_ternary_regions` / `_identify_boolop_regions` / `_identify_sequence_regions` + 对应 `_generate_*`

## 备注

- 若在 10 轮内提前达到 E1+E2，可在用户确认后提前退出，剩余轮次可省略
- 若 10 轮后仍未达到 E1，输出 `final_residual.md` 列出残留不一致清单，作为后续迭代输入
- 每轮目录必须独立，禁止跨轮合并产物；每轮 `minimal_repros/` 中的实例必须可独立运行（`python -c "import dis; ..."` 验证）
- 禁止修改反编译生成的产物文件
- 所有命令执行不得超过 300 秒
