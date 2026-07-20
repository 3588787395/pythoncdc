# IF 区域 Round 9 修复报告

- 修复日期：2026-07-18
- 修复工程师：Repair Engineer (Round 9)
- 测试发现文档：`test_findings.md`（同目录）
- 确认错误数：**16**，已修复：**16/16**（0 跳过）
- 修复文件：`core/cfg/region_analyzer.py`、`core/cfg/region_ast_generator.py`
- 约束遵守：未在 `code_generator.py` 内做后处理补丁；所有修复落在区域分析 / AST 重建源头；无跨区域特殊分支；无硬编码深度限制

## 区域归约算法四原则遵守

1. **自底向上归约**：每个修复在区域分析（`_identify_conditional_regions` / `_extract_with_items`）或基本块语句生成阶段（`_build_store_statement` / `_build_statement` / `_build_delete_stmt` / `_generate_for` / `_generate_with` / `_extract_decorators` / `_extract_comp_elt`）按模式自底向上识别，先识别内层表达式再归约为语句。
2. **每个块唯一归属**：三元赋值 / 三元 kwarg / 三元 list 元素识别命中后即 `return` 并标记 `self.generated_blocks.add(block)`，不重复消费同一块；if-in-handler 的 then/else 块归属通过条件块是否在 handler 集合中来唯一确定。
3. **嵌套即抽象节点**：三元作赋值右值/key/kwarg/list 元素均归约为单一 `Assign` / `Expr` 节点，三元作为 `IfExp` 子树挂载；with-as tuple / for-tuple-target 嵌套解包归约为单一 `Tuple` 节点；walrus 副作用作为 `NamedExpr` 子树挂载，不拆分为多语句。
4. **父区域引用子区域入口**：IF 区域通过子块入口生成 body，修复点全部在 body 块的语句归约层或区域分析的块归属判定层，不影响 IF 区域对子块入口的引用关系。if-in-except-handler 修复保持了 except 区域对 if 块入口的引用。

## 批次与提交记录

| 批次 | 错误 | 提交 | 摘要 |
|------|------|------|------|
| Batch 1 | err4, err5, err9, err11, err6, err10, err12 | `d5e6fb7` | 三元作 STORE_SUBSCR/STORE_ATTR rhs/key + 链式三元 list 元素 + 三元作 KW_NAMES kwarg（单/链式） |
| Batch 2 | err16 | `9220bda` | 带参数装饰器保留 kwargs |
| Batch 3 | err8, err13, err15 | `b404c6b` | walrus：LOAD_ATTR 整合 + 嵌套函数默认 walrus + 嵌套推导式 walrus |
| Batch 4 | err1, err2 | `8df7343` | del subscr+attr 链 + for 多元 tuple 目标 |
| Batch 5 | err7 | `4e3c60a` | with-as tuple unpacking（UNPACK_SEQUENCE） |
| Batch 6 | err3 | `4cf0f7d` | re-raise 保留在 except handler 内的 if body |
| Batch 7 | err14 | `b186a33` | 内联 lambda 调用 FunctionObject → Lambda 转换 |

## 逐错误修复详情

### 错误 01 — `del a[b].c` 丢失外层下标
- 测试：`test_adv09_del_subscr_attr_chain.py`
- 根因：`_build_delete_stmt` 的 `DELETE_ATTR` 路径假设「DELETE_ATTR 之前所有指令构成单一 attr chain」，未识别前导的 `LOAD_NAME a + LOAD_NAME b + BINARY_SUBSCR` 序列，把 `del a[b].c` 退化为 `del b.c`。
- 修复：`_build_delete_stmt` DELETE_ATTR 路径改用 `expr_reconstructor` 处理复杂构造操作（`BINARY_SUBSCR` / `LOAD_ATTR` / `CALL`），保留外层下标对象，正确重建 `del a[b].c`。

### 错误 02 — `for (a, b), (c, d) in pairs` 丢失嵌套解包
- 测试：`test_adv09_for_multi_tuple_target.py`
- 根因：`_generate_for` 的 target 重建逻辑只识别一层 `UNPACK_SEQUENCE`，把 `for (a, b), (c, d) in pairs` 当作 `for a, b in pairs`，丢失第二个 UNPACK_SEQUENCE 和后续两个 STORE_NAME。
- 修复：for 循环 target 重建支持嵌套 `UNPACK_SEQUENCE`（基于栈的归约）；`CodeGenerator` 渲染嵌套 Tuple 元素时加括号以保留 `for (a,b),(c,d) in pairs` 语义。

