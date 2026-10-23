# Python 字节码反编译规则文件（Region Reduction Rules）

> 基于「No More Gotos」(Launez et al., 2013) 区域归约算法，结合 Python 3.11 字节码特性，
> 经 quotation.pyc 迭代（R21-R26）与 2026-09-29 完备性审计实证总结。本文件是反编译器的强制性工程规范。
> 完备性总纲（理论、128 形态台账、破口登记、迭代机制、可用资源）：`wiki/concepts/decompile-invariant-completeness.md`。
>
> **2026-10-23 更新（v9 攻击审计后）**：`attack-completeness-claims` 已把 v8 的 **128/128 = 100% 降级为「形态基线达成（v8 口径）」**，不再作为完备依据。v9 双读数：形态基线 128/128（历史）；判定空间 J v2 全量 **0/1556 covered**、集成样本 **51/1556（3.28%）**、语义样本 **45 EQUAL / 6 DIFF**；G4 **339 条 0 proved**；G6 **20/24 FAIL**（local-bootstrap）；`overall=BLOCKED`。**完备必须同时满足 G1–G6；当前不满足，禁止写「完备」。** 历史 v8 证据：402 八分片 6617/6617、small34 1568/1568、quotation 153/153、pytest 基线名单、IV.2 全绿（本轮未重跑，见 §8.3）；B163–B219 共 57 项未封闭；B142 由 B181 重新定性为形态级缺口。

---

## 一、核心设计原则

### 1.1 区域化分析（Region-Based Analysis）
基于编译器理论中的区域分析算法，将 CFG 分解为层次化的区域。每个区域是一个单入口的子图。

### 1.2 四大算法原则（强制性，不可违反）

| 原则 | 内容 | 违反后果 |
|------|------|---------|
| **原则1：自底向上归约** | 从最内层到最外层识别区域（归约顺序）。内层区域先归约，交付给外层作为抽象节点 | 嵌套结构错乱，内外层条件合并错误 |
| **原则2：每块唯一归属** | 每个基本块在任何层级只属于一个区域。归约时标记 `generated_blocks`/`generated_offsets` 避免重复处理 | 块被多个区域争抢，语句丢失或重复 |
| **原则3：嵌套即抽象节点** | 嵌套区域在其父区域中作为单个抽象节点表示。归约后父区域的 then/else 列表引用子区域的入口，而非所有块 | 父区域展开子区域内部，结构坍塌 |
| **原则4：入口引用语义** | 每个区域类型对应唯一的 AST 节点类型。入口块引用语义显式表达（如 Continue 节点引用回边 entry） | 语义隐式化，条件合并逻辑误吞并 |

### 1.3 单向数据流
分析结果从底层向上层传递，**不回溯修正**。每个结构在识别阶段就正确分类，不需要后处理修正。

### 1.4 算法驱动
用算法替代模式匹配，用数学性质替代启发式规则。**禁止跨区域跨层次的启发式规则，禁止破坏算法对嵌套的天然支持**。

### 1.5 嵌套无感不变式（强制性，2026-09-29 新增）

**要求：程序对嵌套与不嵌套必须完全一样处理；处理对嵌套应是无感。**

| 条款 | 要求 | 与四原则的关系 |
|------|------|---------------|
| **C1 局部消费** | 归约 R(A) 只读 `L(A) = A.blocks ∪ A.out_edges ∪ A.exception_table` | 原则2/4 的强化 |
| **C2 黑箱组合** | 子区域只经 entry/exit 接口被父级消费，父级不窥视子区域内部 | 即原则3 |
| **C3 守卫封闭** | 必须参考非局部信息时（汇合块被区域外引用、continue 目标跨区域、fall-through 是别区域 entry），必须有显式守卫排除/认领 | 新增显性要求 |

**归纳论证**：C1+C2 成立时，一层正确（归纳基）+ 组合封闭（归纳步）⇒ 任意深度/任意组合正确。嵌套深度与组合数**不进入任何能力边界或测量分母**。

**推论（强制）**：凡"深层才错、浅层没事"的缺陷 = C1/C2/C3 某条被破坏。修复方式 = **封闭守卫恢复无感**，不是给语料个案打补丁。修复后无需逐深度验证。

---

## 二、禁止事项（反模式，G3/G4 自检）

