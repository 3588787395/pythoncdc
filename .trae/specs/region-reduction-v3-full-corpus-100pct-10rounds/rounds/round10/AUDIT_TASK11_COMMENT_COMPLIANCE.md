# R10 / Task 11.1 — 注释 vs 代码 不一致登记表（AUDIT-ONLY，零改动）

> 本票只做登记，不做修复。`core/` 下两文件在审计全程 **未被本 agent 触碰**（含 docstring）；
> 唯一新增文件即本文。审计手段为静态 + `ast`，未 import `core`、未跑反编译流水线。

## 0. 封表时点与字节基线（本表所有数字的适用时点）

| 项 | 值 |
|---|---|
| 封表时点（本地墙钟） | **2026-10-08 10:50:18 首表 → 11:23:17 复核重哈希一致** |
| `core/cfg/region_analyzer.py` | 2 058 547 B / 32 337 行 / sha256 前缀 **`38a1d5142d13`** |
| `core/cfg/region_ast_generator.py` | 3 715 383 B / 59 108 行 / sha256 前缀 **`e9a8f65f6451`** |
| 两文件 vs `git HEAD` | `git status --short` 对这两条路径 **空输出**（= 工作树 == HEAD，本票读数即 HEAD 读数） |
| 读取方式 | `open(..., encoding='utf-8-sig', newline='')`（BOM + CRLF），`ast.parse` + 行切片 |

⚠ 其它 agent 正在同树作业：**行号只在上述 sha256 前缀的字节下成立**；任何一方改动 `core/` 后本表锚点即失效，须按 §7 命令重跑。

## 1. 普查口径（范围＝全家族，非抽样）

目标族：`_identify_*`、`_is_*`、`_find_*`、`_compute_*`、`_split_*`、`_generate_*region*`、
`_if_generate_*`、`_loop_generate_*`、`_try_*`；枚举方式＝`ast` 遍历 **所有 ClassDef 直属函数**
（`census.py`；类外闭包 def 单独登记于 §1.3）。

### 1.1 族 × 文件 × 六项完整度

| family | `region_analyzer.py` | `region_ast_generator.py` | total | has docstring | 六项齐(严格①–⑥) | 部分 | 零项 | 六词齐(宽松) | C1/C2/C3 |
|---|---|---|---|---|---|---|---|---|---|
| `_identify_*` | 12 | 0 | 12 | 12 | 1 | 0 | 11 | 12 | 2 |
| `_is_*` | 43 | 16 | 59 | 33 | 2 | 0 | 57 | 2 | 3 |
| `_find_*` | 17 | 4 | 21 | 14 | 0 | 1 | 20 | 2 | 2 |
| `_compute_*` | 5 | 2 | 7 | 5 | 1 | 0 | 6 | 1 | 1 |
| `_split_*` | 0 | 5 | 5 | 5 | 1 | 0 | 4 | 1 | 1 |
| `_generate_*region*` | 0 | 3 | 3 | 3 | 1 | 0 | 2 | 1 | 1 |
| `_if_generate_*` | 0 | 6 | 6 | 4 | 0 | 0 | 6 | 2 | 0 |
| `_loop_generate_*` | 0 | 4 | 4 | 2 | 0 | 0 | 4 | 0 | 0 |
| `_try_*` | 2 | 32 | 34 | 32 | 0 | 0 | 34 | 0 | 2 |
| **合计** | **79** | **72** | **151** | **110** | **6** | **1** | **144** | **21** | **12** |

分面读数（格式面 / 实质面 **分开**，禁止合并成「合规率」——`TASK11_COMMENT_AUDIT_BRIEF.md` 纪律）：

* **格式面**：严格 ①–⑥ 齐 = **6**，全名单（这 6 个同时也是 C1/C2/C3 三词同现者）：
  `region_analyzer.py:3054 _compute_arm_level_join`、`region_analyzer.py:25983 _identify_boolop_regions`、
  `region_ast_generator.py:3092 _is_return_none_join_block`、`region_ast_generator.py:3171 _is_region_internal_exit_sink`、
  `region_ast_generator.py:3978 _generate_region`、`region_ast_generator.py:15072 _split_arm_at_chain_exit`。
  部分命中 = **1**（`region_ast_generator.py:31443 _find_return_chain_via_successors`，5/6 缺③）；
  零命中 = **144**；**完全无 docstring = 41**（analyzer 29 + generator 12）。
  反例提醒：`_try_build_ternary_merge_consumer_expr`(48282) 有 C1/C2/C3 三词但**严格标记 0/6**，不得计入齐项。
