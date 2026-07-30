# Tasks

## 预备阶段（Phase 0：基础设施）

- [x] T0.1 创建 pyc 索引构建脚本 `scripts/pyc_index_builder.py`
  - [x] T0.1.1 扫描 `f:\Downloads\pythoncdc-main\site-packages\**\*.pyc`
  - [x] T0.1.2 提取每个 pyc 的 path / size / function_count
  - [x] T0.1.3 输出 `pyc_index.json`（含 decompile_status=`pending` / bytecode_match_rate=0.0 / ok_py_generated=false / last_tested_round=0 初始状态）
- [x] T0.2 创建批量验证脚本 `scripts/pyc_batch_verify.py`
  - [x] T0.2.1 反编译单个 pyc → 生成 `<name>OK.py`
  - [x] T0.2.2 字节码 diff（原 pyc ↔ 重编译 OK.py）
  - [x] T0.2.3 批量模式：从 pyc_index.json 读取，逐个验证并回写状态
  - [x] T0.2.4 累计成功率统计函数
- [x] T0.3 执行 pyc 索引构建，确认 130+ pyc 文件全部入索引（实际 402 个）
- [x] T0.4 建立首个 pyc 基线：反编译 pyc_index.json 中第一个 pyc + 字节码 diff，记录起始成功率到 `baseline/success_rate.txt`（基线 0.0）

## 阶段一（Phase 1：注释模板对齐）

- [x] T1.1 审计 11 个 `_identify_*_regions` 方法的现有 docstring
  - [x] T1.1.1 列出每个方法的注释缺失节（6 节模板对照）
  - [x] T1.1.2 输出 `phase1/comment_audit.md`（11/11 合规）
- [x] T1.2 审计 9+ 个 `_generate_*` 方法的现有 docstring
  - [x] T1.2.1 列出每个方法的注释缺失节（4 节模板对照）
  - [x] T1.2.2 输出 `phase1/generate_audit.md`（9 核心合规 + 5 待补 docstring）
- [x] T1.3 执行既有区域测试矩阵（IF/LOOP/TRY/WITH/MATCH/ASSERT/BOOLOP/TERNARY/CC/SEQ），记录基线通过率到 `phase1/region_test_baseline.txt`（94.88%，TERNARY/TRY 最弱）

## 阶段二（Phase 2：持续双工程师迭代）

> 每轮从 pyc_index.json 取下一个 `decompile_status != ok` 的 pyc 文件（按 path 字母序轮询）。
> 持续迭代直到所有 pyc 文件所有函数 100% 字节码一致。
> 每轮独立目录 `rounds/round_NN/`，commit 前缀 `rcm-rNN:`。

### 通用轮次模板（每轮执行）

- [ ] T2.NN.1 测试工程师：取下一个 pyc，反编译 + 字节码 diff → `rounds/round_NN/test_engineer/decompile_report.md`
  - [ ] T2.NN.1a 记录不一致函数清单 + 当前 pyc 成功率 + 累计成功率
  - [ ] T2.NN.1b 构造 ≥ 10 个最小复现实例 → `rounds/round_NN/test_engineer/minimal_repros/`（若该 pyc 已 100% 一致则豁免）
  - [ ] T2.NN.1c 若该 pyc 100% 一致：生成 `<name>OK.py`，更新 pyc_index.json
- [ ] T2.NN.2 修复工程师：按区域归约算法修复 → `rounds/round_NN/repair_engineer/fix_report.md`
  - [ ] T2.NN.2a 定位不一致到 `_identify_*_regions` / `_generate_*` 方法
  - [ ] T2.NN.2b 完善逻辑（禁止补丁 / 禁止硬编码 / 禁止跨区域启发式）
  - [ ] T2.NN.2c 同步更新方法 docstring（6 节 / 4 节模板）
  - [ ] T2.NN.2d 运行回归测试（既有矩阵不退化，≤ 280s）
  - [ ] T2.NN.2e 验证 10+ 复现实例全部通过
  - [ ] T2.NN.2f 若该 pyc 修复后 100% 一致：生成 `<name>OK.py`，更新 pyc_index.json
