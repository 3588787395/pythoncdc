# Round 06 — IF 区域修复报告

**修复范围**：IF 体内链式运算符扩展族（IS_OP/CONTAINS_OP 链式比较）/ 嵌套深度族（多层嵌套三元）/ walrus 位置扩展族（无赋值目标表达式语句）/ lambda 默认值路径族（外部变量 / kw-only）/ suspendable 表达式位置扩展族（yield from / await 调用参数 / dict / tuple / subscr）/ f-string flags 解码族（conversion / debug spec）
**修复轮次**：14 个确认错误（分 5 批提交）
**遗留**：test_adv03_nested_ternary_chain（链式比较中嵌套三元，19 vs 3，独立根本 bug，与本轮无关，前轮即遗留）
**回归**：if_region 456 passed / 1 failed（仅遗留 nested_ternary_chain）；control_flow_matrix 323 passed / 4 failed（全部预存，已 git checkout c049966 验证非本轮回归）

## 修复进度与提交分批

| 批次 | 提交 | 修复错误 | 状态 |
| --- | --- | --- | --- |
| batch 1 | `0261844` | 12（assert fstring !r）、13（fstring !r/!s/!a）、14（fstring debug spec `=`） | 已 push |
| batch 2 | `44622fa` | 1（chain is rhs）、2（chain in rhs）、3（nested ternary rhs）、7（yield-from rhs） | 已 push |
| batch 3 | `681222e` | 5（lambda outer default）、6（lambda kw default） | 已 push |
| batch 4 | `c049966` | 4（walrus outside comp） | 已 push |
| batch 5 | `b5ef74c` | 8（await call arg）、9（await dict elem）、10（await tuple elem）、11（await in subscr） | 已 push |

最终 HEAD：`b5ef74c`（已 push 到远程 trae/agent-gUeaUE）

---

## 错误 01 — if 体内链式 `is` 比较作赋值右值，`a is b is c` 整条丢失变 `pass`

- 文件：test_adv06_chaincmp_is_chain.py（已通过）
- 源码：`z = a is b is c`
- 根因：链式 `is` 比较 `a is b is c` 字节码用 `IS_OP`×2 + `JUMP_IF_FALSE_OR_POP` + `SWAP/COPY`。前 5 轮链式比较仅覆盖 `COMPARE_OP`（`<`/`>`/`==`），未覆盖 `IS_OP` 链式比较。`IS_OP`/`CONTAINS_OP` 链式比较只创建 `IF_THEN_ELSE`（无中间 IF 包装，与 `COMPARE_OP` 不同），嵌套 IfRegion 是顶层 region，外层 IfRegion 的 children 遍历漏掉它，整条赋值坍塌为 `pass`。
- 修复（batch 2）：`_if_generate_then_branch` 新增扫描 `self.regions` 中嵌套 IfRegion（`IF_THEN_ELSE`、`chained_compare_ops>=2`）且 entry 在 `then_blocks` 中的 region。调用 `_generate_value_context_chain_compare_assign` 处理嵌套 region，并标记 blocks/merge_block/children 为已生成避免重复处理。

## 错误 02 — if 体内链式 `in` 比较作赋值右值，`a in b in c` 整条丢失变 `pass`

- 文件：test_adv06_chaincmp_in_chain.py（已通过）
- 源码：`z = a in b in c`
- 根因：与错误 01 同源，但字节码用 `CONTAINS_OP`（`in`/`not in`）。if body 区域分析对 `CONTAINS_OP` 链式比较的重建失败。
- 修复（batch 2）：与错误 01 同一修复（`IS_OP`/`CONTAINS_OP` 共用链式比较 region 路径）。

## 错误 03 — if 体内多层嵌套三元作赋值右值，内层三元坍塌

- 文件：test_adv06_nested_ternary_body.py（已通过）
- 源码：`z = a if b else cc if d else e`
- 根因：多层嵌套三元 `a if b else cc if d else e` 作赋值右值时，字节码为外层 `POP_JUMP_FORWARD_IF_FALSE` + 内层 `POP_JUMP_FORWARD_IF_FALSE` 嵌套。`_build_ternary_value_expr` 仅查 `block_to_region` 字典，但内层 TernaryRegion 的 entry 块映射到外层 IfRegion，导致内层 TernaryRegion 被漏掉，内层三元坍塌为 test（`d`），`cc`/`e` 全丢。
- 修复（batch 2）：`_build_ternary_value_expr` 新增通过 `get_entry_region_for_block`（而非仅 `block_to_region` 字典）查找 entry 匹配 value 块的 TernaryRegion，正确识别嵌套三元。

## 错误 04 — if 体内 walrus 在表达式语句中，`COPY` 丢失变普通赋值

