---
type: concept
title: 反编译迭代总纲：嵌套无感与语法完备
tags:
  - code-kb
  - completeness
related:
  - "[[cfg-anatomy]]"
  - "[[branch-conditions]]"
  - "[[if-continue-sibling-loss]]"
created: 2026-09-29
updated: 2026-09-29
kind: concept
sources:
  - tools/kb/syntax_coverage.py
  - tools/kb/branch_conditions.py
  - tools/kb/program_cfg.py
  - docs/refactor/syntax-coverage.json
  - docs/refactor/branch-conditions.json
  - docs/refactor/program-cfg.json
  - core/cfg/region_analyzer.py
  - core/cfg/region_ast_generator.py
  - core/cfg/code_generator.py
---

# 反编译迭代总纲：嵌套无感与语法完备

**本文是反编译器"嵌套无感 + 语法完备"的唯一权威文档**：理论（§1–§4）、逐形态台账（§5）、破口登记（§6）、迭代机制（§8）、口径演变史（§9）、全部可用资源（§10）尽在于此。旧版标准页与台账页已并入本文（转址映射见文末）。

## 0. 一句话标准与当前读数

> **完备占比 = 完备形态数 ÷ 128。分子判据 = 三路径存在 ∧ 嵌套无感不变式成立。**
> 要求：程序对嵌套与不嵌套必须完全一样处理；处理对嵌套无感。

| 层 | 当前读数（2026-10-04 终审更新） |
|---|---|
| 路径存在（识别+归约+生成） | **128/128 = 100%** |
| 嵌套无感不变式（形式层） | **完备 128 / 破口 0 / 零能力 0**（B1 族于对抗规范 Round 1 五臂封闭，Round 2–9 复验零漂移） |
| 组合级对抗挂账 | **25 号未清零**（B42–B51/B56–B65/B69–B71/B73–B76 内未封闭部分 + 残留单元；权威清单 = `.trae/specs/harden-completed-forms-10rounds/rounds/round10/REVIEW.md` 残留决策表 + REVIEW2.md） |
| **完备占比** | **128/128 = 100%**（形式层；组合级挂账透明挂账、未清零，不计入形式层分母） |

三维度禁止互替：**语法完备**（本文）/ **结构正确率**（sstrict 缺陷口径）/ **字节等价**（门禁口径，见 §9.2）。

---

## 1. 嵌套无感不变式（理论核心）

对区域 A，归约规则 R 必须满足三条款：

| 条款 | 要求 | 违反后果 |
|---|---|---|
| **C1 局部消费** | R(A) 只读 `L(A) = A.blocks ∪ A.out_edges ∪ A.exception_table` | 读了邻居/父级信息 ⇒ 归属错误 |
| **C2 黑箱组合** | 子区域只经 entry/exit 接口被父级消费，父级不窥视子区域内部 | 跨层泄漏 ⇒ 深层行为 ≠ 浅层行为 |
| **C3 守卫封闭** | 必须参考非局部信息时（汇合块被区域外引用、continue 目标跨区域、fall-through 是别区域 entry），必须有显式守卫排除/认领 | 未封闭 ⇒ 无感破口 |

**归纳论证（分母为什么不是无限的）**：C1+C2 成立时，一层正确（归纳基）+ 组合封闭（归纳步）⇒ 任意深度/任意组合正确。嵌套对 R 不可见，完备性只需在**形态维度**测量。

**推论（强制）**：凡"深层才错、浅层没事"的缺陷 = C1/C2/C3 某条被破坏。修复 = **封闭守卫恢复无感**，不是给语料个案打补丁；修完无需逐深度验证。

**与四大算法原则的映射**（`rules.md` §1.2/1.5）：C2 = 原则3（嵌套即抽象节点）；C1 强化原则2/4（每块唯一归属 + 入口引用语义）；C3 是新增的显性守卫要求。

---

## 2. 语法完备：分母、判定

