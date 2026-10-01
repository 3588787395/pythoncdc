# Round 2 评审工程师报告（对抗性审查 Round 2：Try/ExceptHandler/try-finally/except* 族）

- 评审对象：Round 1 全部落地修复代码的守卫封闭性（commit 链 1a0f2760 → 9725103d → dbfa936f，工作树 = dbfa936f，core/ 零改动）
- 理论权威：`wiki/concepts/decompile-invariant-completeness.md` §1（C1 局部消费/C2 黑箱组合/C3 守卫封闭）、§5 表A（Try 行 `:7891/:9342/:9915`、孤儿 finally 帧 `:9017-9019`；TryStar 行）、§6、§8
- 任务B判据（唯一）：`python scripts/pyc_verify.py single`（pylingual compare_pyc 逐单元）
- 复现落盘：`test_repros/round2/`（r2_*.py/.pyc/*OK.py/*_dec.py + n2_*.py 负对照；注：该目录内另有旧规范 region-adversarial Round 2a 的历史 r2_* 归档文件（git 已跟踪），本轮文件以焦点后缀区分，未覆盖任何既有文件）
- 硬约束遵守：未修改 core/、scripts/、site-packages/ 任何文件；*OK.py 全部由 `python pycdc.py -o` 生成；每条 shell 命令 ≤300 s；工作流 = `python -m py_compile` → pyc 拷回同目录 → `pycdc.py -o *OK.py` → `pyc_verify.py single` → 首分歧用 dis/pycdas 对照
- 基线对照法：`git archive 57f3e944`（Round 1 两批修复前）解包至系统临时目录，同 pyc 复跑 + 产物逐字节 diff，判定每个 MISMATCH 是「本轮回退」还是「基线既有」

---

## 任务A：Round 1 修复代码守卫封闭性审计（算法合规零容忍）

审计面 = Round 1 落地的全部新判据在「Try/ExceptHandler/try-finally/except* 新语料」下是否仍封闭：region_analyzer.py 五臂（A=`_try_unify_mixed_boolop_chain` or 裸尾续接、B/B2=LoopRegion body_blocks 认领豁免+`_b1b_loop_body_run_continuation`、C=continue-sink 邻接 elif 排除收窄、D=IfExp 真值块守卫收窄、E=chained compare 内部块不可吸收）+ B6 七处（`_detect_while_condition_boolop_chain` 混合链双向续接、boolop Step5 所有权校验与残链超越、`_b6_assert_absorb_and_run`、`_detect_ternary_pattern` 升级、`_loop_generate_while` if-break 三分、or_groups 分组、comprehension 甄别窗）+ R1-REG 守卫（MERGEPATH 升级端让位）。

### A-1 异常边被新判据当成正常边消费？ —— 通过

| 锚点 | 事实 |
|---|---|
| `core/cfg/basic_block.py:92-93` | `conditional_successors = set(self.successors) - self.exception_successors` —— 异常边与正常边在集合层分离 |
| `region_analyzer.py:26575`（B 臂）/ `:27206`（`_b1b_loop_body_run_continuation` 入口）/ `:27432`（`_try_unify_mixed_boolop_chain`）/ `:24509-24528`（B6-while or 尾续接）/ `:24286`（B6-while 回溯） | 全部 fall-through/跳转探测走 `conditional_successors`；条件跳转 `argval` 是指令级正常边，异常表边不携带指令、不可能被 `get_block_by_offset(last.argval)` 解析为异常边 |
| `region_analyzer.py:24253-24257` | B6-while 后向回溯显式守卫：前驱含 `PUSH_EXC_INFO/CHECK_EXC_MATCH/CHECK_EG_MATCH/PREP_RERAISE_STAR/WITH_EXCEPT_START` 即 break —— handler 入口不被吸进 while 条件链 |
| `region_analyzer.py:27287-27357` | `_b1b_loop_body_run_continuation` 三类续接判据全部要求块末正向条件跳转 + 汇聚签名；finally 清理帧（RERAISE/POP_EXCEPT/JUMP_BACKWARD 收尾）结构性不满足 |

附注（基线既有，非 Round 1 引入）：`_b6_assert_absorb_and_run` 用原始 `chain_head.predecessors`（`region_analyzer.py:15418`）迭代候选——异常边前驱可进入迭代，但其 fall-through 等值过滤（`:15428-15431`：`p_fts == [chain_head]`）要求正常 fall-through 恰为链头，handler 入口仅经异常边可达、无正常 fall-through 进入路径，误吸收被结构性排除。未获复现；列 R2-O1 哨兵监控（fix 批若改 assert 前驱扫描须回归本条）。

### A-2 try 内混合链被 while/assert/ternary 判据抢走所有权？ —— 通过（附实证注记）

| 锚点 | 事实 |
|---|---|
| `region_analyzer.py:1448/:1456/:1484/:1487` | 识别顺序：try（:1448）先于 assert（:1456）、boolop/while 条件 Step5（:1484）、ternary（:1487）——异常区域先认领 |
| `region_analyzer.py:26596-26609`（B 臂）/ `:27436-27462`（A 臂 `_try_unify`） | body_blocks 认领豁免仅在 `isinstance(_ft_reg, LoopRegion)` 时放行；TryRegion/IfRegion/BoolOpRegion/其他一切持有者一律 break——新判据对 try/finally 认领块**零新增吸收面** |
| `region_analyzer.py:24031-24041`（Step5 所有权校验） | B6-while 链块持有者仅允许「未认领 / 本 LoopRegion / 待超越残链 BoolOpRegion」，其余持有者 ⇒ 整链放弃（continue）——or 尾 walk（`:24515-24549` 不查 block_to_region）的越权被 Step5 兜底拒绝 |
| 实证 r2_10（try 内 while/assert/ternary 混合链三单元） | `f_while`/`f_assert` **MATCH**（try 内浅层混合链由 B6 正确装配，未回退）；`f_ternary` MISMATCH 经基线复跑产物逐字节相同 = **基线既有残缺**（B6-ternary 升级判据在 try 内未触发的装配顺序问题，属「未触发」而非「抢走」——与 B7 同族的未修状态，非本轮回退） |
| 实证 r2_08.g（handler 内 while 混合链） | MISMATCH 基线同产物 = 判据在 handler 上下文**未触发**（降级不封闭），未见判据把 handler 帧吸进链的迹象（产物无 handler 帧混入条件） |

### A-3 finally 块被链续接待收？ —— 通过（附注记）

| 锚点 | 事实 |
|---|---|
| `region_analyzer.py:10061-10078`（`_register_region_blocks`）/ `:9184-9186`（孤儿 finally 帧登记一例） | finally/finally_copy/cleanup 块进入 `block_to_region` 由 TryRegion 持有；A/B 臂豁免只认 LoopRegion，finally 帧不可被链豁免吸收 |
| `region_analyzer.py:27287-27357` | 续接签名要求正向条件跳转收尾 + 汇聚结构；finally 帧尾 RERAISE/POP_EXCEPT/JUMP_BACKWARD 不满足 |
| 实证 r2_09 | **f 单元（finally 内 `if a and b or c:`）当前树 MATCH，基线 1/3 → 现树 2/3 改善**——Round 1 B6 修复在 finally 上下文正向获益（基线产物为 `if not (a and b): ... if c:` 拆裂极性反转形，现树整链重建）；g 单元（finally 内 while+assert 混合链）MISMATCH 为**装配未触发**（链拆裂 + 幻影 `while False` + `assert False`），非 finally 帧被吸收 |
| 实证 r2_02/r2_03/r2_05（finally-only/四段全/try 嵌循环嵌 try） | 全部 3/3、3/3、2/2 MATCH |

注记（基线既有丢弃路径，非 Round 1 扩大）：`_loop_generate_while` if-break 三分的「orelse 含真实语句维持丢弃」分支（`region_ast_generator.py:6568-6576`）与 finally 吞异常形态叠加，在 r2_14.f（finally 内 `if i == 1: break`）实证 break 丢失 + return 前移进 finally——基线产物逐字节相同，历史行为。

### A-4 R1-REG 守卫（MERGEPATH 升级端让位）—— 通过

| 锚点 | 事实 |
|---|---|
| `region_ast_generator.py:42563-42605` | 让位判据只读本块指令流两次构建探针（`:42588-42590` `_probe_keep/_probe_strip`）+ 可绑定类型集合与 R59-B 升级端逐字一致（`:42597-42599`）；撤销 = delattr 幂等（`:42601-42603`）；不成立时维持剥离+wrap 原通道（`:42604-42605`） |
| 交互面检查 | 让位点在 TernaryRegion merge 块内；本轮 try/finally 新语料（r2_02/r2_03/r2_09/r2_10）未出现 merge 尾条件段跨 try 边界的形态，无竞争面新触发；块不跨异常表边界切割，探针只读单块指令流无跨层读取 |
| 真身哨兵 | risk_calculation `get_daily_summary` 未重跑——本轮零 core 改动，工作树与 Round 1 归档验证时同一 commit（dbfa936f），读数（41/43）不受本轮影响 |

### A-5 五臂 + B6 七处在 try/except/finally 新语料下整体回退检查 —— 通过（零回退）

- 12 个 MISMATCH 单元全部经 `git archive 57f3e944` 基线复跑确证为**基线既有**：其中 11 个产物与现树**逐字节相同**；r2_09 为**改善**（基线 1/3 → 现树 2/3）。
- Round 1 宣称形态抽验（r1_01/r1_10/r1_11/r1_14/r1_21/n1_01）当前树全 MATCH——守卫封闭面在已宣称形态上未失守。

### 任务A 总裁定：通过（5/5），零打回；附 R2-O1 哨兵 + 2 条基线既有注记

---

## 任务B：完备形态对抗攻击（Try / ExceptHandler / try-finally / except* 族）

统计：**20 文件（17 攻击目标 + 3 负对照）全部过 `py_compile` → 12 MISMATCH / 8 MATCH（文件级；失败单元逐个列于下表）。**
合成切片全部可用（无需真身码对象移植）。12 个 MISMATCH 全部基线既有（11 个产物与 57f3e944 逐字节相同；r2_09 改善）。

### MISMATCH 清单（12；首分歧 = dis 归一化（剔除 RESUME/CACHE/NOP/PRECALL）后第一条不一致指令）

| 文件 | 焦点形态 | 失败单元 | 首分歧指令（orig vs dec） | 产物症状 | 根因归类 |
|---|---|---|---|---|---|
| r2_11_except_star_single | except* 单 handler（`except* TypeError:`） | f（1/2） | o106 `LOAD_GLOBAL TypeError` vs d106 `LOAD_GLOBAL Exception` | `except* Exception:`（类型表达式整体丢失） | **R2-B8**（TryStar × C1 × 丢弃） |
| r2_12_except_star_multi | 多 except* 链（TypeError/ValueError/KeyError 各 as） | f（1/2） | o188 `LOAD_GLOBAL TypeError` vs d188 `LOAD_GLOBAL Exception` | **首个** handler 类型退化 Exception，后续 handler 类型保留 | **R2-B8** |
| n2_02_except_star_simple | 负对照（最小 except* `as e`）→ **翻案为攻击成功** | f（1/2） | o72 `LOAD_GLOBAL ValueError` vs d72 `LOAD_GLOBAL Exception` | 同上（负对照失败 ⇒ 最小形态即破） | **R2-B8** |
| r2_08_handler_mixed_boolop | handler 内 while 混合链 | g（1/3） | o46 `JUMP_FORWARD to 136` vs d46 `to 138` | `if not (a and b):` 极性反转 + 幻影 `while False:` + `if c:` 拆裂 | **R2-B9**（B6×handler 装配未触发，C1/C2） |
| r2_09_finally_mixed_boolop | finally 内 while+assert 混合链 | g（2/3，f 单元现树 MATCH=改善） | o104 `PJFIF to 110` vs d104 `to 134` | 链拆裂嵌套 if + 幻影 `while False:` + `assert False`（assert 链丢失） | **R2-B9**（B6×finally 装配未触发） |
| r2_10_trybody_mixed_boolop | try 内三元混合链（while/assert 两单元 MATCH） | f_ternary（2/4） | o4 `LOAD_FAST acc` vs d4 `LOAD_FAST a` | `acc.append(2 if a and b or c else 3)` → `if a and b: pass`（语句+or 尾双丢） | **R2-B9**（B6-ternary×try 装配未触发） |
| r2_17_trywrap_loop_mixed | try 包裹外层循环+内层混合链（B7×try） | g（1/3） | o4 `PJFIF to 148` vs d4 `to 150` | `if a and b or c:` → `if not (a and b):` + `if c: pass`（B1b 形拆裂） | **R2-B9**（B7 的异常区域包裹维度实例） |
| r2_04_try_nest3 | try 嵌 try 3 层+重抛 | f（1/2） | o60 `JUMP_FORWARD to 134` vs d60 `to 208` | 中层 handler 物化为 `else: try: pass except...` 幻影结构 | R2-01（Try 嵌套归约 × C2 × 结构） |
| r2_06_loop_try_continue | 循环内 try 体 continue | f（2/3） | o70 `JUMP_BACKWARD to 10` vs d70 `JUMP_FORWARD to 146` | try 体 `continue` 整句丢失（g 单元 handler 内 continue 正常） | R2-02（R76-D continue-sink 族 × C1 × 丢弃，基线既有） |
| r2_07_try_with_match | try 体含 with/match | f（1/2） | o174 `PJFIF to 256` vs d174 `to 236` | match 模式降级（`case {"k": v}`→`case {}`、`first, *rest = None`） | R2-03（match 模式重建 × 结构，基线既有） |
| r2_14_finally_swallows | finally 内 break/return 吞异常 | f（3/4） | o36 `FOR_ITER to 174` vs d36 `to 186` | finally 内 `if i == 1: break` → `pass` + `return out` 前移进 finally | R2-04（finally 吞异常 × if-break 既有丢弃面，基线既有） |
| r2_13_except_star_mixed | except* 与普通 except 混用（嵌套/finally 变体） | g（1/3） | o10 `PJFIF to 100` vs d12 `PJFIF to 102`（指令缺失） | 首 handler `except* Exception as e:`（同 R2-B8）+ 框架序位移 | **R2-B8**（+结构位移） |

### MATCH 清单（8）

| 文件 | 焦点形态 | 读数 |
|---|---|---|
| r2_01_try_multi_handler | try/except 多 handler 链（裸 except、元组、as、handler 内 return/break/continue、for-else） | 3/3 |
| r2_02_try_finally_only | try/finally-only（含循环内变体） | 3/3 |
| r2_03_try_four_part | try/except/else/finally 四段全（含循环变体） | 3/3 |
| r2_05_try_loop_try | try 嵌循环嵌 try | 2/2 |
| r2_15_reraise | try 内 raise + 裸 raise 重抛 | 2/2 |
| r2_16_handler_complex_type | handler 类型为复杂表达式（属性链/调用/下标）——普通 except 的 W12 重建全对 | 3/3 |
| n2_01_try_simple | 负对照：单 handler 简单 try/except | 2/2 |
| n2_03_while_plain_try | 负对照：普通 while×try 无混合链 | 2/2 |

---

## B7 复验（rv_03/rv_05/rv_09，--source 法：pycdc 重反编译到系统临时目录 + `pyc_verify single --source`）

| 探针 | 当前树读数 | Round 1 归档读数 | 判定 |
|---|---|---|---|
| rv_03_loopbody_forinwhile_break | failure 1/2 | failure 1/2 | 读数未变 |
| rv_05_while_mixed_in_for | failure 1/2 | failure 1/2 | 读数未变 |
| rv_09_ternary_mixed_in_while | failure 1/2 | failure 1/2 | 读数未变 |

**B7 状态维持「已定位（复现+机制定性）未修复」，基线既有读数未变；round 1 宣称形态（r1_01/r1_10/r1_11/r1_14/r1_21/n1_01）当前树全 MATCH，零回退。**

---

## 新破口登记（编号续接 §6，B7 之后）

### B8 — except* 首个 handler 的类型表达式被丢弃并退化为 `Exception`（**新破口，基线既有，非本轮回退**）

- **复现**：`test_repros/round2/r2_11_except_star_single.py`、`r2_12_except_star_multi.py`、`r2_13_except_star_mixed.py`（g 单元）、**负对照翻案 `n2_02_except_star_simple.py`**（最小 `except* ValueError as e:` 即破——「完备」宣称形态的最小化反例）。
- **首分歧**：orig `LOAD_GLOBAL ValueError/TypeError` vs dec `LOAD_GLOBAL Exception`（三处实测）。
- **机制（锚点齐全）**：except* 首 handler 入口块 = `PUSH_EXC_INFO; COPY; BUILD_LIST 0; SWAP; LOAD_GLOBAL <类型>; CHECK_EG_MATCH`。`_collect_pre_check_instrs`（`region_analyzer.py:10116-10134`）把 PUSH_EXC_INFO 与 CHECK_EG_MATCH 之间的**整段**收集为匹配表达式——except* 组匹配的框架指令 COPY/BUILD_LIST/SWAP 混入段内；`_reconstruct_except_match_expr`（`:10136-10196`）对含组合指令的段走 ExpressionReconstructor，框架污染致「栈上恰余一个白名单节点」接受判据失败，命中 `:10191-10196` 保守回退 **'Exception'**；code_generator 直通发射 `except* Exception`（`code_generator.py:717/:2094` 兜底）。后续 handler 的入口块若无框架前缀则类型保留（r2_12 实证 ValueError/KeyError 保留、仅首 handler 丢失）。
- **条款**：C1（同 handler 入口块内类型求值段的信息被框架噪声污染而未按 except* 组匹配语义解读——识别面读了 L(A) 但归约语义错配）；性质 = **丢弃**（类型表达式被默认值替换，语义面 = 捕获范围扩大）。
- **台账影响**：§5 表A TryStar 行与 §7 的「完备」判定须降格——§7 的锚点只证明识别/归约/生成**构造点存在**（误解 2「有过就算」的 except* 版），本轮给出产物级反例 + 机制锚点；按 §2.2 判据「三路径存在 ∧ 不变式破坏有确证」改判**破口**。
- **状态**：基线既有（57f3e944 同产物）；按 §8 状态机登记「已定位（复现+机制），交 fix 批」。

### B9 — 异常区域（try/except handler/finally）包裹下的混合链装配降级（B7 的姊妹维度扩登记）

- **复现**：`r2_08_handler_mixed_boolop`（g）、`r2_09_finally_mixed_boolop`（g）、`r2_10_trybody_mixed_boolop`（f_ternary）、`r2_17_trywrap_loop_mixed`（g，B7 形态在 try 内的实例）。
- **机制**：B6 各装配判据（while 双向续接 / ternary 升级 / assert 吸收）的触发前提在异常区域包裹下不成立（try 体块被异常表切分改变链块布局、handler 入口帧占用装配锚点），残链由主扫描物化为拆裂结构——症状随消费方而异（极性反转/幻影 while False/assert False/语句+or 尾双丢），与 B7「外层循环包裹」同构，包裹维度从 Loop 扩至 Try 族。
- **条款**：C1/C2（同一混合链形态浅层 MATCH、异常区域包裹 MISMATCH——嵌套无感签名）。
- **状态**：基线既有（四复现产物与 57f3e944 逐字节相同）；注意 r2_09 **f** 单元（finally 内 if 混合链）为 Round 1 B6 修复**改善**单元（1/3→2/3），B9 范围不含该已封闭形态。

### 观察登记（防回归）

- **R2-O1**：`_b6_assert_absorb_and_run` 用原始 `predecessors`（`region_analyzer.py:15418`）——异常边前驱进入候选迭代，靠 fall-through 等值过滤（`:15428-15431`）结构性排除；无复现，fix 批改 assert 前驱扫描时须回归。
- **R2-O2**：`exception_handler.py:148/:196` 异常类型名白名单（`'ValueError','TypeError',...,'BaseException'`）——零容忍口径下的**基线既有**违规（非 Round 1 代码）；它是 B8 之外的另一 except*/except 定位 fallback 面（`CHECK_EG_MATCH` 最近 LOAD 搜索），fix 批处理 B8 时应一并结构性移除。
- **R2-O3**：`r2_06.f`（try 体 continue 丢弃）、`r2_07.f`（match 模式降级）、`r2_14.f`（finally 吞异常形态 break 丢失）为基线既有独立缺陷，本轮归类 R2-01/02/03/04 待后续轮按 §8 立项（本轮登记不编号为 Bn，因三路径均存在且与本轮审计面正交；其中 r2_06 属 R76-D continue-sink 族既有登记的复现扩充）。

