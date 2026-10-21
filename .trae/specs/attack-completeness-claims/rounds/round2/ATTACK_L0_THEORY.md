# ATTACK_L0_THEORY — L0 理论层攻击（不变式 C1/C2/C3 + 归纳论证 + 区域划分）

> 规范：`.trae/specs/attack-completeness-claims/`（Task 2，L0 层）
> 被攻击对象：`wiki/concepts/decompile-invariant-completeness.md:43-54`（C1/C2/C3 + 归纳论证原文）、`core/cfg/region_analyzer.py`、`core/cfg/region_ast_generator.py`
> 取证方式：只读代码 + 33 探针实跑（`rounds/round2/probes/`，`rounds/round2/tools/`）+ 2 个机检工具
> 纪律：本文件不修改 `core/cfg/**`、`tests/**`、`wiki/**`、`rules.md`、前一规范目录；未 push。
> 结论口径：击穿 / 未击穿且不可证伪 / 不可证伪（`spec.md:52-58` 反确认偏误纪律）

---

## §0 结论摘要

| 攻击项 | 结论 | 一句话理由 |
|---|---|---|
| **AT-01** 非局部信息通道穷尽性 | **击穿** | C1 的 `L(A)=A.blocks ∪ A.out_edges ∪ A.exception_table` 中 **`A.out_edges` 与 `A.exception_table` 在 `core/cfg/**` 全仓 0 处定义**（`region_analyzer.py:203-212` 的 `Region` 无此二字段；异常表只有全局 `cfg.exception_table`）；实测 12 类 L(A) 外通道被生成期读取（`region_analyzer.regions` 113 次、`get_block_role` 104 次、`block_to_region` 38 次…），其中 `Region.metadata`（自由字典）、`Region.parent/children`、全局角色表、全局块→区域表均**不在任何 C3 守卫的声明面内**。 |
| **AT-02** 归纳步的组合元数 | **击穿** | 归纳步的前提「二元组合封闭」本身为假：同文件最小对 `m1`（失败）/`m2`（通过）唯一差「try 体末尾一条 `g(x)`」；且三元 `try×if×for-else` 失败而其**全部二元投影**通过（e6/e7 通过、b5/e8 失败）。 |
| **AT-03** 区域划分的唯一性与完备性 | **击穿** | 划分不是原理的函数：同优先级冲突（`FOR_LOOP==WHILE_LOOP==60`、`IF_THEN_ELSE==IF_ELIF_CHAIN==30`、`TRY_EXCEPT==TRY_FINALLY==70`）由**注册顺序**裁决（`region_analyzer.py:1926-1958`），实测 7 个探针文件共 **22 处平局块**由「先到先得」定归属；实现自身为 match×match 单点打了特例补丁（B16, `:1948-1958`），即非唯一性的自证。 |
| **AT-04** 「必须知道外层」判据自洽性 | **击穿** | 找到**同块双重归属**与**语义级归属矛盾**：finally 正常路径副本同时被 try 体与 finally 认领（m1/c4/c5/e9/e10，finally 体被复制进 try 体 ⇒ 副作用重复）；`for-else` 在 `try×if` 宿主下塌陷为顺序语句（b5/e8，含 `break` 时 else 语义被破坏）。 |
| **AT-05** C3 守卫的封闭性 | **击穿** | continue 守卫 `_block_is_continue_target`（`region_ast_generator.py:14832-14843`）**无 loop 限定**、**无 docstring**、无触发集声明；同文件另两个 continue 守卫（B106 `:28590-28614`、B145 `:62067-62091`）均显式限定「本循环自身入口」⇒ 守卫族触发集**不对称且未封闭**。 |
| **AT-06** 不变式与实现的一致性 | **击穿** | 抽检 9 处 docstring/注释与代码不符，其中 2 处是 C1 公式在**代码注释里**引用不存在的字段（`region_ast_generator.py:17641`、`:28597`）。 |
| **AT-07**（增）归纳基「单层正确」 | **不可证伪** | 单层正确只有抽样证据，无「每条归约规则的不变式 + 覆盖引理」；需形态级证明义务 + 机检覆盖检查器。 |
| **AT-08**（增）守卫活性假说 | **未击穿且不可证伪** | 我曾假设 `IfRegion.get_offset_range` 的「更近循环」守卫因 `analyzer.regions` 未填充而**是死代码**；机检实测调用时刻 `len(analyzer.regions)=2..4`（非空）⇒ 假说被否证，但该守卫读的是**phase-1 部分视图**（最终集合 `:1987` 才赋值），其完整性依赖阶段序 ⇒ 不可由抽样判定。 |
| **AT-09**（增）判定空间 covered 语义与正确性正交 | **击穿** | 本轮证伪的条目（`JS-TRY-047/049`、`JS-CONTINUE-001/002`、`JS-MATCHSTMT-015`…）在 `judgment_space.json` 中**全部标 `covered`** ⇒ 覆盖检查器的 covered 轴只验「见证探针存在」，不验「该变体被判对」。 |

---

## §1 攻击项清单

