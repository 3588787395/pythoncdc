# Round 1 评审工程师报告（对抗性审查）

- 评审对象：commit `c53df077`（在途未评审变更快照）`core/cfg/region_ast_generator.py` +419 行（`[R76-A1/A2]` 守卫 wrap + `[R75 fix1]` B1a `_graft_pending_operand` 嫁接）
- 理论权威：`wiki/concepts/decompile-invariant-completeness.md` §1 三条款 / §5 台账 / §6 破口登记
- 任务B判据（唯一）：`scripts/pyc_verify.py single`（pylingual `compare_pyc` 逐单元判定）
- 复现落盘：`test_repros/round1/`（r1_*.py / .pyc / *OK.py / *_dec.py / *_dec.pyc / n1_* 负对照）
- 硬约束遵守：未修改 core/、scripts/、site-packages/ 任何文件；*OK.py 全部由 pycdc.py 生成；每条 shell 命令 ≤300 s

---

## 任务A：算法合规审计（对象 = 标记新增 420 行，diff hunk：1741/1773/1823/32720/42430/43174/48021/48035）

| # | 审计项 | 结论 | 依据（file:line = region_ast_generator.py 当前树） |
|---|---|---|---|
| A1 | 新增 self 跨方法状态 | **通过** | 全部 420 新增行 0 处 `self.*` 赋值（git diff c53df077~1 c53df077 实测）。`_r76g_stack` 为 generate() 栈式局部状态（:1751，闭包 `_r76g_emit/_r76g_close` 消费，:1753-1760）；跨方法传递走「挂块」模式 `setattr(block,'_leading_operand'/'_leading_guard')`（:48045/:32892），挂在块对象上非 self；`_R76_IGNORE_KEYS`（:32972）为类级常量 frozenset（比较词汇表，非可变状态）；`_generated_regions/_generating_regions`（:283-284）确认为预存属性非新增 |
| A2 | 跨层信息读取无显式守卫 | **通过** | ①`_graft_pending_operand`（:32734-32786）只读 L(A)：region.entry 挂记录、op_chain、merge_block；去向由「jump_target∈链出口集 / ck==1 链首续接」两条同层结构判据决定（:32774-32785），`_contains_identity` 保证幂等（:32754）。②`_leading_guard_candidate`（:32848-32893）读 region_analyzer 表与 parent 指针属非局部信息，但有三重显式守卫：守卫①顶层 IfRegion 身份（:32869-32873）、守卫②目标未生成（:32874-32877）、守卫③块集归属+extent 内 owner 区域入口闭合（:32882-32891）。③`_leading_guard_extent`（:32805-32846）边收敛校验（:32838-32845）——越界边即放弃记录、行为逐字节不变。④`_r76_test_consumes_guard`（:32996-33023）只读本区域产物 test 与记录操作数，A1/A2 裁决由发射后结构事实决定（:1838-1841），不预测分析器行为 |
| A3 | 函数名/文件名白名单、start_offset 魔法阈值 | **通过** | 全部分判据为同层块对象结构事实：start_offset **恒等比较**（块身份配对 :32771/:32830）、op_chain 链位（ck==1 :32778）、conditional_successors≥2（:32923）、argval 跳转指向（:32925-32932）、指令 opname 集合过滤（:32916-32949，与 CJB 既有过滤序列 :47940-47949 逐条镜像）。无任何函数名/文件名/模块名白名单；无绝对偏移阈值（start_offset 只作身份不作数值比较） |
| A4 | 「以少发射换全绿」路径 | **通过（带保留）** | 2 行删除（`ast_nodes.extend/append(region_ast)`）为发射路由替换，else 分支（:1847-1853）复刻原行为，不丢语句；条件指令剥离（:42445-42448/:43188-43191）仅在守卫记录建立成功后发生，接回路径=generate() wrap。**保留**：①B1b（前存破口，非本批引入）经任务B 14 个复现确证仍未封闭；②登记观察 O1（见下）：守卫记录存在「登记→消费」之间的孤儿化路径，若触发则构成新丢弃路径（未获复现） |
| A5 | docstring 三要素与 C1/C2/C3 名实相符 | **通过（2 处措辞附注）** | 逐函数核验：`_contains_identity`（识别条件齐，helper 无 AST 映射可接受）；`_graft_pending_operand`（①根因②同层判据③去向三段，与 ck==1 分支 :32778-32785 行为一致）；`_build_boolop_expression`（三要素齐，"jq_trans_module 63/65→65/65 修复点"声明与 diff 实际相符）；`_leading_guard_extent`（三要素齐+C3 边收敛声明）；`_leading_guard_candidate`（记录约定+三重校验，AST 映射由消费端 wrap 段声明）；`_detect_leading_guard`（三要素齐，None-check 极性规则与 CJB :48013-48018 同款）；`_r76_expr_equal/_r76_test_consumes_guard`（三要素齐，[C1] 声明属实）。**附注1**：`_leading_guard_extent` docstring 自称"[C1] 只读 L(A) 内结构事实"，实际遍历读的是从 then_entry 出发的 CFG 正常后继边（超出严格 L(A)）——机制本身是 C3 式「识别→校验→消费」显式守卫，判定不破但措辞失准，建议改称"[C3] 守卫发现步"。**附注2**：守卫②（:32874-32877）只在**登记时点**检查"未生成"，登记→消费之间状态可变（见观察 O1） |

