# 对抗完备形态 v2：嵌套无感与语法完备终局 10 轮 Spec

## Why

前序规范 `harden-completed-forms-10rounds` 已完成 9 轮（402 全量 6554/6617 = 99.05%、文件 369/402、quotation 152/153、小测试集 34 = 1505/1568，全部零回退），但存在三项未竟：① wiki 总纲 §5 台账 127 个"完备"判定的对抗覆盖仍是逐轮抽样，未做全台账终局复验；② 残余破口 B42×3/B43/B44/B46–B51/B56–B65/B69/B70 未清零，旧规范 Round 10 终审未执行；③ `_identify_*` 十族识别方法的注释合规（rules.md §四 六项模板 + C1/C2/C3 条款）与代码行为一致性未经逐方法独立审计。

**本规范主任务不是修复未完成 OK 的 pyc 文件**，而是对文档标榜"无感完备"的区域与语法形态进行对抗性评审与完善：评审工程师独立攻击，修复工程师（可多位协同）做真正的算法修复；凡不符合「算法驱动 / 嵌套无感 / 完备精简」的，严格认定、对抗进行、不得通容。未完全 OK 的 pyc 仅作为小测试集供子代理回归自测；全量验证由主代理执行。

---

## 理论基准 I：修复必须遵循的设计原则（rules.md §1/§2/§四/§6.4，强制性，违者评审零容忍打回）

### I.1 四大算法原则（不可违反）

| 原则 | 内容 | 违反后果 |
|------|------|---------|
| **原则1 自底向上归约** | 从最内层到最外层识别区域（归约顺序）；内层先归约，交付外层作抽象节点 | 嵌套结构错乱，内外层条件合并错误 |
| **原则2 每块唯一归属** | 每个基本块在任何层级只属于一个区域；归约时标记 `generated_blocks`/`generated_offsets` 避免重复处理 | 块被多个区域争抢，语句丢失或重复 |
| **原则3 嵌套即抽象节点** | 嵌套区域在父区域中作为单个抽象节点；归约后父区域 then/else 列表引用**子区域入口**，不是子区域所有块 | 父区域展开子区域内部，结构坍塌 |
| **原则4 入口引用语义** | 每个区域类型对应唯一 AST 节点类型；入口块引用语义显式表达（如 Continue 节点引用回边 entry） | 语义隐式化，条件合并逻辑误吞并 |

### I.2 单向数据流与算法驱动

- 分析结果从底层向上层传递，**不回溯修正**；每个结构在识别阶段就正确分类，不需要后处理修正
- 用算法替代模式匹配，用数学性质替代启发式规则；**禁止跨区域跨层次的启发式规则，禁止破坏算法对嵌套的天然支持**

### I.3 嵌套无感不变式 C1/C2/C3（2026-09-29 起强制性）

> 程序对嵌套与不嵌套必须完全一样处理；处理对嵌套无感。

| 条款 | 要求 | 违反后果 |
|------|------|---------|
| **C1 局部消费** | 归约 R(A) 只读 `L(A) = A.blocks ∪ A.out_edges ∪ A.exception_table` | 读了邻居/父级信息 ⇒ 归属错误 |
| **C2 黑箱组合** | 子区域只经 entry/exit 接口被父级消费，父级不窥视子区域内部 | 跨层泄漏 ⇒ 深层行为 ≠ 浅层行为 |
| **C3 守卫封闭** | 必须参考非局部信息时（汇合块被区域外引用、continue 目标跨区域、fall-through 是别区域 entry），必须有显式守卫排除/认领 | 未封闭 ⇒ 无感破口 |

**归纳论证**：C1+C2 成立 ⇒ 一层正确（归纳基）+ 组合封闭（归纳步）⇒ 任意深度/任意组合正确；嵌套深度与组合数不进入任何能力边界或测量分母。
**推论（强制）**：凡"深层才错、浅层没事"的缺陷 = C1/C2/C3 某条被破坏；修复 = **封闭守卫恢复无感**，不是给语料个案打补丁；修完无需逐深度验证。

### I.4 判据白名单与黑名单（修复代码的唯一合法性来源）

- **判据白名单（只允许同层块对象的结构事实）**：块末指令 opcode、后继/前驱集合、异常边、区域成员关系
- **判据黑名单（出现即打回）**：文件名/函数名白名单（「目标函数名 == 'xxx'」类）、start_offset 魔法阈值、跨层 `X.entry in Y.blocks` 反查、新增 self 跨方法状态、以少发射换全绿、硬编码深度/计数上限（`if depth > 10` 类）

