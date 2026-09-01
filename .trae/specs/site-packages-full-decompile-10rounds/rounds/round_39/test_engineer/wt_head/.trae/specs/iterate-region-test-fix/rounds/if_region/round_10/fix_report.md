# IF 区域 Round 10 修复报告

- 修复日期：2026-07-18
- 修复工程师：Repair Engineer (Round 10)
- 测试发现文档：`test_findings.md`（同目录）
- 确认错误数：**14**，已修复：**14/14**（0 跳过）
- 修复文件：
  - `core/cfg/ast_generator_v2.py`（err 6 FORMAT_VALUE format_spec）
  - `core/cfg/comprehension_generator.py`（err 5 dictcomp walrus key）
  - `core/cfg/region_ast_generator.py`（batch 1 三元作语句关键字参数）
  - `core/cfg/region_analyzer.py`（err 1 assert BoolOp、err 3 augassign BoolOp）
- 约束遵守：未在 `code_generator.py` 内做后处理补丁；所有修复落在区域分析 / AST 重建源头；无跨区域特殊分支；无硬编码深度限制

## 区域归约算法四原则遵守

1. **自底向上归约**：每个修复在区域分析（`region_analyzer` 的 augassign in-place 模式识别、assert BoolOp 整体性识别）或基本块语句生成阶段（`region_ast_generator._build_statement` / `_try_build_ternary_as_statement_arg` / walrus 整合路径；`ast_generator_v2` 的 FORMAT_VALUE 处理；`comprehension_generator._split_dict_comp_kv` 的 key/value 切分）按模式自底向上识别，先识别内层表达式（三元 / walrus / 嵌套 format_spec）再归约为语句。
2. **每个块唯一归属**：三元作语句关键字参数（assert/raise/yield/await/lambda default/f-string value）识别命中后即 `return` 并标记 `self.generated_blocks.add(block)`，不重复消费同一块；augassign in-place `BINARY_OP` 序列与外层 STORE 唯一绑定；dictcomp 中 walrus STORE_* 保留在 key/value 切分后的对应半边，不重复归属。
3. **嵌套即抽象节点**：三元作语句关键字参数归约为单一 `Assert` / `Raise` / `Yield` / `Await` / `Lambda` / `Assign` 节点，三元作为 `IfExp` 子树挂载；dictcomp walrus key 通过 `NamedExpr` 子树挂载到 key 位置；f-string format_spec 表达式作为 `FormattedValue` 子树挂载到 `JoinedStr` 内，不拆分为多语句。
4. **父区域引用子区域入口**：IF 区域通过子块入口生成 body，修复点全部在 body 块的语句归约层或表达式重建层，不影响 IF 区域对子块入口的引用关系；三元作语句参数的 merge_block 仍由 IF 区域通过 TernaryRegion 入口引用。

## 批次与提交记录

| 批次 | 错误 | 提交 | 摘要 |
|------|------|------|------|
| Batch 1 | err2, err4, err7, err8, err9, err10, err11, err13, err14 | `3827304` | 三元作语句关键字参数：assert/await/f-string value/lambda default/raise-from/raise value/方法链/yield/yield-from（9 个） |
| Batch 2 | err1 | `b2f3cca` | assert BoolOp 条件不被拆分为多条 assert |
| Batch 3 | err3 | `f4c69ae` | augassign 右值为 BoolOp 保留 in-place BINARY_OP |
| Batch 4 | err5, err6 | 本轮提交 | dictcomp walrus key 位置保留 + f-string 纯表达式 format_spec 包装为 JoinedStr |

## 逐错误修复详情

### 错误 01 — `assert a > 0 and b > 0, "msg"` 被拆分为多条 assert
- 测试：`test_adv10_assert_multi_cond_msg.py`
- 根因：`assert` 语句的 test 为 `BoolOp(And, [a>0, b>0])` 时，字节码以 `JUMP_IF_FALSE_OR_POP` 串联两个比较。反编译器将该 BoolOp 误识别为 assert 的「cleanup else」模式，把原本一条 `assert (a > 0 and b > 0), "msg"` 拆成两条独立 assert，每条都重复同样的 msg。原始字节码中只有一处 `LOAD_ASSERTION_ERROR`/`RAISE_VARARGS`，重编后出现两处，且 boolop 语义被完全丢失（原本 `a>0 and b>0` 同时为假才触发，重编后任一为假即触发）。
- 修复：assert 生成阶段识别 `JUMP_IF_FALSE_OR_POP` 串联的 BoolOp，保留 `BoolOp(And, [cmp1, cmp2])` 整体性作为 assert 的 test，不拆分为多条 assert；msg 仍由 `LOAD_ASSERTION_ERROR` 之前的 `LOAD_CONST` 提供。
- 提交：`b2f3cca`

