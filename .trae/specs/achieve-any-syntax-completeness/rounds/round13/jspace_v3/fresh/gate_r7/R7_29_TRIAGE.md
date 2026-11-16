# R7 29 条 DIFFERENT 定性、生成侧可修性与 G1 可修上限

- 日期：2026-11-17　仓库 `F:\Downloads\pythoncdc-main`　解释器 `D:/Python/python.exe`（3.11.7）
- 口径：**只读分析**。未改 `core/`、`scripts/`、`tests/`、`tools/`；未改判定口径，未改
  `scripts/pyc_verify.py`，未豁免任何 R7 差异。
- 输入（既有证据，直接采用）：`D:/temp/opencode/cl_layout/gap/g3gap/r7_transfer.json`（29 条清单）、
  `.../gap/g3fix/semantic_v3m_b275_g3fix_merged.json`（1556 条 C1–C5 记录）、
  `.../round13/jspace_v3/fresh/gate_gap/{G3_DECISIONS.md,COVERAGE_G3_V21.md}`。
- 产物：本文件 + `fresh/gate_r7/r7_29.json`（逐条机器可读定性）+
  `r7_deep_diff.{json,log}`（嵌套 code object 逐层差异）、`repro_min.{json,log}`（9 条链路 +
  机制探针 + 反事实）、`dead_const_scan.{json,log}`、`nop_accounting.json`；
  同步副本在 `D:/temp/opencode/cl_layout/r7/`。

## 0. 结论摘要

| 项 | 结论 |
|---|---|
| 29 条的根因数 | **只有 3 个**：29 个 J 条目只对应 **3 个 `(pyc, product)` 站点**（同站点 product 字节完全相同） |
| T1/T2/T3 分布 | **T2 = 12**、**T1 = 11**、**T3 = 6**（不是"12 + 17"） |
| 背景里"17 条真实差异"的修正 | 17 条中 **11 条只是 `co_code` 操作数（`LOAD_CONST` 索引）差异**，opcode 序列 20/20 完全相同；**只有 6 条** opcode 序列不同（22 vs 21） |
| 生成侧可修 | **可修，但不是"重排常量池"**：反编译器根本没有常量池发射阶段（它发源文本，`co_consts` 由 CPython 编译器决定）。只能改**发射的源文本形态**，让 CPython 编译出同一池 |
| 影响面 | 反事实验证：3 个站点各改 1 处源文本 ⇒ judge 全部 `DIFFERENT → EQUAL`；且 1151 条 EQUAL 里 **1013 条本身就有死常量**仍然 EQUAL（见 §5.4），说明修法在这些点上是**恒等变换**，不改已 EQUAL 的文本 |
| G1 可修上限 | `covered_5tuple 1151 →` **区间 [1163, 1180]**：1163 = 只修 T2（+12）；1174 = 再修 T1（+23）；1180 = 连 T3 一起修（= 转出前的 `checked_5tuple_before`） |

## 1. 方法与判定口径（先对齐"在比什么"）

`tools/completeness/semantic_runner.py:131-151` 把每条 J 记录交给
`semantic_diff.compare_case`：`original = {"pyc": p_j 的 pyc}`、`product = {"source": 反编译产物}`。
`semantic_diff._load_target`（`:578-598`）对 pyc 用 `SourcelessFileLoader`、对产物用
`SourceFileLoader`，代码对象取 `loader.get_code(module_name)`（`:776`）。
因此 **R7 差异 = 原件 pyc 里的 code object 树 vs "把反编译产物源文本重新编译"得到的 code object 树**。

被比字段（`semantic_diff.py:62-67` 的 `CO_FIELDS`，去掉 `IGNORABLE_CODE_FIELDS` 三项）：
`co_code`、`co_consts`、`co_exceptiontable`（这三项是 `PROTECTED_METADATA_FIELDS`，
`tolerance.ignore_metadata_fields` 对它们无效，见 `_unregistered_r7_ignores`）
以及 `co_argcount/…/co_flags/co_names/co_varnames/co_freevars/co_cellvars/co_qualname`；
`co_filename`、`co_firstlineno`、`co_linetable` 被忽略。嵌套 code object **递归展开**
（`_const_meta` / `_code_metadata`，`:202-259`），所以差异路径是
`$.metadata.code.co_consts.v[i].co_consts.v[j]…`。