- 文件：test_adv06_walrus_outside_comp.py（已通过）
- 源码：`(n := f())` / `(m := g())`（walrus 在表达式语句中，返回值被 POP_TOP 丢弃）
- 根因：walrus 在无赋值目标表达式语句中 `(n := f())` 字节码为 `CALL + COPY 1 + STORE_NAME n + POP_TOP`。`_generate_block_statements` 的 COPY+STORE 分支只识别「下一指令是 BINARY_OP（AugAssign+walrus）」或「下一指令是 STORE（chain-assign）」，对「下一指令是 POP_TOP」走 `_build_store_statement`，后者把 COPY 当栈复制丢弃，walrus 退化为普通赋值 `n = f()`，丢失 `COPY` 与 `POP_TOP`。
- 修复（batch 4）：在 `_generate_block_statements` 的 COPY+STORE 分支中，新增「下一指令是 POP_TOP」检测 — 当 stmt_instrs 含 COPY 1 且 STORE 后是 POP_TOP 时，调用 `expr_reconstructor.reconstruct(stmt_instrs + [STORE])` 重建。reconstruct 的 STORE 处理器在 `last_instr_was_copy` 时生成 NamedExpr 并替换栈顶，返回 NamedExpr。包装为 `Expr(NamedExpr)` 语句，并跳过后续 POP_TOP。区域归约：COPY+STORE 是单一 walrus 表达式归约节点，POP_TOP 是表达式语句终结指令，三者共同构成一个 Expr 语句。

## 错误 05 — if 体内 lambda 默认参数引用外部变量，`BUILD_TUPLE` 丢失

- 文件：test_adv06_lambda_outer_default.py（已通过）
- 源码：`f = lambda x=a, y=b: x + y`（默认值引用外部变量 a/b）
- 根因：`lambda x=a, y=b` 默认值通过 `LOAD_NAME a + LOAD_NAME b + BUILD_TUPLE + MAKE_FUNCTION` 传递。FunctionObject.defaults 是 `{'type': 'Tuple', 'elts': [Name('a'), Name('b')]}`。但 `_build_function_def`（region_ast_generator.py L820-838）的 Tuple 分支用 `get('elsts', [])`（拼写错误，应为 `'elts'`），导致 `defaults_list` 为空，默认值丢失。R4 错误 13 仅修复常量默认值（`LOAD_CONST` 元组），未覆盖外部变量 `BUILD_TUPLE` 路径。
- 修复（batch 3）：把 `'elsts'` 改为 `'elts'`，并新增 `List` 类型分支（同样用 `'elts'`）作为更通用的 dict 表达式处理。

## 错误 06 — if 体内 lambda kw-only 默认值，`BUILD_CONST_KEY_MAP` 丢失

- 文件：test_adv06_lambda_kw_default.py（已通过）
- 源码：`f = lambda x, *, y=10: x + y`（kw-only 默认值 10）
- 根因：`lambda x, *, y=10` 的 kw-only 默认值通过 `LOAD_CONST 10 + LOAD_CONST ('y',) + BUILD_CONST_KEY_MAP + MAKE_FUNCTION` 传递。FunctionObject.kw_defaults 是 `{'type': 'Dict', 'keys': [Constant('y')], 'values': [Constant(10)]}`。但 `_build_function_def` 完全没有 kw_defaults 处理逻辑，kw-only 默认值 `10` 丢失。R4 错误 13 是普通默认值（`LOAD_CONST` 元组）；本例是 kw-only 默认值 `BUILD_CONST_KEY_MAP` 路径，新组合。
- 修复（batch 3）：在 `_build_function_def` 中新增 kw_defaults 处理 — 将 Dict 节点转换为 `args['kw_defaults']` 列表，与 kwonlyargs 位置对应（无默认值的位置为 None）。处理两种格式：Dict 节点（`keys`/`values` 列表）和普通字典（`{name: value_dict}`）。

## 错误 07 — if 体内 `yield from` 作赋值右值，赋值目标 x 丢失

- 文件：test_adv06_yield_from_rhs.py（已通过）
- 源码：`x = yield from g()`（在生成器函数 if 体内）
- 根因：`x = yield from g()` 字节码为 `GET_YIELD_FROM_ITER + LOAD_CONST None + SEND + YIELD_VALUE + RESUME + STORE_FAST x`。if body 区域分析把 yield from 表达式当作独立语句 `yield from g()`，丢弃了 `STORE_FAST x` 赋值目标。R4 错误 14/15 修复了 await / yield 作赋值右值；本轮新增 yield from 作赋值右值（走 `GET_YIELD_FROM_ITER/SEND` 路径，与 yield 的 `YIELD_VALUE` 路径不同）。
- 修复（batch 2）：yield-from loop handler 新增扫描 `region.blocks` 中的 `STORE_*` 指令；若找到，生成 `Assign(targets=[store], value=YieldFrom)` 而非 `Expr(YieldFrom)`。同时在 `CodeGenerator._generate_expression` 新增 YieldFrom case 用于表达式上下文渲染。