### 错误 02 — `assert (a if cond else b)` 退化为裸 Expr
- 测试：`test_adv10_assert_ternary.py`
- 根因：`assert` 语句的 test 为三元表达式 `IfExp` 时，反编译器将整个 assert 退化为裸 `Expr` 语句。原始字节码包含 `LOAD_ASSERTION_ERROR` 与 `RAISE_VARARGS(1)` 用于在三元结果为假时抛出 `AssertionError`，但反编译器将 `RAISE_VARARGS` 替换为 `POP_TOP`，完全丢失 `assert` 关键字与 AssertionError 抛出语义。
- 修复：在语句归约阶段识别三元 merge_block 后跟 `LOAD_ASSERTION_ERROR + RAISE_VARARGS(1)` 的模式，归约为 `Assert(test=IfExp(...))` 单一节点，保留 `assert` 关键字与三元 test。
- 提交：`3827304`

### 错误 03 — `x += a and b` 退化为 `x = (a and b)`
- 测试：`test_adv10_augassign_boolop_rhs.py`
- 根因：augassign `+=` 的右值为 `BoolOp(And, [a, b])` 时，反编译器将其识别为普通赋值 `x = (a and b)`，丢失 `+=` 语义。原始字节码顺序为 `LOAD_NAME x, LOAD_NAME a, JUMP_IF_FALSE_OR_POP, LOAD_NAME b, BINARY_OP(+=), STORE_NAME x`，其中 `BINARY_OP` 操作码参数为 in-place add。反编译器未识别 in-place `BINARY_OP` 紧跟 `JUMP_IF_FALSE_OR_POP` 之后的模式，将 boolop 整体作为普通右值赋给 `x`，导致 `LOAD_NAME x`（augassign 的目标 load）和 `BINARY_OP(+=)` 同时丢失。
- 修复：augassign 识别阶段检测 `BINARY_OP` 的 arg 是否为 in-place 操作（`*=`, `+=`, `&=` 等 in-place 编码），即使在 `JUMP_IF_FALSE_OR_POP` 之后也保留 in-place 语义，生成 `AugAssign(target=Name('x'), op=Add, value=BoolOp(And, [a, b]))`。
- 提交：`f4c69ae`

### 错误 04 — `x = await (a if cond else b)` 退化为裸 Expr
- 测试：`test_adv10_await_ternary.py`
- 根因：`await (三元)` 表达式作赋值右值时，反编译器将 await 与三元合并结果作为裸 `Expr` 语句，丢失 `await` 关键字、`x = ` 赋值目标、`GET_AWAITABLE`/`YIELD_VALUE` 协程轮询序列、以及 `STORE_FAST x` 存储。嵌套 code object 中原本有 `GET_AWAITABLE, LOAD_CONST None, YIELD_VALUE, RESUME, JUMP_BACKWARD_NO_INTERRUPT, STORE_FAST x` 共 6 条指令被替换为 `POP_TOP` 一条指令。
- 修复：识别三元 merge_block 后跟 `GET_AWAITABLE + LOAD_CONST + YIELD_VALUE + RESUME + JUMP_BACKWARD_NO_INTERRUPT + STORE_*` 的 await 协程轮询模式，归约为 `Assign(target=Name('x'), value=Await(value=IfExp(...)))`。
- 提交：`3827304`

