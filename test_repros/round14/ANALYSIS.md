# Round 14 — 测试工程师根因报告（R14-D：dict/容器字面量里的**同级**推导式被焊接）

判据唯一：`_r10_strict_check.strict_compare`（严格尺子，逐指令 + 跳转终点）。本文**不引入任何第二判据**。
复现电池：`test_repros/round14/run_all.py`（17 个形状，2026-09-20 22:56 实测
`repros=17 MISMATCH=10 MATCH=7 ERROR=0 UNEXPECTED=0 NOT-REPRODUCED=1`，`--strict` 退出码 **0**，墙钟 **0.6 s**）。

> **命名消歧**：R14-D 就是 `test_repros/round13/ANALYSIS.md` 里的 **R13-D**（复现文件 `r13_05_dict_two_comprehensions.py`）。
> 本轮（14）把它从「一句话分类」升级为「可下手的指令级定位 + 二分边界 + A/B 反证」。
> 共享任务清单里的「Round 14 — Fix engineer: R14-D」= 本文的 **R14-D**，编号一致，无需换名。

---

## 0. 结论速览（修复工程师只需要读这一段就能动手）

**两个兄弟推导式被 `comprehension_generator.py:111-144` 的 chained-pair 探测器误判为嵌套推导式，
而 `comprehension_generator.py:197` 的逃逸白名单 `_expr_build` 漏掉了 `BUILD_CONST_KEY_MAP`（以及全部
`CALL*`），于是 `comprehension_generator.py:198` 的「推导式结果被更大表达式消费 ⇒ 放弃焊接、交回通用
路径」这道保险没有触发，`:185` 把第二个推导式的 iterable 换成第一个推导式的 AST，`:215` 又用
`prev_end = len(instrs)` 把整块（含第二个推导式自己的装载链 + 键元组 + `BUILD_CONST_KEY_MAP`）声明为已生成。**

归因：**属于 (c) —— 「dict 构建指令从未被识别，尾部整段被吞」**，并伴随 **(a) 的 region 误分类**（pair 探测器
把兄弟当成嵌套）。**明确不是 (b)**：表达式栈没有「弹错操作数」，第二个推导式的 iterable 指令是**根本没被送去
重建**（`comprehension_generator.py:162` 只切了 `_ci1+1:_inner_get_iter` 这一段给第一个推导式，第二个推导式的
装载段落在 `_outer_call_end` 之前却被 `:185` 用第一个推导式的 AST 顶替）。

`file:line` 锚点（全部为现状代码，本轮**未修改任何 core/ 文件**）：