> 复现时的一个坑（本报告所有"重编译"都按此处理）：`compile()` 默认 `dont_inherit=False` 会
> 继承**调用方模块**的 `from __future__ import annotations`，给每个 code object 多加
> `CO_FUTURE_ANNOTATIONS = 0x1000000`：
> `load_src_code` 修正前 → `o flags 0x0 p flags 0x1000000`；改
> `compile(text, path, 'exec', dont_inherit=True)` 后 → 双侧 `0x0`。判分侧
> `source_to_code` 用的正是 `dont_inherit=True`。

## 2. 29 条 → 3 个站点（先把"条目"和"缺陷"分开）

```
D:/Python/python.exe -X utf8 fresh/gate_r7/r7_deep_diff.py
groups=3 entries=29
  e04_g2_ifexp_deep.pyc#1            entries=12  tags=['T2_const_object']
  r7_05_ternary_comprehension.pyc#2  entries=11  tags=['code_operands_only', 'const_len_differs', 'const_value_differs']
  c13_class_misc.pyc#3               entries=6   tags=['code_opseq_differs', 'const_value_differs', 'name_table_differs']
```

分组键是 `(pyc, sha256(product 文本))`，所以"同一组"= 同一份 pyc + 字节相同的反编译产物。
`r7_29.json` 的 `distinct_pyc = 3`、`distinct_product_sha = 3`。
三个站点的 29 条 J 条目之间**只差 J 标签**（`form/host/variant/depth`）与
`input_model.calls`，`p_j`/`pyc`/`product` 完全一样。例如 `JS-IFEXP-001..015` 的
`calls` 逐字相同，只是 `host` 标成 function-body / module-level / assign-rhs / call-arg / …。

> 这条对 G1 记账很关键：**29 是 3 个缺陷被 29 个 J 标签重复计数**。修 1 个常量渲染规则就能让
> 12 个条目同时翻绿；反过来，任何"每条目单独定位"的排查都会把同一个缺陷重复算 12 次。

## 3. 29 条逐条定性

`站点` 列指向 §4 的详细证据；`差异字段` 用 judge 的字段名。

