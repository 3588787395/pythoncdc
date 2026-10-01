# Round 1 评审工程师复核报告（REVIEW2，对抗复审）

- 复核对象：修复工程师一（B1b 核心，commit 1a0f2760，报告 FIX.md）、
  修复工程师二（B6 四上下文，commit 9725103d，报告 FIX_B6.md）。
- 复核日期：2026-10-01。判据唯一：`python scripts/pyc_verify.py single`（pylingual compare_pyc）。
- 理论权威：`wiki/concepts/decompile-invariant-completeness.md` §1（C1/C2/C3）、§3（十三条误解）、§6（破口登记）。
- 方法：工作树两提交已落位（working tree clean，无未评审在途变更）；新代码逐段读
  diff + 当前树；全部宣称读数用「pycdc 重反编译到系统临时目录 + --source 法」复跑；
  嵌套攻击构造 10 个新探针（rv_ 前缀，test_repros/round1/），并以
  `git archive 57f3e944`（两批修复前基线）到系统临时目录复跑基线产物，
  判定每个 MISMATCH 是「本批回退」还是「基线既有」。
- 本评审零写入 core/、scripts/、site-packages/；所有 *OK.py 判据产物均由 pycdc.py 生成。

---

## 0. 逐项结论表

| # | 复核项 | 结论 | 证据锚点 |
|---|---|---|---|
| 1 | 算法合规零容忍（两批全部新代码逐段审） | **通过**（附 2 条注记） | §1 |
| 2 | 嵌套无感抽攻（10 个 rv_ 探针，7 MATCH / 3 MISMATCH） | **通过**（零回退）＋ **新破口登记 B7**（打回证据，指向「封闭」宣称） | §2/§3 |
| 3 | 修复一宣称验收复验 | **通过**（抽 5/10 + 3 哨兵全达标） | §4.1 |
| 4 | 修复二宣称验收复验 | **通过**（4/4 全 MATCH + tlb 118/128） | §4.2 |
| 5 | docstring 三要素名实相符 | **通过**（附 3 条注记级瑕疵） | §5 |
| 6 | core/ 调试残留 | **通过** | §6 |

---

## 1. 清单1：算法合规零容忍 —— 通过

两批全部新增代码逐段审（fix1 region_analyzer.py +392 行；fix2 region_analyzer.py
+335 / region_ast_generator.py +112 / comprehension_generator.py +152）：

**白名单**：无。语料名（r1_09/trade_live_broker/is_future_tradetime_now 等）仅出现
于注释「实测」注记（`git show` + 过滤验证），不进任何判据表达式。

**start_offset 魔法阈值**：无绝对偏移数字判据。偏移仅用于：
块身份恒等（`ft_succ == _ft_reg.header_block`）、跳转目标解析
（`get_block_by_offset(argval)`）、目标偏移排序（comprehension 甄别窗
`inner_instr.offset < instr.argval`——跳转目标身份的序关系，非数值阈值）。

**跨层读取**：逐处核对，全部有显式守卫（C3）：
- fix1 B/B2/A 臂的 `ft_succ in self.block_to_region` + `LoopRegion.body_blocks`
  成员查表（region_analyzer.py:26597-26610、:27437-27460）：双重守卫 =（a）链首非该
  LoopRegion 的 header/condition_block（同层身份）∧（b）`_b1b_loop_body_run_continuation`
  三类降级续接判据（region_analyzer.py:27244-27370，判据全为块末 opcode 族 + 后继块身份）。
  非该循环 header/condition_block 的循环自身条件装配路径维持原 break，逐字节不变。
- fix1 D 臂（:26135-26175）：候选块 fall-through 块的指令 opcode 集 + 裸 JF 目标块末
  指令是否 RETURN_*，均同层结构事实。
- fix1 E 臂（:26320-26345）：`self.regions` 同层区域表的 `chained_compare_blocks`
  成员关系 + entry 身份恒等。
