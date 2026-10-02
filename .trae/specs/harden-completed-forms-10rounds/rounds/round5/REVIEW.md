# Round 5 评审（对抗性审查：推导式族 ListComp / SetComp / DictComp / GeneratorExp / comprehension / nested_comprehension）

- 评审人：评审工程师（Round 5，对抗攻击者）
- 日期：2026-10-02
- 唯一判据：`scripts/pyc_verify.py`（附件 pylingual `compare_pyc`，逐 code object 单元判 Equal，全 Equal 才 success）；验证方式 = `python -c "import py_compile; py_compile.compile(file='test_repros/round5/X.py', cfile='test_repros/round5/X.pyc', doraise=True)"` → `python pycdc.py -o test_repros/round5/XOK.py test_repros/round5/X.pyc` → `python scripts/pyc_verify.py single test_repros/round5/X.pyc`。
- 首分歧定位工具：`test_repros/round3/_r3_firstdiff.py` + 本轮新增只读对照器 `test_repros/round5/_r5_cmp.py`（将 code object 身份/地址/行号归一为名字后逐指令 diff，消除 `<module>` 级 LOAD_CONST code-object 同身份噪声；仍只读，不修改 core/ 与 scripts/）。所引三元组为 `(offset, opname, argval)`，o=原 pyc，d=OK.py 重编译。
- 硬约束遵守：未修改任何 `core/`、`scripts/`、`pycdc.py`、既有 `*OK.py`、`site-packages/`、`.trae/specs/` 既有内容；每条 shell 命令 ≤300 s；全部 `*OK.py` 由 `pycdc.py` 生成。
- 源码级合法性注记：构造中 2 个初版形态为 CPython 3.11 源码级非法（`[*a for a in pairs]`（解包不得作推导式体顶层）、`[v for v in (s := xs)]`（walrus 不得入 iterable 表达式）），已在攻击源内替换为合法同族形态（`[[*a] for a in pairs]`、双 walrus 体），非判据产物问题。
- 管线活性探针：`probe_comp_min`（最小 `[x*2 for x in xs]`）= **3/3 success** —— 推导式管线活性确认，后续按形态覆盖展开。

---

## §1 任务A — 推导式族攻击总表（14 攻击面 / 16 文件：13 r5_* + 负对照 n5_01 + 2 探针；可比较 192 单元 180 MATCH，另 r5_07 compile_error 11 单元不可比）

统计：**MISMATCH 文件 7/16（r5_04、r5_06、r5_07、r5_09、r5_10、r5_11、probe_lam_default）**；文件级 success 9/16；单元级 **180/192 = 93.75%（可比较面），失败 12 单元**；加 r5_07 compile_error（0/11 不可比）后为 180/203 = 88.7%。**wiki 将 ListComp/SetComp/DictComp/GeneratorExp/comprehension/nested_comprehension 判为「完备」的声明被对抗证伪**：14 攻击面中 8 面全 MATCH（浅层封闭），6 面 MISMATCH（跨 clause 条件、解包 target、walrus、try/finally×return-comp、async 组合、lambda 默认值）。

### 全表（读数均以 pyc_verify single 输出为准）

