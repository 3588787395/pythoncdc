# Tasks

## 预备阶段（建立 V3 基线）

- [ ] V3-0-1 继承 V2 的 baseline 与测试基础设施（`baseline/original_bytecode.txt` / `baseline/region_baseline.txt` 可复用）
- [ ] V3-0-2 继承 V2 的 `final_residual_v2.md` 残留清单（3 个不一致函数：get_str_data / change_his_to_backward / get_date_and_count）
- [ ] V3-0-3 复用 V2 round_20 的 `exact_match_stats.py`（含跳转目标归一化 + `<module>` 传递性委托）作为 V3 基线
- [ ] V3-0-4 创建 10 轮目录骨架 `rounds/round_21..round_30/{test_engineer,repair_engineer}/`
- [ ] V3-0-5 确认远程仓库可达性（`https://github.com/3588787395/pythoncdc`，token 鉴权已配置到 remote URL）

## 轮 21 (Round 21) — 重点攻克 get_str_data 根因 A（BUILD_CONST_KEY_MAP 消费模式建模）

### 阶段一：测试工程师

- [ ] R21-1 反编译 quotation.pyc + 字节码 diff，输出 `rounds/round_21/test_engineer/decompile_report.md`
  - [ ] R21-1a 复用 V2 的 `decompile_quotation.py` / `exact_match_stats.py`（输出到 `/tmp/r21_decompiled.py`，禁止修改反编译产物）
  - [ ] R21-1b 统计一致函数数 / 总函数数 / 成功率，确认基线 147/150=98.00% 无退化
  - [ ] R21-1c 按函数输出不一致指令 diff，聚焦 3 个残留函数（get_str_data / change_his_to_backward / get_date_and_count）
- [ ] R21-2 ≥10 最小复现实例到 `rounds/round_21/test_engineer/minimal_repros/`
  - [ ] R21-2a 重点针对 get_str_data 的 BUILD_CONST_KEY_MAP+STORE_SUBSCR dict 构造消费模式
  - [ ] R21-2b 每个 repro 可独立 py_compile 且能复现缺陷
  - [ ] R21-2c 若残留 < 10 个不一致函数，记录为已达成退出条件 E2

### 阶段二：修复工程师

- [ ] R21-3 根因分析（建模 BUILD_CONST_KEY_MAP+STORE_SUBSCR 消费模式：当 merge_block 直接进入 BUILD_CONST_KEY_MAP n + STORE_SUBSCR 时，值表达式作为整体 dict 构造语句归约）
- [ ] R21-4 按区域归约算法 4 原则修复 + 同步更新方法 docstring（6 节模板）
- [ ] R21-5 回归测试
  - [ ] R21-5a 10 个 repro 全部 py_compile 通过
  - [ ] R21-5b 既有区域测试矩阵无退化（9 fail/318 pass/11 skip）
  - [ ] R21-5c quotation.pyc 一致函数数 ≥ 147（目标 147→148，+1 单调递增）
  - [ ] R21-5d `python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"` 编译通过
- [ ] R21-6 输出 `rounds/round_21/repair_engineer/fix_report.md`

### 验证与提交

- [ ] R21-7 一致函数数 ≥ 轮 20（147→148，+1 单调递增；get_str_data -48→0 或显著减少）
- [ ] R21-8 反模式自检通过（G3：0 新增；G4：0 新增硬编码深度）
- [ ] R21-9 编译通过（IMPORT_OK）
- [ ] R21-10 commit + push `rr-r21:` 到 origin

## 轮 22 (Round 22) — get_str_data 根因 A 边界对齐（entry 不含前驱载入块）

### 阶段一：测试工程师

- [ ] R22-1 反编译 + diff（输出到 round_22，`decompile_report.md` 已生成）
- [ ] R22-2 ≥10 最小复现实例（重点针对 TernaryRegion entry 边界：应从条件测试点开始，不含前驱 price 载入块 1226-1270）

### 阶段二：修复工程师

- [ ] R22-3 根因分析（TernaryRegion@1226 区域边界对齐：entry 应从条件测试点 1274 开始，不含前驱载入块）
- [ ] R22-4 按算法修复 + docstring 更新（若 R21 已完全修复 get_str_data，本轮转为验证 + 推进 P1）
- [ ] R22-5 回归测试（quotation.pyc 一致函数数 ≥ R21；既有矩阵 0 退化；IMPORT_OK）
- [ ] R22-6 fix_report.md

