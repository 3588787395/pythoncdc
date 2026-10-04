# Round 10 终审评审报告（任务 10.1）

评审角色：对抗攻击 + 合规审计（零容忍立场）。本轮零代码修改、零 site-packages OK 手改、零 git 提交。
判据工具：`scripts/pyc_verify.py` batch（ruler = pylingual equivalence_check，sha 9c7567bd6776b36b）；解释器 3.11.7。

---

## §0 结论速览

| 项 | 读数 |
|---|---|
| 覆盖矩阵 | 台账 §5 全 41 组（表A 17 + 表B 10 + 表C 14）映射完毕：35 组有对抗覆盖（含宿主被动），**6 组零专攻**（§2） |
| 补攻击 | 零覆盖最高风险 2 组（Import/ImportFrom/Alias、Global/Nonlocal）+ R-1 观察项面：**61/72 单元 = 84.7%**，11 单元 MISMATCH；负对照 9/9 全 MATCH |
| 残留破口决策 | 29 项全部判 (a) 可封闭（判据草案见 §4）；**(b) 不可达清单为空**；B64 实测更正为已封闭 |
| 新破口 | **B71–B75** 共 11 个 MISMATCH 单元，全部经 d8246a8e worktree 逐字节同败证实为既有缺口（与 Round 9 修复零关联） |
| 合规审计 | 四项红线全过（§6）：core/parsers/scripts 零 diff、双核心单 BOM、零插桩残留、OK 产物零手改；归因 worktree 已 remove 清零 |

---

## §1 覆盖矩阵（round1..9 攻击面 × 台账 §5 形态组）

读数列 = 该组最近一轮全量验证口径；「宿主」= 仅作为其他组探针的嵌套宿主被动覆盖，无专攻探针。

### 表A — 语句与结构形态

| # | 台账形态组 | 覆盖轮次 | 读数 / 备注 |
|---|---|---|---|
| A1 | Module | 宿主（全轮） | 无模块级专攻 → 缺口组① |
| A2 | If（IF/IF_THEN/IF_THEN_ELSE/ELIF_CHAIN） | R1/R7/R9 | 已覆盖（B2 守卫族防回归面） |
| A3 | For / AsyncFor | R3/R6 | 已覆盖 |
| A4 | While | R3 | 已覆盖 |
| A5 | Break / Continue | R3/R9；R10 再攻（R-1 面） | 2/4（B71） |
| A6 | Try（含 try_finally_only） | R2/R6/R9；R10 再攻 | B71/B73/B75 命中 |
| A7 | TryStar（except*） | R2 | 已覆盖 |
| A8 | With / AsyncWith | R6/R9 | 已覆盖（B66/B68 已封闭面） |
| A9 | Match | R4；R10 再攻 | B74 命中 |
| A10 | Raise / Assert | R8 | 已覆盖（B56–B58 残留在册） |
| A11 | Return / Pass / Expr | R8 | 已覆盖 |
| A12 | Delete / Assign / AugAssign / AnnAssign | R8 | Delete/Assign/AugAssign 已覆盖；**AnnAssign 专攻零 → 缺口组③** |
| A13 | Import / ImportFrom / Alias | **R10 专攻** | 26/28（B73/B74） |
| A14 | Global / Nonlocal | **R10 专攻** | 33/40（B72） |
| A15 | FunctionDef / AsyncFunctionDef / ClassDef | 宿主（全轮，函数体为一切探针载体） | **ClassDef 体专攻零 → 缺口组②** |
| A16 | ExceptHandler | R2/R8 | 已覆盖（B45/B50/B55 已封闭面） |
| A17 | match_case / withitem | R4/R6 | 已覆盖 |

### 表B — 表达式形态

