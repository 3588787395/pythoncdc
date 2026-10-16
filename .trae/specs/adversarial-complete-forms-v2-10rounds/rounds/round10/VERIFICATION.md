# Round 10 主代理全量终验（任务 10.1 验证序六步；基线 = merge gate 42 冻结树）

- 判据唯一 = `scripts/pyc_verify.py`；compare 基线 = `rounds/round10/baseline42/`（= merge gate 42 `e42b8509` 认证件，round9 已转换，逐位同源）
- 驱动 = 本目录 `verify_driver.py` / `verify7_split.py` / `final_verify_run.py` / `iv2_recheck.py`（round9 同款复制 + BOM 口径修正 + 插桩检查升级为 tokenize 区分字符串/代码行）
- 执行：regen 先行（402 个 `*OK.py` 全量以 HEAD 代码覆盖重生成）→ 逐片 batch → compare；全程 **614.3s**（`final_verify_summary.json`）；单链串行

## 一、验证序六步实录（全绿）

### ① 34 小测试集（无回退）
- A 515/515 + B 1053/1053 = **1568/1568（100%）、34/34 success**；compare（vs v2 基线）：`1505/1568 -> 1568/1568`、files 1→34、**REGRESSIONS=0 IMPROVED=33**。

### ② 402 全量八分片（regen → batch → compare）
| 分片 | 文件 | 单元 | compare |
|---|---|---|---|
| shard0..6 | 51×7 | 786/469/538/887/855/999/801 | REGRESSIONS=0 ×7 |
| shard7 | 45 | 1282/1282（拆半 608+674） | REGRESSIONS=0 |
| **合计** | **402/402** | **6617/6617（100%）** | **REGRESSIONS=0 ×8** |

- **402 产物零字节差异**：regen 后 `site-packages/**` git 零 M 态（修复批对认证语料零字节影响，与 compare 逐位双证）。

### ③ quotation 单验
- `status=success units=153/153 success_rate=100.00%`（rc=0）；零新增失败。

### ④ tests 七套件（零新增失败）
- `2 failed / 282 passed / 2 xpassed`；失败名单与基线逐位一致：`test_B01_simple_if_then_else_merge`、`test_BOUNDARY_02_large_function`。

### ⑤ IV.2 门禁自检（`final_verify_summary.json.iv2` + `r10v10_fv_iv2.json`）
| 项 | 结果 |
|---|---|
| IMPORT_OK | ✓（八 core 模块） |
| COMPILE_OK | ✓（region_analyzer / region_ast_generator：compile() + py_compile 过；**BOM `efbbbf` 双单头** = round8/9 既有约定，本轮编制器以单头完整校验确认） |
| repro 全 match | 引用 round9 实测（r9v9fix3b_* 17 件、承重面等）；冻结树复检不重登 |
| G0 六项 | docstring：三方法 978/1360/1391 字符模板齐；无 self 新状态 0；无白名单路径 0；无 start_offset 阈值 0；ast.parse + py_compile ✓ |
| 插桩 | **代码行 0 命中**；唯一 2 行 `[T]` 命中（20631/21366）经 tokenize 判定 ∈ 字符串（docstring 形态记号），非插桩 |
| G3 | **0** 新增前缀方法 |
| G4 | **0** 硬编码深度/计数上限（新增行全扫） |
| 影响面 | compare REGRESSIONS=0 ×8 + 402 产物零字节差异 + 34 集 IMPROVED=33 |

### ⑥ 读数汇报
本文件即汇报。**终态读数（冻结树）：单元级 6617/6617（100%）、文件级 402/402；tests 2 failed（基线名单）/282 passed/2 xpassed；quotation 153/153；34 集 1568/1568。** 形式层完备占比与三态终表由 10.2（wiki §8.2 六步）统一落账后汇报。

## 二、运行勘误记录（透明存档）

1. **10.1 首跑 HERE 误写事故**：套件复制件（`a8bc0abc`）中 `final_verify_run.py` 残留 round9 硬编码 HERE → 首次启动实际执行 round9 套件并回写 round9 目录。运行 ~5 分钟后发现，立即终止（cmd 304 / python 4152 及子进程全灭）；round9 4 个 M 态文件（log + shard0-2 报告）经 `git checkout` 复原、零未跟踪残留；未完成写出的 round10 无产出。修正提交 `ea34ae03`（HERE → round10，docstring 同步）后重跑。
2. `tools/kb/syntax_coverage.py --help` 误触实跑一次：输出与提交态逐字节一致（JSON 零 diff），零影响。
3. 重跑读数与 9.4 逐位一致（6617/6617、1568/1568、153/153、2/282/2）——冻结树确定性复现。

## 三、证据索引（rounds/round10/）
- `final_verify_log.txt`（六步逐段实录）、`final_verify_summary.json`（机器可读汇总）
- `shard0..7_report_new.json` 8 件、`_shard7_a.json`/`_shard7_b.json`、`regen_shard0..7.json`（全空 = 0 失败）
- `small34_report_a/b/new.json`、`r10v10_fv_iv2.json`、`iv2_recheck.py`
- `baseline42/`、驱动四件、`WIKI_BRIEF.md`（10.2 派发简报，此件同时为 10.2 输入）

## 四、结论
**验证序六步全过：零回归、零新增失败、认证语料零字节差异。** 放行 10.2（wiki §8.2 复审六步全量重验与增量更新，评审工程师执行）→ 10.3 终归档 + push + 终态读数汇报。
