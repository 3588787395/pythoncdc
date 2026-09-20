# Round 16 — 修复记录（R16-A：if 臂表达式子区域预生成抢占结构兄弟入口块）

## 一、目标与根因（实测，非推测）

受害真源：`site-packages/IQCommon/arg_checker.pyc`
`<module>.ArgumentChecker._is_valid_quarter`，严格尺子 orig=90 / decomp=74，
丢失的 16 条指令恰为 `try` 外壳 + `except` 处理块（orig 偏移 240–288：
`PUSH_EXC_INFO` … `RERAISE 1`）；`if` / 守卫 / `else` 臂全在。

根因链在**生成层**，Round 15 §四 移交的「分析层未建父子」猜想被 `D:/Temp/r16_arm/out/tree.txt`
**否证**：`TryExceptRegion@94.parent == IfRegion@86`，父子关系本来就已建好。

1. `_if_generate_then_branch` 的两个「表达式子区域预生成」循环
   （`region.children` 循环：锚点 `:14052`、块标记 `:14070-14071`；
   `if not _expr_child_stmts:` 回退循环遍历 `self.regions`：锚点 `:14213`、标记 `:14228-14229`）
   把 `BoolOpRegion@94` / `TernaryRegion@94` 的 `blocks` **整批**写入 `generated_blocks`；
2. 这批块与 `TryExceptRegion@94.try_blocks` 完全重叠（表达式子区域与 try 共享入口块 94）；
3. `_process_if_blocks` 的 `_try_entry_generate`（`:20153-20167`，守卫 `:20154-20155`）
   见入口块已在 `generated_blocks` 即空转；
4. ⇒ `try/except` 整块无人发射。

免疫路径（差分证据）：else 臂收集器 `_try_collect_c3` **先**收结构子区域
（`:14663-14675`）**后**收表达式子区域（`:14677+`）⇒ 不受影响，复现差分 `r16a_09`（MATCH）。

## 二、方案与区域归约算法的对应

新增「结构兄弟优先」约束，而不是新增跨层次启发式：

- 类常量 `_STMT_LEVEL_STRUCTURAL_REGION_TYPES = (LoopRegion, TryExceptRegion, WithRegion, MatchRegion)`
  —— 语句级结构区域类型集合，沿用既有区域分类词汇。
- 新方法 `_expr_child_blocked_by_structural_sibling(expr_region, parent_region)`：
  同一父区域内存在**语句级**兄弟区域、其 `entry` 落在 `expr_region.blocks` 内 ⇒ True。
  谓词纯结构（同父 ∧ 语句级 ∧ entry ∈ blocks），不看地址差、不看节点数、不看指令模式。
- 两个预生成循环各加 3 行 `continue` 守卫：被结构兄弟占位的表达式子区域**不在预生成阶段认领**，
  交由 `_process_if_blocks` 的入口块生成路径按地址序正常发射 —— 直接落实
  「每个块只属于一个区域」「父区域引用子区域**入口**而非全部块」「自底向上归约」。

刻意不做的两件事（记录以免被当成遗漏）：

- **不把 `IfRegion` 纳入语句级集合**：实测变体 `S12c` 使
  `IQEngine/api/api_base.assure_asset` 112→117（净伤害）⇒ IfRegion 继续走既有嵌套路径；
- **不做 T1/T2「then 臂先结构后表达式」整体重排**：它改的是发射顺序而非抢占谓词，
  影响面未测 ⇒ 移交候选 16-B。

## 三、补丁与落地

- 补丁脚本：`D:/Temp/r16_arm/r16a_patch.py`（断言式字节级，4 hunks，**+53 / −0**）。
  前置断言：`BASE_SHA == d07996aaa20d4665`、每个锚点唯一、保留 UTF-8 BOM、纯 CRLF、
  `ast.parse` 通过、拒绝重复施加。
- hunk 位置：`@@ -180,0 +181,5`（类常量）、`@@ -13845,0 +13851,42`（新方法，
  含「识别条件 → 归约方式 → AST 映射 → 反例 → 代价」注释）、
  `@@ -14051,0 +14099,3`、`@@ -14212,0 +14263,3`（两处 `continue` 守卫）。
- 落地前副本：`D:/Temp/r16_arm/gen_R16.py`（sha `0fc591a8433e7032`，48122 → 48175 行）。
- 落地：`core/cfg/region_ast_generator.py` `d07996aaa20d4665 → 0fc591a8433e7032`，
  **与已验证副本逐字节相同**（sha256 全值一致），落地前副本备份
  `D:/Temp/r16_arm/backup_region_ast_generator_preR16.py`。

## 四、落地前验证（副本播种，仓库零写入）

| 项 | 裸核心 | R16 播种 |
|---|---|---|
| 目标 pyc 严格尺子 | 48/49 | **49/49** |
| 目标 pyc 官方尺子 | 46/47 | **47/47**（rate=1.0） |
| 404 pyc 语料缺陷函数行 | 258 | **257**（FIXED=1 BROKEN=0 CHANGED=0） |
| `round16_arm` 16 复现 | MISMATCH=10 | **MISMATCH=1** |
| `round15_arm` | MISMATCH=4 | **2** |
| `round14_join` / `round14` / `round13` | — | 逐条不变 |
| `quotation.pyc` 缺陷集合 | 3 函数 | 逐函数相同 |