### 2.1 禁止的方法命名前缀
```
_fix_ / _merge_ / _patch_ / _fallback_ / _hack_ / _workaround_ / _temp_
```
新增方法不得使用以上前缀。修复必须修正 region 边界判定，不得用补丁式后处理。

### 2.2 禁止硬编码深度上限
```python
# 禁止
if depth > 10: ...     # 硬编码深度上限
if count > 100: ...    # 硬编码计数上限
```
区域归约的终止性由区域数量有限性保证，不得引入硬编码上限（也是 C1 的必然结论：无感处理下深度无关）。

### 2.3 禁止跨区域启发式
- 不得在外层区域识别时直接处理内层区域的块
- 不得用「如果某块满足某模式则特殊处理」的启发式规则
- 不得破坏嵌套区域作为抽象节点的语义

### 2.4 完备性测量反模式（2026-09-29 新增，2026-10-23 扩为 17 条误解清单的工程禁令形态）

| 禁止 | 理由 |
|------|------|
| 拿实现自身 `RegionType` 枚举当覆盖分母 | 循环论证；分母 = 语言语法面 128 形态（97 ast 节点 + 31 扩展形态） |
| 节点类/构造引用存在即判"能处理" | 有过就算；分子判据 = 三路径存在 **∧** C1/C2/C3 成立 |
| 用语料命中/门禁读数定义能力边界 | 正确性 ≠ 完备性，语料深度上限 ≠ 程序能力上限 |
| 把"任意嵌套组合"当无限分母 | 无感不变式下由归纳覆盖，分母不随深度/组合膨胀 |
| 用 3.12 操作码当 3.11 检测标准 | `PRELOAD_RERAISE` 是 3.12 的；**3.11 的 except\* 标记 = CHECK_EG_MATCH / PREP_RERAISE_STAR / is_except_star** |
| 把 v8 形态基线 128/128 写成「完备 100%」 | 形态计数不承载语义/J 覆盖/变异/规则证明；v9 已降级为历史回归口径 |
| 把 51/1556 集成样本写成 J 全量或语义完备 | 样本省略 C1 缺失项；全量 9.3 读数是 0/1556 covered |
| 把 local-bootstrap 24 条 canary 写成独立 G6 证据 | 生成/保管/轮换同源 ⇒ 共同原因未排除；G6 当前 FAIL |
| 把 339 条规则枚举写成 G4 已证 | `proved=0/open=339`、无 rule traces；G4 INCONCLUSIVE |

完整 17 条（含每条的错误做法/为什么错/正确做法）：`wiki/concepts/decompile-invariant-completeness.md` §3。

---

## 三、区域类型与归约规则

### 3.1 区域类型分类（对齐 `RegionType` 枚举 19 类；锚点 **2026-10-21 逐条重核**，v3 十轮改动后重定位）

| 区域类型 | 对应语法 | 识别函数（`region_analyzer.py` 锚点） |
|---------|---------|--------------------------------------|
| IfRegion（IF/IF_THEN/IF_THEN_ELSE/IF_ELIF_CHAIN） | `ast.If` / elif 链 | `_identify_conditional_regions` `:21221`（链式判定 `_check_elif_chain` `:24427`；boolop 条件链 `_detect_boolop_conditional_chain` `:32488`） |
| LoopRegion（FOR_LOOP/WHILE_LOOP） | `ast.For`/`ast.While` | `_identify_loop_regions` `:5267`（for-else/while-else：`_find_loop_else` `:7257`；try 内收敛 `_clamp_loop_else_to_enclosing_try` `:7120`） |
| TryRegion（TRY_EXCEPT/TRY_FINALLY） | `ast.Try`（含 except\*） | `_identify_try_except_regions` `:10219`、else 段 `_find_try_else_blocks` `:13800`（finally 正常副本 `_find_finally_normal_copy_blocks` 在 `region_ast_generator.py:35000`） |
| WithRegion | `ast.With`/`ast.AsyncWith` | `_identify_with_regions` `:15784` |
| MatchRegion | `ast.Match` + 8 模式 | `_identify_match_regions` `:16486`、嵌套 match `_identify_nested_match_regions` `:18447`（模式解析 `core/cfg/pattern_parser.py`） |
| AssertRegion | `ast.Assert` | `_identify_assert_regions` `:19784` |
| BoolOpRegion | `ast.BoolOp` | `_identify_boolop_regions` `:29451` |
| TernaryRegion | `ast.IfExp` | `_identify_ternary_regions` `:26247` |
| 链式比较区域 | `ast.Compare` 链 | `_identify_chained_compare_regions` `:20595` |
| SEQUENCE/BASIC/BREAK/CONTINUE/PASS/RETURN | 顺序/直线/跳转语义 | `_identify_sequence_regions` `:35588` + `BlockSemantics` |

