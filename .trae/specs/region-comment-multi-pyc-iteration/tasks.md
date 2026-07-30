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
- [x] R01 残留澄清：tooling 修复（pyc_batch_verify.py + testqouter/round1/base.py 增加 code-object 身份噪声过滤）后，IQCommon/__init__.pyc 实测 100% 字节码一致（原 0.5 为 code-object 地址/路径噪声）；R01-12 状态升级为 ok
- [x] T2.02 第 02 轮（取第 2 个 pyc: IQCommon/api/__init__.pyc，已 commit aab71b8）
- [x] T2.03 第 03 轮（取第 3 个 pyc: IQCommon/api/klinedata.pyc）
  - [x] T2.03.1 测试工程师：取下一个 pyc，反编译 + 字节码 diff → `rounds/round_03/test_engineer/decompile_report.md`（51.11%，22 mismatches，14 复现实例 10 DEFECT-REPRO）
  - [x] T2.03.2 修复工程师：按区域归约算法修复 → `rounds/round_03/repair_engineer/fix_report.md`（Pattern D dictcomp key/value 互换修复，51.11%→53.33%，1/5 模式修复）
  - [x] T2.03.3 commit + push `rcm-r03:`
  - 残留：Pattern A/B/C/E 共 21 个不一致函数，后续轮次修复
- [x] T2.04 第 04 轮（取 pyc #3: IQCommon/api/klinedata.pyc，续修 Pattern A）
  - [x] T2.04.1 测试工程师：取下一个 pyc，反编译 + 字节码 diff → `rounds/round_04/test_engineer/decompile_report.md`（53.33%，21 mismatches，15 复现实例 8 NO-DEFECT/7 DEFECT-REPRO）
  - [x] T2.04.2 修复工程师：按区域归约算法修复 → `rounds/round_04/repair_engineer/fix_report.md`（Pattern A 子模式 A1 BoolOp-in-try-body-if 坍缩修复，4/5 Pattern A repro 修复，实际 pyc match_rate 持平 53.33% — 实际函数触发 A2 子模式残留）
  - [x] T2.04.3 commit + push `rcm-r04:`
  - 残留：Pattern A 子模式 A2（9 函数）+ Pattern B/C/E 共 21 个不一致函数，后续轮次修复
- [x] T2.05 第 05 轮（取 pyc #4: IQCommon/data/base_storage.pyc，新 pyc 轮询）
  - [x] T2.05.1 测试工程师：取下一个 pyc，反编译 + 字节码 diff → `rounds/round_05/test_engineer/decompile_report.md`（80%→100%，1 mismatch，12 复现实例 7 DEFECT-REPRO/5 NO-DEFECT）
  - [x] T2.05.2 修复工程师：按区域归约算法修复 → `rounds/round_05/repair_engineer/fix_report.md`（Pattern M 装饰器调用坍缩 @deco()→@deco 修复，_generate_decorator ASTCall 始终发射括号，11/12 repro NO-DEFECT，base_storage.pyc 100% 升级 ok）
  - [x] T2.05.3 commit + push `rcm-r05:`
  - 残留：Pattern M2（repro_11 堆叠装饰器嵌套错误，表达式重建层，后续轮次修复）
- [x] T2.06 第 06 轮（取 pyc #5: IQCommon/data/basic_data_source.pyc，新 pyc 轮询）
  - [x] T2.06.1 测试工程师：取下一个 pyc，反编译 + 字节码 diff → `rounds/round_06/test_engineer/decompile_report.md`（pending→100%，0 mismatch，10 控制组复现实例全部 NO-DEFECT）
  - [x] T2.06.2 修复工程师：无需修复（pyc 首次验证即 100%）→ `rounds/round_06/repair_engineer/fix_report.md`（no repair needed）
  - [x] T2.06.3 commit + push `rcm-r06:`
  - 残留：无新增；跨轮残留 Pattern A2/B/C/E/F/M2 不变
- [x] T2.07 第 07 轮（取 pyc #6: IQCommon/backtest/backtest.pyc，新 pyc 轮询）
  - [x] T2.07.1 测试工程师：取下一个 pyc，反编译 + 字节码 diff → `rounds/round_07/test_engineer/decompile_report.md`（failed 0%，backtestOK.py 含 2 处语法错误 Pattern G + Pattern T，13 复现实例 9 DEFECT/4 NO-DEFECT）
  - [x] T2.07.2 修复工程师：按区域归约算法修复 → `rounds/round_07/repair_engineer/fix_report.md`（Pattern G f-string 花括号转义 + Pattern T 3 处 block_to_region 归属守卫；4 G repro 全修复，1/2 T repro 全修复 1 编译通过；backtest 编译通过，main partial 33%；graph 残留 Pattern T3）
  - [x] T2.07.3 commit + push `rcm-r07:`
  - 残留：Pattern T3（graph.pyc 嵌套 try in loop，_generate_try post-try 检测消费 handler）/ Pattern T2（except body drop）/ repro_05 trailing-return / 跨轮残留 A2/B/C/E/F/M2 不变
