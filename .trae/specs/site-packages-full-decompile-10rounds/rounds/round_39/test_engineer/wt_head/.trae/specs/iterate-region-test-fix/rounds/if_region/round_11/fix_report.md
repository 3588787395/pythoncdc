# IF 区域 Round 11 修复报告

- 修复日期：2026-07-18
- 修复工程师：Repair Engineer (Round 11)
- 测试发现文档：`test_findings.md`（同目录）
- 确认错误数：**28**，已修复：**27/28**（1 跳过：bytes_in_cond）
- 修复文件（累计全部 9 个批次）：
  - `core/cfg/region_ast_generator.py`（三元作语句参数 / 三元作 if 条件子表达式 / for 复杂 target / augassign 复杂目标 / class 三元基类 / lambda 装饰器 / 多目标解包 / 分组 boolop / while walrus boolop）
  - `core/cfg/region_analyzer.py`（augassign in-place 模式识别 / ann_assign SETUP_ANNOTATIONS）
  - `core/cfg/comprehension_generator.py`（async comprehension）
  - `core/cfg/code_generator.py`（多目标链式赋值渲染）
- 约束遵守：未在 `code_generator.py` 内做后处理补丁（仅多目标链式赋值的渲染路径，属正常代码生成）；所有修复落在区域分析 / AST 重建源头；无跨区域特殊分支；无硬编码深度限制

## 区域归约算法四原则遵守

1. **自底向上归约**：每个修复在区域分析（`region_analyzer` 的 augassign in-place 模式、ann_assign SETUP_ANNOTATIONS 识别）或 AST 重建阶段（`region_ast_generator` 的 `_generate_ternary` / `_try_build_ternary_as_if_cond` / `_loop_generate_for` target 构建 / `_build_function_def` 装饰器与注解 / `_build_boolop_expression` 分组检测 / `_loop_extract_self_loop_stmts` walrus 栈模拟）按模式自底向上识别，先识别内层表达式（三元 / walrus / 嵌套 target）再归约为语句或表达式子树。
2. **每个块唯一归属**：三元作语句参数命中后即 `return` 并标记 `generated_blocks`；for 循环复杂 target 通过 `for_target_consumed_offsets` 元数据记录被消费指令偏移，在 body 生成时跳过；walrus 回边条件重检的 COPY+STORE 由栈模拟排除出 body，不重复归属。
3. **嵌套即抽象节点**：三元作装饰器 / kwonly 默认值 / 返回注解 / class 基类归约为对应 `FunctionDef` / `ClassDef` 节点的子树（`decorator_list` / `kw_defaults` / `returns` / `bases` 含 `IfExp`）；分组 boolop `(a or b) and (c or d)` 归约为嵌套 `BoolOp(And, [BoolOp(Or, [a,b]), BoolOp(Or, [c,d])])`；while 条件 walrus 保留为 `NamedExpr` 子树挂在 `BoolOp.values`，不拆分为独立赋值。
4. **父区域引用子区域入口**：IF 区域通过子块入口生成 body，全部修复点在 body 块的语句归约层或表达式重建层，不影响 IF 区域对子块入口的引用关系；BoolOpRegion / TernaryRegion / LoopRegion 的入口仍由父区域引用。

## 批次与提交记录

| 批次 | 错误（test_findings 编号） | 提交 | 摘要 |
|------|------|------|------|
| Batch 1 | err 1-4 | `bd4ddb3` | 三元作装饰器 / 装饰器参数 / kwonly 默认值 / 返回注解（4 个） |
| Batch 2 | err 5-8 | `5d823e0` | 三元作 if 条件子表达式：walrus / subscr / call（4 个） |
| Batch 3 | err 9-12 | `791dd3d` | for 循环复杂 target：属性 / 下标 / starred / 多属性（4 个） |
| Batch 4-5 | err 13-15, 18-19, 25(skip), 26 | `2ce71a7` | augassign 复杂目标 + AnnAssign 属性/下标 + class 三元基类 + bytes 跳过（6 修复 + 1 跳过） |
| Batch 6 | err 20-21, 27 | `cbd9797` | lambda 装饰器 + 相对导入（3 个） |
| Batch 7 | err 16-17 | `010dbde` | 多目标链式解包赋值（2 个） |
| Batch 8 | err 24 | `c00b87f` | starred 集合字面量作 in 容器（1 个） |
| Batch 9 | err 22-23 | `b14bdd3` | while walrus boolop + 分组 boolop 条件（2 个，本轮修复） |