- fix2 Step5 所有权校验（:24017-24056）：链块持有者仅允许「未认领 / 本 LoopRegion
  （condition_block 惯例）/ 待超越残链 BoolOpRegion」三类，残链超越另要求
  entry∈chain[1:] 且 op_chain 更短；撤销动作（block_to_region 删除、regions/
  children 注销）是该所有权校验通过后的显式转移，非无守卫窥视。
- fix2 ternary 升级（:21834-21885）：`self.regions` 中 `BoolOpRegion.entry is block`
  身份配对，经 entry/merge 接口消费（跳转目标 `is merge_block`），不窥视链内部。
- fix2 assert 吸收（:15386-15450）：前驱过滤 `p in known or p in self.block_to_region`
  ——只吸收未认领前驱，认领块不进链。

**新增 self 跨方法状态**：零。`grep "self\._b1b_.*=\|self\._b6.*="` 零命中；
两个新方法 `_b1b_loop_body_run_continuation`/`_b6_assert_absorb_and_run` 均为
纯函数式（输入块/集合 → 输出链）。

**以少发射换全绿**：未发现。两批核心动作均为「把脱离链的操作数块显式认领接回
op_chain」（A 臂 append、assert 吸收 pre、while 前向续接 or 尾），消费端按完整链
or_groups 分组重建。fix2 `_loop_generate_while` 的 if-break 过滤三分将历史「全丢」
收窄为「仅 orelse 含真实语句时维持丢弃」，净发射面增大；无新丢弃入口。

**or_groups 分组算法同源性（对抗专项核对）**：fix2 新增的三处 or_groups
（region_ast_generator.py:3984-4042 assert、:35368+ ternary、
comprehension_generator.py:1594+ ）与既有 `_build_boolop_expression_inner`
（region_ast_generator.py:4026-4042）逐行同构，含「and→or 转换时把当前 IF_TRUE 块
并入 and 组收口」的关键语义；op 标注约定（'IF_FALSE'→'and'/'IF_TRUE'→'or'，
回向跳转取反）与 BoolOpRegion op_chain 一致。初读疑为「or 值被误并进 and 组」，
经 `if a and b or c:` 字节码逐边推演（b 的 POP_JUMP_IF_TRUE→then 即 (a∧b) 真出口）
确认为同一正确算法。

**注记 1**：`_b1b_loop_body_run_continuation` or-run 步界 `range(8)`（:27305）为
run 长度上限（带 visited 终止），非偏移阈值；与同文件既有 R3-K walk 的
`_r3k_steps < 8`（:26253）同源。放行。
**注记 2**：fix2 Step5 的「残链超越替换」是全两批唯一对共享归约状态
（block_to_region/regions/parent.children）的**删除型**改动；所有权三分类校验 +
entry 非首成员 + op_chain 更短 + 边界闭合（链首假边=第一个 or 尾成员）四重守卫齐备，
且 r1_10 与 n1/r1 组复测零回退。放行，但列为后续轮回归监控点（建议 sentinel：
rv_05 类深嵌套形态，见 §3）。

---

## 2. 清单2：嵌套无感抽攻 —— 7 MATCH / 3 MISMATCH（MISMATCH 均基线既有）

10 个新探针（test_repros/round1/rv_*.py + .pyc + OK.py，工作流
`py_compile → pycdc.py -o OK.py → pyc_verify single`）：

