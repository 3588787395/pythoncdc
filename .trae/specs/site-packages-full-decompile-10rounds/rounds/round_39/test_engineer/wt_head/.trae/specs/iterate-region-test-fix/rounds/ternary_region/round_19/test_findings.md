# Ternary Round 19 测试发现

## 基线
- ternary: 45 failed / 513 passed / 9 skipped
  （运行 `timeout 280 python -m pytest tests/exhaustive/ternary/ -q --tb=no` 验证）
- 添加 R19 测试后: 59 failed / 513 passed / 9 skipped
  （14 个新测试全部真实失败，无 PASS / SKIP 误判，差值精确匹配 45 + 14 = 59）

## 调试产物
- 探索脚本: `/workspace/.trae/specs/iterate-region-test-fix/rounds/ternary_region/round_19/_explore.py`
  （批量验证 55 个候选模式，定位真实字节码 diff，筛出 14 个真实失败）

## 发现的 bug（14 个）

### Bug R19-01: try-finally 的 finally 体含 raise E(ternary)
- 测试文件: `tests/exhaustive/ternary/test_r19_ternary_try_finally_raise.py`
- 源码:
  ```python
  def f():
      try:
          x = 1
      finally:
          raise E(a if c else b)
  ```
- 失败原因: finally 清理块内 `raise E(a if c else b)` —— ternary 是 raise 调用
  E(...) 的位置参数，整体位于 try-finally 的 finally 异常清理路径中。R14
  finally_body 测过 `finally: x = (ternary)` (assign)，R14 raise_arg 测过
  `raise E(ternary)` (非 finally 上下文)。本用例 finally 块的 PUSH_EXC_INFO +
  POP_EXCEPT + RERAISE 清理链与 ternary merge 块的 PRECALL+CALL+RAISE_VARARGS
  消费链归属冲突，反编译把 raise 误移入 try 体并退化为
  `try: ... raise E(a if c else b) except: pass`，丢失 finally 块结构。
- 验证: FAILED `嵌套code object不匹配 (指令1): 指令数不匹配: 21 vs 18`
  原始: `['RESUME', 'LOAD_CONST', 'STORE_FAST', 'LOAD_GLOBAL'×4, 'PRECALL', 'CALL', 'RAISE_VARARGS', 'PUSH_EXC_INFO', 'LOAD_GLOBAL'×4, 'PRECALL', 'CALL', 'RAISE_VARARGS', 'COPY', 'POP_EXCEPT', ...]`
  重编: `['RESUME', ..., 'RAISE_VARARGS', 'PUSH_EXC_INFO', 'POP_TOP', 'POP_EXCEPT', 'LOAD_CONST', 'RETURN_VALUE', 'COPY', 'POP_EXCEPT', 'RERAISE']`

### Bug R19-02: with ctx() as cm[(ternary)] — ternary 作 with as-target 的 subscript 下标
- 测试文件: `tests/exhaustive/ternary/test_r19_ternary_with_as_subscr_target.py`
- 源码: `with ctx() as cm[(a if c else b)]:\n    pass`
- 失败原因: with 语句的 as-target 是 subscript 形式 `cm[(ternary)]` —— ternary 是
  下标。R3 with_as 测过 `with ctx() as (ternary)` (ternary 直接作 as-target Name)，
  R18 for_iter_subscr 测过 `for x in y[(ternary)]`。本用例 ternary 是 with as-target
  的 subscript：BEFORE_WITH + STORE_SUBSCR 消费链与 ternary merge 块归属冲突，
  反编译退化为 `with ctx(): (a if c else b)`，丢失 as-target 与 subscript 结构。
- 验证: FAILED `指令6操作码不匹配: LOAD_NAME vs POP_TOP`