| 位置 | 现状 | 后果 |
|---|---|---|
| `core/cfg/region_ast_generator.py:43106` | `comp_stmt = self.comp_generator.try_generate_comprehension_assign(block, region_ast_gen=self)` | 焊接路径的**唯一入口**，先于通用语句生成 |
| `core/cfg/comprehension_generator.py:67-74` | 收集 `comp_indices`（`LOAD_CONST <code>` + `MAKE_FUNCTION`，co_name ∈ `<listcomp>/<dictcomp>/<setcomp>/<genexpr>`） | 兄弟推导式与嵌套推导式在此**信息完全相同**，无法区分 |
| `core/cfg/comprehension_generator.py:124-131` | `if _first_call_end is None: continue` + `_all_closure = all(... or (LOAD_CONST and hasattr(argval,'co_name')))` | **两重 vacuity**：真嵌套时 `instrs[_first_call_end:_ci2]` 是**空切片** → `all([])=True`；兄弟时该切片**恰好只含兄弟自己的 `LOAD_CONST <code>`**，被第二个 disjunct 判为「闭包装载」→ 也 True。两种情形都被接受 |
| `core/cfg/comprehension_generator.py:139-144` | 只要求「后面还存在某个 `GET_ITER`」+ MAKE_FUNCTION flag 检查 | 兄弟序列同样满足；flag 判据只挡「闭包数变了」这一种 |
| `core/cfg/comprehension_generator.py:162` | `_inner_iter_instrs_raw = instrs[_ci1+1:_inner_get_iter]` | 只重建**第一个**推导式的 iterable |
| `core/cfg/comprehension_generator.py:185` | `_outer_comp_ast = self.parse_comprehension_inner(_cc2, _inner_comp_ast)` | **坍缩发生点**：第二个推导式的 iter 位置被塞进第一个推导式的 AST |
| `core/cfg/comprehension_generator.py:197-199` | `_expr_build = frozenset({'BUILD_TUPLE','BUILD_LIST','BUILD_SET','BUILD_MAP','BINARY_OP','BINARY_SUBSCR'})`；`if any(...): return None` | **保险失效点**：`BUILD_CONST_KEY_MAP` / `CALL` / `CALL_FUNCTION` / `CALL_METHOD` / `CALL_FUNCTION_KW` / `CALL_FUNCTION_EX` / `MAP_ADD` / `LIST_APPEND` / `SET_ADD` / `LIST_EXTEND` / `*_UPDATE` 全部不在集合内 → 该 `return None` 不触发 |
| `core/cfg/comprehension_generator.py:209-215` | 无 store ⇒ `_last_i is RETURN_VALUE` → `Return(_outer_comp_ast)`；`prev_end = len(instrs)` | 尾部指令被**声明为已消费**，`LOAD_CONST ('open_orders','delayed_orders')` + `BUILD_CONST_KEY_MAP 2` 就此消失（不是「没生成」，是「被吞」） |

**通用路径本来能正确产出这个 dict**：`core/cfg/ast_generator_v2.py:948`（`ExpressionReconstructor` 的
`BUILD_CONST_KEY_MAP` 处理，弹键元组 + 弹 count 个值）与 `:1274/:1288-1313`（`CALL` + 推导式 Iter/ComprehensionObject
合并）都在。⇒ 修复方向不是「新造一个 dict 焊接分支」，而是**让 `:198` 的保险认出这些消费者，把控制权还给通用路径**。
（接线：`region_ast_generator.py:195-197` 用同一个 `ExpressionReconstructor` 构造 `ComprehensionGenerator`。）

---

## 1. 真实目标的指令级对齐（唯一权威证据，取自 `D:/Temp/r14/real_dis.txt`）

### 1.1 `site-packages/IQEngine/plugins/plugin_system_simulation/broker.pyc` → `<module>.SimulationBroker.save`
严格尺子：`[seq_len] orig=22 decomp=15`（**-7**）。

```
ORIG (22 条，已滤 NOP/CACHE/PRECALL/EXTENDED_ARG)        DECOMP (15 条)
 #0  RESUME                                              #0  RESUME
 #1  LOAD_CONST   <code <listcomp> line 118>             #1  LOAD_CONST   <code <listcomp>  -> 93>
 #2  MAKE_FUNCTION                                      #2  MAKE_FUNCTION
 #3  LOAD_GLOBAL  NULL + copy                            #3  LOAD_CONST   <code <listcomp>  -> 93>   <- 第二个 code
 #4  LOAD_ATTR    deepcopy                               #4  MAKE_FUNCTION
 #5  LOAD_FAST    self                                   #5  LOAD_GLOBAL  NULL + copy
 #6  LOAD_ATTR    _open_orders                           #6  LOAD_ATTR    deepcopy
 #7  CALL                                                 #7  LOAD_FAST    self
 #8  GET_ITER                                             #8  LOAD_ATTR    _open_orders
 #9  CALL                                                 #9  CALL
#10  LOAD_CONST   <code <listcomp> line 119>             #10 GET_ITER
#11  MAKE_FUNCTION                                       #11 CALL
#12  LOAD_GLOBAL  NULL + copy                            #12 GET_ITER
#13  LOAD_ATTR    deepcopy                               #13 CALL
#14  LOAD_FAST    self                                   #14 RETURN_VALUE
#15  LOAD_ATTR    _delayed_orders                         <- 消失
#16  CALL                                                 <- 消失
#17  GET_ITER            <- 复用（焊接后 comp2 的 iter 是 comp1 的 AST）
#18  CALL
#19  LOAD_CONST   ('open_orders', 'delayed_orders')       <- 消失
#20  BUILD_CONST_KEY_MAP 2                                <- 消失
#21  RETURN_VALUE
```