### I.5 禁止事项（反模式，G3/G4 自检）

- 禁止方法命名前缀：`_fix_ / _merge_ / _patch_ / _fallback_ / _hack_ / _workaround_ / _temp_`（新增方法不得使用）
- 禁止硬编码深度/计数上限：区域归约终止性由区域数量有限性保证
- 禁止跨区域启发式：不得在外层识别时直接处理内层块的"某模式则特殊处理"
- 禁止完备性测量反模式（对准知识库 13 条误解，见 II.7）：拿实现自身 `RegionType` 枚举当分母、有过就算、语料证据口径、无限分母、节点词汇当完备、浅层测试当无感证明、门禁读数当完备性等

### I.6 修复语义与落地声明（rules.md §6.4）

- 修复 = **封闭守卫、恢复 C1/C2/C3**，不是补语料个案；修完按 wiki §8 复审对应形态并更新台账
- 落地归档必须写明「代码已落地」或「仅归档 spec 未落地」（B1 教训：fix1 嫁接方案在 jqop1.json 验证通过但代码未落地，落地标记 `_graft_pending_operand` 树中零命中）；复审 = grep 落地标记确认代码真在树

### I.7 注释合规口径（rules.md §四 + C 条款）

修复触及的每个 `_identify_*_regions` / `_generate_*` 方法 docstring 必须六项齐全：

```
①算法依据：No More Gotos 章节 + 四原则条款
②归约顺序：自底向上，内层区域先归约
③唯一归属判定：具体块归属判定逻辑（= 识别条件）
④嵌套处理：嵌套区域如何作为抽象节点（= 归约方式）
⑤入口引用语义：入口块引用语义（= AST 映射接口）
⑥反编译流程：本方法在整个反编译流程中的位置
```

并注明本方法满足/恢复的 C1/C2/C3 条款。③④⑤ 即前序规范的"三要素"（识别条件/归约方式/AST 映射），本规范以六项模板为完整口径；**注释与代码行为不一致 = 评审不通过**。

---

## 理论基准 II：完备性的正确预期（知识库 `wiki/concepts/decompile-invariant-completeness.md`，评审以此为准）

### II.1 一句话标准

> **完备占比 = 完备形态数 ÷ 128。分子判据 = 三路径存在 ∧ 嵌套无感不变式成立。**

### II.2 分母 128 的构成（权威 = Python 3.11 `ast` 模块）

- **97 个 ast 节点类型**：`dir(ast)` 具体类，剔除 3.8 前废弃别名与非语法面
- **31 个无独立节点的语句形态**（全名册 = `docs/refactor/syntax-coverage.json` `covered_extra_forms` + except\*）：elif 链、for-else、while-else、多目标赋值、多上下文 with、增量赋值、链式比较、海象、装饰器带参、关键字实参、`*args`、`import *`、相对导入、global/nonlocal、切片、f-string 转换符、async 五件套（def/for/with/await/yield from）、多重 for 推导、try-finally-only、match+守卫+8 模式（value/singleton/sequence/mapping/class-keyword/or/capture/star）、except\* 异常组
- **三条"永不"**：永不取自实现自身 `RegionType` 枚举、永不取自语料、不随嵌套深度/组合膨胀

### II.3 三级判定（评审结论只有这三态）

| 级别 | 判据 | 计入分子 |
|------|------|---------|
| **完备** | 三路径存在 ∧ 无破口证据 | ✅ |
| **破口** | 三路径存在 ∧ 不变式破坏有确证（锚点+机制） | ❌ |
| **零能力** | 任一路径缺失 | ❌ |

数字规则：路径层由 `tools/kb/syntax_coverage.py` 实测（→ `syntax-coverage.json`）；不变式层由台账 §5 汇总；**禁止手改数字，禁止页面间矛盾数字**。

### II.4 三路径与 T1–T8（每形态的完备证据链）