| id | 攻击命题 | 攻击方法 | 击穿判据 | 不可证伪判据 | 结论 | 证据路径 |
|---|---|---|---|---|---|---|
| AT-01 | C1 的 `L(A)` 覆盖全部非局部信息通道 | ①字段存在性扫描（`out_edges`/`exception_table`）；②生成期 `self.region_analyzer.*` 读取点全量计数；③逐通道判「是否 C3 声明」 | 存在未声明通道、或 `L(A)` 字段不存在 | 需先把 `L(A)` 重定义为可机检字段集 | **击穿** | `region_analyzer.py:203-212,1227-1234`；`region_ast_generator.py:544,14832-14843,17641,28597`；`logs/l0_partition.json` |
| AT-02 | 归纳步（二元组合封闭 ⇒ 任意深度正确）成立 | 构造 3 元嵌套 + **二元投影对照** + **同文件最小对** | 任一三元失败而其二元投影全通过；或二元本身失败 | 需覆盖全部组合元的穷举/证明义务 | **击穿** | `probes/l0_a2/a3/a4/b5/e1/e6/e7/e8/e9/e10/f1*.py`；`logs/l0_probes_l0final.json` |
| AT-03 | 块→区域的划分唯一且完备（原则 2） | 机检枚举「被 ≥2 区域认领的块」+ 裁决方式分类 | 存在由**注册顺序**（非原理）裁决的归属；或存在无归属块 | 「原理是否决定划分」需换序不变性 property test | **击穿** | `region_analyzer.py:1926-1958,4397-4412,4574-4584,35709+`；`tools/l0_partition_probe.py`；`logs/l0_partition.json` |
| AT-04 | 「必须知道外层」判据完整且互不矛盾 | 构造 finally 副本 / loop_else / handler-break / continue 目标交叉形态 | 同块被两判据同时认领且产出语义差 | 需形式化「归属唯一」证明义务 | **击穿** | `probes/l0_c4/c5/e9/e10/b5/e8/f1*.py`；`logs/l0_probes_l0final.json` |
| AT-05 | 已落地守卫的触发集 = 该形态的完整语法触发集 | 逐守卫读 docstring 声明的触发面 vs 代码实际判据；与同族守卫对拍 | 守卫触发集为语法触发集的真子集/真超集且无声明 | 需「守卫触发集完备性」机检 | **击穿** | `region_ast_generator.py:14832-14843` vs `:28590-28614` vs `:62067-62091`；`region_analyzer.py:7120-7163` |
| AT-06 | R2–R8 编辑后 docstring/注释仍与代码一致 | 逐函数抽检（≥8） | docstring 说 X、代码做 Y | 需 docstring↔代码一致性检查器 | **击穿** | 见 §2.6 表 |
| AT-07 | 归纳基「一层正确」已被证明 | 检视证据类型 | — | 抽样 ≠ 证明；需形态级证明义务 | **不可证伪** | `wiki/concepts/decompile-invariant-completeness.md:101`（T7 自认「成立（语料口径仅旁证）」） |
| AT-08 | `IfRegion.get_offset_range` 的「更近循环」守卫是死代码 | 插桩测调用时刻 `len(analyzer.regions)` 与分支命中 | 分支恒不命中且表恒空 | 需阶段序无关性证明 | **未击穿且不可证伪**（假说被实测否证） | `tools/l0_guard_liveness_probe.py`；`logs/l0_guard_liveness.json` |
| AT-09 | 判定空间 `covered` 蕴含该条目被判对 | 对照本轮失败探针与 `judgment_space.json` 状态 | 存在被判错的条目仍标 `covered` | 需覆盖检查器升级为「证据 + 判定结果」双轴 | **击穿** | `rounds/round1/judgment_space.json`（`JS-TRY-047` 等标 covered） |

---

## §2 逐项论证

### 2.1 AT-01 非局部信息通道穷尽性 —— 击穿

**实现的区域数据结构**（`core/cfg/region_analyzer.py:203-212`）：

```
Region: region_type / entry / blocks / exit / parent / children /
        metadata: Dict[str, Any] / has_trailing_return_none
```

**C1 公式里的两个字段不存在**：`grep` 全 `core/cfg/**` ⇒ `out_edges` 在 `region_analyzer.py` 出现 **0** 次、在 `region_ast_generator.py` 仅 2 次且**两处都是注释**（`:17641`、`:28597`，即 C1 公式在代码里的复述）；`exception_table` 在两文件中**从不作为区域/分析器实例字段**存在，只有全局 `cfg.exception_table`（`region_analyzer.py:4590,10262,12062,…`），区域靠**偏移区间包含**从全局表里「派生」自己的视图。

⇒ 结论 1：**C1 的 `L(A)` 不是任何实现对象的字段集**，因此「R(A) 只读 L(A)」在当前表述下**不可机检、也不可证伪**；代码里复述该公式的两处注释本身即引用不存在的字段（AT-06 的 #1/#2）。

**实测通道清单**（`tools/l0_partition_probe.py` + 读取点计数；括号内为 `region_ast_generator.py` 中 `self.region_analyzer.<x>` 的出现次数）：

| # | 通道 | 位置 | 是否被 C3 声明 |
|---|---|---|---|
| 1 | 全局区域表 `analyzer.regions`（**全部层级**） | `region_analyzer.py:1227` + 13 处 `append`（`:6217,11669,12015,15752,16710,18714,19059,19371,20099,20834,27332,29319,32478`）；读 113 次 | **否**（B145 的 docstring 反而声称「只读本层区域列表」） |
| 2 | 全局块→区域归属表 `block_to_region` | `region_analyzer.py:1228`；读 38 次（`:452,708,2605,2867-2868,3061,…`） | **否** |
| 3 | 全局角色表 `block_roles` / `get_block_role` | `region_analyzer.py:1234,3970`；读 104 次 | **否**（角色由全局 `_annotate_all_roles` 一次性标注） |
| 4 | 全局块→入口区域 `get_entry_region_for_block` | 读 46 次 | **否** |
| 5 | 全局块→区域 `get_region_for_block` | 读 36 次 | **否** |
| 6 | 外层区域导航 `find_enclosing_region` / `_find_enclosing_region` | 读 6+4 次 | **否** |
| 7 | `Region.parent` / `children` + `find_enclosing_parent`(:238) / `find_descendant_region_for_block`(:250) / `iter_descendants`(:266) | 区域树自身 | **否**（`analyze()` 的 19 覆写点清单 `:1405-1424` 完全未提这三支——它们正是「必须知道外层」的真正入口） |
| 8 | `Region.metadata`（自由字典，30+6 处 `.metadata[`） | `region_analyzer.py:211`；如 `for_target_consumed_offsets` / `for_iter_fall_through`（`region_ast_generator.py:4274-4292`） | **否** |
| 9 | 生成器级「当前循环」栈 `self._current_loop` | `region_ast_generator.py:544`；读点 `:13611,13646,13769,13871,14000,14008,14862-14902,14985-14989,15125,21561,…`；写点 `:6215-6246,17092-17097` | 部分（仅作为「外层知识」使用，未登记为守卫面） |
| 10 | 分析器级「当前循环体」`self._current_loop_blocks` | `region_analyzer.py:1243,5707` | **否** |
| 11 | 块级属性 `BasicBlock.loop_header`（由支配分析写入） | `basic_block.py:79`；写 `dominator_analyzer.py:356,361`；读 `region_ast_generator.py:14838` | **否** |
| 12 | 块级属性 `BlockSemantics.belongs_to_region` | `region_analyzer.py:198` | **否** |
| 13 | 异常表归属 + **布局序假设**（B157 依赖「内层 finally 副本在布局中更早」） | `region_analyzer.py:10400-10414` | 声明为「异常表条目派生」，但**布局序是断言而非推导** |
| 14 | 区域编号/顺序 | 无编号；身份=列表序（`region_ast_generator.py:2033-2034` 按 entry 偏移排序；`region_analyzer.py:35714-35717` 按偏移区间排序） | **否** |

