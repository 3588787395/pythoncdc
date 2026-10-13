# Round 8 主代理无回退验证报告（任务 8.4 · 验证序六步）

- 主代理亲自执行（spec「主代理无回退验证」需求；判据唯一 = `scripts/pyc_verify.py`，RV2 口径 = 先 regen（pycdc -o）后 verify；所有 verify 子命令 ≤290s，分片执行）
- 验证对象 = HEAD 072dc1bf（Round 8 全部修复批次合入后：位A B121/B109残 → 位B B108/B111/B104/B105/B107/B99残/B98-R1/B77/B82/B83 + P0 回退修复① → 位C B81/B103/B102/B113+B110/B96/B106 + B112 部分移交 → 整改批 B104-R2a/R2b/B105-R2/B107-R2/B103-R2 → P0 回退修复② B106-R3）
- 驱动 = rounds/round8/verify_driver.py + verify7_split.py（round7 同款复制，HERE 相对路径）
- 基线 = `.trae/specs/adversarial-complete-forms-v2-10rounds/baseline/`（402 = 6554/6617、369/402；small_test_report 1505/1568；quotation 152/153；tests 基线名单 test_B01 + test_BOUNDARY_02）

## §0 验证经过（两遍）

### 第一遍（首跑，发现 1 回退 → P0 修复②闭环）
- 402 八分片：**7 片 REGRESSIONS=0 IMPROVED=0** 逐位基线一致；**shard4 REGRESSIONS=1**（finance.pyc 132/132→131/132，`PositionDict.__init__.<dictcomp>` Different bytecode——dictcomp 键链 `symbol.replace().replace()` 蒸发）
- small34 1505/1568 REGRESSIONS=0；quotation 152/153 基线；tests 277 passed / 2 failed（基线名单）/ 2 xpassed
- 按回退拦截条款打回修复工程师：根因定位（修复工程师二分勘误：B106 修复 865b901e `_find_dict_kv_split_point` LOAD_METHOD stale delta，非整改批；主代理 worktree 首测系 stale financeOK.py 误导，如实勘误）→ [B106-R3] 修复（comprehension_generator.py:1683-1697 单 hunk +14，I.4 白名单：LOAD_METHOD 净栈 +1 与 [R40 fix] CALL 口径配套）→ 定向验证全过（FIX_R3.md：最小复现 9/9、finance.pyc 132/132、放行面 74/74、变体电池全绿、round1face 417/423、34 集 shard0 NEWFAIL=0）
- 首跑证据（REGRESSIONS=1 原始记录）随 P0 修复批 072dc1bf 存档

### 第二遍（P0 修复②后终验，全绿）
全部六步重跑，读数如下（§1-§5）。第二遍产物 = 本目录 `shard*_report_new.json`（12 件 M 态为第二遍覆写）+ `small34_report_*` + regen_shard*（0 failed）。

## §1 402 全量八分片 batch + compare（REGRESSIONS=0）

| 分片 | units | files success | compare 判定 |
|------|-------|--------------|--------------|
| shard0 | 777/786 | 46 | REGRESSIONS=0 IMPROVED=0 |
| shard1 | 462/469 | 48 | REGRESSIONS=0 IMPROVED=0 |
| shard2 | 537/538 | 50 | REGRESSIONS=0 IMPROVED=0 |
| shard3 | 883/887 | 48 | REGRESSIONS=0 IMPROVED=0 |
| shard4 | **848/855** | 46 | **REGRESSIONS=0 IMPROVED=0**（首跑 847→P0 修复后 848 = 基线逐位恢复；finance.pyc 132/132） |
| shard5 | 993/999 | 46 | REGRESSIONS=0 IMPROVED=0 |
| shard6 | 789/801 | 48 | REGRESSIONS=0 IMPROVED=0 |
| shard7 | 1265/1282 | 37 | REGRESSIONS=0 IMPROVED=0 |
| **合计** | **6554/6617（99.05%）** | **369/402** | **八片 REGRESSIONS=0，与基线逐位一致** |

- 全量 regen 0 失败（regen_shard0-7.json：51/51×7 + 45/45，0 failed）
- 附注：P0 修复批 072dc1bf 随验证序入库 57 个 regen `*OK.py`（含 financeOK.py 修复后正确形态）；第二遍 regen 后这些文件零 M 态（P0 delta 仅影响 finance.pyc 输出，其余 56 件逐位一致）——57 件为工具再生的当前态产物，非手改。

## §2 34 小测试集 batch（无 success→failure 位移）

- **1505/1568，compare 对 baseline/small_test_report.json：REGRESSIONS=0 IMPROVED=0**（1 success 维持 + 33 failure 维持，全部为基线存量）
- 证据：small34_report_a/b/new.json（两半分片执行，单批 ≤300s 纪律）

## §3 quotation.pyc 单验（零新增失败）

- **152/153**（唯一失败 `change_his_to_forward` = 承接基线一致，round10 起存量）

## §4 tests 六套件（零新增失败）