* **实质面**：宽松六词齐 = **21**；C1/C2/C3 三词同现 = **12**。⇒ 与简报第 23-26 行一致：
  形状面缺口巨大，长度面不空洞（散文／字节码模式段存在）。
* **简报核对**：`_identify_*` 在 analyzer = **12**、在 generator = **0** —— 与
  `TASK11_COMMENT_AUDIT_BRIEF.md:6` 的实测 **一致**（本票复测，未沿用其数）。

### 1.2 逐方法花名册

151 行全量花名册（file / line / class / family / name / body_lines / has_doc / doc_lines /
strict_n / strict_items / loose_n / loose_items / clauses）落盘：
`D:/Temp/r11audit/roster.tsv`（由 `census.py` 生成）与 `D:/Temp/r11audit/census.json`（含 stamp + sha256）。
本文不转储 151 行（体积），需要时用 §7 的 `cat roster.tsv` 一条命令取。

### 1.3 族外闭包（上表未覆盖的面，实测补登记）

上表只统计 **类直属方法**。同一族正则还匹配到 **26 个函数体内的闭包 def**
（14 个在 `region_analyzer.py`，12 个在 `region_ast_generator.py`），它们不在 151 之内：

`region_analyzer.py` 1716 `_is_ternary_conditional_context`、2640 `_is_normal_flow_sink`、
20547 `_is_loop_continue_block`、20556 `_is_loop_break_block`、20801 `_find_containing_loop_body`、
21633 `_is_implicit_return_block`、23101 `_is_boolop_ternary_candidate`、
23104 `_is_not_ternary_boolop_pattern`、23215 `_is_ternary_block`、
24145 `_is_call_without_value_used`、24475 `_is_shared_return_merge`、
25464 `_is_statement_ternary_entry`、**25856 `_try_create_ternary_region`（区域决策类闭包，六项模板从未要求其交付）**、
28183 `_is_trivial_sink`；
`region_ast_generator.py` 243 `_is_duplicated_cleanup_exit_return`、3805 `_is_none_return`、
10044 `_is_setup`、15863 `_is_implicit_return_none`、18648 `_try_collect_c3`、21104 `_is_pass_like`、
21110 `_find_nested_ifregion_with_else`、26885 `_is_continue_like`、26919 `_is_break_like`、
31497 `_is_cleanup_only_no_return`、31537 `_is_cleanup_with_return`、31576 `_is_finally_copy_return`。

⇒ **普查口径必须写明**：本票「151」＝类直属；含闭包则族命中 **177**。二者不可混用。
闭包体的六项模板与断言对账 **本轮未做**（登记为未覆盖面，不是合规）。

## 2. 注释断言登记规模（不是抽样，是全家福的计数）

`claims.py` 对 151 个方法逐条抽取 docstring 句 + 体内注释（含行尾注释），按六类断言正则过滤：

| 指标 | 值 |
|---|---|
| 断言句总数 | **1381** |
| 有 ≥1 条断言的方法 | **101** / 151 |
| 零断言方法（多为无 docstring 的 `_try_*`/`_is_*` 小料） | **50** |
| GUARD（守卫/排除/拒绝/必须/禁止） | 549 |
| EXCLUSIVE（唯一/仅/只/一律/均不） | 462 |
| SCOPE（不限于/所有/任何/任意/顶级区域） | 335 |
| ENFORCE（保证/确保/已实现/覆盖） | 115 |
| INVARIANT（行为不变/逐字节不变/互不干扰/幂等） | 60 |
| NOMAGIC（无硬编码/零阈值/无名字白名单/无偏移） | 18 |

⇒ 1381 条不可能逐条手工了结；本票的做法是 **把可机械证伪的断言类全部证伪到底**，
每类给出「population / 命中 / 判定」三个数（§6 与 §7 的反哑炮测量），
剩下不可机械判定的留给后续工单面。

## 3. `COMMENT_OVERCLAIMS`（危险类：注释读起来像已封闭的守卫，代码留有静默豁免）

判定纪律：只登记 **能指出「哪一行代码使该断言不成立」** 的条目。凡因规则局部作用域
（句子只约束紧邻的那一条判据）而无法证伪的，一律降级到 §6 `MATCH` 并加注，不进本节。