**逐通道判定**：通道 1–8、10–12、14 在 C1/C3 文本中**均未出现**，且其中数条被区域归约直接读取（例如 `IfRegion.get_offset_range`（`:446-479`）读 `analyzer.block_to_region`（`:452`）与 `analyzer.regions`（`:460`），并把**另一区域**的 `try_blocks/except_handlers/else_blocks/finally_blocks` **并入本区域的偏移区间**（`:470-478`）⇒ 该区域的 offset range ⊄ L(A)）。通道 9/13 有局部说明但不构成 C3 守卫登记。

**结构性理由（为何不可由「复跑全绿」结案）**：C1 之所以能被声称成立，前提是「L(A) 是一个封闭、可枚举的字段集」。当前它既不对应实现对象，又被代码注释复述成两个虚构字段；在 L(A) 未被重定义之前，「C1 成立/违反」根本不是一个可判定命题——**这不是缺证据，而是缺定义**。故 AT-01 判**击穿**（对现有表述），同时把「重定义 L(A) + 通道静态登记」转方法层（§7）。

### 2.2 AT-02 归纳步的组合元数 —— 击穿

**被攻击的论证原文**（`wiki/concepts/decompile-invariant-completeness.md:52`）：
> 归纳论证：C1+C2 成立时，一层正确（归纳基）+ 组合封闭（归纳步）⇒ 任意深度/任意组合正确。

**攻击设计**：三元构造 + **全部二元投影**对照 + **同文件最小对**。

| 构造 | 二元投影（须全绿才构成「步前提成立」） | 三元结果 | 判定 |
|---|---|---|---|
| `b5`/`e8` = `try × if × for-else` | `e6`（if×for-else）✅、`e7`（try×for-else）✅ | ❌ 失败 | **二元全通过而三元失败 ⇒ 步的推论被直接否证** |
| `a4` = `while × try × for` | `e3`（while×try）✅、`e4`（try×for）✅、`e5`（while×for）✅ | ❌ 失败（`while True:` 宿主**整体丢失**） | 同上 |
| `a3` = `for × try/finally × try/finally` | `c4`/`e10`（for×try/finally）❌ | ❌ 失败 | **步的前提本身为假**（二元已红） |
| `f1` 同文件最小对 | `m1`（try 体只有 `if x: continue`）❌ / `m2`（多一条 `g(x)`）✅ | — | **二元组合的正确性被一条无关语句翻转 ⇒ 归约对「偶然形状」敏感，非「嵌套无感」** |

**为什么这是理论击穿而不是「新 bug」**：前一轮已把「嵌套 try/finally 内的 continue」登记为 **B142 稀窝并 park 不追**（`.trae/specs/attain-true-completeness/rounds/round8/REVIEW.md:139`），同时对外读数仍写「完备 128 / 破口 0 = 100%」且仍复述「二元组合封闭 ⇒ 任意深度正确」。本轮实测复现该残余（`l0_d4` 逐字复刻 `v_b71_face` ⇒ 仅 `v_nest_fin_continue` 红，与基线读数一致），**并证明同一族在二元深度即已失守**（`m1`/`c4`/`e9`/`e10`）。⇒ 「归纳步」的前提不成立，而主张仍以 100% 呈现 ⇒ **归纳论证被击穿**。

**诚实附注**：`for × match` 家族（`e1/e11/e12/e13/a2`）判据红但**可能是控制流形状差而非语义差**（产物里被合成的 `case 0 if x == 0:` 守卫与尾部 `continue` 语义中性）。该族**不计入** AT-02 的击穿证据，仅列为 §7 的待语义差分裁决项。

### 2.3 AT-03 区域划分的唯一性与完备性 —— 击穿

**划分点的裁决规则**（`region_analyzer.py:1926-1958`，重建 `block_to_region`）：

1. 遍历序 = `all_phase12_regions + sequence_regions`（`:1906`）——**列表序**即注册序；
2. 冲突时：①BoolOp+elif 特例（`:1934-1937`）→②`_should_use_dynamic_priority`（`:1938-1942`，**只覆盖 5 个 (BOOL_OP|TERNARY, IF_*) 对**，`:4577-4583`）→③静态 `REGION_TYPE_PRIORITY` 比较（`:1944-1947`，**平局不换手**）→④match×match 真子集特例（`:1954-1958`，B16）。

**静态优先级表存在同值**（`:4397-4412`）：`FOR_LOOP == WHILE_LOOP == 60`；`IF_THEN_ELSE == IF_ELIF_CHAIN == 30`；`TRY_EXCEPT == TRY_FINALLY == 70`。⇒ 这三组冲突**不走动态分支**，只能落到「先到先得」。

**机检实测**（`tools/l0_partition_probe.py` → `logs/l0_partition.json`）：

