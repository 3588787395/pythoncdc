# Tasks

> 迭代策略：按区域类型逐类迭代，每区域 20 轮，共 200 轮。
> 区域顺序：TERNARY → TRY → BOOLOP → CHAINED_COMPARE → IF → LOOP → WITH → MATCH → ASSERT → SEQUENCE
> 每轮：测试工程师（找 ≥ 10 错误即停）→ 修复工程师（按区域归约算法修复 + 更新注释 + 回归）→ commit + push `r20-<REGION>-rNN:`
> 每区域每轮独立目录：`rounds/<REGION>/round_NN/{test_engineer/, repair_engineer/}`

## 预备阶段（Phase 0：基线确认）

- [ ] T0.1 确认 `pyc_index.json` 可用（复用 region-comment-multi-pyc-iteration 产物）
- [ ] T0.2 确认 `scripts/pyc_batch_verify.py` 可用
- [ ] T0.3 记录 10 类区域当前基线通过率到 `baseline/region_baseline.txt`（参考既有 region_test_baseline.txt 94.88%）
- [ ] T0.4 确认 git push 凭据已配置（`gh auth status` 或 credential helper），禁止使用任何嵌入 token

## 阶段一（Phase 1：TERNARY 区域，20 轮）

> 目标方法：`_identify_ternary_regions`（6 节注释）+ `_generate_ternary_assign` 等（4 节注释）
> 残留缺陷参考：R09 repro_12 Pattern G3、R12 ternary assign+return 合并

### 通用轮次模板（每轮执行）

- [ ] T1.NN.1 测试工程师：阅读 TERNARY 区域识别/生成方法 → 找问题点 → 构造测试实例 → `rounds/TERNARY/round_NN/test_engineer/findings.md`
  - [ ] T1.NN.1a 从 pyc_index.json 选取触发 TERNARY 的 pyc/函数
  - [ ] T1.NN.1b 构造 ≥ 10 个最小复现实例 → `minimal_repros/`
  - [ ] T1.NN.1c 累计 ≥ 10 真实错误即停止（正确不算；非 TERNARY 缺陷标注 CTRL）
- [ ] T1.NN.2 修复工程师：按区域归约算法修复 → `rounds/TERNARY/round_NN/repair_engineer/fix_report.md`
  - [ ] T1.NN.2a 定位错误到 `_identify_ternary_regions` / `_generate_ternary_*` 方法
  - [ ] T1.NN.2b 完善逻辑（禁止补丁 / 禁止硬编码 / 禁止跨区域启发式）
  - [ ] T1.NN.2c 同步更新方法 docstring（6 节 / 4 节模板）
  - [ ] T1.NN.2d 运行回归测试（既有矩阵不退化，≤ 280s）
  - [ ] T1.NN.2e 验证 ≥ 10 测试实例全部通过
  - [ ] T1.NN.2f 确保相似问题不再出现（完善判据/入口条件）
- [ ] T1.NN.3 commit + push `r20-TERNARY-rNN:`（≤ 300s）

### 首批轮次

- [ ] T1.01 TERNARY round_01
- [ ] T1.02 TERNARY round_02
- [ ] T1.03 TERNARY round_03
- [ ] T1.04 TERNARY round_04
- [ ] T1.05 TERNARY round_05
- [ ] T1.06 TERNARY round_06
- [ ] T1.07 TERNARY round_07
- [ ] T1.08 TERNARY round_08
- [ ] T1.09 TERNARY round_09
- [ ] T1.10 TERNARY round_10
- [ ] T1.11 TERNARY round_11
- [ ] T1.12 TERNARY round_12
- [ ] T1.13 TERNARY round_13
- [ ] T1.14 TERNARY round_14
- [ ] T1.15 TERNARY round_15
- [ ] T1.16 TERNARY round_16
- [ ] T1.17 TERNARY round_17
- [ ] T1.18 TERNARY round_18
- [ ] T1.19 TERNARY round_19
- [ ] T1.20 TERNARY round_20