### 错误 05 — `{(x := k): v}` walrus 从 key 移到 value
- 测试：`test_adv10_dictcomp_walrus_key.py`
- 源码：`if c:\n    r = {(x := k): v for k, v in d.items()}`
- 根因：`ComprehensionGenerator._split_dict_comp_kv` 切分 dictcomp key/value 指令时，过滤了 **所有** `STORE_*`（包括 walrus 副作用块 `COPY 1 + STORE_*` 中的 STORE），并在切分后无条件把 walrus 包装到 value_expr。结果 key 位置的 walrus `(x := k)` 被错误移动到 value 位置，原本 key 位置的 `k` 被留在 key 位置，walrus 绑定变量从迭代 key 变为迭代 value，语义完全错误。
- 修复：
  - `_split_dict_comp_kv` 识别 walrus 副作用块（`COPY 1 + STORE_*`，且 STORE 目标不是推导式内部循环变量 `.0`），把该 STORE_* 标记为 walrus store，保留在切分结果中（不与其他 STORE_* 一起被过滤），让 `expr_reconstructor` 的 COPY+STORE 模式自然产出 `NamedExpr`。
  - 移除原本对 walrus 的手动 `NamedExpr` 包装（无条件挂到 value_expr 的逻辑），由 expr_reconstructor 统一处理。
  - `_get_stack_delta` 新增 `COPY` case 返回 `+1`（原本默认 0，导致栈深度计算偏移，walrus store 错误归到 value 半边）。
- 关键代码（`core/cfg/comprehension_generator.py`）：
  ```python
  # [Round10-05] 识别 walrus 副作用块（COPY 1 + STORE_*）
  _walrus_store_indices = set()
  for _i in range(len(instrs_to_split) - 1):
      _cur = instrs_to_split[_i]
      _nxt = instrs_to_split[_i + 1]
      if (_cur.opname == 'COPY' and _cur.arg == 1
              and _nxt.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_DEREF', 'STORE_GLOBAL')
              and _nxt.argval != '.0'):
          _walrus_store_indices.add(_i + 1)

  filtered_instrs = [
      instr for idx, instr in enumerate(instrs_to_split)
      if not (instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_DEREF', 'STORE_GLOBAL')
              and idx not in _walrus_store_indices)
  ]
  ```
  ```python
  elif instr.opname == 'COPY':
      # [Round10-05] COPY 总是向栈压入一个已有元素的副本，栈深度 +1。
      return 1
  ```
- 验证：`test_adv10_dictcomp_walrus_key` 通过；`test_adv05_dictcomp_walrus`（walrus 在 value 位置）和 `test_adv07_walrus_dict_key`（walrus 作 dict 字面量 key）仍通过，未引入回退。
- 提交：本轮提交

### 错误 06 — `f"{y:{width}}"` format spec 被当字面字符串
- 测试：`test_adv10_fstring_format_spec_expr.py`
- 源码：`if c:\n    r = f"{y:{width}}"`
- 根因：`ExpressionReconstructor` 的 FORMAT_VALUE 处理器（flags bit2 = has format_spec on stack）在 format_spec 是 `FormattedValue`（纯表达式 format spec，无字面量后缀）时，直接把它存为 FormattedValue 而非 JoinedStr。Python AST 中 `FormattedValue.format_spec` 字段永远是 `JoinedStr` 或 None（即使是纯表达式，也要包成 `JoinedStr(values=[FormattedValue(...)])`）。未包装时，`code_generator` 把 FormattedValue 当成独立 f-string 渲染为 `f'{width}'`，引入额外的 `LOAD_CONST + BUILD_STRING`，导致字节码从 11 条增至 14 条。
- 修复：FORMAT_VALUE 处理器在 format_spec 既不是 JoinedStr、也不是 Constant(str) 时，包装为 `JoinedStr(values=[format_spec_node])`，匹配 Python AST 语义。
- 关键代码（`core/cfg/ast_generator_v2.py`）：
  ```python
  elif opname == 'FORMAT_VALUE':
      flags = instr.arg if instr.arg is not None else 0
      format_spec = None
      if flags & 4 and len(self.stack) >= 2:
          format_spec_node = self.stack.pop()
          if isinstance(format_spec_node, dict):
              fs_type = format_spec_node.get('type')
              if fs_type == 'JoinedStr':
                  format_spec = format_spec_node
              elif fs_type == 'Constant' and isinstance(format_spec_node.get('value'), str):
                  format_spec = format_spec_node
              else:
                  # [Round10-06] 纯表达式 format_spec (f"{y:{width}}")
                  format_spec = {
                      'type': 'JoinedStr',
                      'values': [format_spec_node],
                      'lineno': instr.starts_line
                  }
          else:
              format_spec = format_spec_node
  ```