### Bug R19-03: with open(t1) as f, open(t2) as h — multi-with 两个 item 均含 ternary 调用参数
- 测试文件: `tests/exhaustive/ternary/test_r19_ternary_with_multiple_both_ternary.py`
- 源码: `with open(a if c else b) as f, open(d if e else g) as h:\n    pass`
- 失败原因: multi-with 两个 with-item 的 context manager 调用 open(...) 各含一个
  ternary 位置参数。R14 with_multiple_second_as 测过 `with a as x, (ternary) as y`
  (仅第二 item 的 cm 是 ternary，第一 item cm 是常量 a)。本用例两个 item 的 cm
  都是 open(ternary) 调用：两个 ternary merge 块先后汇聚到各自 BEFORE_WITH +
  STORE_NAME，再叠加 WITH_EXCEPT_START 清理链，反编译完全丢失两个 ternary 与第二
  with-item，退化为 `with context() as f: pass` (IfExp MISSING)。
- 验证: FAILED `反编译结果中未找到预期的区域类型 TERNARY (期望AST节点: ['IfExp'])`
  反编译输出: `with context() as f: pass`

### Bug R19-04: with body 内 cm.process(t1).finalize() — ternary 作方法链参数位于 with body
- 测试文件: `tests/exhaustive/ternary/test_r19_ternary_with_body_method_chain_arg.py`
- 源码: `with ctx() as cm:\n    cm.process(a if c else b).finalize()`
- 失败原因: with body 内表达式 `cm.process(t1).finalize()` —— ternary 是中间方法
  process(...) 的位置参数，外层 .finalize() 调用消费 process 的返回值。R17
  method_arg_then_attr 测过 `obj.method(t1).other` (非 with body)，R17
  method_chain_arg_middle 测过 `s.replace('a','b').split(t1)`。本用例 ternary 在
  with body 内且外层是方法链 .process(t1).finalize()：ternary merge 块的
  PRECALL+CALL (process) + LOAD_METHOD finalize + PRECALL+CALL (finalize) 消费链
  与 with body 块归属冲突，反编译丢失外层 .finalize() 调用，退化为
  `cm.process(a if c else b)`。
- 验证: FAILED `指令数不匹配: 38 vs 35`
  原始末尾: `..., 'PRECALL', 'CALL', 'LOAD_METHOD', 'PRECALL', 'CALL', 'POP_TOP', ...`
  重编末尾: `..., 'PRECALL', 'CALL', 'POP_TOP', 'LOAD_CONST', 'LOAD_CONST', 'LOAD_CONST', 'PRECALL', 'CALL'`

### Bug R19-05: raise (t1) from (t2) — raise 的异常与 cause 均为 ternary
- 测试文件: `tests/exhaustive/ternary/test_r19_ternary_raise_from_both_ternary.py`
- 源码: `raise (a if c else b) from (d if e else f)`
- 失败原因: raise 语句的异常对象 (a if c else b) 与 cause (d if e else f) 都是
  ternary。R8 raise_from_ternary_cause 测过 `raise E from (ternary)` (异常常量，
  cause ternary)，R14 raise_ternary_type_from 测过 `raise (ternary) from E2`
  (异常 ternary，cause 常量)，R14 raise_arg_and_cause 测过 `raise E(ternary)
  from (ternary)` (异常是 E(ternary) 调用)。本用例异常本身是裸 ternary (非
  E(ternary) 调用)，且 cause 也是 ternary：两个 ternary merge 块先后汇聚到同一
  RAISE_VARARGS 2，反编译退化为两段独立表达式语句 `(t1)` 与 `(t2)`，完全丢失
  raise 语句结构。
- 验证: FAILED `指令数不匹配: 8 vs 14`
  原始: `['RESUME', 'LOAD_NAME'×6, 'RAISE_VARARGS']`
  重编: `['RESUME', 'LOAD_NAME'×3, 'POP_TOP', 'LOAD_NAME'×2, 'POP_TOP', 'LOAD_CONST', 'RETURN_VALUE', 'LOAD_NAME', 'POP_TOP', 'LOAD_CONST', 'RETURN_VALUE']`

