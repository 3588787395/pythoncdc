# Python 字节码反编译规则文件（Region Reduction Rules）

> 基于「No More Gotos」(Launez et al., 2013) 区域归约算法，结合 Python 3.11 字节码特性，
> 经 quotation.pyc 反编译迭代（R21-R26）实证总结。本文件是反编译器的强制性工程规范。

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
区域归约的终止性由区域数量有限性保证，不得引入硬编码上限。

### 2.3 禁止跨区域启发式
- 不得在外层区域识别时直接处理内层区域的块
- 不得用「如果某块满足某模式则特殊处理」的启发式规则
- 不得破坏嵌套区域作为抽象节点的语义

---

## 三、区域类型与归约规则

### 3.1 区域类型分类

| 区域类型 | 对应 AST 节点 | 识别方法 |
|---------|--------------|---------|
| IfRegion | `ast.If` | `_identify_conditional_regions` |
| LoopRegion | `ast.For`/`ast.While` | `_identify_loop_regions` |
| BoolOpRegion | `ast.BoolOp` | `_detect_while_condition_boolop_chain` / 'and' 链检测 |
| TernaryRegion | `ast.IfExp` | `_identify_ternary_regions` |
| TryRegion | `ast.Try` | `_identify_try_regions` |
| WithRegion | `ast.With` | `_identify_with_regions` |

### 3.2 IfRegion 归约规则

#### 3.2.1 then/else 边界判定（R24 缺陷A、R25 缺陷2）
- **then-region 边界止于 then 分支末尾的 JUMP_FORWARD 跳转点**
- 循环体内 if/elif/else 链的**公共汇聚后继块保留为循环体兄弟语句**，不得并入 then 分支
- else-region 边界**包含其体内所有语句**（含尾部 for 循环），不得把 else 体内尾随循环外提到 if/elif/else 之后
- 判据：`_check_elif_chain` 中 `inner_merge ≠ merge_` 时阻止 elif 链构建，尾随语句保留 else 体内

#### 3.2.2 if-continue 兄弟语句（R23 修复）
当 IfRegion.merge_block 是当前循环的 back_edge_block（纯 JUMP_BACKWARD）且无 else_blocks 时：
- 两分支均→回边（continue 无条件）
- 生成显式 `Continue` 兄弟节点，标记回边块已生成
- 防止条件合并逻辑把 `[inner_if, Continue]` 误合并为 `if A and B:`

判据（全部满足才触发）：
1. `_current_loop is not None`（循环上下文中）
2. `merge == back_edge_block`（merge 是循环回边）
3. `back_edge 仅含 JUMP_BACKWARD`（纯 continue 回边）
4. `not else_stmts`（无 else，两分支均→回边）

#### 3.2.3 'and' 复合条件处理（R26 缺陷3）
- **统一不拆分**任何 `and` 复合条件，保持 `if A and B:` 形式
- 禁止只对 if 首条拆分（外层 `if A:` + 内层 `if B:`）而 elif 保留冗余 `and`
- 'and' 链检测（Step6）+ `main_inline_boolop_chain` 存入 IfRegion
- `generate()` 入口：当 IfRegion.entry 是 entry_block 且存在以 entry_block 为首块的 inline_boolop_chain 时，让 `_if_generate_normal` 统一处理

### 3.3 LoopRegion 归约规则

#### 3.3.1 while 条件 boolop 链（R24 缺陷B）
`_detect_while_condition_boolop_chain` 反向链回溯：
- **判据**：`if not cond_in_loop: break`
- 合法 while-boolop 前驱的 fall-through 恒为下一条件块（在循环内，`cond_in_loop` 恒真）
- `cond_in_loop=False` 仅出现在外层 if/elif/while 嵌套场景，此时前驱是外层 if/elif 条件块，须由 IfRegion 归约（原则2 + 原则3）

#### 3.3.2 循环后顺序语句
- 循环正常退出后、且后继块仍位于外层 if/elif/else 同一子分支内（未被外层分支的 JUMP_FORWARD to return 截断）时
- 后继条件块作为循环后的子分支内顺序语句保留在原分支内
- **不得外提为兄弟，不得把 while 条件并入外层 elif**

#### 3.3.3 loop_else 边界
- `_find_loop_else` 的 else_blocks/natural_exit 边界判定须精确
- 不得把 else 子分支的 while 回边链误判为 loop_else

### 3.4 嵌套区域作为抽象节点
- 嵌套区域归约后，父区域的 then/else 列表引用**子区域的入口**，不是子区域的所有块
- 外层 IfRegion 引用 `[inner_if, Continue]` 作为 then_stmts（不是展开内层 if 的所有块）

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

### 6.2 验证清单（每轮必须）
1. IMPORT_OK（`import core.cfg.region_analyzer; import core.cfg.region_ast_generator`）
2. COMPILE_OK（反编译产物 `compile()` 通过）
3. repro 全部 match
4. 归一化口径不退化（≥ 上轮）
5. L1 严格口径逐项核查
6. 既有区域测试矩阵无退化（318 pass / 9 fail / 11 skip）
7. 反模式自检（G3 0 新增前缀方法，G4 0 硬编码深度上限）

### 6.3 提交规则
- 每轮必须 commit + push 到远程
- commit message 前缀 `rr-rNN:`
- 包含：缺陷描述、修复方案、验证结果、反模式自检

---

## 七、R21-R26 修复案例索引

| 轮次 | 缺陷 | 区域类型 | 修复方法 | 原则 |
|------|------|---------|---------|------|
| R23 | get_str_data if-continue 兄弟 | IfRegion | `_if_generate_normal` 检测 merge=回边 | 原则2+4 |
| R24A | change_his_to_backward IF 吸收兄弟 | IfRegion | 循环感知 merge 重算 | 原则2+3 |
| R24B | get_date_and_count LOOP 吸收外层条件 | LoopRegion | `_detect_while_condition_boolop_chain` `if not cond_in_loop: break` | 原则2+3 |
| R25 | build_future_fill_time else 块尾部 for 提升 | IfRegion | `_build_elif_chain` `inner_merge ≠ merge_` + `_generate_if` orelse 守卫 | 原则2+3 |
| R26 | one_prod_to_dataframe and 部分提取 | IfRegion/BoolOp | 方案B 不拆分任何 and + generate() 入口复合 'and' 识别 | 原则1+4 |

---

## 八、最终状态

| 指标 | 数值 |
|------|------|
| 归一化口径 | 150/150 = 100.00% |
| L1 严格口径 | 148/150 = 98.67%（2项理论极限）|
| 真实控制流缺陷 | 0 |
| 既有测试矩阵 | 318 pass / 9 fail / 11 skip（0 退化）|
| 反模式新增 | 0 |
| 最终交付文件 | `/workspace/quotation_decompiled.py`（3673行）|
| HEAD commit | `ece3c91` |