消失的 7 条 = comp2 的装载链 `LOAD_GLOBAL copy / LOAD_ATTR deepcopy / LOAD_FAST self / LOAD_ATTR
_delayed_orders / CALL`（5 条）+ 键元组 `LOAD_CONST ('open_orders','delayed_orders')` + `BUILD_CONST_KEY_MAP 2`。
`GET_ITER`/`CALL` 没少，只是被 comp2「借用」了 —— 这正是 `:185` 的形状。

产物（`D:/Temp/r14/build/BROKER_DECOMP.py:93`）：

```python
return [o.load() for account, o in [o.load() for account, o in copy.deepcopy(self._open_orders)]]
```

**语义错误，不是布局差异**：dict 结构整体消失，返回值从「两个键的字典」变成一个 list；`_delayed_orders` 从未被读取。

### 1.2 `.../live.pyc` → `<module>.DefaultLiveBroker.save`（同族第二例）
严格尺子：`[seq_len] orig=16 decomp=12`（**-4**）。
消失的 4 条 = `LOAD_FAST self` + `LOAD_ATTR _delayed_orders` + `LOAD_CONST ('open_orders','delayed_orders')` +
`BUILD_CONST_KEY_MAP 2`。产物 `return [o.load() for account, o in [o.load() for account, o in self._open_orders]]`。
与 1.1 同一条代码路径，只是 iterable 更短（无 `copy.deepcopy` 调用），所以吞掉的条数更少。
**⇒ delta 条数不是特征，「第二个 iterable + 键元组 + BUILD_CONST_KEY_MAP」这一组合才是特征。**

---

## 2. 调用链与精确定位（trace 证据：`D:/Temp/r14/where_s01.txt`，`sys.settrace` 返回值断言法）

```
pycdc.py:691 decompile_pyc -> use_region=True
  core/cfg/region_ast_generator.py:1920  _build_function_def()      nested_gen.generate()
  core/cfg/region_ast_generator.py:1181  generate()                 entry_ast = _generate_block_statements(...)
  core/cfg/region_ast_generator.py:41258 _generate_block_statements -> _generate_block_statements_body()
  core/cfg/region_ast_generator.py:43106 _generate_block_statements_body()
      comp_stmt = self.comp_generator.try_generate_comprehension_assign(block, region_ast_gen=self)   # 非 None 即整块交账
  core/cfg/comprehension_generator.py:185  try_generate_comprehension_assign()   <- _chained_pairs 命中
  core/cfg/comprehension_generator.py:803  parse_comprehension_inner()
  core/cfg/comprehension_generator.py:932  _parse_comprehension_inner_impl()
  core/cfg/comprehension_generator.py:1863 _build_comp_result()      -> {'type':'ListComp','generators':[{'iter': ListComp}]}
```

trace 里被捕获的「坍缩返回值」：`value=ListComp(iters=['ListComp'])`，
即**返回类型仍是 ListComp 而不是 Dict**，且它的唯一 generator 的 iter 又是 ListComp ——
一个 region 产出了一个「跨两个推导式」的节点，dict 字面量这个 AST 节点类型**从未出现**。

### 2.1 结构判据：真嵌套 vs 假嵌套（兄弟）在字节码上是可分的

实测两份最小源码（`D:/Temp/r14/nest_vs_sib.txt`，同一 Python 3.11 编译器）：