### Bug R19-06: x, y = c, (ternary) — tuple unpack 仅一个元素为 ternary
- 测试文件: `tests/exhaustive/ternary/test_r19_ternary_tuple_unpack_one_ternary.py`
- 源码: `x, y = c, (a if d else b)`
- 失败原因: tuple unpack 赋值 RHS = (c, ternary)，仅第二个元素是 ternary，第一个
  是简单 Name c。R6 unpack_assign 测过 `x, y = (t1), (t2)` (两元素均 ternary)，
  R13 tuple_swap 测过 `x, y = (t1), (t2)` (两元素均 ternary)。本用例仅一个 ternary
  元素 + 一个常量元素：BUILD_TUPLE 2 (在 ternary merge 块之后) + UNPACK_SEQUENCE 2
  + STORE_NAME x + STORE_NAME y 消费链中，常量 c 的 LOAD_NAME 与 ternary merge
  块归属未协调，反编译退化为 `x = c`，丢失 ternary 与第二目标 y (IfExp MISSING)。
- 验证: FAILED `反编译结果中未找到预期的区域类型 TERNARY (期望AST节点: ['IfExp'])`
  反编译输出: `x = c`

### Bug R19-07: a, b, c = 1, (ternary), 2 — ternary 位于 tuple unpack 中间位置
- 测试文件: `tests/exhaustive/ternary/test_r19_ternary_tuple_unpack_middle_ternary.py`
- 源码: `a, b, c = 1, (x if d else y), 2`
- 失败原因: tuple unpack 赋值 RHS = (1, ternary, 2)，三个元素中中间是 ternary，
  前后均为常量。R6/R13 unpack 测过两元素均 ternary。本用例三目标 unpack 中 ternary
  在中间：BUILD_TUPLE 3 (在 ternary merge 块之后) + UNPACK_SEQUENCE 3 + STORE_NAME
  a/b/c 消费链中，前置 LOAD_CONST 1 与后置 LOAD_CONST 2 协调失败，反编译退化为
  `a = 2`，丢失 ternary 与中间目标 b、首元素 1 (IfExp MISSING)。
- 验证: FAILED `反编译结果中未找到预期的区域类型 TERNARY (期望AST节点: ['IfExp'])`
  反编译输出: `a = 2`

### Bug R19-08: x: (A if c else B) = None — ternary 作 annotated assignment 的注解
- 测试文件: `tests/exhaustive/ternary/test_r19_ternary_ann_assign_ternary_annotation.py`
- 源码: `x: (A if c else B) = None`
- 失败原因: annotated assignment `x: annotation = value` 的 annotation 是 ternary。
  R8 ann_assign 测过 `x: int = (ternary)` (注解常量，value ternary)，R6 annotation
  测过 `x: (ternary)` (无 value 纯注解)。本用例 annotation 是 ternary 且 value 是
  None：SETUP_ANNOTATIONS + STORE_NAME x + LOAD_CONST None + ternary merge +
  LOAD_CONST 'x' + STORE_SUBSCR (写入 __annotations__)，反编译退化为 `x = None`
  + `__annotations__['x'] = (A if c else B)` 两段独立语句，丢失 SETUP_ANNOTATIONS
  指令，字节码指令数不匹配 (12 vs 11)。
- 验证: FAILED `指令数不匹配: 12 vs 11`
  原始: `['RESUME', 'SETUP_ANNOTATIONS', 'LOAD_CONST', 'STORE_NAME', 'LOAD_NAME'×4, 'LOAD_CONST', 'STORE_SUBSCR', 'LOAD_CONST', 'RETURN_VALUE']`
  重编: `['RESUME', 'LOAD_CONST', 'STORE_NAME', 'LOAD_NAME'×4, 'LOAD_CONST', 'STORE_SUBSCR', 'LOAD_CONST', 'RETURN_VALUE']` (缺 SETUP_ANNOTATIONS)