## 逐错误修复详情

### 错误 01 — `@(dec1 if c2 else dec2)` 三元作装饰器
- 测试：`test_adv11_ternary_decorator.py`
- 根因：装饰器表达式本身为三元 `IfExp` 时，`_build_function_def` 完全丢失整个装饰器（包括 `@` 调用与 `STORE_NAME`），只剩孤立的 `MAKE_FUNCTION`。
- 修复：扩展 `_generate_ternary` 的 MAKE_FUNCTION 检测，处理 flag 0 + CALL after MAKE_FUNCTION 的装饰器模式；`_build_function_def` 的 `decorator_list` 支持任意表达式（含 `IfExp`）。
- 提交：`bd4ddb3`

### 错误 02 — `@dec(a if c2 else b)` 三元作装饰器参数
- 测试：`test_adv11_ternary_decorator_arg.py`
- 根因：装饰器调用 `dec(ternary)` 的实参为三元时，反编译器丢失全部装饰逻辑。
- 修复：扩展 `_generate_ternary` 检测 flag 0 + CALL before+after MAKE_FUNCTION 的装饰器参数模式。
- 提交：`bd4ddb3`

### 错误 03 — `def f(*, x=a if c2 else b)` kwonly 默认值为三元
- 测试：`test_adv11_ternary_kwonly_default.py`
- 根因：函数 kw-only 参数默认值为三元时，`BUILD_CONST_KEY_MAP` 构造的默认值字典被丢失，函数签名变成 `def f(*, x)`。
- 修复：扩展 `_generate_ternary` 的 MAKE_FUNCTION 检测处理 flag 2 (kw_defaults)，从 `BUILD_CONST_KEY_MAP + LOAD_CONST (tuple)` 提取 kw arg 名构造 Dict 节点。
- 提交：`bd4ddb3`

### 错误 04 — `def f() -> (a if c2 else b)` 返回注解为三元
- 测试：`test_adv11_ternary_return_ann.py`
- 根因：函数返回类型注解为三元时，`BUILD_TUPLE` 单元素元组作为返回注解被丢失，函数签名变为 `def f()`。
- 修复：扩展 `_generate_ternary` 处理 flag 4 (annotations)，从 cond_block preload 提取注解键名（如 'return'）构造 annotations dict；`_build_function_def` 处理 `func_obj['annotations']` 提取 'return' 注解为 `returns` 字段。
- 提交：`bd4ddb3`

### 错误 05 — `if (n := a if b else c):` walrus + 三元作 if 条件
- 测试：`test_adv11_walrus_ternary_if_cond.py`
- 根因：if 条件为 walrus 赋值且其值表达式为三元时，反编译器将 if 退化为单条赋值 `n = (a if b else c)`，丢失 `if` 关键字。
- 修复：新增 `_try_build_ternary_as_if_cond` 方法，检测 ternary 作为 if 条件子表达式的 walrus 消费模式（COPY + STORE_NAME → NamedExpr）。
- 提交：`5d823e0`

### 错误 06 — `if (n := (a if b else c if d else e)):` 嵌套三元 + walrus
- 测试：`test_adv11_nested_ternary_walrus_cond.py`
- 根因：与错误 05 同根因，但三元为嵌套形式。
- 修复：同错误 05，`_try_build_ternary_as_if_cond` 不限制三元嵌套深度。
- 提交：`5d823e0`

### 错误 07 — `if x[a if b else c]:` 三元在下标作 if 条件
- 测试：`test_adv11_ternary_subscr_in_cond.py`
- 根因：if 条件的下标表达式 `x[ternary]` 中包含三元时，反编译器丢失外层 `x[...]` 下标与整个 if 语句。
- 修复：`_try_build_ternary_as_if_cond` 检测 subscr 消费模式（BINARY_SUBSCR → Subscript），保留外层下标与 if 语句。
- 提交：`5d823e0`