---

## 总结论

| 项 | 裁定 |
|---|---|
| **任务A（Round 1 修复代码守卫封闭性）** | **通过（5/5，零打回）**。异常边不进新判据（conditional_successors 集合层隔离 + PUSH_EXC_INFO 族显式守卫）；try/finally 认领块零新增吸收面（豁免仅认 LoopRegion + Step5 所有权兜底）；R1-REG 让位判据无跨层读取。12 个新语料 MISMATCH 全部基线既有（11 产物逐字节同基线，1 个反为改善）——Round 1 两批修复**零回退**。附 R2-O1 哨兵 + finally 既有丢弃路径注记。 |
| **任务B（对抗攻击）** | **12 MISMATCH / 8 MATCH**（20 文件，含负对照翻案 1）。全部合成切片可用，无需真身移植；首分歧全部定位到指令级。 |
| **B7 复验** | rv_03/rv_05/rv_09 读数未变（各 failure 1/2），维持「已定位未修复」；round 1 宣称形态零回退。 |
| **新破口** | **B8**（except* 首 handler 类型丢弃 → Exception；负对照 n2_02 翻案；台账 §5.2/§7 TryStar「完备」判定须降格）＋ **B9**（异常区域包裹混合链装配降级，B7 姊妹维度）。观察 R2-O1/O2/O3。 |
| **交 fix 批** | ①B8 以 n2_02 为最小验收组（`except* ValueError as e:` 类型保留），同时移除 R2-O2 白名单；②B9 以 r2_08.g/r2_09.g/r2_10.f_ternary/r2_17.g 为验收组，机制先证（装配顺序 vs 判据触发面）；③回归 B7 三探针 + Round 1 全组 + 本轮 20 文件。 |

复核者：评审工程师（Round 2）。本报告零修改 core/、scripts/、site-packages/；`test_repros/round2/` 复现与本报告为全部产出。