- **T1 识别路径**：`RegionType` 枚举 19 类（`region_analyzer.py:170-189`）+ `_identify_*` 十族（锚点见 III.1）
- **T2 归约路径**：`Region.add_child:221`、臂收集+汇合剪枝、handler 归并、`_find_loop_else:5242`、孤儿块释放+守卫
- **T3 生成路径**：dict 工厂（If/While/Try/Match/elif/Break/Continue/Lambda/ListComp）→ `ast_converter.py` dict→AST → `code_generator.py` 发射
- T4 归约只消费 L(A)（C1/C3）/ T5 子区域黑箱（C2）/ T6 非局部信息守卫封闭（C3）/ T7 归纳基（门禁旁证）/ T8 生成递归于区域树

### II.5 三维度禁止互替

**语法完备**（本规范）/ **结构正确率**（sstrict 缺陷口径）/ **字节等价**（门禁口径）——三个维度独立测量，任何一方读数不得反驳另一方。

### II.6 承接读数基线（旧规范 round10 终态 f831eeae，2026-10-04 承接；基线快照实测复核逐位一致）

**承接事实修正（Task 0 实测确认）**：旧规范 Round 10 已完成终审归档（提交链 72f46912→b53d449c→0caea12b→f831eeae + 网络故障记录 fc2aa1b1），唯 push 因 github.com:443 网络中断未竟（待推送 f831eeae/fc2aa1b1，本轮 push 时一并补推）；wiki §8.2 复审六步已在旧 round10 全量执行（口径 v6：形式层 128/128 = 100%，B1 族升格已封闭；组合级挂账 25 号透明分层不计入形式层分母）。本规范 Round 1 定位由"承接旧 Round 10 未竟终审"修正为"round10 终态承接复验"（v6 口径核对 + 残余名单实测 + 覆盖矩阵盘点 + 合规审计），Round 10 终审做全量重验与增量更新而非首跑。

| 读数 | 值 |
|------|-----|
| 402 全量单元级 | 6554/6617（99.05%）；文件级 369/402（Task 0 fresh 复核逐位一致） |
| 小测试集 34 pyc | 1505/1568（Task 0 fresh 复核一致） |
| quotation.pyc | 152/153（唯一失败 change_his_to_forward 基线一致） |
| tests 六套件 | 277 passed / 2 failed（基线名单 test_B01 + test_BOUNDARY_02）/ 2 xpassed |
| 路径存在 | 128/128（syntax-coverage.json 实测，旧 round10 §8.2 第 4 步重跑确认） |
| 台账不变式（v6） | 形式层 完备 128 / 破口 0 / 零能力 0 = 100%；组合级挂账 25 号透明分层（见 III.5）；已封闭：B1b/B6/B8/B9/B10/B11/B20–B25/B29–B35/B37–B40/B45/B48/B54/B55/B64/B66/B67/B68/B72 等 |
| 哨兵面（站桩回归基线） | round6 全量 16 pyc = 115/115、round7 108/128、round8 110/118、六哨兵 + option_account 302/308 |

### II.7 评审反模式 = 知识库 13 条误解清单（对抗时逐条对准）

循环论证分母 / 有过就算 / 语料证据口径 / 无限分母 / 节点词汇当完备 / 浅层测试当无感证明 / 门禁读数当完备性 / 顶层构造粗清单 / 识别率当完备性 / 维度互替 / 改工具不改方法 / 错误检测标准（3.11 的 except\* 标记 = CHECK_EG_MATCH/PREP_RERAISE_STAR/is_except_star，禁用 3.12 的 PRELOAD_RERAISE）/ 语料上限当能力上限。评审工程师宣告"完备成立"前必须逐条自查未犯任何一条；宣告"破口"必须给出锚点+机制+违反条款。

---

## 理论基准 III：对抗目标台账（wiki §5 标榜完备形态全名单，锚点 2026-09-29 审计）

### III.1 `_identify_*` 十族识别方法（对抗与注释审计的对象）