| # | J id | form | host | depth | 类 | 差异字段 |
|---|---|---|---|---|---|---|
| 1 | JS-IFEXP-001 | IfExp | function-body | d1 单层 | T2 | co_consts.v[0] |
| 2 | JS-IFEXP-002 | IfExp | module-level | d1 单层 | T2 | co_consts.v[0] |
| 3 | JS-IFEXP-003 | IfExp | assign-rhs | d1 单层 | T2 | co_consts.v[0] |
| 4 | JS-IFEXP-007 | IfExp | call-arg | d1 单层 | T2 | co_consts.v[0] |
| 5 | JS-IFEXP-008 | IfExp | subscript-index | d1 单层 | T2 | co_consts.v[0] |
| 6 | JS-IFEXP-009 | IfExp | condition-expr | d1 单层 | T2 | co_consts.v[0] |
| 7 | JS-IFEXP-010 | IfExp | comprehension-scope | d1 单层 | T2 | co_consts.v[0] |
| 8 | JS-IFEXP-011 | IfExp | lambda-body | d1 单层 | T2 | co_consts.v[0] |
| 9 | JS-IFEXP-012 | IfExp | boolop-operand | d1 单层 | T2 | co_consts.v[0] |
| 10 | JS-IFEXP-013 | IfExp | binop-operand | d1 单层 | T2 | co_consts.v[0] |
| 11 | JS-IFEXP-014 | IfExp | if-arm | d1 单层 | T2 | co_consts.v[0] |
| 12 | JS-IFEXP-015 | IfExp | match-guard | d1 单层 | T2 | co_consts.v[0] |
| 13 | JS-IFEXP-024 | IfExp | comprehension-scope | d2 双层 | T1 | co_code,co_consts.len,co_consts.v,co_consts.v[1] |
| 14 | JS-IFEXP-025 | IfExp | comprehension-scope | d3plus | T1 | 同上 |
| 15 | JS-LISTCOMP-012 | ListComp | comprehension-scope | d2 双层 | T1 | 同上 |
| 16 | JS-LISTCOMP-028 | ListComp | return-value-expr | d1 单层 | T1 | 同上 |
| 17 | JS-LISTCOMP-029 | ListComp | comprehension-scope | d2 双层 | T1 | 同上 |
| 18 | JS-BREAK-001 | Break | loop-body | d3plus | T3 | co_code,co_consts.v[1],co_consts.v[2],co_consts.v[3],co_names,co_names[0] |
| 19 | JS-BREAK-011 | Break | loop-body | d3plus | T3 | 同上 |
| 20 | JS-BREAK-023 | Break | loop-body | d3plus | T3 | 同上 |
| 21 | JS-BREAK-027 | Break | loop-body | d3plus | T3 | 同上 |
| 22 | JS-BREAK-030 | Break | loop-body | d3plus | T3 | 同上 |
| 23 | JS-WHILE-040 | While | if-arm | d3plus | T3 | 同上 |
| 24 | JS-SETCOMP-017 | SetComp | return-value-expr | d1 单层 | T1 | co_code,co_consts.len,co_consts.v,co_consts.v[1] |
| 25 | JS-DICTCOMP-019 | DictComp | return-value-expr | d1 单层 | T1 | 同上 |
| 26 | JS-DICTCOMP-020 | DictComp | return-value-expr | d1 单层 | T1 | 同上 |
| 27 | JS-GENEXP-005 | GeneratorExp | call-arg | d1 单层 | T1 | 同上 |
| 28 | JS-GENEXP-017 | GeneratorExp | call-arg | d1 单层 | T1 | 同上 |
| 29 | JS-GENEXP-018 | GeneratorExp | call-arg | d1 单层 | T1 | 同上 |

分类定义（严格按任务口径，另加一条必要的细分）：

- **T1 常量表索引**：`LOAD_CONST` 操作数指向的索引变了。细分为
  **T1a 纯排列**（同一组常量、只换次序）→ **0 条**；
  **T1b 池内容差一个死常量**（集合不同，后续索引整体平移）→ **11 条**。
- **T2 常量对象/类型**：同一位置 `==` 相等但对象/类型不同（`0` vs `False`）→ **12 条**。
- **T3 真实代码差异**：`co_code` 的 **opcode 序列**不同（不是只有操作数）→ **6 条**。

> 背景把 17 条写成"嵌套 `co_code`/`co_consts` 真实差异"，实测应拆成 11（T1b）+ 6（T3）。
> 其中 11 条的 `co_code` 字节确实不同，但**指令序列逐条相同**，只差 1 个 `LOAD_CONST` 操作数
> （见 §4.2），因此不能算"真实代码差异"。

## 4. 三类根因逐条

### 4.1 T2（12 条）：折叠臂的常量被合成为 `False`，原件是 `int 0`

- 站点：`e04_g2_ifexp_deep.pyc` → `<module>.co_consts[6]` = `f_ternary_comp_cond`
  → `.co_consts[2]` = `f_ternary_comp_cond.<locals>.<listcomp>`（第 3 层，depth 2）→ `co_consts[0]`。
- 原件对应源码（`test_repros/round3/e04_g2_ifexp_deep.py`）：
  `return [x for x in xs if (x if b else 0)]`
- 产物（`.../semantic_products/shard0/JS-IFEXP-001.py`）：
  `return [x for x in xs if (x if b else False)]`
- 差异字段：`co_consts` 的**第 0 个元素本身**；`co_code` **逐字节相同**（`0` 与 `False` 同为假值，
  折叠后的跳转长度一致）。
- 原件 listcomp 的 `co_consts = (0,)`，且**没有任何 `LOAD_CONST`**——`0` 是死常量：

