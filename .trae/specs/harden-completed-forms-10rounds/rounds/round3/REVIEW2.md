# Round 3 复核（对抗性复审：B10 / B11 / B1b 两批修复）

- 复核人：评审工程师（Round 3 复核，独立于两批修复工程师，零容忍口径）
- 日期：2026-10-02
- 对象：commit `5f26202c`（批次一 B10 收尾 5 单元，FIX.md）+ `95046711`（批次二 B11×4 + B1b×2，FIX2.md）。HEAD=95046711，工作树已跟踪文件零改动（实测），两批 diff 即现树代码。
- 唯一判据：`scripts/pyc_verify.py`。登记复验一律 `--source` 法（现树代码 × 树中现存 OK 产物；未再生成任何 `*OK.py`）。
- 硬约束遵守：未修改 `core/`、`scripts/`、`site-packages/` 与任何 `*OK.py`；未 git commit；自构变体探针（`test_repros/round3/_rv3_a/b/c`）运行后已全部清理，只留读数进本报告。

---

## §1 读数复验（--source 法，14 探针 72 单元）

命令模式：`python scripts/pyc_verify.py single <x>.pyc --source <x>OK.py`（pyc/OK 均为 `test_repros/round3/` 树中现存文件）。

### 原 21 个 MISMATCH 单元逐项核对（REVIEW.md §2 清单）

| 文件 | 复核读数 | 原评审读数 | 21 单元核对 |
|---|---|---|---|
| r3_20_for_else_break_exit | **success 4/4** | 1/4 | inner_break_out ✓ / else_break_with_flag ✓ / while_else_break_exit ✓ |
| r3_22_loop_else_return_continue | **success 5/5** | 3/5 | for_else_continue_outer ✓ / while_else_continue_outer ✓ |
| r3_24_double_loop_break | **success 5/5** | 1/5 | double_loop_inner_break ✓ / double_loop_outer_break ✓ / double_loop_both_else ✓ / double_break_with_continue ✓ |
| r3_25_triple_for_else | **success 4/4** | 1/4 | triple_for_else ✓ / triple_for_mixed_break ✓ / for_for_while_else ✓ |
| r3_26_while_for_mixed | **success 4/4** | 2/4 | while_for_mixed ✓ / while_for_continue_cross ✓ |
| r3_27_loop_try_with_match | **success 9/9** | 8/9 | loop_try_with_break ✓ |
| r3_28_while_mixed_chain | **success 5/5** | 1/5 | while_and_or ✓ / while_or_and ✓ / while_chain3 ✓ / for_body_while_mixed ✓ |
| r3_31_else_mixed_if | **success 5/5** | 3/5 | else_mixed_if ✓ / elif_chain_in_else ✓ |

**21/21 全部转 MATCH。**

### 已 MATCH 单元与负对照保持

| 文件 | 复核读数 | 原读数 | 判定 |
|---|---|---|---|
| r3_21_for_else_empty | 5/5 | 5/5 | 保持 ✓ |
| r3_23_if_break_continue_guard | 5/5 | 5/5 | 保持 ✓ |
| r3_30_for_unpack_async | 5/5 | 5/5 | 保持 ✓ |
| r3_32_comp_loop_interleave | 11/11 | 11/11 | 保持 ✓ |
| **n3_01_simple_loops（负对照）** | 5/5 | 5/5 | 保持 ✓ |
| **n3_02_guard_and_else（负对照）** | 5/5 | 5/5 | 保持 ✓ |

合计 **72/72 单元全 MATCH**（单元级 100%）。**读数复验：通过。**

---

## §2 算法合规审计（两批 diff 全量，逐 hunk；锚点 = 现树行号实测）

### 批次一 5f26202c