| # | 锚点（file:line） | 注释断言（逐字） | 与之矛盾的代码事实 | 修正方向（单句） |
|---|---|---|---|---|
| CO-1 | `region_ast_generator.py:2819` 与 `:2825`（方法 `_split_subscr_operands`，def `:2812`） | 「逐个剥离最小完整后缀，**不依赖固定指令数**，因而能正确处理多指令容器…」／「剥离以 ``dis.stack_effect`` 为**唯一判据**」 | `:2863-2864` `if len(expr_instrs) < MIN_INSTRS_FOR_SUBSCR_ASSIGN: return None`，而 `:27` `MIN_INSTRS_FOR_SUBSCR_ASSIGN = 3` —— 方法入口有一条**固定 3 指令**的拒绝门，早于任何栈效应计算；「不依赖固定指令数」与「唯一判据」两句同时为假 | **改注释**：栈效应剥离这一判据本身为真，删去「不依赖固定指令数／唯一判据」的绝对措辞、改写为「入口另有 `MIN_INSTRS_FOR_SUBSCR_ASSIGN=3` 下界门」；该门是否判为 §2/G4 违规属工单面（证据见 §4.2、§5.3） |
| CO-2 | `region_ast_generator.py:54911-54913`（CJB 入口形态注释，所在方法 `_generate_block_statements_body` def `:52105`） | 「消费端在 `generate()` 顶层区域循环按 `region.entry` 身份配对，包裹成 `if <守卫>: <extent 单元>`，**替代此处对条件的静默丢弃**」 | 「替代」只在一条分支上成立，注释却是无条件陈述：①`:54899` `if _cjb_pend_key is not None and _cjb_pure_cond:` —— `_cjb_pure_cond` 为空时（整段被判为前导语句，`:54866-54867` 把 `_cjb_cond_expr` 兜底成 `Constant True`）**不登记记录**，`:54920-54921` 直接 `return stmts`，条件仍被静默丢弃；②`:54891-54894` 的 else-entry 臂把 `_cjb_skip_inline_if=True` 而 `_cjb_pend_key` 保持 `None` ⇒ 同一条 return，**永不**登记；③唯一消费端 `:1859-1877` 的 `continue`（`:1863-1869`）先于读记录（`:1874`），记录可孤儿化——本文件 `:48445` 自证「此形态下 wrap 记录必然孤儿化（顶层循环到 fall-through 入口区域时 allgen 直接 `continue`）」 | **改注释**（措辞降为「仅 then-entry ∧ `_cjb_pure_cond` 非空时替代静默丢弃；else-entry 与 allgen-continue 两径仍丢弃」），**代码侧另开工单**补 else-entry 臂登记与孤儿记录兜底消费——`:48445` 已承认孤儿形态存在，注释却把它写成已封闭 |

**本类合计 = 2 条**（另见 §3.1：同段注释中确证为真的半句，防整段判假）。

### 3.1 CO-2 同一段注释里 **为真** 的半句

| 半句（逐字） | 使之为真的行 |
|---|---|
| 「[C3] 同层身份三重校验在 `_leading_guard_candidate` 内」 | `:38493-38497`（守卫①顶层 IfRegion + entry 同一对象）、`:38498-38501`（守卫②未生成）、`:38502-38515`（守卫③extent 归属）——三组确在该方法内 |
| 「BoolOpRegion 等其它区域类型**不命中**（行为不变）」 | `:38494` `if not isinstance(_R, IfRegion) or _R.entry is not then_entry: return False`——类型门真实存在，BoolOpRegion 进不来 |
| 「与 B1a 的 `_leading_operand` 属性**独立**」 | 两属性分别 `setattr` 于 `:54906` / `:38516`，读点分别 `:38305` / `:1874`，无同名覆盖 |
| 「撤销记录用 delattr 恢复块属性原状」（`:48456`，另一发射端注释） | `:48479` `delattr(_grd_then, '_leading_guard')` 实存 |

## 4. 两处「本轮已怀疑」的判定（票面点名，逐条给证）

### 4.1 (a) `region_ast_generator.py:19316-19323` 豁免循环 —— 判 `MATCH`，怀疑方向被证伪