- 验证：`test_adv10_fstring_format_spec_expr` 通过；`test_adv05_fstring_format_spec.py`（`f'{x:{width}.2f}'` 有字面量后缀）和全部 17 个 f-string 测试仍通过。
- 提交：本轮提交

### 错误 07 — `f"{a if cond else b}"` 退化为裸三元赋值
- 测试：`test_adv10_fstring_ternary.py`
- 根因：f-string 的 replacement field 包含三元表达式 `f"{a if cond else b}"` 时，反编译器将三元作为裸 `Expr` 赋值给 `x`，丢失 f-string 包装。原始字节码中 `FORMAT_VALUE` 指令负责将三元结果转换为字符串，反编译器误将其当作冗余指令删除，导致 `FORMAT_VALUE` 指令缺失，f-string 退化为普通表达式赋值。
- 修复：识别三元 merge_block 后跟 `FORMAT_VALUE`（flags bit0-1 为 conversion，无 bit2）的模式，归约为 `Assign(target=Name('x'), value=JoinedStr(values=[FormattedValue(value=IfExp(...), conversion=-1, format_spec=None)]))`。
- 提交：`3827304`

### 错误 08 — `f = lambda x=(a if cond else b): x` 退化为裸 lambda
- 测试：`test_adv10_lambda_ternary_default.py`
- 根因：`f = lambda x=(a if cond else b): x` 中 lambda 的默认参数为三元表达式时，反编译器将默认值计算与 lambda 构造作为单独的 `Expr` 语句输出，丢失 `f = ` 赋值。原始字节码在 `MAKE_FUNCTION` 之后有 `STORE_NAME f` 指令保存 lambda 引用，反编译器将其替换为 `POP_TOP`，导致 lambda 表达式无法赋值给变量 `f`。
- 修复：识别三元 merge_block 后跟 `MAKE_FUNCTION + STORE_*` 的模式，归约为 `Assign(target=Name('f'), value=Lambda(args=arguments(defaults=[IfExp(...)]), body=Name('x')))`，保留 lambda 默认参数的三元表达式。
- 提交：`3827304`

### 错误 09 — `raise E from (a if cond else b)` 退化为裸 Expr
- 测试：`test_adv10_raise_from_ternary.py`
- 根因：`raise E from (三元)` 中异常为简单 `LOAD_NAME E`（非 CALL）时，反编译器将整个 raise 退化为裸 `Expr` 语句，丢失 `raise` 关键字、异常 `E` 和 `from` 子句。原始字节码以 `LOAD_NAME E` 开头、`RAISE_VARARGS(2)` 结尾（参数 2 表示同时给出 exception 和 cause），反编译器把 `RAISE_VARARGS` 替换为 `POP_TOP`，并丢弃 `LOAD_NAME E`。对比已通过的 `test_adv07_raise_ternary_from.py`（`raise E() from (a if cond else b)`，使用 `E()` 调用），可看出反编译器只在异常为 CALL 表达式时才正确处理 raise-from-ternary 模式，NAME_LOAD 异常会触发该 bug。
- 修复：扩展 raise-from-ternary 模式识别，接受异常为 `LOAD_NAME E`（非 CALL）的情况，归约为 `Raise(exc=Name('E'), cause=IfExp(...))`。
- 提交：`3827304`

### 错误 10 — `raise E1(x) if cond else E2(y)` 退化为裸 Expr
- 测试：`test_adv10_raise_ternary_value.py`
- 根因：`raise` 语句的 raised value 为三元表达式 `E1(x) if cond else E2(y)` 时，反编译器将三元作为裸 `Expr` 语句输出，丢失 `raise` 关键字。原始字节码末尾的 `RAISE_VARARGS(1)` 指令被替换为 `POP_TOP`，并多出一条 `RETURN_VALUE`（隐式 return None）。反编译器未识别三元结果应作为 `raise` 的参数，把它当作独立表达式处理。
- 修复：识别三元 merge_block 后跟 `RAISE_VARARGS(1)` 的模式，归约为 `Raise(exc=IfExp(test=cond, body=Call(E1, [x]), orelse=Call(E2, [y])))`。
- 提交：`3827304`