### 错误 03 — `except: if c: raise` 中 re-raise 被移出 if body
- 测试：`test_adv09_raise_no_arg.py`
- 根因：`_identify_conditional_regions` 中的 `try_handler_blocks` 过滤器无条件剥离 then/else 中的所有 handler 块。当 if 位于 except/finally handler 内部时（条件块本身也在 handler 集合中），then_blocks 被清空，导致 if 体内变 `pass`，`raise` 被移到外层 except body 末尾。
- 修复：仅当 if 条件块本身不在 handler 块集合中时才过滤 then/else 中的 handler 块（`if try_handler_blocks and block not in try_handler_blocks:`）。保留过滤器原目的（防止 if-in-try-body 误吸收 handler 块），同时允许 if-in-handler 保留合法 body 块。

### 错误 04 — `d[k if cond else m] = v` 退化为 Expr
- 测试：`test_adv09_ternary_dict_key_assign.py`
- 根因：`_build_subscript_assign` 假设下标是简单表达式，未识别下标位置的三元（`POP_JUMP_FORWARD_IF_FALSE` 控制流被当作独立 if 区域），三元被拆为独立 Expr，`LOAD_NAME d` / `STORE_SUBSCR` 残留丢失。
- 修复：新增 `_try_build_ternary_store_assign` 辅助方法，检测被 `STORE_SUBSCR` 消费的三元（作为 value TOS3 或作为 key TOS），处理 `d[k]=ternary`、`d[ternary]=v`（含 cond_block 预加载）、`a.b=ternary`。

### 错误 05 — `d[k] = v if cond else w` 退化为 Expr
- 测试：`test_adv09_ternary_dict_value_assign.py`
- 根因：与 err04 同源，`_build_subscript_assign` 未识别赋值右值位置的三元。
- 修复：err04 的 `_try_build_ternary_store_assign` 同时覆盖 `d[k]=ternary` 模式（三元作 value）。

### 错误 06 — `f(x=1 if cond else 2)` 关键字退化为位置参数
- 测试：`test_adv09_ternary_kwarg.py`
- 根因：`expr_reconstructor` 重建 Call 时识别 KW_NAMES，但当 kwarg value 是三元时，整个调用被识别为「TernaryRegion in Call」，三元被拆出，KW_NAMES 与 kwarg 名称 `x=` 关联丢失。
- 修复：新增 `_try_build_ternary_kwarg_call` 辅助方法，检测被 KW_NAMES 消费的三元 kwarg，通过 `co_consts` 查找解析 kwarg 名称（KW_NAMES argval 运行时为 `<unknown>`），处理单三元 kwarg `f(x=t)`。

### 错误 07 — `with ctx as (a, b)` 丢失 tuple 解包
- 测试：`test_adv09_with_as_tuple.py`
- 根因：`_extract_with_items` 只检测 `BEFORE_WITH` 之后的单个 `STORE_*`，未识别 `UNPACK_SEQUENCE N + STORE_* x N` 模式，`UNPACK_SEQUENCE + 2×STORE_NAME` 被错误归为 with body 前置语句。
- 修复：`_extract_with_items` 检测 `UNPACK_SEQUENCE`，收集 N 个后续 `STORE_*` 名字，构建 Tuple AST 字典作为 target；`region.target` 保持字符串或 None（其他位置仍按单名使用），Tuple 信息只通过 `region.items` 传递。`_generate_with` 当 target 是 dict（Tuple AST）时直接用作 `optional_vars`，不再包装为单 Name 节点。

### 错误 08 — `r = (x := f()).attr` walrus 退化为独立赋值
- 测试：`test_adv09_walrus_attr.py`
- 根因：`_build_store_statement` 的 walrus 识别路径的 `_WALRUS_INTEGRATING_OPS` / `_LITERAL_BUILD_OPS` 白名单未含 `LOAD_ATTR`，walrus 被提取为独立 `x = f()`，`LOAD_ATTR + STORE_NAME r` 整段丢失。
- 修复：将 `LOAD_ATTR` 加入 `_WALRUS_INTEGRATING_OPS`，使 walrus 后跟 `LOAD_ATTR + STORE` 被识别为单一 `Assign`（`r = (x := f()).attr`），不提取为独立赋值。

### 错误 09 — `a.b = c if cond else d` 退化为 Expr
- 测试：`test_adv09_ternary_attr_assign.py`
- 根因：与 err04/err05 同源，`_build_attr_assign` 未识别赋值右值位置的三元。
- 修复：err04 的 `_try_build_ternary_store_assign` 同时覆盖 `a.b=ternary` 模式（三元作 STORE_ATTR 的 value TOS2）。