| # | 审计项（锚点） | 判据性质核查 | 结论 |
|---|---|---|---|
| 1 | FIX-A 真 else 豁免 `region_analyzer.py:4823-4861` | `lr.has_break` + eb 全部正常前驱 ∈ lr.body/header/else + 异常边豁免——同层块结构事实；三要素注释齐（:4823-4846） | 通过 |
| 2 | FIX-1 前驱扫描 `:5536-5570`（docstring :5343-5361） | 前驱集合 + 末条 opcode∈{JUMP_FORWARD, JUMP_ABSOLUTE}；异常边/JUMP_BACKWARD/非跳转前驱显式排除；无阈值无白名单 | 通过 |
| 3 | FIX-3 元组收窄 `:5514-5521` | JUMP_BACKWARD 桩不再判伪；「break_targets 分支前置 return 挡住普通 continue 桩」论证链完整 | 通过 |
| 4 | FIX-2a R102 落点放行 `region_ast_generator.py:5358-5401` | 判据 = 归零 ∧ ∉else_blocks ∧ **∈ `_post_break_blocks`**。该台账为**既有**（父提交 `5f26202c^` :289 声明、:22615-22616 登记，实测确证），本轮仅接消费者——非新增 self 状态、非隐式白名单 | 通过 |
| 5 | FIX-2b R58 落点放行 `:5477-5532` | `_r3b10_child_emits` 臂集合守卫（body/else/then/try/handler/finally 成员即不放行）+ 与 FIX-2a 同收窄判据 | 通过 |
| 6 | FIX-4 双 Break 守卫 `:22845-22855` | 语句表尾类型检查（`bs[-1]=='Break'` 不再补发）——消除死代码双 Break，非吞语句 | 通过 |
| 7 | FIX-5 else 桩→Continue `:5135-5179` | 纯单条 JUMP_BACKWARD 桩 + 后继 ∈ 祖先链 header 集合——同层结构事实 | 通过 |
| 8 | FIX-6 子区域抑制 `:15870-15895` | 父链最近 LoopRegion + `child.entry ∈ break_blocks`——同层生成派发判据（与既有 R58/R102 break_blocks 消费同类） | 通过 |
| 9 | **G0 保护 BOM 剥离 `region_ast_generator.py:1`** | diff hunk `-﻿"""`→`+"""`：父提交首字节 `EF BB BF` → 现树无 BOM（实测字节）；**FIX.md（批次一）全篇未声明此变更** | **打回（R2-1）** |

### 批次二 95046711

| # | 审计项（锚点） | 判据性质核查 | 结论 |
|---|---|---|---|
| 1 | FIX-B11a 跨类调用 `region_ast_generator.py:6603/:8276` | `self._is_equivalent_exit_block` → `self.region_analyzer._is_equivalent_exit_block`——消除被 `except Exception` 吞掉的 AttributeError（原先整 While 降级消失） | 通过 |
| 2 | FIX-B11b 所有权校验 `region_analyzer.py:24191-24220` | ② 结构判据 `region.header_block in 认领者.blocks`（:24216-24218，与既有 parent_body 清理判据 :4771-4779 同类的同层归属仲裁，非绕过归约的跨层消费）；**① parent 链祖先豁免（:24203-24209）注释与代码不一致** | **打回（R2-2，限①）** |
| 3 | FIX-B11c-1 链首守卫豁免 `:24590-24631` | 未认领 + IF_FALSE 前向收尾 + 假目标出体语义集合——B6 边界闭合的镜像，结构性 | 通过 |
| 4 | FIX-B11c-3 or 前缀续接 `:24677-24787` | 链首 fall-through==header + or 成员 PJT∈{cond}∪链块 + and-run 逐块推进；结构性、注释三要素齐（守卫边界实测见 §3） | 通过 |
| 5 | FIX-B11c-2 or 尾多成员 `:24880-24912` | 统一假出口 + 真边 fall-through + 残链 BoolOpRegion 认领放行（其余一票否决）；结构性 | 通过 |
| 6 | FIX-B11d 残链超越泛化 `:24164-24240` | 相交 ∧ entry∈链块 ∧ op_chain 严格更短；原 [B6] 否决权保留（:24227-24229）；被超越残链块释放后回归完整链发射，无吞语句 | 通过 |
| 7 | FIX-B11e loop-else 认领豁免 `:27848-27864` | `ft_succ ∈ else_blocks ∧ ∉ body_blocks ∧ ≠ header` + 链首守卫（≠循环 header/condition_block）；**放行后实测落入标准验收路径（:27899-27933：多成员 run 交 `_detect_boolop_conditional_chain` / 单成员 or 尾交 [B1b] 三判据）**——只放行合法形态、走标准验收，LoopRegion 认领面零扩大 | 通过 |