```
真嵌套  {'a': [y for y in [x for x in t]], 'b': 1}      兄弟  {'a': [x for x in t], 'b': [y for y in u]}
  2  LOAD_CONST <code>                                    2  LOAD_CONST <code>
  4  MAKE_FUNCTION            <- 外层                     4  MAKE_FUNCTION
  6  LOAD_CONST <code>        <- 内层                     6  LOAD_FAST t
  8  MAKE_FUNCTION                                       8  GET_ITER
 10  LOAD_FAST t                                        14  CALL
 12  GET_ITER                                            ...  <- 第二个 MAKE_FUNCTION 在 CALL **之后**
 18  CALL               <- 第二个 MAKE_FUNCTION 在首个
 28  GET_ITER              CALL **之前**（偏移 8 < 12）
 34  CALL
```

判据（一句话）：**真嵌套时，第二个 `MAKE_FUNCTION` 的索引 < 第一个推导式的 `GET_ITER` 的索引
（更 < 其 `CALL`）；兄弟时它 > 第一个 `CALL`。** 现状代码 `:117-123` 反向使用这个事实：它从 `_ci1+1` 找
第一个 `GET_ITER` 并当作「第一个推导式的结束」，对兄弟而言这确实是对的（`_first_call_end` 落在 `CALL` 之后），
但它随后只用 `_after_first` 做「是否只有闭包装载」的弱检验（§0 表第 3 行），**没有校验 `_ci2` 是否落在
`_first_call_end` 之前** —— 而这恰恰是嵌套的充要结构。

---

## 3. region-reduction 算法对本类缺陷的要求（不变式，修复必须可被这三条检验）

1. **一个 region / 一段被声明消费的指令 ⇒ 恰好一种 AST 节点类型。**
   焊接路径认领整块时，产出的节点类型必须是**该块最外层消费者的类型**（此处为 `Dict`），
   而不是其中一个子表达式的类型（`ListComp`）。产出 `ListComp` 而块尾是 `BUILD_CONST_KEY_MAP`，即类型不匹配 ⇒ 违规。
2. **dict/list/tuple/set 字面量的每个值子 region 必须各自归约成它自己的表达式节点**，然后由**一条**容器构建
   指令（`BUILD_CONST_KEY_MAP` / `BUILD_MAP` / `BUILD_LIST` / `BUILD_TUPLE` / `BUILD_SET` / `CALL*`）合成父节点。
   `:185` 把一个值（comp1）塞进另一个值（comp2）的 iter 槽 ⇒ 两个子 region 塌成一个节点，值数从 2 变 1，违规。
3. **不得声明自己没翻译的指令。** `:215` 的 `prev_end = len(instrs)` 是「我全吃了」的记账；
   只有当 `_ow_clean` 里的每条指令都已映射进 AST 时才允许。任何「尾部还有指令但我不认识」的情形都必须
   `return None`（即 `:199` 那条逃逸），交回通用 `ExpressionReconstructor`（`core/cfg/ast_generator_v2.py:948`）。
   **这正是现状唯一缺失的一环**：`_expr_build` 是第 3 条不变式的机器可读形式，它的成员表不完整。

---

## 4. 缺陷面二分表（17 个复现文件；每次只改一个轴）

