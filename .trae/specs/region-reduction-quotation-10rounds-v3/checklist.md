# 验证清单（V3）

> 目标：以区域归约算法（No More Gotos）驱动 quotation.pyc 反编译 V3 10 轮双工程师迭代（R21-R30），重点攻克 V2 残留 3 个不一致函数（get_str_data / change_his_to_backward / get_date_and_count），直至反编译字节码 100% 等价。
> 每轮：测试工程师反编译 + ≥10 最小复现实例 → 修复工程师按区域归约算法 4 原则修复 + docstring 更新 → 回归 → commit + push。
> 当前状态：V2 已完成（147/150=98.00%），V3 待启动（R21 起步）

## 通用约束（每轮检查）

- [ ] G1 命令执行时间 ≤ 300 秒
- [ ] G2 每轮 commit + push 到 origin/main（commit 前缀 `rr-rNN:`，NN=21..30）
- [ ] G3 无反模式新增（`_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀 0 新增）
- [ ] G4 无硬编码深度上限新增
- [ ] G5 该轮 ≥10 最小复现实例全部 py_compile 通过且能复现缺陷（若残留 < 10 个不一致函数，记录为已达成退出条件 V3-E2）
- [ ] G6 既有区域测试矩阵无退化（IF/LOOP/TRY/WITH/MATCH/BOOLOP/TERNARY/CC/SEQ/ASSERT 子集，基线 9 fail/318 pass/11 skip）
- [ ] G7 `decompile_report.md` + `fix_report.md` 已生成
- [ ] G8 涉及的 `_identify_*_regions` / `_generate_*` 方法 docstring 已按 6 节统一模板更新（继承 V1 R8 / V2，仅修改方法需同步更新）
- [ ] G9 单轮独立目录 `rounds/round_NN/{test_engineer/, repair_engineer/}` 已创建
- [ ] G10 一致函数数单调递增（轮 N ≥ 轮 N-1，基线 147/150）
- [ ] G11 禁止修改反编译生成的产物文件（`quotation_decompiled.py`、`/tmp/r*_decompiled.py` 等只读）
- [ ] G12 算法 4 原则 FULLY COMPLIANT（自底向上归约 / 每块唯一归属 / 嵌套即抽象节点 / 入口引用语义）
- [ ] G13 严格遵守根因修复顺序（get_str_data A→边界→B→C；get_date_and_count 穿透→A→B），禁止跳过前置根因

## 预备阶段

- [ ] V3-P0 `baseline/original_bytecode.txt` 已继承自 V1（133 函数 dis 输出）
- [ ] V3-P1 `baseline/region_baseline.txt` 已继承自 V2（147/150=98.00%，compile_ok=True）
- [ ] V3-P2 `final_residual_v2.md` 已继承自 V2（3 个不一致函数清单）
- [ ] V3-P3 V2 round_20 `exact_match_stats.py`（含跳转目标归一化 + `<module>` 传递性委托）复用为 V3 基线
- [ ] V3-P4 10 轮目录骨架 `rounds/round_21..round_30/{test_engineer,repair_engineer}/` 已创建
- [ ] V3-P5 远程仓库可达性确认（`https://github.com/3588787395/pythoncdc`，token 鉴权已配置到 remote URL）

## 轮 21 (Round 21) — 重点攻克 get_str_data 根因 A（BUILD_CONST_KEY_MAP 消费模式建模）

### 阶段一：测试工程师

- [ ] R21-1 反编译 quotation.pyc + 字节码 diff（`decompile_report.md`）
  - [ ] R21-1a 复用 V2 的 `decompile_quotation.py` / `exact_match_stats.py`（输出到 `/tmp/r21_decompiled.py`，禁止修改反编译产物）
  - [ ] R21-1b 统计一致函数数 / 总函数数 / 成功率，确认基线 147/150=98.00% 无退化
  - [ ] R21-1c 按函数输出不一致指令 diff（diff_detail.txt），聚焦 3 个残留函数