### 错误 08 — `if f(a if b else c):` 三元在调用参数作 if 条件
- 测试：`test_adv11_ternary_call_arg_in_cond.py`
- 根因：if 条件的函数调用实参为三元时，反编译器将 if 退化为裸 `Expr` 语句。
- 修复：`_try_build_ternary_as_if_cond` 检测 call 消费模式（PRECALL + CALL → Call），保留外层调用与 if 语句。
- 提交：`5d823e0`

### 错误 09 — `for x.a in pairs:` 属性 target
- 测试：`test_adv11_for_attr_target.py`
- 根因：for 循环 target 为属性 `x.a` 时，反编译器将 target 变成 `Name(a)`，`x` 误解为循环体 Expr。
- 修复：重构 `_loop_generate_for` 的 target 构建循环，识别 `LOAD obj; STORE_ATTR` → `Attribute(value, attr, ctx=Store)`；新增 `for_target_consumed_offsets` 元数据避免 body 重复发射。
- 提交：`791dd3d`

### 错误 10 — `for x[0] in pairs:` 下标 target
- 测试：`test_adv11_for_subscr_target.py`
- 根因：for 循环 target 为下标 `x[0]` 时，反编译器产生语法错误（target 误识别为 `None`）。
- 修复：识别 `LOAD obj, LOAD key; STORE_SUBSCR` → `Subscript(value, slice, ctx=Store)`。
- 提交：`791dd3d`

### 错误 11 — `for *a, b in pairs:` starred target
- 测试：`test_adv11_for_starred_target.py`
- 根因：for 循环 target 含 starred `*a` 时，反编译器丢失 starred 标记，`UNPACK_EX` 被当作 `UNPACK_SEQUENCE`。
- 修复：识别 `UNPACK_EX`（含 `EXTENDED_ARG`）→ 含 `Starred` 节点的 Tuple target。
- 提交：`791dd3d`

### 错误 12 — `for x.a, y.b in pairs:` 多属性 target
- 测试：`test_adv11_for_multi_attr_target.py`
- 根因：for 循环 target 为多属性 `x.a, y.b` 时，反编译器丢失属性目标，`y` 泄漏到循环体。
- 修复：嵌套 `UNPACK_SEQUENCE` 内组合 Attribute / Subscript / Starred 的统一识别。
- 提交：`791dd3d`

### 错误 13 — `x.y += a and b` augassign 属性目标 + boolop 右值
- 测试：`test_adv11_augassign_attr_boolop.py`
- 根因：augassign 目标为属性 `x.y`、右值为 boolop 时，反编译器丢失 augassign 语义与目标，只剩 boolop Expr。
- 修复：识别 `LOAD_ATTR + BINARY_OP(in-place) + SWAP + STORE_ATTR` 的 augassign 属性目标模式，保留 in-place 操作码与 boolop 右值。
- 提交：`2ce71a7`

### 错误 14 — `x[0] += a and b` augassign 下标目标 + boolop 右值
- 测试：`test_adv11_augassign_subscr_boolop.py`
- 根因：与错误 13 同根因，但目标是下标 `x[0]`。
- 修复：识别 `BINARY_SUBSCR + BINARY_OP(in-place) + SWAP + STORE_SUBSCR` 的 augassign 下标目标模式。
- 提交：`2ce71a7`

### 错误 15 — `x[0] += a if b else c` augassign 下标目标 + 三元右值
- 测试：`test_adv11_augassign_subscr_ternary.py`
- 根因：augassign 下标目标 + 三元右值时，反编译器输出 `x[0][ternary] = 0`，完全错乱。
- 修复：Pattern C 检测 `BINARY_OP(arg>=13) + SWAP` 后缀，重建 Subscript/Attribute target for ternary augassign rhs。
- 提交：`2ce71a7`