### 2.1 分母 = 128（Python 3.11 语言语法面，权威 = `ast` 模块）

- **97 个 ast 节点类型**：`dir(ast)` 具体类，剔除 3.8 前废弃别名（`Num/Str/Bytes/NameConstant/Ellipsis/AugLoad/AugStore/Param/ExtSlice`）与非语法面（`Interactive/Expression/FunctionType/Suite/TypeIgnore/AST` 及抽象基类）。
- **31 个无独立节点的语句形态**（全名册 = `docs/refactor/syntax-coverage.json` `covered_extra_forms` + except_star）：elif 链、for-else、while-else、多目标赋值、多上下文 with、增量赋值、链式比较、海象、装饰器带参、关键字实参、`*args`、`import *`、相对导入、global/nonlocal、切片、f-string 转换符、async 五件套（def/for/with/await/yield from）、多重 for 推导、try-finally-only、match+守卫+8 模式（value/singleton/sequence/mapping/class-keyword/or/capture/star）、**except\* 异常组**。
- **永不**取自实现自身 `RegionType` 枚举、**永不**取自语料、**不**随嵌套深度/组合膨胀。

### 2.2 三级判定

| 级别 | 判据 | 计入分子 |
|---|---|---|
| **完备** | 三路径存在 ∧ 无破口证据 | ✅ |
| **破口** | 三路径存在 ∧ 不变式破坏有确证（锚点+机制） | ❌ |
| **零能力** | 任一路径缺失 | ❌ |

数字规则：路径层由 `tools/kb/syntax_coverage.py` 实测（→ `syntax-coverage.json`）；不变式层由 §5 台账汇总。**禁止手改数字，禁止页面间矛盾数字。**

---

## 3. 十三条误解清单（反模式，含本仓真实发生史）

| # | 误解 | 错误做法（真实发生） | 为什么错 | 正确做法 |
|---|---|---|---|---|
| 1 | **循环论证分母** | 拿实现自身 `RegionType` 枚举当"全部可能分支"测覆盖 | 自洽自证，只证明枚举与实现一致 | 分母取语言（`ast` 模块）权威语法面 |
| 2 | **有过就算** | 节点类/构造引用存在即计入分子（首版 91.5%→99.2% 都犯此病） | 存在≠能处理；半成品也"存在" | 路径存在 ∧ 不变式成立才计入 |
| 3 | **语料证据口径** | "match 语料零命中⇒无证据⇒不算"，拿门禁读数定义完备 | 正确性不由语料定义；语料只旁证归纳基 | 完备性看代码结构性质 |
| 4 | **无限分母** | "任意嵌套组合分母无限大" | 无感处理下嵌套由归纳覆盖 | 分母=128 形态 |
| 5 | **节点词汇当完备** | "97 ast 节点 100% 产出 ⇒ 完备 100%" | 词汇是必要条件非充分条件 | 路径层与不变式层分开报告 |
| 6 | **浅层测试当无感证明** | 语料深度 32 内全过 ⇒ 声称任意深度能处理 | 单层正确 ≠ 归纳步成立 | 每形态审 C1/C2/C3 |
| 7 | **门禁读数当完备性** | 字节等价 99.55% 直接当"能处理占比" | 等价率是正确性口径（语料上） | 两个维度分列，禁止互替 |
| 8 | **顶层构造粗清单** | 34 形态顶层列表冒充语法全集（97.1% 虚高） | 顶层清单粒度粗 | 97 节点+31 扩展形态全清单 |
| 9 | **识别率当完备性** | 语料形态命中率混入完备分子 | 命中率是语料属性 | 完备分子只看形态×不变式 |
| 10 | **维度互替** | 用"等价率 99.55%"反驳完备占比 | 正确性与完备性是两个轴 | 各维度独立测量 |
| 11 | **改工具不改方法** | 修 syntax_coverage.py 但保留错误口径 | 工具对≠口径对 | 先定理论再动工具 |
| 12 | **错误检测标准** | 用 `PRELOAD_RERAISE` 零引用判 except\* 未实现 | PRELOAD_RERAISE 是 **3.12** 操作码；3.11 的标记是 CHECK_EG_MATCH/PREP_RERAISE_STAR——本仓实际全链实现（§7） | 检测标准对准目标版本真实标记 |
| 13 | **语料上限当能力上限** | "语料最深 32 层 ⇒ 程序只能处理 32 层" | 无感不变式成立时深度由归纳覆盖 | 能力边界由不变式判定，不由样本外推 |