| 探针 | 攻击面（判据 × 嵌套） | 读数 | 基线（57f3e944）复跑 |
|---|---|---|---|
| rv_01_stmt_mixed_forinwhile | 修复一 A 臂：`if a and b or c:` 嵌 while>for>if 三层 | **success 2/2 100%** | — |
| rv_02_stmt_mixed_elif_deep | 修复一 A 臂+C 臂：混合链 elif 臂嵌 if>if 两层 | **success 2/2 100%** | — |
| rv_03_loopbody_forinwhile_break | 修复一 B 臂：`if a and b or c: break` 嵌 for>while>if | **failure 1/2**（Different control flow） | failure 1/2（产物逐字节同现树） |
| rv_04_loopbody_orrun_doublenest | 修复一 B 臂 or-run 类：`if b or c and a:` 嵌 for>for | **success 2/2 100%** | — |
| rv_05_while_mixed_in_for | 修复二 while：`while a and b or c:` 嵌 for 体，带 if-break | **failure 1/2**（Different control flow） | failure 1/2（形态更差：极性反转） |
| rv_06_while_mixed_in_class | 修复二 while：`while a and b or c:` 嵌类方法 | **success 3/3 100%** | — |
| rv_07_comp_mixed_in_class | 修复二 comp：listcomp 混合过滤器嵌类方法 | **success 4/4 100%** | — |
| rv_08_comp_mixed_set_dict | 修复二 comp：setcomp+dictcomp 混合过滤器嵌 while | **success 4/4 100%** | — |
| rv_09_ternary_mixed_in_while | 修复二 ternary：`1 if a and b or c else 2` 嵌 while 体 | **failure 1/2**（Different control flow） | failure 1/2（产物逐字节同现树） |
| rv_10_assert_mixed_in_for | 修复二 assert：`assert a and b or c, "rv10"` 嵌 for 体 | **success 2/2 100%** | — |

**统计：10 探针 = 7 MATCH / 3 MISMATCH；3 个 MISMATCH 经基线复跑确证均为
基线既有（非两批引入、无回退）**。

**MISMATCH 定性（深层≠浅层，嵌套无感不变式破坏证据）**：
- rv_05：浅层 r1_10（`while a and b or c:` 函数顶层）= 2/2 MATCH；同形态嵌进 for 体
  后 while 整体退化为 `if a and b or c:` + 幻影 `if a: continue`（源码无 continue）+
  循环结构丢失。基线更差（`if not (a and b):` 极性反转形）——fix2 改善了条件形态
  但未闭合深层。C 条款破坏点：Step5 所有权校验/残链超越与 `_detect_while_condition_
  boolop_chain` 双向续接在外层 Loop 包裹下不触发（浅层守卫的触发面依赖 condition_
  block 的 claim 形态）。
- rv_03：浅层 r1_09 族 = 2/2；`if a and b or c: break` 嵌 while（while 再嵌 for）
  体内退化为 `if a: if b or c: break`——链拆裂且语义不等价（(a∧b)∨c ≠ a∧(b∨c)，
  c 真 a 假即分歧）。B/B2 臂豁免在该深嵌套下未放行。
- rv_09：浅层 r1_11 = 2/2；混合链三元嵌 while 体后 `acc.append(...)` 语句整体丢失
  （被丢弃不接回）+ 链拆裂 `if a: 1 if b or c else 2`。ternary 升级判据
  （walk 止步于非末成员）未在此触发。

---

## 3. 新破口登记（B7 续接）

### B7 — 外层循环包裹下的混合链装配降级（深层嵌套不封闭，**未修复，登记续接**）

- **破坏条款**：C1/C2/C3 未在深层上下文恢复无感——同一形态浅层 MATCH、深层
  MISMATCH（理论 §1 推论的判定签名），三探针证据 rv_03/rv_05/rv_09（§2）。
- **状态**：**基线即失败**（57f3e944 两批修复前复跑同为 MISMATCH），非 round 1
  两批回退；round 1 两批修复其宣称形态（浅层 14 目标）全部成立。按
  §8 破口状态机登记为「已定位（复现 + 机制定性），交 round 2」。
- **与既有登记的关系**：FIX_B6 §5.3 已登记 while 家族残留（不同混合形态
  `while a and (b or c)` 等）；本破口补其**嵌套维度**：r1_10 同形态深嵌套即败。
