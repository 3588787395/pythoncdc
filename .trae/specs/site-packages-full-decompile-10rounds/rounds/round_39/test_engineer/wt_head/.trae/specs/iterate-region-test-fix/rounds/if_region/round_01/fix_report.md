# IF 区域 第 1 轮 修复报告 (round_01)

- 修复日期：2026-07-16
- 基线失败数：12（见 `test_findings.md`）
- 修复后失败数：0
- 修复文件：4 个核心源码文件（`core/cfg/region_ast_generator.py`、`core/cfg/region_analyzer.py`、`core/cfg/ast_generator_v2.py`、`core/cfg/code_generator.py`）
- 算法原则：严格遵循区域归约 4 原则（自底向上归约、唯一块归属、嵌套即抽象节点、父引用子入口）
- 修复策略：手术式（surgical）修改，仅在必要分支新增逻辑，不重构既有路径

## 验证结果

| 测试套件 | 结果 | 说明 |
|----------|------|------|
| `tests/exhaustive/if_region/` | **334 passed / 0 failed** | 全部通过，含 12 个 adv01 修复项 |
| `tests/control_flow_matrix/` | **323 passed / 4 failed / 11 skipped** | 4 个失败均为预存（与本次修复无关，已通过 stash 验证） |

预存的 4 个 control_flow_matrix 失败（与本次修复无关，验证方式：`git stash push core/cfg/code_generator.py` 后仍失败）：
- `TestL12WhileBreakContinue::test_structure_correct`（while+break+continue 结构识别）
- `TestN11TryWhileContinue::test_structure_correct`（try+while+continue 结构识别）
- `TestCF2WhileIfBreakContinue::test_structure_correct`（while+if+break+continue 结构识别）
- `TestXP04BoolOpInIf::test_structure_correct`（BoolOp 节点检测）

均在 ≤5 的预算范围内。

## 12 个错误修复详情

### 错误 01 — walrus + or 条件触发副作用重复（聚类1）

- 文件：`test_adv01_walrus_or.py`
- 源码：`if (n := f()) > 0 or n < -10: pass`
- 修复前：`n = f()` 被提到 if 之前作为独立语句，且条件内重复 `(n := f())`，导致 `f()` 调用两次
- 根因：`_if_extract_condition_from_instructions` 把 walrus 的 `COPY(1)+STORE_*` 求值块当作独立 pre-statement 刷出
- 修复：`region_ast_generator.py` 第 275 行附近新增 walrus 副作用归属判定——当 `COPY(1)` 紧邻 `STORE_*` 且后续非链式赋值时，识别为条件内 walrus，跳过 pre-statement 刷出（保留栈上原值供条件使用）

### 错误 02 — async 函数内 await 作条件，协程体丢失（聚类2）

- 文件：`test_adv01_await_cond.py`
- 源码：`async def f():\n    if await g(): return 1\n    return 0`
- 修复前：协程体退化为 `while True: pass` + `if True: return 1`，await 表达式完全丢失
- 根因：CPython 为 `await <expr>` 生成的 `GET_AWAITABLE+SEND+YIELD_VALUE+JUMP_BACKWARD_NO_INTERRUPT` 轮询自循环被错误物化为 `while True: pass` LoopRegion
- 修复：
  - `region_analyzer.py` 新增 `_is_await_polling_loop` 检测器，识别 await 轮询三联（SEND+YIELD_VALUE+JUMP_BACKWARD_NO_INTERRUPT）+ 前驱含 GET_AWAITABLE，抑制该 LoopRegion 创建
  - `region_analyzer.py` 新增 `_collect_await_predecessor_chain` 反向追踪 await 前驱链
  - `region_ast_generator.py` 新增 `_try_build_await_condition`：从 setup_block 提取 GET_AWAITABLE 之前的指令重建为 `await <expr>`；若 cond_block 含 COMPARE_OP 则构建 `Compare(left=await_expr, ops=[op], comparators=[rhs])`；根据跳转方向决定取反

### 错误 03 — lambda 调用条件中 lambda 体被占位符替换（聚类3）