| 文件 | 攻击面（任务书编号） | 函数数 | 读数（single） | 失败单元签名（首分歧指令三元组 / 产物形态） | 破口 |
|---|---|---|---|---|---|
| probe_comp_min | 活性探针：最小 listcomp | 1 | **3/3 success** | — | — |
| r5_01_comp_basic | 1 ListComp 基础 + 2 SetComp/DictComp | 6 | **13/13 success** | — | — |
| r5_02_genexp | 3 GenExp（实参/赋值保留/嵌套实参/join） | 5 | **12/12 success** | — | — |
| r5_03_comp_multifor | 4 多 for（二层/三层/依赖 iter/dict/set/genexp 多 for） | 6 | **13/13 success** | — | — |
| r5_04_comp_cond | 5 条件推导（单 if/双 if/if-else 体/跨 for 条件/for 间条件/set 条件） | 6 | **12/13 failure** | `c_between_fors.<listcomp>` Different control flow，首分歧 @3 o(8,'FOR_ITER',58) vs d(8,'FOR_ITER',50)；@5 o(12,'LOAD_FAST','x') vs d(12,'LOAD_DEREF','b')；27→23 指令。产物 `[x+y+z for x in a for y in b for z in c]` —— **`if x`、`if y` 两个跨 clause 过滤条件整体丢失**（尾部双 if 的 c_double_if MATCH） | **B20** |
| r5_05_comp_nested | 6 嵌套推导（矩阵/flatten/dict 内推导/推导式实参内推导/三层 cube/genexp 内嵌） | 6 | **19/19 success** | — | — |
| r5_06_comp_unpack | 7 解包/星号推导 | 6 | **11/13 failure** | `u_nested_target.<listcomp>` Different bytecode：@3 o(8,'UNPACK_SEQUENCE',2) vs d(8,'UNPACK_SEQUENCE',3)，产物 `[a + c for a, b, c in triples]` —— **嵌套元组目标 `(b, c)` 拍平**；`u_star_target.<listcomp>` Different bytecode：@3 o(8,'UNPACK_EX',1) vs d(8,'UNPACK_SEQUENCE',2)，产物 `[a + rest[0] for a, rest in pairs]` —— **星号目标 `*rest` 坍缩为普通名**。正向：`for a, b`（u_tuple_target）、`[[*a] for a in pairs]`（u_star_body）、`[[*a, *b] ...]`（u_two_star）、`d.items()`（u_dict_items）全 MATCH | **B21** |
| r5_07_comp_walrus | 8 walrus 在推导式内 | 5 | **compile_error 0/0**（11 单元不可比） | 产物 5 函数全部被注入**幻影迭代目标**：`[(y := x * 2) for x in xs]` → `[(y := x * 2) for x, y in xs]`、`[x for x in xs if (n := x * 2) > 4]` → `[x for x, n in xs if (n := x * 2) > 4]`、w_double_if 注入双幻影 `for x, p, q in xs`。py_compile 报 `SyntaxError: assignment expression cannot rebind comprehension iteration variable 'y'`（line 5）——文件级语法非法，0 单元可比 | **B22** |
| r5_08_comp_in_loop | 9 循环体/分支内推导式（for×break/continue、while、if 分支、genexp 守卫 break、嵌套循环） | 6 | **14/14 success** | — | — |
| r5_09_comp_try | 10 try 包推导式 + 属性链/下标/方法链 iterable | 6 | **11/12 failure** | `t_try_finally` Different bytecode：@8 o(30,'LOAD_FAST','log') vs d(30,'POP_TOP',None)；o 侧 (98,'RETURN_VALUE') 处 d 侧为 (98,'POP_TOP')+(100,'LOAD_CONST',None)+(102,'RETURN_VALUE')。产物 `try: [x for x in xs] / finally: log.append(len(xs))` —— **`return <推导式>` 的 return 被剥除：推导式值 POP_TOP 丢弃、函数改返回 None**。正向：try/except 包 return-comp（t_try_wrap）、try 内逐元素、属性链/下标/方法链全 MATCH | **B24** |
| r5_10_comp_async | 11 async 推导 | 6 | **9/13 failure** | `a_async_multi` Different control flow + `a_async_multi.<listcomp>` **Missing bytecode**；`a_await_body` 同。首分歧 a_async_multi @5 o(12,'LOAD_CONST',`<code:<listcomp>>`) vs d(24,'GET_AWAITABLE',0)。产物两函数体均为 **`await ait()`** —— 推导式整体坍缩为对 iterable 的 await 调用，`<listcomp>` 代码对象整个丢失。正向：单 async for 裸体/带 if（a_async_for、a_async_cond）、async set/dict comp 全 MATCH | **B23** |
| r5_11_comp_lambda | 12 lambda/闭包×推导式 | 6 | **17/19 failure** | `lam_default_arg.<listcomp>` / `lam_with_arg.<listcomp>` Different bytecode（两者签名一致）：@4 o(10,'LOAD_FAST','x') vs d(10,'LOAD_CONST',`<code:<lambda>>`)；@7 o(16,'MAKE_FUNCTION',1) vs d(16,'JUMP_BACKWARD',6)；11→9 指令。产物 `[lambda x: x * 2 for x in xs]` / `[lambda v, y: v + y for x in xs]` —— **lambda 默认值元组（LOAD_FAST x; BUILD_TUPLE 1 + MAKE_FUNCTION flags 1→0）整体丢失**。正向：晚绑定 `[lambda: x for x in xs]`（lam_late_binding）、map/立即调用/genexp 内 lambda 全 MATCH | **B25** |
| r5_12_comp_compress | 13 压缩形态（list()/tuple()/set()/sorted()/any()/all()/dict()/join 消费 genexp） | 8 | **17/17 success** | — | — |
| r5_13_comp_return | 14 推导式作 return + 多推导式共存 | 6 | **18/18 success** | — | — |
| probe_lam_default | 追加鉴别探针：lambda 默认值 函数级 vs 推导式级 | 2 | **4/6 failure** | `fd_stmt` Different bytecode：@0 o(2,'LOAD_GLOBAL','x') vs d(2,'LOAD_CONST',`<code:<lambda>>`)；@3 o(18,'MAKE_FUNCTION',1) vs d(6,'MAKE_FUNCTION',0) —— **函数级 `f = lambda x=x: x*2` 同样丢默认值**（B25 非推导式专属）；`fd_in_comp.<listcomp>` 同 r5_11 签名 | **B25** |
| **n5_01_control（负对照）** | 等价 for+append/add/赋值循环（覆盖面 1/2/4/5/6 的循环等价形） | 6 | **7/7 success** | —（判据无误报，失败非误归因于循环本身） | — |