| # | 台账形态组 | 覆盖轮次 | 读数 / 备注 |
|---|---|---|---|
| B1 | BoolOp（and/or） | R1/R7/R9 | 在册唯一完备破口 B1（B1a 已验证未落地 / B1b 未定位） |
| B2 | IfExp（三元） | R7/R8/R9 | 已覆盖（B42/B46–B51 残留在册） |
| B3 | Compare/BinOp/UnaryOp/Constant/Name/Attribute/Subscript/Starred/List/Tuple/Dict/Set/Slice/Index | R7/R8 | 已覆盖 |
| B4 | Lambda | R7 | 已覆盖 |
| B5 | ListComp/SetComp/DictComp/GeneratorExp/comprehension | R5/R9 | 已覆盖 |
| B6 | Call / keyword / arguments / arg | R8（被动力） | **keyword_args/star_args 调用点专攻零 → 缺口组⑤** |
| B7 | JoinedStr / FormattedValue | 无专攻记录 | **缺口组④（fstring_conversion）** |
| B8 | Await / Yield / YieldFrom | R6/R7 | 已覆盖（B47 残留在册） |
| B9 | NamedExpr（海象） | 组合面随 R7/R8 复合探针被动 | 专攻随缺口组⑤登记 |
| B10 | 上下文/操作符叶子（Load/Store/Del + 32 操作符） | 全轮隐式 | 已覆盖 |

### 表C — 扩展形态

| # | 台账形态组 | 覆盖轮次 | 读数 / 备注 |
|---|---|---|---|
| C1 | elif 链 | R1/R7；R10 再攻 | r10_06 elif 链 5/5 MATCH |
| C2 | for-else / while-else | R3/R8 | 已覆盖（B49/B61 残留在册） |
| C3 | except* 异常组 | R2 | 已覆盖 |
| C4 | match + 守卫 + 8 模式 | R4；R10 再攻 | B74 命中（guard 幻影族） |
| C5 | 多上下文 with / try_finally_only | R6/R8/R9 | 已覆盖（B68 已封闭面） |
| C6 | multi_target_assign / augmented_assign | R8 | 已覆盖（B54 已封闭；B65 残留） |
| C7 | chained_comparison / walrus / keyword_args / star_args / slice | R7 部分 | chained_comparison 已覆盖；其余 → 缺口组⑤ |
| C8 | relative_import / star_import / global_nonlocal | **R10 专攻** | r10_05（rel/star）4/4 MATCH；global_nonlocal 见 A14 |
| C9 | fstring_conversion | 无专攻记录 | 缺口组④ |
| C10 | nested_comprehension | R5 | 已覆盖 |
| C11 | decorator_with_args | 无专攻记录 | **缺口组⑥** |
| C12 | async 五件套（def/for/with/await/yield_from） | R6 | 已覆盖（B37/B40/B41 残留在册） |

**矩阵结论**：41 组中 35 组有对抗覆盖（其中 R10 新增专攻 2 组：A13/A14 及 C8 的 relative/star 面）；6 组零专攻缺口见 §2。

---

## §2 零覆盖清单与风险理由（诚实登记，未补攻部分不粉饰）

| 缺口组 | 台账定位 | 风险理由 | 本轮处置 |
|---|---|---|---|
| ① Module 专攻 | A1 | 模块级语句序/docstring/顶层 if-main 归约路径从未被单测；区域树根装配无独立探针 | 未补攻（本轮名额用于风险更高两组）；登记待后续轮 |
| ② ClassDef 体专攻 | A15 | 类体宿主（类级赋值/方法间语句/装饰器位）无专攻；全部探针仅函数体宿主 | 未补攻；登记 |
| ③ AnnAssign | A12 组内 | `x: T = v` 带注解赋值装配位无专攻（同组 Assign/AugAssign 已覆盖） | 未补攻；登记 |
| ④ fstring_conversion | B7/C9 | JoinedStr/FormattedValue 的 conversion/format-spec 位无专攻 | 未补攻；登记 |
| ⑤ keyword_args/star_args 调用点（含 walrus/slice 随组） | B6/B9/C7 | 调用点 kwarg/双星/海象/slice 操作数位无专攻 | 未补攻；登记 |
| ⑥ decorator_with_args | C11 | 带参装饰器应用位无专攻 | 未补攻；登记 |

