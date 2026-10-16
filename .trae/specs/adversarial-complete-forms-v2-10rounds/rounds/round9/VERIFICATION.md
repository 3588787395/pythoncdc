# Round 9 主代理验证（任务 9.4 验证序六步 + 9.5 归档）

- 轮主题：全台账 128 形态终局对抗复验（III.2–III.4 全形态各 ≥1 深层探针 + 负对照 + 站桩回归全重放）
- 基线与判据：**merge gate 42（e42b8509）**；compare 基线 = `rounds/round9/baseline42/shard0..7_report.json`（自 `.trae/specs/region-reduction-v3-full-corpus-100pct-10rounds/rounds/round42/after/` 转换：路径前缀 `D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main` → `F:/Downloads/pythoncdc-main`；转换先例 = `make_baseline42.py`，转换后 8 片全绿 786+469+538+887+855+999+801+1282=6617/6617、402/402）
- 驱动：`verify_driver.py`（regen/verify/compare，round8 同款，BL 表 = v2 baseline/shards，compare 基线改 baseline42）、`verify7_split.py`（shard7 拆两侧 CUT=23）、`final_verify_run.py`（六步编排）、`iv2_recheck.py`（IV.2 全项复检）
- 执行：regen 先行（402 个 `*OK.py` 全部以 HEAD 代码覆盖重生成，杜绝陈旧产物读数）→ 逐分片 batch → compare；全程 610s（`final_verify_summary.json`）；单链串行（无并行争用）

## 一、验证序六步实录

### ① 34 小测试集 batch（无回退）

| 段 | 文件 | 单元 | 状态 |
|---|---|---|---|
| A（17 pyc） | small34_report_a.json | 515/515 | 17/17 success |
| B（17 pyc） | small34_report_b.json | 1053/1053 | 17/17 success |
| 合计 | small34_report_new.json | **1568/1568（100%）** | **34/34 success** |

- compare（vs v2 基线 `baseline/small_test_report.json`）：`1505/1568 (95.98%) -> 1568/1568 (100.00%)`，files success 1→34，**REGRESSIONS=0 IMPROVED=33**。

### ② 402 全量八分片（regen → batch → compare）

| 分片 | 文件 | 单元 | compare |
|---|---|---|---|
| shard0 | 51/51 | 786/786 | REGRESSIONS=0 IMPROVED=0 |
| shard1 | 51/51 | 469/469 | REGRESSIONS=0 IMPROVED=0 |
| shard2 | 51/51 | 538/538 | REGRESSIONS=0 IMPROVED=0 |
| shard3 | 51/51 | 887/887 | REGRESSIONS=0 IMPROVED=0 |
| shard4 | 51/51 | 855/855 | REGRESSIONS=0 IMPROVED=0 |
| shard5 | 51/51 | 999/999 | REGRESSIONS=0 IMPROVED=0 |
| shard6 | 51/51 | 801/801 | REGRESSIONS=0 IMPROVED=0 |
| shard7 | 45/45 | 1282/1282 | REGRESSIONS=0 IMPROVED=0 |
| **合计** | **402/402** | **6617/6617（100%）** | **REGRESSIONS=0 ×8** |

- shard7 拆两半执行（23+22 文件：608/608、674/674），合并报告 `shard7_report_new.json` 1282/1282。
- **regen 后 `site-packages/**/ *OK.py` 相对 merge gate 提交态 git 零 M 态 = 402 产物逐字节一致**（本轮修复对认证语料零字节影响，与 compare 逐位 REGRESSIONS=0 双向互证）。

### ③ quotation 单验（零新增）

- `status=success units=153/153 success_rate=100.00%`（rc=0）；零新增失败（v2 检查表口径基线 152/153；merge gate 42 与本轮同为 153/153，逐位一致）。

### ④ tests 七套件（零新增失败）

- `python -X utf8 -m pytest tests/test_algorithm_correctness.py tests/test_deep_nesting_pressure.py tests/test_control_flow_completeness_matrix.py tests/test_complete_syntax_coverage.py tests/test_boundary_cases.py tests/test_core_functional.py tests/test_repo_tool_hygiene.py -q`
- 结果：**2 failed / 282 passed / 2 xpassed**；失败名单与基线逐位一致（`test_B01_simple_if_then_else_merge`、`test_BOUNDARY_02_large_function`）= **零新增失败**。

### ⑤ IV.2 门禁自检（`r9v9_fv_iv2.json`）