### 验证与提交

- [ ] R22-7 一致函数数 ≥ 轮 21
- [ ] R22-8 反模式自检 + 编译通过（G3/G4 0 新增；IMPORT_OK）
- [ ] R22-9 commit + push `rr-r22:` 到 origin

## 轮 23 (Round 23) — get_str_data 根因 B/C（在 R21/R22 修复根因 A 基础上）

### 阶段一：测试工程师

- [ ] R23-1 反编译 + diff（输出到 round_23，`decompile_report.md` 已生成）
- [ ] R23-2 ≥10 最小复现实例（重点针对根因 B/C：兄弟 TernaryRegion 在 IfRegion else / 链式共享 merge_block）

### 阶段二：修复工程师

- [ ] R23-3 根因分析（根因 B：_process_if_blocks 遗漏兄弟表达式子区域；根因 C：链式共享 merge_block 独占标记；守卫：B 修复需跳过 parent 是嵌套 IfRegion 且 entry 也在 blocks 中的）
- [ ] R23-4 按算法修复 + docstring 更新（B 兄弟表达式子区域收集 + C 链式共享 merge_block discard；若仍退化则回退并 defer）
- [ ] R23-5 回归测试（quotation.pyc 一致函数数 ≥ R22；既有矩阵 0 退化；IMPORT_OK）
- [ ] R23-6 fix_report.md

### 验证与提交

- [ ] R23-7 一致函数数 ≥ 轮 22
- [ ] R23-8 反模式自检 + 编译通过（G3/G4 0 新增；IMPORT_OK）
- [ ] R23-9 commit + push `rr-r23:` 到 origin

## 轮 24 (Round 24) — 重点攻克 get_date_and_count 穿透缺陷（IfRegion else-branch 不穿透嵌套 LoopRegion）

### 阶段一：测试工程师

- [ ] R24-1 反编译 + diff（输出到 round_24，`decompile_report.md` 已生成）
- [ ] R24-2 ≥10 最小复现实例（重点针对 IfRegion else-branch 块收集穿透嵌套 LoopRegion）

### 阶段二：修复工程师

- [ ] R24-3 根因分析（IfRegion else-branch 块收集穿透嵌套 LoopRegion：若块 parent 是嵌套 LoopRegion，应交由嵌套 LoopRegion 统一生成）
- [ ] R24-4 按算法修复 + docstring 更新（_process_if_blocks 守卫：跳过 parent 是嵌套 LoopRegion 的块）
- [ ] R24-5 回归测试（quotation.pyc 一致函数数 ≥ R23；既有矩阵 0 退化；IMPORT_OK）
- [ ] R24-6 fix_report.md

### 验证与提交

- [ ] R24-7 一致函数数 ≥ 轮 23
- [ ] R24-8 反模式自检 + 编译通过（G3/G4 0 新增；IMPORT_OK）
- [ ] R24-9 commit + push `rr-r24:` 到 origin

## 轮 25 (Round 25) — get_date_and_count 根因 A（Loop 反向链 fall-through 校验）

### 阶段一：测试工程师

- [ ] R25-1 反编译 + diff（输出到 round_25，`decompile_report.md` 已生成）
- [ ] R25-2 ≥10 最小复现实例（重点针对 Loop 反向链 fall-through 吸收外层 IfRegion else-branch 块）

### 阶段二：修复工程师

- [ ] R25-3 根因分析（_identify_loop_regions 反向链走 fall-through 吸收外层 if/elif/else 条件块）
- [ ] R25-4 按算法修复 + docstring 更新（反向链 fall-through 校验：不吸收外层 IfRegion else-branch 块；若退化则回退并 defer）
- [ ] R25-5 回归测试（quotation.pyc 一致函数数 ≥ R24；既有矩阵 0 退化；IMPORT_OK）
- [ ] R25-6 fix_report.md

### 验证与提交

- [ ] R25-7 一致函数数 ≥ 轮 24
- [ ] R25-8 反模式自检 + 编译通过（G3/G4 0 新增；IMPORT_OK）
- [ ] R25-9 commit + push `rr-r25:` 到 origin

