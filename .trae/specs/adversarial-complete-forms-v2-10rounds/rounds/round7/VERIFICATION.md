# VERIFICATION.md —— Round 7 主代理验证（Task 7.4）

- 规范：`.trae/specs/adversarial-complete-forms-v2-10rounds`
- 主代理角色：调度 + 阶段提交 + 全量验证 + push（本轮零实现）
- 验证前置 HEAD：`417ec182`（`rr-v2r07: round7 复核（任务 7.3）`）
- 判据唯一工具：`scripts/pyc_verify.py`（ruler = pylingual `equivalence_check.py::compare_pyc`，单位 = code object 含嵌套）
- 方法学 RV2：一切读数先 `python pycdc.py <pyc> -o <同目录>OK.py` regen 再 verify
- 编排脚本：`rounds/round7/final_verify_run.py`（8 分片 regen → verify 0–6 + shard7 拆分 → compare×8 → small34 拆两半 → quotation → tests 六套件）；日志 `rounds/round7/final_verify_log.txt`
- 本轮性质：**算法修复**（Task 7.2：B117/B118/B119/B120 四守卫封闭，唯 core 改动 = `core/cfg/region_ast_generator.py` +516/-6）

---

## §1 验证序六步读数表

| 步 | 项目 | 本轮读数 | 基线（承接/round6 终态） | 判定 |
|---|---|---|---|---|
| 1 | 402 全量·单元级 | **6554/6617（99.05%）** | 6554/6617 | 逐位一致 |
| 1 | 402 全量·文件级 | **369/402**（failure 33） | 369/402 | 逐位一致 |
| 1 | 8 分片 compare | **REGRESSIONS=0 ×8，IMPROVED=0** | — | PASS |
| 2 | 34 小测试集 | **1505/1568（95.98%）** | 1505/1568 | REGRESSIONS=0，NEWFAIL=0 |
| 3 | quotation.pyc 单验 | **152/153（99.35%）** | 152/153 | 唯一失败 `change_his_to_forward` 与基线同 |
| 4 | tests 六套件 | **277 passed / 2 failed / 2 xpassed** | 同 | 失败名单同基线 |
| 5 | IV.2 门禁自检 | **全 PASS**（见 §5） | — | PASS |
| 6 | 读数汇报 | 见 §6，轮门禁达成 | — | — |

---

## §2 402 八分片明细（单元级 + 文件级）

| 分片 | files_by_status | units |
|---|---|---|
| shard0 | compile_error 0 / error 0 / failure 5 / success 46 | 777/786 |
| shard1 | 0 / 0 / 3 / 48 | 462/469 |
| shard2 | 0 / 0 / 1 / 50 | 537/538 |
| shard3 | 0 / 0 / 3 / 48 | 883/887 |
| shard4 | 0 / 0 / 5 / 46 | 848/855 |
| shard5 | 0 / 0 / 5 / 46 | 993/999 |
| shard6 | 0 / 0 / 3 / 48 | 789/801 |
| shard7 | 0 / 0 / 8 / 37 | 1265/1282 |
| **合计** | **failure 33 / success 369** | **6554/6617** |

**8 分片 compare（baseline/shards vs 本轮）**：全部 `REGRESSIONS=0 IMPROVED=0`，各分片 units 与基线逐位一致（shard0 777/786、shard1 462/469、shard2 537/538、shard3 883/887、shard4 848/855、shard5 993/999、shard6 789/801、shard7 1265/1282）。

注：verify/compare 全部子命令 ≤300s（verify 内部 290s 上限）；REGEN 阶段为产品再生（单文件 90s 超时守卫，非验证读数），分片墙钟 317.6/260.7/88.9/207.9/42.8/43.0/40.4/43.6s，与 round6 同编排同口径。

---

## §3 34 小测试集 + quotation