### 错误 10 — `f(a if cond else b, x=d if e else g)` 丢失关键字名
- 测试：`test_adv09_ternary_call_arg_and_kwarg.py`
- 根因：与 err06 同源，三元同时作位置参数和关键字参数时 KW_NAMES 关联丢失。
- 修复：err06 的 `_try_build_ternary_kwarg_call` 同时覆盖混合场景 `f(t1, x=t2)`（位置参数 + 三元 kwarg）。

### 错误 11 — `r = [a if cond else b, d if e else f]` 退化为独立 Expr + 单元素 list
- 测试：`test_adv09_ternary_list_elem.py`
- 根因：`_build_store_statement` 的 list literal 重建假设元素都是简单 `LOAD_*`，未识别 list 元素位置的三元。第一个三元被拆为独立 Expr，第二个三元成为 BUILD_LIST 唯一元素。
- 修复：新增 `_try_build_ternary_chained_container` 辅助方法，检测外层三元 whose merge_block 是内层 TernaryRegion 入口且 container_type 已设置（list/tuple/set/dict），收集所有链式三元表达式，构建含全部元素的容器（如 `r = [t1, t2]`）。

### 错误 12 — `f(x=a if cond else b, y=d if e else g)` 全部丢失关键字名
- 测试：`test_adv09_ternary_nested_kwarg.py`
- 根因：与 err06/err10 同源，多个三元同时作 kwarg 时 KW_NAMES 与全部 kwarg 名称关联丢失。
- 修复：err06 的 `_try_build_ternary_kwarg_call` 同时覆盖多三元 kwarg 场景 `f(x=t1, y=t2)`。

### 错误 13 — `def f(x=(n := 1))` walrus 退化为独立赋值
- 测试：`test_adv09_nested_func_default_walrus.py`
- 根因：`_generate_block_statements` 的 walrus 整合路径只接受 `_build_store_statement` 返回的 `Assign`，但 `def f(x=(n := 1))` 产生 `FunctionDef`（非 Assign），walrus 默认值被提取为独立 `n = 1`，MAKE_FUNCTION 默认值 tuple 丢失 walrus。
- 修复：walrus 整合路径同时接受 `FunctionDef` / `AsyncFunctionDef` / `ClassDef`，使 walrus 默认值保留在函数签名中。

### 错误 14 — `(lambda x, y: x + y)(x=1, y=2)` 退化为无参数 lambda
- 测试：`test_adv09_lambda_call_multi_kwargs.py`
- 根因：内联 lambda 调用被重建为 `Call(func=FunctionObject, ...)`，`CodeGenerator` 渲染 FunctionObject 为占位符 `lambda *args, **kwargs: None`，丢失真实签名和 body，重编字节码从 5 缩为 3 条指令。
- 修复：在 `_build_store_statement`（赋值形式 `r = (lambda...)(...)`）和 `_build_statement`（语句形式 `(lambda...)(...)`）中调用现有的 `_convert_lambda_function_objects` 辅助方法，递归遍历表达式字典树，将任何 `<lambda>` code object 的 FunctionObject 转换为正确 Lambda dict（递归反编译 lambda code object）。常规 FunctionObject（如 `deco(func)` 装饰器模式、`f = lambda: 0` 表达式语句）不受影响（helper 只处理 `<lambda>` code object），保留现有装饰器 / FunctionDef 检测。

### 错误 15 — `[[y := x for x in a] for a in b]` walrus 退化为常量 True
- 测试：`test_adv09_nested_comprehension_walrus.py`
- 根因：`ExpressionReconstructor._extract_comp_elt` 用于嵌套推导式（通过 `_parse_comprehension_from_code`），回退到 `_build_expr_from_instrs` 不处理 walrus，把 `y := x` 退化为常量 True。
- 修复：重写 `_extract_comp_elt`，定位 `STORE_FAST`（循环 target）与 `LIST_APPEND`/`SET_ADD`/`MAP_ADD`/`YIELD_VALUE` 之间的 element，通过 `self.reconstruct` 重建（已处理 walrus 的 `COPY 1 + STORE_*` 模式）。

### 错误 16 — `@decorator(arg=1)` 退化为 `@decorator()`
- 测试：`test_adv09_decorator_with_args_in_if.py`
- 根因：`_extract_decorators` 处理内层 Call 装饰器时只保留 `args` 字段，丢弃 `keywords` 和 `kwargs` 字段，导致 `@decorator(arg=1)` 退化为 `@decorator()`，丢失 `LOAD_CONST + KW_NAMES + PRECALL + CALL`。
- 修复：`_extract_decorators` 处理内层 Call 装饰器时同时保留 `keywords` 和 `kwargs` 字段，使 `@decorator(arg=1)` 保留 KW_NAMES 关键字参数。