> 锚点维护规则：任何触及 `core/cfg/**` 的批次结束后，必须重核本表行号并随批次提交更新（v3 R2–R8 期间本表已滞后两轮，R9 落账时统一重核）。

### 3.2 IfRegion 归约规则

#### 3.2.1 then/else 边界判定（R24 缺陷A、R25 缺陷2）
- **then-region 边界止于 then 分支末尾的 JUMP_FORWARD 跳转点**
- 循环体内 if/elif/else 链的**公共汇聚后继块保留为循环体兄弟语句**，不得并入 then 分支
- else-region 边界**包含其体内所有语句**（含尾部 for 循环），不得把 else 体内尾随循环外提到 if/elif/else 之后
- 判据：`_check_elif_chain`（`region_analyzer.py:24427`）中 `inner_merge ≠ merge_` 时阻止 elif 链构建，尾随语句保留 else 体内

#### 3.2.2 if-continue 兄弟语句（R23 修复；B2 守卫族）
当 IfRegion.merge_block 是当前循环的 back_edge_block（纯 JUMP_BACKWARD）且无 else_blocks 时：
- 两分支均→回边（continue 无条件）
- 生成显式 `Continue` 兄弟节点，标记回边块已生成
- 防止条件合并逻辑把 `[inner_if, Continue]` 误合并为 `if A and B:`

判据（全部满足才触发）：
1. `_current_loop is not None`（循环上下文中）
2. `merge == back_edge_block`（merge 是循环回边）
3. `back_edge 仅含 JUMP_BACKWARD`（纯 continue 回边）
4. `not else_stmts`（无 else，两分支均→回边）

continue 侧守卫族（防回归锚点，2026-10-21 重核）：`_block_is_continue_target` `region_ast_generator.py:14832`（调用点 `:13715-13733/:14205`）、continue 目标排除 loop_else `:14985-14988`、`_loop_else_set` 交互 `:14985-14990`。

#### 3.2.3 'and' 复合条件处理（R26 缺陷3）
- **统一不拆分**任何 `and` 复合条件，保持 `if A and B:` 形式
- 禁止只对 if 首条拆分（外层 `if A:` + 内层 `if B:`）而 elif 保留冗余 `and`
- 'and' 链检测（Step6）+ `main_inline_boolop_chain`（`region_analyzer.py:32488` 一带）存入 IfRegion
- `generate()` 入口：当 IfRegion.entry 是 entry_block 且存在以 entry_block 为首块的 inline_boolop_chain 时，让 `_if_generate_normal`（`region_ast_generator.py:25234`）统一处理

### 3.3 LoopRegion 归约规则

#### 3.3.1 while 条件 boolop 链（R24 缺陷B；v3 R8 修订 B162）
`_detect_while_condition_boolop_chain`（`region_analyzer.py:30247`）反向链回溯：
- **判据**：`if not cond_in_loop: break`
- 合法 while-boolop 前驱的 fall-through 恒为下一条件块（在循环内，`cond_in_loop` 恒真）
- `cond_in_loop=False` 仅出现在外层 if/elif/while 嵌套场景，此时前驱是外层 if/elif 条件块，须由 IfRegion 归约（原则2 + 原则3）
- **链完成判据（R8/B162 修订，强制）**：多成员 or/and 链的**完成**以**链尾**为准——链尾块（`chain[-1][0]`，其 TRUE 边进入循环体）必须 fall-through 到 `loop.header_block`；**禁止**以链首 fall-through 等于 header 作为完成判据（该判据只在单成员链成立，多成员链会把整条 or/and 链误判为普通条件而丢链）。完成后走与单成员链同路的 Phase-7-E 归并与块重注册，不得另起分支。