### Bug R19-09: def f(x: (A if c else B)) — ternary 作函数参数注解
- 测试文件: `tests/exhaustive/ternary/test_r19_ternary_func_arg_ternary_annotation.py`
- 源码: `def f(x: (A if c else B)):\n    pass`
- 失败原因: 函数参数 x 的注解是 ternary。R8 annotation_default 测过
  `x: int = (ternary)` (注解常量 + 默认值 ternary)。本用例注解本身是 ternary：
  MAKE_FUNCTION 时 BUILD_TUPLE 收集注解，注解 ternary 的 merge 块在 MAKE_FUNCTION
  之前汇聚。ternary merge 块归属与函数定义的 MAKE_FUNCTION 消费链冲突，反编译
  退化为 `def f(x): return None`，完全丢失注解 ternary (IfExp MISSING)，字节码
  指令数不匹配 (11 vs 6)。
- 验证: FAILED `反编译结果中未找到预期的区域类型 TERNARY (期望AST节点: ['IfExp'])`
  反编译输出: `def f(x):\n    return None`

### Bug R19-10: (t1) < (t2) < g — 链式比较两端均为 ternary
- 测试文件: `tests/exhaustive/ternary/test_r19_ternary_chained_compare_both_ternary.py`
- 源码: `x = (a if c else b) < (d if e else f) < g`
- 失败原因: 链式比较 a < b < c 的左操作数与中操作数都是 ternary。R3/R4/R5
  chained_compare 系列测过单 ternary 在左/右/中位置，R16 chained_compare_middle
  测过 `a < (ternary) < b` (单 ternary 中间)。本用例两个 ternary 分别在左与中：
  SWAP+COPY+COMPARE_OP+JUMP_IF_FALSE_OR_POP 链式比较模板中，两个 ternary merge
  块先后汇聚，反编译退化为两段独立表达式 `(t1)` 与 `if (t2): pass`，完全丢失
  链式比较与赋值结构。
- 验证: FAILED `指令数不匹配: 18 vs 14`
  原始: `['RESUME', 'LOAD_NAME'×6, 'SWAP', 'COPY', 'COMPARE_OP', 'JUMP_IF_FALSE_OR_POP', 'LOAD_NAME', 'COMPARE_OP', 'SWAP', 'POP_TOP', 'STORE_NAME', 'LOAD_CONST', 'RETURN_VALUE']`
  重编: `['RESUME', 'LOAD_NAME'×3, 'POP_TOP', 'LOAD_NAME'×3, 'LOAD_CONST', 'RETURN_VALUE', 'LOAD_CONST', 'RETURN_VALUE', 'LOAD_CONST', 'RETURN_VALUE']`

### Bug R19-11: (t1) in (t2) — `in` 比较两端均为 ternary
- 测试文件: `tests/exhaustive/ternary/test_r19_ternary_compare_in_both_ternary.py`
- 源码: `x = (a if c else b) in (d if e else f)`
- 失败原因: 二元比较 `in` 的左右操作数都是 ternary。R5 compare_in 测过
  `(ternary) in seq` (左 ternary，右常量)，R2 contains 测过 `x in (ternary)`
  (左常量，右 ternary)。本用例两端均 ternary：COMPARE_OP (in) 消费栈顶两个
  ternary 结果，两个 ternary merge 块先后汇聚，反编译退化为两段独立表达式
  `(t1)` 与 `x = (t2)`，丢失 `in` 比较与第一 ternary。
- 验证: FAILED `指令4操作码不匹配: LOAD_NAME vs POP_TOP`

### Bug R19-12: {(t1): (t2)} — dict literal 的 key 与 value 均为 ternary
- 测试文件: `tests/exhaustive/ternary/test_r19_ternary_dict_literal_key_value_ternary.py`
- 源码: `x = {(a if c else b): (d if e else f)}`
- 失败原因: dict literal `{key: value}` 的 key 和 value 都是 ternary。R18
  dictcomp_key_value_ternary 测过 dict comprehension `{(t1): (t2) for k in y}`
  (MAP_ADD 消费)。本用例是 dict literal (BUILD_MAP 消费)：BUILD_MAP 1 消费栈顶
  value (t2) 与次栈顶 key (t1)，两个 ternary merge 块先后汇聚到同一 BUILD_MAP，
  反编译退化为独立表达式 `(t1)`，丢失 value ternary 与 dict literal 结构。