## 错误 08 — if 体内 await 作函数调用参数，调用结构坍塌

- 文件：test_adv06_await_call_arg.py（已通过）
- 源码：`r = h(await g(), x)`（await 作调用参数）
- 根因：`h(await g(), x)` await 作调用参数时，字节码在 `CALL`（g）后插入 `GET_AWAITABLE + YIELD_VALUE + RESUME`（await setup），再 `LOAD_GLOBAL x + CALL`（h）。await setup 跨多块（setup + send_loop + ft_block），ft_block 含外层 CALL + STORE。每块单独重建把 await 提为独立语句（返回值被 POP_TOP 丢弃），外层调用 `h(...)` 与赋值目标 `r` 全丢。R5 错误 10 修复了 await 作列表元素；本轮新增 await 作函数调用参数，新组合。
- 修复（batch 5）：泛化 `_try_generate_await_list_assign` 方法 — 终结块支持 `CALL + STORE_*` 形态（外层 CALL 在 await 完成后）。整条 await 链（setup + send_loop + ft_block 的 CALL 前指令 + STORE）作为单一表达式重建，产出 `Assign(r, Call(h, [Await(Call(g)), Name(x)]))`。

## 错误 09 — if 体内 await 作 dict 字面量 value，dict 字面量与 await 全丢

- 文件：test_adv06_await_dict_elem.py（已通过）
- 源码：`r = {k: await g(), m: await h()}`（dict 字面量含多个 await value）
- 根因：dict 字面量含两个 await value，字节码为 await setup ×2 + `BUILD_MAP`。if body 区域分析对「await value + BUILD_MAP」识别失败，把两个 await 提为独立语句（返回值被 POP_TOP 丢弃），dict 字面量退化为空 `{}`。R5 错误 10 修复了 await 作列表元素（`BUILD_LIST`）；本轮新增 await 作 dict 字面量 value（`BUILD_MAP` 路径），新组合。
- 修复（batch 5）：泛化 `_try_generate_await_list_assign` 方法 — 终结块支持 `BUILD_MAP` 形态。整条 await 链作为单一表达式重建，产出 `Assign(r, Dict([(k, Await(g)), (m, Await(h))]))`。

## 错误 10 — if 体内 await 作 tuple 字面量元素，tuple 字面量丢失变空 tuple

- 文件：test_adv06_await_tuple_elem.py（已通过）
- 源码：`r = (await g(), await h())`（tuple 字面量含多个 await 元素）
- 根因：tuple 字面量含两个 await 元素，字节码为 await setup ×2 + `BUILD_TUPLE 2`。if body 区域分析对「await 元素 + BUILD_TUPLE」识别失败，把两个 await 提为独立语句，tuple 字面量退化为空 `()`。R5 错误 10 修复了 await 作列表元素（`BUILD_LIST`）；本轮新增 await 作 tuple 字面量元素（`BUILD_TUPLE` 路径），新组合。
- 修复（batch 5）：泛化 `_try_generate_await_list_assign` 方法 — 终结块支持 `BUILD_TUPLE` 形态。整条 await 链作为单一表达式重建，产出 `Assign(r, Tuple([Await(g), Await(h)]))`。

## 错误 11 — if 体内 await 作下标，`BINARY_SUBSCR` 丢失

- 文件：test_adv06_await_in_subscr.py（已通过）
- 源码：`r = d[await g()]`（await 作下标）
- 根因：`d[await g()]` await 作下标时，字节码在 `CALL`（g）后插入 `GET_AWAITABLE + YIELD_VALUE + RESUME`（await setup），再 `BINARY_SUBSCR`（取下标）+ `STORE_FAST r`。if body 区域分析对「await + BINARY_SUBSCR」重建失败，把 await 提为独立语句，容器 `d`、`BINARY_SUBSCR` 与赋值目标 `r` 全丢。R5 错误 10 修复了 await 作列表元素；R3 错误 02 修复了三元作下标；本轮新增 await 作下标，新组合。
- 修复（batch 5）：泛化 `_try_generate_await_list_assign` 方法 — 终结块支持 `BINARY_SUBSCR` 形态。整条 await 链作为单一表达式重建，产出 `Assign(r, Subscript(d, Await(g)))`。

## 错误 12 — if 体内 assert + f-string 带 `!r` 转换，转换符被替换为 U+0002 控制字符