#### 3.3.2 循环后顺序语句
- 循环正常退出后、且后继块仍位于外层 if/elif/else 同一子分支内（未被外层分支的 JUMP_FORWARD to return 截断）时
- 后继条件块作为循环后的子分支内顺序语句保留在原分支内
- **不得外提为兄弟，不得把 while 条件并入外层 elif**

#### 3.3.3 loop_else 边界
- `_find_loop_else`（`:5242`）的 else_blocks/natural_exit 边界判定须精确；try 内循环经 `_clamp_loop_else_to_enclosing_try`（`:5105`）收敛
- 不得把 else 子分支的 while 回边链误判为 loop_else

### 3.4 嵌套区域作为抽象节点
- 嵌套区域归约后，父区域的 then/else 列表引用**子区域的入口**，不是子区域的所有块
- 外层 IfRegion 引用 `[inner_if, Continue]` 作为 then_stmts（不是展开内层 if 的所有块）

### 3.5 except\* 异常组规则（2026-09-29 新增，审计确证全链已实现）

**检测标准（3.11）**：`CHECK_EG_MATCH` / `PREP_RERAISE_STAR` / `is_except_star`。**禁止**用 `PRELOAD_RERAISE`（3.12 操作码）当 3.11 判据——曾因此误判"未实现"。

| 层 | 锚点（2026-10-21 重核） |
|----|------|
| 识别 | `region_analyzer.py:8043`（块含 CHECK_EG_MATCH ⇒ except\* 分支；3.11 操作码集合 `:1217`）、`exception_handler.py:50`（`_find_handler_type_load`：handler 异常类型 LOAD_GLOBAL 定位）、`:114`（`identify_try_except_simplified` handler 提取） |
| 归约 | handler_type `'except_star'` 与普通 except 同路并入 TryRegion：`region_analyzer.py:10219`（Try 识别）/`:13800`（else 段）；except\* 框架指令上下文判定 `region_ast_generator.py:37923-37927`（CHECK_EG_MATCH/PREP_RERAISE_STAR） |
| 生成 | `region_ast_generator.py:36425`（`handler_node['is_except_star'] = True`） |
| 发射 | `code_generator.py:702`（**`except_keyword = 'except*'`**，`:713-717` 表头发射） |

---

## 四、docstring 统一模板（6 项）

每个 `_identify_*_regions` / `_generate_*` 方法必须有完整 docstring，包含 6 项：

```python
def _identify_xxx_regions(self, ...):
    """
    ①算法依据：No More Gotos 第 X 章 + 4 原则条款 Y
    ②归约顺序：自底向上，内层区域先归约
    ③唯一归属判定：[具体的块归属判定逻辑]
    ④嵌套处理：[嵌套区域如何作为抽象节点]
    ⑤入口引用语义：[入口块引用语义]
    ⑥反编译流程：[本方法在整个反编译流程中的位置]
    """
```

---

## 五、字节码一致性比较规则

### 5.1 分级口径（强制性）

| 口径 | 用途 | 规则 |
|------|------|------|
| **归一化口径（主）** | 交付确认 | L1 + 跳转目标等价 + 常量 set/frozenset 等价 + module 委托比较 |
| **L1 严格口径（辅助诊断）** | 发现真实缺陷 | 跳过 CACHE，保留 NOP/EXTENDED_ARG，code 递归忽略元数据，跳转目标绝对，常量严格 |

### 5.2 合理豁免项（永远合理）

| 豁免项 | 理由 |
|--------|------|
| 跳过 CACHE | CPython inline cache slot，重编译必然重新生成 |
| code 递归忽略元数据 | co_filename/co_firstlineno/运行时地址不可恢复 |
| 跳转目标等价 | 覆盖 CPython 重编译对齐偏移（修复真实缺陷后仅剩合理偏移）|
| 常量 set/frozenset 等价 | CPython 常量折叠，set literal 是正确还原 |

### 5.3 NOP/EXTENDED_ARG 差异必须逐项核查（强制性）

**NOP 增减往往是控制流语法不正确导致**，不可一概豁免为"对齐偏移"：
- R25 缺陷2（build_future_fill_time）：5个 JUMP_FORWARD 跳错目标 → 真实 NameError 缺陷
- R26 缺陷3（one_prod_to_dataframe）：EXTENDED_ARG +1 → 真实 AST 形状不一致

