# 落地机制标记清单（`core/cfg/*.py` 内 `[Bn-V3Rn]` 标记族）

> 目的：为 L3 机制层攻击提供**可数、可抽检**的机制面（每族 ≥1 抽检点）。
> 取证方式：只读扫描 `core/cfg/*.py` 全文 + 读标记点注释原文；所有计数为本次实测，**不沿用台账声称值**。

---

## 1. 计数口径（先声明，便于复算与反驳）

| 口径 | 正则 | 本次实测合计 | 备注 |
|---|---|---|---|
| **A（本文主口径）** | `\[B\d+[A-Za-z]*-V3R\d+`（按出现次数计） | **191** | 允许破口号带字母后缀（B61a…B61k、B70c…B70j）；实测每个标记独占一行 ⇒ 与行计数等价 |
| B（严格） | `\[B\d+-V3R\d+\]` | **123** | 只认纯数字破口号，漏掉 68 处带后缀标记 |
| 台账口径 | — | 声称 **174** | **不可复现**，详见 §5 |

复算命令（仓内可复现）：

```
git grep -o -E "\[B[0-9]+[A-Za-z]*-V3R[0-9]+" HEAD -- "core/cfg/*.py"
```

---

## 2. 逐轮 × 逐文件计数（口径 A，本次实测）

| 文件 | R2 | R3 | R4 | R5 | R6 | R7 | R8 | 合计 |
|---|---|---|---|---|---|---|---|---|
| `core/cfg/region_ast_generator.py` | 34 | 19 | 10 | 25 | 6 | 15 | 6 | **115** |
| `core/cfg/region_analyzer.py` | 6 | 6 | 0 | 19 | 6 | 2 | 12 | **51** |
| `core/cfg/comprehension_generator.py` | 6 | 0 | 0 | 0 | 0 | 4 | 0 | **10** |
| `core/cfg/pattern_parser.py` | 0 | 0 | 0 | 7 | 0 | 0 | 0 | **7** |
| `core/cfg/code_generator.py` | 1 | 0 | 0 | 0 | 0 | 0 | 4 | **5** |
| `core/cfg/ast_generator_v2.py` | 0 | 0 | 3 | 0 | 0 | 0 | 0 | **3** |
| **逐轮合计** | **47** | **25** | **13** | **51** | **12** | **21** | **22** | **191** |
| 台账声称 | 47 | 25 | 13 | **34** | 12 | 21 | 22 | **174** |

> 逐轮数与台账**六轮逐位一致**，仅 R5 不符（51 vs 34）。逐轮数自该轮提交起即固定（`git grep` 于 ece1aab5/69132f55/71fda309/841e511e/8c088ef7/63520cb4/b6e634b7 各测得同一组值），即**不是后续轮次新增导致，而是当初计数口径不同**。

---

## 3. 在用破口号（`core/cfg` 内实测 54 个标记族 / 191 处）

| 轮 | 破口号（处数） |
|---|---|
| R2 | B43(1)、B78(3)、B98(34)、B123(9) |
| R3 | B56(1)、B69(3)、B73(2)、B82(1)、B87(4)、B131(3)、B133(2)、B134(5)、B135(2)、B136(2) |
| R4 | B47(3)、B112(8)、B128(2) |
| R5 | B61a(2)、B61b(3)、B61c(2)、B61d(1)、B61e(5)、B61f(1)、B61g(2)、B61h(2)、B61i(3)、B61j(2)、B61k(1)、B70(19)、B93(1)、B122(7) |
| R6 | B137(3)、B138(1)、B139(2)、B140(5)、B141(1) |
| R7 | B144(2)、B145(6)、B146(3)、B147(1)、B148(1)、B149(1)、B150(2)、B151(4)、B152(1) |
| R8 | B153(1)、B154(4)、B155(5)、B156(3)、B157(3)、B158(2)、B159(1)、B160(1)、B162(2) |

**B129–B162 区间内的「未落地 / 无标记」编号（如实登记，L3 须区分「登记」与「机制」）**：