- [ ] T2.NN.3 commit + push `rcm-rNN:`（≤ 300s）

### 首批轮次（按 pyc 字母序）

- [x] T2.01 第 01 轮（取 pyc_index.json 第 1 个 pyc: IQCommon/__init__.pyc）
  - [x] T2.01.1 测试工程师：取下一个 pyc，反编译 + 字节码 diff → `rounds/round_01/test_engineer/decompile_report.md`（0% → 50%，try 体坍缩缺陷，12 复现实例）
  - [x] T2.01.2 修复工程师：按区域归约算法修复 → `rounds/round_01/repair_engineer/fix_report.md`（3 处修复，TRY 90.43%→96.96%，10/12 复现通过，get_python_version 100%）
  - [x] T2.01.3 commit + push `rcm-r01:` (1cf0fde + 8d01fe3)
  - 残留：repro_10 except return 值丢失 / repro_12 elif BoolOp 拆分（独立缺陷，后续轮次修复）
- [ ] T2.02 第 02 轮（取第 2 个 pyc: IQCommon/api/__init__.pyc）
- [ ] T2.03 第 03 轮（取第 3 个 pyc）
- [ ] T2.04 第 04 轮
- [ ] T2.05 第 05 轮
- [ ] T2.06 第 06 轮
- [ ] T2.07 第 07 轮
- [ ] T2.08 第 08 轮
- [ ] T2.09 第 09 轮
- [ ] T2.10 第 10 轮
- [ ] T2.11 第 11 轮（持续，直到所有 pyc `decompile_status = ok`）
- [ ] T2.NN ... 持续直到退出条件满足

> 注：轮次数不设上限，持续直到所有 pyc 文件所有函数 100% 字节码一致。

## 阶段三（Phase 3：全量验证与 +OK 生成）

- [ ] T3.1 执行 `scripts/pyc_batch_verify.py` 对全部 pyc 文件批量反编译
- [ ] T3.2 每个反编译成功的 pyc 在同目录生成 `<name>OK.py`
- [ ] T3.3 验证所有 `+OK.py` 的 `py_compile` 通过
- [ ] T3.4 验证所有 `+OK.py` 重编译字节码与原 pyc 100% 一致
- [ ] T3.5 更新 `pyc_index.json`：所有条目 `decompile_status = ok`，`ok_py_generated = true`
- [ ] T3.6 禁止修改任何 `+OK.py` 文件（如失败，回到 Phase 2 继续修复）

## 阶段四（Phase 4：最终验证）

- [ ] T4.1 所有 pyc 文件字节码不一致函数数 = 0
- [ ] T4.2 所有轮次 commit + push 完成（`git log --grep="rcm-r"` 计数 ≥ 已执行轮数）
- [ ] T4.3 既有测试矩阵无退化
- [ ] T4.4 算法 4 原则 FULLY COMPLIANT
- [ ] T4.5 无反模式残留（`_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀 0 新增）
- [ ] T4.6 11 个 `_identify_*_regions` 方法 docstring 全部 6 节模板合规
- [ ] T4.7 9+ 个 `_generate_*` 方法 docstring 全部 4 节模板合规
- [ ] T4.8 所有 pyc 文件 `+OK.py` 已生成且字节码 100% 一致
- [ ] T4.9 `python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"` 编译通过

# Task Dependencies

- T0.* 必须先于 T2.* 完成（索引与基线是迭代前提）
- T1.* 必须先于 T2.* 完成（注释审计是修复时同步更新的依据）
- T2.NN+1 依赖 T2.NN 完成（成功率单调递增，禁止跳轮）
- T3.* 依赖 Phase 2 退出条件满足（所有 pyc 100% 一致）
- T4.* 依赖 T3.* 完成
- 每轮内：测试工程师 → 修复工程师 → commit+push（严格顺序）