```
  8 FOR_ITER 10 (to 30)
 10 STORE_FAST 1 (x)
 12 LOAD_DEREF 2 (b)
 14 POP_JUMP_FORWARD_IF_FALSE 3 (to 22)   # b 假 -> 直接跳过（假值）
 16 LOAD_FAST 1 (x)
 18 POP_JUMP_BACKWARD_IF_FALSE 6 (to 8)
 20 JUMP_FORWARD 1 (to 24)
 22 JUMP_BACKWARD 8 (to 8)
 24 LOAD_FAST 1 (x)
 26 LIST_APPEND 2
 28 JUMP_BACKWARD 11 (to 8)
 30 RETURN_VALUE
```

`(0,)` 12 条 / `(False,)` 12 条；judge 路径 `...co_consts.v[6].co_consts.v[2].co_consts.v[0]`。
最小差异：**同一个 code object 的第 0 个常量从 `int 0` 变成 `bool False`**，其余全同。

### 4.2 T1（11 条）：池里多出的死 `True` 把 `0` 的索引从 2 挤到 1

- 站点：`r7_05_ternary_comprehension.pyc` → `<module>.co_consts[2]` = `t_listcomp_ternary_filter`
  → `.co_consts[1]` = `<listcomp>`（第 2 层，depth 1）。
- 原件：`return [x if flag else 0 for x in xs if (x % 2 if flag else True)]`
- 产物：`return [x if flag else 0 for x in xs if not flag or x % 2]`
- 池：原件 `(2, True, 0)`（`True` 在 index 1，**无 `LOAD_CONST` 引用 → 死常量**）；
  产物 `(2, 0)`。`0` 的索引 **2 → 1**。
- `co_code` 42 vs 42 字节、20 vs 20 条指令、**opcode 序列完全相同**，仅 1 处操作数不同：

```
@34   orig LOAD_CONST 2 (0)   |  prod LOAD_CONST 1 (0)
```

两种源形态编译出的字节码**逐条相同**（已实测：`x % 2 if flag else True` 与 `not flag or x % 2`
都得到上面这段），差别只在"`True` 有没有被 intern 进池"。因此这不是"排列"，而是**池内容差一项**：
后续索引平移，`LOAD_CONST` 操作数字节随之改变，`co_code` 字节也就不同。

### 4.3 T3（6 条）：`if 0:` 的死体与 `pass` 的 NOP 丢了，另外凭空长了 `while 1:`

- 站点：`c13_class_misc.pyc` → `<module>.co_consts[1]` = `CMisc`（class body）
  → `.co_consts[3]` = `CMisc.boom`（第 3 层，depth 2）。
- 原件源码：

```python
def boom(self):
    if 0:
        raise ValueError('x')
    for i in range(2):
        if i > 0:
            while True:
                if i:
                    break
                else:
                    continue
    pass
    return None
```

- 产物文本（`.../semantic_products/shard1/JS-BREAK-001.py`）：

```python
def boom(self):
    while 1:
        for i in range(2):
            if i > 0:
                while 1:
                    if i:
                        break
        continue
        break
```

- 池：原件 `(None, 0, 'x', 2)` / 产物 `(None, 1, 2, 0)`；名字表原件 `('ValueError','range')`
  / 产物 `('range',)`；`co_exceptiontable` **相同**（都是空）。
- 指令级差异（22 vs 21 条，`opseq_equal=False`）：

```
@4    orig LOAD_GLOBAL 3 'range'   | prod LOAD_GLOBAL 1 'range'      (names 表少一项导致索引变)
@16   orig LOAD_CONST 3 (2)        | prod LOAD_CONST 2 (2)
@40   orig LOAD_CONST 1 (0)        | prod LOAD_CONST 3 (0)
@58   orig JUMP_BACKWARD 5 (to 50) | prod JUMP_BACKWARD 4 (to 52)   (回边是否包含行号 NOP)
@62   orig NOP                     | prod LOAD_CONST 0 (None)       (原件 `pass` 的 NOP 被吞)
@64   orig LOAD_CONST 0 (None)     | prod RETURN_VALUE
```