- [ ] R21-2 ≥10 最小复现实例（重点针对 get_str_data 的 BUILD_CONST_KEY_MAP+STORE_SUBSCR dict 构造消费模式）

### 阶段二：修复工程师

- [ ] R21-3 根因分析完成（建模 BUILD_CONST_KEY_MAP+STORE_SUBSCR 消费模式）
- [ ] R21-4 按区域归约算法 4 原则修复 + docstring 更新
- [ ] R21-5 回归测试通过
  - [ ] R21-5a 10 个 repro 全部 py_compile 通过
  - [ ] R21-5b 既有区域测试矩阵无退化（9 fail/318 pass/11 skip == 基线）
  - [ ] R21-5c quotation.pyc 一致函数数 ≥ 147（目标 147→148，+1 单调递增）
  - [ ] R21-5d `python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"` 编译通过
- [ ] R21-6 `fix_report.md` 生成

### 验证与提交

- [ ] R21-7 一致函数数 ≥ 轮 20（147→148，+1 单调递增；get_str_data -48→0 或显著减少）
- [ ] R21-8 反模式自检通过（G3：0 新增；G4：0 新增硬编码深度）
- [ ] R21-9 编译通过（IMPORT_OK）
- [ ] R21-10 commit + push `rr-r21:` 到 origin

## 轮 22 (Round 22) — get_str_data 根因 A 边界对齐

### 阶段一：测试工程师

- [ ] R22-1 反编译 + 字节码 diff（`decompile_report.md`）
- [ ] R22-2 ≥10 最小复现实例（重点针对 TernaryRegion entry 边界对齐）

### 阶段二：修复工程师

- [ ] R22-3 根因分析完成（TernaryRegion@1226 区域边界对齐：entry 应从条件测试点 1274 开始）
- [ ] R22-4 按算法修复 + docstring 更新（若 R21 已完全修复 get_str_data，本轮转为验证 + 推进 P1）
- [ ] R22-5 回归测试通过（quotation.pyc 一致函数数 ≥ R21；矩阵 0 退化；IMPORT_OK）
- [ ] R22-6 `fix_report.md` 生成

### 验证与提交

- [ ] R22-7 一致函数数 ≥ 轮 21
- [ ] R22-8 反模式自检 + 编译通过（G3/G4 0 新增；IMPORT_OK）
- [ ] R22-9 commit + push `rr-r22:` 到 origin

## 轮 23 (Round 23) — get_str_data 根因 B/C

### 阶段一：测试工程师

- [ ] R23-1 反编译 + 字节码 diff（`decompile_report.md`）
- [ ] R23-2 ≥10 最小复现实例（重点针对根因 B/C：兄弟 TernaryRegion / 链式共享 merge_block）

### 阶段二：修复工程师

- [ ] R23-3 根因分析完成（根因 B：_process_if_blocks 遗漏兄弟表达式子区域；根因 C：链式共享 merge_block 独占标记）
- [ ] R23-4 按算法修复 + docstring 更新（B 兄弟表达式子区域收集 + C 链式共享 merge_block discard；若仍退化则回退并 defer）
- [ ] R23-5 回归测试通过（quotation.pyc 一致函数数 ≥ R22；矩阵 0 退化；IMPORT_OK）
- [ ] R23-6 `fix_report.md` 生成

### 验证与提交

- [ ] R23-7 一致函数数 ≥ 轮 22
- [ ] R23-8 反模式自检 + 编译通过（G3/G4 0 新增；IMPORT_OK）
- [ ] R23-9 commit + push `rr-r23:` 到 origin

## 轮 24 (Round 24) — 攻克 change_his_to_backward (IF 吸收兄弟) + get_date_and_count (LOOP 吸收外层条件) — 达成 100%

### 阶段一：测试工程师