- **交接建议（round 2 候选方案，须先证机制后落地）**：
  1. rv_05：Step5 所有权校验把「外层 Loop 的 body_blocks 认领」纳入合法持有者
     分类（镜像 fix1 B 臂的 body_blocks 豁免思路），并核查幻影 `if a: continue`
     的物化来源；
  2. rv_03：B 臂豁免的 LoopRegion 查表取的是 block_to_region 直属 owner——深嵌套
     下候选块 claim 归属变化，需按同层后继结构重判；
  3. rv_09：`_detect_ternary_pattern` 升级判据前置条件（BoolOpRegion 已完整装配）
     在外层 while 的条件装配竞争中未成立，属装配顺序问题非消费端问题。

---

## 4. 宣称验收复验

### 4.1 修复一（清单3）—— 通过

「pycdc 重反编译到临时目录 + `pyc_verify single --source`」法（抽 5 个 ≥ 4 个要求）：

| 目标 | 读数 |
|---|---|
| r1_01_stmt_andor3 | success 2/2 100% |
| r1_07_deep3_mixed | success 2/2 100% |
| r1_09_continue_break_guard | success 2/2 100% |
| r1_15_ifelse_mixed | success 2/2 100% |
| r1_18_ortail_return | success 2/2 100% |
| neg75_jqcond2（B1b 验收判据） | **success 3/3 100%** |
| IQCommon/strategy/jq_trans_module.pyc | **success 65/65 100%** |
| fly/data/quotation.pyc | **152/153 99.35%**（唯一失败 change_his_to_forward = 基线既有，零新增） |

MATCH 组/负对照防回退抽 4：r1_02、r1_12、r1_19、n1_01 全 2/2 100%。

### 4.2 修复二（清单4）—— 通过

| 目标 | 读数 |
|---|---|
| r1_10_while_mixed | success 2/2 100% |
| r1_11_ternary_mixed | success 2/2 100% |
| r1_14_assert_mixed | success 2/2 100% |
| r1_21_comprehension_mixed | success 3/3 100% |
| 修复一 10 目标抽 3（r1_01/r1_09/r1_15，与 §4.1 重叠） | 全 2/2 100%，零回退 |
| IQEngine/.../trade_live_broker.pyc | **118/128 92.19%**（≥ 118 达标） |

---

## 5. 清单5：docstring 三要素名实相符 —— 通过（附 3 条注记）

逐方法对照（识别条件/归约方式/AST 映射 + C 条款声明 vs 代码行为）：

| 方法 | 判定 |
|---|---|
| `_b1b_loop_body_run_continuation`（region_analyzer.py:27247） | ✅ 三要素+C1/C2/C3 全声明，三类续接与代码逐条吻合（含 has_or_member 豁免、同 TRUE 族拒绝） |
| `_try_unify_mixed_boolop_chain`（:27389） | ✅ 判据 (1)(2)(3) 与代码一致；Round 33 签名反向用途声明准确 |
| `_detect_boolop_conditional_chain` docstring（:25589-25616） | ✅ [B1b fix]/[fix-r2]/IfExp 收窄/cc 守卫四段与三处代码一致 |
| `_identify_conditional_regions` Step5 docstring（:16124） | ✅（见注记 3） |
| `_detect_while_condition_boolop_chain`（:24197/:24459） | ✅ 四条识别条件与代码逐条对应；「混合链不经 all_same_target」与代码分支一致 |
| `_identify_boolop_regions` Step5 docstring（:23677） | ✅ 三类持有者 + 残链超越判据与 :24017-24056 一致 |
| `_b6_assert_absorb_and_run`（:15390） | ✅ 三要素+C1/C2/C3；「仅吸收未认领前驱」与代码一致 |
| `_build_ternary_boolop_condition`（region_ast_generator.py:35288） | ✅ 「不处理混合and/or」旧文已删，or_groups 声明与代码一致 |
| `_loop_generate_while`（:6533） | ✅ 三分识别/归约/映射声明与代码一致 |
| `_detect_comp_ternary`（comprehension_generator.py:1875） | ✅ [B6-comp] 融合回跳签名声明与代码一致 |
| `_build_assert_boolop_condition`（region_ast_generator.py:3949） | ⚠️ 注记 4 |
| `_detect_ternary_pattern`（region_analyzer.py:21834 内联） | ⚠️ 注记 5 |