- 全部 33 个探针文件均出现「被 ≥2 个区域 `.blocks` 同时认领」的块（每文件 1–25 处）；
- **22 处**冲突的静态优先级相同 ⇒ 归属由注册顺序决定。样例（`logs/l0_partition.json`，`show_ties.py` 输出）：

```
l0_e5_proj_while_for.pyc::e5 @off=4
    claimants   = ['LoopRegion/FOR_LOOP', 'LoopRegion/WHILE_LOOP']
    canonical   = LoopRegion (first-claimant-wins=True)
    dyn_applies = False   scores=[50.0, 50.0] equal=True
```
同型：`l0_b4`（内外 for-else @off=8）、`l0_c2`（内层循环自然出口 @off=8）、`l0_a3`（4 处）、`l0_d4`（4 处）、`l0_c1`/`l0_d3`/`l0_e5`（各 2–3 处）。

**完备性**：机检显示 `unowned_count = 0`（无「块不属于任何区域」的空洞）——**完备性未破**；破的是**唯一性**：划分不是四条原则的函数，而是「原则 + 列表序」的函数。实现自身为 match×match 打的 B16 特例补丁（`:1948-1958`，注释自认「平局（优先级相等）时先到先得会让外层 match 占住内层体的块」）是**非唯一性的自证**。

**层级构建同样无全序**（`_build_region_hierarchy`, `:35709-35818+`）：候选祖先筛选后有 5 级并列 tie-breaker（If 候选剔除 `:35746-35774`、entry-owner `:35785-35793`、嵌套 loop `:35796-35802`、If tiebreaker `:35803-35808`、loop/container `:35810-35818`），无一条覆盖「所有同层冲突」。

**遗留空洞（不在本轮范围）**：`Region.blocks` 之外的归属（`then_blocks/else_blocks/try_blocks/handler_blocks/finally_blocks`）**不进 `block_to_region`**，故「每块唯一归属」在这些字段上**无机器可查的判据**——本轮无法证伪，列 §7。

### 2.4 AT-04 「必须知道外层」判据的自洽 —— 击穿

**矛盾 1：finally 正常路径副本被双重认领（语义级）**
`m1` 源：`try: if x: continue` + `finally: g(0)`；产物：

```python
def m1(items, g):
    for x in items:
        try:
            if x:
                continue
            g(0)          # ← finally 副本被搬进 try 体
            continue      # ← 多出的 continue
        finally:
            g(0)          # ← finally 体第二次出现
```

`g(0)` 每轮被调用 **2 次**（源 1 次）⇒ **可观测语义差**。同型：`c4`/`e10`（`continue` 被整条丢弃 + finally 体复制）、`c5`/`e9`（`if x: continue` + finally 复制）。根因与已登记的 B142 同源（`.trae/specs/attain-true-completeness/rounds/round6/FIX.md:92`：「把『正常路径 finally 副本』误纳为外层 try 的 try_blocks」）。⇒ **同一块同时是「finally 副本」与「try 体成员」**——这正是 AT-04 所问的「自相矛盾」。

**矛盾 2：loop_else 归属 vs 外层结构（语义级）**
`b5`/`e8` 源：`try: if xs: for x in xs: … else: print('else')`；产物把 `else:` 塌陷为顺序语句（`print('else')` 与 for 平级）。`e8` 加 `break` 后 ⇒ **else 子句被错误执行**（真语义 else 仅在无 break 时执行）⇒ 语义差。同一 loop_else 在 `with`（b1✅）、`match`（b2✅）、`try/except`（b3✅）、嵌套 for（b4✅）宿主下均正确 ⇒ 失效条件是 **`try` 与 `if` 同时出现**（三元），非单个外层。

**矛盾 3：handler 内 break（B140）与循环出口**
`c3`（for → try → handler 内 break）✅ 通过；B140 守卫（`region_analyzer.py:36334-36357`）的五条判据完整且**已 loop 限定** ⇒ 本项未击穿，登记为「已封闭守卫」。

### 2.5 AT-05 C3 守卫的封闭性 —— 击穿

| 守卫 | 位置 | 声明的触发面 | 代码实际判据 | 判定 |
|---|---|---|---|---|
| **continue 守卫** `_block_is_continue_target` | `region_ast_generator.py:14832-14843` | **无 docstring、无触发集声明** | 「末指令是 JUMP_BACKWARD 且目标块 `loop_header` 为真」**或**「全局角色 ∈ {CONTINUE, PURE_CONTINUE}」——**无 loop 限定** | **击穿（真超集）** |
| continue 守卫 B106 `_except_tail_backedge_is_loop_continue` | `:28590-28614` | 「(b) 回跳目标块是**本循环自身的入口**：`LoopRegion.is_block_entry(tgt)`」 | 同 | 合格（对照基准） |
| break 守卫 B145 | `:62067-62091` | 「③只读 `LoopRegion.break_blocks` 的成员关系…④只读本层区域列表」 | 遍历 `self.region_analyzer.regions`（**全部层级**） | 判据合格，**docstring 不符**（见 AT-06 #2） |
| break 守卫 B140 | `region_analyzer.py:36334-36357` | 五条合取判据，loop 限定 | 同 | 合格 |
| loop_else 夹取 `_clamp_loop_else_to_enclosing_try` | `region_analyzer.py:7120-7163` | 「只针对 TryExceptRegion」 | 只扫 `TryExceptRegion` | **形态特化**（语法触发集 = {try, with, match, loop}，实现只覆盖 try）——但 with/match/loop 宿主实测通过 ⇒ 归 L3「机制通用性」，**本项不判击穿** |
| finally 归属唯一化 B157 | `region_analyzer.py:10400-10414` | 「按保护跨度升序、跨度同取 handler_start 升序——**内层 finally 副本在布局中更早**」 | 依赖**异常表布局序**这一断言 | 断言非推导 ⇒ 需证明义务（§7） |

⇒ 击穿点：**同一 continue 语义有两个守卫，一个 loop 限定、一个不限定**；不限定的那一个正是 `if` 分支 continue 判定的主路径（直接调用点 **12 处**：`:13715,13720,13726,13733,14205,14206,14717,14986,14987,14988,14989,32048`），且其输入来自**全局角色表**与**支配分析写下的块级 `loop_header` 标志**（通道 3/11），二者都把「哪个循环」这一必要限定压扁掉。

