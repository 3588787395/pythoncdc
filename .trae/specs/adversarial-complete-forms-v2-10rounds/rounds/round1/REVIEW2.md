# REVIEW2.md — Round 1.3 评审工程师复核报告（修复批次 A/B 对抗审计）

规范：`adversarial-complete-forms-v2-10rounds`（tasks.md 1.3，零容忍打回）
复核对象：批次 A `a411d9d5`（core/cfg/region_analyzer.py）+ 批次 B `33d6e87e`（region_ast_generator.py / ast_generator_v2.py / structured_analyzer.py）
方法学：**RV2 方法学**——`pyc_verify.py` 只比对磁盘 OK.py 产物，故全部复跑先以 HEAD 代码重生成 OK.py（`rv2_regen_verify.py`）再验证；归因用 `git archive` 提取 a411d9d5 与 a411d9d5^（基线）两提交运行时文件做干净重放。

---

## §0 终判：**放行**（附读数修正 + B77–B82 新登记）

批次 A/B 修复**真实有效且零回归**（71 文件重放 REGRESSED=0，变体面净改善 8 单元），判据全部落在 I.4 白名单，合规复验四项全过。但 **FIX_A 自述 r7_08「8/8 三轮复现」不可复现**：干净重生成下 a411d9d5 与 HEAD 均为 **7/8**（失败单元 `t_host_match_case`，基线即 FAIL，系未封闭存量缺口 → 登记 B77）。该单元非 B50 修复目标且批次 A 对 r7_08 真实改善（基线 6/8→7/8），不构成打回条件；读数虚报记入 §2 表并按零容忍原则明示。FIX_B 自述读数与复跑**逐位一致**。

## §1 逐 hunk 审查表（对照 I.1–I.7）

**批次 A**（region_analyzer.py，425 行 diff）：

| hunk | 内容 | 条款 | 判定 |
|---|---|---|---|
| A1 | analyze() 尾部接入 `_b50_fix_try_hosted_ternary_normal_copies` | I.4 | PASS |
| A2 | `_b50_fix_try_hosted_ternary_normal_copies` + `_b50_finally_copy_iso_seqs` 定义 | I.7 六项模板 + [C1][C2][C3]；判据=入口块同一性/区域父子/块集成员/剥噪 opname 同构/finally_copy_blocks 键集 | I.4 PASS |
| A3 | `_b74_guard_arm_targets_case_body` 定义 | I.7 六项模板；判据=opname/跳转目标偏移/体块成员关系 | I.4 PASS |
| A4–A6 | 三处 match 装配调用点统一后校验 | 不命中⇒原行为逐字节不变（C3 守卫封闭） | PASS |
| A7–A10 | DBG_OR ×9 / FIXA-DBG ×3 / trace 开关删除 | 纯删除 hunks | PASS |
| A11–A13 | B46-tail 三处（连接块解引用/while_cond 改写守卫/空值块豁免） | 判据=块末 opcode ∈ RETURN_VALUE/RETURN_CONST + 后继目标∈值位 | I.4 PASS |

**批次 B**（region_ast_generator.py +682 等）：

| hunk | 内容 | 条款 | 判定 |
|---|---|---|---|
| B1 | `_B71_FRAME_BRIDGE_OPS` frozenset | opname 集合（I.4 允许 opname 判据） | PASS |
| B2–B4 | [B71] for-else 误判守卫 / finally 正常副本 elif 剥离 / 共享入口 try 域例外 | 后继前驱集合 + TRY_FINALLY 域成员关系；offset 比较为 try_offset_end 结构派生非魔数 | I.4 PASS |
| B5–B6 | [B75] `_b75_consume_arm_return_copies`（六项模板）+ 两认领点 | `_hard_reserved` 拆分后判据仍为块集成员+序列同构；瞬态键挂 region 对象（单次 generate 生命周期），**非 self 跨方法状态** | I.4 PASS |
| B7, B9 | [B71] finalbody 出口归属守卫 / finally 异常副本 break 终结识别 | 块成员关系 + 前驱集合 | PASS |
| B8 | [B73] `_is_finally_copy_return` 接入 BFS | 剥头剥尾 opname 序列同构（I.4 白名单） | PASS |
| B10 | [B76] 封闭发射守卫（`_generated_regions` + return results + 补发射还原） | C3 守卫封闭 | PASS |
| B11 | [B65] R61 形状泛化（[COPY,STORE] 对 → n 目标） | 指令 opname/oparg 判据 | PASS |
| B12 | ast_generator_v2 魔数 62 段 / `==74` no-op 删除 | 纯删除 | PASS |
| B13 | structured_analyzer `depth>3` → 单后继线性链判据（visited 防环） | 结构判据替代硬编码上限 | PASS |