| 方法族 | 锚点（region_analyzer.py） | 覆盖形态 |
|--------|------|---------|
| `_identify_conditional_regions` | `:15981` | If / elif 链 |
| `_identify_loop_regions` | `:3782`（for-else/while-else `_find_loop_else:5242`、clamp `:5105`） | For/AsyncFor/While/loop-else |
| `_identify_try_except_regions` | `:7603`（空体 finally `:9016`、`_find_try_else_blocks:10647`；except\* 规则4 `:9731/:9813`、框架块 `:12701-12709`、`exception_handler.py:93-276`） | Try/TryStar/try-finally-only/ExceptHandler |
| `_identify_with_regions` | `:12282` | With/AsyncWith/多上下文 with |
| `_identify_match_regions` | `:12920`（嵌套 match `:14044`、模式解析 `pattern_parser.py`） | Match/match_case/8 模式/守卫 |
| `_identify_assert_regions` | `:14799` | Assert |
| `_identify_boolop_regions` | `:23420`（`_build_boolop_expression:32662`） | BoolOp(and/or) |
| `_identify_ternary_regions` | `:20515` | IfExp |
| `_identify_chained_compare_regions` | `:15495` | Compare 链 |
| `_identify_sequence_regions` | `:27519` | 顺序/直线（含 Break/Continue/Pass/Return 语义 `BlockSemantics:199-201`） |

### III.2 表A — 语句与结构形态（区域管线，台账判"完备"）

Module；If（B2 守卫族已落地）；For/AsyncFor；While；Break/Continue（continue 守卫 `region_ast_generator.py:10289/:10423-10427`）；Try（孤儿 finally 帧 `:9017-9019`）；TryStar except\*（§7 纠正在案，全链锚点 = 识别 `:9731/:9813`、归并 `:7891/:8724/:9342/:9915`、生成 `:26839-26843/:27809-27816`、发射 `code_generator.py:702/2079`）；With/AsyncWith；Match；Raise/Assert；Return/Pass/Expr；Delete/Assign/AugAssign/AnnAssign；Import/ImportFrom/Alias；Global/Nonlocal；FunctionDef/AsyncFunctionDef/ClassDef；ExceptHandler；match_case/withitem

### III.3 表B — 表达式形态（表达式重建管线，台账判"完备"除 BoolOp）

BoolOp and/or（**台账唯一破口 B1**）；IfExp 三元；Compare/BinOp/UnaryOp/Constant/Name/Attribute/Subscript/Starred/List/Tuple/Dict/Set/Slice/Index；Lambda；ListComp/SetComp/DictComp/GeneratorExp/comprehension（`comprehension_generator.py` 专用管线）；Call/keyword/arguments/arg；JoinedStr/FormattedValue；Await/Yield/YieldFrom；NamedExpr 海象；上下文叶子 Load/Store/Del + 操作符叶子 32 个（Add…NotIn）

### III.4 表C — 31 扩展形态（台账判"完备"）

elif 链（`IF_ELIF_CHAIN:176`、`'_is_elif'` 标记）；for-else/while-else（`_find_loop_else:5242`、发射 `region_ast_generator.py:4974-5006`）；except\* 异常组；match+守卫+8 模式；多上下文 with；try_finally_only；multi_target_assign；augmented_assign（`code_generator.py:1149` 对照路径）；chained_comparison；walrus；keyword_args；star_args；slice；relative_import；star_import；global_nonlocal；fstring_conversion；nested_comprehension；decorator_with_args；async 五件套（def/for/with/await_expr/yield_from，`:30154`）

### III.5 已封闭守卫族与残余破口承接名单

**已封闭守卫族（站桩回归对象，防回归锚点）**：

| 编号 | 模式 | 落地守卫锚点 |
|------|------|------|
| B2 | If×continue | `region_ast_generator.py:10289/:10423-10427/:10455-10579` |
| B3 | Loop 共享尾 | W14-C `region_analyzer.py:27282/27304/19602`、fix3-T1/T2 `:12945-13075`、fix3-T6 `:18593`、W23 `:19185`、R71-thenover `:22758` |
| B4 | 孤儿子 | `region_ast_generator.py:1593-1663`、`region_analyzer.py:1410-1424/:9017-9019` |

**残余破口承接名单（round10 终态 v6 口径，权威清单 = `harden-completed-forms-10rounds/rounds/round10/REVIEW.md` §4 残留决策表 + `REVIEW2.md`；以 Round 1 评审逐项复验实测为准）**：