- 34 集（`baseline/failing_index.json`，拆两半 batch）：**1505/1568（95.98%）**；`compare --before baseline/small_test_report.json` → `REGRESSIONS=0 IMPROVED=0`，与基线逐位一致（files failure 33 / success 1，名单同基线）。
- quotation.pyc 单验：**152/153**，唯一失败 `***<module>.change_his_to_forward: Different control flow`（与基线同，历史既有）。

---

## §4 tests 六套件

命令：`python -m pytest tests/test_algorithm_correctness.py tests/test_deep_nesting_pressure.py tests/test_control_flow_completeness_matrix.py tests/test_complete_syntax_coverage.py tests/test_boundary_cases.py tests/test_core_functional.py -q --tb=no`

**277 passed / 2 failed / 2 xpassed**（与基线名单一致）：
- `test_algorithm_correctness.py::TestDominanceFrontierIf::test_B01_simple_if_then_else_merge`
- `test_deep_nesting_pressure.py::TestBoundaryConditions::test_BOUNDARY_02_large_function`

---

## §5 IV.2 门禁自检

| 门禁项 | 读数 | 判定 |
|---|---|---|
| IMPORT_OK | `import core.cfg.region_analyzer` / `region_ast_generator` / `code_generator` 均成功 | PASS |
| COMPILE_OK / compile_error | 8 分片 compile_error 合计 **0**；触及文件 `py_compile` doraise 全过 | PASS |
| BOM 单头 | `region_analyzer.py` head3=`efbbbf` count=1；`region_ast_generator.py` head3=`efbbbf` count=1 | PASS |
| 插桩残留（新增） | 修复期临时门控 `R7FIXDBG` grep = **0**（全清） | PASS |
| I.5 七前缀（新增） | 修复 diff（`49e5301b..384ad07c`）新增七前缀方法 = **0** | PASS |
| I.4 黑名单（新增） | 修复 diff 新增 `depth>`/`max_depth`/`start_offset` 魔法条件 = **0**（评审复核逐 hunk 确证判据全白名单） | PASS |
| 落地标记（I.6） | `region_analyzer.py` `C 条款：` **10** 处；`region_ast_generator.py` `C 条款：` **24** 处（+1 = 新谓词 `_if_region_is_loop_body_tail`）；FIX.md §9 锚点 20/20 grep 实证（复核 §2） | PASS |
| 在途变更 | `git status --porcelain core/` 空；tracked `*OK.py` 零修改（regen 副作用逐阶段还原） | PASS |

---

## §6 汇报与轮门禁

**本轮读数**：
- 单元级成功率：402 全量 **6554/6617（99.05%）** 与基线逐位一致，零回退
- 文件级 success：**369/402** 与基线一致
- 本轮封闭破口：**4 项（B117/B118/B119/B120）**，全部「已落地」并经 7.3 复核「已复审」（wiki §8.3 状态机闭环）
- 站桩回归读数（6 面，修复后 r7v7fix_* 证据 + 复核独立复跑）：round2face **235/251（+1 改善）**、probe42 176/196、round1face 417/423、residual **418/446（+1 改善）**、oldface 664/692、quotation 152/153；**WORSE = 0**
- 攻击面读数：r7v7 47 探针 attack **122/122**（评审基线 114/122，+8）+ 负对照 **18/18**；复核变体 r7v7r_* 5 文件 35 单元中 34 MATCH（唯一失败 `r7v7r_b121_whilehdr` = 新登记 B121，基线 `49e5301b` 同败 5/7 确证**存量缺口、非本批回归**）
- 新登记未封闭：**B121**（移交 Round 8 残余破口清零冲刺）
- 完备占比：本轮无台账判定变更（形式层 维持 128/128 口径不变）

**轮门禁**：每轮 ≥1 破口登记并封闭（本轮 4 项）**达成**；另附 3 项读数改善（round2face/residual/攻击面）。

**回退拦截**：未触发（REGRESSIONS=0 ×8 + 34 集 NEWFAIL=0 + 站桩 WORSE=0 + tests 失败名单同基线）。