### 通用反模式核查（两批全量）

- 函数名/文件名白名单：**零**；start_offset 魔法阈值：**零**（guard<16 为防环护栏，非阈值判据）。
- 新增 self 跨方法状态：**零**（`_post_break_blocks`/`generated_blocks`/`_generated_regions` 均为既有台账，diff 内无新 `self._x` 声明）。
- 以少发射换全绿（吞语句）：**未发现**——FIX-2a/2b/FIX-5 为补发射，FIX-4 仅消重死 Break，FIX-B11d 撤销残链后按完整链重建发射。

### R2-1 / R2-2 打回详情

- **R2-1（批次一，BOM 剥离未声明）**：`region_ast_generator.py:1`。违反条款：`wiki/concepts/decompile-invariant-completeness.md` §9.3（「region_ast_generator.py 带 G0 保护 BOM……工具读取一律 `utf-8-sig`」）+ `rules.md` §6.2 条款2（「COMPILE_OK……BOM `efbbbf` 保持」）+ spec「评审工程师对树中一切代码独立攻击」。机制：该 BOM 是「裸 utf-8 读导致 compile SyntaxError」的 G0 tripwire，剥离后保护面被静默拆除，且未在 FIX.md 留痕（FIX2.md §6 反将 BOM 当污染剥离，口径相悖）。处置：恢复 BOM，或在 wiki/rules 明文修订该保护条款（二选一，必须留痕，禁止无声明漂移）。
- **R2-2（批次二，注释/代码不一致）**：`region_analyzer.py:24200-24202`（注释）vs `:24203-24209`（代码）。注释与 FIX.md §3-B11b 均宣称豁免判据为「认领者是 region.parent 链上的 **LoopRegion**（祖先循环），不跨越非循环区域边界」，但代码沿 parent 链上溯、认领者匹配**任意类型祖先**即豁免——无 `isinstance(…, LoopRegion)` 校验、不在非循环区域边界停止上溯。违反条款：spec「注释与代码不一致 = 评审不通过」+「判据只允许同层块对象的结构事实」（豁免面宽于声明 = 守卫不封闭；如链首块被祖先 IfRegion 认领时亦被放行越权）。r3_28 验收单元的认领者恰为 LoopRegion，故读数不受影响，但零容忍口径下守卫面与声明不符即打回。处置：补 `isinstance` 收窄至声明口径，或如实改写注释/FIX.md 为实际行为并论证任意祖先豁免的封闭性。

---

## §3 封闭声明核实与变体探针（3 探针实测，已清理）

| 探针 | 覆盖形态 | 读数 | 判定 |
|---|---|---|---|
| _rv3_a | ① or 前缀**三成员** `while (a or b or c) and k < m:`；② or 尾三成员 and 组 `while a and k < m or b and d and e:`；③ 交错四操作数 `while a and b or k < m and c:` | ① or_prefix3 **MISMATCH**（Different control flow）；② ortail3 MATCH；③ cross_four MATCH | B11 残留（B11-R） |
| _rv3_b | loop-else 内**三重 elif 混合布尔链**（`if a and b or c:` / `elif d and e or f:` / `elif g or h and i:`） | **2/2 MATCH** | B1b 扩充封闭 ✓ |
| _rv3_c | ① **四层** for-else 各层含 break+else；② 内层 for-else 体含纯 `if i == 5: break` 跳外层 | ① quad_for_else MATCH；② outer_break_rise **MISMATCH** | B10 残留（B10-R） |

### 逐破口核实