`if 0:` 在 3.11 只编译成**一条 NOP**（`r7_nop_accounting.py`：`if0_then_for` → `NOPs=[2]`，
`len=44`，且池里留下 `0`、`'x'`、名字 `ValueError`）；反编译把整条语句丢掉，连带丢掉死常量
`'x'`/死名字 `ValueError`。产物改用 `while 1:` 包裹 for，`while 1:` 自己的行号 NOP 恰好落在
偏移 2（顶替了原 `if 0:` 的 NOP），而尾随 `pass` 的 NOP 消失 → 68 vs 66 字节。

> 结论：**6 条 T3 是"我方生成形态错误"**（不是环境/口径问题）：产物文本丢了一条不可达语句和一条
> `pass`，并凭空插入 `while 1:`；三者都可从原件指令流看到痕迹（NOP 存在、位置固定）。

## 5. 任务二：生成侧能不能对齐常量池？

### 5.1 3 条 T2 + 3 条 T1 的最小复现（链路逐条实测）

```
D:/Python/python.exe -X utf8 fresh/gate_r7/r7_repro_min.py
G1_ifexp_deep      before=DIFFERENT  after=EQUAL      tree False -> True
G2_ternary_comp    before=DIFFERENT  after=EQUAL      tree False -> True
G3_class_misc      before=DIFFERENT  after=EQUAL      tree False -> True
```

链路（`repro_min.log` 原文摘要，`sha(pyc)`/`sha(product)` 为实测）：

| 抽样 | J id | p_j | pyc sha | product sha | 差异 |
|---|---|---|---|---|---|
| T2 | JS-IFEXP-001 | `test_repros/round3/e04_g2_ifexp_deep.py` | `babc1446dcb81f82…` | `c7d4a5f451d2b069…` | `co_consts[(…).co_consts[2].co_consts] [('int','0')] != [('bool','False')]` |
| T2 | JS-IFEXP-002 | 同上 | 同上 | 同上 | 同上（同站点） |
| T2 | JS-IFEXP-003 | 同上 | 同上 | 同上 | 同上（同站点） |
| T1 | JS-IFEXP-024 | `test_repros/round7/r7_05_ternary_comprehension.py` | `ded1b82a2ce6009b…` | `d59ffb494db355d9…` | `co_code 42!=42` + `co_consts [('int','2'),('bool','True'),('int','0')] != [('int','2'),('int','0')]` |
| T1 | JS-IFEXP-025 | 同上 | 同上 | 同上 | 同上（同站点） |
| T1 | JS-LISTCOMP-012 | 同上 | 同上 | 同上 | 同上（同站点） |
| T3 | JS-BREAK-001 | `test_repros/round2/c13_class_misc.py` | `78eea14ccccbf8dc…` | `73250ce5dbce8861…` | `co_code 68!=66` + 池 + `co_names ('ValueError','range') != ('range',)` |
| T3 | JS-BREAK-011 / 023 | 同上 | 同上 | 同上 | 同上（同站点） |

> 说明：T1/T2 各自的 3 条抽样落在**同一个站点**（同 pyc、同 product 字节），这是数据本身的形状，
> 不是抽样偷懒：11 条里没有任何第二条 pyc。为避免"只证明了一次"，§5.2 另给了隔离探针。

### 5.2 常量表顺序/对象由什么决定（实证）

1. **顺序 = 编译器遍历中首次出现的先后**（同一 `(类型, 值)` 只登记一次）：
   `return 1 if c else 2` → `(None,1,2)`；把两臂对调成 `return 2 if c else 1` → `(None,2,1)`；
   链式 `(1 if c else 2), (2 if c else 3)` → `(None,1,2,3)`（`repro_min.json.pool_rules`）。
2. **`0` / `False` / `0.0` 是三个不同池项**（`0 == False == 0.0` 为真、`hash` 也相等，但池不合并）：
   ```
   def f():
       a = 0; b = False; c = 0.0
       return a, b, c
   consts: [('NoneType','None'), ('int','0'), ('bool','False'), ('float','0.0')]
   ```
   这正是 T2 能成立的前提：`False` 与 `0` 在池里**不等价**，judge 的 `canon` 也带 `t` 字段。
