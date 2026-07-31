# 验证清单

> 目标：按区域类型逐类深度迭代（每区域 20 轮，共 200 轮），通过「测试工程师 + 修复工程师」对抗，将反编译逻辑写入 11 个 `_identify_*_regions`（6 节模板）与 9+ 个 `_generate_*`（4 节模板）方法注释，驱动 site-packages 下全部 pyc 文件反编译字节码 100% 等价，每个 pyc 生成同名 `+OK.py`。
> 当前状态：待执行

## 通用约束（每轮检查）

- [ ] G1 命令执行时间 ≤ 300 秒
- [ ] G2 每轮 commit + push 到 origin/main（commit 前缀 `r20-<REGION>-rNN:`）
- [ ] G3 无反模式新增（`_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀 0 新增）
- [ ] G4 无硬编码深度上限新增（`depth > N` / `count < N` 等魔法数字）
- [ ] G5 该轮 ≥ 10 个最小复现实例全部通过（若该区域已 100% 一致则豁免）
- [ ] G6 既有测试矩阵无退化（10 类区域全量回归）
- [ ] G7 `findings.md` + `fix_report.md` 已生成
- [ ] G8 涉及的 `_identify_*_regions` 方法 docstring 已按 6 节模板更新
- [ ] G9 涉及的 `_generate_*` 方法 docstring 已按 4 节模板更新
- [ ] G10 单轮独立目录 `rounds/<REGION>/round_NN/{test_engineer/, repair_engineer/}` 已创建
- [ ] G11 禁止修改反编译生成的 `+OK.py` 文件
- [ ] G12 禁止任何投机取巧（针对特定 pyc 的硬编码绕过）
- [ ] G13 测试工程师累计 ≥ 10 真实错误即停止（正确不算；非本区域缺陷标注 CTRL 不计入）
- [ ] G14 修复工程师确保相似问题不再出现（完善判据/入口条件，非单实例补丁）
- [ ] G15 禁止在命令/文件/commit message 中嵌入任何 token / 凭据
- [ ] G16 跨区域交叉影响已记录并运行全量回归

## 预备阶段（Phase 0）

- [ ] P0.1 `pyc_index.json` 可用（复用既有产物）
- [ ] P0.2 `scripts/pyc_batch_verify.py` 可用
- [ ] P0.3 `baseline/region_baseline.txt` 已记录 10 类区域当前基线通过率
- [ ] P0.4 git push 凭据已配置（`gh auth status` 或 credential helper），无嵌入 token

## 阶段一（Phase 1：TERNARY，20 轮）

### 通用轮次检查清单（每轮 NN 复制一份）

- [ ] T-TERNARY-NN-0 该轮目录 `rounds/TERNARY/round_NN/` 已创建
- [ ] T-TERNARY-NN-1 测试工程师 `findings.md` 已生成（含问题点清单 + 测试实例路径 + 错误清单 + 成功率）
- [ ] T-TERNARY-NN-2 ≥ 10 个最小复现实例已归档至 `minimal_repros/`（全部 py_compile + DEFECT-REPRO 验证；若该区域已 100% 一致则豁免）
- [ ] T-TERNARY-NN-3 测试工程师累计 ≥ 10 真实错误即停止（正确不算；非 TERNARY 缺陷标注 CTRL）
- [ ] T-TERNARY-NN-4 修复工程师 `fix_report.md` 已生成（修复点 + 算法依据 + 注释更新清单 + 回归结果 + 残留不一致数）
- [ ] T-TERNARY-NN-5 涉及的 `_identify_ternary_regions` 方法 docstring 已按 6 节模板更新
- [ ] T-TERNARY-NN-6 涉及的 `_generate_ternary_*` 方法 docstring 已按 4 节模板更新
- [ ] T-TERNARY-NN-7 既有测试矩阵无退化（10 类区域全量回归）
- [ ] T-TERNARY-NN-8 ≥ 10 测试实例全部通过
- [ ] T-TERNARY-NN-9 反模式自检通过（G3）
- [ ] T-TERNARY-NN-10 算法 4 原则 FULLY COMPLIANT（自底向上归约 / 每块唯一归属 / 嵌套抽象节点 / 入口引用语义）
- [ ] T-TERNARY-NN-11 `python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"` 编译通过
- [ ] T-TERNARY-NN-12 修复工程师确保相似问题不再出现（完善判据/入口条件）
- [ ] T-TERNARY-NN-13 commit + push `r20-TERNARY-rNN:`