## 阶段二（Phase 2：TRY 区域，20 轮）

> 目标方法：`_identify_try_except_regions`（6 节注释）+ `_generate_try` 等（4 节注释）
> 残留缺陷参考：Pattern T2（except body drop）/ Pattern T3（post-try 消费 handler_entry）

### 通用轮次模板（每轮执行）

- [ ] T2.NN.1 测试工程师：阅读 TRY 区域识别/生成方法 → 找问题点 → 构造测试实例 → `rounds/TRY/round_NN/test_engineer/findings.md`
  - [ ] T2.NN.1a 从 pyc_index.json 选取触发 TRY 的 pyc/函数
  - [ ] T2.NN.1b 构造 ≥ 10 个最小复现实例 → `minimal_repros/`
  - [ ] T2.NN.1c 累计 ≥ 10 真实错误即停止
- [ ] T2.NN.2 修复工程师：按区域归约算法修复 → `rounds/TRY/round_NN/repair_engineer/fix_report.md`
  - [ ] T2.NN.2a 定位错误到 `_identify_try_except_regions` / `_generate_try*` 方法
  - [ ] T2.NN.2b 完善逻辑（禁止补丁）
  - [ ] T2.NN.2c 同步更新方法 docstring（6 节 / 4 节模板）
  - [ ] T2.NN.2d 运行回归测试（≤ 280s，无退化）
  - [ ] T2.NN.2e 验证 ≥ 10 测试实例全部通过
  - [ ] T2.NN.2f 确保相似问题不再出现
- [ ] T2.NN.3 commit + push `r20-TRY-rNN:`（≤ 300s）

### 首批轮次

- [ ] T2.01 TRY round_01
- [ ] T2.02 TRY round_02
- [ ] T2.03 TRY round_03
- [ ] T2.04 TRY round_04
- [ ] T2.05 TRY round_05
- [ ] T2.06 TRY round_06
- [ ] T2.07 TRY round_07
- [ ] T2.08 TRY round_08
- [ ] T2.09 TRY round_09
- [ ] T2.10 TRY round_10
- [ ] T2.11 TRY round_11
- [ ] T2.12 TRY round_12
- [ ] T2.13 TRY round_13
- [ ] T2.14 TRY round_14
- [ ] T2.15 TRY round_15
- [ ] T2.16 TRY round_16
- [ ] T2.17 TRY round_17
- [ ] T2.18 TRY round_18
- [ ] T2.19 TRY round_19
- [ ] T2.20 TRY round_20

## 阶段三（Phase 3：BOOLOP 区域，20 轮）

> 目标方法：`_identify_boolop_regions`（6 节注释）+ `_generate_boolop` 等（4 节注释）
> 残留缺陷参考：Pattern B/E

- [ ] T3.01..T3.20 BOOLOP round_01..round_20（同 T1/T2 模板，目录 `rounds/BOOLOP/round_NN/`，commit 前缀 `r20-BOOLOP-rNN:`）

## 阶段四（Phase 4：CHAINED_COMPARE 区域，20 轮）

> 目标方法：`_identify_chained_compare_regions`（6 节注释）+ `_generate_chained_compare` 等（4 节注释）
> 残留缺陷参考：Pattern G3（链式比较跨块误判）

- [ ] T4.01..T4.20 CHAINED_COMPARE round_01..round_20（目录 `rounds/CHAINED_COMPARE/round_NN/`，commit 前缀 `r20-CHAINED_COMPARE-rNN:`）

## 阶段五（Phase 5：IF 区域，20 轮）

> 目标方法：`_identify_conditional_regions`（6 节注释）+ `_generate_if` / `_process_if_blocks` 等（4 节注释）
> 残留缺陷参考：Pattern A2/C/C2/D2

- [ ] T5.01..T5.20 IF round_01..round_20（目录 `rounds/IF/round_NN/`，commit 前缀 `r20-IF-rNN:`）

## 阶段六（Phase 6：LOOP 区域，20 轮）