3. **折叠/不可达都会留下"死常量"**：`[x for x in xs if (x if b else 0)]` 的 listcomp
   `consts=[(int,0)] loaded_indices=[]`（一条 `LOAD_CONST` 都没有）；
   模块级 `if 0:\n    raise ValueError('x')` → 池 `(0, 'x', None)`、名字 `('ValueError',)`；
   本 fixture 的函数级形态（`if 0:` 之后还有语句）→ 池 `(None, 0, 'x', 2)`。
4. **同一段字节码可以有多个合法源形态**，池随形态变：
   - `[x for x in xs if (x if b else 0)]` 与 `... else False` → `co_code` 完全相同，池 `(0,)` vs `(False,)`；
   - `(x % 2 if flag else True)` 与 `not flag or x % 2` → `co_code` 完全相同，池 `(2,True,0)` vs `(2,0)`；
   - 隔离探针（`probes/B1_true_orelse.py`）：**单独**的 filter 场景下 `True` 并不会进池
     （`([('int','2')], 34, ['LOAD_CONST 0'])`），只有当元素表达式本身也是三元
     （`[x if flag else 0 for x in xs if (x % 2 if flag else True)]`）时池才变成 `(2, True, 0)`。
     即"死常量"是**具体形态**的编译器产物，不能靠普适规则推出来。

### 5.3 明确回答：能不能在不改判定口径、不改 `scripts/pyc_verify.py` 的前提下对齐？

**能，但不是通过"重排常量池"，而是通过"改发射的源文本形态"。** 分层回答：

- **架构事实（必须先纠正一个前提）**：本仓库的反编译器**没有"常量池发射顺序"这一层**。
  `pycdc.py` 产出的是 Python 源文本（`semantic_runner.decompile` →
  `[python, pycdc.py, pyc, -o, product]`），产物 `co_consts` 是**判分侧 `compile()` 重新生成的**。
  因此 `core/cfg/code_generator.py` 里"调整常量池次序"是不可能实现的——那里没有池。
  能改的只有"发什么形状的源"。
- **T2（12 条）：可修，且风险最低。** 折叠臂的**值**不在指令流里，但**池里躺着那个 `0`**
  （`loaded_indices=[]`）。把"按极性合成 `True/False`"改成"优先采用池里未被引用的那个常量"，
  该站点会发出 `else 0`，重编译后池 = `(0,)`，与原件逐字节一致（反事实已证 EQUAL）。
  相关合成点（代码阅读定位，未打补丁）：`core/cfg/comprehension_generator.py` 的推导式过滤器
  表达式解析器 `_parse_impl`（`:5761` `'value': True if _cond == 0 else False`）、
  `_arm_const`（`:5548` `'value': False if _j.argval == _next_off else True`）、`_try_ifexp`
  （`:5689`，注释明确写着"两臂均被编译期折叠为空的三元…按折叠常量约定发射真值常量"）。
  这条注释就是 T1/T2 的成因自述：**约定发射真值常量 ⇒ 丢掉原件常量对象**。
- **T1（11 条）：可修，但属于"规范化选择"，不是必然正确。** 该站点池里也有死 `True`，
  而 `comprehension_generator.py:6323-6364` 已经有一段专门处理"折叠真值 orelse"的分支，
  它会发出 `IfExp(test=cond, body=真臂, orelse=Constant(True))`，注释同样承认
  "filter 位真值常量折叠不可分辨（True/1/"x" 同码），取规范真值 True"。
  本次产物走的是 `not flag or x % 2`（BoolOp）通道，没有走该分支。让该分支优先即可对齐
  （反事实：改回 `(x % 2 if flag else True)` ⇒ judge EQUAL）。但**字节码不区分**这些形态，
  所以这是"选一个能复现池的规范形"，不是"从指令推断出原件"。