### 观察登记（未构成破口，防回归）

**O1 — 守卫记录孤儿化路径**（generate() 顶层循环）
- 锚点：:1769-1775（already-generated continue，记录捕获点 :1780 之前）与 :1816-1825（`region_ast` 为假时 :1838 的 wrap 裁决被整体跳过）。
- 机制：发射端已在 :42447/:43190 剥离条件指令并以记录承诺接回；若目标区域在消费前被其他路径整体置 generated（孤儿释放 :1593-1663、R57b 扫描 :1740-1742 等）或 `_generate_region` 返回假值，wrap 不打开、条件丢失无接回。
- 现状：顶层 IfRegion 块集被其他路径整体消费的构造未找到，**静态可达性低、未获复现**，不编号为破口；fix 批若改动守卫消费时序，须回归 r76_01/02/03 与本 round 全组。

---

## 任务B：完备形态对抗攻击（BoolOp 破口族 B1 + If 形态）

统计：**22 个攻击目标 → 14 MISMATCH / 8 MATCH；另 3 个 MATCH 负对照 → 合计 14 MISMATCH / 11 MATCH。**
合成复现全部成功命中（无需「真身码对象移植法」升级；该方法仅合成失败时启用，参照 round76 惯例保留）。

### MISMATCH 清单（判据输出 `Different control flow` / `Different bytecode`）