> 目标方法：`_identify_loop_regions`（6 节注释）+ `_generate_loop` 等（4 节注释）
> 残留缺陷参考：Pattern R（模块级 NOP padding / LOAD_CONST 顺序）

- [ ] T6.01..T6.20 LOOP round_01..round_20（目录 `rounds/LOOP/round_NN/`，commit 前缀 `r20-LOOP-rNN:`）

## 阶段七（Phase 7：WITH 区域，20 轮）

> 目标方法：`_identify_with_regions`（6 节注释）+ `_generate_with` 等（4 节注释）
> 残留缺陷参考：Pattern F

- [ ] T7.01..T7.20 WITH round_01..round_20（目录 `rounds/WITH/round_NN/`，commit 前缀 `r20-WITH-rNN:`）

## 阶段八（Phase 8：MATCH 区域，20 轮）

> 目标方法：`_identify_match_regions` + `_identify_nested_match_regions`（6 节注释）+ `_generate_match` 等（4 节注释）

- [ ] T8.01..T8.20 MATCH round_01..round_20（目录 `rounds/MATCH/round_NN/`，commit 前缀 `r20-MATCH-rNN:`）

## 阶段九（Phase 9：ASSERT 区域，20 轮）

> 目标方法：`_identify_assert_regions`（6 节注释）+ `_generate_assert` 等（4 节注释）

- [ ] T9.01..T9.20 ASSERT round_01..round_20（目录 `rounds/ASSERT/round_NN/`，commit 前缀 `r20-ASSERT-rNN:`）

## 阶段十（Phase 10：SEQUENCE 区域，20 轮）

> 目标方法：`_identify_sequence_regions`（6 节注释）+ `_generate_block_statements` 等（4 节注释）

- [ ] T10.01..T10.20 SEQUENCE round_01..round_20（目录 `rounds/SEQUENCE/round_NN/`，commit 前缀 `r20-SEQUENCE-rNN:`）

## 阶段十一（Phase 11：全量验证）

- [ ] T11.1 执行 `scripts/pyc_batch_verify.py` 对全部 pyc 文件批量反编译
- [ ] T11.2 验证所有 `+OK.py` 的 `py_compile` 通过
- [ ] T11.3 验证所有 `+OK.py` 重编译字节码与原 pyc 100% 一致
- [ ] T11.4 更新 `pyc_index.json`：所有条目 `decompile_status = ok`
- [ ] T11.5 既有测试矩阵无退化（10 类区域全量回归）

## 阶段十二（Phase 12：最终验证）

- [ ] T12.1 所有 200 轮 commit + push 完成（`git log --grep="r20-"` 计数 ≥ 200）
- [ ] T12.2 所有 pyc 文件字节码不一致函数数 = 0（或残留已记录 final_residual）
- [ ] T12.3 算法 4 原则 FULLY COMPLIANT
- [ ] T12.4 无反模式残留（`_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀 0 新增）
- [ ] T12.5 11 个 `_identify_*_regions` 方法 docstring 全部 6 节模板合规
- [ ] T12.6 9+ 个 `_generate_*` 方法 docstring 全部 4 节模板合规
- [ ] T12.7 `python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"` 编译通过
- [ ] T12.8 所有 pyc 文件 `+OK.py` 已生成且字节码 100% 一致

# Task Dependencies

- T0.* 必须先于所有 Phase 完成（基线与凭据确认）
- 每个 Phase 内：round_NN+1 依赖 round_NN（成功率单调递增，禁止跳轮）
- Phase 之间按顺序：TERNARY → TRY → BOOLOP → CHAINED_COMPARE → IF → LOOP → WITH → MATCH → ASSERT → SEQUENCE
- T11.* 依赖所有 Phase 1..10 完成（200 轮）
- T12.* 依赖 T11.* 完成
- 每轮内：测试工程师 → 修复工程师 → commit+push（严格顺序）
- 跨区域交叉影响：若修复本区域时发现影响其他区域，一并解决并记录，运行全部 10 类区域测试矩阵