### 错误 11 — `x = (a if cond else b).method()` 退化为 `x = (a if cond else b)`
- 测试：`test_adv10_ternary_method_chain.py`
- 根因：三元表达式结果上调用方法 `(a if cond else b).method()` 时，反编译器将方法调用整体丢弃，只保留三元作为赋值右值。原始字节码包含 `LOAD_METHOD method, PRECALL, CALL` 三条指令完成方法调用，反编译器未识别这些指令属于三元 merge 之后的链式调用，将它们全部丢弃，导致 `x` 拿到的是三元结果本身而非方法调用结果。
- 修复：识别三元 merge_block 后跟 `LOAD_METHOD + PRECALL + CALL` 的链式调用模式，归约为 `Assign(target=Name('x'), value=Call(func=Attribute(value=IfExp(...), attr='method'), args=[]))`。
- 提交：`3827304`

### 错误 12 — `a, b = (d := f())` 丢失 tuple unpack
- 测试：`test_adv10_walrus_tuple_unpack.py`
- 根因：tuple unpack `a, b = (d := f())` 中右值为 walrus 表达式时，反编译器只保留 walrus 绑定 `d = f()`，完全丢失 tuple unpack 的 `UNPACK_SEQUENCE` 和两个 `STORE_NAME a, STORE_NAME b` 指令。原始字节码使用 `COPY` 复制栈顶值同时供 walrus 存储（`STORE_NAME d`）和 unpack（`UNPACK_SEQUENCE 2, STORE_NAME a, STORE_NAME b`）使用，反编译器只识别了 walrus 部分，把后续 unpack 序列当作冗余 cleanup 丢弃。
- 修复：扩展 walrus 整合路径，识别 `COPY 1 + STORE_*`（walrus 绑定）后跟 `UNPACK_SEQUENCE N + STORE_* x N`（tuple unpack 目标）的复合模式，归约为 `Assign(targets=[Tuple([Name('a'), Name('b')])], value=NamedExpr(target=Name('d'), value=Call(Name('f'))))`。
- 提交：`3827304`

### 错误 13 — `yield a if cond else b` 退化为裸 Expr
- 测试：`test_adv10_yield_ternary.py`
- 根因：`yield` 语句的值为三元表达式 `yield a if cond else b` 时，反编译器将三元作为裸 `Expr` 语句输出，丢失 `yield` 关键字。原始字节码包含 `YIELD_VALUE` 指令将三元结果作为生成器输出，反编译器将其替换为 `POP_TOP`，同时丢失 `RETURN_GENERATOR` 标记指令，导致函数从生成器退化为普通函数，语义彻底错误。
- 修复：识别三元 merge_block 后跟 `YIELD_VALUE` 的模式，归约为 `Expr(value=Yield(value=IfExp(...)))`，保留生成器语义。
- 提交：`3827304`

### 错误 14 — `yield from (a if cond else b)` 拆为裸 Expr + 错误的 yield from
- 测试：`test_adv10_yieldfrom_ternary.py`
- 根因：`yield from (三元)` 语句中，反编译器将三元拆分为两个独立语句：一条裸 `Expr` 三元和一条 `yield from a`（仅使用三元的 then 分支变量 `a`）。原始字节码中 `GET_YIELD_FROM_ITER` 应作用于三元 merge 后的结果，反编译器未将三元与 yield from 关联，反而引入额外的 `LOAD_GLOBAL a` 重新加载 then 分支变量，导致指令数从 17 增至 19 且语义错误（else 分支 `b` 完全丢失）。
- 修复：识别三元 merge_block 后跟 `GET_YIELD_FROM_ITER + LOAD_CONST + YIELD_VALUE + RESUME + JUMP_BACKWARD_NO_INTERRUPT` 的 yield-from 协程模式，归约为 `Expr(value=YieldFrom(value=IfExp(...)))`，三元作为整体传入 yield from。
- 提交：`3827304`

## 最终回归结果

### R10 全部 14 个错误（逐个验证）
```
41 passed, 1 skipped in 5.21s
```
14 个错误对应的测试全部通过；1 skipped 为 `test_adv10_match_mapping_rest.py`（match mapping `**rest` 的捕获名覆盖已存在变量名，是 framework 误判为已知限制的真实 bug，不计入本轮 14 个错误范围）。