- **B10（R3-A 识别层 + R3-B 生成层）**：验收组 15/15 MATCH（§1）+ 四层深嵌套变体 MATCH（深度无感在已证形态成立）。但 `outer_break_rise`（r3_20.else_break_with_flag 深化形）实测 **`break` → 幻影 `return acc`**（外层 for-else `'done'` 保留但 break 语义丢失）——与 B10 R3-B 登记签名同族（break→return 折叠面，锚点 `region_ast_generator.py:4530/:5242/:7056`）。**判定：验收组封闭成立，族封闭性未证**；登记残留 **B10-R**（验收组续接，不新增编号）。
- **B11（四形态）**：比较操作数 / or 组前置（二成员）/ 三操作数链 / 嵌套循环内混合链全部 MATCH（§1），外加 or 尾三成员 and 组、交错四操作数两个变体 MATCH。但 `or_prefix3` 证明 **or 组前置封闭仅对二成员 or 组成立**：三成员 or 组整组被提出 while 条件（产物形如 `if a or b or c:` 包裹 `while k < m:` + 幻影 `continue`）。机制：FIX-B11c-3 的 and-run 要求自 or 成员 fall-through 起逐块 IF_FALSE 推进至链首（`region_analyzer.py:24740-24758`），而 or 成员之间的 fall-through 仍是 IF_TRUE 成员 → run 断裂；且 :24787 返回前仅 prepend 单个 or 成员。**判定：四登记形态封闭成立；「or 组前置」覆盖声明降格为二成员**；登记残留 **B11-R**。
- **B1b 扩充（loop-else 上下文）**：r3_31 5/5 + 深链 elif 变体 2/2 = **封闭成立**；:27848 豁免只放行 else_blocks 成员且走标准验收（实读确证），无越权放行。
- **B6/B7 封闭声明降格表述**：FIX2.md §3 已如实落实（B6 降格为「`A and B or C` 单名操作数浅层封闭」+ 扩展覆盖列举；B7「深层才错」签名修正）——**落实属实**。但因 B11-R 残留，B11 在台账应记「已落地（登记面全 MATCH）+ 残留子面 B11-R」，**不得记「破口封闭」**。

---

## §4 总结论

1. **读数复验：通过**——14/14 文件 72/72 单元全 MATCH；REVIEW.md §2 全部 21 个 MISMATCH 单元转 MATCH；负对照与已 MATCH 单元零回退。
2. **合规审计：16 项通过，打回 2 项**——R2-1（BOM 剥离未声明，批次一）、R2-2（FIX-B11b 注释/代码不一致，批次二）；锚点、违反条款、机制见 §2。
3. **封闭声明核实：B1b 扩充通过；B6/B7 降格表述落实属实；B10/B11 = 验收组封闭、族封闭性未证**——登记残留 B10-R（内层 for-else 体纯 if-break 跳外层 → 幻影 return，折叠面 :4530/:5242/:7056）与 B11-R（or 前缀三成员组条件提出 + 幻影 continue，FIX-B11c-3 边界 :24677-24787）。两残留均在原登记破口族签名内，验收组扩入，下一 fix 批按封闭守卫口径修复，禁止个案补丁。
4. **总判定：打回**（零容忍口径）——读数全绿属实，但 R2-1/R2-2 须处置留痕、B10-R/B11-R 须进台账后方可归档放行。本轮单元级成果（21/21 转 MATCH、零回退）予以确认；「B10/B11 封闭」表述按 §3 降格执行。

---

## §5 打回处理记录（批次三修复工程师，2026-10-02）

### R2-1 — BOM 已恢复 ✓

- 字节级操作：读 `region_ast_generator.py` bytes，确认首 3 字节无 `EF BB BF` 后前置写回（实测现 `efbbbf 22 22 22`）；`py_compile.compile(doraise=True)` COMPILE_OK。
- 无副作用复验：`r3_20_for_else_break_exit` 4/4、`fly/data/quotation` 152/153，均持平。
- 注记：本批两次 Edit 亦曾意外剥离该 BOM（含 `region_analyzer.py`），均以字节级剥离/前置回滚并以首字节 hex 断言收尾；最终态 generator 带 G0 BOM、analyzer 无 BOM（与父提交一致）。

### R2-2 — 守卫面已收窄对齐声明 ✓

- 锚点：`region_analyzer.py:24200-24217`（FIX-B11b 祖先豁免①）。代码对齐注释语义：沿 parent 链上溯，命中认领者时 `isinstance(_b6_anc, LoopRegion)` 方可豁免；上溯途中遇非循环区域（IfRegion/TryExceptRegion/BoolOpRegion 等结构化边界）即停止上溯、不豁免（维持一票否决）。
- 判据性质：纯同层结构事实（祖先区域类型 + 上溯边界），无白名单/阈值/跨层信息；注释三要素同步（豁免面与既有结构判据② `header_block ∈ 认领者.blocks` 同族——链首块双重角色仅由 LoopRegion 体首收集产生）。
- 复验：round3 全组 14 文件 72/72、quotation 152/153、jq_trans_module 65/65、r2_09 2/3、r2_10 2/4、r2_17 2/3 全持平。