### 错误 16 — `a, b = e, f = g, h` 多目标元组解包
- 测试：`test_adv11_multi_target_unpack.py`
- 根因：多目标元组解包反编译时丢失中间目标 `e, f`，只剩首个目标 `(a, b)` 与最后值 `(g, h)`。
- 修复：新增 `_build_multi_target_unpack` 检测 `COPY 1` 紧跟 `UNPACK_SEQUENCE` 的多目标解包模式，发射带 `is_chain_assign=True` 标志的 Assign 节点，触发 CodeGenerator 链式赋值渲染。
- 提交：`010dbde`

### 错误 17 — `a, b = c = d, e` 多目标混合解包
- 测试：`test_adv11_multi_target_mixed_unpack.py`
- 根因：与错误 16 同根因，多目标解包 `a, b = c = d, e` 丢失中间标量目标 `c`。
- 修复：同错误 16，`_build_multi_target_unpack` 通用化支持混合 unpack/name 目标。
- 提交：`010dbde`

### 错误 18 — `x.y: int = 1` AnnAssign 属性目标
- 测试：`test_adv11_ann_assign_attr_target.py`
- 根因：AnnAssign 的 target 为属性 `x.y` 时，反编译器拆成 `Assign(x.y = 1)` + `Expr(int)`，丢失 `SETUP_ANNOTATIONS`。
- 修复：识别 `SETUP_ANNOTATIONS` + `STORE_ATTR` 模式，归约为 `AnnAssign(target=Attribute(...), annotation=Name('int'), value=Constant(1))`。
- 提交：`2ce71a7`

### 错误 19 — `x[0]: int = 1` AnnAssign 下标目标
- 测试：`test_adv11_ann_assign_subscr_target.py`
- 根因：与错误 18 同根因，但 target 是下标 `x[0]`。
- 修复：识别 `SETUP_ANNOTATIONS` + `STORE_SUBSCR` 模式，归约为 `AnnAssign(target=Subscript(...), ...)`。
- 提交：`2ce71a7`

### 错误 20 — `@lambda f: None` lambda 装饰器
- 测试：`test_adv11_lambda_decorator.py`
- 根因：装饰器为 lambda 表达式时，反编译器把 lambda body 错填 `False`、参数填 `*args, **kwargs`，丢失被装饰函数。
- 修复：CALL 处理器增加 FunctionObject 装饰器分支（栈顶两个 FO 时下方为装饰器）；`_extract_decorators` 扩展支持任意表达式（Lambda/FunctionObject）作为装饰器。
- 提交：`cbd9797`

### 错误 21 — `@(lambda f: lambda *a, **k: f(*a, **k))` 嵌套 lambda 装饰器
- 测试：`test_adv11_decorator_lambda_with_args.py`
- 根因：与错误 20 同根因，但装饰器是带嵌套 lambda 的复杂形式。
- 修复：同错误 20，lambda 装饰器处理不限于简单 lambda。
- 提交：`cbd9797`

### 错误 22 — `while (x := f()) and g():` walrus + boolop 作 while 条件【本轮修复】
- 测试：`test_adv11_while_walrus_boolop.py`
- 源码：
  ```python
  if c:
      while (x := f()) and g():
          pass
  ```
- 失败信息：`AssertionError: 指令数不匹配: 32 vs 37`
- 反编译输出（修复前）：
  ```python
  if c:
      while (x := f()) and g():
          x = f()
  ```
