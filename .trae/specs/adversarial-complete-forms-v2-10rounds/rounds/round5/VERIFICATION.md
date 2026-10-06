# Round 5 主代理验证（Task 5.4）—— 验证序六步

- 规范：`.trae/specs/adversarial-complete-forms-v2-10rounds`
- 角色：主代理（零实现；只调度、跑验证序六步、归档）
- 验证对象 HEAD：`3078f55f`（复核终审批次；核心 = round5 修复 `6fa1fa70` + 打回整改 `711dc506`）
- 方法学 RV2：一切读数先 `python pycdc.py <pyc> -o <同目录>OK.py` regen，再 `scripts/pyc_verify.py` verify
- 判据唯一：`scripts/pyc_verify.py`（ruler = pylingual `equivalence_check.py::compare_pyc`，单位 = code object 含嵌套）
- 编排：`rounds/round5/final_verify_run.py`（后台运行，退出码 0；日志 `final_verify_log.txt`）

---

## §0 验证序六步总表

| 步 | 内容 | 读数 | 判定 |
|---|---|---|---|
| 1 | 402 全量：八分片 regen + verify + compare（对照 `baseline/shards`） | **6554/6617（99.05%）**、files_failure=33；**8 片 REGRESSIONS=0 / IMPROVED=0** | PASS |
| 2 | 34 小测试集 batch（拆两半 CUT=17）compare 基线 | **1505/1568（95.98%）**，**REGRESSIONS=0**（files: success 1 / failure 33 与基线逐位一致） | PASS |
| 3 | quotation.pyc 单验锚点 | **152/153（99.35%）**，唯一失败 `<module>.change_his_to_forward`（与基线同一单元） | PASS |
| 4 | tests 六套件 `pytest -q` | **277 passed / 2 failed / 2 xpassed**（失败单元与基线同名单，无新增） | PASS |
| 5 | IV.2 门禁自检 | IMPORT_OK / compile_error=0 / BOM 单头 / 插桩 0 / I.4 五项新增 0 / I.5 七前缀新增 0 / 落地标记 grep 命中 | PASS |
| 6 | 读数汇报 | 见 §6 | PASS |

**轮门禁**：≥1 破口封闭 ✅（B114/B115/B116 三破口全封闭）∧ 验证序六步全过 ∧ REGRESSIONS=0 ✅。

---

## §1 步骤一：402 全量八分片（RV2）

REGEN0–7 全 rc=0（20.5s–35.3s/片）；VERIFY0–6 + VERIFY7-SPLIT 全 rc=0；COMPARE0–7 全 rc=0。

| 分片 | 新读数 | Movement |
|---|---|---|
| shard0 | 777/786（98.85%） | REGRESSIONS=0 IMPROVED=0 |
| shard1 | 462/469（98.51%） | REGRESSIONS=0 IMPROVED=0 |
| shard2 | 537/538（99.81%） | REGRESSIONS=0 IMPROVED=0 |
| shard3 | 883/887（99.55%） | REGRESSIONS=0 IMPROVED=0 |
| shard4 | 848/855（99.18%） | REGRESSIONS=0 IMPROVED=0 |
| shard5 | 993/999（99.40%） | REGRESSIONS=0 IMPROVED=0 |
| shard6 | 789/801（98.50%） | REGRESSIONS=0 IMPROVED=0 |
| shard7 | 1265/1282（98.67%） | REGRESSIONS=0 IMPROVED=0 |
| **合计** | **6554/6617（99.05%）** | **REGRESSIONS=0 ×8**；files_failure=33、compile_error=0 |

与 `baseline/`（round4 终态 6554/6617、369/402）**逐位一致**，无 success→failure 回退。

---

## §2 步骤二：34 小测试集

`small34_report_a/b.json` → 合并 `small34_report_new.json` → compare `baseline/small_test_report.json`：

```
units: 1505/1568 (95.98%) -> 1505/1568 (95.98%)
files: success 1 -> 1
REGRESSIONS=0 IMPROVED=0
```