- **旧 round10 新封闭**：B72（nonlocal，co_freevars/co_cellvars + STORE_DEREF 元数据判据）、B48 主形态（in-place BINARY_OP oparg 13-25 + AugAssign 发射）、B64（B68 修复覆盖实测划除）、B46 部分（true 臂嵌套三元对称放行，净 +7 单元）
- **实施降级未封闭（取证在案 D:\Temp\r10_incond.py / r10_then38.py）**：B71（finally 体仅含循环控制 fin_continue/fin_break 发射归属层，W11-A 认领分支）、B46 尾项（t_nest_in_condition 融合条件三件套）
- **旧 round10 新登记未封闭**：B73（try 四段 import 宿主泄漏）、B74（match case 体首 import guard 幻影）、B75（try 宿主 global 声明 + finally 条件段归属错位）、B76（augassign × BoolOp RHS 体蒸发）、B48 残留变体（r7_08 t_host_while_body while 体宿主）
- **沿袭残留（round10 复核逐位持平；Round 1.1 复验补录 B52/B53/B63——round10 决策表有残留实测但 v6 初稿漏列）**：B42×3 / B43 / B44 / B47 / B49 / B50 / B51 / B52 / B53 / B56–B62 / B63 / B65 / B69 / B70 / B11-R2（r4_or4_and2 1/2）
- **零专攻形态组 6 组（round10 覆盖矩阵如实登记，本规范 Round 2–9 主题输入）**：Module 专攻、ClassDef 体专攻、AnnAssign、fstring_conversion、keyword_args/star_args、decorator_with_args
- **挂账**：组合级挂账 25 号（上列未封闭部分 + 残留单元）+ round7 残留登记面 81/117，按 wiki §8.3 状态机继续推进
- **新登记自 B77 续接**（B71–B76 已用尽）

---

## 理论基准 IV：字节码一致性与验证门禁

### IV.1 分级口径（rules.md §五，强制性）

- **归一化口径（主，交付确认）**：L1 + 跳转目标等价 + 常量 set/frozenset 等价 + module 委托比较
- **L1 严格口径（辅助诊断）**：跳过 CACHE，保留 NOP/EXTENDED_ARG，跳转目标绝对，常量严格
- **NOP/EXTENDED_ARG 差异必须逐项核查**（往往是控制流语法不正确），唯一可豁免 = PEP626 多行签名行追踪 NOP；理论极限 = frozenset 元素顺序/地址

### IV.2 验证判据与门禁自检

- **判据唯一** = `F:\Downloads\pythoncdc-main\scripts\pyc_verify.py`（single / batch --index --json / compare --before --after / selfcheck）
- **门禁自检清单**（rules.md §6.2 适用项，每轮修复批与主代理验证各执行一次）：IMPORT_OK、COMPILE_OK（产物 `compile()` 通过 + BOM `efbbbf` 单头完整）、repro 全 match、G0 自检（六项 docstring、无 self 新状态、无跨层反查、无白名单、无 start_offset 阈值、ast+py_compile）、G3/G4 反模式自检（0 新增前缀方法、0 硬编码上限）、影响面实测（全部产物逐字节比对，只有目标单元 sha 变化 = 零回归字节级证据）

---

## What Changes

- 新建本规范承接旧规范 Round 10 终态（已完成归档，唯 push 未竟，本规范 push 时补推 f831eeae/fc2aa1b1；本规范 Round 1 = 终态承接复验轮），历史归档全部保留、禁止回滚
- 优化迭代流程（相对旧规范的四点变化）：
  - **修复工程师多位协同**：单轮评审登记 ≥2 个互不相交破口族（破口族不相交 ∧ 涉改文件不相交）时并行派发，合并后统一验证
  - **站桩回归常设化**：每轮强制重放已封闭破口登记探针面（round6 全量 16 pyc = 115/115、round7 108/128、round8 110/118、round9 50/50、round10 修复面（B72 23/23、B48 面、B46 面）及本规范已完结各轮），读数不得变差，不再单设回归轮
  - **注释合规入对抗面**：识别/生成方法 docstring 六项模板（I.7）与代码行为不一致 = 打回项，设专轮全量审计
  - **主代理零实现**：主代理只做调度、阶段边界提交、全量验证、归档 push
- 对抗优先级：零专攻形态组 6 组（Module 专攻、ClassDef 体专攻、AnnAssign、fstring_conversion、keyword_args/star_args、decorator_with_args）→ 台账 §5 判"完备"形态（表A/表B/表C 全名单见 III.2–III.4）→ 已封闭守卫族（B2/B3/B4）深度外推 → 残余破口族（III.5）
- 破口登记 Bn 续接（自 B77 起），走 wiki §8.3 状态机（未定位→已定位→已落地→已复审）；每轮封闭破口随轮更新台账；Round 10 终审统一执行 wiki §8.2 复审六步全量重验与增量更新（旧 round10 已执行 v6 首跑；本规范 = grep 全部落地标记核验（含 B77+）→ 台账更新 → syntax_coverage 重跑 → 占比重算 → 数字同步 → log 记录）