- 根因分析：当 while 条件为 `(x := f()) and g()` 时，反编译器在循环体中凭空插入一条 `x = f()` 赋值语句。原始字节码循环体仅 `pass`（`LOAD_CONST None; RETURN_VALUE`），反编译后多出 `LOAD_NAME f; PRECALL; CALL; COPY; STORE_NAME x`。

  精确定位：`_loop_extract_self_loop_stmts` 的 `FORWARD_CONDITIONAL_JUMP_OPS` 分支在检测到 walrus store（`COPY 1 + STORE_*`）时，把 `_body_end_idx` 设为 `_walrus_store_idx`（walrus STORE 的索引）。这导致迭代循环在 `_sli_idx <= _body_end_idx` 时处理 walrus STORE 指令，`_build_store_statement` 把累积的 `LOAD_NAME f, PRECALL, CALL, COPY, STORE_NAME x` 重建为独立 `Assign(x, f())`。

  对比 `BACKWARD_CONDITIONAL_JUMP_OPS` 分支（`while (x := f()):` 通过）：该分支在 walrus 检测失败后回退到栈模拟，从末尾指令反向累积栈效应，当 `stack_depth <= 0` 时把 `_body_end_idx = _sli - 1`（walrus 值计算起点之前），正确排除整个 walrus 序列。

  字节码结构（`if c:` 包裹下）：
  ```
  block@50 (LOOP_HEADER, 回边条件重检):
    NOP, PUSH_NULL, LOAD_NAME f, PRECALL, CALL, COPY 1, STORE_NAME x, POP_JUMP_FORWARD_IF_FALSE 108
  ```
  walrus `(x := f())` 的 `LOAD/CALL/COPY/STORE` 是回边条件重检的一部分，不应作为 body 语句输出。
- 修复：在 `FORWARD_CONDITIONAL_JUMP_OPS` 分支的 `_walrus_store_idx >= 0` 子分支，用栈模拟（与 `BACKWARD_CONDITIONAL_JUMP_OPS` 分支一致）找到 walrus 值计算起点，把 `_body_end_idx` 设到起点之前。
- 关键代码（`core/cfg/region_ast_generator.py` `_loop_extract_self_loop_stmts`）：
  ```python
  if _walrus_store_idx >= 0:
      # [R11-err8] walrus (COPY 1 + STORE_*) 是回边条件重检的一部分，
      # 不应作为 body 语句输出。需要用栈模拟找到 walrus 值计算的起点，
      # 把 _body_end_idx 设到该起点之前（与 BACKWARD 分支一致）。
      _cond_break_start_idx = _walrus_store_idx + 1
      stack_depth = 0
      for _sli in range(len(hdr.instructions) - 1, -1, -1):
          _sl_instr = hdr.instructions[_sli]
          try:
              effect = _dis.stack_effect(_sl_instr.opcode, _sl_instr.arg)
          except Exception:
              effect = 0
          stack_depth -= effect
          if stack_depth <= 0:
              _body_end_idx = _sli - 1
              break
      if _body_end_idx is None:
          _body_end_idx = _walrus_store_idx - 1
  ```
- 验证：`test_adv11_while_walrus_boolop` 通过；`test_adv11_while_walrus_only`（`while (x := f()):` 无 boolop）仍通过；`test_adv01_walrus_and` / `test_adv02_walrus_and_reuse` 等 11 个 boolop+walrus 相关测试仍通过。
- 提交：`b14bdd3`

### 错误 23 — `if (a or b) and (c or d):` 分组 boolop 丢失括号【本轮修复】
- 测试：`test_adv11_grouped_boolop_cond.py`
- 源码：
  ```python
  if (a or b) and (c or d):
      pass
  ```
- 失败信息：`AssertionError: 指令数不匹配: 11 vs 9`
- 反编译输出（修复前）：
  ```python
  if (a or b and c or d):
      pass
  ```
- 根因分析：`_build_boolop_expression` 的 `or_groups` 算法把所有操作数平坦化后按 Python 优先级分组（and 绑定比 or 紧）。对于 `(a or b) and (c or d)`，平坦化得到 `[a, b, c, d]` 与 ops `[or, and, or]`，`or_groups` 按 and/or 转换分组为 `or[a, and[b, c], d]`，即 `a or (b and c) or d`，与原始 `(a or b) and (c or d)` 语义完全不同（括号丢失导致运算符优先级改变）。

  关键观察：平坦的 `a or b and c or d` 中，每个链块的短路跳转目标都指向链外（body/else/merge）。而括号化的 `(a or b) and (c or d)` 中，`block@0 (or)` 的 `IF_TRUE` 跳转目标是 `block@10`（另一个链块）——因为 `(a or b)` 是自包含子组，a 为真时跳到下一组 `(c or d)` 继续求值，而非直接跳到 body。因此「跳转目标 ∈ 链块集合」是内层操作符的可靠信号。