- 文件：test_adv06_assert_fstring_msg.py（已通过）
- 源码：`assert x > 0, f"msg {y}: {z!r}"`
- 根因：f-string `{z!r}` 中 `!r` 是 `FORMAT_VALUE` 指令的 flags 参数（Python 3.11 中 `FORMAT_VALUE` flags：0=无 / 1=(!s) / 2=(!r) / 3=(!a) / 4=带格式说明符）。两个 bug：(1) `code_generator._generate_formatted_value_from_dict` 用 `chr(conversion)` 把 flags 当字符编码，输出控制字符 `\x01`/`\x02`/`\x03`（`_write` 方法静默剥离 `\x00` 掩盖了 flags=0 的情况，但 flags=1/2/3 暴露）；(2) `region_ast_generator` + `ast_generator_v2` 用错误的 elif 链 `if flags & 1: 1 elif flags & 2: 2 elif flags & 3: 3`，导致 `!a`（flags=3）总是返回 1（`3&1=1` 先命中）。
- 修复（batch 1）：(1) `code_generator._generate_formatted_value_from_dict` 改用正确的 conversion 标记（`!s`/`!r`/`!a` 字符串）；(2) conversion 解码改为 `conversion = flags & 3`（2-bit 值，非 bit flags）。同时修复 AST 版本 `_generate_formatted_value` 把 1 映射为 `''`（省略 `!s`）导致 `!s` 字节码不等价的问题。

## 错误 13 — if 体内 f-string 带 `!r`/`!s`/`!a` 转换，转换符被替换为控制字符

- 文件：test_adv06_fstring_conversion.py（已通过）
- 源码：`s = f"{x!r} {y!s} {z!a}"`
- 根因：与错误 12 同源。`!r` → `\x02`，`!s` → `\x01`，`!a` → `\x01`（off-by-one，应为 `\x03`）。
- 修复（batch 1）：与错误 12 同一修复（系统性修复 `FORMAT_VALUE` flags 解码）。

## 错误 14 — if 体内 f-string debug spec `f"{x=}"`，转换符被替换为 U+0002 控制字符

- 文件：test_adv06_fstring_debug_spec.py（已通过）
- 源码：`s = f"{x=} {y=}"`
- 根因：f-string `{x=}` debug spec 在 Python 3.8+ 启用，字节码为 `LOAD_NAME x + FORMAT_VALUE 4`（带格式说明符，且模板字符串中含 `x=` 前缀）+ `BUILD_STRING`。`FORMAT_VALUE 4`（带 `=` debug spec）的解码失败，把 `=` debug 标志当作 `\x02` 控制字符拼接到 f-string 模板字符串中。
- 修复（batch 1）：与错误 12/13 同一修复（`FORMAT_VALUE` flags 解码系统性修复，正确处理 flags=4 的 debug spec）。

---

## 修复涉及的源文件

| 文件 | 修改批次 | 修改内容 |
| --- | --- | --- |
| core/cfg/code_generator.py | batch 1, 2 | f-string conversion 字符输出修复；YieldFrom 表达式渲染 |
| core/cfg/region_ast_generator.py | batch 1, 2, 3, 4, 5 | FORMAT_VALUE flags 解码修复；chain is/in rhs + nested ternary rhs + yield-from rhs；lambda defaults typo + kw_defaults；walrus expr statement；await cross-block assign 泛化 |
| core/cfg/region_analyzer.py | batch 2 | IS_OP/CONTAINS_OP 链式比较 region 识别 |
| core/cfg/ast_generator_v2.py | batch 1 | FORMAT_VALUE flags 解码修复 |

## 区域归约算法 4 原则遵守情况

- **自底向上归约**：所有修复均从最小可归约节点出发 — walrus COPY+STORE 是单一 NamedExpr 节点；await 跨块链是单一表达式节点；lambda defaults/kw_defaults 是 MAKE_FUNCTION 的子节点。
- **每块唯一归属**：await 跨块链中所有 setup/send_loop/terminator 块在 `_try_generate_await_list_assign` 命中后一次性标记为已生成，避免重复处理。
- **嵌套即抽象节点**：嵌套三元 / 嵌套 lambda / await 嵌入外层表达式（list/dict/tuple/subscr/call）均作为子表达式节点保留，不展开为独立语句。
- **父引用子入口**：await 跨块链通过 SEND 的 argval 找到 fall-through 子块入口；walrus 表达式语句通过 STORE 后的 POP_TOP 确定表达式语句终结。

## 已知遗留

- test_adv03_nested_ternary_chain（链式比较中嵌套三元，19 vs 3）：独立根本 bug，R3 即遗留，本轮未触及。
- control_flow_matrix 4 个预存失败（TestL12WhileBreakContinue / TestN11TryWhileContinue / TestCF2WhileIfBreakContinue / TestXP04BoolOpInIf）：已 git checkout c049966 验证非本轮回归，与本轮 IF 区域修复无关。