### 已执行轮次（按实际进度填充）

- [ ] T-TERNARY-01 通用清单全部通过
- [ ] T-TERNARY-02 通用清单全部通过
- [ ] T-TERNARY-03 通用清单全部通过
- [ ] T-TERNARY-04 通用清单全部通过
- [ ] T-TERNARY-05 通用清单全部通过
- [ ] T-TERNARY-06 通用清单全部通过
- [ ] T-TERNARY-07 通用清单全部通过
- [ ] T-TERNARY-08 通用清单全部通过
- [ ] T-TERNARY-09 通用清单全部通过
- [ ] T-TERNARY-10 通用清单全部通过
- [ ] T-TERNARY-11 通用清单全部通过
- [ ] T-TERNARY-12 通用清单全部通过
- [ ] T-TERNARY-13 通用清单全部通过
- [ ] T-TERNARY-14 通用清单全部通过
- [ ] T-TERNARY-15 通用清单全部通过
- [ ] T-TERNARY-16 通用清单全部通过
- [ ] T-TERNARY-17 通用清单全部通过
- [ ] T-TERNARY-18 通用清单全部通过
- [ ] T-TERNARY-19 通用清单全部通过
- [ ] T-TERNARY-20 通用清单全部通过

## 阶段二（Phase 2：TRY，20 轮）

### 通用轮次检查清单（每轮 NN）

- [ ] T-TRY-NN-0 该轮目录 `rounds/TRY/round_NN/` 已创建
- [ ] T-TRY-NN-1 测试工程师 `findings.md` 已生成
- [ ] T-TRY-NN-2 ≥ 10 个最小复现实例已归档
- [ ] T-TRY-NN-3 测试工程师累计 ≥ 10 真实错误即停止
- [ ] T-TRY-NN-4 修复工程师 `fix_report.md` 已生成
- [ ] T-TRY-NN-5 涉及的 `_identify_try_except_regions` 方法 docstring 已按 6 节模板更新
- [ ] T-TRY-NN-6 涉及的 `_generate_try*` 方法 docstring 已按 4 节模板更新
- [ ] T-TRY-NN-7 既有测试矩阵无退化
- [ ] T-TRY-NN-8 ≥ 10 测试实例全部通过
- [ ] T-TRY-NN-9 反模式自检通过
- [ ] T-TRY-NN-10 算法 4 原则 FULLY COMPLIANT
- [ ] T-TRY-NN-11 编译通过
- [ ] T-TRY-NN-12 修复工程师确保相似问题不再出现
- [ ] T-TRY-NN-13 commit + push `r20-TRY-rNN:`

### 已执行轮次

- [ ] T-TRY-01..T-TRY-20 通用清单全部通过（20 轮）

## 阶段三（Phase 3：BOOLOP，20 轮）

- [ ] T-BOOLOP-01..T-BOOLOP-20 通用清单全部通过（目录 `rounds/BOOLOP/round_NN/`，commit 前缀 `r20-BOOLOP-rNN:`）
  - 每轮：findings.md / ≥10 minimal_repros / fix_report.md / `_identify_boolop_regions` 6 节 / `_generate_boolop*` 4 节 / 回归无退化 / 10 实例通过 / 4 原则合规 / 编译通过 / 相似问题不再出现 / commit+push

## 阶段四（Phase 4：CHAINED_COMPARE，20 轮）

- [ ] T-CC-01..T-CC-20 通用清单全部通过（目录 `rounds/CHAINED_COMPARE/round_NN/`，commit 前缀 `r20-CHAINED_COMPARE-rNN:`）
  - 每轮：`_identify_chained_compare_regions` 6 节 / `_generate_chained_compare*` 4 节

## 阶段五（Phase 5：IF，20 轮）

- [ ] T-IF-01..T-IF-20 通用清单全部通过（目录 `rounds/IF/round_NN/`，commit 前缀 `r20-IF-rNN:`）
  - 每轮：`_identify_conditional_regions` 6 节 / `_generate_if` / `_process_if_blocks` 4 节

## 阶段六（Phase 6：LOOP，20 轮）

- [ ] T-LOOP-01..T-LOOP-20 通用清单全部通过（目录 `rounds/LOOP/round_NN/`，commit 前缀 `r20-LOOP-rNN:`）
  - 每轮：`_identify_loop_regions` 6 节 / `_generate_loop*` 4 节