维护规则：**只增不删**，新口径错误编号续接并注明发现场景。

---

## 4. 理论要求 → 代码实现程度（T1–T8，锚点全部 2026-09-29 实测）

| # | 理论要求 | 代码落点 | 程度 |
|---|---|---|---|
| T1 | 每形态有识别路径 | `RegionType` 枚举 19 类 `region_analyzer.py:170-189`；识别函数族：`_identify_conditional_regions:15981` / `_identify_loop_regions:3782` / `_identify_try_except_regions:7603` / `_identify_with_regions:12282` / `_identify_match_regions:12920` / `_identify_assert_regions:14799` / `_identify_boolop_regions:23420` / `_identify_ternary_regions:20515` / `_identify_chained_compare_regions:15495` / `_identify_sequence_regions:27519`；except\* 规则4 `:9731/:9813`、框架块 `:12701-12709` | **128/128** |
| T2 | 每形态有归约路径 | `Region.add_child:221`；臂收集+汇合剪枝 W14-C `:27282/27304`；handler 归并 `:7891/:8724/:9342`；`_find_loop_else:5242` + clamp `:5105`；孤儿块释放+守卫 `region_ast_generator.py:1593-1663`、`region_analyzer.py:1410-1424` | **128/128** |
| T3 | 每形态有生成路径 | dict 工厂：If `region_ast_generator.py:9575/18957/24043`、While `:5463/12086`、Try `:26901/27389`、Match `:31596`、elif `:17027/17261`、Break/Continue `:10198/:24098`、Lambda `:2250`、ListComp `comprehension_generator.py:2074`；`ast_converter.py` dict→AST；`code_generator.py` 发射 | **128/128**（`syntax-coverage.json` 实测） |
| T4 | 归约只消费 L(A)（C1/C3） | continue 守卫 `_block_is_continue_target:10289` + `_loop_else_set` 排除 `:10423-10427`；共享尾守卫族 W14-C/fix3-T1T2T6/W23/R71-thenover（`region_analyzer.py:27282/27304/19602`、`region_ast_generator.py:12945-13075/18593/19185/22758`） | 守卫族已落地；**B1 破坏**（§6） |
| T5 | 子区域黑箱消费（C2） | 孤儿块释放+合法子区域不释放守卫（R74 族） | 已落地 |
| T6 | 非局部信息守卫封闭（C3） | 同 T4 守卫族 | 大族已落地；**B1 未封闭**（§6） |
| T7 | 归纳基：单层正确 | 门禁旁证（§9.2）：官方 41 靶 0 ERR、字节等价 99.55% | 成立（语料口径仅旁证） |
| T8 | 生成递归于区域树 | 生成器对 children 递归，`ast_converter.py` 消费 dict 树 | 成立 |

---

## 5. 128 形态逐形态审计台账

证据规则：锚点 = 2026-09-29 审计亲眼所见的 `file:line`；"JSON 背书" = 构造点存在性由 `syntax-coverage.json` 实测背书。**禁止**凭记忆补锚点，找不到写未找到。

### 5.1 共享管线锚点

| 管线段 | 锚点 |
|---|---|
| 块分割 | `core/cfg/cfg_builder.py` |
| 区域识别分发 | `RegionType` `region_analyzer.py:170-189` |
| 区域树 | `Region.add_child` `:221` |
| 块语义 | `BlockSemantics.is_continue/is_break/is_return` `:199-201` |
| 表达式重建 | `expr_reconstructor.reconstruct` 调用点 `region_ast_generator.py:47610` |
| dict→AST / 发射 | `ast_converter.py` / `code_generator.py` |