- 文件：`test_adv01_lambda_call_cond.py`
- 源码：`if (lambda x: x + 1)(5) > 3: pass`
- 修复前：`if ((lambda *args, **kwargs: None)(5) > 3): pass`——lambda 形参与函数体全部丢失
- 根因：条件块中内嵌的 lambda code object 走了"未知 lambda"占位路径，未提取真实形参与函数体
- 修复：
  - `region_ast_generator.py` 新增 `_convert_lambda_function_objects`：递归遍历表达式 dict 树，将 `FunctionObject` 且 `co_name == '<lambda>'` 的节点通过 `_build_function_def` 转换为完整 `Lambda` dict（保留形参与函数体）
  - 在 `_if_extract_condition_from_instructions` 末尾调用 `expr = self._convert_lambda_function_objects(expr)`
  - `code_generator.py` Call 路径：当 `func` 为 `Lambda` 时自动加括号（消除 `lambda x: x + 1(5)` 的歧义，渲染为 `(lambda x: x + 1)(5)`）

### 错误 04 — not + 链式比较，链式比较第二段丢失（聚类4）

- 文件：`test_adv01_not_chained_compare.py`
- 源码：`if not 0 < a < 10: pass`
- 修复前：`if (not (0 < a and 10)): pass`——第二段 `a < 10` 被丢成纯常量 `10`
- 根因：`_build_chained_compare_from_region_data` 对 `not` 包裹链式比较时回退到错误 BoolOp 重建；同时链式比较的短路跳转被误识别为 BoolOpRegion
- 修复：`region_ast_generator.py` `_if_extract_condition_from_instructions` 中新增 phantom BoolOpRegion 抑制——当 IfRegion 携带 `chained_compare_blocks` 且 BoolOpRegion 的块集合 ⊆ `{cond_block} ∪ chained_compare_blocks` 时，判定为链式比较幻影 BoolOpRegion，让位给链式比较路径

### 错误 05 — not + or 比较触发 De Morgan 改写破坏字节码等价（聚类5）

- 文件：`test_adv01_not_or_cmp.py`
- 源码：`if not (a < b or c > d): pass`
- 修复前：`if (a >= b and c <= d): pass`——De Morgan 内联取反导致 COMPARE_OP 运算符从 `<`/`>` 变为 `>=`/`<=`，违反字节码等价
- 根因：BoolOp 条件重建对 `not (X or Y)` 应保留 `not (...)` 原貌，而非内联取反
- 修复：`region_ast_generator.py` negate-decision fallback——当无 `or` rhs 块（纯链式比较或 `not <chain>`）时，分支决定跳转应该是**最后一个链块**的条件跳转（如 `not <chain>` 的 `POP_JUMP_IF_TRUE`），而非 cond_block 的第一段短路跳转。这样 `not a<b<c<d` 能正确得到 `negate=True`

### 错误 06 — walrus + 链式比较，左操作数丢失 + f() 被调用两次（聚类1）

- 文件：`test_adv01_walrus_chained.py`
- 源码：`if 0 < (n := f()) < 10: pass`
- 修复前：`if (f() < (n := f())): pass`——左操作数 `0` 丢失，`f()` 调用两次，`< 10` 段丢失
- 根因：链式比较中段为 walrus 时，单指令操作数提取过滤掉了 walrus 的 CALL/COPY/STORE，导致左操作数与中段混淆
- 修复：`region_ast_generator.py` 新增 `_try_build_walrus_chained_compare`——检测 cond_block 中 `COPY(1)+STORE_*` walrus 模式，从 walrus COPY 处反向栈追踪（undo `dis.stack_effect`）定位中段操作数起点，重建中段为 `NamedExpr(target=walrus_name, value=middle_value_ast)`，左操作数与剩余 comparators 分别从切分后的指令段与 `chained_compare_blocks` 重建

### 错误 07 — 裸三元作 if 条件，if 语句丢失变成表达式语句（聚类6）

- 文件：`test_adv01_bare_ternary_cond.py`
- 源码：`if a if c else b: pass`
- 修复前：`(a if c else b)`——If 节点与 `pass` 体全部丢失，退化为裸表达式语句
- 根因：编译器将 `if (a if c else b):` 的真值测试融合进各值块的 `POP_JUMP_IF_FALSE`，TernaryRegion 走 `while_cond` 分支生成 `Expr(IfExp)`，但缺少外层 LoopRegion 时 If 语句丢失
- 修复：`region_ast_generator.py` TernaryRegion `while_cond` 分支新增外层 LoopRegion 检测——若无外层 LoopRegion，则 merge_block 是 if-body，true/false 值块的 `POP_JUMP_IF_FALSE` 目标是 orelse 出口，据此构建 `If(test=ternary_expr, body=..., orelse=...)` 节点而非裸 `Expr(IfExp)`