注释逐字（`:19314-19317`）：「若将其标记为 generated_blocks，嵌套区域在父区域的块迭代中被跳过
（all(b in generated_blocks) 检查通过），造成代码块丢失。修复：检查 merge_block 是否为任何区域的
entry（**不限于顶级区域**），若是则不标记。」循环体：`:19319` `for _tr in self.regions:`
+ `:19320` `if _tr.entry is elif_boolop.merge_block:`。

**`self.regions` 不是顶级列表**，四条独立证据（行号在本票 sha256 下）：

1. 生成端赋值点唯一：`region_ast_generator.py:770` `self.regions = self.region_analyzer.analyze()`
   （全文件 `self.regions =` 仅此一处 + `:372` 的 `[]` 初始化，实测全命中）。
2. `analyze()` 返回**扁平全集**：`region_analyzer.py:1932` `self.regions = all_regions`，
   `all_regions = all_phase12_regions + sequence_regions`（`:1851`），
   而 `all_phase12_regions` 显式含**嵌套**区域——`match_regions = match_regions + nested_match_regions`（`:1651`）。
3. 「顶级」是**另行派生**的：`region_ast_generator.py:1389`
   `top_level = [r for r in self.regions if r.parent is None]`；`:1614-1615` 更直接证明集合里存在
   `parent is not None` 的成员（`for r in self.regions: if isinstance(r,(TernaryRegion,MatchRegion)) and r.parent is not None:`）。
4. 生成端为孤儿块新建的 BASIC 区域也**回灌进同一列表**：`:1752-1753`
   `top_level_regions.append(_basic_region)` 紧跟 `self.regions.append(_basic_region)`
   ⇒ 「任何区域」连合成区域也覆盖。

⇒ **结论：注释正确、怀疑错误**；被误的是「`self.regions` 只含顶级区域」这一前提。
判 `MATCH`，使之为真的行 = `region_analyzer.py:1932` + `region_ast_generator.py:1389`（派生式）+ `:19319`（循环容器）。
**修正方向：代码与该注释都不必动**；要改的是工单/简报里的那句前提。
（附带登记：同一方法 `_if_generate_elif_chain` 内同型第二处 `:19760` 亦迭代 `self.regions`，同判 `MATCH`。）

### 4.2 (b) `MIN_INSTRS_FOR_SUBSCR_ASSIGN` 定义/使用普查 + docstring 是否承认 §2/G4

| 项 | 实测 |
|---|---|
| 定义 | `region_ast_generator.py:27` `MIN_INSTRS_FOR_SUBSCR_ASSIGN = 3  # value + container + index 三指令构成下标赋值 a[b]=c` |
| 兄弟常量 | `:28` `MIN_INSTRS_FOR_CHAIN_ASSIGN_PATTERN = 3  # value + COPY + first_store 三指令构成链式赋值 a=b=c`（同为 3 指令门，票面未列，本票补登记） |
| 使用点（扫全 `core/` 树，非两文件限定） | **6 处**：`:2863`、`:3535`、`:52856`、`:53079`、`:53205`、`:56805` —— 与票面 6 个锚点 **逐一对上，行号未漂移**；两文件之外全树无其它命中 |
| 使用点所在方法 | `:2863`→`_split_subscr_operands`(2812，族内)；`:3535`→`_build_effective_stmts`(3493，**docstring 仅 1 行**)；`:52856/:53079/:53205`→`_generate_block_statements_body`(52105，**六项式 docstring 65 行**，通篇未提该门)；`:56805`→`_generate_stmts_from_instrs`(56748，40 行，未提) |
| 是否有 docstring 承认它是 §2/G4 违规 | **无一处承认**。族内唯一提到该阈值的地方是 `_split_subscr_operands`，而它在写「三指令」的同时**否认依赖固定指令数** ⇒ 判入 CO-1；其余 5 点所在方法对此门**完全沉默** ⇒ 判入 `CODE_UNDOCUMENTED`（§5.3） |
| 性质判定（留给工单面，非本票裁决） | 该常数是 STORE_SUBSCR 的**操作数下界**（三操作数），与 §2.2 禁的「深度/计数**上限**」方向相反；但 `:52856/:53079/:53205/:56805` 以 `len(...) >= 3` 作**放行门**，落入 §2.2 关注的计数判据面，是否计违规需按 `rules.md` §2 释义裁决 |

## 5. `CODE_UNDOCUMENTED`（代码里有真门，docstring 未认领 ⇒ 违反六项模板与 §2 反模式自检）

