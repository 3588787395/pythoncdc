# ATTACK — L1 口径层攻击（分母 / 粒度 / 三态可判定性）

- **角色**：评审工程师（口径层攻击）｜**轮次**：round3（Task 3）｜**日期**：2026-10-21
- **被攻击对象**：`attain-true-completeness` v8 终读数 **完备 128 / 破口 0 / 零能力 0 = 100%**
- **攻击面**：spec.md 攻击分层表 **L1 口径层**（`spec.md:43`）
- **本轮不改**：core/cfg/**、tests/**、wiki/**、rules.md、前一规范目录；本文件 + `_scripts/` + `_out/` 为全部产出
- **可复现脚本**（全部保留）：`rounds/round3/_scripts/{denominator_audit,numerator_lexical_audit,variant_quantify,three_state_and_reconcile}.py`；输出 JSON 在 `rounds/round3/_out/`
- **复现命令**（PowerShell，≤300s）：
  `python -X utf8 .trae\specs\attack-completeness-claims\rounds\round3\_scripts\denominator_audit.py`
  `python -X utf8 .trae\specs\attack-completeness-claims\rounds\round3\_scripts\numerator_lexical_audit.py`
  `python -X utf8 .trae\specs\attack-completeness-claims\rounds\round3\_scripts\variant_quantify.py`
  `python -X utf8 .trae\specs\attack-completeness-claims\rounds\round3\_scripts\three_state_and_reconcile.py`

> **编号裁决**：本报告的临时破口号已被主代理统一注册表取代——见 ../round3/BREACH_REGISTRY.md（本报告临时号 → 正式号映射在注册表「来源临时号」列）。

---

## §0 结论摘要

> 攻击项编号约定：`AT-1N`（本轮 N=1..8）。三类结论：**击穿** / **未击穿且不可证伪** / **不可证伪**。

| id | 攻击命题（一句话） | 结论 |
|---|---|---|
| AT-11 | 分母 128 = Python 3.11 语言面 | **击穿** |
| AT-12 | 分母 128 是冻结产物（语言加形态不会漂移） | **击穿** |
| AT-13 | 分子「三路径存在（识别+归约+生成）」被实测 | **击穿** |
| AT-14 | 128 折叠掉「宿主×变体×深度」维度不构成实质缺口 | **击穿** |
| AT-15 | 三态（完备/破口/零能力）互斥且穷尽 | **击穿**（互斥成立、**穷尽不成立**） |
| AT-16 | 「行有深层探针且全绿 ⇒ 该行完备」 | **击穿** |
| AT-17 | 「零能力」与「破口」在实现中有形式化区分 | **不可证伪** |
| AT-18 | 「100%」蕴含「判定空间 62.72% 覆盖」不矛盾 | **未击穿且不可证伪** |

**总判**：v8 的 **100% 不成立为「完备性」结论**。它成立的唯一读数是「**词法存在性 128/128 + 25 行抽样探针全绿**」；分母本身既非语言面分区（缺 7 / 多 32 / 重复 31，独立覆盖增量 = 0）、也非冻结产物（随解释器漂移，3.12 ⇒ 96.24%），分子从未按「三路径」实测，完备桶按「无破口证据」判定 ⇒ **未被证伪的形态默认落入「完备」**。新登记破口 **B164–B171（8 项）**（F1 已占 B163，见 `rounds/round1/FINDING_F1_GLOBAL_NONLOCAL.md`）。

---

## §1 攻击项清单

| id | 攻击命题 | 方法 | 击穿判据 | 不可证伪判据 | 结论 | 证据 |
|---|---|---|---|---|---|---|
| AT-11 | 分母 97 ast 节点集 = 语言面 | 用 Python 3.11.7 `ast` 独立重算全类集（**不设大小写过滤**），剔除抽象基类/废弃别名/编译模式，再与工具规则对拍 | 存在「非独立语法项」或「语言面缺项」且 ≥1 | 两法完全一致且无冗余 | **击穿** | `_scripts/denominator_audit.py`：全类 131 → 真语法面 73；工具分母 97 = 65 大写语法 + 29 运算符/比较/布尔词法类 + 3 ctx 类；**缺 7 个小写真语法类**（`alias/arg/arguments/comprehension/keyword/match_case/withitem`，因 `n[0].isupper()` 被丢，`ExceptHandler` 却因大写而保留 ⇒ 划分依据是**字母大小写**） |
| AT-12 | 31 扩展形态 = 冻结产物 | 定位定义处 + 模拟解释器漂移（注入 3.12 已知类集重算） | 规则取运行解释器且 deny-list 失效 | 分母为写死清单且与解释器无关 | **击穿** | `tools/kb/syntax_coverage.py:92-107`（取 `dir(pyast)`，全文无 `sys.version_info` 断言）；`:82-83` deny-list 写 `'typevar'/'type_param'`（小写）而 ast 类名是 `TypeVar`/`TypeParam` ⇒ **两条 deny 项永久失效**；3.12 模拟：分母 97→**102**，总项 128→**133**，分子仍 128 ⇒ **96.24%** |
| AT-13 | 分子 = 三路径存在 | 复算分子并做「去注释/去字符串」三档分级 | 任一路径无测点，或分子只由词法命中构成 | 工具按识别/归约/生成分别有测点 | **击穿** | `tools/kb/syntax_coverage.py:113-120`（正则 `ast\.[A-Z]\w+` + **任意引号大写词**）、`:146-184`（`hint in all_text` 子串）；`_scripts/numerator_lexical_audit.py`：97 命中 = **43 个 `ast.X` 代码引用 + 54 个仅字符串字面量类型标签**，严格去字面量只剩 **22**；31 扩展形态中 **3 项（capture_pattern/or_pattern/value_pattern）的 hint 仅出现在注释** |
| AT-14 | 128 折叠变体维度不构成实质缺口 | 以判定空间为机器可读基准，逐行算 (form,variant,host,depth) | 空间条目数 ≫ 128 且行级探针不覆盖变体 | 空间条目数 ≈ 128 且逐变体有证 | **击穿** | 判定空间 **1556 条目 / 39 形态 / 299 (form,variant) / 1251 (form,variant,host)**；25 行声明变体 **279**，登记探针只触发 **118（42.3%）**；判定空间证据共触发 **227（81.4%）**；**24/25 行存在变体缺口** |
| AT-15 | 三态互斥且穷尽 | 读台账 §0/§2.2/§5.5 定义 + 全仓测点审计 | 存在落入「完备」却无任何证据的形态 | 空集被显式判为「未判定/不可判定」 | **击穿**（穷尽不成立） | `wiki/concepts/decompile-invariant-completeness.md:78-80`：完备=「三路径存在 ∧ **无破口证据**」（证据空集 ⇒ 完备）；`:197-199` 汇总 128/0/0；本轮实测：**零能力 0** 只由词法路径测试决定，**破口 0** 无任何机器测点（`three_state_and_reconcile.py`：全仓 39 个 .py 提及三态关键字，**状态赋值测点 0 处**） |
| AT-16 | 单元绿 ⇒ 完备 | 对 25 行登记探针用 `ast` 解析，检查行声明形态节点是否出现、变体谓词是否触发 | 存在行：登记探针**零**含该行形态 | 每行探针含该行形态且覆盖全部变体 | **击穿** | `_scripts/variant_quantify.py`（变体谓词取 `tools/completeness/jspace_generator.py:382-1077`）：**`slice` 行（REVIEW.md:52）登记探针 `r8v8rev3_b104_exprtail_battery.py` 的 `ast.Slice` 实例数 = 0**、10 变体触发 0 ⇒ **F1 同构第二例**；`global_nonlocal` 行 0/5（F1 已占 B163） |
| AT-17 | 零能力 vs 破口 有形式化区分 | 追两条判据的实现测点 | 两者的判定依据不同类且可机器判定 | 判定依据同类或纯人工 | **不可证伪** | 零能力 = 「任一路径缺失」，路径「存在」= 词法命中（`syntax_coverage.py:113-184`）；破口 = 「三路径存在 ∧ 不变式破坏有确证（锚点+机制）」，确证由人工台账给出（`decompile-invariant-completeness.md:79`、`:206+`）。二者区分依据是**证据种类**（词法 vs 人工），不是能力层级；「词法有、能力无」的形态**既非零能力也非破口**，默认落完备 ⇒ 现有判据体系不足以判定该攻击，转方法层 |
| AT-18 | 「100%」与「覆盖 62.72%」不矛盾 | 尝试把 128 分母项与 1556 空间条目对齐 | 存在无歧义对齐使二者可同时成立 | 无无歧义对齐 | **未击穿且不可证伪** | 25 行只对应空间 39 形态中的 25 个，**14 个 NEW 族无行**（AnnAssign/AsyncFor/AsyncFunctionDef/AsyncWith/Decorator/DictComp/ExceptStar/GeneratorExp/JoinedStr/Lambda/NamedExpr/PEP604Union/SetComp/Starred）；`ExceptStar` 整族 **96/96 未覆盖**（`rounds/round1/COVERAGE_BASELINE.md`）⇒ 空间口径与 128 口径**无共同坐标系**，既不能证真也不能证伪 |

---

## §2 分母正确性审计

### 2.1 (a) 97 个 ast 节点类型 —— 与语言权威对拍

**方法**：本机 Python 3.11.7（解释器即语言权威的同版本；语料侧另有 3.11 硬门，见 `baseline/judge_criteria.md:17`）。独立枚举 `dir(ast)` 的全部 AST 子类（**131 个，不设大小写过滤**；工具规则只取其中首字母大写的 112 个），逐类判定是否属语法面，再与 `tools/kb/syntax_coverage.py` 的规则复算对拍（复算结果 97 与已发布 JSON 一致 ⇒ 本脚本对工具规则忠实）。

| 类别 | 数量 | 说明 |
|---|---|---|
| `ast` 中 AST 子类总数（**不设大小写过滤**） | **131** | 工具规则只取 `n[0].isupper()` 的 112 个 |
| **真语法节点面**（剔除抽象基类/废弃别名/编译模式/运算符与 ctx 载荷类） | **73**（= 65 大写语法 + 7 小写语法 + 1 小写抽象基类 `excepthandler`） | 本轮独立重算 |
| 工具分母（`denominator_ast`） | **97** | 与已发布 JSON `denominator.ast_node_types = 97` 一致（复算 97 = 65 + 29 + 3 ✓） |
| **语言面缺项（missing）** | **7** | `alias`、`arg`、`arguments`、`comprehension`、`keyword`、`match_case`、`withitem` —— 因规则里的 `n[0].isupper()`（`tools/kb/syntax_coverage.py:92-94`）**被大小写过滤掉**（同类的 `ExceptHandler` 因首字母大写而留在分母内 ⇒ 划分依据是**字母大小写**而非语义） |
| **分母冗余（extra，非独立语法项）** | **32** | ① **29 个运算符/比较/布尔词法类**：`Add Sub Mult MatMult Div Mod Pow LShift RShift BitOr BitXor BitAnd FloorDiv Invert Not And Or Eq NotEq Lt LtE Gt GtE Is IsNot In NotIn UAdd USub`；② **3 个 ctx 类** `Load/Store/Del`（`skip` 只排除了基类 `operator/unaryop/cmpop/boolop/expr_context`，**未排除其子类** ⇒ 冗余 32 项由此进入分母） |
| **alias 处理** | 见下 | `DEPRECATED`（`:85-87`）9 项正确排除 Num/Str/Bytes/NameConstant/Ellipsis/AugLoad/AugStore/Param/ExtSlice；`NON_SYNTAX`（`:89-90`）5 项正确；**但 `skip`（`:81-83`）的 `'typevar'`/`'type_param'` 大小写错误 → 对 3.12 的 `TypeVar`/`TypeParam` 永久无效** |

**缺项 7 项的补偿情况**（`denominator_audit.py: dropped_but_recovered_as_extra_form`）：按名引用，`alias`→`star_import`、`comprehension`→`nested_comprehension`、`match_case`→`case_guard` 被 31 扩展形态以「形态」方式补回；`keyword`/`withitem` 仅被 `keyword_args`/`multi_context_with` 语义隐含覆盖；**`arg` 与 `arguments`（函数形参名 / 形参表：`def f(x: int = 1, *a, **k)`）在 97 与 31 中均无任何对应项** ⇒ **函数形参面无分母项**（新破口 B171）。

**文件:行**：
- 规则本体 `tools/kb/syntax_coverage.py:92-107`（`py311_nodes` 取 `dir(ast)` 中 `n[0].isupper()` 的类 → `stmt/expr/mod` 三段并集；① **大小写过滤丢 7 个真语法类**；② `expr` 只减 `skip`，**不排除运算符类与 ctx 类** ⇒ 冗余 32 项由此进入分母）；
- 抽象基类/载荷类未排除 ⇒ `skip` 缺 `operator` 子类与 `expr_context` 子类（`:81-83`）；注意 `skip` 里已有 `'operator'/'unaryop'/'cmpop'/'boolop'/'expr_context'` —— **只排除了基类，没排除其子类**，这是 32 项冗余的根因；
- 文档与实现不一致：docstring `:4-6` 与 JSON `source` 字段（`:198`）宣称「分母 = Python 3.11 ast 模块（语言权威）」，但代码取**运行解释器**的 `dir(ast)`，全文**无 `sys.version_info` 断言**（`Select-String` 实测 0 命中）⇒ 口径实为「运行解释器的 ast 类清单」。
- **已发布产物不可自证**：`docs/refactor/syntax-coverage.json` 只存**计数**（97/31/128/97/31/128/100%），**不含分母节点清单、不含扩展形态定义与 hint**（`denominator_audit.py: published_json_has_denominator_node_list = False`）⇒ 第三方无法从产物复核 128 是什么。

### 2.2 (b) 31 个扩展形态 —— 冻结 or 派生？

| 维度 | 实测 | 结论 |
|---|---|---|
| 定义处 | `tools/kb/syntax_coverage.py:32-64`（`EXTRA_FORMS` 硬编码 dict，31 项，各带中文描述） | **人工维护的冻结清单**，非派生 |
| 维护者/机制 | 仓内无第二份清单、无生成器、无版本字段、无「语言版本」标注；仅 `except_star`（`:55`）与 `async` 族带 3.11/3.12 注释痕迹 | **靠人记**，语言加形态时**不会自动进分母** |
| 与 97 节点分母的**重复计数** | **28/31 项**在语义上指向分母内已存在的 ast 节点（`elif_chain→If`、`for_else→For`、`augmented_assign→AugAssign`、`slice→Slice`、`global_nonlocal→Global/Nonlocal`、`async_def→AsyncFunctionDef`、`await_expr→Await`、`walrus→NamedExpr`、`match_statement→Match`、`except_star→TryStar`、8 个 match 模式→`MatchClass/MatchMapping/MatchSequence/MatchOr/MatchAs/MatchStar/MatchValue/MatchSingleton`、`decorator_with_args`/`keyword_args→Call` 等）；**另 3 项**（`star_import`/`nested_comprehension`/`case_guard`）指向**被大小写规则丢弃的小写类**（`alias`/`comprehension`/`match_case`），实为「缺项补偿」；**新增语言面 = 0**（`numerator_lexical_audit.py: extra_forms_class_counts` = {overlaps 28, compensates 3, new 0}） | **分母不是互斥分区**：128 = 97 + 31，而 97 中 32 项是载荷类、31 项**全部**是既有项的「变体视角」或缺项补偿 ⇒ **对 3.11 语言面的独立覆盖增量 = 0**；同时反向漏计 7 个小写真语法类（其中 `arg`/`arguments` 无人补偿 ⇒ B171） |
| 语言加形态时的漂移 | ① ast 节点侧：自动进入分母（派生）→ 3.12 模拟分母 97→**102**；新增 5 类在 `core/**` **0 命中** ⇒ 同一工具在 3.12 下读数 **128/133 = 96.24%（非 100%）**。② 扩展形态侧：**不自动进入**（冻结） ⇒ 3.12 `type` 语句别名 / PEP 695 泛型语法**永远不会被计入分母**，直到有人手改 dict | **一半派生、一半冻结，且两者都未钉版本** ⇒ 分母是**可漂移的复合体**，无版本锁、无 manifest、无「语言版本」字段 |

**分母漂移风险（具体化）**：
1. 同一份代码在 3.11 = 100.00%、在 3.12 = 96.24%（模拟 5 个 3.12 类注入后实测分母 102，分子仍 97/31）；
2. 3.13 起 PEP 695/695 更进一步（`TypeAlias` 已在 3.12 模拟中体现）；
3. 扩展形态清单**反向漏计**：任何语言新增的「无独立 ast 节点」的形态（如 3.12 `type` 别名、3.13 新语法）在被人工补进 `EXTRA_FORMS` 之前，**不在分母内 ⇒ 不影响占比读数 ⇒ 100% 仍显示成立**（分母越小占比越"好看"，存在**口径自利方向**）。

---

## §3 粒度错配量化

**机器可读基准**：`rounds/round1/judgment_space.json`（39 形态族 / 1556 条目；维度 form×host×depth×variant），变体谓词在 `tools/completeness/jspace_generator.py:382-1077`（`fam(...)` 内的 `lambda c: ...`），证据索引在 `:253-286`，观测器在 `:293-335`。本轮脚本 `variant_quantify.py` **复用同一批谓词**（不另造口径），并与树 `attain-true-completeness/rounds/round8/REVIEW.md §2` 的 25 行登记探针交叉核对。

### 3.1 折叠掉的维度规模

| 读数 | 数量 | 对 128 的倍数 |
|---|---|---|
| 判定空间条目（form,variant,host,depth） | **1556** | 12.2× |
| (form, variant) 对 | **299** | 2.3× |
| (form, variant, host) 三元组 | **1251** | 9.8× |
| 25 行的声明变体合计 | **279** | 2.2× |
| 登记探针实际触发的变体 | **118（42.3%）** | 0.9× |
| 判定空间全部证据可触发的变体 | **227（81.4%）** | 1.8× |

⇒ 「128」把 **宿主（48）× 变体（408）× 深度（3）** 三维整体折进分母；**分母项数比可判定单元少 12.2 倍**，且**行级证据只覆盖其中 42.3%**。

### 3.2 逐行：声明变体 vs 登记探针实际触发（25 行全表）

> 列义：**声明变体** = 判定空间该行形态族的变体槽数；**宿主/条目** = 该行在判定空间中的宿主数与条目数；**登记探针触发** = REVIEW.md §2 登记的深层探针源码（用 `ast` 解析、跑同一批变体谓词）实际触发的变体数；**形态实例** = 登记探针中该行声明形态的 AST 节点出现次数（0 ⇒ F1 同构）。

| # | 行 | 声明变体 | 宿主 | 空间条目 | 登记探针触发 | 空间证据触发 | 形态实例 | 判定 |
|---|---|---|---|---|---|---|---|---|
| 1 | If | 13 | 15 | 118 | 2 | 12 | 1 | 缺口 |
| 2 | BoolOp | 13 | 14 | 85 | 7 | 12 | 16 | 缺口 |
| 3 | IfExp | 14 | 13 | 28 | 3 | 9 | 13 | 缺口 |
| 4 | Try | 12 | 12 | 108 | 7 | 12 | 4 | 缺口 |
| 5 | Raise | 10 | 10 | 39 | 2 | 9 | 1 | 缺口 |
| 6 | Assert | 11 | 11 | 46 | 7 | 8 | 9 | 缺口 |
| 7 | Import | 12 | 12 | 47 | 7 | 10 | 6 | 缺口 |
| 8 | Global | 7 | 10 | 19 | 4 | 5 | 5 | 缺口 |
| 9 | global_nonlocal | 5 | 8 | 40 | **0** | **0** | **0** | **F1 同构**（B163） |
| 10 | Await | 12 | 9 | 23 | 7 | 11 | 7 | 缺口 |
| 11 | ListComp | 14 | 12 | 40 | 3 | 8 | 2 | 缺口 |
| 12 | await_expr | 9 | 10 | 21 | 6 | 7 | 6 | 缺口 |
| 13 | Yield | 10 | 12 | 18 | 2 | 6 | 6 | 缺口 |
| 14 | Match | 12 | 11 | 37 | 3 | 10 | 11 | 缺口 |
| 15 | With | 10 | 11 | 83 | 8 | 10 | 11 | 缺口 |
| 16 | match_statement | 10 | 10 | 60 | 3 | 9 | 2 | 缺口 |
| 17 | Break | 10 | 10 | 32 | 6 | 7 | 1 | 缺口 |
| 18 | Continue | 10 | 10 | 35 | 3 | 8 | 2 | 缺口 |
| 19 | While | 11 | 11 | 45 | 2 | 9 | 2 | 缺口 |
| 20 | Delete | 10 | 11 | 24 | 7 | 8 | 9 | 缺口 |
| 21 | AugAssign | 20 | 12 | 63 | **20** | 20 | 18 | OK（唯一全覆盖行） |
| 22 | Return | 13 | 13 | 80 | 2 | 11 | 7 | 缺口 |
| 23 | Slice | 9 | 9 | 25 | 6 | 8 | 8 | 缺口 |
| 24 | augmented_assign | 12 | 12 | 49 | 1 | 9 | 3 | 缺口 |
| 25 | slice | 10 | 10 | 32 | **0** | 9 | **0** | **F1 同构（B167）** |

**汇总**：25 行中 **24 行存在变体触发缺口**；**2 行登记探针零触发**（`global_nonlocal`、`slice`）；唯一全覆盖行是 `AugAssign`（20/20，因其登记探针 `r8_06_augassign_ops.pyc` 恰是 16 种算子 + 4 种形态的算子族全集）。登记探针触发率合计 **118/279 = 42.3%**。

**具体形态的变体枚举（抽样，节选）**：`ast.If` 承载 13 变体（if-no-else / if-else-arm / if-elif-chain / if-cond-ternary / if-cond-boolop / if-cond-await / if-cond-compare-chain / if-empty-then / if-in-loop / if-in-try / if-in-handler / if-in-with / if-in-match-case）× 15 宿主（module-level…match-case-body）；`ast.Try` 12 变体（handler-as / handler-tuple-type / handler-typed / in-func / in-class-body / nested-in-loop / nested-in-with / nested-in-try / finalbody…）× 12 宿主；`ast.Match` 12 变体（pat-value / pat-class / pat-mapping / pat-sequence / pat-or / pat-capture / pat-star / pat-nested / pat-literal …）——**每形态都已 >1 语义变体**，按 spec.md:66「变体维度被折叠 ⇒ 折叠计数不得作为完备依据」。

---

## §4 三态分类审计

**台账定义**（`wiki/concepts/decompile-invariant-completeness.md`）：
- §0:32「完备占比 = 完备形态数 ÷ 128。分子判据 = 三路径存在 ∧ 嵌套无感不变式成立」；§0:37「路径存在（识别+归约+生成）**128/128 = 100%（工具实测）**」；
- §2.2:78-80 三级判定：**完备** = 三路径存在 ∧ **无破口证据**（计入分子）／**破口** = 三路径存在 ∧ 不变式破坏**有确证**（锚点+机制）／**零能力** = **任一路径缺失**（不计入分子）；
- §5.5:196-200 汇总：路径存在 128/128、完备 128、破口 0、零能力 0、占比 100%。

**逐问回答**：

1. **互斥性**：在**测量空间**上成立 —— 破口要求「三路径存在」，零能力要求「任一路径缺失」，完备要求「三路径存在 ∧ 无破口证据」⇒ 三者两两不交。**但**：① 完备的补集写作「**无破口证据**」（证据缺席）而非「已证无破口」（证真缺席）⇒ 空证据形态**落入完备**（F1 的 `global_nonlocal` 即是：0 证据仍判完备，REVIEW.md:36）；② 破口桶要求「锚点+机制」确证，红单元的**归属行**由人工裁决（B142 稀窝「不升格」、B75 归 global_nonlocal 而非 Global 行等），故**同一份证据可被归到不同行** ⇒ 完备/破口在同一形态上**可同时"成立"**（行内绿 ⇒ 完备；同族红 ⇒ 破口），冲突由归属裁决消解，而非由测量消解。
2. **穷尽性**：**不成立**。「三路径存在」实测 = 词法存在性（见 §2/AT-13）；「词法存在但能力缺失」的形态**既非零能力、也非破口**，默认落完备。⇒ 三态是对**读数**的划分，不是对**能力**的划分；能力空间存在第四类（词法有/能力无）被静默归入完备。
3. **零能力 vs 破口的形式区分**：**零能力 = 词法路径测试失败**（`syntax_coverage.py:113-184`）；**破口 = 词法路径测试通过 ∧ 人工确认不变式破坏**（台账 §5/§6）。两者**区分依据是证据种类**（机器词法 vs 人工锚点），不是能力层级；且**破口 0 没有任何机器测点**——`three_state_and_reconcile.py` 实测：全仓 39 个 `.py` 提及「完备/破口/零能力」关键字（注释与文档字符串），**状态赋值测点 0 处**（`state_assignment_sites = []`）⇒ 「破口 0」是**人工断言**，不是测量输出。
4. **同一文档内的读数并存**：台账 §5.4:186 仍写「**global_nonlocal 破口：B75**」、:185 写「**slice 破口：B127**」，而 §5.5:197-199 汇总「完备 128 / 破口 0 / 零能力 0」——**历史破口与终态破口 0 同文并存**，二者只由 v8 叙述连接；本轮实测：这两行恰好是**登记探针零形态证据**的两行（§3.2 #9、#25）⇒ **行的完备结论与其形态证据脱钩，且脱关节恰落在两处历史破口上**。

---

## §5 「单元绿 ⇒ 完备」推断链

**推断链（逐环定位）**：

```
R8 §2 25 行终表：行完备 ⇔ 深层(≥3 级)探针全单元绿 + 负对照不误杀 + 台账 §5 形项可装配   ← 判据定义（REVIEW.md:20）
  └─ 环1「深层探针」= 该行登记的 1 个 .pyc（REVIEW.md:28-52）                        ← 唯一形态级证据
      └─ 环2「全单元绿」= 该探针每个 code object 的字节码/CFG 等价（pyc_verify + 附件 compare_pyc）  ← 只比该探针含有的东西
          └─ 环3 ⇒ 「该行声明的形态被验证」                                            ← **断点在此**
              └─ 环4 ⇒ 「该形态完备」 ⇒ 25 行 ⇒ 128 形态完备 ⇒ 100%
```

**断点（环3）**：环2 的绿只覆盖**探针源码里实际存在的形态**；环1 的探针是**人工指定的一个文件**，系统**不校验它是否含该行声明的形态**。⇒ 「绿」与「该行形态」之间**没有任何机器约束**。

**结构同构案例枚举（本轮实测，方法：对 25 行登记探针源码用 `ast` 解析，检查行声明形态的 AST 节点出现次数与变体谓词触发）**：

| 判据 | 行 | 实测 |
|---|---|---|
| **登记探针零含该行形态**（F1 同构，最强） | `global_nonlocal`（REVIEW.md:36） | `ast.Nonlocal`/`ast.Global` 实例 **0**；变体 **0/5**（F1，B163） |
| | `slice`（REVIEW.md:52） | `ast.Slice` 实例 **0**（探针 `r8v8rev3_b104_exprtail_battery.py` 实为 while+compare+boolop+f-string/dict-comp/三元「表达式尾电池」）；变体 **0/10** ⇒ **新破口 B167** |
| **登记探针含该形态但只触发 ≤1/3 变体**（部分错配） | `If` 2/13、`Raise` 2/10、`Return` 2/13、`While` 2/11、`Yield` 2/10、`ListComp` 3/14、`IfExp` 3/14、`Match` 3/12、`match_statement` 3/10、`Continue` 3/10、`augmented_assign` 1/12、`Slice` 6/9、`Global` 4/7 … | 合计 **24/25 行**；登记探针触发率 **118/279 = 42.3%** |
| **登记探针含该形态且覆盖全部变体**（唯一） | `AugAssign` 20/20 | 登记探针恰为算子族全集（`r8_06_augassign_ops.pyc`） |

**与台账的交叉印证**：台账 §5.4 把 **B75（global 声明错位）** 归到 `global_nonlocal` 扩展形态、把 **B127（切片边界）** 归到 `slice` 形态，而这两行的登记探针**恰都不含该形态** ⇒ **历史破口的封闭证书与行级探针不是同一份证据**（真实 `nonlocal` 探针 `r10_13/r10_14`、真实切片探针 `e07_*` 未进入行→探针映射；F1 已实测 `r10_13/r10_14` 0 命中）。

---

## §6 与判定空间的差距

**round1 覆盖基线**（`rounds/round1/coverage_baseline.json` / `COVERAGE_BASELINE.md`）：条目 **1556**、covered **976**、uncovered **580**、**62.72%**、39 族、status_mismatch 0；最差族 **ExceptStar 96/96 全未覆盖**、**global_nonlocal 40/40 全未覆盖**。

**本轮 §3/§5 读数与它的关系**：

| 口径 | 分母 | 分子 | 读数 | 语义 |
|---|---|---|---|---|
| v8「形态基线」 | 128（97 节点 + 31 扩展形态；实为 65 大写真语法 + 32 载荷类 + 31 变体视角/缺项补偿，且**缺 7 个小写真语法类**） | 128 | **100%** | 「**词法存在**」100% + 「**25 行各 1 个抽样探针**全绿」 |
| 判定空间（round1） | 1556（39 形态 × 48 宿主 × 3 深度 × 408 变体槽） | 976 | **62.72%** | 「(形态,变体,宿主,深度) **单元**有形态级证据」62.72% |
| 本轮行级核验 | 25 行的 279 个声明变体 | 118 | **42.3%** | 「**行的登记探针**触及其声明变体」42.3% |

**因此「100%」精确地意味着**：在「Python 3.11 `ast` 类清单（97）+ 人工清单（31）」这一**自定分母**上，**源码中出现过相应名字**（97 中 43 个为真实 `ast.X` 引用、54 个仅字符串类型标签），**且** 25 个抽样行各有一个全绿的深层探针文件。

**它不意味着**（逐条否证）：
1. 不意味「Python 3.11 语言面 100% 可反编译」——分母含 32 项非独立语法项、31 项为既有项的变体视角/缺项补偿、且**缺 7 个小写真语法类**（含函数形参面 `arg`/`arguments`）；
2. 不意味「三路径（识别/归约/生成）逐项存在」——工具只测一维词法存在性，**三路径从未分路径实测**；
3. 不意味「形态的各语义变体被验证」——行级触发率 42.3%，24/25 行有缺口；
4. 不意味「组合/宿主维度被覆盖」——判定空间 62.72%，580 个单元无任何形态级证据（含 ExceptStar 整族 96 条）；
5. 不意味「换解释器/换语言版本仍 100%」——3.12 模拟 96.24%；
6. 不意味「未被证伪的形态已成立」——完备桶按「无破口证据」判定 ⇒ **零证据 = 完备**（`global_nonlocal`、`slice` 两行即是）。

**双读数建议**：保留 128 作**形态基线（历史口径）**，对外一律标注「形态基线达成（v8 词法+抽样口径）」；完备性结论改由**判定空间覆盖 + 语义差分 + 变异测试 + 覆盖检查器**四证决定（spec.md:109 门槛）。

---

## §7 新破口登记（自 **B164** 起；B163 = F1 已被占用）

| 破口 | 名称 | 判定依据（可复现） | 影响 | 归属层 |
|---|---|---|---|---|
| **B164** | **分母构成错误：缺 7 / 多 32 / 重复 31**（128 非语言面分区） | `denominator_audit.py`：分母 97 = 65 大写真语法 + 29 运算符/比较/布尔词法类 + 3 ctx 类；**7 个小写真语法类被 `n[0].isupper()` 丢弃**（`alias/arg/arguments/comprehension/keyword/match_case/withitem`）；`numerator_lexical_audit.py`：31 扩展形态三分归类 = {与 97 内节点重复 **28**、补偿被丢弃小写类 **3**、新增语言面 **0**} | 「完备占比 = 完备形态数 ÷ 128」的分母**与语言面无对应关系**：32 项是载荷类、31 项是既有项的变体视角/缺项补偿 ⇒ 独立覆盖增量 = 0；占比读数不可解释为语言面覆盖率 | L1 |
| **B165** | **分母随解释器漂移且 deny-list 失效** | `tools/kb/syntax_coverage.py:92-107` 取运行解释器 `dir(ast)`，全文无版本断言；`:82-83` 的 `'typevar'/'type_param'` **大小写错误** ⇒ 对 3.12 `TypeVar`/`TypeParam` 永久无效；3.12 模拟（注入 5 类）分母 97→**102**、总项 128→**133**、分子仍 128 ⇒ **96.24%**；新增 5 类在 `core/**` 0 命中 | 「分母 = 3.11 语言权威」只在本机 3.11 成立；工具**无版本锁**；扩展形态侧反向漏计（3.12 `type` 别名等永不入分母） | L1 |
| **B166** | **分子为词法存在性读数；「三路径」无分路径测点** | `syntax_coverage.py:113-120`（正则 + **任意引号大写词**）、`:146-184`（`hint in all_text` 子串）；实测 97 命中 = 43 `ast.X` + 54 仅字符串类型标签，严格去字面量仅 **22**；31 扩展形态中 `capture_pattern`/`or_pattern`/`value_pattern` 的 hint **仅见于注释** | 台账 §0/§2.2 的「三路径存在」在工具层**无对应测点**；100% 实为「名字出现过」 | L1 |
| **B167** | **F1 同构第二例：行 `slice` 的登记探针零形态证据** | `variant_quantify.py`：行 `slice`（REVIEW.md:52）登记探针 `r8v8rev3_b104_exprtail_battery.py` 的 `ast.Slice` 实例 = **0**、10 个声明变体触发 **0**；台账 §5.4:185 恰把 B127（切片边界）记在该形态 | 该行「完备」结论**无形态级证据**；与 B163 构成「F1 非孤例」的证据 | L1 |
| **B168** | **行级变体证据缺口（粒度折叠的实例化）** | 25 行声明变体 279，登记探针触发 **118（42.3%）**；**24/25 行有缺口**；仅 `AugAssign` 20/20 全覆盖 | 「行完备」实际含义 = 「该行登记探针全绿」，与「该行形态各变体被验证」相差 **161 个变体槽** | L1 |
| **B169** | **完备桶的「证据空集即完备」+ 三态无机器测点** | 台账 §2.2:78「完备 = 三路径存在 ∧ **无破口证据**」；`three_state_and_reconcile.py`：全仓 **状态赋值测点 0 处**（39 个 .py 仅在注释提及三态） | 零证据形态默认判完备；「破口 0」是人工断言非测量；三态在**能力空间**不完备（第四类「词法有/能力无」被静默吞掉） | L1 |
| **B170** | **分子口径与分母口径错配（128 完备数 ≠ 逐项判定）** | 判定空间 39 形态中 **25 个有行、14 个 NEW 族无行**（AnnAssign/AsyncFor/AsyncFunctionDef/AsyncWith/Decorator/DictComp/ExceptStar/GeneratorExp/JoinedStr/Lambda/NamedExpr/PEP604Union/SetComp/Starred）；分子 128 由 25 行 + 组合级 28 项 + 人工台账汇总得出，**非对 128 个分母项逐项判定** | 「完备 128」与「分母 128」**不同坐标**，占比公式在形式上即不成立 | L1 |
| **B171** | **分母漏项：函数形参面无对应项** | `denominator_audit.py: dropped_and_never_recovered` = `['arg','arguments','keyword','withitem']`；`ast.arg`/`ast.arguments`（形参名 / 形参表 / 默认值 / 注解 / `*a`/`**k`）在 97 节点项与 31 扩展形态中**均无任何条目**（`keyword`/`withitem` 至少被 `keyword_args`/`multi_context_with` 语义隐含） | 「128 = 语言面」的断言在**函数签名面**上不成立；台账 §5.2 以「JSON 背书」把 FunctionDef 判完备 ⇒ 该面**从未进入过完备判定** | L1 |

---

## §8 方法论结论（喂 Task 8）

要让「完备」**可证伪**，口径必须做以下 7 项改造（每项给出可机检判据）：

1. **分母钉版 + 可自证**：分母改为**版本钉死的 manifest**（`py311_ast_nodes` 显式清单 + 扩展形态清单 + 生成器 + 校验和），JSON 必须落**分母节点清单与扩展形态定义**（现产物只落计数，不可复核）；补 `sys.version_info` 断言，**运行解释器 ≠ 钉定版本即拒跑**（消 B165）。
2. **分母去重、补缺与分层**：把 29 个运算符/比较/布尔词法类与 3 个 ctx 类从「形态」降为「载荷类」单列；**补回**被大小写规则丢弃的 7 个小写真语法类（`alias/arg/arguments/comprehension/keyword/match_case/withitem`，其中 `arg`/`arguments` 必须独立成项 ⇒ 消 B171）；31 扩展形态与节点项**去重后**计一次（真语法面 = 65 + 7 = **72**）⇒ 占比分母改为**互斥分区**（消 B164）。
3. **分子改三路径分测**：`syntax_coverage.py` 必须对**识别/归约/生成**三路径各给一个**可执行**测点（不能是名字命中）；词法命中只能记为「词汇存在」档，**不得计入完备分子**（消 B166）。
4. **完备桶改证伪型定义**：「完备」须为「**已证**（三路径 × 该形态全部声明变体 × 全部声明宿主 × 全部深度档）有形态级证据」；**证据空集 ⇒ 判『未判定』，不得判完备**；三态增第四态「未判定/不可判定」（消 B169）。
5. **行→形态→变体→证据的强制映射**：任何行的完备结论 SHALL 附带**变体级证据映射**（行 → 变体 → 探针文件 + 该探针内该变体的 AST 谓词命中）；映射由覆盖检查器机械校验：**行名形态在探针中零出现 ⇒ 直接判该行未验证**（消 B163/B167，并推广到 24/25 行的缺口 B168）。
6. **零能力/破口判据同源化**：两者都必须由**同一台机器**基于**同一份执行级证据**产生（破口 = 有执行/差分反证；零能力 = 有执行级缺失反证），禁止「词法 vs 人工」异源划分（消 AT-17 的不可证伪）。
7. **分子分母同坐标**：完备数必须逐**分母项**判定并落表（含 14 个 NEW 族与 ExceptStar 96 条空间单元），占比公式在**同一坐标系**内计算（消 B170）；对外双读数：**形态基线（历史）** 与 **判定空间口径** 分列，v8 的 100% 明确标注为「词法+抽样口径的历史读数」，不得再作为完备性结论引用。

> 附：本轮未改任何 core/tests/wiki/rules；新破口 B164–B171 仅登记，待 Task 10 统一封闭。