风险排序依据：本轮选取补攻组 = A13+A14（Import 族、Global/Nonlocal 族），理由：(1) 402 语料中 import 密度最高但九轮零专攻；(2) global/nonlocal 语义破坏最重（闭包写降级 UnboundLocalError，属静默语义破坏而非仅字节码差异）。实测证明该判断正确——两组各挖出 1 个系统性新破口（B72/B73/B74/B75）。

---

## §3 补攻击读数（探针：test_repros/round10/；验证：rounds/round10/r10_*.json）

### 3.1 Import 族（r10_import.json：26/28 = 92.9%）

| 探针 | 攻击面 | 单元 | 结果 |
|---|---|---|---|
| r10_01_import_alias | import a.b.c / import x.y as q / 多别名 | 4/4 | MATCH |
| r10_02_fromimport_alias | from-import 括号多名 / as 别名 | 5/5 | MATCH |
| r10_03_import_nested_hosts | class Host.method 内 import / def>for>if>import（4 层）/ while>try>import | 5/5 | MATCH |
| r10_04_import_try_cross | try 四段各 import + handler 内 as 别名 | 2/3 | **MISMATCH（B73）** |
| r10_05_relative_star | from . / from ..x as / from .stars import * | 4/4 | MATCH |
| r10_06_import_deep_combo | match case 内 import（lambda 默认值）/ elif 链各臂 import | 2/3 | **MISMATCH（B74）** |
| n10_01/n10_02（负对照） | 裸 import / 裸 from-import | 4/4 | MATCH |

### 3.2 Global/Nonlocal 族（r10_scope.json：33/40 = 82.5%）

| 探针 | 攻击面 | 单元 | 结果 |
|---|---|---|---|
| r10_11_global_basic | global 读写 + 全算子增量赋值 | 3/3 | MATCH |
| r10_12_global_deep | 三层嵌套 global / 双 global | 7/7 | MATCH |
| r10_13_nonlocal_basic | 双层闭包 nonlocal（counter/swap） | 5/5 | MATCH |
| r10_14_nonlocal_deep | 四层闭包链 nonlocal / 多名 nonlocal | 4/7 | **MISMATCH（B72，s2/s3/s4）** |
| r10_15_global_hosts | global × try/with/match/for>if 宿主交叉 | 5/6 | **MISMATCH（B75，g_in_try_except）** |
| r10_16_scope_mix | global+nonlocal 三层混合 / 推导式捕获自由变量 | 4/7 | **MISMATCH（B72，mix 链 3 单元）** |
| n10_03/n10_04（负对照） | 裸 global / 裸 nonlocal | 5/5 | MATCH |

### 3.3 R-1 观察项实证面（r10_finloop.json：2/4 = 50%）

| 探针 | 攻击面 | 单元 | 结果 |
|---|---|---|---|
| r10_21_fin_loopctrl | finally 体仅含 continue / 仅含 break / continue-with-stmt 正对照 | 2/4 | **MISMATCH（B71：fin_continue + fin_break）**；fin_continue_stmt 正对照 MATCH |

### 3.4 汇总

- 攻击读数：**61/72 = 84.7%**（import 26/28 + scope 33/40 + R-1 面 2/4）
- MISMATCH：11 单元（B71×2 / B72×6 / B73×1 / B74×1 / B75×1）
- 负对照：**9/9 全 MATCH**（简单形态零误伤，证明失败非噪声）
- 归因：6 个失败 pyc 在 worktree @ d8246a8e（Round 9 评审批次一锚点，其 core 与合规基线 201234ab 零差异）重生成产物，MD5 逐字节相同 → **全部既有缺口，与 Round 9 修复（B66/B67/B68）零关联**。worktree 已 `git worktree remove` 清零。

---

## §4 残留破口逐项决策表

判定口径：(a) 可封闭 = 判据只允许同层块结构事实（块末 opcode、后继/前驱集合、异常表区间/异常边、区域成员关系、指令 opcode/oparg、code object 元数据），禁止名字白名单/魔法阈值/跨层回溯/self 跨方法状态；(b) 判据不可达 = 字节码层信息在 pyc 中不可恢复。**本轮 (b) 清单为空**，论证见 §4.2。