| 文件 | 焦点形态 | 首分歧指令（orig vs dec，dis 实测） | 反编译产物症状 | 根因归类 |
|---|---|---|---|---|
| r1_01_stmt_andor3 | 语句上下文 `if a and b or c:`（B1b 归档形态） | f+5: `POP_JUMP_FORWARD_IF_TRUE to 18` vs `to 24`；o14 `LOAD_FAST c` + o16 PJIF 整体缺失 | `if not (a and b): total += 4`（or 尾丢失+极性反转） | **RN-B1b** |
| r1_03_chain3 | 3 层混合链 `a and b or c and d or e` | 同位 PJIF 目标错 | 拆成 `if not (a and b or c and d): pass` + `if e:` 两语句 | **RN-B1b**（链拆裂） |
| r1_04_nested_if_mixed | 嵌套 if 内混合链 | f+3: PJIF 目标 32 vs 40 | 内层同 r1_01 形态 | **RN-B1b**（嵌套不封闭，C2 归纳步失败实证） |
| r1_07_deep3_mixed | 深度 3 嵌套 + 内层混合链 | f+3: PJIF 目标 36 vs 44 | 同上 | **RN-B1b** |
| r1_08_elif_try_for_with | if-elif-else 臂内嵌 try/for/with | f+5: PJIT 目标 18 vs 70 | 混合链 `if not (a and b):`，elif 降级为顺序 if | **RN-B1b×If** |
| r1_09_continue_break_guard | 混合链 + continue/break（B2 交叠） | f+7: PJIF 目标 22 vs 58 | `if not b: if c and a: break`（多余否定+结构错位） | **RN-B1b×B2** |
| r1_10_while_mixed | `while a and b or c:` | f+5: PJIF 目标 18 vs 50 | `if a: while b or c:`（循环条件拆裂；循环内 a 翻转语义改变） | **RN-B1b-loop**（→B6） |
| r1_11_ternary_mixed | 三元 `1 if a and b or c else 2` | f+1: PJIF 目标 10 vs 22 | `(1 if c else 2) if a and b else 1`（错序） | **RN-B1b-ternary**（→B6） |
| r1_14_assert_mixed | `assert a and b or c` | f+1: PJIF 目标 10 vs 22 | `if a: assert b or c; return 1`（尾部 return 被吸入） | **RN-B1b-assert**（→B6） |
| r1_15_ifelse_mixed | if-else 带混合链 | f+5: PJIT 目标 18 vs 24 | `if not (a and b):` + else 体提升为顺序语句 | **RN-B1b** |
| r1_17_elif_mixed | elif 臂为混合链 | f+3: PJIF 目标 22 vs 24 | else 内拆裂+末臂 return 错位 | **RN-B1b×elif** |
| r1_18_ortail_return | or 尾臂以 return 终结 | f+4: `LOAD_FAST c` vs `LOAD_CONST 1`（c 测试整体缺失） | `if not (a and b): return 1` | **RN-B1b** |
| r1_21_comprehension_mixed | 推导式筛选子句混合链 | f+2: `MAKE_CELL c` 缺失；listcomp+3 FOR_ITER 目标错 | `b if a else 1`（整链崩塌） | **RN-B1b-comp**（→B6） |
| r1_22_multistmt_body | or 尾臂 + 多语句 if 体 | f+5: PJIT 目标 18 vs 34 | `if not (a and b):` 两语句全收 | **RN-B1b** |

### MATCH 清单（当前算法已正确，形态边界实测）

| 文件 | 焦点形态 | 性质 |
|---|---|---|
| r1_02_stmt_orand | `if a or b and c:`（or 先行语句链） | 攻击目标意外 MATCH——B1b 触发条件收敛为「and 组先行 + 裸尾操作数」 |
| r1_05_or_tail_compare | `if a or b >= 2:`（or 尾为比较） | 同上 |
| r1_06_paren_groups | `if (a and b) or (c and d):`（双完整组） | MATCH——完整组无裸尾时不触发 |
| r1_12_and_group_or | `if a and (b or c):`（B1a 嫁接 ck==1 路径） | **B1a 嫁接修复的正向证据** |
| r1_13_return_mixed | `return a and b or c`（表达式上下文） | MATCH |
| r1_16_two_groups | `if a and b or c and d:`（两组无裸尾） | MATCH |
| r1_19_negated_mixed | `if not (a and b or c):`（UNARY_NOT 包裹） | MATCH——取反路径全链重建正确 |
| r1_20_orlead_and | `if (a or b) and c:`（or 组作链首） | MATCH |
| n1_01/n1_02/n1_03 | 浅层 and / or / and-and-and | **负对照（强制 MATCH，通过）** |

### 形态边界结论（攻击收敛）

B1b 触发条件实测收敛：**and 组先行 + or 裸尾操作数（尾操作数求值块被区域管线消费）**——完整双组（r1_06/r1_16）、or 先行（r1_02/r1_05/r1_20）、取反包裹（r1_19）、纯表达式上下文（r1_13）均 MATCH。B1a 嫁接（`_leading_operand`）对 `a and (b or c)` 形态修复有效（r1_12 MATCH）；`a and b or c` 的 then-侧嫁接不生效，因为首个条件跳转所在的 and 链块被 IfRegion 条件重建跨块消费、or 尾块经 merge 剪枝（W14-C 族）脱离区域——与归档 FACTS"未走 skip 分支、属 `_build_boolop_expression` 家族"定性一致。