FIX_A.md §1/§2/§3/§6 与 diff 逐字相符；FIX_B.md §0–§6 与 diff 逐字相符。**唯一不符项 = FIX_A §7 读数表 r7_08「8/8」**（见 §2）。

## §2 读数独立复跑表（rv2 前缀落盘，全部先 HEAD 重生成再验证）

**修复目标 8 面**：

| 面 | 自述 | RV2 复跑 | 判定 |
|---|---|---|---|
| r7_08（B50） | 8/8 | **7/8**（t_host_match_case: Different control flow） | **不符**→存量缺口 B77 |
| r7_07（B46 尾项） | 7/7 | 7/7 | 符 |
| r10_06（B74） | 3/3 | 3/3 | 符 |
| r10_21（B71） | 4/4 | 4/4 | 符 |
| r10_04（B73） | 3/3 | 3/3 | 符 |
| r10_15（B75） | 6/6 | 6/6 | 符 |
| rv10_32（B76） | 8/8 | 8/8 | 符 |
| b6576_probe（B65） | 4/4 | 4/4 | 符 |

**归因链（r7_08）**：基线 a411d9d5^ 干净重放 = **6/8**（t_host_try_sections + t_host_match_case 双 FAIL）→ a411d9d5 = **7/8**（B50 封闭 t_host_try_sections，真实 +1）→ HEAD = 7/8（批次 B 零影响）。`t_host_match_case` 三点全 FAIL → 存量 → B77。

**负对照 14 文件**：自述全 MATCH = 复跑 **66/66** 全 MATCH（逐位一致）。
**站桩五行**（rv2_sentry_regen.json，24 文件先重生成）：round6 **115/115** 持平；哨兵 site-packages **302/308** 持平（trade_info_utils 36/41 `query_strategy_id` + quotation 152/153 `change_his_to_forward`，与基线同单元）。
**34 小测试集**（rv2_small34.json）：**1505/1568**，failure=33 与基线名单一致，REGRESSED=0。
**71 文件重放对比**（rv2_compare.py，rv2_replay_r78/r910 vs r1_residual_replay）：**REGRESSED=0，IMPROVED=8**（r10_04 2/3→3/3、r10_06 2/3→3/3、r10_15 5/6→6/6、r10_21 2/4→4/4、rv10_32 7/8→8/8、r7_07 6/7→7/7、r7_08 4/8→7/8、rv8_01 6/7→7/7〔未自述增益〕）。
**位 B 降级归因复核**：rv9_01/rv9_02 HEAD 重放各 **4/5**，失败单元 `emptyfin_in_if` / `while_with_whole_body` 与 Round 1.1 基线（r1_residual_replay.json :737/:751）逐位相同 → **存量归因成立**（较 stash 法更直接：直接对基线重放 JSON 逐位对比）。

口径注记：Round 1.1 基线重放中 r7_08 记 4/8 系磁盘陈旧 OK.py 读数；干净基线重生成实为 6/8。回归判据不受影响（4/8→7/8 仍为改善）。

## §3 变体攻击表（probes_rv2/ 8 文件 24 单元，HEAD vs 基线 a411d9d5^ 双重放）

