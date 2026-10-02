# Round 5 复核（对抗性复审：B20–B25 两批修复，Task 5.3）

- 复核人：评审工程师（Round 5 复核批次，独立复核）
- 日期：2026-10-02
- 复核对象：批次一 `7e09e36d`（B20/B21/B22）、批次二 `45864cc5`（B23/B24/B25）
- 唯一判据：`python scripts/pyc_verify.py single <pyc>`（逐 code object 判 Equal，全 Equal 才 success）
- 硬约束遵守：未修改任何 `core/`、`scripts/`、`pycdc.py`、既有 `*OK.py`、`site-packages/`、`.trae/specs/` 既有内容；本次仅新增本文件与 `test_repros/round5/rv5_20..rv5_26` 探针（OK 产物全部由 `pycdc.py -o` 生成）；未 git commit；全部命令 ≤300 s；复核用修复前树经临时 worktree（`D:\Temp\r5_tree` @ eec7041a）复测后已删除。
- 方法说明：变体失败归属鉴别采用「修复前树同源复测」——将失败变体 pyc 置于 eec7041a worktree 用该树的 pycdc/判据复测，签名一致 = 修复前已存在（非本批引入）；签名消失 = 修复引入。

---

## §1 读数复跑全表（21 支，实测 vs FIX.md 自测读数）

### 最小验收组（7 支，转 MATCH 验收面）

| 哨兵 | FIX.md 声称 | 本轮实测 | 判定 |
|---|---|---|---|
| r5_04_comp_cond.pyc | 13/13 | **13/13 success 100.00%** | 一致 |
| r5_06_comp_unpack.pyc | 13/13 | **13/13 success 100.00%** | 一致 |
| r5_07_comp_walrus.pyc | 11/11 | **11/11 success 100.00%** | 一致 |
| probe_lam_default.pyc | 6/6 | **6/6 success 100.00%** | 一致 |
| r5_11_comp_lambda.pyc | 19/19 | **19/19 success 100.00%** | 一致 |
| r5_10_comp_async.pyc | 13/13 | **13/13 success 100.00%** | 一致 |
| r5_09_comp_try.pyc | 12/12 | **12/12 success 100.00%** | 一致 |

### 回归哨兵（8 支）

| 哨兵 | FIX.md 声称 | 本轮实测 | 判定 |
|---|---|---|---|
| r5_01_comp_basic.pyc | 13/13 | **13/13 success** | 一致 |
| r5_02_genexp.pyc | 12/12 | **12/12 success** | 一致 |
| r5_03_comp_multifor.pyc | 13/13 | **13/13 success** | 一致 |
| r5_05_comp_nested.pyc | 19/19 | **19/19 success** | 一致 |
| r5_08_comp_in_loop.pyc | 14/14 | **14/14 success** | 一致 |
| r5_12_comp_compress.pyc | 17/17 | **17/17 success** | 一致 |
| r5_13_comp_return.pyc | 18/18 | **18/18 success** | 一致 |
| n5_01_control.pyc | 7/7 | **7/7 success** | 一致 |

### site-packages 抽验（3 支）

| 哨兵 | FIX.md 声称 | 本轮实测 | 判定 |
|---|---|---|---|
| fly/data/quotation.pyc | 152/153 | **152/153（99.35%）** | 一致 |
| IQCommon/strategy/jq_trans_module.pyc | 65/65 | **65/65（100%）** | 一致 |
| IQEngine/plugins/plugin_system_risk_calculation/__init__.pyc | 41/43 | **41/43（95.35%）** | 一致 |

### 前轮抽验（3 支）

| 哨兵 | 登记值 | 本轮实测 | 判定 |
|---|---|---|---|
| round4/r4_04_match_mapping.pyc | 4/6 持平 | **4/6（66.67%）** | 一致 |
| round3/r3_34_b10r_innerforelse_break.pyc | 1/2 持平 | **1/2（50.00%）** | 一致 |
| round2/r2_01_try_multi_handler.pyc | 3/3 持平 | **3/3 success** | 一致 |

**§1 结论：21/21 支读数与 FIX.md 逐一相符，虚报数为 0。**

---

## §2 变体攻击全表（6 探针文件 / 61 单元，57 MATCH / 4 失败——4 失败经修复前树复测证实均为修复前已存在，非本批引入）