### 5.2 表A — 语句与结构形态（区域管线）

| 形态 | 识别锚点 | 归约锚点 | 生成锚点 | 判定 |
|---|---|---|---|---|
| Module | 管线根 | 顶级区域列表 | `region_ast_generator.py:6728` | 完备 |
| If | `IF/IF_THEN/IF_THEN_ELSE/IF_ELIF_CHAIN` `:173-176` | 臂收集+汇合剪枝 `:27282/27304` | `:9575/18957/24043` | 完备（B2 守卫族已落地） |
| For / AsyncFor | `FOR_LOOP:178` | `_find_loop_else:5242`、clamp `:5105` | JSON 背书 | 完备 |
| While | `WHILE_LOOP:177` | 同上 | `:5463/12086` | 完备 |
| Break / Continue | `:184-185` | `BlockSemantics:199-201` | `:10198`/`:24098` | 完备（continue 守卫 `:10289/:10423-10427`） |
| Try | `:179-180` | handler 归并 `:7891/:9342/:9915` | `:26901/27389` | 完备（孤儿 finally 帧 `:9017-9019`） |
| **TryStar（except\*）** | 规则4 `:9731/:9813`、框架块 `:12701-12709`、`exception_handler.py:93-276` | handler_type `'except_star'` 同路 `:8724`、多 handler 链 `:10424-10483` | `:26839-26843`、发射 `code_generator.py:702/2079` | **完备**（§7 纠正记录） |
| With / AsyncWith | `WITH:181` | with 区域构造 | `:29499` | 完备 |
| Match | `MATCH:182` | case-pattern 块族+框架块排除 `:14622-14623/:12731-12736` | `:31596` | 完备 |
| Raise / Assert | `ASSERT:183` / JSON 背书 | JSON 背书 | JSON 背书 | 完备 |
| Return / Pass / Expr | JSON 背书 | JSON 背书 | `has_trailing_return_none` `:212/217` | 完备 |
| Delete / Assign / AugAssign / AnnAssign | JSON 背书 | JSON 背书 | `code_generator.py:1149` | 完备 |
| Import / ImportFrom / Alias | JSON 背书 | JSON 背书 | JSON 背书 | 完备 |
| Global / Nonlocal | JSON 背书 | JSON 背书 | JSON 背书 | 完备 |
| FunctionDef / AsyncFunctionDef / ClassDef | JSON 背书 | 区域树子区域消费 | `AST*` 类族 `core/ast_nodes.py` | 完备 |
| ExceptHandler | `exception_handler.py:262-276` 三分类 | `:1478-1479` 停止收集 | `ast_converter.py:1418-1420` | 完备 |
| match_case / withitem | Match/With 区域内构 | 同区域 | `:31596`/`:29499` | 完备 |

### 5.3 表B — 表达式形态（表达式重建管线）

| 形态 | 识别/归约锚点 | 生成锚点 | 判定 |
|---|---|---|---|
| **BoolOp（and/or）** | `BOOL_OP:188`；`_build_boolop_expression:32662` | 同左 | **破口 B1**（§6） |
| IfExp（三元） | `TERNARY:189` | `:12654` | 完备 |
| Compare / BinOp / UnaryOp / Constant / Name / Attribute / Subscript / Starred / List / Tuple / Dict / Set / Slice / Index | 表达式栈重建（`:47610`）；`ASTCompare/ASTBinary` 类族 | JSON 背书 | 完备 |
| Lambda | JSON 背书 | `:2250`、`ast_generator_v2.py:4162` | 完备 |
| ListComp / SetComp / DictComp / GeneratorExp / comprehension | `comprehension_generator.py` 专用管线 | `:2074`、`ast_generator_v2.py:4284` | 完备 |
| Call / keyword / arguments / arg | `ASTCall` 族 | JSON 背书 | 完备 |
| JoinedStr / FormattedValue | JSON 背书 | JSON 背书 | 完备 |
| Await / Yield / YieldFrom | JSON 背书（async 管线 `:30154`） | JSON 背书 | 完备 |
| NamedExpr（海象） | JSON 背书 | JSON 背书 | 完备 |
| 上下文叶子 Load/Store/Del、操作符叶子（Add…NotIn 32 个） | 隐式/字面量词汇 | JSON 背书 | 完备 |