| 编号 | 状态 | 依据 |
|---|---|---|
| B129、B130 | **仅登记，无落地机制**（R2 首攻 `r2synth1` 域外 5 单元，裁决归 R8） | rr-v3r02 提交说明；本次实测 `core/cfg` 内 0 处标记 |
| B142、B143 | **仅登记（稀窝，park 不追）**，无落地机制 | `rounds/round6/FIX.md:92-93`；`rounds/round8/REVIEW.md:139-140`；本次实测 `core/cfg` 内 0 处标记 |
| B161 | 判据**撤销并入 B162 的实现注记**，无独立标记 | `rounds/round8/REVIEW.md:101`（"B161 判据撤销并入本实现注记"）；本次实测 `core/cfg` 内 1 处提及、0 处 `[B161-V3R*]` 标记 |
| B153–B162 | R8 的 **10 项通用机制**（B161 撤销 ⇒ 实际落地 9 个编号 / 22 处标记） | `rounds/round8/REVIEW.md:15`（"本轮通用机制 10 项（B153–B162）"） |

---

## 4. 机制族清单（族 = 落地图；每族一行 + 每族触及文件 + 每个破口号一行机制说明）

### 族 R2 —— 条件合并块族（If / BoolOp / IfExp 的合并与短路链）
**触及文件**：`region_ast_generator.py`(34)、`region_analyzer.py`(6)、`comprehension_generator.py`(6)、`code_generator.py`(1)

| 破口 | 处数 | 机制（据标记点注释原文） |
|---|---|---|
| B98 | 34 | or/and 链前缀过滤与合并块归约的多点联动；含「AST 对象路径原判据 `hasattr(if_clause,'_node_type')` 恒 False ⇒ 括号守卫从未生效」这类**判据自身失效**的修复（`code_generator.py:5700`） |
| B123 | 9 | and 尾 IfExp 钻石操作数吸收（while 头链式比较 + IfExp 尾） |
| B78 | 3 | 嵌套三元宿主折叠（if / while / 值消费三宿主）：编译器把真值出口直连宿主目标、常量 orelse 臂折叠为直接跳转，分析层未及此形 |
| B43 | 1 | 链式比较钩子命中形判别：entry 命中 vs merge 命中（链内后续 COMPARE 段 vs 链外真操作数） |

### 族 R3 —— try / raise / assert 宿主族
**触及文件**：`region_ast_generator.py`(19)、`region_analyzer.py`(6)

| 破口 | 处数 | 机制 |
|---|---|---|
| B56 | 1 | 汇合块值延续 + RETURN 收尾：短路链值先与链首块残留栈经 merge 块的 BINARY_OP/CALL 拼接，再由 RETURN_VALUE 消费 |
| B69 | 3 | 例外：R66-diag1 E1 的「空 then 臂」判据改以**臂块指令**为准 |
| B73 | 2 | finally 体含条件段时，handler 内 return 路径上的「条件段副本头」中继块判定 |
| B82 | 1 | try 臂 finally 条件段副本**外置消费**（退化 try 体子型） |
| B87 | 4 | 重入复检（for_in_try）：上方前缀 flush 经 if 生成路径进入「前缀块所属的 TryExceptRegion」并整树生成，内嵌子循环被递归生成 |
| B131 | 3 | 外部前驱条件采纳门（底部闩锁存在性）：只有体携带条件反向跳转闩锁时 header 才可能不是条件块本身 |
| B133 | 2 | then 臂为 continue 汇聚（回跳循环头）时 merge 的取法修正 |
| B134 | 5 | 循环体外前驱的条件求值必须在循环体内被**逐迭代重检** |
| B135 | 2 | IfRegion → `ast.Assert`（assert 失败臂形态） |
| B136 | 2 | 栈效应判据：被跳过的 `PUSH_NULL+LOAD_*` 前缀必须是外层调用的 callee preload，跳过后净栈效应恰为 +1 |

### 族 R4 —— await 挂起链族
**触及文件**：`region_ast_generator.py`(10)、`ast_generator_v2.py`(3)

| 破口 | 处数 | 机制 |
|---|---|---|
| B47 | 3 | 三元臂值表达式：await 挂起链经链流合并重建臂值 |
| B112 | 8 | 上一显著操作码（跳过 PRECALL/CACHE 等编译器填充），供 CALL(0) 推导式区分同步 GET_ITER / async GET_AITER |
| B128 | 2 | 只读判定：await setup 块的挂起结果是否由 IfRegion 条件消费 |