- 验证: FAILED `指令数不匹配: 11 vs 10`
  原始: `['RESUME', 'LOAD_NAME'×6, 'BUILD_MAP', 'STORE_NAME', 'LOAD_CONST', 'RETURN_VALUE']`
  重编: `['RESUME', 'LOAD_NAME'×2, 'POP_TOP', 'LOAD_CONST', 'RETURN_VALUE', 'LOAD_NAME', 'POP_TOP', 'LOAD_CONST', 'RETURN_VALUE']`

### Bug R19-13: (t1) == (t2) — `==` 比较两端均为 ternary
- 测试文件: `tests/exhaustive/ternary/test_r19_ternary_compare_eq_both_ternary.py`
- 源码: `x = (a if c else b) == (d if e else f)`
- 失败原因: 二元比较 `==` 的左右操作数都是 ternary。R1 ternary_in_compare 测过
  `(ternary) == x` (左 ternary，右常量)，R2 compare_right 测过 `x == (ternary)`
  (左常量，右 ternary)。本用例两端均 ternary：COMPARE_OP (==) 消费栈顶两个
  ternary 结果，两个 ternary merge 块先后汇聚，反编译退化为两段独立表达式
  `(t1)` 与 `x = (t2)`，丢失 `==` 比较与第一 ternary。
- 验证: FAILED `指令4操作码不匹配: LOAD_NAME vs POP_TOP`

### Bug R19-14: {1:2}.update({(t1): 3}) — dict literal 方法调用，参数是含 ternary key 的 dict
- 测试文件: `tests/exhaustive/ternary/test_r19_ternary_dict_literal_method_dict_arg.py`
- 源码: `{1: 2}.update({(a if c else b): 3})`
- 失败原因: dict literal `{1: 2}` 调用 `.update(...)`，参数是另一个 dict literal
  `{(t1): 3}` —— ternary 是参数 dict 的 key。R15 dict_literal_method 测过
  `{}.get((ternary))` (ternary 直接作 .get 的位置参数)。本用例 ternary 是 .update
  参数 dict 内部的 key：外层 BUILD_MAP (参数 dict) 消费 ternary merge 块栈顶
  (value 3) 与次栈顶 (key t1)，再被外层 LOAD_METHOD update + PRECALL+CALL 消费，
  反编译退化为 `{}.update({a if c else b: 3})`，丢失外层 dict literal 的常量键值对
  `{1: 2}`，字节码指令数不匹配 (15 vs 13)。
- 验证: FAILED `指令数不匹配: 15 vs 13`
  原始: `['RESUME', 'LOAD_CONST', 'LOAD_CONST', 'BUILD_MAP', 'LOAD_METHOD', 'LOAD_NAME'×3, 'LOAD_CONST', 'BUILD_MAP', 'PRECALL', 'CALL', 'POP_TOP', 'LOAD_CONST', 'RETURN_VALUE']`
  重编: `['RESUME', 'BUILD_MAP', 'LOAD_METHOD', 'LOAD_NAME'×3, 'LOAD_CONST', 'BUILD_MAP', 'PRECALL', 'CALL', 'POP_TOP', 'LOAD_CONST', 'RETURN_VALUE']` (缺 `LOAD_CONST, LOAD_CONST`)

## 共性根因分析

14 个 bug 可归为 5 类共性根因：

### 根因 A: 同一语句两个 ternary merge 块汇聚到单一消费指令 (5 个)
- R19-05 (raise t1 from t2 → RAISE_VARARGS 2), R19-10 (t1 < t2 < g → COMPARE_OP×2),
  R19-11 (t1 in t2 → COMPARE_OP), R19-12 ({t1: t2} → BUILD_MAP), R19-13 (t1 == t2 → COMPARE_OP)
