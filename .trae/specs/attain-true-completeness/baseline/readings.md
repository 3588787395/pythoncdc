# 基线读数快照（gate 42 终验 + wiki v7 台账）

- 快照日期：2026-10-17
- 冻结树：HEAD `3e0d6905a392c86361c2f75089ddd745755ff9d5`（rr-v2r10：10.1 全量终验 + VERIFICATION.md + WIKI_BRIEF.md）
- 源目录（S1）：`.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round10/`
- 本快照只读复读；所有数字均给出源文件与行号。

## 1. gate 42 终验（任务 10.1 验证序六步，全绿）

### 1.1 402 八分片（regen → batch → compare）

- 合计：**402/402 文件 success、6617/6617 单元（100%）**；compare **REGRESSIONS=0 ×8**
  - 源：`final_verify_summary.json:130-135`（total units 6617/6617、files_failure 0）；`final_verify_log.txt:61/100/139/178/217/256/295/355`（八次 COMPARE 均 `REGRESSIONS=0 IMPROVED=0`）；`VERIFICATION.md:12-19`
- 分片单元明细（success/total 全 100%）：
  - shard0 786/786、shard1 469/469、shard2 538/538、shard3 887/887、shard4 855/855、shard5 999/999、shard6 801/801、shard7 1282/1282（拆半 _shard7_a 608 + _shard7_b 674）
  - 源：`final_verify_summary.json:40-129`；`final_verify_log.txt:25-355`
- total_elapsed = **614.3s**（单链串行；源：`final_verify_summary.json:134`；`VERIFICATION.md:5`）
- compare 基线 = `rounds/round10/baseline42/`（= merge gate 42 `e42b8509` 认证件，round9 已转换，逐位同源；源：`VERIFICATION.md:3`）

### 1.2 regen 零字节差异

- regen 后 `site-packages/**` **git 零 M 态**（402 产物零字节差异；与 compare 逐位双证）
  - 源：`VERIFICATION.md:19`（注：该读数不在 summary/log/iv2 三件中，引自同目录 VERIFICATION.md）；regen 八分片 rc=0 且 `0 failed` 源：`final_verify_log.txt:1-23`；`regen_shard0..7.json` 全空

### 1.3 34 集（small34）

- **1568/1568（100%）、34/34 success**（A 515/515 + B 1053/1053）
  - 源：`final_verify_log.txt:358-434`（两半 515/515、1053/1053）；`final_verify_summary.json:2-11`
- compare（vs v2 基线）：`1505/1568 -> 1568/1568`、files success 1→34、**REGRESSIONS=0 IMPROVED=33**（failure→success 33 行清单见 `final_verify_log.txt:465-499`；判定行 `:500-502`）

### 1.4 quotation 单验

- `status=success units=153/153 success_rate=100.00%`（rc=0）
  - 源：`final_verify_log.txt:504-508`；`final_verify_summary.json:12-15`

### 1.5 tests 七套件

- 读数：**2 failed / 282 passed / 2 xpassed in 8.94s**（rc=1）
- 失败名单（与基线逐位一致）：
  - `test_B01_simple_if_then_else_merge`（`tests/test_algorithm_correctness.py::TestDominanceFrontierIf`）
  - `test_BOUNDARY_02_large_function`（`tests/test_deep_nesting_pressure.py::TestBoundaryConditions`）
  - 源：`final_verify_log.txt:510-518`（FAILED 行 516-517、汇总行 518）；`final_verify_summary.json:16-19`

### 1.6 IV.2 门禁自检（同 1.1 冻结树）

- 结果摘要（源：`final_verify_log.txt:520`；`final_verify_summary.json:20-38`；`r10v10_fv_iv2.json`）：
  - IMPORT_OK = true（八 core 模块）
  - COMPILE_OK = true（两文件 compile() + py_compile 过；BOM 双单头，见 §3）
  - 插桩：代码行 0 命中；唯一 2 行 `[T]` 命中（20631/21366）经 tokenize 判定 ∈ 字符串（docstring 形态记号）
  - `G3_forbidden_prefix_new_defs` = 0（`r10v10_fv_iv2.json:31`）
  - G4 可疑行 = 0（`r10v10_fv_iv2.json:32`）；G0 各计数项均为空/ok（`:20-30`）
  - repro 引用 = round9 实测 17 件 + 承重面 quotation 153/153（冻结树复检不重登；`:11-19`）
  - 影响面引用：REGRESSIONS=0 ×8 + 402 产物零字节差异 + 34 集 IMPROVED=33（`:33-35`）

## 2. wiki v7 台账（形式层三态）