## Impact

- Affected specs: `harden-completed-forms-10rounds`（Round 10 已完成归档、唯 push 未竟；本规范 Round 1 承接其终态复验、Round 10 承接终审重验与增量更新；归档保留，禁止回滚）
- Affected code: `core/cfg/region_analyzer.py`、`core/cfg/region_ast_generator.py`、`core/cfg/comprehension_generator.py`、`core/cfg/code_generator.py`、`core/cfg/exception_handler.py`、`core/cfg/pattern_parser.py`
- Affected wiki: `wiki/concepts/decompile-invariant-completeness.md`（台账判定、破口登记、占比重算、§8.2 六步、log）
- 小测试集 = 34 个未完全 OK 的 pyc（`harden-completed-forms-10rounds/baseline/failing_index.json`），仅供子代理回归自测；全量验证（402）由主代理执行

## ADDED Requirements

### Requirement: 三方角色与主代理纪律

主代理 SHALL 只承担：调度子代理、阶段边界本地提交、全量验证（无回退判定）、归档提交与 push；禁止执行任何修复/评审实现任务，子代理故障时重试派发或如实上报，不得代笔。修复工程师 SHALL 只做区域归约算法内修复（受理论基准 I 全部条款约束），可多位协同：并行派发判据 = 破口族不相交 ∧ 涉改文件不相交，合并后统一过验证序。评审工程师 SHALL 独立于修复工程师，对树中一切代码（含在途未提交变更）攻击；修复工程师对评审结论不得协商通容，只能以更优算法修复回应或举证反驳。

#### Scenario: 一轮完整闭环
- **WHEN** Round N 启动
- **THEN** 顺序 = 主代理本地提交 → 建 `rounds/roundN/` → 评审工程师对抗攻击 + 合规审计（REVIEW.md）→ 修复工程师 1..m 位算法修复 + 注释合规（FIX.md，可多份）→ 评审工程师复核（通过/打回，REVIEW2.md）→ 主代理全量验证无回退（VERIFICATION.md）→ 归档 → 提交并 push origin main

### Requirement: 评审工程师独立对抗审查

评审工程师每轮 SHALL 执行两类审查，结论只有「通过 / 打回」两态，打回必须给出锚点（file:line）+ 违反条款编号（I.1–I.7 / C1/C2/C3 / 13 条误解编号）+ 机制说明：

1. **完备形态攻击**：按本轮主题从台账 §5 已判"完备"形态（III.2–III.4）中抽取（优先文档标榜完备者、覆盖矩阵空白格），每形态构造 ≥10 个最小复现（深层嵌套/交叉组合，深度 ≥3）+ ≥2 个 MATCH 负对照，实测「深层与浅层产物结构一致」（C2 判据）；复现存 `test_repros/roundN/`，结果入 `rounds/roundN/REVIEW.md`。宣告"完备成立"前 SHALL 逐条自查 13 条误解（II.7）未犯
2. **算法合规审计**：对当前树逐守卫审查 I.4 黑名单五项 + 注释六项模板与代码一致性 + BOM/插桩/在途变更，发现即打回，零容忍

站桩回归（常设）：每轮 SHALL 重放前序已封闭破口的登记探针面（round6 115/115、round7 r7 面、round8 r8 面、round9 50/50 及本规范已完结各轮攻击面），读数不得变差。

#### Scenario: 对抗发现伪完备
- **WHEN** 台账判完备的形态在深层嵌套探针下与浅层产物结构不一致
- **THEN** 按 II.3 登记 Bn 破口（锚点+机制+违反条款），修复工程师按 I.3 推论封闭守卫恢复无感（禁止个案补丁）

#### Scenario: 注释与代码不一致
- **WHEN** 识别/生成方法 docstring 六项模板中任一项与实际代码行为不符，或缺失 C1/C2/C3 条款声明
- **THEN** 评审工程师打回，修复工程师以代码真实算法为准修正注释、或以注释声明的正确算法为准修正代码——两者必居其一，禁止含糊

### Requirement: 修复工程师算法修复