Movement Matrix 对角（success 1 / failure 33），无位移。**NEWFAIL=0**。

---

## §3 步骤三：quotation.pyc 单验锚点

`[single] status=failure units=152/153 success_rate=99.35%`；唯一失败单元 `<module>.change_his_to_forward: Failure: Different control flow`——与 baseline 同一单元，**零新增失败**。

---

## §4 步骤四：tests 六套件

`tests/test_algorithm_correctness.py`、`test_deep_nesting_pressure.py`、`test_control_flow_completeness_matrix.py`、`test_complete_syntax_coverage.py`、`test_boundary_cases.py`、`test_core_functional.py`：

```
2 failed, 277 passed, 2 xpassed
```

失败单元与 baseline 同名单（`test_B01_simple_if_then_else_merge`、`test_BOUNDARY_02_large_function`），**无新增失败**。

---

## §5 步骤五：IV.2 门禁自检

| 门禁 | 检查 | 读数 | 判定 |
|---|---|---|---|
| IMPORT_OK / compile_error | 八分片 `files_by_status.compile_error` 求和 | **0** | PASS |
| BOM 单头 | `region_analyzer.py` / `region_ast_generator.py` 首 3 字节 + 全文 BOM 计数 | 均 `efbbbf` / 计数 = **1** | PASS |
| 插桩残留 | grep `pdb|breakpoint(|# TODO|# FIXME|# DEBUG|B115DBG` in 两核心文件 | **0** | PASS |
| I.5 七前缀（新增） | grep `def (_fix_|_merge_|_patch_|_fallback_|_hack_|_workaround_|_temp_)` | 命中 2，均 `region_ast_generator.py` 历史存量（复核 §1 已认定，**非本轮新增**） | PASS（新增 0） |
| I.4-② start_offset 常数比较 | grep `start_offset == \d|> \d|< \d` in 两核心文件 | **0** | PASS |
| 落地标记 | grep `\[B114 fix\]/[B115 fix]/[B116 fix]` in 两核心文件 | 命中 **10** | PASS |
| 在途变更 | `git status --porcelain`（非未跟踪） | **空**；无 tracked `*OK.py` 被修改 | PASS |

---

## §6 步骤六：读数汇报与轮门禁

**Round 5 终读数**：
- 单元级：402 全量 **6554/6617（99.05%）**；文件级 **369/402（33 failure）**——与基线逐位一致。
- 34 小测试集 **1505/1568**；quotation **152/153**；tests **277 passed / 2 failed / 2 xpassed**；8 片 compare **REGRESSIONS=0**。
- 本轮修复：**B114**（未别名点号 import 幻影别名，含 path3 else 分支与 `_loop_extract_self_loop_stmts` 两条收口路径）、**B115**（外层 if 体首 while 条件融合）、**B116**（函数内裸注解 → 局部名退化）三破口全封闭；最小复现 `r5v5_01`/`r5v5_08`+`k1`+`k2`/`r5v5_03`+`k4` 及复核变体 `r5v5r_b114_in_for`/`r5v5r_b114_in_while` 全转 MATCH。
- 站桩回归 6 面 **WORSE=0**（复核终审独立复跑，见 `REVIEW2.md` §6）。

**移交下一轮（Task 6 起）**：同 Bn 存量（B105 walrus / B106 star_args / B111 decorator / B102 残余 except*×with / round3 F5 star-lambda）；非阻断登记项（B116 posonlyargs/co_cellvars 缺口、注解硬编码 `str`）；沿袭未封闭清单（B103 残余、B104–B112、B113、B98/B99 残余、B44、B1b 五单元、B87/B88 残余、B93/B94/B96/B97）；合规存量观察（17 处 env-gated 调试守卫、`region_ast_generator.py:24486-24487` 偏移魔数、`max_depth` 搜索上限）。

*主代理零实现；本报告一切读数经 RV2；提交前缀 `rr-v2r05:`。*