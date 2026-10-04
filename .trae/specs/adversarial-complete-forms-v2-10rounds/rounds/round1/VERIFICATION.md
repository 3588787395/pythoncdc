# VERIFICATION.md — Round 1 主代理无回退验证（任务 1.4 闭环复跑）

- 验证人：主代理（零实现，判据唯一 = `scripts/pyc_verify.py`，ruler sha256 前缀 9c7567bd6776b36b，interpreter 3.11.7）
- 触发：616437c3 首跑发现 shard7 op_station.pyc REGRESSION=1 → 打回 → 批次 C 修复（12d7ddb9）→ REVIEW3 只读对抗审计**终判放行**（判据全落 I.4 白名单、边类型封闭与块构建代码事实一致、对抗实测 v1/v3/v4 FAIL→MATCH、v2 存量同态、BOM/插桩/前缀三项门禁全过）
- 本轮 = 批次 C 放行后的验证序全量复跑；驱动脚本 `final_verify_run.py`，逐命令日志 `final_verify_log.txt`；**regen 先行**（402 OK.py 全部以 HEAD 代码先删后生成，杜绝陈旧产物读数），总耗时 494s，全部命令 ≤300s

## 1. 验证序六步实测

| # | 步骤 | 结果 | 判定 |
|---|------|------|------|
| 1 | 34 小测试集 batch（baseline/failing_index.json） | 1505/1568（95.98%），compare vs baseline/small_test_report.json：success 1→1、failure 33→33，**零位移** | PASS |
| 2 | 全量 402 八分片 batch + compare（before = baseline/shards/shard{0-7}_report.json） | 6554/6617（99.05%）、文件 369 success/33 failure/0 compile_error/0 error；8 片 Movement Matrix 全部对角线零移动（REGRESSIONS=0，IMPROVED=0） | PASS |
| 3 | quotation.pyc 单验 | 152/153（99.35%），唯一失败单元 `***<module>.change_his_to_forward: Different control flow` 与承接基线同单元；single 命令 exit 1 = failure 状态预期行为 | PASS |
| 4 | tests 六套件（algorithm_correctness / deep_nesting_pressure / control_flow_completeness_matrix / complete_syntax_coverage / boundary_cases / core_functional） | **277 passed / 2 failed / 2 xpassed**（3.55s）；失败名单 = test_B01_simple_if_then_else_merge + test_BOUNDARY_02_large_function，与基线名单逐位一致，零新增 | PASS |
| 5 | IV.2 门禁自检 | 见 §2 | PASS |
| 6 | 读数汇报 | 见 §3 | — |

分片明细（units=success/total）：

| shard0 | shard1 | shard2 | shard3 | shard4 | shard5 | shard6 | shard7 |
|--------|--------|--------|--------|--------|--------|--------|--------|
| 777/786 | 462/469 | 537/538 | 883/887 | 848/855 | 993/999 | 789/801 | 1265/1282 |

op_station.pyc（shard7，616437c3 时 20/21 REGRESSION=1）本轮 **21/21 恢复**，全量单元总数回到基线 6554/6617 —— 批次 C 回归闭环确认。

## 2. IV.2 门禁自检

| 项 | 证据 | 判定 |
|---|------|------|
| IMPORT_OK | import core.cfg.{region_analyzer, region_ast_generator, structured_analyzer, code_generator, exception_handler, pattern_parser, comprehension_generator} 全部成功 | PASS |
| COMPILE_OK | 产物 ptradeAccountOK.py `compile()` 通过；round1 diff 涉及产物 op_stationOK.py 经批次 C 门禁 1 single 21/21 复核 | PASS |
| BOM 单头 | region_analyzer.py / region_ast_generator.py 首 3 字节 = `efbbbf`，全文 BOM 计数各 = 1（无双头） | PASS |
| repro 全 match | 修复面 v1/v3/v4 MATCH、负对照全 MATCH（REVIEW3 §2 独立复跑）；本轮 compare 零位移 | PASS |
| G0 自检 | 新增判据全为块元数据/边类型/前驱集合/区域成员关系（REVIEW3 §1.1 逐项白名单归属核查）；无跨层反查新增、无 self 新状态（REVIEW3 §1.3：批次 C diff 仅 docstring + 守卫两处） | PASS |
| G3（0 新增前缀方法） | `git diff 616437c3..HEAD -- core/` 新增行 grep `def _(fix_/merge_/patch_/fallback_/hack_/workaround_/temp_)` = 0 | PASS |
| G4/插桩（0 硬编码上限、0 遗留插桩） | round1 diff（8236b6a0..HEAD）新增行 grep `print(/breakpoint(/import pdb` = 0；批次 A/B 已删 ast_generator_v2 魔数 62/74、structured_analyzer depth>3、DBG_OR/FIXA-DBG/FIXB-DBG（REVIEW2 §4 复验 0 命中） | PASS |
| 影响面（字节级） | 全量 regen 402 产物后 `git status`：**唯一变化的 OK.py = site-packages/fly/simtradding/ptradeAccountOK.py**（其余 401 产物与 HEAD 逐字节一致）——即批次 A/B/C 修复对全语料的净产物影响 = op_stationOK.py（已随 12d7ddb9 提交）+ ptradeAccountOK.py 两文件，其余零漂移 | PASS |
| 命令时限 | regen 每文件 90s / verify 290s 上限；实测最长单命令 VERIFY7-SPLIT 41.6s | PASS |

## 3. 读数汇报

- **单元级成功率**：6554/6617 = 99.05%（与承接基线逐位一致，回归闭环）
- **文件级 success**：369/402（failure 33 名单与基线一致）
- **本轮封闭破口**：批次 A = B48 残留变体、B46 尾项、B74；批次 B = B71、B73、B75、B76、B65；批次 C = B71 边类型封闭（op_station REGRESSION 根因修复）。合计 **8 项登记破口封闭**
- **新登记（存量移交）**：REVIEW2 §5 登记 **B77–B82**（基线同态证实）；REVIEW3 §2.2 登记候选 1 项（try/finally + while + 循环内 raise + finally 非空语句 → 循环体镜像泄漏进 finalbody）——因 B77–B82 已被 REVIEW2 占用，正式编号顺延为 **B83**，状态 = 未定位（移交 Round 2+）
- **站桩回归读数**：REVIEW2 §2 五行（round6 115/115、哨兵 site-packages 302/308 等）持平；本轮全量 compare 零位移为最强站桩证据
- **完备占比变动**：无（台账 v6 形式层 128/128 未变；本轮未做台账判定变更，Round 10 终审统一重验）

## 4. 遗留移交（致 Round 2+）

1. **B83**（未定位）：try/finally + 循环内 raise 形态，循环体镜像块泄漏进 Try.finalbody（REVIEW3 §2 rvC_v2，探针归档 probes_rvC/）
2. **B77–B82**：REVIEW2 §6.5 优先级建议 —— B77（match 臂三元）/B78（条件位融合）收益面最大；变体探针 probes_rv2/ 八文件可作回归基准
3. III.5 沿袭残留（B42×3/B43/B44/B47/B49–B53/B56–B62/B63/B69/B70/B11-R2）+ 零专攻 6 组（Round 2–9 主题输入，REVIEW.md §3.4 空白格清单）
4. ptradeAccountOK.py 在途重生成残留：本轮随归档提交（REVIEW3 §1.6 建议采纳，byte-identical 与 HEAD 现场重生成）

**终判：验证序六步全过，REGRESSIONS=0，Round 1 门禁通过，准予归档（任务 1.5）。**