修复 SHALL 满足理论基准 I 全部条款：
- 只在区域归约算法内进行；判据只取 I.4 白名单（同层结构事实：块末指令 opcode、后继前驱集合、异常边、区域成员关系）
- 修复语义 = 封闭守卫、恢复 C1/C2/C3（I.3/I.6），不是补语料个案；修复后无需逐深度验证（归纳论证）
- 触及方法 docstring 六项模板齐全 + C1/C2/C3 条款（I.7）；落地声明必须写明「代码已落地」（I.6）
- 自测门禁 = 本轮全部 MISMATCH 复现转 MATCH ∧ 负对照保持 MATCH ∧ 小测试集（34 pyc）无回退 ∧ 站桩回归面不变差 ∧ IV.2 门禁自检清单全过（IMPORT_OK/COMPILE_OK/BOM 单头/无遗留插桩/G0/G3/G4/影响面字节级抽验）

#### Scenario: 算法合规
- **WHEN** 修复方案依赖「目标函数名 == 'xxx'」类判据或 start_offset 魔法阈值
- **THEN** 评审工程师直接打回，改用同层结构事实判据

#### Scenario: 深层才错
- **WHEN** 缺陷仅在嵌套深度 ≥2 时出现，浅层正确
- **THEN** 判定为 C1/C2/C3 破坏（I.3 推论），修复方向 = 定位被破坏条款并封闭守卫，禁止在生成层按深度加特判

### Requirement: 主代理无回退验证

主代理每轮 SHALL 亲自执行验证序（判据唯一 = `scripts/pyc_verify.py`，所有命令 ≤300s，超时分片）：

1. 小测试集（34 pyc）batch 验证：无 success→failure 位移
2. 全量 402 分片 batch（每片 ≤300s）+ `pyc_verify.py compare --before <基线报告> --after <本轮报告>`：**REGRESSIONS=0**
3. `quotation.pyc` 单验通过（无新增失败，承接基线 152/153）
4. 现有区域相关测试（tests/ 下六套件）：零新增失败（基线名单 test_B01 + test_BOUNDARY_02）
5. IV.2 门禁自检（G0/G3/G4、BOM、影响面抽验）
6. 汇报读数：单元级成功率、文件级 success 数、本轮封闭破口数、站桩回归读数、完备占比变动（如涉台账判定变更）

#### Scenario: 回退拦截
- **WHEN** 批量回归出现任一 success→failure 位移或单元数下降
- **THEN** 本轮修复不得合入，打回修复工程师定位根因

### Requirement: 每轮门禁与推进纪律

- 每轮独立文件夹 `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/roundN/`（REVIEW.md、FIX.md（可多份）、REVIEW2.md、VERIFICATION.md）；复现在 `test_repros/roundN/`
- 调用子代理前必须先本地提交（含阶段边界：评审后、修复后各一次）
- 每轮必须产出 ≥1 个被登记并封闭的破口，或 ≥1 个 pyc 读数改善；两者皆无 = 本轮未过门禁，禁止开启下一轮
- 每轮结束必须提交并 push 到 origin main；commit message 前缀 `rr-v2rNN:`
- 所有命令 ≤300 秒，超时必须分片
- 禁止手改 `*OK.py`、禁止修改反编译生成文件、禁止跳过验证、禁止虚报读数、禁止投机取巧；必须逐步进行

### Requirement: 台账推进与终态

- 每个确认破口按 wiki §8.3 状态机推进（未定位→已定位→已落地→已复审），只有走到已复审才允许计入完备分子；每轮封闭的破口随轮更新台账判定
- Round 10 终审 SHALL 统一执行 wiki §8.2 复审六步全量重验与增量更新（旧 round10 已执行 v6 首跑）：grep 全部落地标记（含本规范各轮「代码已落地」声明与 B77+ 核验，I.6）→ 台账（§5）全量更新 → `tools/kb/syntax_coverage.py` 重跑 → 完备占比重算 → wiki 页面数字同步（禁手改、禁矛盾数字）→ log 记录
- 终态目标：残余破口（III.5 名单及 B77+）全部封闭或经对抗证伪降级；台账 128 形态全部经对抗验证仍成立 = 完备占比 128/128（形式层）且组合级挂账清零或如实分层；`_identify_*` 十族方法注释六项模板全量过审

## MODIFIED Requirements

无。

## REMOVED Requirements

无（历史规范与归档全部保留；对旧规范目录的既有状态不回滚）。
