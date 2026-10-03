# Round 9 评审报告（评审工程师 · 防回归对抗批次 / REVIEW.md）

- 评审人：评审工程师（Round 9 任务 9.1 攻击批次）
- 日期：2026-10-04
- 树状态：HEAD = `d59556e2`（round9 启动快照）；合规基线 = `201234ab`（round8 归档）。**`git diff 201234ab -- core/ parsers/ scripts/ pycdc.py` = 空**（本轮工作树唯一差异 = `.trae/.../rounds/round9/verify_driver.py` + tasks.md Task 9 勾选，core 零触碰）
- 唯一判据：`scripts/pyc_verify.py`（single/batch，pylingual compare_pyc，Python 3.11.7）；全部命令 ≤300 s
- 红线遵守：零改码；零手改既有 OK.py（quotationOK 重生成验证走临时文件后即删，见 §1 注记）；探针产物（源码 + py_compile 3.11 pyc + `pycdc.py -o` 生成的 OK.py）全部落 `test_repros/round9/`
- 归因手段：`git worktree` 于 `201234ab` 独立工作树（`D:/Temp/r9_pre`）实测失败单元，用后已移除

## 终判：**零回归成立；新登记候选破口 B66/B67/B68（5 单元）交修复工程师**

前八轮全部复验面逐位持平（round6 115/115、round7 104/128、round8 107/118、残留登记面 98/137、round1/3/4/5 抽样 168/169 逐文件零漂移）；守卫族双向攻击（外推 + 收缩）10 探针 43 单元 38 MATCH，5 个 MISMATCH 单元经 201234ab worktree **产物逐字节同败**证实为既有缺口的结构变体新暴露，非在途引入；负对照 n9_01 3/3 + n9_02 4/4 全 MATCH。

---

## §1 合规审计（任务 9.1 第 5 项）

| # | 项 | 判据 | 实测 | 判定 |
|---|---|---|---|---|
| A1 | 在途变更 | `git diff 201234ab -- core/ parsers/ scripts/ pycdc.py` | 空（无任何 diff 输出） | **通过** |
| A2 | BOM | `head -c 3 \| xxd` 关键文件 vs `201234ab` 基线 | region_ast_generator.py = `efbb bf`；region_analyzer.py / cfg_builder.py / comprehension_generator.py / pycdc.py / pyc_verify.py 与基线逐字节一致（原文件本无 BOM） | **通过** |
| A3 | 插桩 | grep `_R23N20_DEBUG\|R23N21_DEBUG\|_patch_dbg\|_probe_r` + R7/8/9DBG 族 core/ | 0 / 0 | **通过** |
| A4 | 既有 OK.py 零手改 | 重生成对照（quotationOK.py 临时名重生成） | 重生成产物与归档版**正文不一致**——归档版 `quotationOK.py` 为旧战役遗留产物（git log 末次实质修改 = 旧战役 commit `739d342f`，本规范 1–8 轮未再生，其与 fresh regen 的差异属归档陈旧性，非本轮变更）；基线口径（`site-packages/fly/data/quotation.pyc` + fresh regen + single）= **152/153**，唯一失败 `change_his_to_forward` = Round 8 VERIFICATION 逐字一致 | **通过**（临时产物已删，未触碰归档 OK.py） |

**哨兵注记（诚实记录）**：仓库根的平面副本 pyc `_Downloads_..._quotation.cpython-311.pyc`（sha d2808754…）与基线路径 `site-packages/fly/data/quotation.pyc`（sha 1a51fbb5…）**字节不同**（疑为再序列化副本）；以其 fresh regen 做 single 得 153/153，**非** 402 基线口径（shard7 引用原路径）。402 基线口径按原路径实测 152/153 持平。建议后续轮统一以 shard json 路径为哨兵口径。

## §2 前八轮封闭破口复验（任务 9.1 第 2/3 项，防回归重点）

### 2.1 round6/7/8 全量重放（命令与任务书逐字一致，报告 = `rounds/round9/r9_regress.json`）