- **完备 103 / 破口 25 / 零能力 0 ⇒ 完备占比 80.47%**（103 ÷ 128 = 80.46875%）
- 分母 128 = 表A 29 + 表B 68（31+8+29）+ 表C 31
- 组合级 25 号（B42–B51/B56–B65/B69–B71/B73–B76 内未封闭部分，扣除已划除 B45/B64）：**清零 9 / 维持 16**
- 源：`wiki/concepts/decompile-invariant-completeness.md` §0（行 35-40）与 §5.5（行 190-200）；组合级分层源 = `rounds/round10/WIKI_REVIEW.md` §3.3（行 195-236）
- 明细另册：`baseline/breaches_25rows.md`（25 行破口）、`baseline/combos_25.md`（组合级 25 号分层）

## 3. 工具面读数

- `docs/refactor/syntax-coverage.json`：
  - sha256 = `86539c44fe6ae974fa5a03f2500f5d0fe99d4bac3d34f79b8ca6a766bfd4b9ae`（前 16 位 `86539c44fe6ae974`；**本快照复算复核一致**）
  - size = **2724** 字节
  - 读数：**128/128 = 100%、uncovered = 0**
  - 源：`WIKI_REVIEW.md:250-261`（步④ before/after 快照同 sha ⇒ 确定性重跑零漂移）；存证件 `r10v10_coverage_before.json` / `r10v10_coverage_after.json`

## 4. 常量口径（基线固定值）

### 4.1 双单头 BOM

- `core/cfg/region_ast_generator.py` 与 `core/cfg/region_analyzer.py` 均为 **`efbbbf` single-head（双单头 BOM）**
  - 源：`r10v10_fv_iv2.json:3-10`（两文件 `:bom` = `efbbbf single-head`）；`final_verify_summary.json:23-24`（值 = `one`/`one`）
  - 判定式（`rounds/round10/final_verify_run.py:112-118`）：raw[:3] == BOM 且 raw[3:6] 非 BOM 起头；round8/9 既有约定，`VERIFICATION.md:31`

### 4.2 tests 七套件名单

源：`rounds/round10/final_verify_run.py:18-26`（SEVEN_TESTS）

1. `tests/test_algorithm_correctness.py`
2. `tests/test_deep_nesting_pressure.py`
3. `tests/test_control_flow_completeness_matrix.py`
4. `tests/test_complete_syntax_coverage.py`
5. `tests/test_boundary_cases.py`
6. `tests/test_core_functional.py`
7. `tests/test_repo_tool_hygiene.py`

### 4.3 IV.2 门禁自检项口径

源：`rounds/round10/final_verify_run.py:99-151`（Phase 6）+ `rounds/round10/iv2_recheck.py:28-105` + 输出件 `r10v10_fv_iv2.json`

- IMPORT_OK：`core.cfg` 八模块（region_analyzer / region_ast_generator / comprehension_generator / ast_generator_v2 / code_generator / pattern_parser / ast_converter / exception_handler）import 通过
- COMPILE_OK：`compileall core` + 两文件 `compile()` / `py_compile` + BOM 双单头
- repro_ref：round9 实测引用（`r9v9fix3b_*` 17 件、承重面 quotation 153/153 等；冻结树复检不重复登记）
- G0（对 `git diff e42b8509..HEAD -- core/` 新增本核查）：docstring 模板（三方法 `_extract_recheck_store_stmts` 978 / `_b126r2_raise_only_trampoline_exit` 1360 / `_b124r1_chain_region_is_self_return` 1391 字符）；`new_self_state_added_lines` = 0；`whitelist_path_strings` = 0；`start_offset_threshold_lines` = 0；`ast_parse` = ok
- 插桩：tokenize 区分代码行 / 字符串行；检查键 `breakpoint(` / `pdb.set_trace` / `[T] [W] [G]` 标记 ⇒ 代码行 0 命中
- G3_forbidden_prefix_new_defs = 0：新增 `def _fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 计数
- G4_suspect_lines = 0：疑硬编码 depth/hop/count/limit/cap/max_ 阈值的比较行
- 影响面引用：compare REGRESSIONS=0 ×8 + 402 产物零字节差异 + 34 集 IMPROVED=33

## 5. 套件复制注记

- 门禁批次须逐批复读的固定五常量 = §4.1 双单头 BOM、§4.2 七套件名单、§4.3 IV.2 口径、本 §1 终验数值、§2 三态数值。
- `baseline/kit/` 复制源：`verify_driver.py` / `verify7_split.py` / `final_verify_run.py` / `iv2_recheck.py` / `baseline42/` 均自 S1（round10）；**`make_baseline42.py` S1 无此件（经 Test-Path 实测），按功能同源自 S9（round9，行 6-7 硬编码 DST=round9\baseline42，用途为 baseline42 生成脚本）复制**，内容未改。此为与任务口径的唯一来源差异，如实登记（对照：`rounds/round9/make_baseline42.py`）。