计数口径：**按门（gate site）计，不按方法计**；同一方法多个门分别计。

### 5.1 CU-1 硬编码**深度**门（§2.2 禁面），docstring 全沉默 —— **10 处**

| 锚点 | 门 | 所在方法（docstring 行数） | 修正方向 |
|---|---|---|---|
| `region_analyzer.py:2763` | `if depth >= 3: continue` | `_compute_merge_from_jump_targets`(37) | 改注释认领 + 工单评估该 BFS 界可否由支配性质取代 |
| `region_analyzer.py:6499` | `while _a_frontier and _a_depth < 4:` | `_find_loop_else`(71) | 改注释认领（该方法是 C3 登记点，⑥项须写明此界） |
| `region_analyzer.py:8190` | `if start_block in visited or depth > 16: return None` | `_find_async_with_return_path`(14) | **改代码优先**：命中即 `return None` 是静默豁免面，深度界语义未定义 |
| `region_analyzer.py:17682` | `while cur is not None and cur not in seen and depth < 8:` | `_find_assertion_error_block`(21) | 改注释认领（docstring 已述原则 4 却未述此界） |
| `region_ast_generator.py:15787` | `if _ft3_depth > 8:` | `_if_generate_full_elif_chain`(56) | 改注释认领 |
| `region_ast_generator.py:16546` 与 `:16562` | `if depth <= 1:` ×2 | `_try_build_method_call_chained_compare`(11) | 改注释认领（同族门在 `:16420` 已被 docstring 认领 ⇒ 只这两处漏） |
| `region_ast_generator.py:16659` | `if depth <= 1:` | `_try_build_literal_middle_from_blocks`(15) | 改注释认领 |
| `region_ast_generator.py:16925` | `if depth <= 1:` | `_try_build_attr_middle_from_blocks`(5) | 改注释认领 |
| `region_ast_generator.py:21704` | `while _queue2 and _depth2 < 32:` | `_if_generate_normal`(**无 docstring**) | **改代码面优先登记**：方法 0 docstring，是简报 §二 第 2 类「代码有、注释无」的最大单点 |

（剔除两条同族命中：`region_analyzer.py:23874` `if _r67_depth < 0:`、
`region_ast_generator.py:58607` `if self._loop_depth <= 0:` —— 是**符号谓词**不是上限，不计入。）

### 5.2 CU-2 硬编码**计数**门，docstring 与邻近注释**双沉默** —— **8 处**

| 锚点 | 门 | 所在方法（docstring 行数） | 修正方向 |
|---|---|---|---|
| `region_analyzer.py:6346` | `if _r03_none_count >= 3 and _r03_has_precall: return None` | `_find_loop_else`(71) | 改注释认领；「3 条 LOAD_CONST None」是语料经验值，工单面按 §2.2 复审 |
| `region_analyzer.py:15775` | `... for i in rest[:3]) if len(rest) >= 3 else False` | `_is_wildcard_match_block`(25) | 改注释认领（窗口宽度 3 未述） |
| **`region_analyzer.py:20076`** | **`if len(_8_test) > 25: merge = else_succ`** | `_identify_conditional_regions`(139) | **改代码优先**：25 直接翻转 merge 选择，邻近注释（`:20050-20072`）通篇未提，全票未发现任何文档认领 |
| `region_analyzer.py:30362` | `if first_ft and len(first_ft.instructions) <= 3:` | `_is_nested_if_else_pattern`(**无 docstring**) | 补该段实质（含六项） |
| `region_ast_generator.py:27487` | `if len(_target_meaningful) >= 3 and ...` | `_try_generate_conditional_break_or_continue`(60) | 改注释认领 |
| `region_ast_generator.py:31655` | `if len(remaining) < 4: continue` | `_find_return_through_cleanup_chain`(17) | 改注释认领（`LOAD_CONST/STORE/DELETE` 四指令形状应写在⑤项） |
| `region_ast_generator.py:47413` | `if len(_reg_stack) >= 3:` | `_try_build_ternary_store_assign`(13) | 改注释认领 |
| `region_ast_generator.py:58807` | `if len(instrs) < 3: return` | `_try_deferred_return_in_loop`(32) | 改注释认领 |