| 面 | 外推变体 | 负对照 | HEAD | 基线 | 判定 |
|---|---|---|---|---|---|
| B50 | v_two_except_fin（双 except+finally） | n_plain_assign_fin、n_ternary_nofin | **4/4** | 2/4 | 封闭真实（+2），外推过 |
| B46 | v_while_cond_nest、v_if_cond_nest（条件位融合） | n_for_body_nest（for 体融合） | 1/4 | 1/4 | 三单元基线同态 FAIL → **存量 B78** |
| B71 | v_fin_else_continue（else 臂）、v_nest_fin_continue（嵌套双层） | n_fin_noctrl | **3/4** | 1/4 | 封闭真实（+2）；嵌套 finally×continue 存量 → **B79** |
| B73 | v_imp_cond_fin（finally 条件段×else 臂） | n_imp_nofin | 2/3 | 2/3 | 同单元同态 → **存量 B80** |
| B74 | v_case_if_last、v_case_if_mid（体首 if 末/中 case） | n_true_guard（真 guard） | 3/4 | 3/4 | 外推过；真 guard `case 1 if flag:` 基线同态 → **存量 B81** |
| B75 | v_swap_arm_returns（两臂 return 互换） | n_fin_noseg（finally 无条件段） | 1/3 | 1/3 | 同单元同态（Different bytecode / control flow）→ **存量 B82** |
| B76 | v_cmp_chain（BoolOp×Compare）、v_or3_chain（三链 or） | n_mul_and | **4/4** | 1/4 | 封闭真实（+3），外推全过 |
| B65 | v_chain3_boolop（3 目标链式） | n_single_target | **3/3** | 2/3 | 泛化判据真实覆盖 3 目标（+1） |

**变体总结**：净改善 8 单元、零「基线 MATCH→HEAD FAIL」回归；5 面外推变体通过，B46/B73/B75 三面外推与负对照暴露的 6 个 MISMATCH 均为基线同态存量。

## §4 合规复验

| 项 | 证据 | 判定 |
|---|---|---|
| BOM 单头 | region_analyzer.py / region_ast_generator.py 头 4 字节 = `efbbbf 22`（恰一 BOM，无双头） | PASS |
| 插桩删净 | `grep 'DBG_OR\|FIXA-DBG\|FIXB-DBG\|R10DBG\|_R23N20_DEBUG\|临时调试'` in core/ = **0 命中** | PASS |
| 魔数/硬编码清理 | ast_generator_v2 临时调试段与 `==74` grep=0；structured_analyzer `depth>3` grep=0 | PASS |
| OK.py 抽验重生成 | handlers.pyc、fly/logger.pyc 以 HEAD 重生成，SHA256 与磁盘 34 集产物一致（9AE24F68D60C / 1C85C580ECFD）→ 1505/1568 读数确系 HEAD 产物 | PASS |
| 只读纪律 | `git status --porcelain -- core/` = 0 行；在途变更仅 rounds/round1/ 内 rv2 产物 | PASS |

## §5 新登记 B77–B82（全部基线同态证实为存量，非修复引入）

| 编号 | 形态 | 证据 |
|---|---|---|
| **B77** | match case 臂内 `return "x" if flag else "y"`（r7_08 单元 t_host_match_case） | 基线/a411d9d5/HEAD 三点 7/8 同单元 FAIL |
| **B78** | B46 族残留：while/if **条件位**融合三元 + for 体 append 位融合三元 | v_b46_face 三单元双点同态 |
| **B79** | 嵌套 finally×continue 双层 | v_nest_fin_continue 双点同态 |
| **B80** | finally 条件段（`if fh: closer(fh)`）× else 臂 import × handler return | v_imp_cond_fin 双点同态 |
| **B81** | 真 guard `case 1 if flag:`（与 B74 幻影 guard 修复无冲突，系真 guard 装配缺口） | n_true_guard 双点同态 |
| **B82** | B75 残留：两臂 return 互换（Different bytecode）+ finally 无条件段×except 臂 return | v_b75_face 双点同态 |

## §6 残留交接

1. **FIX_A 读数修正**：r7_08 = 7/8（非 8/8）；「三轮复现」未在干净重生成口径下成立——Round 1.4 修复位须以 regen+verify 复测后更新台账，B77 转入下一轮修复目标。
2. 存量观察项（FIX_A §8）：生成端 finally 副本预_pass 条件 ⑤ len 相等假配对弱判据（region_ast_generator.py:26894-26924），B77 或与之相关。
3. 站桩挂账：trade_info_utils `query_strategy_id`（36/41）、quotation `change_his_to_forward`（152/153）——基线已知，本轮持平。
4. 34 集 33 文件失败名单与基线一致；rv9_01/rv9_02 4/5 存量确认（B68/B66 族挂账不变）。
5. 下一轮优先级建议：B77/B78（match 臂三元 + 条件位融合）收益面最大；变体探针 probes_rv2/ 八文件可直接作回归基准。

**产物**：rv2_targets/neg/rv9/sentry/small34/replay_r78/replay_r910/variants *.json + rv2_regen_verify.py + rv2_compare.py + probes_rv2/（8 py + 8 pyc + 8 OK.py）