### 5.4 表C — 31 个扩展形态

| 形态 | 锚点 | 判定 |
|---|---|---|
| elif 链 | `IF_ELIF_CHAIN:176`；`'_is_elif': True` `:17027/17261`、`:16454` | 完备 |
| for-else / while-else | `_find_loop_else:5242`、clamp `:5105`；发射 `region_ast_generator.py:4974-5006`、`_loop_else_set:10423` | 完备 |
| **except\* 异常组** | §7 全链四层表 | **完备**（纠正记录在案） |
| match + 守卫 + 8 模式 | `MATCH:182`、`:31596`；`:14622-14623/:12731-12736`；模式解析 `pattern_parser.py` | 完备 |
| 多上下文 with / try_finally_only | `WITH` 管线 + withitem；`TRY_FINALLY:180` + `:9017-9019` | 完备 |
| multi_target_assign / augmented_assign | `code_generator.py:1149` 对照路径 + `ASTAugAssign` 族 | 完备 |
| chained_comparison / walrus / keyword_args / star_args / slice | Compare 链 / NamedExpr / `ASTCall`+arguments / Subscript | 完备 |
| relative_import / star_import / global_nonlocal | `ASTImportFrom`/`ASTGlobal` 族 | 完备 |
| fstring_conversion | `ASTConvert/ASTFormattedValue` 族 | 完备 |
| nested_comprehension | `comprehension_generator.py:2074` 族 | 完备 |
| decorator_with_args | `ASTDecoratorApplication` 族 | 完备 |
| async 五件套（def/for/with/await_expr/yield_from） | `:30154` + JSON 背书 | 完备 |

### 5.5 判定汇总

| 维度 | 计数 |
|---|---|
| 路径存在（工具实测） | **128/128 = 100%** |
| **完备** | **128**（B1 族封闭后升格；对抗 10 轮终审 syntax_coverage 复跑 128/128） |
| **破口** | **0**（形式层；组合级对抗挂账 25 号未清零，见文首读数表） |
| **零能力** | **0** |
| **完备占比** | **128/128 = 100%**（形式层） |

残留 sstrict 67 缺陷单元未逐个归类守卫族：归类属 fix 批工作流，落位后按 §8 复审。对抗 10 轮登记的组合级挂账破口与 6 组零专攻形态组（Module 专攻、ClassDef 体专攻、AnnAssign、fstring_conversion、keyword_args/star_args、decorator_with_args）为终审透明遗留，按 §8.3 状态机继续推进。

---

## 6. 破口登记与验收

### B1a — `_cjb_skip_inline_if` 前导操作数丢弃（**已封闭**）

- **破坏条款**：C1（读了"fall-through 恰是某区域 entry"这一跨块信息且未接回）
- **历史确证**：`region_ast_generator.py:47629-47643` 丢弃版形态（round75 fix1 嫁接方案 `_graft_pending_operand` 仅存归档 spec、未落地）
- **封闭（对抗规范 Round 1）**：放弃嫁接路线，改由 `region_analyzer.py` 五臂算法封闭（臂 A/B/B2/C/D/E，or 裸尾续接判据 + `_sb_has_body` 同一谓词）；落地标记 = `[B1b fix]`/`[B1b fix-r2]`（`:17592/:19011/:27601` 等十余处）+ `_sb_has_body`；Round 2–9 守卫族回归攻击与 BoolOp 面攻击复验零漂移