- 触发: 同一二元/链式消费指令的两个操作数都是 ternary
- 根因: `_detect_ternary_context` 与 `_try_build_ternary_merge_consumer_expr` 仅处理
  单 ternary 在左/右/中位置 (R1-R5/R16 已覆盖)，未覆盖「两个 ternary 同时汇聚到
  同一 COMPARE_OP / BUILD_MAP / RAISE_VARARGS」的复合形态。两个 ternary merge 块
  归属未协调，第一个 ternary 被丢弃为独立 POP_TOP 表达式。
- 代码位置: `core/cfg/region_ast_generator.py` `_try_build_ternary_chained_r6_pattern`
  Pattern A 仅处理两 ternary + BinOp，未覆盖两 ternary + Compare / Dict / Raise。

### 根因 B: tuple unpack 中 ternary 与常量元素混合 (2 个)
- R19-06 (x, y = c, t1), R19-07 (a, b, c = 1, t1, 2)
- 触发: tuple unpack RHS 含一个 ternary + 一个或多个常量元素
- 根因: R6/R13 unpack 处理「两元素均 ternary」(BUILD_TUPLE 在两 ternary merge 之后)，
  但「一个 ternary + 常量元素」时，常量的 LOAD_NAME/LOAD_CONST 与 ternary merge
  块归属未协调，UNPACK_SEQUENCE + 多个 STORE_NAME 消费链被部分丢弃。
- 代码位置: `core/cfg/region_ast_generator.py` `_try_build_ternary_chained_r6_pattern`
  Pattern B (SWAP N + N×STORE_*) 仅处理 N=len(chain) 全 ternary，未覆盖混合元素。

### 根因 C: ternary 在 with 语句各槽位 (3 个)
- R19-02 (with as cm[t1] — as-target subscript), R19-03 (with open(t1) as f, open(t2) as h — 两 item cm 均 ternary),
  R19-04 (with body cm.process(t1).finalize() — body 内方法链)
- 触发: ternary 在 with as-target subscript / multi-with 两 item cm / with body 方法链
- 根因: WithRegion 的 BEFORE_WITH + STORE_SUBSCR / 多个 BEFORE_WITH + WITH_EXCEPT_START
  清理链 与 ternary merge 块归属冲突。R3/R7/R14 with 系列仅覆盖单 item ternary cm +
  as / with body 简单 ternary，未覆盖 as-target subscript / 双 item cm / body 方法链。
- 代码位置: `core/cfg/region_analyzer.py` `_consumer_extra_blocks` 未覆盖 with 清理块。

### 根因 D: ternary 作 annotation / ann assign 注解 (2 个)
- R19-08 (x: (t1) = None — ann assign 注解), R19-09 (def f(x: (t1)) — 函数参数注解)
- 触发: ternary 是 annotated assignment 的注解表达式 / 函数参数的注解
- 根因: SETUP_ANNOTATIONS + STORE_SUBSCR (写入 __annotations__) / MAKE_FUNCTION
  收集注解的消费链与 ternary merge 块归属冲突。R6/R8 annotation 系列仅覆盖
  `x: (ternary)` (无 value) / `x: int = (ternary)` (注解常量)，未覆盖注解本身是
  ternary 的形态。
- 代码位置: `core/cfg/region_ast_generator.py` AnnAssign / FunctionDef 注解处理未识别
  ternary region 的 merge_block 作为注解来源。

### 根因 E: try-finally finally 块内 raise E(ternary) (1 个)
- R19-01
- 触发: finally 清理块内 raise 调用含 ternary 参数
- 根因: finally 块的 PUSH_EXC_INFO + POP_EXCEPT + RERAISE 清理链与 ternary merge
  块的 PRECALL+CALL+RAISE_VARARGS 消费链归属冲突，raise 被误移入 try 体。R14
  finally_body 仅覆盖 `finally: x = (ternary)` (assign)，未覆盖 raise 调用。