单元合计：可比较 192（180 MATCH / 12 MISMATCH）+ compile_error 11 不可比（r5_07 名义 11 单元）。

---

## §2 机制分析（锚点均 2026-10-02 实际 grep/read/探针核对；新破口 B20–B25 续接登记）

理论权威：`wiki/concepts/decompile-invariant-completeness.md` §1（C1 局部消费 / C2 黑箱组合 / C3 守卫封闭）；被攻击声明 = 该文件 :165 行「ListComp / SetComp / DictComp / GeneratorExp / comprehension → `comprehension_generator.py` 专用管线 `:2074`、`ast_generator_v2.py:4284` → **完备**」及 :185 行「nested_comprehension → `comprehension_generator.py:2074` 族 → 完备」。实测 `comprehension_generator.py` 共 2217 行；多 for 重建入口 `_parse_multi_for_comprehension`（:1029 起，:910-914 FOR_ITER 计数判多 for）；单 for 重建 `_parse_comprehension_inner_impl`（:903 起）；target 装配 `_build_comprehension_target`（:1358）。

### B20 — 多 for 推导式跨 clause 过滤条件整体丢失（**新登记，未修**）

- **破坏条款**：C3（守卫封闭失败）+ C1（语义破缺：过滤谓词被静默剥除，产出超集）
- **现象**：`[x + y + z for x in a if x for y in b if y for z in c]` → `[x + y + z for x in a for y in b for z in c]`（`<listcomp>` 27→23 指令，控制流少两条 `POP_JUMP_BACKWARD_IF_FALSE` 回边）。字节码形态：跨 clause 过滤 = `STORE_FAST x; LOAD_FAST x; POP_JUMP_BACKWARD_IF_FALSE → 本层 FOR_ITER`（原 pyc `c_between_fors.<listcomp>` @12-14 实测），与尾部过滤同型，仅位置在后续 FOR_ITER 之前。
- **机制（已定位，锚点实测）**：多 for 路径 `_parse_multi_for_comprehension` 装配每个 generator 时**硬编码 `'ifs': []`**（`comprehension_generator.py:1102`，generators.append 字面量），随后**只在最内层 generator 上挂 ifs**：`generators[-1]['ifs'] = ifs`（:1121 三元 filter 分支、:1156 三元+filter 分支、:1175 普通 filter 分支）。非最内层 generator 的过滤条件无任何提取路径 → 静默丢失。尾部条件（挂在最内层 for 后，如 c_single_if/c_double_if/sc_cond_set）经 `_extract_comp_ifs(all_instrs, innermost_store_idx, append_idx)` 提取窗覆盖 → MATCH，与本破口互为对照组。
- **复现组**：r5_04.c_between_fors（1 单元）。
- **状态**：已定位（识别/装配层锚点 :1102/:1121/:1156/:1175 实测确认）。