### B1b — 语句上下文 or 臂第二丢弃入口（**已封闭**）

- **归档复现**：`rounds/round75/batches/fix1/synth/neg75_jqcond2.py/.pyc`（`if a and b or c: total += 4` 退化）
- **封闭（对抗规范 Round 1）**：与 B1a 同批五臂封闭 + B6 四上下文封闭（3 文件 7 处）；Round 3 追加 B1b 扩充（loop-else 认领豁免）与 B11 跨类修复；验收判据全部达成（jq_trans_module 65 单元面持续 MATCH、round1 攻击面 22 目标封闭面零回退）
- **验收判据（存档）**：两丢弃入口全部定位并接回；jq_trans_module 保持；161 产物逐字节不变；neg75_jqcond2 success

### 已封闭守卫族（保留登记防回归）

| 编号 | 模式 | 落地守卫锚点 |
|---|---|---|
| B2 | If×continue | `region_ast_generator.py:10289/:10423-10427/:10455-10579` |
| B3 | Loop 共享尾 | W14-C `region_analyzer.py:27282/27304/19602`、fix3-T1/T2 `region_ast_generator.py:12945-13075`、fix3-T6 `:18593`、W23 `:19185`、R71-thenover `:22758` |
| B4 | 孤儿子 | `region_ast_generator.py:1593-1663`、`region_analyzer.py:1410-1424/:9017-9019` |

**涉及形态**：BoolOp（and/or 链）+ if 复合条件连带。

---

## 7. except\* 审计纠正（误解 12 的方法论实证）

**旧结论（错误）**："有 ASTTryStar 节点类、无识别逻辑 ⇒ 零能力"。错因：检测标准用了 `PRELOAD_RERAISE`（3.12 操作码）零引用。

**审计确证（全链已实现，`[Phase 3 adv17_try_except_star]` 标记族）**：

| 层 | 锚点 |
|---|---|
| 识别 | `region_analyzer.py:9731`（规则4 PUSH_EXC_INFO+CHECK_EG_MATCH→'except_star'）、`:9813/:10008`、框架清理块 `:12701-12709`、`exception_handler.py:93-276`（handler 提取+异常类型 LOAD_GLOBAL 定位） |
| 归约 | handler_type `'except_star'` 与普通 except 同路并入 TryRegion：`region_analyzer.py:7891/:8724/:9342/:9915`；多 handler 链 `:10424-10483` |
| 生成 | `region_ast_generator.py:26839-26843`（`handler_node['is_except_star']=True`）、`:27809-27816`（框架指令过滤 BUILD_LIST/LIST_APPEND/PREP_RERAISE_STAR/SWAP/COPY）、`ast_generator_v2.py:18081-18096`、`ast_converter.py:1418-1420` |
| 发射 | `code_generator.py:702/2079-2080`（**`except_keyword = 'except*'`**） |

判定：**完备**。注：`ASTTryStar` 类（`core/ast_nodes.py:6444`）与 `region_ast_generator.py:6728` 的 'TryStar' 分发是同义冗余词汇（无生产者），不影响判定。

---

## 8. 迭代机制（可执行）

### 8.1 落地标记表（复审 = grep 标记，零新脚本）

| 编号 | 落地标记（树中出现 = 落地） | 状态（2026-10-04 终审） |
|---|---|---|
| B1a | `[B1b fix]`/`[B1b fix-r2]` 五臂封闭 + `_sb_has_body`（归档嫁接标记 `_graft_pending_operand` 已废弃不落地） | 已封闭（防回归监控） |
| B1b | 同上（与 B1a 同批封闭；Round 3 扩充认领豁免） | 已封闭（防回归监控） |
| B2 | `_block_is_continue_target`（`:10289`） | 已落地（防回归监控） |
| B3 | `[fix3-T1` / `[fix3-T6` / `[W23` / `[R71-thenover` 注记 + W14-C | 已落地（防回归监控） |
| B4 | 孤儿块释放段 `:1593-1663` | 已落地（防回归监控） |