### 2.6 AT-06 不变式与实现的一致性 —— 击穿（9 处）

| # | 位置 | docstring/注释说 | 代码做 |
|---|---|---|---|
| 1 | `region_ast_generator.py:17641-17643` | 「C1 局部消费：只读 L(A) = A.blocks ∪ **A.out_edges** ∪ **A.exception_table**」 | 二者均不存在于任何 Region 类 |
| 2 | `region_ast_generator.py:28595-28598` | 同上（rules.md §1.5 C1 复述） | 同上 |
| 3 | `region_ast_generator.py:14904-14911` | `_block_is_pure_continue`「**此函数仅在 if-branch 生成时使用**」 | 5 个调用点：`:14770/14782`（`_loop_handle_exit_successors`，**循环头出口处理器**）、`:14988/14989`（`_loop_handle_no_exit_successors`，**循环头出口处理器**）、`:14920`（自调用）；**无一**是 if-branch 生成器（那是 `_if_generate_branch_stmts`） |
| 4 | `region_ast_generator.py:62077-62080` | B145「④嵌套处理：不展开任何子区域；**只读本层区域列表**」 | `for _lr in self.region_analyzer.regions:` —— **全部层级**的区域表 |
| 5 | `region_analyzer.py:1446-1448` | 「算法合规度: **完全合规**（4 核心原则全满足，无硬编码深度限制）」 | 四原则**不决定**划分：同优先级冲突由注册顺序裁决（§2.3 实测 22 处） |
| 6 | `region_analyzer.py:1446` | 「全量通过率: 100%（**2068/2068**）」 | 源码内冻结的旧读数；当前门禁基线为 402 语料 **6617 单元**（`baseline/readings.md:29`）——已过时 |
| 7 | `region_analyzer.py:1405-1424` | 「多态分发…当前共 **19 个覆写点**」并逐条列举 | 计数正确，但**遗漏**三个具体跨区域导航方法 `find_enclosing_parent`(:238)/`find_descendant_region_for_block`(:250)/`iter_descendants`(:266)——恰是 C1 通道所在 |
| 8 | `region_analyzer.py:315-316` | `get_offset_range`「IfRegion 覆写（**按需扩展到后继 try 体**）」 | 实际把**另一区域**的 try/handler/else/finally 块并入本区域偏移区间（`:470-478`），且依据是全局 `block_to_region` + **部分** `analyzer.regions`（`:452,460`）⇒ range ⊄ L(A) |
| 9 | `region_analyzer.py:7290` | `_find_loop_else`「else 块**仅在**循环正常退出（非 break）时执行」 | 无 break 时真 else 与顺序后继**字节码不可区分**（docstring `:7277-7279` 自承），实现改用 `_is_post_merge_sibling_head` 启发式 + NOP 判别器（`_loop_else_nop_marker`, `:7165`）**猜测** ⇒ docstring 的绝对表述与实现的启发式不一致（docstring 内部已部分自注，故降级为「表述与实现强度不一致」） |

### 2.7 AT-08 守卫活性假说（我自己的假说被实测否证）—— 未击穿且不可证伪

**假说**：`IfRegion.get_offset_range`（`:446-479`）的「更近循环」守卫（`:456-469`，读 `analyzer.regions`）在 `_build_region_hierarchy`（`:1960`）调用时，因 `self.regions` 直到 `:1987` 才被赋值 ⇒ 守卫恒判 `_has_closer_loop=False` ⇒ **死代码**。

**实测**（`tools/l0_guard_liveness_probe.py` → `logs/l0_guard_liveness.json`）：调用时刻 `len(analyzer.regions)` = 2–4（**非空**），`expansion_fired` 在 `l0_d2` 命中 1 次 ⇒ **假说被否证**（`self.regions` 在 phase-1 的 13 个 `append` 点已部分填充）。

**残留的结构性问题（不可由抽样判定）**：守卫读到的永远是**阶段序相关的部分视图**（最终集合 `:1987` 才赋值），故「更近循环」的判定依赖 phase 顺序 ⇒ 与「嵌套无感」冲突，但当前判据无法把「依赖阶段序」与「依赖语义」区分开 ⇒ 不可证伪，转 §7。

---

## §3 反例集

产物目录：`rounds/round2/probes/`（源 `.py` + `.pyc` + `...OK.py` 同置，仓库既有约定）；判定命令：

```powershell
python -X utf8 pycdc.py rounds/round2/probes/<name>.pyc -o rounds/round2/probes/<name>OK.py
python -X utf8 scripts/pyc_verify.py single rounds/round2/probes/<name>.pyc --source rounds/round2/probes/<name>OK.py
```

> 注：仓库 `.gitignore:2` 忽略 `*.pyc`（既有 `test_repros/**` 亦然，只入库 `.py` 与 `...OK.py`）⇒ 提交的探针集含 `.py` + `...OK.py`；`.pyc` 由 `tools/l0_probe_driver.py` 内的 `py_compile` 在同目录按同名重建（见附命令清单）。

全量读数：**33 探针 / 72 单元 / 57 通过 / 15 单元失败**（`logs/l0_probes_l0final.json`）。

### R1（B164+B165+B167 共用）finally 副本双重归属 —— 二元深度即失守

```python
def m1(items, g):
    for x in items:
        try:
            if x:
                continue
        finally:
            g(0)
```
期望：`try` 体只有 `if x: continue`；finally 只执行一次。
实际：`try` 体多出 `g(0)` 与 `continue`，finally 体再执行一次 `g(0)` ⇒ **`g(0)` 每轮 2 次**。
同文件对照 `m2`（仅多一条 `g(x)`）**通过** ⇒ 最小对。
复现：`l0_f1_minpair_same_file.py`（units 2/3，`m1` 红 `m2` 绿）。
最小变体：`l0_c4_finally_copy_continue.py`（`continue` 被整条丢弃）、`l0_c5_continue_in_nested_try_finally.py`、`l0_e9_minpair_try_only_if_continue.py`、`l0_e10_minpair_try_only_continue.py`。