**唯一可豁免的 NOP 差异**：PEP626 装饰器+多行签名续行行追踪 NOP（行号是原始源码行号，反编译器无法恢复原始排版）

### 5.4 理论极限（不可恢复）
| 差异类型 | 原因 |
|---------|------|
| PEP626 多行签名 NOP | 原始源码行号不可恢复，反编译产物行号从1开始 |
| frozenset 元素顺序/地址 | CPython 哈希决定，不可控 |

---

## 六、迭代修复流程规则

### 6.1 双工程师分工
- **测试工程师**：反编译 + 字节码 diff + 最小复现实例（≥10个）+ 根因初判
- **修复工程师**：按区域归约算法修复 + docstring 更新 + 回归验证

### 6.2 验证清单（每轮必须，2026-10-23 更新为 v9 终审门禁）

1. IMPORT_OK（`import core.cfg.region_analyzer; import core.cfg.region_ast_generator`）
2. COMPILE_OK（反编译产物 `compile()` 通过；BOM `efbbbf` 保持）
3. repro 全部 match（真实失败单元单函数切片 + 负例两臂逐字节相同）
4. **官方 41 靶 h62**：SAME/IMPROVED/REGRESSION/ERR 全 0 退化（regained/lost 均空）
5. **sstrict 34 pyc / 1528 函数**：defects 不增，RESOLVED 只增真修复
6. **battery 82** 复现 landed vs 基线 worse=0；**金丝雀 4/4** sha16 全中

> 4–6 项为历史基线（round75/fix1 口径，留档监控）；**v3 十轮的实际放行门禁 = 第 11–14 项**（402 八分片 + small34 + quotation + pytest + IV.2 + 25 行矩阵/组合终表 + I.4 证据纪律 + 守卫过宽自捕获）。
7. 归一化口径不退化（≥ 上轮）；L1 严格口径逐项核查
8. G0 自检：三要素 docstring、无 self 新状态、无跨层 `X.entry in Y.blocks`、无 .py/函数名白名单、无 start_offset 阈值、ast+py_compile、git status 已跟踪程序文件零改动
9. 反模式自检（G3 0 新增前缀方法，G4 0 硬编码深度上限）
10. **影响面实测**：全部产物逐字节比对，只有目标单元 sha 变化（零回归的字节级证据）
11. **v3 门禁（E 编排，强制）**：402 语料八分片 **6617/6617 files_failure=0**；small34 **1568/1568**；quotation **153/153（rc=0）**；pytest 七套件**基线名单一致**（2 failed 在放行名单）；IV.2 全绿（BOM 单头 / G3=0 / instrumentation code 命中 0）
12. **v3 形态面（强制）**：25 行矩阵（每行 ≥1 深层 ≥3 级宿主探针 + 负对照）全绿；组合级 25 号终表 + 另册口径差并入全数处置；17 误解逐条自查零触犯
13. **v3 证据纪律（强制）**：每个机制给出 **I.4 白名单证据**（opcode 顺序 / 跳转极性 / pred-succ / 异常边 / 区域成员 / 注册态）与 C1/C2/C3 归属；语义 hunk 标 `[Bn-V3Rn]`；新方法六项 docstring；**合成非语料探针**须同时交付（防止只在语料上成立）
14. **守卫过宽自捕获**：任何新守卫若在 E 门禁首跑误杀既绿文件，必须按 I.4 收窄后二跑复原，并留二分记录（v3 R5/R6/R7 三次实例：B70g、B139、B145）
15. **v9 语义/覆盖门禁（强制）**：G1 判定空间 C1–C5（0 缺口）、G2a/G2b/G2c 语义差分（0 失败）、G3 变异漏检（0）、G4 规则覆盖（0 open）、G6 独立 canary（24/24 + 0 泄漏）；G5 全量回归（402 八分片/small34/quotation/pytest/IV.2）必须本轮重跑，不得引用历史基线充当本轮结果
16. **v9 当前状态（2026-10-23，禁止写成绿）**：G1 样本 51/1556、全量 0/1556；G2a 45 EQUAL / 6 DIFF；G2b/G2c UNESTABLISHED；G3 UNESTABLISHED；G4 0/339 proved、INCONCLUSIVE；G5 仅历史基线；G6 20/24、FAIL；`overall=BLOCKED`
17. **v9 诚实性**：任何页面/PR 必须同时标注形态基线（128，历史）与判定空间口径（J 1556，当前未覆盖）；未同时满足 G1–G6 时只能写「形态基线达成」，不得写「完备」「100%」「规则完备」「语义完备」