| 面 | 基准 | 本轮实测 | 逐位对照 | 判定 |
|---|---|---|---|---|
| round6 全量（r6_01..15 + n6_01，16 文件） | 115/115 | **115/115**（r6 107/107 + n6 8/8） | 16/16 文件全 success | ✓ 零回归 |
| round7 全量（r7_01..14 + n7_01/02，16 文件） | 104/128 | **104/128**（r7 94/118 + n7 10/10） | 24 失败单元名单 = r7_01(1)/r7_03(2)/r7_04(1)/r7_05(1)/r7_06(3)/r7_07(3)/r7_08(4)/r7_10(1)/r7_11(1)/r7_12(3)/r7_14(4)，与 B42×3/B43/B44/B46–B51 登记面逐一对应 | ✓ 零回归 |
| round8 全量（r8_01..11 + n8_01/02，13 文件） | 107/118 | **107/118**（r8 98/109 + n8 9/9） | 11 失败单元 = r8_assert_nested_func / r8_aug_chain_rhs / r8_dh_for_else_del / r8_dh_with_assert / r8_dh_match_multi / r8_x_assert_ternary / r8_x_augassign_ternary / r8_x_for_iter_ternary / r8_x_raise_ternary_class / r8_x_ret_nested_ternary / r8_dh2_match_guard，与 round8 REVIEW.md §5（B56×2/B57/B58/B59/B60/B61/B62/B48×2/B46×1）逐一对应 | ✓ 零回归 |
| **合计** | 326/361 | **326/361** | 45 文件 status 与 unit 数逐位一致 | ✓ |

### 2.2 Round 8 残留登记面持平（任务书 20 pyc 名单，报告 = `r9_residual.json`）

| 面 | 基准 | 实测 | 对照 |
|---|---|---|---|
| 17 文件 r7/rv6/rv7 残留面 | 81/117（round8 r8_residual.json） | **81/117** | 17/17 文件 units 与提交 json **零差异**（r7_01 8/9 … rv7_04 2/3 逐位） |
| rv8 变体面 | 17/20（round8 REVIEW2 §4） | **17/20**（rv8_01 6/7、rv8_02 5/7、rv8_03 6/6） | 失败单元 = chain_value_boolop / tryfin_then_more / with_body_tryfin_chain（B65/B63/B64），逐位持平 |
| **合计** | 98/137 | **98/137** | ✓ 零漂移 |

### 2.3 round1/3/4/5 封闭面抽样重放（各 ≥3 文件，偏向 B2/B3 交叠探针；报告 = `r9_prev_rounds.json`）

| 轮 | 抽样（基准读数出处） | 实测 | 判定 |
|---|---|---|---|
| round1 | r1_09_continue_break_guard 2/2（FIX.md §4.1，B1b×B2 交叠）、r1_01_stmt_andor3 2/2、r1_10_while_mixed 2/2（B6）、n1_01 2/2、n1_02 2/2 | **10/10 全 MATCH** | ✓ |
| round3 | r3_20 4/4、r3_23_if_break_continue_guard 5/5（B2 交叠）、r3_24 5/5、r3_27 9/9（FIX.md §5.1）、r3_28 5/5、r3_31 5/5（FIX2.md §5.1）、n3_01 5/5、n3_02 5/5 | **43/43 全 MATCH** | ✓ |
| round4 | r4_01_match_value 6/6、r4_09_match_guard 7/7、r4_14_match_case_body 7/7（FIX.md 批次二）、rv4_14 4/4、rv4_15 4/4、r4_or4_and2 **1/2（B11-R2 登记残留）** | **29/30**；r4_or4_and2 保持 1/2，失败签名 `or4_and2: Different control flow` 与 round4 REVIEW2 §「一致」读数逐字同 | ✓ 不变差 |
| round5 | r5_01 13/13、r5_04 13/13、r5_08 14/14、r5_11 19/19、r5_13 18/18、rv5_20 9/9（FIX.md/REVIEW2.md） | **86/86 全 MATCH** | ✓ |
| **合计** | 169 单元 | **168/169，零漂移** | ✓ |

## §3 B2/B3/B4 守卫族回归攻击（任务 9.1 第 1/4 项）

判据面定位（现行行号）：B2 = `_block_is_continue_target`（region_ast_generator.py:12243-12252）+ `_loop_else_set` 排除与纯 continue 分支守卫（:12377-12410）；B3 = W14-C（region_analyzer.py:21095/21104/29844/29866）+ fix3-T1/T2（region_ast_generator.py:14898）+ fix3-T6（:20569）+ W23（:21161）+ R71-thenover（:24739/24744）；B4 = 孤儿块释放（region_ast_generator.py:1636-1696，[R74 fix1 abs2] 覆盖集豁免）。