### 族 R5 —— match-with 幻影族
**触及文件**：`region_ast_generator.py`(25)、`region_analyzer.py`(19)、`pattern_parser.py`(7)

| 破口 | 处数 | 机制 |
|---|---|---|
| B61a | 2 | IF_TRUE 族：or 守卫真值边与 case 体首断言检查跳过边同极性，鉴别改靠 **or 守卫结构签名**而非极性 |
| B61b | 3 | 前导 POP_TOP 允许多条（类模式失败链 MATCH_CLASS 双 COPY 协议） |
| B61c | 2 | case 体首融合块的**模式捕获材料切片**（体首块同时是嵌套区域条件块时） |
| B61d | 1 | case 体内 AssertRegion 分发缺口（assert 块此前落入 body_start 切片路径 → 断言语义丢失） |
| B61e | 5 | 种子后继筛选 + or 守卫臂链连续性（case 体块不是模式材料，旧实现把体块种进 worklist 推走守卫锚点） |
| B61f | 1 | or 守卫臂链归约（链行走已收敛 ⇒ 整链是 guard 材料而非 case 体） |
| B61g | 2 | 判据收窄为「本 case 的体块集」+「臂所属块 ∈ 体块集」 |
| B61h | 2 | 嵌套类模式类引用（unpack 槽位上的子模式 `int(a)`：类引用先于 MATCH_CLASS 装载） |
| B61i | 3 | 嵌套 match 的 merge 越出 with 体时的归属让位（由 with 后体块走查发射） |
| B61j | 2 | with 退出链 return 尾块的**重复发射**判定 |
| B61k | 1 | match 宿主于 for/with/try 时的 case 体内嵌 if（宿主先 Claim ⇒ 旧守卫一律跳过 IfRegion 创建） |
| B70 | 19 | 循环归属/出口分类族：同入口循环归属回退（WithRegion 优先级 > LoopRegion）、while True 自然回边、handler 保护区延伸否决、with 体内 if 的清理块过滤补口（B70g）、NOP 前导循环头链（B70h）、then 臂真路径出口分类（B70f/i）、无回边 while True + with break 的循环壳重建（B70j）、回跳目标经平凡前导块链达循环头（B70d）、占位体甄别（B70c） |
| B93 | 1 | with 跨体祖先判定（候选 WithRegion 的异常表体范围含本区域入口偏移 ⇒ 候选是祖先 with） |
| B122 | 7 | 模式比较材料隔离 / 入口同块去重 / 链首 subject 优先 / and-guard 链解析 / 嵌套字面量链 case 守卫提取 / or 组共享守卫 |

### 族 R6 —— 循环控制族
**触及文件**：`region_analyzer.py`(6)、`region_ast_generator.py`(6)

| 破口 | 处数 | 机制 |
|---|---|---|
| B137 | 3 | while True 体首 NOP 占位（体首 NOP 无语句可承载 ⇒ 发射 `while False: pass` 占位） |
| B138 | 1 | 回边块同时是带 else 的 IfRegion.merge_block 时不得并入 then 体 |
| B139 | 2 | 旋转 while 的 else 体（condition-false 目标）：即使以隐式 return None 收尾，含实际语句就不是纯尾返回 |
| B140 | 5 | except handler 体内的 break 块登记（偏移 → 块）；CPython 3.11 把 handler 内 break 编译为 POP_EXCEPT + JUMP_FORWARD(循环出口) |
| B141 | 1 | 宿主链 try→handler→with→match 时的 case 体**语义归属**（祖先 TryExceptRegion 先认领 ⇒ case 体退化为 pass） |

### 族 R7 —— 赋值 / 删除 / return / slice 族
**触及文件**：`region_ast_generator.py`(15)、`comprehension_generator.py`(4)、`region_analyzer.py`(2)