### 8.2 复审六步（修复批落位后照单执行）

1. fix 批归档落位 → 2. **grep 该批落地标记**确认代码真在树（B1 教训：归档 spec ≠ 已落地）→ 3. 台账（§5）更新涉及形态判定 → 4. 路径层重跑 `tools/kb/syntax_coverage.py` → 5. 占比重算、页面数字同步（禁手改、禁矛盾数字）→ 6. [[log]] 记录迭代 + 破口状态变迁。

### 8.3 破口状态机

`未定位 → 已定位(仅spec) → 已落地 → 已复审(台账升"完备")`。只有走到**已复审**才允许计入分子；fix 批 BRIEF/FACTS 引用破口编号（B1a/B1b/…）作验收对象。

---

## 9. 口径演变史与正确性旁证

### 9.1 完备占比口径演变（五次，全记录不删）

| 版本 | 口径 | 读数 | 错误 |
|---|---|---|---|
| v1 | `RegionType` 枚举当分母 | 循环论证 | 误解 1 |
| v2 | 34 顶层形态清单 | 97.1% 虚高 | 误解 8 |
| v3 | 97 节点+31 形态的词汇存在率 | 99.2%（"有过就算"） | 误解 2/5 |
| v4 | 语料证据口径 + 无限分母 | "给不出占比" | 误解 3/4 |
| **v5（2026-09-29）** | **路径 × 嵌套无感不变式** | **路径 100% / 不变式 127/1/0 ⇒ 99.2%** | — |
| **v6（2026-10-04 终审，现行）** | **v5 口径 + 对抗分层** | **路径 100% / 形式层 128/0/0 ⇒ 100%；组合级对抗挂账 25 号透明挂账未清零** | — |

### 9.2 正确性旁证（语料口径，仅证归纳基，不进完备分子）

官方 41 靶 h62 SAME=40/MOVED=1/ERR=0、fully matched 33/33；sstrict 34 pyc/1528 函数 defects 67（未清零）；battery 82；金丝雀 4/4；字节等价 99.55%（5720/5746）、mandated 98.93%。门禁全表见 `rules.md` §6.2。

### 9.3 程序自身复杂度（BOM 纠正后）

60 模块 / 6,923 code object / **60,933 分支点**（子分支 91.2%，最深 164 层 = `ast_builder._process_instruction`）；**61,289 条分支判定条件**逐条入库（详见 [[cfg-anatomy]]、[[branch-conditions]]）。region_ast_generator 以 18,356 分支点（30.1%）为最大分支巢。**BOM 教训**：`region_ast_generator.py` 带 G0 保护 BOM，裸 `utf-8` 读导致 compile SyntaxError、最大模块整个从旧读数缺失（51,518 → 60,933 纠正）——工具读取一律 `utf-8-sig`。

---

## 10. 可用资源索引（全部可用资源）

### 10.1 测量工具（`tools/kb/`，输入输出与用法）

| 工具 | 用途 | 输出 | 用法 |
|---|---|---|---|
| `syntax_coverage.py` | 路径层完备实测（97 节点+31 形态构造点存在性） | `docs/refactor/syntax-coverage.json` | `python -X utf8 tools/kb/syntax_coverage.py` |
| `branch_conditions.py` | **逐分支判定条件入库 + 相似度比较**（7 类判定点、结构归一化、结构哈希） | `docs/refactor/branch-conditions.json` | 提取：`python -X utf8 tools/kb/branch_conditions.py`；查询：`... branch_conditions.py similar "<expr>" [--top-k N] [--kind K] [--module M]`；聚簇：`... dupes [--min-size N]` |
| `program_cfg.py` | 程序自身 CFG 分支点枚举（支配深度全层级） | `docs/refactor/program-cfg.json` | `python -X utf8 tools/kb/program_cfg.py` |
| `cfg_branch_walk.py` | 语料 pyc 分支规模（对照） | `docs/refactor/` | 见 [[cfg-anatomy]] §6 |
| `check_stale.py` | KB 页面 vs 源 stale 检查 | — | `python -X utf8 tools/kb/check_stale.py` |
| 其余 KB 工具 | `gen_modules/gen_classes/cluster_markers/reachability/cfg_anatomy` | `docs/refactor/` | 见 [[overview]] |