### R2（B167）三元 `while × try × for` —— while 宿主整体丢失

```python
def a4(xs):
    while True:
        try:
            for x in xs:
                if x:
                    break
                else:
                    continue
        except Exception:
            break
        else:
            continue
```
期望：`while True` 保留；try 的 `else: continue` 保留；handler 内 `break` 保留。
实际：`while True:` **整层消失**，try 的 `else` 消失，handler 内 `break` 变成 `return None`。
复现：`l0_a4_triple_while_try_for.py`（1/2）。二元投影 `e3`/`e4`/`e5` 全绿。

### R3（B167）三元 `for × try/finally × try/finally` —— 内层 try 体整块丢失

```python
def a3(xs):
    for x in xs:
        try:
            try:
                if x:
                    continue
                else:
                    break
            finally:
                print('inner-fin')
        finally:
            print('outer-fin')
```
期望：内层 try 体（`if/else`）与两级 finally 各一次。
实际：`if/else` **整块消失**；`print('inner-fin')` 出现两次；两级 finally 错位（`outer-fin` 成了内层 finally，`inner-fin` 成了外层 finally）。
复现：`l0_a3_triple_nested_finally_continue.py`（1/2）。

### R4（B167）三元 `try × if × for-else` —— for-else 归属塌陷（语义级）

```python
def e8(xs):
    try:
        if xs:
            for x in xs:
                if x:
                    break
                print(x)
            else:
                print('else')
    except Exception:
        pass
```
期望：走 `break` 时 **不** 执行 `print('else')`。
实际：`else:` 塌陷为顺序语句 ⇒ `print('else')` **必执行** ⇒ 语义差。
复现：`l0_e8_for_else_break_in_if_in_try.py`（1/2）；无 break 版 `l0_b5_for_else_in_if_in_try.py`（1/2，形状差）。二元投影 `l0_e6_proj_if_for_else.py`、`l0_e7_proj_try_for_else.py` 全绿。

### R5（既有残余复现，非新破口）B142 `v_nest_fin_continue`

`l0_d4_repl_v_b71_face.py`（逐字复刻 `v_b71_face.py`）→ 仅 `v_nest_fin_continue` 红（3/4），与基线读数（`baseline/readings.md:75`）一致 ⇒ **B142 在当前树上原样复现**，且其形态是 R1/R3 同族。

---

## §4 与判定空间的映射

| 发现 | 判定空间条目（`rounds/round1/judgment_space.json`） | 空间状态 |
|---|---|---|
| R1 finally 副本双重归属 | `JS-TRY-047` (Try/loop-body/d2/try-with-finally)、`JS-TRY-049` (Try/with-body/d2/try-with-finally)、`JS-TRY-043/045` (Try/function-body, if-arm/d2)、`JS-TRY-052` (Try/try-body/d3plus/try-with-finally)、`JS-TRY-006/024` (d3plus) | 全部 **covered**（但本轮实测红） |
| R2 while 宿主丢失 | `JS-WHILE-007` (While/try-body/d3plus/while-true)、`JS-WHILE-033` (While/try-body/d3plus/while-in-func)、`JS-WHILE-038` (While/try-body/d2/while-in-try) | **covered** |
| R3 内层 try 体丢失 | `JS-TRY-010` (Try/try-body/d3plus/try-no-handler)、`JS-TRY-027` (d3plus/try-with-handler)、`JS-TRY-006` (Try/loop-body/d3plus) | **covered** |
| R4 for-else 塌陷 | `JS-TRY-040` (Try/try-body/d2/try-with-else)、`JS-IF-040/041` (If/try-body/d2,d3plus/if-else-arm)、`JS-IF-016/017` | **covered** |
| AT-03 划分非唯一 | `JS-CONTINUE-001/002`（Continue/loop-body/d2,d3plus/continue-in-for）、`JS-CONTINUE-013/014`（while）、`JS-BREAK-001`（Break/loop-body/d3plus） | **covered**（`JS-BREAK-002` 为 uncovered，不计入） |
| `for×match` 控制流红（语义待裁决） | `JS-MATCHSTMT-015/026/034`（match_statement/loop-body/d2）、`JS-MATCHSTMT-020/021`（match-case-body）、`JS-MATCHSTMT-004`（**uncovered**，d1） | covered / uncovered 混合 |

**AT-09 的读数**：上表所有 `covered` 条目在本轮均被判错 ⇒ **`judgment_space.json` 的 `covered` 轴只验「见证探针路径存在」，不验「该变体被判对」**；覆盖检查器（`tools/completeness/coverage_checker.py`）的 covered/uncovered 分母因此**与正确性正交**，不足以支撑「完备」结论（归 L1/L2）。

---

## §5 破坏条款归属

| 发现 | 破坏条款 | 上一版 13 误解编号（`wiki/concepts/decompile-invariant-completeness.md:73-87`） |
|---|---|---|
| AT-01（`L(A)` 字段不存在 + 14 类通道未声明） | **C1 局部消费**（表述层）；C3 守卫封闭（登记面） | #1「循环论证分母」相关；#6「浅层测试当无感证明」（实测通道 ≠ 声明通道）；#11「改工具不改方法」（改注释不改定义） |
| AT-02（最小对 m1/m2；三元 vs 二元投影） | **归纳步**（前提「组合封闭」为假）+ **C2 黑箱组合** | #4「无限分母」（用归纳掩盖组合元数缺口）；#6「浅层测试当无感证明」 |
| AT-03（平局由注册序决定） | **原则 2「每块唯一归属」**（`rules.md` §1.2）+ 归纳论证的划分良定性前提 | #1「循环论证分母」；#5「节点词汇当完备」（RegionType 枚举 ≠ 划分唯一性） |
| AT-04（finally 副本双重归属 / for-else 归属矛盾） | **C1**（归约读了区域外信息：try/finally 副本归属）+ **C3**（守卫未覆盖该触发面） | #2「有过就算」（副本存在即认为已处理）；#13「语料上限当能力上限」（残余 park 仍报 100%） |
| AT-05（continue 守卫无 loop 限定） | **C3 守卫封闭**（触发集为语法触发集的真超集且未声明） | #2「有过就算」；#9「识别率当完备」 |
| AT-06（9 处 docstring/注释与代码不符） | 不变式**表述**与实现的一致性（§1 T4/T6 的落点声明） | #11「改工具不改方法」；#12「错误检测标准」（检测口径对准了错误的字段集） |
| AT-08（守卫读阶段序部分视图） | C3 守卫的**阶段无关性**（未在任何条款中显式声明） | #6「浅层测试当无感证明」 |