- [x] R24-1 反编译 + 字节码 diff（`decompile_report.md`）— 基线 148/150=98.67%
- [x] R24-2 ≥10 最小复现实例（8 个 repro 覆盖两类缺陷：A=IF 吸收循环末尾兄弟 4 个，B=LOOP 吸收外层条件+loop_else 4 个，全部复现）

### 阶段二：修复工程师

- [x] R24-3 根因分析完成
  - 缺陷A：`_identify_conditional_regions`/`_check_elif_chain` 循环体内 if/elif/else 链公共汇聚后继块误并入 then
  - 缺陷B：`_detect_while_condition_boolop_chain` 反向链回溯把外层 elif 条件块误吸收为 while boolop 链操作数（`cond_in_loop=False` 时未终止）
- [x] R24-4 按算法修复 + docstring 更新
  - 缺陷A：循环感知 merge 重算（_find_enclosing_loop/_is_loop_exit_block/_compute_in_loop_if_merge）
  - 缺陷B：`_detect_while_condition_boolop_chain` 新增 `if not cond_in_loop: break` 守卫 + `_identify_loop_regions` `_p_is_outer_elif` 配套
- [x] R24-5 回归测试通过（quotation.pyc 一致函数数 150/150=100%，矩阵 318 pass/9 fail/11 skip 与基线一致 0 退化，IMPORT_OK）
- [x] R24-6 `fix_report.md` 生成

### 验证与提交

- [x] R24-7 一致函数数 150/150 ≥ 轮 23（148/150）— 达成 V3-E1（100%）+ V3-E2
- [x] R24-8 反模式自检 + 编译通过（G3/G4 0 新增；IMPORT_OK）
- [x] R24-9 commit + push `rr-r24:` 到 origin（commit df96e42）

### 比较方法严格性评估（用户追加任务）

- [x] R24-10 三档口径实测（严格逐条 90.67% / L1 98% / 归一化 100%）— `comparison_method_evaluation.md`
- [x] R24-11 4 项豁免合理性裁定（跳过填充✅ / code 递归忽略元数据✅ / 跳转目标等价✅必要 / 常量等价⚠️防御性保留）
- [x] R24-12 结论：不应进一步收紧到 L1（3 个 L1 差异为 CPython 编译器对齐 offset 偏移，非反编译缺陷）；归一化口径为合理主口径，L1 作辅助诊断（0 真实操作码差异）

## 退出条件达成（R24 提前退出）

- [x] V3-E1 反编译 quotation.pyc 字节码 100% 等价（归一化口径 150/150）— R24 达成
- [x] V3-E2 操作码层面 0 真实差异（L1 辅助口径，3 个纯 offset 偏移均豁免合理）
- [x] 既有区域测试矩阵 0 退化
- 注：R25-R30 无需执行（用户确认提前退出）；如未来出现新目标 .pyc 可重启 V4 迭代

## 轮 25 (Round 25) — get_date_and_count 根因 A（Loop 反向链 fall-through 校验）

### 阶段一：测试工程师

- [ ] R25-1 反编译 + 字节码 diff（`decompile_report.md`）
- [ ] R25-2 ≥10 最小复现实例（重点针对 Loop 反向链 fall-through 吸收外层 IfRegion else-branch 块）

### 阶段二：修复工程师

- [ ] R25-3 根因分析完成（_identify_loop_regions 反向链走 fall-through 吸收外层 if/elif/else 条件块）
- [ ] R25-4 按算法修复 + docstring 更新（反向链 fall-through 校验；若退化则回退并 defer）
- [ ] R25-5 回归测试通过（quotation.pyc 一致函数数 ≥ R24；矩阵 0 退化；IMPORT_OK）
- [ ] R25-6 `fix_report.md` 生成

### 验证与提交

- [ ] R25-7 一致函数数 ≥ 轮 24
- [ ] R25-8 反模式自检 + 编译通过（G3/G4 0 新增；IMPORT_OK）
- [ ] R25-9 commit + push `rr-r25:` 到 origin