- 修复：新增两个方法：
  1. `_detect_boolop_grouping`：检测链块短路跳转目标是否指向另一个链块（自包含子组信号）。遍历 op_chain，对每个非末尾链块检查其末尾跳转指令的目标是否在链块集合内。若是，标记为 INNER 并记录内层操作符类型。外层操作符通过互斥推导（内层全为 or → 外层是 and；内层全为 and → 外层是 or；混合则回退）。每个链块分类为 INNER / OUTER / LAST。
  2. `_build_grouped_boolop_expression`：按分类重建嵌套 BoolOp。遍历 op_chain，INNER 块加入当前内层组，OUTER/LAST 块结束内层组（>1 值则嵌套 BoolOp）并作为外层操作数。最终 `BoolOp(outer_op, [外层操作数...])`。

  在 `_build_boolop_expression` 入口先调用分组检测，命中则用分组重建，失败回退 `or_groups` 算法。
- 关键代码（`core/cfg/region_ast_generator.py`）：
  ```python
  # [R11-err2] 显式分组（括号化的 and/or 组合）检测：
  _has_grouping, _group_outer_op, _group_classifications = self._detect_boolop_grouping(region, op_chain)
  if _has_grouping:
      _grouped_result = self._build_grouped_boolop_expression(
          region, op_chain, _group_outer_op, _group_classifications)
      if _grouped_result is not None:
          return _grouped_result
      # 分组重建失败时回退到 or_groups 算法
  ```
- 验证：`test_adv11_grouped_boolop_cond` 通过；`test_adv01_walrus_and` / `test_adv02_walrus_or_reuse` / `test_adv02_multi_walrus_and` 等 11 个 boolop 相关测试仍通过（平坦 boolop 不触发分组检测，走原 `or_groups` 路径）。
- 提交：`b14bdd3`

### 错误 24 — `if c in {*a, *b}:` starred 集合字面量作 in 容器
- 测试：`test_adv11_starred_set_in_cond.py`
- 根因：if 条件为 `c in {*a, *b}`（含 starred 元素的集合字面量）时，反编译器丢失 starred 集合字面量，把 `a` 误当作容器。
- 修复：在 `ExpressionReconstructor._process_instruction` 添加 `SET_UPDATE` 指令处理器。`SET_UPDATE` 把可迭代对象元素加入集合：Tuple/List 展开 elts 加入 Set.elts；Constant frozenset 展开常量元素；其他（Name/Call/...）归约为 Starred 节点追加到 Set.elts。同步为 `_process_instruction_sequence` 的 SET_UPDATE 添加 Starred 分支。
- 提交：`c00b87f`

### 错误 25 — `if b"abc":` bytes 字面量作 if 条件【跳过】
- 测试：`test_adv11_bytes_in_cond.py`
- 根因：if 条件为 bytes 字面量 `b"abc"` 时，反编译器完全丢失整个 if 语句，只剩孤立的 `pass`。CPython 3.11 peephole 优化器对 `if b"abc":` 进行常量折叠（`b"abc"` 永远为真），编译后的字节码中没有 `POP_JUMP_FORWARD_IF_FALSE` 条件跳转，反编译器无法从字节码恢复原始 if 语句。
- 跳过原因：这是 CPython 编译器的常量折叠优化，原始 `if b"abc":` 与 `pass`（直接执行 body）在字节码层面完全等价。反编译器无法区分「用户写的 `if b"abc":`」与「编译器优化掉的常量条件」，属于编译器有损转换，不是反编译器 bug。
- 提交：`2ce71a7`（标记为 skip）

### 错误 26 — `class C(A if c2 else B):` class 三元基类
- 测试：`test_adv11_class_ternary_base.py`
- 根因：class 的基类为三元 `IfExp` 时，反编译器输出原始 `__build_class__` 调用形式，`<CodeObject>` 占位符导致语法错误。
- 修复：检测 `LOAD_BUILD_CLASS + MAKE_FUNCTION` 在 ternary cond_block preload 中，构造 `__build_class__` Call with FunctionObject + ternary base，归约为 `ClassDef(name='C', bases=[IfExp(...)])`。
- 提交：`2ce71a7`