（剔除：`region_ast_generator.py:16703` 的命中来自 docstring 内示例文本 ``11 >= len(s) >= 9``，非代码门——
登记为**仪器假阳性**；§7 的 `gates.py` 需加 docstring 行屏蔽，复跑者以此为已知噪声。）

### 5.3 CU-3 `MIN_INSTRS_*` 门所在方法的 docstring 沉默 —— **5 处**

`:3535`(`_build_effective_stmts`，1 行)、`:52856`、`:53079`、`:53205`
（同在 `_generate_block_statements_body`，65 行**六项式** docstring 逐条列了 5 类守卫却未列此门）、
`:56805`(`_generate_stmts_from_instrs`，40 行)。
修正方向：**改注释**（在③「唯一归属判定」段写明下界门与其数值）；门本身是否 §2/G4 违规由工单面裁决。
注：`_generate_block_statements_body` / `_build_effective_stmts` / `_generate_stmts_from_instrs`
**不在 151 花名册内**（方法名不匹配九族正则），此三处缺口属**口径外**，本票单列、不并入 §1.1。

### 5.4 CU-4 区域类型豁免分支无 docstring 认领 —— **4 处**

`region_ast_generator.py:8064`(`_loop_generate_while`，无 docstring)、`:8303`(`_loop_generate_body`，1 行)、
`:21114` 与 `:21365`(`_if_generate_normal`，**无 docstring**)。
四条均为 `isinstance(...) or …` 型**让位/豁免**判据（正是 C3「必须显式守卫排除/认领」的面），
③④⑤项全部缺席。修正方向：**补注释**（先实质后模板），不改判据。

### 5.5 CU-5 §2.1 G3 前缀名实不符 —— **2 处**（族普查口径外，本票补登记）

| 锚点 | 方法 | 事实 | 修正方向 |
|---|---|---|---|
| `region_ast_generator.py:20171` | `_merge_block_is_then_exclusive` | 方法**不 merge**，只**判定**（返回 bool），名字却命中 §2.1 禁用前缀 `_merge_`；docstring 声明「非深度硬编码」但从未认领命名条款 | **改代码面**（更名为判定式命名）；注释侧无可补 |
| `region_ast_generator.py:41539` | `_merge_block_is_loop_back_edge` | 同上：返回 bool 的谓词带 `_merge_` 前缀 | 同上 |