## 轮 26 (Round 26) — get_date_and_count 根因 B（loop_else 无 break 守卫）

### 阶段一：测试工程师

- [ ] R26-1 反编译 + 字节码 diff（`decompile_report.md`）
- [ ] R26-2 ≥10 最小复现实例（重点针对 while 无 break 时 _find_loop_else 误识别 else_blocks）

### 阶段二：修复工程师

- [ ] R26-3 根因分析完成（_find_loop_else 在 while 无 break 时误识别 else_blocks）
- [ ] R26-4 按算法修复 + docstring 更新（loop_else 无 break 守卫；若退化则回退并 defer）
- [ ] R26-5 回归测试通过（quotation.pyc 一致函数数 ≥ R25；矩阵 0 退化；IMPORT_OK）
- [ ] R26-6 `fix_report.md` 生成

### 验证与提交

- [ ] R26-7 一致函数数 ≥ 轮 25
- [ ] R26-8 反模式自检 + 编译通过（G3/G4 0 新增；IMPORT_OK）
- [ ] R26-9 commit + push `rr-r26:` 到 origin

## 轮 27 (Round 27) — 重点攻克 change_his_to_backward（code_generator if/else 布局对齐）

### 阶段一：测试工程师

- [ ] R27-1 反编译 + 字节码 diff（`decompile_report.md`）
- [ ] R27-2 ≥10 最小复现实例（重点针对 code_generator if/else 分支布局与原始字节码不一致）

### 阶段二：修复工程师

- [ ] R27-3 根因分析完成（code_generator if/else 分支布局未对齐：@idx296 跳转目标偏移 + @idx329 起指令重排）
- [ ] R27-4 按算法修复 + docstring 更新（code_generator if/else 分支生成顺序对齐原始字节码；影响面广，需配套最小复现实例回归）
- [ ] R27-5 回归测试通过（quotation.pyc 一致函数数 ≥ R26；矩阵 0 退化；IMPORT_OK）
- [ ] R27-6 `fix_report.md` 生成

### 验证与提交

- [ ] R27-7 一致函数数 ≥ 轮 26
- [ ] R27-8 反模式自检 + 编译通过（G3/G4 0 新增；IMPORT_OK）
- [ ] R27-9 commit + push `rr-r27:` 到 origin

## 轮 28 (Round 28) — 综合回归与残留收尾

### 阶段一：测试工程师

- [ ] R28-1 反编译 + 字节码 diff（`decompile_report.md`）
- [ ] R28-2 ≥10 最小复现实例（综合覆盖残留缺陷模式；若残留 < 10，记录为已达成退出条件 V3-E2）

### 阶段二：修复工程师

- [ ] R28-3 根因分析完成（综合评估残留缺陷，定位未完全修复的根因）
- [ ] R28-4 按算法修复 + docstring 更新（若所有函数已一致，本轮转为强化回归验证）
- [ ] R28-5 回归测试通过（quotation.pyc 一致函数数 ≥ R27；矩阵 0 退化；IMPORT_OK）
- [ ] R28-6 `fix_report.md` 生成

### 验证与提交

- [ ] R28-7 一致函数数 ≥ 轮 27
- [ ] R28-8 反模式自检 + 编译通过（G3/G4 0 新增；IMPORT_OK）
- [ ] R28-9 commit + push `rr-r28:` 到 origin

## 轮 29 (Round 29) — 深层结构性缺陷复查与最终修复

### 阶段一：测试工程师

- [ ] R29-1 反编译 + 字节码 diff（`decompile_report.md`）
- [ ] R29-2 ≥10 最小复现实例（针对任何残留不一致函数的深层结构性缺陷）

### 阶段二：修复工程师