探针文件：`test_repros/round5/rv5_20_b20_var.py` … `rv5_26_diag.py`（.pyc 由 py_compile 3.11.7 生成，OK 产物由 `pycdc.py -o` 生成）。失败归属鉴别基线：eec7041a worktree 复测（`D:\Temp\r5_pre`，已删）。

| 探针 | 攻击变体 | 读数 | 逐变体判定 |
|---|---|---|---|
| rv5_20_b20_var | B20：4 clause 每 clause 2 过滤（c4_double_filters）；clause 过滤含 walrus（c_walrus_filters）；解包 target + 非最内层过滤（c_unpack_noninner_filter）；3 clause 解包+过滤 walrus+尾过滤（c3_walrus_unpack_mix） | **9/9 success** | 全过 ✅ |
| rv5_21_b21_var | B21：3 层嵌套元组+星号混排 `(a,(b,(c,d))),*rest`；单元素元组深层嵌套 `(a,(b,))`/`((b,),)`；星号居中 `a,*rest,c`；嵌套内星号 `(p,(q,*r))` | **11/11 success** | 全过 ✅ |
| rv5_22_b22_var | B22：体内 2 walrus；体 walrus + if 过滤 walrus 同推导式；GenExp 内 walrus；DictComp key/value 双 walrus | **10/10 success** | 全过 ✅ |
| rv5_23_b23_var | B23：async+sync+async 三 clause 混排（✅ MATCH）；async dict comp 双 clause（✅ MATCH）；await set comp（✅ MATCH）；**async GenExp 括号形式作调用实参（❌ 8/10）** | **8/10 failure** | a_genexp：产物 `return None(ait())`，`<genexpr>` Missing bytecode。eec7041a 复测同签名失败（修复前 4/10，同两形态 + a3_mixed/a_dict_comp）→ **修复前已存在，登记 B26**（同时证实 a3_mixed/a_dict_comp 系修复后转好，零回归） |
| rv5_24_b24_var | B24：try/except（无 finally）包 return [comp]（✅）；try/finally 包 return {dict comp}（✅）；try/finally 包 return {set comp}（✅）；**嵌套 try 包 return comp（❌ 8/9）** | **8/9 failure** | t_nested_try：内层 `return [x for x in xs]` 降级为裸表达式。eec7041a 复测同签名失败（修复前 6/9，t_finally_dict/t_finally_set 亦失败）→ **修复前已存在，登记 B27**（t_finally_dict/set 系修复后转好，零回归） |
| rv5_25_b25_var | B25：函数级双默认+kwonly+vararg 全形态 `lambda a,b=1,c=2,*args,d,e=5,**kw`（✅ MATCH）；推导式内 lambda *args/**kw 带默认（✅ MATCH）；函数级 kwonly 默认（✅ MATCH）；**推导式内纯 vararg/kwarg lambda `lambda *args,**kw`（❌ 11/12）** | **11/12 failure** | lam_in_comp_starkw：产物 `lambda : (args, kw)`，形参声明整体丢失。eec7041a 复测同签名失败（修复前 fd_full/lam_in_comp_full/lam_kwonly_stmt 亦失败）→ **修复前已存在，登记 B28**（fd_full 等 3 形态系修复后转好，零回归） |
| rv5_26_diag（鉴别诊断） | 函数级纯 vararg/kwarg lambda（diag_vararg_fn ❌ 4/6）；**无推导式的嵌套 try return 普通值**（diag_nested_try_plain ❌）；同步 GenExp 作实参对照组（diag_sync_genexp_arg ✅ `sum((x for x in xs))`） | **4/6 failure** | 证实 B28 在函数级同样存在（旧扁平路径对 argcount=0 的 vararg/kwarg 形参无渲染路径）；证实 **B27 与推导式无关**——普通值 return 在嵌套 try 下同样被剥除（try 区域装配子系统既有缺口，与 FIX.md 已如实登记的「except handler 内 return 值」同族）；同步 GenExp 对照 MATCH，B26 收窄为 async 协议 × GenExp 实参位形 |

### 新破口登记（B26–B28，均为修复前已存在、经变体攻击新暴露，不要求本轮封闭）

| 编号 | 破口 | 锚点 | 机制一句话 | 归属建议 |
|---|---|---|---|---|
| **B26** | async GenExp（括号形式）作调用实参整体坍缩 `sum(x async for x in ait)` → `return None(ait())`，`<genexpr>` Missing bytecode | `rv5_23_b23_var.a_genexp`（`<module>.a_genexp` Different bytecode + `.a_genexp.<genexpr>` Missing bytecode） | 调用实参位的 GenExpObject 认领路径不识别 async 取值协议（GET_AITER/GET_ANEXT/SEND），callable 重建失败落 None | 推导式族 × 调用实参窗，后续轮与 B23 同族扩展 |
| **B27** | 嵌套 try（内 try/finally 套外 try/finally）包 `return <值>`（推导式与普通值同杀）：内层 return 剥除、值降级 Expr | `rv5_24_b24_var.t_nested_try`、`rv5_26_diag.diag_nested_try_plain`（后者纯 `return xs` 亦复现） | 嵌套异常表布局下 return 值穿越两层清理段，`_find_returns_pending_value_successor` 的单层「前向正常后继」结构判据不命中，回退 Expr 降级 | try 区域装配子系统（W11/SW11 族），与 FIX.md 已登记的「except handler 内 return 值带 finally」同族 |
| **B28** | 纯 vararg/kwarg lambda（无默认值）`lambda *args, **kw:` → `lambda :`，形参声明整体丢失（函数级与推导式内双杀） | `rv5_25_b25_var.lam_in_comp_starkw.<listcomp>.<lambda>`、`rv5_26_diag.diag_vararg_fn.<lambda>` | B25 修复的 [C3] 守卫仅当 defaults/kw_defaults 非空才走 arguments dict 重建；argcount=0 且 flags 0x04/0x08 位形落旧扁平路径（co_varnames[:co_argcount] 为空），`*args, **kw` 无渲染路径 | B25 同族补全（args dict 重建守卫应扩为「defaults/kw_defaults 非空 ∨ vararg/kwarg 位存在」） |

**§2 结论：B20/B21/B22 新守卫在 9+11+10 单元变体攻击下无新破口；B23/B24/B25 新守卫各自主形态全过，但攻击揭出 3 个修复前已存在的相邻缺口（B26/B27/B28），每支均有 eec7041a 同签名基线 + 鉴别诊断证据，且同探针内 6 个相邻形态系修复后转好——零回归。**

---

## §3 逐 hunk 审查（9 项判据，按 commit 分组）

### 批次一 7e09e36d（2 core 文件 / 8 hunk）

| # | 文件:位置 | 内容 | 白名单 | 魔法阈值 | 跨层/self状态 | 少发射换全绿 | docstring 三要素+C 条款 | 判定 |
|---|---|---|---|---|---|---|---|---|
| 1 | comprehension_generator `_parse_multi_for_comprehension` docstring（现 :1253-1264 域） | [Round5-B20] 识别/归约/AST 映射 + [C1][C3] | 无 | 无 | 无 | — | ✓ 与行为一致（窗=本流 FOR_ITER 偏移+存储序列末端） | 通过 |
| 2 | 同上 装配循环（`_next_iter_start`/每 clause `ifs`/`'ifs': list(ifs)`） | clause k 过滤窗 `[seq_end-1, fi_{k+1})` 复用 `_extract_comp_ifs`；iter 窗改 `_iter_start` 不回扫 STORE；最内层置空占位防双重归属 | 无 | 无（窗口由 FOR_ITER 偏移与 seq_end 决定） | 无（全局部变量） | 否（ifs 实际挂入，r5_04 产物含 if） | ✓ 行内注记与代码一致 | 通过 |
| 3 | comprehension_generator `_find_comp_target_names`（现 :1623） | walrus 守卫：`COPY 1 ∧ 后继∈STORE_*` 收集进排除集 | 无（`.0` 为 comp 迭代器参数惯例名，非用户标识符） | 无 | 无 | — | ✓ [C3] 守卫注记一致 | 通过 |
| 4 | comprehension_generator `_parse_target_store_sequence`（现 :1658） | UNPACK_SEQUENCE/UNPACK_EX 栈结构递归下降（EX 低 8 位星号前/高 8 位星号后） | 无 | 无（0xFF 位掩码=UNPACK_EX 协议结构） | 无 | — | ✓ 三要素 + [C1][C2] 齐全 | 通过 |
| 5 | comprehension_generator `_build_comprehension_target`（现 :1720） | FOR_ITER 后结构解析优先，名袋仅异步回退 | 无 | 无 | 无 | — | ✓ [C1][C2][C3] 齐全 | 通过 |
| 6 | code_generator `_generate_for_target`（现 :1873）/`_generate_for_target_from_dict`（现 :1908） | 单元素 Tuple 补尾随逗号（`(b,)`/`b,`），递归对 1 元素子 Tuple 已返回 `b,` 仅补括号 | 无 | 无 | 无 | — | ✓ [Round5-B21] 注记（识别=elt 数/归约=按结构补齐/映射=`(x,)`↔UNPACK_SEQUENCE 1）与行为一致 | 通过 |
| 7 | code_generator `_generate_comprehensions_from_dict`（现 :5096 域） | 目标渲染统一委托 `_generate_for_target_from_dict` | 无 | 无 | 无 | — | ✓ 三要素 + [C1][C2] 注记 | 通过 |
| 8 | code_generator `_generate_comprehensions`（现 :5469 域） | dict/ASTTuple 两分支同改委托 | 无 | 无 | 无 | — | ✓ 注记同引 | 通过 |

### 批次二 45864cc5（4 core 文件 / 12 hunk）

| # | 文件:位置 | 内容 | 白名单 | 魔法阈值 | 跨层/self状态 | 少发射换全绿 | docstring 三要素+C 条款 | 判定 |
|---|---|---|---|---|---|---|---|---|
| 9 | comprehension_generator :288-312 闭包过滤局部状态机 | closure 系 op 开启、紧随 BUILD_TUPLE 闭合 | 无 | 无 | 无（局部 `_in_closure_seq`） | 否（只消除闭包元组误留；用户 BUILD_TUPLE 前驱为 LOAD_*/CALL 不受影响） | ✓ 三要素式注记 + [C3] 终止符守卫宽度不变 | 通过 |
| 10 | comprehension_generator :563-580 R9 收窄 | `any(POP_TOP)` → `instrs[wrapper_end].opname == 'POP_TOP'`（紧邻才弹推导式值） | 无 | 无 | 无 | 否（R9 原形仍命中，未关闭；r5_09 其余单元与 r2_01/r2_03 全过） | ✓ 栈顶来源/前驱形态注记一致 | 通过 |
| 11 | comprehension_generator :644-668 B24 认领分支 | 末 clause + 末条非跳转 + 后继判据命中 → `Return(comp_value)`；不标记后继已生成 | 无 | 无 | 无 | **否（重点核查）**：后继块仍由 try 装配认领 finalbody——r5_09 12/12 产物含 `finally: log.append(len(xs))`；未吞任何语句 | ✓ [原则 3] 注记一致 | 通过 |
| 12 | comprehension_generator :685-797 `_find_returns_pending_value_successor` | 三重判据：(a) 非帧头（PUSH_EXC_INFO/CHECK_EXC_MATCH/CHECK_EG_MATCH）；(b) 末条 RETURN 前线性无跳转；(c) `dis.stack_effect` 栈深模拟全程无下溢且末条前恰 0；簿记（POP_EXCEPT/COPY/SWAP/RERAISE）按 0、有界穿越 ≤4 跳 | 无 | 无（栈深 0 / ≤4 有结构语义） | 无（只读本块+后继块指令流） | 否：双向反例由判据排除（`LOAD_CONST None; RETURN` 末条前栈深 1；`cleanup; POP_TOP; LOAD y; RETURN` 模拟下溢）；簿记按 0 的近似方向偏保守（COPY 按 0 提前下溢→更严），POP_EXCEPT 按 0 使 handler 内 return（SWAP 2+POP_EXCEPT 留值）末条前栈深 1→不命中→交回 Expr 原路径，与 FIX.md「handler 内 return 未落地」登记一致，无误认领 | ✓ 三要素 + [C1][C2][C3] 齐全一致 | 通过 |
| 13 | comprehension_generator :1066-1081 多 clause 入口 | clause 头 = FOR_ITER ∪ GET_ANEXT 协议块，总数 >1 走统一路径 | 无 | 无 | 无 | — | ✓ 注记一致 | 通过 |
| 14 | comprehension_generator :1192-1240 `_find_async_clause_heads` | GET_ANEXT; LOAD_CONST None; SEND; 协议尾（YIELD_VALUE/RESUME/JUMP_BACKWARD_NO_INTERRUPT/CLEANUP_THROW/END_ASYNC_FOR）后首条 STORE/UNPACK 为目标序列起点 | 无（LOAD_CONST None=协议常量位） | 无 | 无 | — | ✓ 三要素 + [C1][C2][C3]（头判据失败即不认领） | 通过 |
| 15 | comprehension_generator :1247-1393 统一 clause 装配 | async/同步头合并排序；target 各自从头后结构解析；过滤窗 `[seq_end, 下一头)`；锚点 GET_AITER/GET_ITER 按头种类；`is_async` 沿 clause 归位 | 无 | 无 | 无 | — | ✓ [Round5-B23] docstring 段 + 行内注记一致；批次一 B20 判据（窗语义/互斥守卫）未被更改仅被推广 | 通过 |
| 16 | ast_converter :996-1040 FunctionObject 分支 | `<lambda>` 且宿主带 defaults/kw_defaults → `_build_lambda_args_dict_from_function_obj` → 委托 `_convert_lambda_expr` | 无 | 无（0x04/0x08=CO_VARARGS/CO_VARKEYWORDS flags 位） | 无 | 否（[C3] 无默认值显式守卫走旧路径） | ✓ 三要素 + [C1][C2][C3] | 通过 |
| 17 | ast_converter :1630-1673 `_convert_lambda_expr` | args 为 dict 且 defaults/kw_defaults 非空 → `_args_dict` 挂节点 | 无 | 无 | 无 | — | ✓ [C3] 守卫注记一致 | 通过 |
| 18 | ast_converter :1675-1748 `_build_lambda_args_dict_from_function_obj` | co_varnames 分段布局 + flags 位 → arguments dict；Constant 包装原始 tuple defaults 按元素展开 | 无 | 无 | 无 | — | ✓ 三要素 + [C1][C2][C3]（无默认位显式置 None） | 通过 |
| 19 | code_generator :5439-5474 `_generate_lambda_expr` | 带 `_args_dict` → 委托 `_generate_arguments_dict`（与 FunctionDef 同发射器）；否则旧扁平路径 | 无 | 无 | 无 | 否（[C3] 未携带走旧路径，行为不变） | ✓ 三要素 + [C1][C2][C3] 注记 | 通过 |
| 20 | ast_generator_v2 :1353-1372 CALL PUSH_NULL 补消费 | func 弹出后栈顶为 `'PUSH_NULL'` 类型伪节点则补弹 | 无（PUSH_NULL 伪节点仅由 PUSH_NULL 操作码处理器创建，:436-440，永不承载用户值——grep 实证 40 处 'PUSH_NULL' 全为伪节点判定/创建） | 无 | 无 | **否（重点核查）**：仅弹伪节点，真值节点不动；方法调用形（无 PUSH_NULL）不受影响 | ✓ 三要素 + [C3] 仅认伪节点 | 通过 |