---

## §6 新破口登记（自 **B163** 起连续编号）

> 编号冲突说明：round1 的 F1（行级证据—形态错配）预留了 **B163** 但标「待立」。本轮按任务指定自 **B163** 起编号 ⇒ **F1 的破口号顺延为 B170**（登记时改号，见 §6 末）。

| 编号 | 形态 | 最小复现 | 归属层 | 判定空间条目 | 影响面 | 建议机制方向 |
|---|---|---|---|---|---|---|
| **B163** | **不变式表述—实现不对应**：C1 的 `L(A)` 引用两个不存在的字段（`A.out_edges`/`A.exception_table`），使 C1「成立/违反」不可判定 | `grep -c "out_edges" core/cfg/region_analyzer.py` ⇒ 0；`region_ast_generator.py` 仅 2 处且均为注释（`:17641`/`:28597`） | L0 理论 / C1 | 全空间（1556 条） | 全部 1556 条判定空间条目的「完备」依据 | **重定义 L(A)** 为可机检字段集（区域自身 `blocks/entry/exit` + 显式登记的外部输入参数表）；在 `Region` 上加 `external_inputs: FrozenSet[str]` 并由静态检查器断言「未登记的外部读取 = 违规」 |
| **B164** | **非局部通道未登记**：14 类 L(A) 外通道（全局区域表/块→区域表/全局角色表/块级 `loop_header`/`metadata`/区域树导航/分析器级 `_current_loop_blocks`/布局序假设…）在 C1/C3 文本中缺席，生成期读取量 113/104/46/38/36 次 | `tools/l0_partition_probe.py` + `self.region_analyzer.*` 计数 | L0 理论 / C1+C3 | 全空间 | 全部形态的「无感」主张 | **通道静态登记表** + `tools/completeness/l1_channel_audit.py`：扫描 `core/cfg/**` 对 `self.region_analyzer.*`/`analyzer.*`/`cfg.exception_table` 的读取，逐点回填登记表；未登记即红灯 |
| **B165** | **归约对偶然形状敏感（同文件最小对）**：仅差 try 体末尾一条语句，正确性翻转 | `l0_f1_minpair_same_file.py`：`m1` 红 / `m2` 绿（唯一差 `g(x)`） | L0 理论 / 归纳步前提 | `JS-TRY-047/049`、`JS-CONTINUE-001/002` | finally/continue 交互的全部宿主 | **副本谱系图**（沿用 B142 候选机制）：finally 正常路径副本标注 lineage，禁止同时进入 try_blocks 与 finally_blocks；落地后复跑全量门禁 |
| **B166** | **区域划分非唯一（平局由注册顺序决定）**：同静态优先级的区域对同一块的争夺由「先到先得」裁决 | `l0_e5_proj_while_for.pyc::e5 @off=4`（FOR_LOOP vs WHILE_LOOP，scores 50.0/50.0，canonical=先注册者）；全量 22 处 | L0 理论 / 原则 2 | `JS-CONTINUE-001/002/013/014`、`JS-BREAK-001`（均 covered） | 所有同优先级区域对（FOR/WHILE、IF_THEN_ELSE/IF_ELIF_CHAIN、TRY_EXCEPT/TRY_FINALLY） | **全序裁决表**：把 `REGION_TYPE_PRIORITY` 扩成 `(类型优先级, 嵌套深度, 偏移区间包含关系, 结构签名)` 的字典序全序；加「打乱 region 注册顺序 ⇒ 输出逐字节不变」的 property test |
| **B167** | **三元/二元组合击穿**：①`while×try×for` 丢 while 宿主；②`for×try/finally×try/finally` 丢内层 try 体；③`try×if×for-else` 塌陷 for-else | `l0_a4`/`l0_a3`/`l0_e8`（各 1/2），二元投影 `e3`/`e4`/`e5`/`e6`/`e7` 全绿 | L0 理论 / 归纳步 + C2 | `JS-WHILE-007/033/038`、`JS-TRY-010/027/040`、`JS-IF-040/041` | 任意 ≥3 元组合（无界） | **归纳步改为三元闭包命题**并落成机检：生成器必须证明「(A∘B)∘C ≡ A∘(B∘C)」；配套「组合元数」判定空间维度（深度档 ≥3 + 宿主序列） |
| **B168** | **C3 守卫触发集未封闭（continue 守卫无 loop 限定）** | `region_ast_generator.py:14832-14843` vs 同文件 B106 `:28590-28614`；直接调用点 12 处 | L0 理论 / C3 | `JS-CONTINUE-*`（35 条） | 全部 continue 形态 | **continue 判据统一为 loop-qualified**：`(block, loop)` 配对判定，禁止使用全局 `block_roles[CONTINUE]` 与全局 `loop_header` 标志；两处 continue 守卫合并为单一实现并补触发集声明 |
| **B169** | **不变式文本与实现不一致（9 处）**，含 C1 公式在代码注释里引用不存在字段；`analyze()` 自称「完全合规」与「2068/2068」 | `region_ast_generator.py:17641/28597/14904/62077`；`region_analyzer.py:1446/1405/315/7290` | L0 理论 / 表述—实现 | 全空间（文档级） | 全部对外台账与 wiki 断言 | **docstring↔代码一致性检查器**（抽 docstring 中的 C1/C2/C3 断言与字段存在性/调用点比对）；`analyze()` 的合规度自述改为引用机检读数而非硬编码 |
| **B170**（由 F1 顺延） | 行级证据—形态错配（`global_nonlocal` 行证据不含 `nonlocal`） | `rounds/round1/FINDING_F1_GLOBAL_NONLOCAL.md` | L1/L5 | `global_nonlocal` 族 40 条 | 行级完备读数 | 形态级证据映射（行→变体→证据） |