## 五、门禁（mandate 顺序：单点 → quotation → 批量）

1. **单点**：`_r13_gate.py --targets rounds/round16/targets_1fix.txt --baseline D:/Temp/r15_strict_all.txt`
   → `[FLIPPED-CLEAN] IQCommon/arg_checker.pyc 48/49 -> 49/49`，`SUMMARY FLIPPED-CLEAN=1`，
   无回滚，elapsed=5s（`D:/Temp/r16_arm/gate_1fix.json`）。
2. **quotation.pyc 单验**：`148/150 -> 147/150`，`WORSENED(rolled back)` 并自动回滚产物。
   缺陷函数 `change_future_real_date` / `change_his_to_forward` / `get_trend`，与 Round 15 记录同集合；
   盘上产物 148/150 vs 重生成 147/150 的差 1 条属 SubTask 13.3 已登记的「产物/核心漂移」，
   **本轮补丁对该文件缺陷集合逐函数无影响** ⇒ 归因既有漂移，非本轮回退。
3. **全量批量回归**（406 targets，`rounds/round16/targets_all.txt`，2 个 budget 分片）：
   `CLEAN=330  UNCHANGED=64  WORSENED(rolled back)=9  REGRESSION(rolled back)=2  NO-OKPY=1`
   （Round 15 同工具：`329 / 65 / 9 / 2 / 1`）。
   异常文件集合与 R15、R14 **逐个相同（11 个，新增 0）** ⇒ 零新增回退。

## 六、双口径复验（各自同工具 pre/post，禁止跨工具相减）

| 口径 | 落地前 | 落地后 | 差 |
|---|---|---|---|
| 严格（`_r13_gate` 重生成产物，405 计分文件） | 函数 6079/6332，满clean 329 | 函数 **6080/6332**，满clean **330** | +1 / +1 |
| 官方（`scripts.pyc_batch_verify.bytecode_diff`，406 targets） | 355 ok / 50 partial，函数 5699/5838 | **356 ok / 49 partial**，函数 **5700/5838** | +1 ok / +1 函数 |

注：本轮官方口径由新脚本 `D:/Temp/r16_arm/official_all.py` 统一重算 pre/post（分母含未索引与无产物
文件，故与 Round 15 记录的 355 ok / 47 partial / 5619-5746 不同量纲，只取同一脚本自身的差值）。

## 七、复现电池与标注回填（落地后全部 `--strict` 退出码 0）

| 电池 | 落地后 | UNEXPECTED |
|---|---|---|
| `round16_arm`（本轮新增 16 复现） | MISMATCH=1 MATCH=15 | 0 |
| `round15_arm` | MISMATCH=2 MATCH=10 | 0 |
| `round14_join` | MISMATCH=1 MATCH=15 | 0 |
| `round14` | MISMATCH=0 MATCH=17 | 0 |
| `round13` | MISMATCH=14 MATCH=11 | 0 |
| `round16_sink`（并行诊断交付） | MISMATCH=8 MATCH=7 | 0 |

回填：`round16_arm` 9 项 → `SENTINEL`（补丁翻正），`r16a_05` 由误标 `MATCH` 纠正为 `MISMATCH`
（残留）；`round15_arm` 的 `r15a_01` / `r15a_02` → `SENTINEL`。
另：原测试工程师交付的 `EXPECT` 有 3 项误标（`r16a_05/06/12` 预测 MATCH 实为 MISMATCH），
已在回填脚本内纠正并留注释。

## 八、`pyc_index.json` 纠正

`IQCommon/arg_checker.pyc`：`partial / 0.9787 / mismatch_count=1 / matched=46` →
`ok / 1.0 / matched_functions=47`，`last_tested_round=10 → 16`，
note 改为 `index-corrected: R16-A flip verified both rulers (official 47/47, strict 49/49)`。
纯 CRLF 保持（4554 → 4553 行，`json.loads` 复验通过）。

## 九、并行诊断（不属本轮补丁）与残留

`round16_sink` 族（`PluginManager.set_engine` ×2）与 R16-A **正交**：同一批 15 复现在裸核心与
R16 播种下逐条一致（MISMATCH=8 / MATCH=7），症状是 `target_diff`（JUMP 终点漂移）而非语句丢失；
我方独立复测与其记录完全相同。其诊断线索是
`region_analyzer._build_elif_region` / `_check_elif_chain`（`:17831` / `:17948`）的 else 臂归并判据，
去除后 8 个 anchor 全部翻正、7 个负对照无误伤（该 agent 的交叉验证记录）。
诊断 agent 已达 150 轮上限（ANALYSIS.md 未产出），交付物（15 复现 + `run_all.py`）已入库。

残留（移交）：
1. `r16a_05` loop 入口重复发射（orig=31 / decomp=39，over-emit 族）；
2. `r15a_08` `guard_clause_prefix_end` 只为裸名条件写入、`r15a_09` body-sequence 重复发射（+9）；
3. R16-S sink 族（`IQData/manager/plugin_manager` 9/10、`IQEngine/core/plugin_manager` 8/9）；
4. T1/T2 then 臂收集顺序整体重排（影响面未测）；
5. SubTask 13.3 / 13.4、Task 5 遗留（`decrypt_database_url` +29、`cgroup` +2/+1、`replace_utils` 差 2）。
