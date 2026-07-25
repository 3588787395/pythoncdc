# Tasks

> 目标：对 `/workspace/quotation.pyc` 执行 10 轮「测试工程师 + 修复工程师」迭代，直至反编译字节码 100% 等价。
> 每轮：测试工程师反编译 + 提取 10+ 最小复现实例 → 修复工程师按区域归约算法修复 → 回归 → commit + push。
> 所有命令执行不得超过 300 秒。
> 每轮必须提交并 push 到远程。
> **状态：执行中（预备阶段完成，进入 Round 1）**

## 通用任务模板（每轮共用）

- [ ] T1: 测试工程师反编译 quotation.pyc（输出 `decompile_report.md`）
  - 执行 `python pycdc.py /workspace/quotation.pyc`（≤60s）
  - 反编译产物字节码 vs 原 pyc 字节码 diff
  - 不一致清单（函数名 + 偏移 + 字节码模式）
- [ ] T2: 测试工程师提取 ≥10 个最小复现实例（输出 `minimal_repros/`）
  - 每个实例：最小 `.py` 源码 → compile → 反编译 → 字节码 diff
  - 归档至 `rounds/round_NN/test_engineer/minimal_repros/repro_NN_<area>_<feature>.py`
- [ ] T3: 修复工程师分析 + 定位（依赖 T1/T2）
  - 对每个不一致定位到 `_identify_*_regions` 或 `_generate_*` 方法
  - 输出根因分析（涉及的区域类型 + 算法偏离点）
- [ ] T4: 修复工程师实施修复
  - 按区域归约算法 4 原则完善逻辑（禁止补丁）
  - 同步更新方法 docstring（统一 6 项模板）
- [ ] T5: 修复工程师回归测试（≤280s）
  - 该轮 10+ 最小复现实例全部通过
  - 既有测试矩阵无退化（IF/LOOP/TRY/WITH/MATCH/BOOLOP/TERNARY/CC/SEQ/ASSERT 子集）
- [ ] T6: 修复工程师输出 `fix_report.md`
  - 修复点 + 算法依据 + 回归结果 + 残留不一致数
- [ ] T7: commit + push 到 origin/main（前缀 `qpyc-rNN:`，≤300s）
- [ ] T8: 反模式自检（`_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀 0 新增；`_merge_block_is_loop_back_edge` 重命名按计划执行）

## 预备任务

- [x] T0: 建立 quotation.pyc 字节码基线
  - 输出 `baseline/original_bytecode.txt`（dis 输出，133 函数）
  - 输出 `baseline/decompiled_baseline.py`（首轮反编译结果，2593 行）
  - 输出 `baseline/decompile_stderr.txt`（19 处 MatchSingleton 警告）
  - 编译 `decompiled_baseline.py` 失败：line 2579 `filter_type=` 缺默认值
- [x] T0-1: 建立反模式起点快照（`baseline/antipattern_snapshot.txt`：_merge_=1, 其他=0）

## 轮 1 (Round 1)

- [x] R1-T1: 反编译 + 字节码 diff → `decompile_report.md`（rounds/round_01/test_engineer/decompile_report.md，12 类缺陷，line 2579 阻塞 + 19 处 MatchSingleton）
- [x] R1-T2: ≥10 最小复现实例 → `minimal_repros/`（12 个 repro，全部通过 py_compile 验证）
- [x] R1-T3: 根因分析（定位到识别/生成方法）（fix_report.md §1 已确认根因：repro_03→code_generator._generate_arguments；repro_01→region_analyzer._mr_finalize_match_region + ast_converter；repro_05→region_ast_generator 链式比较；repro_07→region_ast_generator POP_EXCEPT/多STORE）
- [x] R1-T4: 实施修复（含 docstring 同步）（P0×2 完全/阻塞解除 + P1×2 完全/部分；4 处 docstring 更新）
- [x] R1-T5: 回归测试（无退化 + 复现实例通过）（10 区域 0 退化，12 repro 全部反编译可编译）
- [x] R1-T6: `fix_report.md`（rounds/round_01/repair_engineer/fix_report.md）
- [ ] R1-T7: commit + push `qpyc-r01:`（待用户授权执行；修复工程师无 commit 权限）
- [x] R1-T8: 反模式自检（G3 通过：0 新增反模式前缀方法；_merge_=1 为 pre-existing）

## 轮 2 (Round 2)

- [ ] R2-T1 ~ R2-T8（结构同 Round 1）

## 轮 3 (Round 3)

- [ ] R3-T1 ~ R3-T8

## 轮 4 (Round 4)

- [ ] R4-T1 ~ R4-T8

## 轮 5 (Round 5)

- [ ] R5-T1 ~ R5-T8

## 轮 6 (Round 6)

- [ ] R6-T1 ~ R6-T8

## 轮 7 (Round 7)

- [ ] R7-T1 ~ R7-T8

## 轮 8 (Round 8)

- [ ] R8-T1 ~ R8-T8

## 轮 9 (Round 9)

- [ ] R9-T1 ~ R9-T8

## 轮 10 (Round 10)

- [ ] R10-T1 ~ R10-T8

## 退出条件（每轮后检查）

- [ ] E1: quotation.pyc 反编译字节码不一致数 = 0（提前达成则提前退出，但仍需完成最少 1 轮闭环）
- [ ] E2: 最近一轮测试工程师可提取的「新增最小复现实例」< 10 个（无可修复点）

未达成 E1/E2 时，10 轮全部执行完毕后输出最终残留清单（`final_residual.md`）。

## 最终验证（10 轮完成后）

- [ ] F1: 共 10 次 commit + push 完成（`git log --grep="qpyc-r"` 计数 = 10）
- [ ] F2: quotation.pyc 字节码不一致数 ≤ 起始基线（优选 = 0）
- [ ] F3: 既有测试矩阵无退化（IF/LOOP/TRY/WITH/MATCH/BOOLOP/TERNARY/CC/SEQ/ASSERT 全部持平）
- [ ] F4: 算法 4 原则 FULLY COMPLIANT（自底向上归约 / 唯一块归属 / 嵌套抽象节点 / 入口引用语义）
- [ ] F5: 无反模式残留（`_merge_block_is_loop_back_edge` 已重命名）
- [ ] F6: `python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"` 编译通过
- [ ] F7: 所有涉及到的 `_identify_*_regions` 方法 docstring 已按 6 项统一模板更新

# Task Dependencies

- 每轮 T2 依赖 T1；T3 依赖 T1+T2；T4 依赖 T3；T5 依赖 T4；T6 依赖 T5；T7 依赖 T6；T8 依赖 T4
- Round N+1 的 T1 依赖 Round N 的 T7（push 完成后从最新代码出发）
- T0（预备任务）必须在 Round 1 T1 之前完成
- T0-1 反模式快照为 F5 验证的对比基准