### 3.1 攻击读数表（10 探针 43 单元：外推 9 + 收缩 1；负对照 2 探针 7 单元）

| 探针 | 攻击面 | 单元 | 读数 | 判定 |
|---|---|---|---|---|
| r9_01_b2_cont_loopelse | B2 × loop-else 外推：for/while-else 宿主内 continue 守卫、continue 后尾随体、否定守卫极性 | 5 | **5/5** | 守卫成立 |
| r9_02_b2_dual_continue | B2 互斥组合：两臂同 continue、break/continue 混排、嵌套循环 continue 目标归属、while 双出口 | 5 | **5/5** | 守卫成立 |
| r9_03_b3_shared_tail | B3 W14-C 外推：臂内嵌套 if 汇合 + 双语句共享尾；try 内共享尾（fix3-T1/T2）+ try 后共享尾；while 变体 | 4 | **4/4** | 守卫成立 |
| r9_04_b3_thenover_w23 | B3 R71-thenover/W23：if/elif 链 merge 共享尾归属、深嵌套 elif + 尾语句、while 帧 elif-else | 4 | **4/4** | 守卫成立 |
| r9_05_b4_orphan_release | B4 孤儿释放边界：loop 内 elif merge 外落、三层 if-else 级联、while 帧 elif 孤儿 | 4 | **4/4** | 守卫成立 |
| r9_06_b2_with_try_cross | 守卫面新构造：B2 × with/try 交叉宿主 + BoolOp × continue | 4 | **2/4** | **2 MISMATCH（B66/B67 候选）**；cont_in_try MATCH |
| r9_07_b3_gen_yield | 循环守卫 × 生成器：yield 体 continue 守卫、yield 共享尾、while+yield continue | 4 | **4/4** | 守卫成立 |
| r9_08_b54_augassign_mix | B54 × augassign 混合 × B2：链式赋值与增量赋值循环体交叠、continue/break 横跨 | 4 | **4/4** | B54 封闭面变体成立 |
| r9_09_b55_boundary | B55-c 窄门控边界外：空 try/finally 尾随 break/continue/BoolOp 守卫 return | 4 | **1/4** | **3 MISMATCH（B68 候选）**；tryfin_shared_guard 形态外单元 MATCH |
| r9_10_b2b3_shrink | 收缩一格：continue 即体末语句（无尾随体）、嵌套 if 无共享尾、纯嵌套 if-else | 5 | **5/5** | 守卫不误触发 |
| **攻击面合计** | 10 探针 | **43** | **38/43（88.4%）** | 5 MISMATCH 全归因既有缺口（§4） |
| n9_01_simple_guard | 负对照：最小 if-continue / if-break | 3 | **3/3** | ✓ MATCH |
| n9_02_plain_forms | 负对照：基础 if-else / for / while | 4 | **4/4** | ✓ MATCH |

汇总 batch 报告 = `rounds/round9/r9_all.json`（50 单元 45 MATCH，10 文件 success / 2 failure）。

## §4 新破口登记（候选，全部经 201234ab worktree 证实逐字节同败 = 既有缺口变体，非本轮引入）

### B66（候选）— B2 continue 守卫 × with 宿主交叉失效：continue 蒸发 + 幻影 `while False`（P2）
- **最小复现**：`r9_06 cont_in_with`：`for x in xs: / with open(p) as f: / if a(f): continue / use(f, x)` → 产物 `if a(f): while False: pass / else: use(f, x)`（continue 蒸发为幻影 `while False: pass`，use 落入 else 臂）。
- **机制**：continue 目标块位于 with 宿主内时，`_block_is_continue_target`（region_ast_generator.py:12243）判据链（JUMP_BACKWARD 目标=loop header / BlockRole.CONTINUE）未命中 with 装配后的角色形态，continue 边被 `_generate_with` 装配面按普通条件分支重建。
- **归因**：pre-fix（201234ab）产物**逐字节相同**，同签名 "Different control flow" 同败。
- **同面正例**：`r9_06 cont_in_try`（try 宿主内 continue）MATCH——失效面限于 with 宿主。