| 破口 | 处数 | 机制 |
|---|---|---|
| B144 | 2 | 独占可达的 break 落点识别（for-else 体以 raise/return 收尾形态） |
| B145 | 6 | 块是否为某循环登记的 break 落点（循环之后的代码）；R7 门禁首跑自捕获「过宽」后按 I.4 收窄为「跳转必须离开所属循环」 |
| B146 | 3 | 入口栈深非零的块（with 体首块形态）：按前驱链求真实入口深度后重做切分 |
| B147 | 1 | with 体内 assert 入口块的**前导语句消费**（`data = fh.read()` 归父序列而非 AssertRegion） |
| B148 | 1 | 值折叠算子族纳入「复合前缀」判据（BINARY_OP / BUILD_SLICE / BINARY_SUBSCR / COMPARE_OP / IS_OP / CONTAINS_OP / UNARY_* / FORMAT_VALUE） |
| B149 | 1 | 尾随「SWAP n; POP_TOP」栈深修正对的后置剥离（for/with 体内 return 时的迭代器/清理槽丢弃） |
| B150 | 2 | 「双臂 return + 单一共享 RETURN_VALUE 汇点」折叠为三元返回 |
| B151 | 4 | 链式比较之后仍有过滤项时的**续解析**（旧行为直接 return，丢弃 `and (flag or x % 2)` 后半段） |
| B152 | 1 | 「if 条件是三元表达式」形态的 if 体与 if 后兄弟语句复原 |

### 族 R8 —— 通用机制 10 项
**触及文件**：`region_analyzer.py`(12)、`region_ast_generator.py`(6)、`code_generator.py`(4)

| 破口 | 处数 | 机制 |
|---|---|---|
| B153 | 1 | 修复 `r810::r8_x_for_iter_ternary`（`total = 0` 与三元的 for-iter 前缀归属） |
| B154 | 4 | 三元作 for-iter 时**补括号**（代码生成侧；判据为 C1 只读节点类型 / C2 不改渲染路径 / C3 非 IfExp 形态） |
| B155 | 5 | 臂尾回边块（POP_EXCEPT 之后、以回边跳转终结）= 内联 finally 副本 + 显式 break/continue 跳转块；控制流应离开 handler 臂，不应沿回边走进外层循环体 |
| B156 | 3 | handler arm tail「inlined finally copy + back-edge jump」块 = 源码级显式 break/continue |
| B157 | 3 | **finally 归属唯一化**：同一 except handler 只归属保护跨度最小且包含它的 finally handler |
| B158 | 2 | C1：只读异常表条目 + 本区域 handler 入口集 + finally 副本 |
| B159 | 1 | 本区域 try 体整体由**嵌套 try 区域**承载时的 try 体末指令补齐（否则 try_body_max_end=0 ⇒ else 子句识别失效） |
| B160 | 1 | 推广为「纯跳转块」排除：try 体正常出口的 JUMP_FORWARD 块不是 else 子句 |
| B162 | 2 | 链式后继三元排除（merge_context 保持值链上下文）+ while-or 链完成判据改取**链尾** `chain[-1]`（B161 判据撤销并入本实现注记） |

---

## 5. 与台账的差异（L3 攻击面必须先解决的口径问题）

1. 台账数 **174**（`rounds/round8/WIKI_REVIEW.md:10`、`rounds/round10/VERIFICATION.md:21`、rr-v3r09/r10 提交说明）**不可复现**：本次实测口径 A = **191**。
2. 差异**只在 R5**：台账 34 vs 实测 51，差 **17**。算术重建：
   - R5 实测 51 = B70(19) + B93(1) + B122(7) + B61a–B61k(24)；
   - R5 自报数 **27**（`rounds/round5/FIX.md:159`、`:206`；rr-v3r05 提交说明同）= 51 − 24（未计 B61a–B61k 24 处）；
   - 台账 34 = 27 + 7（**B122 的 7 处被二次计入**）。
3. 结论：台账 174 与实测 191 差 17 = 24 − 7，与上述重建自洽。**174 不得作为基线事实引用**；后续台账（v9）须改用口径 A 的可复算口径（复算命令见 §1）。
4. 另注：rr-v3r04 提交说明称 R4 标记「25 行」，rr-v3r06 称 R6「11 处」，与实测 13 / 12 不一致 —— 同属**各轮自报数与树内实测不同源**的同一类问题，本表一律以树内实测为准。