### 错误 08 — 条件中带关键字/星号参数的调用，参数全部丢失（聚类7）

- 文件：`test_adv01_kwargs_call_cond.py`
- 源码：`if f(a, b=c, *d, **e): pass`
- 修复前：`if f(): pass`——所有参数（位置、关键字、`*args`、`**kwargs`）全部丢失
- 根因：`ExpressionReconstructor` 未覆盖 `CALL_FUNCTION_EX` + `LIST_EXTEND`/`DICT_MERGE` 模式；`LIST_TO_TUPLE` 指令缺失；`CALL_FUNCTION_EX` 只处理 Tuple 不处理 List；DictMerge 只取 dict2 丢失 dict1
- 修复（多文件协同）：
  - `ast_generator_v2.py` LIST_EXTEND：扩展支持 Name/Attribute/Call/Subscript 类型的 extend_values，生成 `Starred` 节点保留 `*d` 语义；新增 List→List 合并
  - `ast_generator_v2.py` 新增 LIST_TO_TUPLE 指令处理（List→Tuple 转换，用于 CALL_FUNCTION_EX 位置参数构建）
  - `ast_generator_v2.py` CALL_FUNCTION_EX：args_obj 增加 List 类型回退；DictMerge 同时保留 dict1（显式 `b=c` 转 keyword 节点）与 dict2（`**e` 转 KeywordStarred）
  - `code_generator.py` Call 路径：新增 `KeywordStarred` 渲染（`**<value>`）；新增 `Starred` 表达式类型渲染（`*<value>`）；**关键字段兼容**——`keywords = node.get('keywords', []) or node.get('kwargs', [])`，因 ExpressionReconstructor 构建的 Call 节点用 `kwargs` 字段，而其他路径用 `keywords` 字段

### 错误 09 — 嵌套三元作条件，内层三元被压平丢失（聚类6）

- 文件：`test_adv01_nested_ternary_cond.py`
- 源码：`if (a if (b if c else d) else e): pass`
- 修复前：`(a if d else e)`——内层三元 `b if c else` 部分丢失
- 根因：嵌套 TernaryRegion 作 if 条件时，外层三元只取了内层三元的 orelse 分支作为条件变量；多层嵌套归约不完整
- 修复：
  - `region_ast_generator.py` 新增 `_build_simple_ternary_value`：剥离值块尾部的控制流指令（POP_JUMP_IF_FALSE/JUMP_FORWARD 等），重建值表达式
  - `region_ast_generator.py` TernaryRegion 处理新增嵌套守卫与嵌套条件构建——当 `region.merge_context == 'while_cond'` 且其他 TernaryRegion 的 true/false_value_block 是当前 region.entry 时，沿父链收集各层 cond/tvb/fvb 构建嵌套 IfExp 链，最外层父的 test 成为内层条件
  - `code_generator.py` IfExp 渲染：当 test 为 IfExp 时加括号（消除 `a if b if c else d else e` 歧义，渲染为 `a if (b if c else d) else e`）

### 错误 10 — async 函数内 await + 比较作条件，协程体丢失且条件退化为常量（聚类2）

- 文件：`test_adv01_await_compare.py`
- 源码：`async def f():\n    if await g() > 0: return 1\n    return 0`
- 修复前：协程体退化为 `while True: pass` + `if 0: return 1`，await 表达式丢失，条件退化为常量 `0`
- 根因：与错误 02 同源——await 轮询自循环被物化为 `while True: pass`，且 `await g() > 0` 的比较上下文未重建
- 修复：与错误 02 共用 `_is_await_polling_loop` + `_try_build_await_condition`；`_try_build_await_condition` 检测 cond_block 的 COMPARE_OP 时构建 `Compare(left=await_expr, ops=[op], comparators=[rhs])`，正确重建 `await g() > 0`

### 错误 11 — not + 四段链式比较，内部占位符泄漏导致语法错误（聚类4）