| 文件 | 形状（唯一变量加粗） | 实测 | EXPECT | 二分结论 |
|---|---|---|---|---|
| `r14_01_dict_two_listcomps.py` | `{'a': [x for x in t], 'b': [y for y in u]}` | MISMATCH 14→11 ×3 函数 | MISMATCH | 基准形状即最小复现，无需 broker 规模 |
| `r14_02_dict_two_comps_call_iter.py` | iterable 是 `list(t)` / `copy.deepcopy(self._x)` 调用 | MISMATCH **22→15**（broker 字面复现）| MISMATCH | 装载链越长吞得越多，同一缺陷 |
| `r14_03_dict_three_listcomps.py` | **三个**兄弟值 | MATCH | UNCONFIRMED | `:113` 相邻配对 + 第 3 个值使 `_after_first` 含 `LOAD_CONST 'c'`（非 code）→ `_all_closure` False → 探测器**自动失效**。⇒ 缺陷只在「恰好 2 个相邻推导式值」时发作；**不得把它当修复证据**，也不得为凑 MISMATCH 改这个文件 |
| `r14_04_neg_dict_one_listcomp.py` | 1 个推导式 + 标量 / + `len(u)` 调用 | MATCH | MATCH | 负对照：`comp_indices < 2` 时 `:112` 不进分支，通用路径正确 |
| `r14_05_neg_genuine_nested_comps.py` | `[[x for x in row] for row in t]`、`{k: [x for x in v] for k,v in t}` | MATCH | MATCH | **关键负对照**：焊接分支对真嵌套是**有用的**，整体删掉它必翻坏此类 |
| `r14_06_dict_nested_plus_sibling.py` | `{'a': [[x for x in row] for row in t], 'b': [y for y in u]}` | MISMATCH 14→11，且 `<listcomp>` 子对象 13→9 | MISMATCH | 嵌套合法 + 再加兄弟 ⇒ 配对时把「外层」与「兄弟」配成假对；**子 code 也被改坏**（不是只丢父层） |
| `r14_07_neg_list_two_listcomps.py` | `[[x for x in t], [y for y in u]]` + `[{x:x for x in t}, {y:y for y in u}]` | MATCH | MATCH | 负对照：`BUILD_LIST` **在** `:197` 白名单里 ⇒ `:199` 正常 `return None` |
| `r14_08_neg_tuple_two_listcomps.py` | `([x for x in t], [y for y in u])` | MATCH | MATCH | 负对照：`BUILD_TUPLE` 在白名单 |
| `r14_17_neg_set_two_comps.py` | `{[x for x in t][0], [y for y in u][0]}`（`BUILD_SET` + 尾随 `BINARY_SUBSCR`） | MATCH | MATCH | 负对照：`BUILD_SET`/`BINARY_SUBSCR` 在白名单 |
| `r14_09_call_args_two_listcomps.py` | `dump([x for x in t], [y for y in u])` | MISMATCH 14→11 | MISMATCH | **容器不是 dict 也发作**：消费者是 `CALL` ⇒ 证明白名单缺 `CALL*` |
| `r14_10_kwargs_two_listcomps.py` | `dump(a=[...], b=[...])`（`LOAD_CONST keys` + `CALL_FUNCTION_KW`） | MISMATCH 15→11 | MISMATCH | 同上，键元组同形 |
| `r14_11 / r14_12 / r14_13` | 值改 `{x for x in t}` / `{x: x for x in t}` / `(x for x in t)` | MISMATCH 14→11 ×3 | MISMATCH | **与推导式种类无关**（`<setcomp>/<dictcomp>/<genexpr>` 同样中招；genexpr 的 `MAKE_FUNCTION` flag=1 也照样通过 `:140-143`）|
| `r14_16_dict_two_comps_mixed_kinds.py` | list comp + set comp 混合 | MISMATCH 14→11 | MISMATCH | 两个 kind 不同也不影响触发 |
| `r14_14_assign_dict_two_comps.py` | `d = {...}` 与 `if flag: return {...}` | MISMATCH 16→13 / 18→15 | MISMATCH | **非 return 专属**：`:205-208` 的 store 分支同样吞尾（`prev_end = instrs.index(_store_instr)+1`，而 `_store_instr` 扫描在 `_ow_post` 里找不到 store ⇒ 落到 `:210` 分支）|
| `r14_15_neg_store_subscr_two_comps.py` | `d['a']=[...]` 两条 `STORE_SUBSCR`；`a=[...]; b=[...]` 两条语句 | MATCH | MATCH | 负对照：**每条语句各自成块**时探测器不误伤 ⇒ 触发条件是「两个 `MAKE_FUNCTION` 落在同一个基本块内且尾随 `BUILD_CONST_KEY_MAP`/`CALL`」 |

汇总：10 个 MISMATCH（含 broker 字面形状 `r14_02`）+ 6 个负对照 MATCH + 1 个 UNCONFIRMED（`r14_03`，如实记为
NOT-REPRODUCED）。**负对照的 MATCH 不是本轮的功劳**，它们是修复的边界护栏。