### B21 — 推导式 for-target「名袋」重建：嵌套元组拍平 + 星号目标坍缩（**新登记，未修**）

- **破坏条款**：C1（目标结构失真 → 迭代绑定语义改变）
- **现象与签名**：
  - `for a, (b, c) in triples` → `for a, b, c in triples`（`u_nested_target.<listcomp>` @3 o(8,'UNPACK_SEQUENCE',2) vs d(8,'UNPACK_SEQUENCE',3)——原字节码为 UNPACK_SEQUENCE 2 + 内层再 UNPACK，重编译为顶层 3 元解包）；
  - `for a, *rest in pairs` → `for a, rest in pairs`（`u_star_target.<listcomp>` @3 o(8,'UNPACK_EX',1) vs d(8,'UNPACK_SEQUENCE',2)——UNPACK_EX 坍缩为普通解包，`rest` 从「剩余元素列表」变为「第二个元素」，语义翻转）。
- **机制（已定位，锚点实测）**：`_find_comp_target_names`（`comprehension_generator.py:1348-1356`）把**整个推导式 code object 内所有** `STORE_FAST/STORE_DEREF/STORE_NAME` 的 argval 收进一个名字列表（名袋），`_build_comprehension_target`（:1358-1377）对 >1 个名字一律发 `Tuple(Name…) 目标`。该判据不读 UNPACK_SEQUENCE/UNPACK_EX 的嵌套 arity 与星号位，也不验证 STORE 是否真属解包链——嵌套目标与星号目标的结构信息在名袋里不可表达。
- **正向对照**：扁平二元目标 `for a, b`（UNPACK_SEQUENCE 2 恰好对应两名）名袋重建碰巧正确 → u_tuple_target MATCH；`[[*a] for a in pairs]` 星号在**体**内（display 展开非 target）不受此路径影响 → MATCH。
- **复现组**：r5_06.u_nested_target、u_star_target（2 单元）。
- **状态**：已定位（:1348-1377 实测确认）。

### B22 — walrus STORE 被名袋吸收为幻影迭代目标 → 产物语法非法（**新登记，未修，最高优先级**）

- **破坏条款**：C2（黑箱组合失败 → 输出语法非法，全文件 0 单元可比）
- **现象**：r5_07 全部 5 函数产物被注入幻影迭代目标：`[(y := x * 2) for x in xs]` → `[(y := x * 2) for x, y in xs]`；`[x for x in xs if (n := x * 2) > 4]` → `[x for x, n in xs if (n := x * 2) > 4]`；w_double_if 一次注入双幻影 `for x, p, q in xs` 且两个 if-filter 被合并为 `and`（该合并本身字节等价，非独立破口）。`py_compile` 判 `SyntaxError: assignment expression cannot rebind comprehension iteration variable 'y'`（产物 line 5）→ 文件级 compile_error，11 单元不可比。
- **机制（已定位，锚点实测）**：同 B21 名袋——3.11 中推导式内 walrus 编译为 `COPY 1; STORE_DEREF y`（原 pyc `w_body.<listcomp>` @20-22 实测，y 为 freevar），`_find_comp_target_names`（:1348）不区分「解包目标 STORE」与「walrus 副作用 STORE」，把 y 计入 target names → Tuple 目标。**同文件内已有正确先例可对照**：`_split_dict_comp_kv` 的 [Round10-05] 注记（:1189-1196）明示「仅保留 COPY 1 + STORE_* 的 walrus 块、过滤其余 STORE_*」——target 路径没有等价守卫。
- **复现组**：r5_07 全体 5 函数（w_body / w_cond / w_body_use / w_double_if / w_two_walrus）。
- **状态**：已定位（:1348-1356 + 正确先例 :1189-1196 实测确认）。