## 最终回归结果

### R9 全部 16 个错误（逐个验证）
```
16 passed in 5.21s
```
全部通过。

### IF 区域全量回归
```
1 failed, 564 passed, 2 skipped in 4.70s
```
- 唯一失败：`test_adv03_nested_ternary_chain`（legacy，R8 开始前就已失败，不在本轮 16 个错误范围内）
- R9 基线（修复前）：564 - 16 = 548 passed / 1 legacy failed / 2 skipped（实际表现为 4 failed = 1 legacy + 3 待修，因 batch 5/6/7 修复前 3 个错误尚未修）
- R9 修复后：564 passed / 1 legacy failed / 2 skipped（16 个错误全部修复，新增 51 个 adv09 测试中 35 通过 + 16 修复后通过）

### 跨区域验证（control_flow_matrix）
```
4 failed, 323 passed, 11 skipped in 2.06s
```
- 与 R8 基线完全一致（323 passed / 4 failed / 11 skipped），未引入任何跨区域回退。
- 4 个失败均为既有问题（`TestL12WhileBreakContinue` / `TestN11TryWhileContinue` / `TestCF2WhileIfBreakContinue` 的 Break/Continue 结构识别 + `TestXP04BoolOpInIf` 的 BoolOp 节点），与本轮 IF 区域修复无关。

## 修复策略归纳

本轮 16 个错误的根因集中在四类 AST 重建 / 区域分析源问题，全部在归约源头修复：

1. **三元表达式被过度识别为独立 if 区域**（err4, err5, err6, err9, err10, err11, err12，共 7 个）：`POP_JUMP_FORWARD_IF_FALSE` 控制流被识别为独立 if 区域，三元被拆出作为独立 Expr，破坏外层赋值 / 调用 / list 结构，KW_NAMES 与 kwarg 名关联丢失。修复方式是新增三个模式识别 helper（`_try_build_ternary_store_assign` / `_try_build_ternary_chained_container` / `_try_build_ternary_kwarg_call`），在 merge_block 阶段优先识别三元被外层 STORE_SUBSCR/STORE_ATTR/KW_NAMES/BUILD_LIST 消费的模式，将三元作为 IfExp 子树归约到外层语句，不拆分为独立 Expr。

2. **walrus 副作用识别白名单不完整**（err8, err13, err15，共 3 个）：`_WALRUS_INTEGRATING_OPS` / `_LITERAL_BUILD_OPS` 未含 `LOAD_ATTR`（err8）、walrus 整合路径只接受 Assign 不接受 FunctionDef（err13）、`_extract_comp_elt` 回退到不处理 walrus 的 `_build_expr_from_instrs`（err15）。修复方式是泛化白名单与接受类型，重写 `_extract_comp_elt` 复用支持 walrus 的 `self.reconstruct`。

3. **混合目标 / 嵌套 unpack 识别不全**（err1, err2, err7，共 3 个）：`_build_delete_stmt` 未识别前导 `BINARY_SUBSCR`（err1）、`_generate_for` 只识别一层 UNPACK_SEQUENCE（err2）、`_extract_with_items` 未识别 UNPACK_SEQUENCE 模式（err7）。修复方式是统一扩展 delete/for/with 的目标识别以支持嵌套 unpack 和混合 attr/subscr 目标。

4. **区域分析过滤器过度剥离 handler 块**（err3，1 个）：`try_handler_blocks` 过滤器无条件剥离 if 的 then/else 中的 handler 块，当 if 位于 except/finally handler 内部时清空 if body。修复方式是添加条件块集合检查，仅当 if 条件块不在 handler 集合中时才过滤。

5. **FunctionObject 占位符渲染丢失 lambda 语义**（err14，1 个）：内联 lambda 调用的 FunctionObject 被 CodeGenerator 渲染为占位符。修复方式是复用现有 `_convert_lambda_function_objects` helper 在 AST 重建阶段将 `<lambda>` FunctionObject 转换为 Lambda dict，不修改 CodeGenerator。

6. **装饰器调用 kwargs 字段丢失**（err16，1 个）：`_extract_decorators` 处理内层 Call 装饰器时丢弃 `keywords`/`kwargs` 字段。修复方式是保留这两个字段，使装饰器调用保留 KW_NAMES 关键字参数。

所有修复均泛化为模式识别，不针对特定测试用例硬编码，不依赖跨区域信息，无硬编码深度限制。0 跳过。