- [x] T2.08 第 08 轮（取 pyc #7: IQCommon/graph.pyc，R07 残留 Pattern T3，failed 优先）
  - [x] T2.08.1 测试工程师：取下一个 pyc，反编译 + 字节码 diff → `rounds/round_08/test_engineer/decompile_report.md`（failed 0% → partial 87.10%，27/31 一致，Pattern T3 _generate_try post-try 检测消费外层 handler_entry，14 复现实例 6 DEFECT/8 NO-DEFECT）
  - [x] T2.08.2 修复工程师：按区域归约算法修复 → `rounds/round_08/repair_engineer/fix_report.md`（Pattern T3 修复，_generate_try post-try 块检测 else_blocks + try_blocks 两分支追加 block_to_region 归属守卫；repro_11 ERROR→DEFECT-REPRO 编译通过；graph.pyc failed→partial 87.10%）
  - [x] T2.08.3 commit `rcm-r08:`（LOCAL only — push 失败网络 DNS 故障，push-pending）
  - 残留：graph.pyc 4 mismatch 函数（create_full_graph OUTER parent 误判 + 3 函数独立模式）/ 跨轮残留 T2/A2/B/C/E/F/M2 不变
- [x] T2.09 第 09 轮（取 pyc #6: IQCommon/backtest/backtest.pyc，R07 残留 Pattern G2，failed 优先）
  - [x] T2.09.1 测试工程师：取下一个 pyc，反编译 + 字节码 diff → `rounds/round_09/test_engineer/decompile_report.md`（failed 0%，Pattern G2 f-string COMPARE_OP 截断，handle_backtest_build true_diffs=327，14 复现实例 9 DEFECT-REPRO）
  - [x] T2.09.2 修复工程师：按区域归约算法修复 → `rounds/round_09/repair_engineer/fix_report.md`（Pattern G2 修复，_if_extract_cond_instructions COMPARE_OP 清空加双重 FORMAT_VALUE 结构守卫；8/9 DEFECT-REPRO 修复；f-string 5/25→25/25 段；残留 repro_12 链式比较跨块误判 + latent Pattern Q quoting bug）
  - [x] T2.09.3 commit + push `rcm-r09:`
  - 残留：repro_12 Pattern G3（链式比较跨块误判）/ backtest.pyc Pattern Q（f-string quoting bug，latent，code_generator.py）/ 跨轮残留 T3/T2/A2/B/C/E/F/M2 不变
- [x] T2.10 第 10 轮（取 pyc #6: IQCommon/backtest/backtest.pyc，R09 残留 Pattern Q，failed 优先）
  - [x] T2.10.1 测试工程师：取下一个 pyc，反编译 + 字节码 diff → `rounds/round_10/test_engineer/decompile_report.md`（failed 0%，Pattern Q f-string 定界符引号冲突，handle_backtest_build SyntaxError line 69，10 复现实例 7 DEFECT-REPRO）
  - [x] T2.10.2 修复工程师：按区域归约算法修复 → `rounds/round_10/repair_engineer/fix_report.md`（Pattern Q 修复，_generate_joined_str + _generate_joined_str_from_dict + FormattedValue 顶层分支 定界符选择重构；7/7 DEFECT-REPRO 修复；backtest failed→partial 50%，handle_backtest_build 100% 一致）
  - [x] T2.10.3 commit + push `rcm-r10:`
  - 残留：backtest.pyc `<module>` 8 true_diffs（NOP padding / LOAD_CONST 顺序，Pattern R 模块级）/ 跨轮残留 T3/T2/A2/B/C/E/F/M2/G3 不变
- [x] T2.11 第 11 轮（取 pyc #8: IQEngine/main.pyc，R07 残留 Pattern C2，partial 优先）
  - [x] T2.11.1 测试工程师：取下一个 pyc，反编译 + 字节码 diff → `rounds/round_11/test_engineer/decompile_report.md`（partial 33.33%，Pattern C2 tuple unpack no-SWAP，2 BUG：守卫过保守 + cond_block 路径缺失，12 复现实例 10 DEFECT-REPRO/2 NO-DEFECT）
  - [x] T2.11.2 修复工程师：按区域归约算法修复 → `rounds/round_11/repair_engineer/fix_report.md`（Pattern C2 BUG A 守卫白名单→黑名单 + BUG B _if_extract_cond_instructions 添加 C2 检测；7 真实缺陷 repro 全修复；main.pyc _adjust_start_date tuple 解包修复，残留 2 trailing-return diffs）
  - [x] T2.11.3 commit + push `rcm-r11:`
  - 残留：main.pyc `_adjust_start_date` 2 true_diffs（trailing LOAD_CONST None）/ `run` 375 true_diffs（独立模式）/ 跨轮残留 T3/T2/A2/B/C/E/F/M2/G3/R 不变
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