### B23 — async 推导式整体坍缩为 `await <iterable>()`，`<listcomp>` 代码对象 MISSING（**新登记，未修**）

- **破坏条款**：C2（结构组合灾难：推导式区域未成立，函数体被 await 表达式顶替）+ C1（元素变换/多 for 语义全丢）
- **现象与签名**（r5_10 4 失败单元 / 2 函数）：
  - `[x + y async for x in ait for y in b]` → 函数体 **`await ait()`**；`a_async_multi` Different control flow + `a_async_multi.<listcomp>` Missing bytecode；首分歧 @5 o(12,'LOAD_CONST',`<code:<listcomp>>`) vs d(24,'GET_AWAITABLE',0)（重编译体为 CALL ait + GET_AWAITABLE + SEND await 循环）。
  - `[await g(x) async for x in ait]` → 同坍缩为 `await ait()`。
- **机制（已定位至路径，精确分支待查）**：async 推导式识别锚点 = `comprehension_generator.py:316-325`（外层 GET_AITER 识别、`_async_iter` 标记）与 :1014-1024（is_async 判据：GET_AITER/GET_ANEXT/END_ASYNC_FOR 任一出现即 async）、await 模板块焊接 :112-139（`_has_async_comp` → `_extra_async_blocks`）。两个失败形态的共同点 = async for 之外还有第二条装配轴（后随**同步** for clause / elt 含 **await**）：函数体区域的装配把 `MAKE_FUNCTION <listcomp>; LOAD ait; GET_AITER; CALL; GET_AWAITABLE; SEND…` 序列归约为 Await(Call(iter)) 表达式语句，`co_consts` 里的 `<listcomp>` 代码对象从未被认领（Missing bytecode 的直接来源）。单 async for + 简单体/简单 if（识别路径无第二装配轴）MATCH，为对照组。
- **复现组**：r5_10.a_async_multi、a_await_body（2 函数 4 单元）。
- **状态**：已定位（签名 + 识别锚点 :316-325/:1014-1024/:112-139 实测），精确归约分支待查。

### B24 — try/finally 包 `return <推导式>`：return 剥除、值 POP_TOP 丢弃、函数改返回 None（**新登记，未修**）