- 代码位置: `core/cfg/region_analyzer.py` finally 块归属与 TernaryRegion 边界冲突。

### 根因 F: dict literal 方法调用的参数 dict 含 ternary key (1 个)
- R19-14
- 触发: `{1:2}.update({(t1): 3})` — 外层 dict literal 调用方法，参数是含 ternary key 的 dict
- 根因: 外层 dict literal `{1:2}` 的 BUILD_MAP 与参数 dict `{(t1): 3}` 的 BUILD_MAP
  叠加，ternary merge 块栈顶被内层 BUILD_MAP 消费，再被外层 LOAD_METHOD update +
  PRECALL+CALL 消费。R15 dict_literal_method 仅覆盖 `{}.get((ternary))` (ternary 直接
  作参数)，未覆盖「参数本身是含 ternary 的 dict literal」。
- 代码位置: `core/cfg/region_ast_generator.py` `_try_build_ternary_merge_consumer_expr`
  未处理嵌套 BUILD_MAP (外层 dict literal + 参数 dict)。

## 新建测试文件清单（14 个）
1. `/workspace/tests/exhaustive/ternary/test_r19_ternary_try_finally_raise.py`
2. `/workspace/tests/exhaustive/ternary/test_r19_ternary_with_as_subscr_target.py`
3. `/workspace/tests/exhaustive/ternary/test_r19_ternary_with_multiple_both_ternary.py`
4. `/workspace/tests/exhaustive/ternary/test_r19_ternary_with_body_method_chain_arg.py`
5. `/workspace/tests/exhaustive/ternary/test_r19_ternary_raise_from_both_ternary.py`
6. `/workspace/tests/exhaustive/ternary/test_r19_ternary_tuple_unpack_one_ternary.py`
7. `/workspace/tests/exhaustive/ternary/test_r19_ternary_tuple_unpack_middle_ternary.py`
8. `/workspace/tests/exhaustive/ternary/test_r19_ternary_ann_assign_ternary_annotation.py`
9. `/workspace/tests/exhaustive/ternary/test_r19_ternary_func_arg_ternary_annotation.py`
10. `/workspace/tests/exhaustive/ternary/test_r19_ternary_chained_compare_both_ternary.py`
11. `/workspace/tests/exhaustive/ternary/test_r19_ternary_compare_in_both_ternary.py`
12. `/workspace/tests/exhaustive/ternary/test_r19_ternary_dict_literal_key_value_ternary.py`
13. `/workspace/tests/exhaustive/ternary/test_r19_ternary_compare_eq_both_ternary.py`
14. `/workspace/tests/exhaustive/ternary/test_r19_ternary_dict_literal_method_dict_arg.py`

## 验证命令
```bash
# 单独运行 R19 测试 (全部 FAILED)
timeout 60 python -m pytest tests/exhaustive/ternary/test_r19_*.py -v --tb=short

# 完整 ternary 套件 (59 failed = 45 baseline + 14 new)
timeout 280 python -m pytest tests/exhaustive/ternary/ -q --tb=no
```

## 约束遵循
- 未修改任何现有源代码 (`core/cfg/*.py`)
- 未创建根级 `_debug_*.py` 调试脚本 (调试脚本
  `/workspace/.trae/specs/iterate-region-test-fix/rounds/ternary_region/round_19/_explore.py`
  在 round_19 目录下)
- 所有测试验证字节码完全匹配 (非语义等价)，使用 `verify_decompilation()` 完整流程
  (反编译 + 语法检查 + 区域类型 + 字节码等价)
- 未重复 R1-R18 已覆盖场景 (经 grep 核对 SOURCE_CODE，重点核对 R6/R13/R14/R15/R18
  的 unpack/with/raise/compare/dict 系列变体)
- 优先关注共性根因类问题，14 个 bug 归为 6 类根因