### B11-R — 已封闭（or 组多成员前缀反向收集）

- 复现：`test_repros/round3/r3_33_b11r_or3prefix.pyc`（or_prefix3 = `while (a or b or c) and k < m:`，另含 ortail3 / cross_four 两守卫单元）。修复前 or_prefix3 MISMATCH（3/4），症状与评审 §3 一致（or 组整组提出条件 + 幻影 continue）。
- 机制（字节码实证）：CPython 对 or 组非末成员以正向 IF_TRUE 族短路真出口汇聚同一 PJT（a/b/c 前两成员 `POP_JUMP_IF_TRUE→22`）、末成员以 IF_FALSE 假边出体（c `POP_JUMP_FORWARD_IF_FALSE→110`，真值经 fall-through 传 PJT）；原 FIX-B11c-3 仅 prepend 单个 or 成员，三成员时命中中间成员 b 后 and-run 收 c，产出 `or[b,c]+and` 残链，a 被提出条件外。
- 修复锚点：`region_analyzer.py:24761-24853`（FIX-B11c-3 内）。判据（同层结构事实）：沿 fall-through 前驱反向收集——p0 的 fall-through 后继恰为当前成员、p0 块尾正向 IF_TRUE 族、跳转目标与命中成员同一 PJT（or 组真出口汇聚同点的结构签名）、归属未认领或仅 BoolOpRegion；前驱不满足即停（二成员形态自然收空，行为与修复前一致）。链头并入 `[(m,'or'),…]` 交 `_create_boolop_grouping` 同一归约路径，生成端 `_detect_boolop_grouping` INNER 信号重建 `and[or[A,B,C], k<m]`。docstring 三要素齐（:24761-24781）；guard<16 为防环护栏。
- 读数：**r3_33 4/4 MATCH**（or_prefix3 正确重建 `while (a or b or c) and k < m:`）；r3_28 5/5、r3_31 5/5、round3 全组 72/72 零回退；round1 rv_03/rv_05/rv_09 维持 1/2（B7 登记未修项不受影响）。

### B10-R — 精确登记（已定位、部分防御、未封闭；状态=已定位待下轮）

- 复现：`test_repros/round3/r3_34_b10r_innerforelse_break.pyc`（outer_break_rise：内层 for-else 体纯 `if i == 5: break` 跳外层，外层 else `'done'`）现 1/2 MISMATCH，产物 `if i == 5: return acc` 幻影 return，与评审 §3 `_rv3_c` 签名一致。
- **机制修正（对 §3 登记锚点的实证勘误）**：插桩实证幻影 return **不经**折叠面（`_generate_return_ast` 全程零调用），实际路径 = `_process_if_blocks:22547 → _generate_region:3276 → _generate_if:12356 → _if_generate_normal:18370`——IfRegion（`if i == 5`）then 臂末块（POP_TOP+JUMP_FORWARD break 桩）跳转目标块 200 为 RETURN 块且未认领，`_generate_block_statements` 漏斗日志 `BLKSTMT off=200 ret=True` 证实其语句被臂内联为 Return；块 200 同时是外层 for-else 尾（`'done'` 后 fall-through）与函数尾共享的 RETURN 块（原 pyc 中 break 边 `JUMP_FORWARD→200` 应保留为 Break 语义）。登记锚点 :4530/:5242/:7056（break→return 折叠面）为同族但不同路径。
- 防御性扩展（本轮已落，复验零回退）：折叠面接入祖先循环正常退出路径守卫 `_ancestor_loop_exit_reaches_block`（`region_ast_generator.py:4573-4602`，沿 parent 链对每个 LoopRegion 取与 `_loop_exit_reaches_block` 同判定面：正常退出边 = header/condition 体外后继 ∪ else_blocks，只体外前向遍历；docstring 三要素齐）+ 两折叠点接入（:5275-5276 / :7091-7092）——命中即不折叠、保留 Break 发射（C1 局部消费/C2 黑箱组合）。该守卫封堵折叠面上的同族残留，但不覆盖上述 if 臂内联路径。
- 未封闭原因：`_if_generate_normal` 为全部 IfRegion 生成共用主路径，需新增「分支臂跳转目标为祖先循环正常退出路径上的共享 RETURN 块时发射 Break 而非内联 Return」判据（判据形态：目标块角色 RETURN/RETURN_NONE + `_ancestor_loop_exit_reaches_block` 命中 + 臂末块为 POP_TOP+JUMP break 桩形态），并全量回归 quotation/quote/tlb 等大面——超出本轮合理范围，按指令不强行。
- 最小验收组（下轮）：r3_34 outer_break_rise（目标 2/2）+ r3_20 4/4 + r3_22 5/5 + r3_25 4/4 + r3_27 9/9 + n3_01/n3_02 各 5/5 + quotation 152/153 + quote 84/92 + tlb 118/128。