- **破坏条款**：C1（局部消费丢失：返回值→None）
- **现象与签名**：`try: return [x for x in xs] / finally: log.append(len(xs))` → `try: [x for x in xs] / finally: …`。逐指令对照（`_r5_cmp` 实测，o=原 pyc / d=OK.py 重编译，均滤除 RESUME/CACHE/PRECALL 噪声）：o 侧 `CALL(20) → LOAD_FAST log(30) → …append 序列… → RETURN_VALUE(98)`（返回值压栈穿越 finally 体）；d 侧 `CALL(20) → **POP_TOP(30)** → …append 序列… → POP_TOP(98) → LOAD_CONST None(100) → RETURN_VALUE(102)`。28→30 指令，返回值被 POP_TOP 消费、追加显式 `return None`。
- **机制（签名级已定位，精确分支待查）**：推断式侧存在「推导式后跟 POP_TOP → 降级为 Expr 语句」的判据（`comprehension_generator.py:555-565` [Round 9 fix] 注记自述「POP_TOP 是语句终结符，把 wrapper 段（表达式）与其后的语句段切开」）；try/**finally** 装配把 `return <comp>` 的 RETURN_VALUE 区段重组后，推导式与 POP_TOP 相邻，落入该 Expr 降级路径，RETURN 语义被吞。对照组：try/**except** 包 `return [x*2 for x in xs]`（t_try_wrap）与 try 内逐元素 try（t_try_in_loop）均 MATCH —— 单向破口（仅 try/finally × return-comp 组合触发）。
- **复现组**：r5_09.t_try_finally（1 单元）。
- **状态**：已定位（字节级签名 + 判据候选 :555-565），精确触发分支待查。

### B25 — lambda 默认值元组整体丢失（函数级与推导式内双杀）（**新登记，未修**）

- **破坏条款**：C1（默认值语义丢失：调用方少参即 TypeError）
- **现象与签名**：`lambda x=x: x * 2` → `lambda x: x * 2`（位置默认）、`lambda v, y=x: v + y` → `lambda v, y: v + y`。签名：defaults 元组构建指令对（`LOAD_FAST x; BUILD_TUPLE 1`）+ `MAKE_FUNCTION` flags 位 1 → 0。推导式内：`lam_default_arg.<listcomp>` @4 o(10,'LOAD_FAST','x') vs d(10,'LOAD_CONST',`<code:<lambda>>`)、@7 o(16,'MAKE_FUNCTION',1) vs d(16,'JUMP_BACKWARD',6)（11→9 指令）；函数级（probe_lam_default.fd_stmt）@3 o(18,'MAKE_FUNCTION',1) vs d(6,'MAKE_FUNCTION',0)。参数名（co_varnames）保留，仅默认值丢。
- **机制（已定位至装配链，精确丢弃分支待查）**：判据侧排除——`ExpressionReconstructor` 的 MAKE_FUNCTION 分支（`ast_generator_v2.py:1975` 起）对 flags&1 弹栈并写入 `FunctionObject['defaults']`（**本轮探针实测**：对 `lam_default_arg.<listcomp>` elt 窗 `[LOAD_FAST x; BUILD_TUPLE 1; LOAD_CONST <lambda>; MAKE_FUNCTION 1]` 调 `reconstruct` 产出 `FunctionObject{code, defaults=Tuple[Name x]}`，正确）。发射侧排除——`_generate_lambda_from_dict`（`code_generator.py:4948`）复用 `_generate_arguments_dict`（:542-601）支持 defaults 渲染。故丢弃点位于**区域管线装配 Lambda dict 的链路**：`_build_function_def`（`region_ast_generator.py:2024`）的 defaults 装配（:2041-2062）依赖 `func_obj['defaults']` 键存在，而该链路上产出的 FunctionObject 未携带（或携带后被嵌套 code object 递归反编译路径以仅含 co_varnames 的 args 重建覆盖；候选锚点：:2168 与 :21797-21845 `_convert_lambda_function_objects`——其 dict-children 键清单 `('func','value','left','right','test','operand','target','iter','subject','slice')` **不含 `elt`/`generators`**，ListComp.elt 下的 FunctionObject 不经此转换）。最小复现 = probe_lam_default.fd_stmt（`f = lambda x=x: x*2`，与推导式无关）。
- **复现组**：probe_lam_default.fd_stmt / fd_in_comp.<listcomp>、r5_11.lam_default_arg.<listcomp> / lam_with_arg.<listcomp>（4 单元）。
- **状态**：已定位（两端口实测排除 + 装配链圈定），精确丢弃分支待查。

### 封闭面正向记录（对抗未破，8 面）

ListComp 基础（含 index/len 体）、SetComp/DictComp 全形态（含双 iter dict/set）、GenExp 全消费位形（实参/赋值保留/join/嵌套实参）、**无跨 clause 条件的多 for**（二/三层/依赖 iter/dict/set/genexp）、**尾部条件**（单 if/双 if/if-else 体/set 条件）、嵌套推导全形态（矩阵/flatten/dict 内层/推导式实参内推导/三层 cube/genexp 内嵌）、循环体与分支内推导式（for×break/continue、while、if 分支、genexp 守卫 break、嵌套循环）、压缩消费位形（list/tuple/set/sorted/any/all/dict/join）、return+多推导式共存、解包扁平面（`for a, b`/体内星号 display/d.items()）、lambda 晚绑定面（`[lambda: x for x in xs]`）、async 单 clause 面（裸体/简单 if/set/dict）——**wiki「推导式族完备」声明按本轮证据应降格为「浅层封闭：单 clause + 尾部条件 + 扁平 target + 无 walrus + 无 try/finally-return + 非 async 组合」**（与 Round3 B6/B7、Round4 Match 的降格同构：深层与组合面即破）。

---

## §3 负对照结果

| 负对照 | 形态 | 读数 | 判定 |
|---|---|---|---|
| n5_01_control | 无推导式的等价循环改写 ×6：for+append（基础）、set().add（SetComp）、dict 赋值（DictComp）、双层 for+append（多 for）、if+append（条件）、双层 for+内层 append（嵌套） | **7/7 success** | 判据无误报；r5 组 MISMATCH 非误归因于循环本身；B20 崩塌产物（去掉 if 的推导式）对应的显式循环形在真源上 MATCH，证明丢条件是推导式装配错误而非该语义不可表达 |

---

## §4 Round 4 残留复验读数（B12/B13/B16/B17 + r4_04 余量）

| 登记项 | 探针 | 登记读数 | 本轮读数（single，现树） | 判定 |
|---|---|---|---|---|
| B12-R | `test_repros/round4/rv4_12_b12_or_mapping.pyc` | 1/4 | **1/4（25.00%）** | 持平，未变好未变差 |
| B13-R | `test_repros/round4/rv4_13_b13_mid_wildcard.pyc` | 2/4 | **2/4（50.00%）** | 持平 |
| B16-R | `test_repros/round4/rv4_16_b16_loop_nest.pyc` | 2/4 | **2/4（50.00%）** | 持平 |
| B17-R | `test_repros/round4/rv4_17_b17_try_match.pyc` | 2/4 | **2/4（50.00%）** | 持平 |
| r4_04 余量 | `test_repros/round4/r4_04_match_mapping.pyc` | 4/6 | **4/6（66.67%）** | 持平 |

五项全部持平，零漂移。

---

## §5 基线哨兵读数表

| 哨兵 | 登记基线 | 本轮读数（single，现树） | 判定 |
|---|---|---|---|
| site-packages/fly/data/quotation.pyc | 152/153 | **152/153（99.35%）** | 持平 |
| site-packages/IQCommon/strategy/jq_trans_module.pyc | 65/65 | **65/65（100%）** | 持平 |
| site-packages/fly/data/quote.pyc | 84/92 | **84/92（91.30%）** | 持平 |
| site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc | 118/128 | **118/128（92.19%）** | 持平 |
| site-packages/IQEngine/plugins/plugin_system_risk_calculation/__init__.pyc | 41/43（Round4 固化值） | **41/43（95.35%）** | 持平 |

五支哨兵零回退、零改善（只验证，不生成新基线）。

---

## §6 修复工程师交接单（按优先级排序）

| 优先级 | 破口 | 机制一句话 | 最小验收组（转 MATCH 判据 = pyc_verify single success） | 回归哨兵清单 |
|---|---|---|---|---|
| P0 | **B22** | walrus 的 `COPY 1; STORE_DEREF` 被名袋 `_find_comp_target_names`（`comprehension_generator.py:1348`）吸收为幻影迭代目标 → 产物语法非法 compile_error | r5_07（compile_error → ≥11/11 单元可比且全 success；至少 w_body/w_cond compile 通过） | r5_01 13/13、r5_05 19/19、quotation 152/153 不变差；dict-comp walrus 既有正确面（`_split_dict_comp_kv` :1189-1196 守卫）不得回退 |
| P0 | **B25** | lambda 默认值元组在区域管线装配 Lambda dict 链路丢失（MAKE_FUNCTION flags&1→0；两端口已实测排除，精确分支待查：`region_ast_generator.py:2024/:2041-2062/:21838-21845`） | probe_lam_default（2/6 → 6/6：fd_stmt + fd_in_comp）、r5_11（17/19 → 19/19） | r5_11.lam_late_binding / lam_map_pair / lam_call_now / lam_genexp_sort（无默认值 lambda 面）、r5_12 17/17 |
| P1 | **B23** | async 推导式第二装配轴（后随同步 for / elt 含 await）使函数体归约为 `await <iterable>()`，`<listcomp>` 代码对象 MISSING（识别锚点 `comprehension_generator.py:316-325/:1014-1024/:112-139`） | r5_10（9/13 → 13/13：a_async_multi、a_await_body 两函数及其 `<listcomp>` 回归） | r5_10.a_async_for / a_async_cond / a_async_set / a_async_dict（单 clause async 面 4 函数）、r5_03 多 for 面 13/13 |
| P2 | **B21** | for-target 名袋重建不读 UNPACK_SEQUENCE/UNPACK_EX 结构：嵌套元组拍平、星号目标坍缩（`comprehension_generator.py:1348-1377`） | r5_06（11/13 → 13/13） | r5_06.u_tuple_target / u_star_body / u_two_star / u_dict_items（名袋碰巧正确的扁平/体星号面） |
| P2 | **B20** | 多 for 装配每 generator 硬编码 `'ifs': []`（`comprehension_generator.py:1102`）且 ifs 仅挂 `generators[-1]`（:1121/:1156/:1175），跨 clause 过滤静默丢失 | r5_04（12/13 → 13/13） | r5_04.c_single_if / c_double_if / c_ifelse_body / c_cross_for / sc_cond_set（尾部条件面 5 单元）、r5_03 13/13、r5_07 修复后 w_double_if |
| P3 | **B24** | try/finally 装配使 `return <推导式>` 的 RETURN_VALUE 被 POP_TOP 消费、推导式降级 Expr 语句、函数改返回 None（判据候选 `comprehension_generator.py:555-565` R9 POP_TOP 降级路径 × try/finally 区域装配） | r5_09（11/12 → 12/12） | r5_09.t_try_wrap / t_try_in_loop / t_try_finally 其余 5 单元（try/except 面不得回退）、r4_13 try-wrap-match 面（B17 修复后）读数 |
| P3 | **B12-R/B13-R/B16-R/B17-R/r4_04 余量**（Round4 残留，本轮持平） | 见 Round4 REVIEW §6 原交接单 | 读数不得低于本轮登记值 | 本轮 §4 读数即回归基线 |

**修复边界提醒（算法合规）**：所有修复限于区域归约算法同层结构事实判据（识别/归约/生成/发射），禁止白名单式按函数名/文件名打补丁；B21/B22 同根（:1348 名袋），修复须以「读 UNPACK_SEQUENCE/UNPACK_EX/UNPACK_EX 星号位 + 排除 walrus COPY/STORE 副作用」的结构判据一并解决，不得只堵单形；B20 修复须「每 generator 各自提取 ifs」而非仅补 r5_04 单形；docstring 三要素 + C1/C2/C3 条款同步；B23 修复须同时覆盖「async+同步 for 混排」与「elt 含 await」两轴（判据形态嵌套无感）。

**wiki 台账修订建议**：`wiki/concepts/decompile-invariant-completeness.md` :165/:185 两行的「完备」应降格为「浅层封闭（单 clause + 尾部条件 + 扁平 target + 无 walrus + 无 try/finally-return + 非 async 组合）」，并登记 B20–B25 六破口锚点。