- `pytest tests/test_algorithm_correctness.py tests/test_deep_nesting_pressure.py tests/test_control_flow_completeness_matrix.py tests/test_complete_syntax_coverage.py tests/test_boundary_cases.py tests/test_core_functional.py -q`
- **277 passed / 2 failed / 2 xpassed**——failed 名单 = `test_B01_simple_if_then_else_merge` + `test_BOUNDARY_02_large_function` = 承接基线名单，零新增失败

## §5 IV.2 门禁自检

| 项 | 结果 |
|----|------|
| IMPORT_OK | python -c import 全部涉改模块 OK（修复批/整改批/P0 批自检 + 验证序 402 次隐式 import） |
| COMPILE_OK | py_compile 全部涉改文件 rc=0；compile_error 0（402 面 files_by_status.compile_error=0） |
| BOM 单头 | region_analyzer.py / region_ast_generator.py 首 3 字节 efbbbf×1（单头）；pattern_parser / code_generator / comprehension_generator / ast_converter 无 BOM = 存量口径（REVIEW2/FIX_R3 勘误实录在案） |
| 插桩零残留 | grep R8CDBG / R8FIXBDBG / R8CDBGE core/ 零命中（位C收尾段 + 整改终审双确认） |
| G0（六项 docstring / 无 self 新状态 / 无跨层反查 / 无白名单 / 无 start_offset 阈值 / ast+py_compile） | REVIEW2 §1 逐 hunk 审查零打回（含 75 锚点核验）；整改批 G3 新增 def 7 全 `_b104r2_*` 合规 |
| G3（0 新增禁前缀方法） | 通过（各批报告声明 + 评审核验） |
| G4（0 硬编码上限） | 通过（`_steps<8` 三处 = [B75] 存量同型镜像，评审验真 + visited-set 建议登记移交） |
| 影响面 | 第二遍 402 全量逐位基线一致（§1）——零回归字节级证据 |

## §6 读数汇报（本轮成果汇总）

- **单元级成功率**：402 全量 6554/6617（99.05%）与基线逐位一致；34 集 1505/1568；quotation 152/153
- **本轮封闭破口**（登记→落地→复审状态机走完）：**B121**、**B109残**、**B104（含 R2a/R2b）**、**B105（含 R2）**、**B107（含 R2）**、**B99残**、**B77**、**B81**、**B103（含 R2）**、**B102**、**B113残（+B110 划除确认）**、**B96**、**B106（含 B106-R3 回退修复）**、**B108**、**B111**、**B83** = **16 族全链闭环**；部分封闭：B98-R1（matrix 7/15、hosts 13/18）、B82（2/3）
- **站桩回归终读数**：round1face 417/423、round2face 239/251（**+3** = B77/B82/B83 外溢）、probe42 177/196（**+1**）、residual 419/446（**+1**）、oldface 665/692（**+1**）、quotation 152/153——全部 ≥ 基线，WORSE=0
- **攻击面 31 探针**：位A/B/C 已封闭族全绿（B77 8/8、B81 4/4、B83 2/2、B99 9/9、B102 13/13+8/8+10/10、B103 13/13+8/8、B104 14/14、B105 13/13+12/12、B106 13/13+13/13+27/27、B107 14/14、B108 14/14、B111 28/28+22/22、B96 13/13、B113 9/9+14/14）；移交族维持（B78 1/4、B79 3/4、B80 2/3、B82 2/3、B98_matrix 7/15、B98_hosts 13/18、B98_resid 2/5、B112 21/24）
- **评审变体攻击**：评审批 r8v8rev_* 15 对 + 终审 r8v8rev3_* 7 对，域内新形态全数转 MATCH 或域外登记（B122/B123 候选移交 Round 9）
- **移交 Round 9 名单**（各批如实登记 + REVIEW2 §5 复核成立 8/8）：B78（判据事实在案：hop 块判别元/折叠常量合成）、B79（嵌套 try 分区混装）、B80（FIX_A §5 判据在案）、B82-v_swap（异常表区间外布局→识别层）、B98-R2/R3、B44（≥3 层双入口归纳）、B112 ①②（B31 await 链消费门 + 平铺重建，判据方向 FIX_C §6.1）、B122（字面量 case 臂嵌套 match 挂死，存量）、B123（IfExp 尾操作数钻石块集，存量改善）、G4 visited-set 建议、I.7 勘误 2 项（存量 docstring 未随扩）
- **完备台账影响**（Round 10 终审统一落账）：本轮封闭 16 族中 B77/B78-B46 族、B81/B103 guard 族、B102 except* 族、B96/B112 async 族、B106 star_args 族、B113 推导式族、B104/B105/B107/B99/B108/B111/B121/B109 各对应台账 §5 形态行——台账更新随 Round 10 wiki §8.2 六步统一执行（本报告提供全部依据锚点）

## §7 结论

验证序六步全过（第二遍终验全绿）：**402 八分片 REGRESSIONS=0 且与基线逐位一致、34 集零位移、quotation 零新增、tests 基线名单、IV.2 全项通过**。Round 8 达成轮门禁：≥1 破口封闭（16 族）+ ≥1 读数改善（站桩 4 面 +6）。允许归档（任务 8.5）。