## 轮 26 (Round 26) — get_date_and_count 根因 B（loop_else 无 break 守卫）

### 阶段一：测试工程师

- [ ] R26-1 反编译 + diff（输出到 round_26，`decompile_report.md` 已生成）
- [ ] R26-2 ≥10 最小复现实例（重点针对 while 无 break 时 _find_loop_else 误识别 else_blocks）

### 阶段二：修复工程师

- [ ] R26-3 根因分析（_find_loop_else 在 while 无 break 时误识别 else_blocks）
- [ ] R26-4 按算法修复 + docstring 更新（loop_else 无 break 守卫：while 无 break 时不识别 else_blocks；若退化则回退并 defer）
- [ ] R26-5 回归测试（quotation.pyc 一致函数数 ≥ R25；既有矩阵 0 退化；IMPORT_OK）
- [ ] R26-6 fix_report.md

### 验证与提交

- [ ] R26-7 一致函数数 ≥ 轮 25
- [ ] R26-8 反模式自检 + 编译通过（G3/G4 0 新增；IMPORT_OK）
- [ ] R26-9 commit + push `rr-r26:` 到 origin

## 轮 27 (Round 27) — 重点攻克 change_his_to_backward（code_generator if/else 布局对齐）

### 阶段一：测试工程师

- [ ] R27-1 反编译 + diff（输出到 round_27，`decompile_report.md` 已生成）
- [ ] R27-2 ≥10 最小复现实例（重点针对 code_generator if/else 分支布局与原始字节码不一致）

### 阶段二：修复工程师

- [ ] R27-3 根因分析（code_generator if/else 分支布局未对齐：@idx296 POP_JUMP_FORWARD_IF_NOT_NONE 跳转目标 orig=330 vs new=342，@idx329 起指令完全重排）
- [ ] R27-4 按算法修复 + docstring 更新（code_generator if/else 分支生成顺序对齐原始字节码；影响面广，需配套最小复现实例回归）
- [ ] R27-5 回归测试（quotation.pyc 一致函数数 ≥ R26；既有矩阵 0 退化；IMPORT_OK）
- [ ] R27-6 fix_report.md

### 验证与提交

- [ ] R27-7 一致函数数 ≥ 轮 26
- [ ] R27-8 反模式自检 + 编译通过（G3/G4 0 新增；IMPORT_OK）
- [ ] R27-9 commit + push `rr-r27:` 到 origin

## 轮 28 (Round 28) — 综合回归与残留收尾

### 阶段一：测试工程师

- [ ] R28-1 反编译 + diff（输出到 round_28，`decompile_report.md` 已生成）
- [ ] R28-2 ≥10 最小复现实例（综合覆盖残留缺陷模式；若残留 < 10，记录为已达成退出条件 E2）

### 阶段二：修复工程师

- [ ] R28-3 根因分析（综合评估残留缺陷，定位未完全修复的根因）
- [ ] R28-4 按算法修复 + docstring 更新（若所有函数已一致，本轮转为强化回归验证）
- [ ] R28-5 回归测试（quotation.pyc 一致函数数 ≥ R27；既有矩阵 0 退化；IMPORT_OK）
- [ ] R28-6 fix_report.md

### 验证与提交

- [ ] R28-7 一致函数数 ≥ 轮 27
- [ ] R28-8 反模式自检 + 编译通过（G3/G4 0 新增；IMPORT_OK）
- [ ] R28-9 commit + push `rr-r28:` 到 origin

## 轮 29 (Round 29) — 深层结构性缺陷复查与最终修复

### 阶段一：测试工程师

- [ ] R29-1 反编译 + diff（输出到 round_29，`decompile_report.md` 已生成）
- [ ] R29-2 ≥10 最小复现实例（针对任何残留不一致函数的深层结构性缺陷）

### 阶段二：修复工程师

- [ ] R29-3 根因分析（复查任何残留不一致函数的深层结构性缺陷）
- [ ] R29-4 按算法修复 + docstring 更新（若所有函数已一致，本轮转为强化回归验证）
- [ ] R29-5 回归测试（quotation.pyc 一致函数数 ≥ R28；既有矩阵 0 退化；IMPORT_OK）
- [ ] R29-6 fix_report.md

### 验证与提交