**§3 结论：20 hunk 全过，零打回。** 白名单零命中；魔法阈值零命中（`.0` 为 comp 迭代器参数惯例、0xFF 为 UNPACK_EX 位协议、0x04/0x08 为 co_flags 位、栈深 0 与穿越 ≤4 有结构语义）；无跨层读取、无新增跨方法 self 可变状态（闭包过滤 `_in_closure_seq`、`_next_iter_start` 等全为局部变量）；B24/B23 两处「吞真值」重点核查均为否（见 #11/#20）；FIX.md 声称的每个 docstring 落点均在代码中真实存在且与行为一致。

---

## §4 Round4 残留核对

| 登记项 | 探针 | Round4 登记值 | 本轮实测 | 判定 |
|---|---|---|---|---|
| B12-R | test_repros/round4/rv4_12_b12_or_mapping.pyc | 1/4 | **1/4（25.00%）** | 持平 |
| B16-R | test_repros/round4/rv4_16_b16_loop_nest.pyc | 2/4 | **2/4（50.00%）** | 持平 |

两项持平，零漂移（与 FIX.md「未触碰 match/boolop 族面」声明一致）。

## §5 插桩/BOM 检查

| 项 | 方法 | 结果 | 判定 |
|---|---|---|---|
| 插桩残留（批次一） | `git show 7e09e36d` 增行 grep `print(\|DEBUG\|FIXME\|XXX\|TODO\|pdb\|breakpoint` | 唯一命中为 FIX.md 自述行（「grep … 零命中」文字本身），代码行零命中 | 通过 |
| 插桩残留（批次二） | `git show 45864cc5` 同法 | 同上，代码行零命中 | 通过 |
| BOM（G0） | `region_ast_generator.py` 首 4 字节 | `efbbbf22`（efbbbf 在位） | 通过 |
| 其余被改 core 文件首字节 | comprehension_generator/code_generator/ast_converter/ast_generator_v2/pattern_parser | `66726f6d`("from") / `2222220d`(""")×3 / `2222220a`——均无 BOM，与各文件历史形态一致（pattern_parser 无 BOM 与 Round4 REVIEW2 记录一致） | 通过 |
| 判据引用一致性 | 批次二 diff（即两 commit 同文件差集）逐函数核对 | `_find_comp_target_names`/`_parse_target_store_sequence`/`_build_comprehension_target`（批次一 B21/B22 判据）与 code_generator for-target 两 hunk（批次一 B21 发射判据）在批次二 diff 中零改动；批次二仅将 B20 窗语义推广至 async 头（`_parse_multi_for_comprehension` 内），识别/互斥守卫原样保留 | 通过 |

## §6 终判与交接单

### 终判：**放行**（两批修复 20/20 hunk 合规、21/21 读数复跑无虚报、6 支验收面真实转 MATCH、零回归；3 个变体攻击新暴露均为修复前已存在缺口，如实登记不构成本轮打回事由）

- 打回清单：**空**。
- 新破口登记：**B26 / B27 / B28**（全部经 eec7041a 修复前树同签名基线证实为既有缺口非回归；细节见 §2 表）。

### 后续轮交接单（按优先级）

| 优先级 | 破口 | 最小验收组 | 回归哨兵 |
|---|---|---|---|
| P1 | **B27** 嵌套 try 包 `return <值>`（普通值即杀，与推导式无关）：`_find_returns_pending_value_successor` 单层后继判据在双层异常表布局不命中 → return 剥除 | rv5_24.t_nested_try（12 单元全可比全 MATCH）、rv5_26_diag.diag_nested_try_plain | r5_09 12/12、r2_01 3/3、r2_03 3/3、rv5_24 其余 8 单元 |
| P1 | **B28** 纯 vararg/kwarg lambda 形参声明丢失（函数级+推导式内）：B25 [C3] 守卫应扩为「defaults/kw_defaults 非空 ∨ CO_VARARGS/CO_VARKEYWORDS 位存在」 | rv5_25.lam_in_comp_starkw（12/12）、rv5_26_diag.diag_vararg_fn | r5_11 19/19、probe_lam_default 6/6、rv5_25 其余 11 单元 |
| P2 | **B26** async GenExp 括号形式作调用实参坍缩 `None(ait())`：调用实参窗的 GenExpObject 认领不识别 async 协议 | rv5_23.a_genexp（10/10） | r5_10 13/13、rv5_23 其余 8 单元、r5_02 12/12 |
| P2 | B24 已登记残留（FIX.md 如实申报）：except handler 内 `return <值>` 带 finally（handler 装配子系统辖域） | 保持登记 | r5_09 12/12、r2_01 3/3 |
| P3 | Round4 残留 rv4_12/rv4_13/rv4_16/rv4_17 + r4_04 余 2（本轮 rv4_12=1/4、rv4_16=2/4 复验持平） | 见 Round4 交接单 | 本轮 §4 读数即基线 |

### wiki 台账建议

`wiki/concepts/decompile-invariant-completeness.md` 推导式族条目：登记 B26/B27/B28 锚点（B27 属 try 装配族、B28 属 lambda 发射族、B26 属推导式×调用实参组合面）；「推导式族」由 Round5 评审批次的「浅层封闭」升格为「浅层封闭 + 多 clause 过滤/解包 target/walrus/async 混排/try-finally 单层 return/lambda 默认值已封闭（B20–B25）」。