---

## 新破口登记（编号续接 §6，B4 之后）

### B5 — CJB else-entry-only skip 的条件操作数丢弃入口（候选，未获独立复现）
- **锚点**：`region_ast_generator.py:48030-48033`（判定）+ :48035-48060（丢弃点）。
- **机制**：`_cjb_skip_inline_if` 可由 else 侧独立触发（jump target 为区域 entry、fall-through 非区域 entry），此时 `_cjb_pend_key=None`，:48038 的嫁接守卫不成立，`_cjb_cond_expr` 既不嫁接（B1a 路径）也不登记守卫记录（R76-A1 路径），条件操作数静默丢失——fix1/R76 只封闭了 then 侧，本入口与 B1a 完全同构。
- **条款**：C1（前驱块条件信息无接回）+ C3（非局部信息无守卫认领）。
- **状态**：静态确证丢弃入口存在；因与 B1b 混叠（同一 pyc 上两机制难以分离），**独立触发复现未获得**，按破口候选登记，交 fix 批以块级 dump 分离定位。

### B6 — B1 破口面扩大：非 if 语句上下文的 BoolOp 链消费族
- **锚点（复现+判据输出）**：`test_repros/round1/r1_10_while_mixed`（while 条件拆裂 `if a: while b or c:`，循环不变量破坏：循环内 a 翻转原版退出/反版不退出）、`r1_11_ternary_mixed`（错序 `(1 if c else 2) if a and b else 1`）、`r1_14_assert_mixed`（尾部 return 吸入 if 体）、`r1_21_comprehension_mixed`（整链崩塌 `b if a else 1`，连 `MAKE_CELL c` 都消失）。
- **机制**：`_build_boolop_expression_inner`（`region_ast_generator.py:33025`）家族的 and 组先行+裸尾缺失不仅在 if 语句上下文发生；WhileRegion 条件、TERNARY、ASSERT、推导式筛选四处消费点各自把残缺链重新物化成不同结构的错误 AST——即 B1b 的第二丢弃入口在这些上下文同样可达，且后果随消费方结构而异。
- **条款**：C1（or 尾操作数块归属错配）+ C2（嵌套/复合上下文归纳步失效——浅层单测已证深度 1 即错）。
- **状态**：4/4 复现确证（合成即命中，判据 Different control flow）。台账涉及形态：BoolOp（B1）判定维持"破口"，本条为破口面的上下文扩登记。

---

## 总结论

- **任务A：通过（5/5）**，附 2 处 docstring 措辞附注（`_leading_guard_extent` 的 [C1] 措辞、守卫②时点）与 1 条观察登记 O1。标记代码无 self 新状态、无白名单/魔法阈值、无新增丢弃路径，三重守卫与嫁接机制名实相符。
- **任务B：14 MISMATCH / 11 MATCH**（含 3 负对照全过）。B1b 确证**未封闭**且破口面扩大到 while/ternary/assert/comprehension 四个上下文（B6）；B1a 嫁接对其目标形态有效（r1_12 MATCH）。
- **登记**：新破口候选 B5（CJB else 侧第三丢弃入口）、破口扩登记 B6（非 if 上下文消费族）；观察 O1（守卫记录孤儿化，防回归）。
- **对 §5 台账的影响**：BoolOp 判定维持"破口"不变；§0 读数 127/128 不因本轮变化（B1a 落地但 B1b 未封闭，合并验收判据未达成）。
- **交下一轮（fix 工程师）**：①B1b 修复以 r1_01/r1_03/r1_18 为最小验收组（`if not (a and b)` 症状消失、or 尾接回）；②B6 四上下文形态纳入回归；③B5 以块级 dump 分离定位后决定是否成立；④回归 r76_01/02/03 与本 round 全组 25 项。