- [ ] R29-7 一致函数数 ≥ 轮 28
- [ ] R29-8 反模式自检 + 编译通过（G3/G4 0 新增；IMPORT_OK）
- [ ] R29-9 commit + push `rr-r29:` 到 origin

## 轮 30 (Round 30) — 最终验证与收尾

### 阶段一：测试工程师

- [ ] R30-1 反编译 + diff（输出到 round_30，`decompile_report.md` 已生成；最终基线统计）
- [ ] R30-2 ≥10 最小复现实例（残留 < 10，记录为已达成退出条件 V3-E2）

### 阶段二：修复工程师

- [ ] R30-3 根因分析（最终残留缺陷定位；若已 100% 一致，输出达成声明）
- [ ] R30-4 按算法修复 + docstring 更新（若所有函数已一致，本轮转为最终验证）
- [ ] R30-5 回归测试（quotation.pyc 一致函数数 ≥ R29；既有矩阵 0 退化；IMPORT_OK）
- [ ] R30-6 `fix_report.md` + `final_residual_v3.md` 生成（残留不一致函数清单 + V4 后续迭代建议，若有）

### 验证与提交

- [ ] R30-7 一致函数数 ≥ 轮 29
- [ ] R30-8 反模式自检 + 编译通过（G3/G4 0 新增；core/ 与 HEAD 字节一致；IMPORT_OK）
- [ ] R30-9 commit + push `rr-r30:` 到 origin

## 最终验证（V3 10 轮完成后）

- [ ] V3-F1 共 10 次 commit + push 完成（rr-r21..rr-r30）
- [ ] V3-F2 quotation.pyc 字节码一致函数数达到目标（目标 150/150=100%；若未达，输出 `final_residual_v3.md` 残留清单）
- [ ] V3-F3 既有区域测试矩阵无退化（control_flow_matrix 基线 9 fail/318 pass/11 skip 全程 0 退化）
- [ ] V3-F4 算法 4 原则 FULLY COMPLIANT（自底向上归约 / 每块唯一归属 / 嵌套即抽象节点 / 入口引用语义）
- [ ] V3-F5 无反模式残留（0 新增 `_fix_/_hack_/_workaround_` 等前缀，0 新增硬编码深度上限）
- [ ] V3-F6 `python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"` 编译通过
- [ ] V3-F7 全部 11 类 `_identify_*_regions` 识别方法 docstring 维持 6 节统一模板（11/11，继承 V1 R8 / V2）

## 退出条件（每轮后检查）

- [ ] V3-E1 quotation.pyc 反编译字节码不一致函数数 = 0（100% 一致）
- [ ] V3-E2 最近一轮测试工程师可提取新增最小复现实例 < 10 个（残留不一致函数 < 10）

## 备注

- 若在 10 轮内提前达到 V3-E1+V3-E2，可在用户确认后提前退出，剩余轮次可省略
- 若 10 轮后仍未达到 V3-E1，输出 `final_residual_v3.md` 列出残留不一致清单，作为 V4 后续迭代输入
- 每轮目录必须独立，禁止跨轮合并产物；每轮 `minimal_repros/` 中的实例必须可独立运行
- 禁止修改反编译生成的产物文件
- 所有命令执行不得超过 300 秒
- 修复优先级：P0（get_str_data 消费模式建模）→ P1（get_date_and_count 穿透 + 反向链 + loop_else）→ P2（change_his_to_backward 布局对齐）
- 严格遵守根因修复顺序（A → B → C 等），禁止跳过前置根因直接修复后置根因（R12/R13/R19 教训）

# Task Dependencies

- 所有轮次按 N → N+1 顺序执行（轮 N 的修复结果决定轮 N+1 的基线）
- 每轮内：测试工程师（R_N-1, R_N-2）→ 修复工程师（R_N-3..R_N-6）→ 验证 + 提交（R_N-7..R_N-9/10）
- V3-0-4 必须在轮 21 之前完成
- 轮间无并行；轮内测试工程师与修复工程师串行
- 根因修复顺序依赖：get_str_data A → 边界对齐 → B → C；get_date_and_count 穿透 → A → B
- V1/V2 的 11 类 docstring 补全（V1 R8）作为 V3 的继承基线，V3 不重复补全，仅在修改方法时同步更新