### 4.1 决策表（29 项全部 (a)）

| 破口 | 登记面（机制） | 判定 | 判据形态草案（同层事实） | 优先级 | 证据状态 |
|---|---|---|---|---|---|
| B37 | with/try/for 交叉循环控制蒸发（2 单元） | (a) | break/continue 终结块归属由同层后继集合决定：终结块后继须含循环头/出口块（区域成员关系）；异常边（WITH_EXCEPT_START 区间）不得改写成员关系判定 | P3 | r8 REVIEW §rv6 逐位持平 |
| B38 | 外层 handler 边界吞并（2 单元） | (a) | handler 收集边界 = 异常表区间覆盖块集；外层 handler 入口块不在内层 try 异常区间内则禁止归并（前驱集 + 异常边事实） | P3 | 同上 |
| B39 | finally 延迟双写/双 finally 覆盖（3 单元） | (a) | 嵌套 finally 帧按异常表区间分层归属；同区间双 finally 按块线性序切分，禁止跨区间复制 | P3 | 同上 |
| B40 | yield from × for-else 混合（1 单元） | (a) | GET_YIELD_FROM/SEND 块为表达式位输入（栈事实），else 臂归属由汇合块非回边前驱集判定 | P3 | 同上 |
| B41 | withitem 深层 star 元组（3 单元） | (a) | with 前导段（WITH_EXCEPT_START 之前）内 UNPACK_SEQUENCE oparg>1 块归属 withitem 目标还原 | P2 | 同上 |
| B42 | 三元×参数位/比较 LHS/推导式 filter（3 单元） | (a) | 三元区域块边界 = POP_JUMP_FORWARD_IF_FALSE/TRUE 对间块集；CALL 参数栈位内三元块禁止越界（C1 局部消费） | P2 | r7 残留逐位持平 |
| B43 | 链式比较 × BoolOp 组合（2 单元） | (a) | COMPARE_OP 链中 JUMP_IF_FALSE_OR_POP 分支汇合块为消费点；BoolOp 值重建消费汇合块栈输出 | P2 | 同上 |
| B44 | BoolOp and/or 重复/三层嵌套/深右嵌套（3 单元） | (a) | B1 同族：`_build_boolop_expression` 双入口（B1a/B1b）封闭时统一归纳分支链嵌套右臂，禁止右结合压平 | P2 | 同上 |
| B46 | 三元提升 if/else 语句（多单元） | (a) | 判定位块若其值被同块后续 STORE/RETURN 消费（栈事实）则为表达式位，禁止 IfRegion 语句路径接管 | **P1** | r7/r8 残留逐位持平 |
| B47 | await × 三元臂（3 单元） | (a) | GET_AWAITABLE/SEND 块归属 POP_JUMP 对内臂块集（区域成员关系），禁止外提 | P2 | 同上 |
| B48 | augassign × 三元 RHS 操作符丢失（多单元） | (a) | AugAssign 装配消费 STORE 前最近 BINARY_OP 的 oparg 操作符；禁止 TernaryRegion 固定 `x = x + (t)` 模板 | **P1** | r7/r8 同签名双实证 |
| B49 | for-else else 体三元增强赋值（1 单元） | (a) | else 臂块集 = 循环归约后汇合块非回边前驱集；体语句按块归属完整发射 | P3 | 同上 |
| B50 | try sections 宿主尾段归属（1 单元） | (a) | 尾随块前驱仅含 finally 域末块 → 归 finally 域；多前驱汇合块禁止复制到多域 | P2 | 同上 |
| B51 | if 三元链复合值（1 单元） | (a) | 同 B46 + elif 臂内复合值 C1 局部消费 | P3 | 同上 |
| B52 | 链式比较 × 三元操作数（2 单元） | (a) | 链节操作数位三元块不得越出 COMPARE_OP 栈位（同 B42） | P3 | 同上 |
| B53 | dict 嵌套三元值（1 单元） | (a) | BUILD_MAP 键值栈序 + 三元臂块归属（同 B46） | P3 | 同上 |
| B56 | assert 原生形态降级族（多单元） | (a) | LOAD_ASSERTION_ERROR+RAISE_VARARGS 框架块序列为 assert 原生标识（块末 opcode 事实）；幻影 else 源无真实控制边则拒绝生成 else 臂 | P2 | r8 REVIEW §5 |
| B57 | for 可迭代位三元吞前导语句（1 单元） | (a) | FOR_ITER 块是循环头（回边目标事实）；三元区域抢占不得越过循环头边界 | P2 | 同上 |
| B58 | raise 异常类三元整句蒸发（1 单元） | (a) | RAISE_VARARGS 栈输入块属语句块序列；表达式区域归约失败禁止静默 pass，必须回退通用语句路径 | P2 | 同上 |
| B59 | with 体首赋值蒸发（1 单元） | (a) | with 体切分按块归属完整发射；体首块 STORE 目标 ≠ withitem 目标寄存器则归体语句 | P2 | 同上 |
| B60 | match mapping **rest 幻影解包（1 单元） | (a) | MATCH_MAPPING/GET_LEN/UNPACK_SEQUENCE 框架块为模式装配输入（区域成员关系），禁止外提为体语句 | P3 | 同上 |
| B61 | for-else else 体线性外提 + break 蒸发（1 单元） | (a) | else 体 raise 块前驱集仅指循环汇合块 → 归属 else 臂；break 终结块后继 = 循环出口块保留 | P3 | 同上 |
| B62 | return(call+BoolOp) 尾语句蒸发→裸 Expr（1 单元） | (a) | RETURN_VALUE 前 CALL+JUMP 链块为 return 表达式输入，装配必须消费至 RETURN_VALUE（C1） | P3 | 同上 |
| B63 | 空 try/finally 后非纯常量尾随段蒸发（1 单元） | (a) | B68 `_b68_is_tryfin_tail_releasable` 释放门控扩展：尾随块存在真实语句前驱链（前驱 = finally 域末块且非纯常量 return）时禁止释放 | P2 | rv8 实测 6/7 |
| B64 | with 体空 try/finally 尾随 return（with_body_tryfin_chain） | **已封闭** | Round 9 B68 修复覆盖；本轮实测 rv8_02 = 6/7（该单元 MATCH） | — | 从残留名单划除 |
| B65 | 链式赋值 × 嵌套 BoolOp 值（1 单元） | (a) | 多目标 STORE 序列共享值栈；值含 JUMP_IF_FALSE_OR_POP 嵌套时按 B44 判据消费，消费点错位即链目标丢失检测 | P2 | rv8 实测 |
| B69 | if 臂内空 try/finally 吞尾随 return + 结构倒置（1 单元） | (a) | 臂归属 = 区域成员关系（臂内块前驱链止于臂头）；if 区域子节点序按块线性序，禁止 try/finally 与宿主倒置 | P2 | rv9 实测 |
| B70 | while True + with 整体宿主幻影 break（1 单元） | (a) | 幻影 break 检测：源块集无 is_break 语义块（BlockSemantics 事实）时禁止注入 break 终结块 | P2 | rv9 实测 |
| B11-R2 | r4_or4_and2 1/2（or4_and2 嵌套组合） | (a) | B1/B44 同族，随 B1 双入口封闭自然闭合 | P3 | round4 残留逐位持平 |
| R-1 | B68 门控 machinery 集与 finally:continue/break 理论重叠 | **升格 B71** | 本轮实证 2/4 失败 → B68 门控扩展：finally 体仅含循环控制终结块（BlockSemantics.is_break/is_continue）时释放判据显式排除 | **P1** | r10_finloop.json |