---

## 5. A/B 反证（**不改仓库**：`inspect.getsource` → 内存改文本 → `exec` → `setattr`，脚本
`D:/Temp/r14/ab_patch.py`，输出 `D:/Temp/r14/ab_sweep.txt`；28 个形状 + broker + live）

- **a1** = 把 `:197` 的 `_expr_build` 补齐为
  `{'BUILD_TUPLE','BUILD_LIST','BUILD_SET','BUILD_MAP','BUILD_CONST_KEY_MAP','BINARY_OP','BINARY_SUBSCR',
  'MAP_ADD','LIST_APPEND','SET_ADD','LIST_EXTEND','DICT_UPDATE','SET_UPDATE','CALL','CALL_FUNCTION',
  'CALL_METHOD','CALL_FUNCTION_KW','CALL_FUNCTION_EX'}`（即「推导式结果被任何消费者使用」的完整判据）。
- **a2** = 在 `:124` 之后加一条结构判据 `if _ci2 > _first_call_end: continue`（兄弟必须跳过，只有 §2.1 的真嵌套形状才允许焊接）。

实测（每个 pyc 用其**自身**原始 code 做基准，`_load_map` + `strict_compare` 逐限定名）：

| 模式 | 14 个缺陷形状 | 14 个对照形状 | broker.pyc | live.pyc |
|---|---|---|---|---|
| base | 全 MISMATCH（`seq_len -3/-4/-5/-7` + 子 `<listcomp>` `seq_diff`） | 全 MATCH | `save` 22→15 | `save` 16→12 |
| a1 | **全部转 MATCH** | 全部保持 MATCH（零变化） | **全文件 MATCH（所有函数）** | **全文件 MATCH（所有函数）** |
| a2 | **全部转 MATCH** | 全部保持 MATCH（零变化） | **全文件 MATCH（所有函数）** | **全文件 MATCH（所有函数）** |

⇒ 根因**双向成立**：`:197` 白名单不完整（a1 直接证明）与 `:124-131` 配对判据过弱（a2 直接证明）是同一缺陷的
两处表现，任一处补强都足以翻转本轮全部缺陷形状，且**都不越界**（对照零变化）。

**次要观察（写下来免得修复工程师误判）**：`ab_sweep.txt` 里 a2 的 `*_DECOMP.pyc` 行仍报
`<listcomp> [seq_diff] #4 orig=("'y'",...) decomp=("'x'",...)`。那是**第二轮往返**（拿 base 的产物再反编译）
产生的子级差异，不是主判据；a1 连这一层都是干净的。⇒ **若要一次做彻底，优先 a1（消费者白名单），
a2 作为第二道判据叠加更稳（a3 = a1+a2，实测同样全绿）。**
主判据（原 pyc vs 修复后反编译重编译）在 a1/a2/a3 下均为 MATCH。

---

## 6. 子级 `seq_diff`（常被忽略的第二症状，同一根因）

`r14_01/09/10/11/12/13/14/16` 除父函数 `seq_len` 外还报
`<module>.X.<listcomp> [seq_diff] #4 orig=("'x'", 'STORE_FAST') decomp=("'y'", 'STORE_FAST')`。
含义：产物里**剩下的那个子 code 对象**是 comp2 的 body（`'y'`）却挂在 comp1 的装载链上 ——
`:178/_cc1` 与 `:185/_cc2` 的次序错位。修复后这条必须一并消失（a1 实测确实消失）。
**只把父层条数凑平（例如让 `:215` 少吞几条）会留下这条子级缺陷 ⇒ 仍不合格。**

---

## 7. 修复护栏（必须逐条自测，全部已在电池里有对应形状）

1. 不得整体删除 `_chained_pairs` 分支：`r14_05`（真嵌套）当前 MATCH，删了就 UNEXPECTED。
2. 交回通用路径后必须仍能产出正确 dict：`r14_04`（单推导式 + 标量、+ `len(u)`）与 `r14_07/08/17`
   （`BUILD_LIST/TUPLE/SET` 已走这条路）是现成的行为参照。