### 本批自测读数全表（现树代码 × 现存产物，single 法）

| 组 | 文件 | 读数 | 判定 |
|---|---|---|---|
| round3 全组 | n3_01 / n3_02 / r3_20 / r3_21 / r3_22 / r3_23 / r3_24 / r3_25 / r3_26 / r3_27 / r3_28 / r3_30 / r3_31 / r3_32 | 5,5,4,5,5,5,5,4,4,9,5,5,5,11（全 success）= 72/72 | 零回退 ✓ |
| B11-R | r3_33_b11r_or3prefix | **4/4** | 新封闭 ✓ |
| B10-R | r3_34_b10r_innerforelse_break | 1/2 | 已登记（待下轮） |
| 基线 | quotation 152/153、jq_trans_module 65/65、quote 84/92、trade_live_broker 118/128、risk_calculation 29/29 | 全持平 | ✓ |
| round2 抽验 | r2_09 2/3、r2_10 2/4、r2_17 2/3、r2_06 2/3、r2_14 3/4 | 与登记一致 | ✓ |
| round1 抽验 | rv_03 / rv_05 / rv_09 各 1/2 | 与登记一致 | ✓ |

- 纪律：命令 ≤300s；`*OK.py` 全部由 `pycdc.py` 再生成（r3_33/r3_34 新产物含内）；调试插桩两处已按行号还原并 grep `_tb3p|_r3b10_probe` 零残留；未 git commit；未触碰 `.trae/specs/` 既有内容（本节为授权追加）。

---

## §6 复验终判（Round 3 评审工程师对抗性复核，2026-10-02）

对象 = 未提交工作树变更（批次三打回处理：`core/cfg/region_analyzer.py` +74 行、`core/cfg/region_ast_generator.py` +37 行、`test_repros/round3/r3_33*/r3_34*` 新探针、本文件 §5）。HEAD 仍 = 95046711。逐项复验，结论「通过 / 打回」。

### R2-1（BOM 恢复）— **通过**

- 字节实测：`region_ast_generator.py` 首 4 字节 = `efbbbf22`（G0 保护 BOM 恢复）；`region_analyzer.py` 首 4 字节 = `2222220d`（无 BOM，与父提交形态一致）。diff 首行 hunk 确证仅为 BOM 前置写回，无内容漂移。§5 R2-1 记录与实测一致。

### R2-2（守卫面收窄）— **通过**

- 逐行审查 `region_analyzer.py:24203-24213`（diff hunk @24198-24217）：`_b6_anc_hit = False` 初始化；上溯中命中认领者时 `_b6_anc_hit = isinstance(_b6_anc, LoopRegion)` 方可豁免；**途中遇非 LoopRegion（IfRegion/TryExceptRegion/BoolOpRegion 等结构化边界）即 `break` 停止上溯**。代码行为 = 注释声明 = FIX2.md §3-B11b 三处一致（本批同时修正了原注释，`git diff` 实证）。
- 判据性质：区域类型 isinstance + 上溯边界停止——同层结构事实，无白名单/阈值/跨层信息。
- 抽验读数（--source 法）：r3_28 **5/5**、r3_31 **5/5**，未回退。

### B11-R（or 组多成员前缀封闭）— **通过（登记面封闭；族封闭性以 B11-R2 边界登记为前提，禁止宣称全族封闭）**