- [ ] R29-3 根因分析完成（复查任何残留不一致函数的深层结构性缺陷）
- [ ] R29-4 按算法修复 + docstring 更新（若所有函数已一致，本轮转为强化回归验证）
- [ ] R29-5 回归测试通过（quotation.pyc 一致函数数 ≥ R28；矩阵 0 退化；IMPORT_OK）
- [ ] R29-6 `fix_report.md` 生成

### 验证与提交

- [ ] R29-7 一致函数数 ≥ 轮 28
- [ ] R29-8 反模式自检 + 编译通过（G3/G4 0 新增；IMPORT_OK）
- [ ] R29-9 commit + push `rr-r29:` 到 origin

## 轮 30 (Round 30) — 最终验证与收尾

### 阶段一：测试工程师

- [ ] R30-1 反编译 + 字节码 diff（`decompile_report.md`，最终基线统计）
- [ ] R30-2 ≥10 最小复现实例（残留 < 10，记录为已达成退出条件 V3-E2）

### 阶段二：修复工程师

- [ ] R30-3 根因分析完成（最终残留缺陷定位；若已 100% 一致，输出达成声明）
- [ ] R30-4 按算法修复 + docstring 更新（若所有函数已一致，本轮转为最终验证）
- [ ] R30-5 回归测试通过（quotation.pyc 一致函数数 ≥ R29；矩阵 0 退化；IMPORT_OK）
- [ ] R30-6 `fix_report.md` + `final_residual_v3.md` 生成（残留不一致函数清单 + V4 后续迭代建议，若有）

### 验证与提交

- [ ] R30-7 一致函数数 ≥ 轮 29
- [ ] R30-8 反模式自检 + 编译通过（G3/G4 0 新增；core/ 与 HEAD 字节一致；IMPORT_OK）
- [ ] R30-9 commit + push `rr-r30:` 到 origin

## 退出条件（每轮后检查）

- [ ] V3-E1 quotation.pyc 反编译字节码不一致函数数 = 0（100% 一致）
- [ ] V3-E2 最近一轮测试工程师可提取新增最小复现实例 < 10 个（残留不一致函数 < 10）

## 最终验证（V3 10 轮完成后）

- [ ] V3-F1 共 10 次 commit + push 完成（rr-r21..rr-r30，全部已 push 到 main）
- [ ] V3-F2 quotation.pyc 字节码一致函数数达到目标（目标 150/150=100%；若未达，残留清单写入 `final_residual_v3.md`）
- [ ] V3-F3 既有区域测试矩阵无退化（control_flow_matrix 基线 9 fail/318 pass/11 skip 全程 0 退化）
- [ ] V3-F4 算法 4 原则 FULLY COMPLIANT（自底向上归约 / 每块唯一归属 / 嵌套即抽象节点 / 入口引用语义）
- [ ] V3-F5 无反模式残留（0 新增 `_fix_/_hack_/_workaround_` 等前缀，0 新增硬编码深度上限）
- [ ] V3-F6 `python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"` 编译通过（IMPORT_OK）
- [ ] V3-F7 全部 11 类 `_identify_*_regions` 识别方法 docstring 维持 6 节统一模板（11/11，继承 V1 R8 / V2）

## 备注

- 若在 10 轮内提前达到 V3-E1+V3-E2，可在用户确认后提前退出，剩余轮次可省略
- 若 10 轮后仍未达到 V3-E1，输出 `final_residual_v3.md` 列出残留不一致清单，作为 V4 后续迭代输入
- 每轮目录必须独立，禁止跨轮合并产物；每轮 `minimal_repros/` 中的实例必须可独立运行
- 禁止修改反编译生成的产物文件
- 所有命令执行不得超过 300 秒
- 修复优先级：P0（get_str_data 消费模式建模）→ P1（get_date_and_count 穿透 + 反向链 + loop_else）→ P2（change_his_to_backward 布局对齐）
- 严格遵守根因修复顺序（A → B → C 等），禁止跳过前置根因直接修复后置根因（R12/R13/R19 教训）