- **T3（6 条）：可修，但要新增"不可达代码重建"，本质是猜。** NOP 的存在与位置可从指令流看到
  （`if 0:` → 恰好 1 条 NOP；`pass` → 1 条 NOP），所以 **co_code 的 2 字节差可机械修复**；
  但"这条 NOP 原本是 `if 0: raise ValueError('x')`"只能从**池残留**（死 `'x'` + 死名字
  `ValueError`）反推，且重建出的语句还得让池顺序也一致。现有 `ast_generator_v2.py:9458`
  `_generate_nop_if_ast` 的 docstring 写明它就是为了"保持字节码一致性"保留 NOP 型 if
  （对应 `if True:`），但没有覆盖 `if 0:`（常量假 + 体不可达）这个形态。
- **不可修的"根本原因"（如果要求通用）**：`co_consts` 里有一部分项**任何指令都不引用**，
  它们的"值"在字节码里**没有唯一解**；同一段 `co_code` 对应多个池不同的源形态（§5.2 第 4 条已实测）。
  所以"对任意输入都对齐池"在信息论上不成立；能做的是"用池残留当 oracle，在等价形态里挑一个"。

### 5.4 影响面估计：会不会动到 1151 条已 EQUAL 的产物文本？

- **反事实（最强证据）**：3 个站点各改 1 处源文本后，用真 judge 重判
  （`semantic_diff.compare_case`，含 R0–R6 行为维度）：**三条全部 `DIFFERENT → EQUAL`**，
  嵌套树 `False → True`（`repro_min.log` 的 `[counterfactual …]` 段）。
- **为什么可以认为对已 EQUAL 的产物是恒等变换**：新规则发的是"**池里那个对象**"。judge 比较的
  正是同一位置的池对象；若某条产物的该位置已经 EQUAL，说明它当前发出的常量**已经等于**池对象，
  新规则只会发出同一个对象 ⇒ 文本不变。也就是说：**会被改文本的只有当前已经 DIFFERENT 的站点**。
- **规模普查**（`r7_dead_const_scan.py`，全 1556 条逐 code object 扫描"无 `LOAD_CONST` 引用的常量"）：

```
{"with_dead_EQUAL": 1013, "no_dead_EQUAL": 138, "with_dead_ERROR": 376,
 "with_dead_DIFFERENT": 29, "equal_total": 1151, "equal_with_dead": 1013,
 "transferred": 29, "transferred_with_dead": 29}
```

  1151 条 EQUAL 里 **1013 条（88%）本身就带死常量**（类型分布 `NoneType 2747 / str 163 / int 50 /
  bool 8`）却仍然 EQUAL ⇒ 现行反编译器**大体上能复现死常量**，失败只集中在"按极性合成真值常量"
  的少数站点（29 条全部带死常量，且都落在合成点上）。这既说明修法不会大面积动文本，也说明
  **不能靠"随便塞一个真值"蒙对**：剩下的 138 条无死常量条目不受影响。

## 6. 任务三：T3 的指令级抽样与"是不是我们的 bug"

抽样 JS-BREAK-001 / JS-BREAK-011 / JS-BREAK-023（同站点，指令级差异见 §4.3 的表）。判定：

| 差异 | 是否我方生成错误 | 说明 |
|---|---|---|
| 少 1 条 `NOP`（@62，来自 `pass`） | **是** | 原件 `pass` 编译成 NOP；产物把 `pass` 吞掉，`co_code` 68→66 |
| 多出来的 `while 1:` 包裹 | **是（形态错误，但字节码几乎不可见）** | `while 1:` 自身只发 1 条行号 NOP，恰好顶替被丢的 `if 0:` NOP；`continue/break` 落在天然落点，因此未额外增加指令 |
| 回边目标 50 vs 52 | **是** | 产物把内层循环头指向 `LOAD_FAST`（52），原件指向行号 `NOP`（50） |
| 池少 `'x'`、`0` 次序变化；名字表少 `ValueError` | **是（信息丢失）** | `if 0:` 的不可达体被整条删除，池/名字表残留随之丢失 |

对应层（代码阅读定位，未改）：