### 错误 27 — `from . import a` 相对导入
- 测试：`test_adv11_relative_import.py`
- 根因：if body 中包含相对导入 `from . import a` 时，反编译器丢失模块路径 `.`，输出 `from  import a`（模块名空白），语法错误。
- 修复：`IMPORT_NAME` 向前查找 `LOAD_CONST` 获取 level，构造 `module_path = '.' * level + module_name`，修复 `from . import a`。
- 提交：`cbd9797`

### 错误 28 — `x = [i async for i in y]` async comprehension 在 if body
- 测试：`test_adv11_async_comp.py`
- 根因：if body 中包含 async list comprehension `[i async for i in y]` 时，反编译器完全丢失 comprehension 表达式，替换为 `None`。
- 修复：`comprehension_generator.py` 识别 async comprehension 模式（`GET_AITER` / `GET_AWAITABLE` / `YIELD_VALUE` / `JUMP_BACKWARD_NO_INTERRUPT`），重建 `ListComp(elt=Name('i'), generators=[comprehension(is_async=1, target=Name('i'), iter=Name('y'))])`。
- 提交：`2ce71a7`

## 最终回归结果

### R11 全部 28 个错误（逐个验证）
```
44 passed, 1 skipped in 3.17s
```
27 个错误对应的测试全部通过；1 skipped 为 `test_adv11_bytes_in_cond.py`（CPython 3.11 常量折叠，编译器有损转换，非反编译器 bug）。

### IF 区域全量回归
```
3 failed, 647 passed, 4 skipped in 5.38s
```
- 3 个失败均为既有问题（`test_adv03_nested_ternary_chain` / `test_adv03_ternary_call_arg` / `test_adv03_ternary_in_subscr`，legacy 三元嵌套链问题，R11 之前就已失败，不在本轮 28 个错误范围内）。
- R11 修复前基线：645 passed / 5 failed（含 R11 的 err 22 + err 23）/ 4 skipped
- R11 修复后：647 passed / 3 failed（legacy）/ 4 skipped（27 个错误全部修复，1 个跳过）

### 跨区域验证（control_flow_matrix）
```
4 failed, 323 passed, 11 skipped in 2.28s
```
- 与 R10 基线完全一致（323 passed / 4 failed / 11 skipped），未引入任何跨区域回退。
- 4 个失败均为既有问题（`TestL12WhileBreakContinue` / `TestN11TryWhileContinue` / `TestCF2WhileIfBreakContinue` 的 Break/Continue 结构识别 + `TestXP04BoolOpInIf` 的 BoolOp 节点），与本轮 IF 区域修复无关。

## 本轮修复（Batch 9）策略归纳

本轮修复的 2 个错误根因集中在两类 AST 重建源问题，全部在归约源头修复：

1. **分组 boolop 括号丢失**（err 23，1 个）：`(a or b) and (c or d)` 中，`or_groups` 平坦化算法按 Python 优先级重新分组，丢失显式括号语义。修复方式是基于跳转目标分析检测自包含子组（链块的短路跳转目标指向另一个链块），按 INNER/OUTER/LAST 分类重建嵌套 BoolOp 保留括号结构。失败时回退 `or_groups` 算法，不影响平坦 boolop。

2. **while 条件 walrus 被重复生成为 body 语句**（err 22，1 个）：`while (x := f()) and g():` 中，回边条件重检块（LOOP_HEADER）的 walrus `COPY 1 + STORE_*` 被 `_loop_extract_self_loop_stmts` 的 FORWARD 分支错误包含进 `_body_end_idx`，导致 walrus 序列被 `_build_store_statement` 重建为独立 `x = f()` 赋值。修复方式是用栈模拟（与 BACKWARD 分支一致）找到 walrus 值计算起点，把 `_body_end_idx` 设到起点之前，正确排除整个 walrus 序列。

所有修复均泛化为模式识别（跳转目标分析 / 栈模拟），不针对特定测试用例硬编码，不依赖跨区域信息，无硬编码深度限制。1 跳过（bytes_in_cond，CPython 编译器有损转换）。