（两文件全量 `def` 扫描：`_merge_` 前缀命中 **2**；`_fix_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 命中 **0**。）

### 5.6 模板级缺口（不计入上列门数，避免重复计数）

`_identify_*` 族 **11/12 零六项标记**（简报 §一 表逐条复核成立）；全族 **144/151 零严格标记**、
**41/151 完全无 docstring**（analyzer 29 / generator 12），其中同时含 CU-1/CU-2/CU-4 真实门的
`_if_generate_normal`、`_loop_generate_while`、`_is_nested_if_else_pattern` 三个「裸门方法」
是补六项的最高优先目标。

**本类合计 = 10 + 8 + 5 + 4 + 2 = 29 处**（§5.6 的模板面另计，不重复入数）。

## 6. `MATCH`（仅给样本数，不转储）

**已判定并证实的 MATCH 样本 = 101 条**，构成：

| 子面 | 样本数 | 判定手段（可复跑） |
|---|---|---|
| 封闭守卫型否认句（「零阈值/无名字白名单/无偏移/无深度…」）与同体代码不相违 | **31** | `nomagic2.py`：31 个带否认句的方法 × 4 轴（NAME/OFFSET/DEPTH/COUNT）扫描；机器初判 3 条矛盾经作用域复判后**全部撤销**（理由见下） |
| 「拒绝/排除 X」句中 X 的字面量或区域类型确在判据体内 | **56** | `rejects.py` + `table.py` 反哑炮测量：拒绝句 population **177**，携带 ASCII 字面量/类型名 **56**，其中「体内找不到」者 **0** ⇒ 该类无 dangling guard |
| 唯一性/所有权断言经站点计数证实 | **9** | `sole.py`（29 条唯一性断言中可解析标识符者）＋手工：`_split_arm_at_chain_exit` 全文 1 个调用点（`:15745`）、`_leading_guard` 全文 1 个读点（`:1874`）、`_boolop_member_is_loop_condition_entry` 1 读点、`:19626` 唯一消费点 1 命中、§4.1 四证、§3.1 四条真半句 |
| 「无新增 self 状态／不认领任何块」断言：写点确在被约束规则的行段之外 | **5** | `stateclaims.py`：5 个方法命中「声称无状态 ∧ 体内有写点」；逐条比行距后判**规则局部作用域成立** ⇒ `MATCH`（加注：若按整法读即成 overclaim，交文档主裁决，本票不擅自升格） |

**未判定面（诚实登记，不得当合规）**：1381 条断言句减去上述已了结者 ≈ **1280** 条仅完成普查
（分类计数见 §2）；其中 GUARD/ENFORCE/INVARIANT 三类**不可机械证伪**，
须按简报 §二「逐个方法读码写实质」流程处理，属后续票。

机器初判 3 条 overclaim 的撤销理由（写明以免后人重踩）：
`_find_loop_else:6291` 与 `_identify_conditional_regions:19310` 的否认句**语法上只约束紧邻判据**
（「识别条件（只读本块自身字段，无…计数启发）」），而命中的 `>=3` / `>25` 门位于另一条规则的行段内
⇒ 不构成注释与代码相违，转为 §5.2 `CODE_UNDOCUMENTED`；`_is_nested_if_else_pattern:30300` 同理。

## 7. 如何复跑（全部产物幂等、只读、单条命令 < 300 s）

```bash
cd /d/admin/.qoder/worktrees/app/f557fd/pythoncdc-main
mkdir -p /d/Temp/r11audit
python -X utf8 /d/Temp/r11audit/census.py         # §1.1 族表 + roster.tsv + census.json(含 stamp/sha256)
python -X utf8 /d/Temp/r11audit/claims.py         # §2 1381 条断言句登记册 -> claims.json
python -X utf8 /d/Temp/r11audit/rules_census2.py  # §4.2 MIN_INSTRS 全 core/ 普查 + G3 前缀 + len 门
python -X utf8 /d/Temp/r11audit/gates.py          # §5.1/§5.2 深度与计数门 × docstring 认领列（markdown）
python -X utf8 /d/Temp/r11audit/nomagic2.py       # §6 封闭守卫否认句 vs 同体代码（4 轴）
python -X utf8 /d/Temp/r11audit/rejects.py        # §6 「拒绝 X」句 X 是否在体内
python -X utf8 /d/Temp/r11audit/sole.py           # §6 唯一性断言标识符站点计数
python -X utf8 /d/Temp/r11audit/stateclaims.py    # §6 「无新增 self 状态」断言 vs 写点
python -X utf8 /d/Temp/r11audit/sitecheck2.py     # §4.2/§5.1 逐个门：所在方法 + docstring 是否认领
python -X utf8 /d/Temp/r11audit/table.py          # §1.1 markdown + 反哑炮 population 复测
python -X utf8 /d/Temp/r11audit/sx.py DOC  analyzer  3054     # 取任意方法 docstring（utf-8-sig + ast）
python -X utf8 /d/Temp/r11audit/sx.py LINE generator 38472    # 取任意锚点所属方法全文
python -X utf8 /d/Temp/r11audit/sx.py GREP generator "_leading_guard" 0
cat /d/Temp/r11audit/roster.tsv                   # §1.2 全量花名册（151 行）
# §1.3 闭包普查（本轮实测 26）：ast.walk 全树取全部 def，减去「ClassDef 直属」集合，再按九族正则匹配
# 封表一致性自检（前缀必须仍是 38a1d5142d13 / e9a8f65f6451，否则本表锚点全部作废）
python -X utf8 -c "import hashlib;[print(p,hashlib.sha256(open(p,'rb').read()).hexdigest()[:12]) for p in ['core/cfg/region_analyzer.py','core/cfg/region_ast_generator.py']]"
git status --short -- core/cfg/region_analyzer.py core/cfg/region_ast_generator.py   # 只读
```

产物目录 `D:/Temp/r11audit/`：`census.json`、`roster.tsv`、`claims.json`、`gates.json`、
`gate_register.json`、`nomagic.json`、`nomagic2.json`、`sole.json`、`rejects.json`、
`deadguard.json`、`stateclaims.json`、`findings.json` 与上述脚本本体。

纪律遵守：全程 `python -X utf8`，**未设置** `PYTHONIOENCODING`；未 import `core`；未跑流水线；
未在 `core/` 下写入任何字节（含 docstring）；未执行任何 git 写命令（仅 `git status`）。