### 6.3 提交规则
- 每轮必须 commit + push 到远程；commit message 前缀 `rr-rNN:`（v3 规范链用 `rr-v3rNN:`，如 `rr-v3r08:`）
- 修复批归档（batches/fixN）必须包含：缺陷描述、修复方案、验证结果、反模式自检、**破口编号引用（B1/B1b/…）**
- 包含：缺陷描述、修复方案、验证结果、反模式自检
- **v3 补充**：每轮落 `rounds/roundN/FIX.md`（§0–§6 终稿）+ 全部 stamp JSON + 可复跑编排脚本（`final_verify_run_rN.py`）；`tasks.md` 对应 Task 全勾；锚点表（§3.1）随批次更新

### 6.4 修复验收标准（2026-09-29 新增，2026-10-21 增补）

- 修复 = **封闭守卫、恢复 C1/C2/C3**，不是补语料个案；修完按 `wiki/concepts/decompile-invariant-completeness.md` §8 复审对应形态并更新台账
- 落地归档必须写明"代码已落地"或"仅归档 spec 未落地"（防止把已验证 spec 误当已修复代码——B1 教训：fix1 嫁接方案在 jqop1.json 验证通过但代码未落地，树里 `region_ast_generator.py:47639-47643`（**历史行号，2026-10-21 树中该区段已无丢弃版**）曾是丢弃版）
- **v3 增补**：① 判据必须可迁移到同族形态（禁止文件/行号/函数名白名单）；② 每处语义 hunk 标 `[Bn-V3Rn]` 且破口编号连续开档；③ 新方法六项 docstring + 命名不触 §2.1 前缀；④ 交付**合成非语料探针**证明机制不依赖既有语料；⑤ 守卫判据须能被 E 门禁反证（首跑误杀 ⇒ 收窄 ⇒ 二跑复原，二分记录入库）

---

## 七、修复案例与破口索引

### 7.1 R21-R26 案例（quotation 时代，历史索引）

| 轮次 | 缺陷 | 区域类型 | 修复方法 | 原则 |
|------|------|---------|---------|------|
| R23 | get_str_data if-continue 兄弟 | IfRegion | `_if_generate_normal` 检测 merge=回边 | 原则2+4 |
| R24A | change_his_to_backward IF 吸收兄弟 | IfRegion | 循环感知 merge 重算 | 原则2+3 |
| R24B | get_date_and_count LOOP 吸收外层条件 | LoopRegion | `_detect_while_condition_boolop_chain` `if not cond_in_loop: break` | 原则2+3 |
| R25 | build_future_fill_time else 块尾部 for 提升 | IfRegion | `_check_elif_chain` `inner_merge ≠ merge_` + `_generate_if` orelse 守卫 | 原则2+3 |
| R26 | one_prod_to_dataframe and 部分提取 | IfRegion/BoolOp | 方案B 不拆分任何 and + generate() 入口复合 'and' 识别 | 原则1+4 |

### 7.2 破口登记（2026-10-23 更新为 v9 审计态；**v8 形式层开档 0 不代表 v9 完备**）