| 项 | 结果 |
|---|---|
| IMPORT_OK | ✓（八个 core 模块导入过） |
| COMPILE_OK | ✓（region_analyzer / region_ast_generator：compile() + py_compile 全过；**BOM `efbbbf` 双单头**——两文件首 3 字节均为单头，与 round8 VERIFICATION 同口径既有约定） |
| repro 全 match | 引用本轮 9.2/9.3b 修复/复核批实测（r9v9fix3b_* 17 件、承重面 quotation 153/153）；终验不重复登记 |
| G0 六项 | docstring：三新方法全带模板化 docstring（`_extract_recheck_store_stmts` 978 字符、`_b126r2_raise_only_trampoline_exit` 1360、`_b124r1_chain_region_is_self_return` 1391）；无 self 新状态 0 行；无白名单路径串 0 行；无 start_offset 阈值 0 行；ast.parse + py_compile ✓ |
| G3 | **0** 新增前缀方法（`_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 全扫 e42b8509..HEAD diff） |
| G4 | **0** 硬编码深度/计数上限（新增行扫描 depth/hop/count/limit/cap/max_ + 数值比较 = 0 命中） |
| 影响面 | 见 ①-②：compare 逐位 REGRESSIONS=0 与 402 产物零字节差异；34 集 IMPROVED=33 REGRESSIONS=0 |

### ⑥ 读数汇报

本文件即汇报（上表全量）；轮门禁对照 = 9.1 三态 128（完备 101 / 破口 27 / 零能力 0）→ 本轮封闭 B104 族 14 + B124 族 5 + B125 族 2 + B126 族 1 + 存量 B104-R4 1；站桩六面 2092/2161（较 gate42 基线 +1×3 附带改善、WORSE=0）；承重面全绿；移交 B127/B128/Yield 探针重建/B44 证据缺口 → Round 10（合法性已经 REVIEW2 §4 复核）。

## 二、运行勘误记录（透明存档）

1. **首跑驱动编码轰**：`verify_driver.py` / `verify7_split.py` 以 `print()` 直出 batch stdout 尾段，含 U+FFFD 撞 GBK 控制台 → VERIFY 各段 rc=1 假报（batch 本体无碍：报告 JSON 全量正常、compare 全绿）；`verify7_split` 更在打印处中断致合并未发生、`shard7_report_new.json` 缺；summary 循环因缺文件崩。修复（9a3d681c）= stdout 经 UTF-8 replace 写出 + IV.2 落日志 + 汇总容缺；**全链重跑（本文件读数）**。
2. **`verify7_split.py` 拆分标签笔误**：`reps = [run_half(h, 'a') for h in halves]`（'a' 硬编码，两半同名 → b 半报告覆盖 a 文件名；merge 用运行返回值故合并报告在首跑即正确——compare7 1282/1282 REGRESSIONS=0 为证）。修复为 `zip(halves, ('a','b'))` 并重跑该段：half a 608/608 + half b 674/674 → merged 1282/1282、COMPARE7 复跑一致；重跑实录已追加至 `final_verify_log.txt` 尾。
3. 首跑与重跑均为**同一确定性读数**（6617/6617、1568/1568、153/153、2/282/2 逐位一致），勘误仅涉日志与中间产物命名，不涉任何判据结果。

## 三、证据索引（rounds/round9/）

- `final_verify_log.txt`（六步逐段实录 + 重跑注记）、`final_verify_summary.json`（机器可读汇总）
- `baseline42/shard0..7_report.json`（基线转换件）、`make_baseline42.py`
- `shard0..7_report_new.json`（8 件）、`_shard7_a.json`/`_shard7_b.json`（拆半原件）、`regen_shard0..7.json`（全空 = 0 失败）
- `small34_report_a.json`/`small34_report_b.json`/`small34_report_new.json`
- `r9v9_fv_iv2.json` + `iv2_recheck.py`
- `verify_driver.py` / `verify7_split.py` / `final_verify_run.py`
- 前段：`FIX_R9.md`（142 行）、`REVIEW_DRAFT.md`（9.1）、`REVIEW2.md`、`REVIEW3.md`、`r9v9fix*_*`/`r9v9rev2_*`/`r9v9rev3_*` 全量证据

## 四、结论

**验证序六步全过、零新增失败、零回归（compare REGRESSIONS=0 ×8 + 34 集 REGRESSIONS=0）、认证语料 402 产物零字节差异。** 放行进入 9.5 归档与 push；Round 9 完成（封闭清单与移交清单见 FIX_R9.md / REVIEW3.md）。