### 4.2 (b) 不可达清单：空（论证）

全部 29 项登记破口的失败机制均为**装配/归属/收集判据缺口**（语句装配顺序、块归属、区域边界、声明发射），其判别所需事实——块末 opcode、前驱/后继集合、异常表区间、区域成员关系、指令 opcode/oparg、code object 元数据（co_varnames/co_freevars/co_cellvars）——在 pyc 中**全部原样保留**。唯一接近「不可恢复」的候选是 B72 中 `global x` 声明在无读写歧义时被 3.11 编译为零指令（module 级提升噪声），但该声明的**语义事实**仍可由 STORE_GLOBAL opcode 与 code object 元数据完全重建（本轮 n10_03/r10_12 全 MATCH 证明发射路径存在），故不构成不可达。**无降级项。**

---

## §5 新破口登记（B71–B75，编号续接 B70）

全部破口状态 = 已定位（归因 d8246a8e 逐字节同败）；本轮无修复，交 fix 批按 §4 判据草案认领。

| 编号 | 机制 | 失败单元 | 优先级 |
|---|---|---|---|
| **B71**（R-1 升格） | finally 体仅含循环控制流：fin_continue = try 体 `raise ValueError(r)` 蒸发为 pass + 幻影 elif + continue 双发；fin_break = `break` 蒸发为 pass + `return total` 从循环体提升至 finally 域尾（循环语义破坏） | r10_21 ×2 | P1 |
| **B72** | nonlocal 声明发射缺失：孙代闭包（深度 ≥2）s3/s4 全丢 nonlocal；global+nonlocal 混合宿主链 layer2/layer3 全丢（global 保留）；另 global 声明被提升至模块层（字节惰性噪声，不单独计败）。语义破坏 = 闭包写降级 UnboundLocalError。判据 = 按 code object 元数据（co_freevars/co_cellvars）+ STORE_DEREF/STORE_FAST/STORE_GLOBAL opcode 重建每函数作用域声明集 | r10_14 ×3 + r10_16 ×3 = 6 | P1 |
| **B73** | try 四段全 × import 宿主：finally 段 import 泄漏进 except 臂 + 复制保留于 finally + handler 内 return 剥除（B50/B32 族 import 宿主变体） | r10_04 ×1 | P2 |
| **B74** | match case 体首 import 宿主：case guard 幻影注入（`if not v > 0`）+ 幻影 `else: continue`（B16/B56 族变体） | r10_06 ×1 | P2 |
| **B75** | try 宿主 global 声明 + 尾随 return 与 finally 条件段归属错位：`return CACHE[key]` 蒸发为裸表达式 + finally 条件体提升注入 try 主臂/except 臂（幻影 if/else 双臂）（B50/B32 族变体） | r10_15 ×1 | P2 |

