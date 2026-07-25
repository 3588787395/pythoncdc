# 验证清单

> 目标：对 `/workspace/quotation.pyc` 执行 10 轮双工程师迭代，直至反编译字节码 100% 等价。
> 每轮：测试工程师反编译 + 提取 10+ 最小复现实例 → 修复工程师按区域归约算法修复 → 回归 → commit + push。
> 当前状态：待执行

## 通用约束（每轮检查）

- [ ] G1 命令执行时间 ≤ 300 秒
- [ ] G2 每轮 commit + push 到 origin/main（commit 前缀 `qpyc-rNN:`）
- [ ] G3 无反模式新增（`_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀 0 新增）
- [ ] G4 无硬编码深度上限新增
- [ ] G5 该轮 10+ 最小复现实例全部通过
- [ ] G6 既有测试矩阵无退化（IF/LOOP/TRY/WITH/MATCH/BOOLOP/TERNARY/CC/SEQ/ASSERT 子集）
- [ ] G7 `decompile_report.md` + `fix_report.md` 已生成
- [ ] G8 涉及的 `_identify_*_regions` 方法 docstring 已按 6 项统一模板更新
- [ ] G9 单轮独立目录 `rounds/round_NN/{test_engineer/, repair_engineer/}` 已创建

## 预备阶段

- [x] P0 `baseline/original_bytecode.txt` 已生成（133 函数 dis 输出）
- [x] P1 `baseline/decompiled_baseline.py` 已生成（2593 行，19 处 MatchSingleton 警告）
- [x] P2 编译验证：line 2579 `filter_type=` 缺默认值（首轮语法错误）
- [x] P3 反模式起点快照已记录（`baseline/antipattern_snapshot.txt`：_merge_=1, 其他=0）

## 轮 1 (Round 1)

- [x] R1-1 反编译 + 字节码 diff（`decompile_report.md`，12 类缺陷，line 2579 + 19 处 MatchSingleton）
- [x] R1-2 ≥10 最小复现实例（`minimal_repros/`，12 个 repro 全部 py_compile 通过）
- [x] R1-3 根因分析（定位到识别/生成方法）（fix_report.md §1 已确认 4 项根因）
- [x] R1-4 修复实施（含 docstring 同步）（P0×2 + P1×2；4 处 docstring 更新）
- [x] R1-5 回归测试通过（10 区域 0 退化；12 repro 全部可编译）
- [x] R1-6 `fix_report.md` 生成（rounds/round_01/repair_engineer/fix_report.md）
- [ ] R1-7 commit + push `qpyc-r01:`（待用户授权执行）
- [x] R1-8 反模式自检通过（G3：0 新增；F6：import OK）
- [x] R1-9 残留不一致数 ≤ 基线（MatchSingleton 19→0；语法错误 1→0；残留缺陷类 12→8）

## 轮 2 (Round 2)

- [ ] R2-1 ~ R2-9（结构同 Round 1）

## 轮 3 (Round 3)

- [ ] R3-1 ~ R3-9

## 轮 4 (Round 4)

- [ ] R4-1 ~ R4-9

## 轮 5 (Round 5)

- [ ] R5-1 ~ R5-9

## 轮 6 (Round 6)

- [ ] R6-1 ~ R6-9

## 轮 7 (Round 7)

- [ ] R7-1 ~ R7-9

## 轮 8 (Round 8)

- [ ] R8-1 ~ R8-9

## 轮 9 (Round 9)

- [ ] R9-1 ~ R9-9

## 轮 10 (Round 10)

- [ ] R10-1 ~ R10-9

## 退出条件（每轮后检查）

- [ ] E1 quotation.pyc 反编译字节码不一致数 = 0
- [ ] E2 最近一轮测试工程师可提取新增最小复现实例 < 10 个

## 最终验证（10 轮完成后）

- [ ] F1 共 10 次 commit + push 完成（`git log --grep="qpyc-r"` 计数 ≥ 10）
- [ ] F2 quotation.pyc 字节码不一致数 ≤ 起始基线（优选 = 0）
- [ ] F3 既有测试矩阵无退化
- [ ] F4 算法 4 原则 FULLY COMPLIANT
- [ ] F5 无反模式残留（`_merge_block_is_loop_back_edge` 已重命名为 `is_merge_block_loop_back_edge`）
- [ ] F6 `python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"` 编译通过
- [ ] F7 所有涉及到的 `_identify_*_regions` 方法 docstring 已按 6 项统一模板更新

## 备注

- 若在 10 轮内提前达到 E1+E2，可在用户确认后提前退出，剩余轮次可省略
- 若 10 轮后仍未达到 E1，输出 `final_residual.md` 列出残留不一致清单，作为后续迭代输入
- 每轮目录必须独立，禁止跨轮合并产物；每轮 `minimal_repros/` 中的实例必须可独立运行（`python -c "import dis; ..."` 验证）