---

## §7 不可证伪项与所需判据

| 项 | 为何当前不可判定 | 需要的 oracle / judge | 落地位置建议 |
|---|---|---|---|
| **AT-01 的「C1 是否成立」** | `L(A)` 不是实现对象的字段集 ⇒「读了区域外信息」没有可机检的边界 | **先重定义 L(A)**（区域字段集 + 显式外部输入登记表），再给「静态读取审计器」：对 `core/cfg/**` 扫描一切跨对象读取，逐点比对登记表 | `tools/completeness/l1_channel_audit.py`（新）+ 修订 `wiki/concepts/decompile-invariant-completeness.md:48-52` 的 C1 原文 |
| **AT-02/AT-07 的归纳基「单层正确」** | 单层正确只有抽样（T7 自认「语料口径仅旁证」，`wiki/…:101`）；组合元数无界 | **形态级证明义务**：每条归约规则给出「不变式 + 覆盖引理」，并由覆盖检查器机检「规则 → 判定空间条目」全覆盖（0 未覆盖） | `COMPLETENESS_METHOD.md` 支柱 3 + `tools/completeness/coverage_checker.py` 升级为规则级 |
| **AT-03 的「划分是否唯一」在原理层** | 实现层面是确定的（deterministic），但「四原则是否**决定**划分」不可由抽样判定 | **换序不变性 property test**：同一 CFG 下随机打乱 region 注册顺序，要求产物逐字节不变；反例即证明划分非由原理决定 | `tools/completeness/l0_partition_probe.py` 扩展为「乱序注入 + 产物比对」 |
| **AT-03 的「每块唯一归属」在 `.blocks` 之外** | `then_blocks/else_blocks/try_blocks/handler_blocks/finally_blocks` **不进** `block_to_region` ⇒ 这些字段上的归属无机器判据 | **归属全域化**：把所有区域成员字段纳入同一 `block_to_region`（或多值映射），并给出「每块恰一属主」机检 | `region_analyzer.py:1926-1958` 重建逻辑（**本轮不改 core**，登记为 Task 10 修复项） |
| **AT-08 的「守卫是否阶段无关」** | 守卫读 `analyzer.regions` 的**部分视图**，而「部分」依赖 phase 序；判据无法区分「依赖阶段序」与「依赖语义」 | **阶段序无关性测试**：对同一 CFG 以不同 phase 序运行分析，要求 `block_to_region` 与产物一致 | 需先有可参数化的 phase 序（当前 `analyze()` 硬编码 Phase 1→12） |
| **`for×match` 家族（e1/e11/e12/e13/a2）** | 判据红的是**控制流形状**；合成守卫 `case 0 if x == 0:` 与尾部 `continue` 语义中性 ⇒ 是否语义差需执行级判定 | **语义级差分**（同输入序列下比对返回值/副作用/异常/顺序） | `tools/completeness/semantic_diff.py`（Task 9 交付）——本轮结论：仅记「控制流红」，**不计入** AT-02 击穿证据 |
| **B142 是否为「形态级缺口」** | 现登记为稀窝 park（`rounds/round8/REVIEW.md:139`）；而本轮证明其同族在**二元深度**即失守 ⇒ park 前提被推翻 | 仍需**修复 + 全量门禁**才能定性；本轮只给出「park 不成立」的证据 | Task 10 封闭 B165/B167 |
| **AT-09 covered 语义** | `judgment_space.json` 的 covered 只验探针存在 | 覆盖检查器升级为「证据存在 ∧ 判定通过」双轴 | `tools/completeness/coverage_checker.py`（Task 1 已建，可扩） |

---

### 附：本轮可复现命令清单（均 ≤300s）

```powershell
# 探针生成 + 全量实跑（33 探针 / 72 单元）
python -X utf8 .trae/specs/attack-completeness-claims/rounds/round2/tools/make_probes.py
python -X utf8 .trae/specs/attack-completeness-claims/rounds/round2/tools/make_probes_repl.py
python -X utf8 .trae/specs/attack-completeness-claims/rounds/round2/tools/make_probes_proj.py
python -X utf8 .trae/specs/attack-completeness-claims/rounds/round2/tools/make_probes_proj2.py
python -X utf8 .trae/specs/attack-completeness-claims/rounds/round2/tools/make_probes_pair.py
python -X utf8 .trae/specs/attack-completeness-claims/rounds/round2/tools/l0_probe_driver.py `
  --dir .trae/specs/attack-completeness-claims/rounds/round2/probes `
  --log .trae/specs/attack-completeness-claims/rounds/round2/logs --stamp l0final
# 划分唯一性机检
python -X utf8 .trae/specs/attack-completeness-claims/rounds/round2/tools/l0_partition_probe.py `
  --dir .trae/specs/attack-completeness-claims/rounds/round2/probes `
  --out .trae/specs/attack-completeness-claims/rounds/round2/logs/l0_partition.json
python -X utf8 .trae/specs/attack-completeness-claims/rounds/round2/tools/show_ties.py l0_e5 l0_b4 l0_c2
# 守卫活性机检
python -X utf8 .trae/specs/attack-completeness-claims/rounds/round2/tools/l0_guard_liveness_probe.py `
  --dir .trae/specs/attack-completeness-claims/rounds/round2/probes `
  --out .trae/specs/attack-completeness-claims/rounds/round2/logs/l0_guard_liveness.json
```