| 编号 | 状态 | 内容 | 锚点 |
|------|------|------|------|
| **B1a** | **已封闭（防回归监控）** | BoolOp 前导操作数丢弃：`_cjb_skip_inline_if` 真 → extend pre_stmts → return，`_cjb_cond_expr` 丢失（`if A and B or C` 退化）。**嫁接路线已废弃**，改由 `region_analyzer.py` 五臂算法封闭（臂 A/B/B2/C/D/E + `_sb_has_body` 同一谓词，落地标记 `[B1b fix]`/`[B1b fix-r2]`）；**注意：嫁接符号族 `_graft_pending_operand` 仍留在树中（路线废弃、符号未清理），不作为"已落地"判据** | 五臂算法 `region_analyzer.py:21221`（`_identify_conditional_regions`；`_sb_has_body` 同一谓词 `:21255-21258`）、`:32488`（`_detect_boolop_conditional_chain`；`[B1b fix]` 标记 `:32519/:32529/:33140/:33289`）；残留嫁接符号 `region_ast_generator.py:46040` |
| **B1b** | **已封闭（防回归监控）** | 语句上下文 or 臂第二丢弃入口：与 B1a 同批五臂封闭 + B6 四上下文封闭；归档复现 `fix1/synth/neg75_jqcond2.py/.pyc` | 同上 |
| B2 | 已落地（防回归） | If×continue 守卫族 | `region_ast_generator.py:14832`（`_block_is_continue_target` 定义）、调用点 `:13715-13733/:14205`、loop_else 交互 `:14985-14990` |
| B3 | 已落地（防回归） | 共享尾守卫族：W14-C、fix3-T1/T2/T6、W23、R71-thenover | `region_analyzer.py:25199-25208/35351-35373`（W14-C）、`region_ast_generator.py:18379`（fix3-T1）、`:26060`（fix3-T6）、`:26894/62600`（W23）、`:31162-31167`（R71-thenover） |
| B4 | 已落地（防回归） | 孤儿块释放 + 合法子区域守卫 | `region_analyzer.py:304-306/570-571/601`（孤儿块判据）、`:870`（合法子区域）、`region_ast_generator.py:2054-2106/20517-20520` |
| **B129–B162** | **v2–v8 全部封闭** | v3 十轮新开破口族（条件合并 / try-raise-assert 宿主 / await 挂起链 / match-with 幻影 / 循环控制 / 赋值-删除-return-slice / 终审另册） | 各轮 `rounds/roundN/FIX.md` + `round8/REVIEW.md` |
| **B142** | **开放（形态级缺口，v9 反转）** | 嵌套 finally 副本归属；B181 经新构型探针与执行级复现推翻前规范「稀窝不升格」定性；语料外 B207/B208 同族 | `rounds/round5/ATTACK_L3_MECHANISM.md`、`rounds/round6/ATTACK_L4_RUNTIME.md`、`rounds/round3/BREACH_REGISTRY.md` B181 |
| **B143** | **开放（归约级缺口）** | finally 体内 break 的 finalbody 子区域派发：形态齐全，仅派发顺序错 | `rounds/round5/ATTACK_L3_MECHANISM.md`、`rounds/round3/BREACH_REGISTRY.md` B182 |
| **B163–B219** | **开放/定性挂账（57 项，0 封闭）** | L0–L5 新破口：口径/判据/机制/实现/证据；逐条 = `rounds/round3/BREACH_REGISTRY.md`；v9 新增 4 个 fuzz 复现先映射 B203/B207/B210/B197+B202，未新开 B 号 | `rounds/round10/BREACH_TRIAGE.md` |

**破口状态机与复审六步**：`未定位 → 已定位(仅spec) → 已落地 → 已复审`，复审 = grep 落地标记 + 台账更新 + 占比重算，见 `wiki/concepts/decompile-invariant-completeness.md` §8。**B1a/B1b 验收**：两丢弃入口全部定位并接回；jq 65/65 保持；161 产物逐字节不变；neg75_jqcond2 3/3 success。**v9 口径**：v8 形式层 128/0/0 只是历史形态基线；B163–B219 共 57 项未封闭，B142/B143 已改正为开放缺口；完备仍 `BLOCKED`。

---

## 八、完备性与当前状态（2026-10-23 更新为 v9 审计态）

### 8.1 完备性标准（v9 双读数）

**形态基线占比 = 完备形态数 ÷ 128**（分母 = Python 3.11 语言语法面：97 ast 节点 + 31 扩展形态，永不取自实现枚举、永不取自语料、不随嵌套膨胀）。**该占比只作历史回归口径，不再单独构成完备结论。**

**判定空间口径 = 已判定条目数 ÷ 1556（J v2）**；完备须同时满足 G1–G6（判定空间 / 语义差分 / 变异 / 规则覆盖 / 回归 / 独立 canary）。