**注记 4**：`_build_assert_boolop_condition` 的方法级 docstring「输入契约」段仍只
描述旧契约（chain_ops=每段 op），新契约（len(chain_ops)==len(all_blocks) 首项=
condition_block 自身 op）的三要素写在方法体内 [B6-assert op 契约扩展] 行内注释中，
齐备但位置与 FIX_B6「触及方法 docstring 三要素」表述有出入。不构成打回（内容无错、
行为相符），要求 round 2 顺手把契约段补入 docstring。
**注记 5**：`_detect_ternary_pattern` 方法 docstring 未提 [B6-ternary] 升级路径，
三要素在函数内联注释块（:21834-21859）中齐备且与代码一致。同注记 4 处理。
**注记 3**：C 臂注释「与 _sb_has_body 同一谓词」为**同族近似**：opcode 集与
CALL→POP_TOP 判定一致，但 C 臂扫描全块（无 `_cond_start_offset` 下界、无
import-store 豁免、CALL 与 POP_TOP 间额外放行 YIELD_VALUE）。就「else_succ 必须是
纯条件块」的语义而言 C 臂更严的扫描方向是正确的；建议措辞改为「同一 opcode 族谓词」。

---

## 6. 清单6：core/ 调试残留 —— 通过

- fix1 声称清除的调试产物全部不在：`tmp_debug_b1b.py`/`.tmp_fix1_pre/`/
  `.tmp_fix1_probe/`/`_b1b_merge_trace.log`/`.tmp_b6probe` 零存在；
  `B1B_MERGE_DEBUG`/`_b1b_merge_trace` 在 core/ 零命中。
- 两批 diff（`git show 1a0f2760|9725103d -- core/`）新增行中 `open(`/`environ`/
  `.log` 零命中——无新增调试钩子、无临时文件写入代码。
- 存量 env 门控钩子（`_R23N20_DEBUG`、`R23N21_DEBUG`、`R7_DEBUG_IFGEN` 等）经
  `git show 1a0f2760^` 确证为两批之前既有，未动（FIX.md §6.5 声明属实）。

---

## 7. 总结论

| 批次 | 结论 |
|---|---|
| **修复工程师一（B1b 核心，1a0f2760）** | **放行**。合规审计零违例；宣称读数（10 目标、neg75_jqcond2 3/3、jq 65/65、quotation 152/153 零新增、tlb 115→118）全部复验成立；10 探针中攻击其判据的 4 个深嵌套变体全 MATCH。 |
| **修复工程师二（B6 四上下文，9725103d）** | **放行（限定表述）**。合规审计零违例（Step5 删除型改动守卫齐备，列回归监控点）；宣称读数（r1_10/11/14/21 全 MATCH、修复一 25/25 零回退、jq 65/65、quotation 152/153、tlb 118/128）全部复验成立。但其「B6 四上下文封闭」声明按嵌套无感不变式降格为**「浅层（宣称形态）封闭」**——深嵌套变体 rv_03/05/09 证明该族装配判据在深层上下文不触发（基线即败、非本批回退），登记 **B7** 续接 round 2。 |
| **新破口** | **B7 外层循环包裹下的混合链装配降级**（rv_03/rv_05/rv_09 三复现，§3），状态=已定位交 round 2。 |

**rv_ 探针统计：10 个新探针（rv_01..rv_10），7 MATCH / 3 MISMATCH；
3 个 MISMATCH 均经基线复跑确证为基线既有，零回退。**

复核者：评审工程师（REVIEW2）。本报告零修改 core/、scripts/、site-packages/；
探针与报告为本评审全部产出。