- r3_33_b11r_or3prefix 复跑：**4/4 MATCH**；OK 产物实证 `or_prefix3` 正确重建 `while (a or b or c) and k < m:`。
- FIX-B11c-3 新扩展逐 hunk 审查（`region_analyzer.py:24761-24853`）：or-run 反向收集判据 = 沿 fall-through 前驱、块尾正向 IF_TRUE 族、**PJT 与命中成员同一 argval**（or 真出口汇聚同点结构签名）、双后继、fall-through 后继 `is` 当前成员、归属未认领或仅 BoolOpRegion、排除链内/循环体块、guard<16 防环——全部同层结构事实；链头并入 `[(m,'or'),…]` 交同一 `_create_boolop_region_from_chain` 归约路径，不新增认领。docstring 三要素（识别条件/归约方式/AST 映射）+ [C1]/[C2]/[C3] 同步齐全（:24761-24781）。
- **变体攻击（临时 `_rv3_d.py` 编译实测，已清理只留读数）**：指名变体 **or_prefix4（四成员 or 组前置 `while (a or b or c or d) and k < m:`）= MATCH** ✓。额外构造 `or4_and2`（四成员 or 组 × **双 and 尾** `and k < m and b`）= **MISMATCH**：产物 or 组整组提出条件 + 幻影 `if a or b or c or d:` 包裹 `while k < m and b:`——与 B11-R 修复前症状同族的**组合边界残留**（or 组多成员 × and 组多成员衔接；or-run→and-run 推进要求抵达链首块，该拓扑下断裂）。判定：B11-R 登记形态（or 组多成员 + 单 and 尾）封闭成立；新边界登记 **B11-R2**（锚点 `region_analyzer.py:24761-24853` or-run/and-run 衔接面，复现形态 `while (a or b or c or d) and k < m and b:`），状态 = 已定位待下轮，验收组续接。**§5「B11-R 已封闭」表述按此降格执行**。

### B10-R（登记核对）— **通过**

- §5 B10-R 四要素核对：① 机制勘误在案（幻影 return 实证经 `_if_generate_normal:18370` if 臂内联共享 RETURN 块 200，非折叠面——`_generate_return_ast` 零调用证据链完整，原锚点 :4530/:5242/:7056 修正为同族不同路径）；② 折叠面新守卫 `_ancestor_loop_exit_reaches_block`（`region_ast_generator.py:4573-4602`）逐行审查 = 沿 parent 链对每个 LoopRegion 复用既有 `_loop_exit_reaches_block` 同判定面（正常退出边 = header/condition 体外后继 ∪ else_blocks，只体外前向遍历），docstring 三要素 + C1/C2 齐，for/while 两折叠点接入（:5275/:7091），判据同层结构事实；③ 内联面转下轮 + 判据形态预告（RETURN 角色 + 祖先守卫命中 + POP_TOP+JUMP 桩）在案；④ 最小验收组明确（r3_34 2/2 目标 + 5 文件回归 + 3 基线）。
- r3_34_b10r_innerforelse_break 复跑：**1/2 MISMATCH**（outer_break_rise 失败，Different control flow）——与 §5 登记「已定位待下轮」一致，无谎报。
- 新守卫方法名 `_ancestor_loop_exit_reaches_block` 与折叠面既有 `_loop_exit_reaches_block` 同族命名，无 self 新状态（纯查询方法）。

### 终态汇总

| 项 | 终判 |
|---|---|
| R2-1 BOM 恢复 | 通过 |
| R2-2 守卫面收窄 | 通过 |
| B11-R 登记（or 组多成员前缀） | 通过（r3_33 4/4 + 判据合规 + or_prefix4 MATCH）；**附 B11-R2 边界登记**（or×and 组合残留），§5「已封闭」降格为「登记形态封闭」 |
| B10-R 登记（内联共享 RETURN 面） | 通过（如实登记待下轮，r3_34 1/2 与登记一致） |

**Round 3 终态**：原 §4 打回的 R2-1/R2-2 已处置到位；B11-R 登记面封闭（附 B11-R2 新边界）；B10-R 精确登记待下轮。round3 全组 72/72 + r3_33 4/4 零回退属实。**放行 Round 3 归档**（B11-R2/B10-R 两残留作为 Round 4 输入，验收组与最小验收组已明确）。本节为对 §1-§5 原判的复验终判，§1-§4 原文保留不改。