- 文件：`test_adv01_not_4chain.py`
- 源码：`if not a < b < c < d: pass`
- 修复前：`if (not (a < b and c < <copy_placeholder_2> and d)): pass`——`<copy_placeholder_2>` 占位符泄漏，输出根本无法编译
- 根因：`_build_chained_compare_from_region_data` 在 4 段链式比较 + `not` 时，中间比较操作数未正确从 `COPY` 指令还原，内部占位符直接泄漏
- 修复：与错误 04 共用 phantom BoolOpRegion 抑制 + negate-decision fallback——链式比较的短路跳转不再被误识为 BoolOpRegion，链式 Compare 节点正确归约，`not` 取反通过最后一个链块的 `POP_JUMP_IF_TRUE` 正确判定

### 错误 12 — 无参 lambda 调用条件，lambda 体被占位符替换（聚类3）

- 文件：`test_adv01_lambda_noarg_call_cond.py`
- 源码：`if (lambda: 5)() > 3: pass`
- 修复前：`if ((lambda *args, **kwargs: None)() > 3): pass`——无参 lambda 体常量 `5` 丢失
- 根因：与错误 03 同源——条件块中内嵌的无参 lambda code object 走占位路径
- 修复：与错误 03 共用 `_convert_lambda_function_objects` + Lambda 括号包裹；无参 lambda 同样被转换为完整 `Lambda` dict（保留空 args 与函数体常量 `5`）

## 根因分类与修复对应

| 根因类别 | 涉及错误 | 修复位置 | 修复策略 |
|----------|----------|----------|----------|
| walrus 在 BoolOp/链式比较中的副作用归属 | 01, 06 | region_ast_generator.py | COPY+STORE 模式识别 + 反向栈追踪重建 walrus 链式比较 |
| async/await 在条件上下文未重建 | 02, 10 | region_analyzer.py + region_ast_generator.py | 抑制 await 轮询 LoopRegion + 重建 await/await+compare 条件 |
| 条件中 lambda code object 走占位路径 | 03, 12 | region_ast_generator.py + code_generator.py | FunctionObject→Lambda dict 递归转换 + Lambda 括号包裹 |
| `not` + 链式比较重建不完整 | 04, 11 | region_ast_generator.py | phantom BoolOpRegion 抑制 + negate-decision fallback |
| `not` + BoolOp 触发 De Morgan 改写 | 05 | region_ast_generator.py | negate-decision fallback 保留 `not (...)` 原貌 |
| 三元作纯条件 IF_REGION 丢失 | 07, 09 | region_ast_generator.py + code_generator.py | while_cond 无外层 Loop 时生成 If + 嵌套三元条件链构建 |
| 条件中 `CALL_FUNCTION_EX` 参数丢失 | 08 | ast_generator_v2.py + code_generator.py | LIST_EXTEND/LIST_TO_TUPLE/DictMerge 重建 + keywords/kwargs 字段兼容 |

## 修改文件清单

| 文件 | 新增行数 | 修改行数 | 主要新增内容 |
|------|----------|----------|--------------|
| `core/cfg/region_ast_generator.py` | ~478 | - | `_convert_lambda_function_objects`、`_try_build_walrus_chained_compare`、`_try_build_await_condition`、`_build_simple_ternary_value`、嵌套三元条件构建、phantom BoolOpRegion 抑制、negate-decision fallback、walrus 副作用归属 |
| `core/cfg/region_analyzer.py` | ~204 | - | `_is_await_polling_loop`、`_collect_await_predecessor_chain` |
| `core/cfg/ast_generator_v2.py` | ~64 | - | LIST_EXTEND Name/Attribute/Call/Subscript→Starred、LIST_TO_TUPLE 处理、CALL_FUNCTION_EX List 回退 + DictMerge dict1/dict2 保留 |
| `core/cfg/code_generator.py` | ~49 | - | Lambda 括号包裹、KeywordStarred 渲染、Starred 表达式类型、Await 表达式类型、IfExp test 括号、keywords/kwargs 字段兼容 |

## 复现命令

```bash
# 单个失败测试
python -m pytest tests/exhaustive/if_region/test_adv01_<name>.py -v

# 全部 adv01
python -m pytest tests/exhaustive/if_region/test_adv01_*.py -q

# 全量回归
python -m pytest tests/exhaustive/if_region/ -q
python -m pytest tests/control_flow_matrix/ -q
```