- `core/cfg/ast_generator_v2.py:9458 _generate_nop_if_ast`：docstring 明说
  "当 Python 编译器遇到 `if True:` 时会生成 NOP…为了保持字节码一致性，我们需要保留这些
  `if True:` 语句"。它覆盖了 `if True:`，没覆盖 `if 0:`（常量假 + 体不可达）——T3 的第一因。
- 循环结构化层（`core/cfg/ast_generator_v2.py:15511 _generate_loop_ast` /
  `core/cfg/region_ast_generator.py:20026` 的 `test: _combined_cond or Constant(True)`）：
  在失去了 `else: continue` 的天然落点后补 `while 1:` 包裹，并把尾随 `pass` 一起吞掉——T3 的第二因。
  （此处只到"候选层"，未打补丁验证；见 §8 限制。）

## 7. G1 的"可修上限"

| 层级 | 修复内容 | 翻绿条目 | `covered_5tuple` | 依据 |
|---|---|---|---|---|
| 现状 | — | — | **1151** | `COVERAGE_G3_V21.md`、`r7_transfer.json` |
| A. 只修 T2 | 折叠臂常量改用池残留（`0` 而不是 `False`） | **+12** | **1163** | 反事实 G1 站点 judge `DIFFERENT→EQUAL`；12 条同站点 |
| B. A + 修 T1 | 折叠真值 orelse 走已存在的 IfExp 分支（发 `x % 2 if flag else True`，不发 `not flag or …`） | **+11** | **1174** | 反事实 G2 站点 judge `DIFFERENT→EQUAL`；11 条同站点 |
| C. B + 修 T3 | 重建 `if 0:` 的 NOP/不可达体 + 保留 `pass`、不插 `while 1:` | **+6** | **1180** | 反事实 G3 站点 judge `DIFFERENT→EQUAL`；6 条同站点；1180 = `checked_5tuple_before`（转出前读数），也是 29 条全清的天花板 |

**区间 [1163, 1180]**：

- 下界 1163 的依据：T2 的 12 条是"同一站点、同一合成规则、反事实已证 EQUAL"，且 1013 条带死常量
  的 EQUAL 条目证明"用池对象替代合成常量"在已 EQUAL 的站点上是恒等变换，回归面最小。
- 中值 1174 的依据：T1 的 11 条也有反事实 EQUAL，且目标分支已在
  `comprehension_generator.py:6323-6364` 存在，只需让它在 BoolOp 通道之前命中；但它属于
  "等价形态的规范化选择"，改完要回归"原本发 BoolOp 才对的形态"，风险高于 A。
- 上界 1180 的依据：T3 的 6 条反事实也 EQUAL，但需要新增"不可达代码/死池残留重建"能力，
  且重建结果依赖池残留这一非唯一线索（§5.3 末条），属于新特性而非修 bug，故列为上界而非承诺。
- **不可能超过 1180**：分母侧 `excluded=376`、`uncovered=405` 没有产物/判词，常量对齐动不到它们；
  而 29 条是本次从 `covered_5tuple` 转出的全部（`r7_transfer.json.total=29`）。

**性价比排序**：A 用一条渲染规则换 12 条（每个点位成本最低）；B 换 11 条；C 换 6 条但要新特性。

## 8. 未验证 / 限制

1. 三个站点的"修复"都是**改产物文本副本**后的反事实（`D:/temp/opencode/cl_layout/r7/patched/`），
   不等于改了反编译器源码；"改哪一层"的结论来自代码阅读 + 注释自述，**未打补丁验证**
   （纪律要求只读）。
2. §5.4 的"恒等变换"论证基于 judge 的比较语义（同位置同对象）与 1013 条实测普查，
   不是对全部 1151 条逐条重编译验证。
3. T3 的 `while 1:` 注入点只定位到候选函数（`_generate_loop_ast` / 区域生成器的 `Constant(True)`
   兜底），没有单函数级最小化复现（需要插桩，属改代码）。
4. 全部分类数字可由 `fresh/gate_r7/r7_29.json` 与 `r7_deep_diff.json` 复核；本文件所有
   "orig/prod" 字样均指"原件 pyc code object / 产物源文本重编译后的 code object"。