3. 三兄弟 `r14_03` 现在 MATCH 是**巧合性正确**（`_all_closure` 因中间有键 `LOAD_CONST 'c'` 而失败）。
   加强判据后它必须**仍然** MATCH；若翻成 MISMATCH 说明新判据把配对放宽了。
4. 赋值宿主 `r14_14` 与 `if` 臂宿主同形状：`:205-208` 分支不能只修 `:210` 的 Return 分支。
5. 修完请由**修复工程师**跑全量 402 文件回归；本轮明确未跑（测试工程师不做全量门）。

---

## 8. 复现用法

```bash
cd F:/Downloads/pythoncdc-main
# 全电池（<1 s；产物只落 D:/Temp/r14/build/）
PYTHONIOENCODING=utf-8 python -u test_repros/round14/run_all.py --show-diff
PYTHONIOENCODING=utf-8 python -u test_repros/round14/run_all.py --strict   # 有 UNEXPECTED 才非 0
PYTHONIOENCODING=utf-8 python -u test_repros/round14/run_all.py 01 02 05   # 按编号取子串
```
修复后翻账方式（round13 约定）：把已翻正的键从 `'MISMATCH'` 改成 `'SENTINEL'`，
`r14_03` 若因新判据真的复现则改 `'MISMATCH'`（当前状态记为 `REVIVED` 需回查）。

真实目标单函数复核（不跑全量）：
```bash
PYTHONIOENCODING=utf-8 python -u D:/Temp/r14/probe_real.py > D:/Temp/r14/real_dis.txt 2>&1   # dis 对齐 + 产物
PYTHONIOENCODING=utf-8 python -u D:/Temp/r14/ab_patch.py base <pyc> [keyfilter]              # 单 pyc 严格复核
```

---

## 9. 环境/取证注记（本轮踩过的坑，写给下一位）

- **Git Bash 里不要用 `timeout` 前缀**：`timeout.exe`（Windows 自带）会遮蔽 coreutils 的同名命令并吞掉管道，
  表现为「exit 0 且零输出」。约束「单条命令 < 300 s」请改用 Bash 工具的 `timeout` 参数（≤295000 ms）。
- 所有 python 调用一律 `PYTHONIOENCODING=utf-8 ... > file 2>&1` 再读文件，避免控制台编码截断。
- 构建产物、探针、日志全在 `D:/Temp/r14/`（`build/`、`ab/`、`shapes*/`、`real_dis.txt`、
  `where_s01.txt`（settrace 定位）、`ab_sweep.txt`（A/B）、`nest_vs_sib.txt`、`r14_battery.txt`）。
  仓库内**只新增** `test_repros/round14/` 的 18 个文件；`core/`、`scripts/`、`site-packages/`、
  `pyc_index.json`、`_r10_strict_check.py`、`test_repros/round13/` 全部零改动（git 可核）。
- 一次性异常：`probe_shapes.py` 首跑对 3 个形状给出与后续 4 次复跑不一致的结论
  （`s12/s15/s20` 报 MATCH、`s02` 报 +8）。已排除哈希种子（`PYTHONHASHSEED=0` 与 `=1` 产物逐字节相同）；
  连续 4 次复跑（`shapes.txt`/`shapes2.txt`/`h0a.txt`/`h0b.txt`/`h1.txt`）互相完全一致 ⇒
  判定为单次离群，采信稳定结果，`run_all.py` 因此**未**加 PYTHONHASHSEED 自举。若修复工程师遇到
  同类离群，先复跑一次再改代码。
- `decompile_pyc`（`pycdc.py:691`）无跨进程缓存（仅 `core/ast_nodes.py:35` 可选的 in-process LRU），
  小文件电池 0.6 s 属正常，不代表「没真的反编译」；`test_repros/round14/run_all.py` 每次都会重写
  `D:/Temp/r14/build/*_DECOMP.py`，可直接肉眼看产物。