## 阶段七（Phase 7：WITH，20 轮）

- [ ] T-WITH-01..T-WITH-20 通用清单全部通过（目录 `rounds/WITH/round_NN/`，commit 前缀 `r20-WITH-rNN:`）
  - 每轮：`_identify_with_regions` 6 节 / `_generate_with*` 4 节

## 阶段八（Phase 8：MATCH，20 轮）

- [ ] T-MATCH-01..T-MATCH-20 通用清单全部通过（目录 `rounds/MATCH/round_NN/`，commit 前缀 `r20-MATCH-rNN:`）
  - 每轮：`_identify_match_regions` + `_identify_nested_match_regions` 6 节 / `_generate_match*` 4 节

## 阶段九（Phase 9：ASSERT，20 轮）

- [ ] T-ASSERT-01..T-ASSERT-20 通用清单全部通过（目录 `rounds/ASSERT/round_NN/`，commit 前缀 `r20-ASSERT-rNN:`）
  - 每轮：`_identify_assert_regions` 6 节 / `_generate_assert*` 4 节

## 阶段十（Phase 10：SEQUENCE，20 轮）

- [ ] T-SEQ-01..T-SEQ-20 通用清单全部通过（目录 `rounds/SEQUENCE/round_NN/`，commit 前缀 `r20-SEQUENCE-rNN:`）
  - 每轮：`_identify_sequence_regions` 6 节 / `_generate_block_statements*` 4 节

## 阶段十一（Phase 11：全量验证）

- [ ] P11.1 批量反编译全部 pyc 文件完成
- [ ] P11.2 每个反编译成功的 pyc 在同目录生成 `<name>OK.py`
- [ ] P11.3 所有 `+OK.py` 的 `py_compile` 通过
- [ ] P11.4 所有 `+OK.py` 重编译字节码与原 pyc 100% 一致
- [ ] P11.5 `pyc_index.json` 所有条目 `decompile_status = ok`，`ok_py_generated = true`
- [ ] P11.6 未修改任何 `+OK.py` 文件
- [ ] P11.7 10 类区域全量回归无退化

## 退出条件（每区域后检查）

- [ ] E1 该区域 20 轮全部完成
- [ ] E2 该区域相关 pyc/函数字节码一致率 ≥ 99%（或残留缺陷已记录为 final_residual）
- [ ] E3 该区域 `_identify_*_regions` / `_generate_*` 方法注释模板合规

## 退出条件（全部）

- [ ] EF1 10 个区域各 20 轮全部完成（200 轮）
- [ ] EF2 所有 pyc 文件字节码不一致函数数趋近 0
- [ ] EF3 算法 4 原则 FULLY COMPLIANT
- [ ] EF4 无反模式残留（`_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀 0 新增）
- [ ] EF5 11 个 `_identify_*_regions` 方法 docstring 全部 6 节模板合规
- [ ] EF6 9+ 个 `_generate_*` 方法 docstring 全部 4 节模板合规
- [ ] EF7 `python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"` 编译通过
- [ ] EF8 所有 pyc 文件 `+OK.py` 已生成
- [ ] EF9 所有 `+OK.py` 字节码与原 pyc 100% 一致
- [ ] EF10 所有 200 轮 commit + push 完成（`git log --grep="r20-"` 计数 ≥ 200）

## 安全约束（每轮检查）

- [ ] S1 禁止在命令/文件/commit message 中嵌入任何 GitHub token / 凭据
- [ ] S2 git push 使用本机已配置凭据（credential helper / `gh auth login`）
- [ ] S3 若对话中暴露 token，已提示用户撤销，未使用该 token

## 备注

- 每区域 20 轮，共 200 轮，轮次数固定
- 每轮目录必须独立，禁止跨轮合并产物；每轮 `minimal_repros/` 中的实例必须可独立运行
- 禁止修改反编译生成的 `+OK.py` 文件；如需修复，必须修复反编译器本身
- 测试应尽快使成功率增加：优先修复影响面广的缺陷（同一缺陷在多个 pyc / 多个函数中出现）
- 跨区域交叉影响：若修复本区域时发现影响其他区域，一并解决并记录，运行全部 10 类区域测试矩阵
- 每轮 push 强制：若 push 失败（网络/DNS），记录 push-pending 并下一轮重试，但 commit 不得跳过