### 10.2 数据（`docs/refactor/`）

`syntax-coverage.json`（128/128 + 分母构成）、`branch-conditions.json`（61,289 判定点：模块/qualname/行号/条件原文/归一化/结构哈希/深度）、`program-cfg.json`（60,933 分支点/深度直方图/模块排名）、`patch-semantic-clusters.json`、`reachability.json`。

### 10.3 归档与复现（fix 批工作流的直接输入）

| 资源 | 路径 | 内容 |
|---|---|---|
| fix1 批归档 | `.trae/specs/region-reduction-30pyc-perfect-10rounds/rounds/round75/batches/fix1/` | `specs/jqop1.json`（B1a 嫁接方案 repl 三处）、`FACTS.md`（61 单元归属+遗留交接 §7）、`synth/repro75_jqcond.py/.pyc`（B1a 已验证复现）、`synth/neg75_jqcond2.py/.pyc`（**B1b 最小复现**）+ `synth/out/`（两臂产物）、`dump/`（ab75/canary/strict/门禁读数、jq_regions.txt、g0audit.txt） |
| fix2/fix3 批 | 同上 `batches/fix2|fix3/` | F-PAD/F-POLARITY/inside-try 等批次 spec |
| 完备性标准 spec | `.trae/specs/define-cfg-completeness-standard/` | spec/tasks/checklist（本文的前身，已全量并入） |

### 10.4 KB 页面

[[cfg-anatomy]]（程序分支点 60,933）、[[branch-conditions]]（判定条件库 61,289 + 相似度用法 + 缺陷工作流）、缺陷模式页 [[if-continue-sibling-loss]] 等 5 张（`wiki/patterns/`）、[[overview]]/[[log]]。

### 10.5 工程规范

`rules.md`：§1.5 嵌套无感不变式（工程条款形态）、§2.4 测量反模式禁令、§3.5 except\* 规则、§6.2 当前门禁清单、§6.4 修复验收标准（落地声明）、§7.2 破口登记（B1a/B1b 拆行）。

### 10.6 门禁命令（修复批验证用，见 `rules.md` §6.2 全表）

IMPORT_OK / COMPILE_OK / repro match / 官方 41 靶 h62 / sstrict 34 pyc / battery 82 / 金丝雀 4 / G0 自检 / 影响面逐字节比对。

---

## 转址映射（旧页 → 本文）

| 旧页 | 旧位置 | 本文位置 |
|---|---|---|
| `branch-coverage.md` | §1 不变式 / §2 判定 / §3 误解 / §4 T1-T8 / §5 except\* / §6 破口 / §7 迭代 / §8 数字 | §1 / §2 / §3 / §4 / §7 / §6 / §8 / §0+§9 |
| `syntax-audit-ledger.md` | 表A/表B/表C/汇总 | §5 |

## 检索词

反编译迭代总纲 / 嵌套无感 / 无感不变式 / C1 局部消费 / C2 黑箱组合 / C3 守卫封闭 / L(A) / 归纳论证 / 语法完备 / 128 形态 / 三级判定 / 完备 127 破口 1 / 99.2% / 十三条误解 / T1-T8 / 逐形态台账 / B1a _cjb_skip_inline_if / B1b neg75_jqcond2 / 落地标记 / 复审六步 / 破口状态机 / except* 纠正 / PRELOAD_RERAISE 3.12 / CHECK_EG_MATCH / PREP_RERAISE_STAR / is_except_star / 口径演变 v1-v5 / BOM 纠正 utf-8-sig / 60933 分支点 / 61289 判定条件 / 可用资源索引