### IF 区域全量回归
```
1 failed, 605 passed, 3 skipped in 4.70s
```
- 唯一失败：`test_adv03_nested_ternary_chain`（legacy，R8 开始前就已失败，不在本轮 14 个错误范围内）
- R10 修复前基线：605 - 14 = 591 passed / 1 legacy failed / 3 skipped
- R10 修复后：605 passed / 1 legacy failed / 3 skipped（14 个错误全部修复）

### 跨区域验证（control_flow_matrix）
```
4 failed, 323 passed, 11 skipped in 2.06s
```
- 与 R9 基线完全一致（323 passed / 4 failed / 11 skipped），未引入任何跨区域回退。
- 4 个失败均为既有问题（`TestL12WhileBreakContinue` / `TestN11TryWhileContinue` / `TestCF2WhileIfBreakContinue` 的 Break/Continue 结构识别 + `TestXP04BoolOpInIf` 的 BoolOp 节点），与本轮 IF 区域修复无关。

## 修复策略归纳

本轮 14 个错误的根因集中在五类 AST 重建 / 区域分析源问题，全部在归约源头修复：

1. **三元表达式作语句关键字参数被丢失**（err2, err4, err7, err8, err9, err10, err11, err13, err14，共 9 个）：`assert/yield/await/raise/lambda default/f-string value/method-chain/yield-from` 等场景下，当三元表达式作为这些语句的关键参数时，反编译器统一退化为裸 `Expr` 语句，丢失语句关键字与 `RAISE_VARARGS`/`YIELD_VALUE`/`FORMAT_VALUE`/`GET_AWAITABLE`/`MAKE_FUNCTION`/`LOAD_METHOD+CALL`/`GET_YIELD_FROM_ITER` 等关键指令。修复方式是在语句归约阶段识别三元 merge_block 后跟特定关键字指令的模式，统一归约为带 `IfExp` 子树的对应语句节点（`Assert` / `Raise` / `Yield` / `YieldFrom` / `Await` / `Lambda` / `JoinedStr` / `Call`），不拆分为独立 Expr。

2. **assert BoolOp 条件被错误拆分**（err1，1 个）：`assert a > 0 and b > 0, "msg"` 中 BoolOp 的 `JUMP_IF_FALSE_OR_POP` 串联被误识别为 assert 的 cleanup else 边界，导致拆分为多条 assert。修复方式是识别 BoolOp 整体性，保留 `BoolOp(And, [cmp1, cmp2])` 作为 assert 的 test。

3. **augassign in-place BINARY_OP 识别失败**（err3，1 个）：`x += a and b` 中 in-place `BINARY_OP(+=)` 紧跟 `JUMP_IF_FALSE_OR_POP` 后的 BoolOp，反编译器未识别 in-place 操作码，整体作为普通赋值。修复方式是检测 `BINARY_OP` arg 是否为 in-place 编码，即使在 BoolOp 之后也保留 augassign 语义。

4. **dictcomp walrus key/value 切分错误**（err5，1 个）：`{(x := k): v}` 中 walrus STORE_* 被无差别过滤，且无条件包装到 value_expr，导致 walrus 从 key 移到 value。修复方式是识别 walrus 副作用块（`COPY 1 + STORE_*`），保留 walrus store 在切分结果中，由 expr_reconstructor 统一产出 NamedExpr；并补充 `_get_stack_delta` 的 `COPY` case 修正栈深度计算。

5. **f-string 纯表达式 format_spec 包装缺失**（err6，1 个）：`f"{y:{width}}"` 中 format_spec 是纯 `FormattedValue`（无字面量后缀），未包装为 `JoinedStr`，导致 code_generator 渲染为嵌套 f-string。修复方式是 FORMAT_VALUE 处理器在 format_spec 既非 JoinedStr 也非 Constant(str) 时，包装为 `JoinedStr(values=[format_spec_node])`，匹配 Python AST 语义。

所有修复均泛化为模式识别，不针对特定测试用例硬编码，不依赖跨区域信息，无硬编码深度限制。0 跳过。