| 维度 | v9 读数（2026-10-23） | 结论 |
|------|------|------|
| 形态基线（v8 历史） | 路径 **128/128**；旧形式层 **128/0/0 ⇒ 100%** | **仅历史，降级** |
| G1 判定空间 | 全量 **0/1556**；集成样本 **51/1556（3.28%）** | **FAIL** |
| G2a J 语义差分 | 样本 **45 EQUAL / 6 DIFFERENT / 0 ERROR**；全量未跑 | **FAIL** |
| G2b 402 / G2c 46 真实 pyc | 无读数 | **UNESTABLISHED** |
| G3 变异 | 仅 1/1 冒烟；无全量漏检率 | **UNESTABLISHED** |
| G4 规则覆盖 | 339 条；**0 proved / 339 open**；无 traces | **INCONCLUSIVE** |
| G5 语料回归 | 6617/6617、1568/1568、153/153（历史） | **baseline_only** |
| G6 独立 canary | 24 条 local-bootstrap：**20/24**，泄漏 0 | **FAIL** |
| **总体** | **BLOCKED** | **禁止写完备** |

- except\* 全链已实现（见 3.5），**"唯一缺口 except\*"的旧结论作废**（根因 = 3.12 操作码误标）
- B163–B219 共 **57 项未封闭/定性挂账**；B142 已由 B181 重新定性为**形态级缺口**；B143 为归约级缺口
- 三维度禁止互替：形态基线（128）/ 判定空间覆盖（J 1556）/ 语料回归（402 门禁）
- 口径演变史与每版错误形态：总纲 §9.1（v1–v9 全记录不删）

### 8.2 历史快照（R26/quotation 时代，保留存档）

| 指标 | 数值 |
|------|------|
| 归一化口径 | 150/150 = 100.00%（quotation.pyc） |
| L1 严格口径 | 148/150 = 98.67%（2 项理论极限） |
| 当轮 HEAD | `ece3c91` |

### 8.3 历史门禁基线（v8 终态，2026-10-21 `rr-v3r10`；v9 本轮未重跑，仅作 G5 baseline_only）

| 门禁 | 终读数 |
|------|--------|
| 402 语料八分片 | **6617/6617 files_failure=0**（compile_error/error/failure 全 0；574s） |
| small34 | **1568/1568**（34/34 files success） |
| quotation | **153/153 success（rc=0，100.00%）** |
| pytest 七套件 | **2 failed / 282 passed / 2 xpassed**（基线名单一致） |
| IV.2 | 全绿（IMPORT_OK / COMPILE_OK / BOM 单头 / instrumentation code 0 / G3=0） |
| 25 行矩阵 | **257/257**（34 探针，含负对照 60/60） |
| 组合级 25 号 + 另册 3 号 | **241/242**（唯一红 = B142；当时称稀窝，v9 已改判形态级缺口） |
| 7 组回归 | 86/86、46/46、60/60、71/71、65/65、172/172、98/98 |

历史门禁快照：官方 41 靶 h62 SAME=40/MOVED=1/ERR=0、fully matched 33/33；sstrict 34 pyc/1528 函数 defects 67；battery 82；金丝雀 4/4（round75/fix1 归档口径，留档）。

### 8.4 形态工作面（25 行）与落位（v8 终态）

后续任何改动都应能回答"影响哪一行、该行判据是什么"。25 行工作面与逐行探针/负对照见
`.trae/specs/attain-true-completeness/rounds/round8/REVIEW.md` §2（矩阵 257/257），组合级终表见同文件 §3。

| 组 | 行 | v3 落位轮次 |
|---|---|---|
| R2 条件合并 | If / BoolOp / IfExp | R2（R3/R5/R7/R8 补变体） |
| R3 异常与绑定 | Try / Raise / Assert / Import / Global | R3（R5/R8 补变体） |
| R4 挂起链 | Await / ListComp / await_expr / Yield | R4（R7/R8 补变体） |
| R5 模式与资源 | Match / With | R5（R8 补变体） |
| R6 循环控制 | Break / Continue / While | R6 |
| R7 赋值族 | Delete / AugAssign / Return / Slice | R7（R8 补变体） |
| R8 终审 | augmented_assign / slice / match_statement / global_nonlocal 等镜像行 + 组合级另册 | R8（B153–B162） |

行级要求（后续轮次沿用）：每行至少 1 个**深层（≥3 级宿主）**探针 + 1 个负对照；单点修复必须能外推到同族形态；镜像行（表A/表B/表C 同形不同面）须分别取证。