### B67（候选）— BoolOp 混合链 × continue 守卫：链拆裂 + 多余 continue（P2，B1b/B11/B2 交叠变体）
- **最小复现**：`r9_06 cont_with_boolop`：`if a(x) and b(x) or c(x): continue / keep(x)` → 产物 `if a(x): pass / if b(x) or c(x): continue / keep(x) / continue`（and 组被提升拆裂为独立 `if a: pass`，语义改变：a 为假时 b/c 不再求值即落 keep；尾部多出一条 continue）。
- **机制**：`A and B or C` 混合链在 continue 守卫上下文（回边目标块参与装配）时 `_detect_boolop_conditional_chain` 不接管，回落单条件拆裂；continue 块被重复登记发射。
- **归因**：pre-fix 产物逐字节相同。

### B68（候选）— 空 try/finally × 循环控制流尾随装配竞争族（P2，B63/B64 窄门控边界扩展）
- **最小复现**（3 单元，`r9_09`）：
  1. `tryfin_trailing_break`：`for x in xs: try: pass / finally: pass / if a(x): break / return 1` → 产物 `for x in xs: if a(x): break`（**try/finally 整体蒸发 + 尾随 return 1 蒸发**）。
  2. `tryfin_trailing_cont`：`while xs: try: pass / finally: pass / if a(1): continue / xs.pop() / return 2` → 产物 `try: while xs: … / finally: pass`（**try/finally 与 while 嵌套倒置**并吞并循环体 + return 2 蒸发）——B64（with 宿主倒置）的 while 宿主变体。
  3. `tryfin_shared_guard`：`try: pass / finally: pass / if a and b: return 3 / return 4` → 产物 `try: pass / finally: pass / return 4`（**尾随 if+BoolOp 守卫+return 3 整段蒸发**）——B63（非纯常量尾随段蒸发）的 BoolOp 守卫头变体。
- **机制**：尾随块携带循环控制流角色（break/continue）或 if/BoolOp 守卫头时，`_generate_try` 收尾装配与循环/IfRegion 归约竞争归属；B55-c 窄门控（`_b55_is_pure_const_return_block`，round8 :28525）按设计拒绝后该面无守卫接管。
- **归因**：3 单元 pre-fix 产物**逐字节相同**，同败。

**登记纪律说明**：5 个候选单元均不在 Round 8 交接单认领面（B54 4 单元 / B55 2 单元）内；零回归成立（本轮 45+168+326+98 复验单元无一由 MATCH 转 MISMATCH，5 个 MISMATCH 全部为新构造形态首暴露且 pre-fix 逐字节同败）。

## §5 交接单（交修复工程师，任务 9.2）

| 优先 | 项 | 单元 | 提示 |
|---|---|---|---|
| 1 | **B68**（空 try/finally × 循环控制流尾随族） | r9_09 ×3 | 与 B63/B64 同根（收尾装配竞争）；判据建议 = 同层结构事实（尾随块角色/前驱集合/区域归属），勿给个案打补丁 |
| 2 | **B66**（B2 × with 宿主） | r9_06 cont_in_with | continue 目标判定在 with 装配后的角色形态；B2 判据外推一格 |
| 3 | **B67**（BoolOp 混合链 × continue） | r9_06 cont_with_boolop | B1b/B11 族 continue 守卫上下文变体 + 多余 continue（B2 trade_operation 签名） |
| 沿袭 | Round 8 残留：B42×3/B43/B44/B46/B48×2/B56–B62 + Round 7 残留 81/117 名单 | §2.1/§2.2 失败单元名单 | 本轮全部逐位持平，交下批按原交接单认领 |

自测哨兵建议（任务 9.2）：§2 全部复验面禁变差 + r9 攻击面 38/43 禁变差（5 MISMATCH 修复后应转 MATCH 且负对照保持）+ 六哨兵 + option_account + quotation（基线路径口径 152/153）。

## 附：本轮过程产物清单

- 探针：`test_repros/round9/r9_01..r9_10_*.py|.pyc|*OK.py`、`n9_01_simple_guard`、`n9_02_plain_forms`（12 文件组，OK 产物全部 `pycdc.py -o` 生成，零手改）
- 报告 json：`.trae/specs/harden-completed-forms-10rounds/rounds/round9/{r9_regress,r9_residual,r9_prev_rounds,r9_all}.json`
- 归因 worktree：`D:/Temp/r9_pre` @ 201234ab，实测后已移除（`git worktree list` 无残留）
- 临时产物：quotation 重生成临时文件已删；根目录误建 `rounds/` 已清理归位至 `.trae/.../rounds/round9/`
- 零修改：core/、parsers/、scripts/、pycdc.py、既有 REVIEW/FIX/VERIFICATION、既有 OK.py