---

## §6 合规审计结论

| 红线 | 实测 | 结论 |
|---|---|---|
| 零代码修改 | `git diff --stat -- core/ parsers/ scripts/ pycdc.py` = 空 | PASS |
| 单 BOM | region_analyzer.py / region_ast_generator.py 头字节 = `ef bb bf` | PASS |
| 零插桩残留 | core/**/*.py grep `R10DBG|_probe_r|_patch_dbg|_R23N20_DEBUG|R9DBG` = 0 命中 | PASS |
| OK 产物零手改 | 全部 r10_*/n10_* OK.py 由 `pycdc.py -o` 直接生成，无编辑器触碰 | PASS |
| worktree 清零 | 归因 worktree `D:/Temp/r10_rev` 已 `git worktree remove`；仓库仅剩 3 个前轮遗留 worktree（非本轮创建，如实登记交主代理处置） | PASS |
| 命令时限 | 全部命令 ≤300 秒（pyc_verify 单批 ≤1 秒） | PASS |
| 禁止全量 402 | 未运行 | PASS |

---

## §7 产出物清单

- 本报告：`.trae/specs/harden-completed-forms-10rounds/rounds/round10/REVIEW.md`
- 验证输出：`rounds/round10/r10_import.json`（26/28）、`r10_scope.json`（33/40）、`r10_finloop.json`（2/4）
- 探针：`test_repros/round10/` 17 文件组（r10_01..06、r10_11..16、r10_21 + n10_01..04，各含 .py/.pyc/OK.py）
- 临时证据目录 D:\Temp\r10_ev\ 用后即删；归因 worktree 已清零
