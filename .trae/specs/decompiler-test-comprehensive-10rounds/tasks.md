# Tasks

## 预备阶段（Phase 0：基线建立）

- [x] T0.1 反编译 `decompiler_test_comprehensive.cpython-311.pyc` 并记录基线
  - [x] T0.1.1 执行 `python pycdc.py decompiler_test_comprehensive.cpython-311.pyc -o decompiler_test_comprehensive_decompiled.py`
  - [x] T0.1.2 执行字节码 diff（原 pyc ↔ 重编译 decompiled.py），记录基线成功率
  - [x] T0.1.3 记录不一致函数清单到 `baseline/baseline_report.md`
- [ ] T0.2 执行既有区域测试矩阵，记录基线通过率
  - [ ] T0.2.1 执行 `python tests/exhaustive/run_test_matrix.py`
  - [ ] T0.2.2 记录基线通过率到 `baseline/region_test_baseline.txt`

## 阶段一（Phase 1：10 轮双工程师迭代）

> 每轮反编译 `decompiler_test_comprehensive.cpython-311.pyc`，验证字节码一致性。
> 每轮独立目录 `rounds/round_NN/`，commit 前缀 `dtc-rNN:`。
> 每轮必须 commit + push 到远程。

### 通用轮次模板（每轮执行）

- [ ] T1.NN.1 测试工程师：反编译 decompiler_test_comprehensive.cpython-311.pyc + 字节码 diff → `rounds/round_NN/test_engineer/decompile_report.md`
  - [ ] T1.NN.1a 记录不一致函数清单 + 当前成功率 + 与上一轮对比
  - [ ] T1.NN.1b 构造 ≥ 10 个最小复现实例 → `rounds/round_NN/test_engineer/minimal_repros/`（若已 100% 一致则豁免）
- [ ] T1.NN.2 修复工程师：按区域归约算法修复 → `rounds/round_NN/repair_engineer/fix_report.md`
  - [ ] T1.NN.2a 定位不一致到 `_identify_*_regions` / `_generate_*` 方法
  - [ ] T1.NN.2b 完善逻辑（禁止补丁 / 禁止硬编码 / 禁止跨区域启发式）
  - [ ] T1.NN.2c 同步更新方法 docstring（6 节 / 4 节模板）
  - [ ] T1.NN.2d 运行回归测试（既有矩阵不退化，≤ 280s）
  - [ ] T1.NN.2e 验证 10+ 复现实例全部通过
- [ ] T1.NN.3 commit + push `dtc-rNN:`（≤ 300s）

### 10 轮任务

- [ ] T1.01 第 01 轮
- [ ] T1.02 第 02 轮
- [ ] T1.03 第 03 轮
- [ ] T1.04 第 04 轮
- [ ] T1.05 第 05 轮
- [ ] T1.06 第 06 轮
- [ ] T1.07 第 07 轮
- [ ] T1.08 第 08 轮
- [ ] T1.09 第 09 轮
- [ ] T1.10 第 10 轮

## 阶段二（Phase 2：最终验证）

- [ ] T2.1 `decompiler_test_comprehensive.cpython-311.pyc` 字节码不一致函数数 = 0（100% 成功率）
- [ ] T2.2 既有测试矩阵无退化
- [ ] T2.3 算法 4 原则 FULLY COMPLIANT
- [ ] T2.4 无反模式残留（`_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀 0 新增）
- [ ] T2.5 11 个 `_identify_*_regions` 方法 docstring 全部 6 节模板合规
- [ ] T2.6 9+ 个 `_generate_*` 方法 docstring 全部 4 节模板合规
- [ ] T2.7 `python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"` 编译通过
- [ ] T2.8 所有 10 轮 commit + push 完成（`git log --grep="dtc-r"` 计数 ≥ 10）

# Task Dependencies

- T0.* 必须先于 T1.* 完成（基线是迭代前提）
- T1.NN+1 依赖 T1.NN 完成（成功率单调递增，禁止跳轮）
- T2.* 依赖 T1.* 全部完成
- 每轮内：测试工程师 → 修复工程师 → commit+push（严格顺序）
