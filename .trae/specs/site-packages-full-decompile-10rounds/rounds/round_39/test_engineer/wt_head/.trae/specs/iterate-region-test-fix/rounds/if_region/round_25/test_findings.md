# IF Region Round 25 — Test Findings

## 基线
- if_region: 17 failed / 800 passed / 10 skipped
- ternary: 0 failed / 506 passed / 36 skipped

## 测试发现方法
- 在 `tests/exhaustive/if_region/` 下新增 37 个 `test_r25_*.py` 候选测试文件
- 批量运行 `python -m pytest test_r25_*.py --tb=no -q`，保留真正 FAILED 的测试
- 跳过（SKIPPED）的 4 个测试同样为反编译器 bug（生成的代码非法 Python，重编译失败），但因测试框架 skip 而不计入"失败"
- 错误（ERROR）的 1 个测试因源码本身非法（`import *` 仅模块级）已删除
- 最终确认 **13 个新失败测试**，全部不在已知 17 个失败之列

## 发现的新错误（13 个）

### 根因聚类
| 簇 | 描述 | 涉及 Finding | 数量 |
|---|---|---|---|
| R25-A | if-elif-else 头坍塌为三元表达式（条件含 await / f-string+walrus / ternary+boolop 在 elif 上下文） | R25-01, 03, 04, 13 | 4 |
| R25-B | 嵌套 for-else / try-else-finally / with / global+del 的 else/cleanup 子句在三分支内归属错位 | R25-02, 05, 07, 09, 11, 12 | 6 |
| R25-C | 多目标赋值 / tuple return 中表达式归约失败（ternary、comprehension 作为子节点丢失） | R25-06, 10 | 2 |
| R25-D | lambda IIFE 在 elif 条件中递归反编译 body 退化为 `*args, **kwargs: None` | R25-08 | 1 |

---

### Bug R25-01: async if-elif-else 条件含 await 在 call arg 时整 if 坍塌为三元
- 测试文件: tests/exhaustive/if_region/test_r25_await_call_arg_in_elif.py
- 源码:
  ```python
  async def f(x):
      if x > 0:
          return process(await fetch(x), await fetch(x + 1))
      elif x < 0:
          return process(await fetch(-x))
      else:
          return process(0)
  ```
- 期望: 保留 if-elif-else 三分支，每分支含 `await fetch(...)` 调用
- 实际: `async def f(x):\n    (None if x > 0 else x < 0)` — 整个 if-elif-else 坍塌为单个三元表达式，elif/else 分支与所有 await 调用丢失
- 根因猜测: `_identify_conditional_regions` 中 await setup+poll 块（GET_AWAITABLE+SEND）位于 if 条件上下文时，被 `_collect_await_predecessor_chain` 仅收集单组 setup+poll；多 await 时剩余 await 块被当作 BoolOpRegion 抢占 if 头块，IfRegion 创建被跳过，整 if 坍塌为 IfExp。与 R21-11 同源（C5），但此前仅在 if 条件触发，本次在 elif + return 值上下文触发
- 算法原则违反: 原则 1（自底向上归约）— await setup+poll 应作为 IfRegion 子节点；原则 4（父引用子入口）— IfRegion 应通过 entry 引用 await 子表达式

### Bug R25-02: if-elif-else 三分支各自含 for-else + continue 时 else 子句归属错位
- 测试文件: tests/exhaustive/if_region/test_r25_for_else_continue_each_branch.py
- 源码:
  ```python
  def f(items, mode):
      if mode == 'a':
          for x in items:
              if x < 0:
                  continue
              process_a(x)
          else:
              return 'a_done'
      elif mode == 'b':
          for x in items:
              if x > 100:
                  continue
              process_b(x)
          else:
              return 'b_done'
      else:
          return 'c_done'
  ```
- 期望: 保留 if-elif-else 三分支，每分支含 for-else + continue
- 实际: 反编译结果中 elif 分支出现游离的 `items` 表达式语句，且 `else: return 'c_done'` 被剥离为函数末尾裸 `return 'c_done'`，else 子句归属错位。指令数 35 vs 37（多 2 条）
- 根因猜测: `_collect_branch_blocks` 收集 IfRegion.elif_bodies 时，未把 ForLoop（含 for-else）作为整体子节点，沿 fallthrough 拆解 ForLoop.body 与 else_blocks；for-else 的 `else: return 'a_done'` 被错挂到 IfRegion.elif_bodies，而 for setup 之前的 `items` LOAD 块被作为独立 BASIC 块纳入 elif body。与 R21-14/R21-15 同源（C4），但此前是 for-else+break，本次是 for-else+continue
- 算法原则违反: 原则 2（每块唯一归属）+ 原则 3（嵌套即抽象节点）— ForLoop 应作为 elif body 的单一抽象节点

### Bug R25-03: f-string 含三元+walrus 在 if-elif-else 分支时整 if 坍塌
- 测试文件: tests/exhaustive/if_region/test_r25_fstring_ternary_walrus_each_branch.py
- 源码:
  ```python
  def f(x):
      if x > 0:
          return f"{(y := x) if x > 0 else 0} is positive"
      elif x < 0:
          return f"{(y := -x) if x < 0 else 0} is negative"
      else:
          return f"{(y := x)} is zero"
  ```
- 期望: 保留 if-elif-else 三分支，每分支 return f-string
- 实际: `(((y := x) if x > 0 else 0) if x > 0 else x < 0)\n    return f'{((y := -x) if x < 0 else 0)}'` — if-elif 坍塌为嵌套三元表达式，else 分支完全丢失
- 根因猜测: f-string 内嵌套三元 `(y := x) if x > 0 else 0` 的 merge_block（FORMAT_VALUE/FORMAT_SIMPLE）被 TernaryRegion 识别后，IfRegion 头块的 condition_block 被重定向到 TernaryRegion.merge_block，但 `_if_extract_condition_from_instructions` 未能正确处理 f-string 上下文的 ternary，把整个 if-elif-else 误归约为 IfExp。与 R21-01 同源（C1），但此前是 if 条件含三元，本次是 if body 的 return 值含 f-string+三元+walrus
- 算法原则违反: 原则 1（自底向上归约）— TernaryRegion 应作为 IfRegion.then_blocks 内 return value 的子节点；原则 4 失败

### Bug R25-04: async if-elif-else 条件含 await 在 subscript 时整 if 坍塌
- 测试文件: tests/exhaustive/if_region/test_r25_await_in_subscr_each_branch.py
- 源码:
  ```python
  async def f(x):
      if x > 0:
          return data[await fetch(x)]
      elif x < 0:
          return (await fetch(-x))[0]
      else:
          return data[await fetch(0):]
  ```
- 期望: 保留 if-elif-else 三分支，每分支含 `await fetch(...)` 在 subscript 位置
- 实际: `(None if x > 0 else None if x < 0 else None)` — 整个 if-elif-else 坍塌为嵌套三元，所有分支与 await 调用丢失
- 根因猜测: await 在 subscript 上下文（`data[await fetch(x)]`）的 setup+poll 块未被 IfRegion.then_blocks 收集，`_collect_branch_blocks` 把 await 块作为独立 BASIC 块处理；多分支的 await 链导致 IfRegion 头块被 BoolOpRegion/TernaryRegion 抢占，IfRegion 创建被跳过。与 R25-01 同源（C5），但 await 位置在 subscript 而非 call arg
- 算法原则违反: 原则 1（自底向上归约）+ 原则 4（父引用子入口）

### Bug R25-05: if-elif-else 三分支各自含 for + continue + try 时分支结构错乱
- 测试文件: tests/exhaustive/if_region/test_r25_for_continue_try_each_branch.py
- 源码:
  ```python
  def f(items, mode):
      if mode == 'a':
          for x in items:
              try:
                  if x < 0:
                      continue
                  process_a(x)
              except ValueError:
                  pass
          return 'a_done'
      elif mode == 'b':
          for x in items:
              try:
                  if x > 100:
                      continue
                  process_b(x)
              except TypeError:
                  pass
          return 'b_done'
      else:
          return 'c_done'
  ```
- 期望: 保留 if-elif-else 三分支，每分支含 for + try-except + continue
- 实际: `if x < 0: continue` 被重写为 `if (x < 0): continue else: process_a(x); continue`（多出 else 分支 + 多余 continue），且 elif 分支出现游离的 `items` 表达式语句。指令数 53 vs 55（多 2 条）
- 根因猜测: TryExceptRegion 识别时，`continue` 语句的 JUMP_BACKWARD 块被纳入 TryExceptRegion.blocks，但 IfRegion 收集 then_blocks 时把 continue 的 JUMP_BACKWARD 块作为 try body 的 fallthrough，导致 `if x < 0: continue` 被误识别为 `if-else`（continue 跳转目标被当作 else 入口）。`_collect_branch_blocks` 未把 TryExceptRegion 作为 ForLoop.body 的单一子节点
- 算法原则违反: 原则 2（每块唯一归属）— continue 块被 IfRegion 与 TryExceptRegion/ForLoop 同时争抢；原则 3（嵌套即抽象节点）

### Bug R25-06: multi-target 赋值 + 三元在 elif body 时 return 语句丢失
- 测试文件: tests/exhaustive/if_region/test_r25_multi_target_ternary_in_elif.py
- 源码:
  ```python
  def f(x, flag):
      if flag == 'a':
          return 'a'
      elif flag == 'b':
          a = b = (x if x > 0 else 0)
          return a + b
      else:
          return 0
  ```
- 期望: 保留 elif body 内 `a = b = (ternary)` + `return a + b`，else 分支 `return 0`
- 宺际: `a = b = (x if x > 0 else 0)\n    return 0` — elif body 的 `return a + b` 丢失，else 分支被剥离为函数末尾裸 `return 0`。指令数 23 vs 19（少 4 条，`LOAD_FAST a, LOAD_FAST b, BINARY_OP +, RETURN_VALUE` 丢失）
- 根因猜测: TernaryRegion 在 elif body 的 multi-target 赋值上下文（`a = b = (ternary)`）中，merge_block 含 `COPY, STORE_FAST a, STORE_FAST b`。`_generate_ternary` 生成 IfExp 后，后续的 `LOAD_FAST a, LOAD_FAST b, BINARY_OP +, RETURN_VALUE`（return a + b）未被纳入 IfRegion.elif_bodies，被作为独立 BASIC 块处理；else 分支的 `return 0` 被剥离为函数末尾隐式 return。`_collect_branch_blocks` 在 multi-target STORE 块后未正确终止分支收集
- 算法原则违反: 原则 4（父引用子入口）— 父 IfRegion.elif_bodies 应通过 STORE 块后的 fallthrough 引用 return 语句；原则 3（嵌套即抽象节点）— ternary 应作为 multi-target Assign.value 的子节点

### Bug R25-07: 嵌套 with + 多 context 在 elif body 时 with 结构完全错乱
- 测试文件: tests/exhaustive/if_region/test_r25_nested_with_try_in_each_branch.py
- 源码:
  ```python
  def f(flag):
      if flag == 'a':
          return 'a'
      elif flag == 'b':
              with open('a') as fa, open('b') as fb:
                  data = fa.read()
                  with open('c') as fc:
                      data += fc.read()
                  return data + fb.read()
      else:
          return None
  ```
- 期望: 保留 elif body 内多 context with + 嵌套 with
- 实际: `data += fc.read()` 出现在 `fc` 定义之前，`return None(None, None)`（return 值被篡改），`with open('c') as fc: pass` 被推迟到末尾，`open('b')` 作为游离表达式。指令数 108 vs 91（多 17 条）
- 根因猜测: WithRegion 识别时，外层 `with open('a') as fa, open('b') as fb:` 的多 context 与内层 `with open('c') as fc:` 的嵌套 with 共享 cleanup 块（WITH_EXCEPT_START 链）。`_identify_with_regions` 把内层 with 的 BEFORE_WITH + STORE_FAST 也吸收到外层 WithRegion 的 context 列表，导致三个 BEFORE_WITH 全部平铺，嵌套层级破坏。与 R21-18 同源（C6），但此前在 if body，本次在 elif body 且含 read() 调用
- 算法原则违反: 原则 3（嵌套即抽象节点）— 内层 with 应作为外层 with body 的子节点，不应被平铺到外层 with 的 context 列表

### Bug R25-08: lambda IIFE 在 elif 条件中递归反编译 body 退化
- 测试文件: tests/exhaustive/if_region/test_r25_lambda_iife_in_elif_cond.py
- 源码:
  ```python
  def f(y):
      if y > 0:
          return 'pos'
      elif (lambda x: x < 0)(y):
          return 'neg'
      else:
          return 'zero'
  ```
- 期望: elif 条件 `(lambda x: x < 0)(y)`，lambda body 为 `return x < 0`
- 实际: `elif (lambda *args, **kwargs: None)(y):` — lambda 的 `x < 0` body 完全退化为 `*args, **kwargs: None`（参数变为 *args/**kwargs，body 变为 None）。嵌套 code object 指令数 5 vs 3（`LOAD_FAST x, LOAD_CONST 0, COMPARE_OP, RETURN_VALUE` 丢失，仅剩 `LOAD_CONST None, RETURN_VALUE`）
- 根因猜测: lambda code object 的递归反编译未走完整的 region_analyzer 流程。lambda body `(x < 0)` 含 COMPARE_OP + RETURN_VALUE，但递归反编译时 IfRegion/BoolOpRegion 识别未正确处理 lambda body 的简单比较表达式，把 body 当作空体处理，生成 `*args, **kwargs` 默认签名。与 R21-25 同源（C7），但此前在 if 条件，本次在 elif 条件
- 算法原则违反: 原则 1（自底向上归约）— lambda body 内比较表达式应被识别为 Return.value 子节点

### Bug R25-09: if-elif-else 三分支各自含 try-except-else-finally 时 finally cleanup 丢失
- 测试文件: tests/exhaustive/if_region/test_r25_try_else_finally_each_branch.py
- 源码:
  ```python
  def f(x):
      if x > 0:
          try:
              r = process(x)
          except ValueError:
              r = -1
          else:
              r = r + 1
          finally:
              cleanup()
          return r
      elif x < 0:
          try:
              r = process(-x)
          except TypeError:
              r = -2
          else:
              r = r * 2
          finally:
              cleanup()
          return r
      else:
          return 0
  ```
- 期望: 保留 if-elif-else 三分支，每分支含 try-except-else-finally
- 实际: elif 分支的 `finally: cleanup()` 被替换为 `finally: pass`（cleanup 调用丢失）。指令数 80 vs 72（少 8 条，elif 分支的 `LOAD_GLOBAL cleanup, PRECALL, CALL, POP_TOP` 丢失）
- 根因猜测: TryExceptRegion 识别时，`finally_blocks` 含 cleanup 调用块，但 elif 分支的 TryExceptRegion.finally_blocks 被 IfRegion.elif_bodies 重复收集时，cleanup 块被剥离。`_collect_branch_blocks` 沿 fallthrough 走过 try-except-else-finally 后，把 finally 块作为独立 BASIC 块处理，但 elif 链的 finally 块被 IfRegion 与 TryExceptRegion 同时争抢，最终 cleanup 丢失。与 R21-13 同源（C4），但此前在 if body，本次在 if-elif-else 三分支且含 else+finally 双子句
- 算法原则违反: 原则 2（每块唯一归属）— finally cleanup 块被 IfRegion.elif_bodies 与 TryExceptRegion.finally_blocks 同时争抢

### Bug R25-10: tuple return + comprehension 在三分支时 tuple 结构与 comprehension 丢失
- 测试文件: tests/exhaustive/if_region/test_r25_tuple_return_comprehension.py
- 源码:
  ```python
  def f(flag, items):
      if flag == 'a':
          return (sum(items), len(items), [x for x in items if x > 0])
      elif flag == 'b':
          return ({x for x in items}, {k: v for k, v in items})
      else:
          return ((x for x in items), max(items))
  ```
- 期望: 保留 if-elif-else 三分支，每分支 return 多元素 tuple 含 comprehension
- 实际: `return [x for x in items if x > 0]`（仅保留 listcomp，tuple 包装丢失），elif 分支 `return {x for x in items}` 后跟独立的 `return {k: v for k, v in items}`（setcomp 与 dictcomp 分裂为两个 return），else 分支 `return (x for x in items)`（max(items) 丢失）。指令数 49 vs 28（少 21 条）
- 根因猜测: BUILD_TUPLE 2/3 在 IfRegion.then_blocks 中被收集时，tuple 元素块（含 comprehension 的 MAKE_FUNCTION + GET_ITER + CALL）被作为独立 BASIC 块处理。`_collect_branch_blocks` 把 tuple 元素拆解，BUILD_TUPLE 后的 RETURN_VALUE 被作为独立 return 生成，导致每个 comprehension 变成独立 return 语句。与 R21-21 同源（C3），但此前是 set+genexp，本次是 listcomp+setcomp+dictcomp+genexp 四种 comprehension 混合
- 算法原则违反: 原则 3（嵌套即抽象节点）— comprehension 应作为 return value 的 Tuple.elts 子节点，不应被 IfRegion 块收集拆解

### Bug R25-11: global + del 在 elif body 时 else 分支结构丢失
- 测试文件: tests/exhaustive/if_region/test_r25_global_del_in_elif_body.py
- 源码:
  ```python
  g = 0
  def f(mode):
      global g
      if mode == 'a':
          g = 1
          del g
          g = 10
      elif mode == 'b':
          g = 2
      else:
          return g
  ```
- 期望: 保留 if-elif-else 三分支，else 分支 `return g`
- 实际: `return g` 被剥离为函数末尾裸 `return`（else 分支结构丢失），且 `return g` 的 `LOAD_GLOBAL` 在 else 分支应出现但被合并到函数末尾。指令数 20 vs 16（少 4 条，else 分支的 `LOAD_FAST mode, LOAD_CONST 'b'(?), COMPARE_OP, ...` 部分丢失，但 `LOAD_GLOBAL g, RETURN_VALUE` 移到函数末尾）
- 根因猜测: `global g` + `del g` 在 if body 内时，DELETE_GLOBAL 指令的块被 IfRegion.then_blocks 收集，但 elif 链的 else 分支（`return g`）被剥离为函数末尾隐式 return。`_collect_branch_blocks` 在 global + del 后未正确终止分支收集，导致 else 分支块被 IfRegion.else_blocks 丢失。`global` 声明的 STORE_GLOBAL/DELETE_GLOBAL/LOAD_GLOBAL 序列与 IfRegion 边界交互错误
- 算法原则违反: 原则 2（每块唯一归属）— else 分支的 return 块被 IfRegion.else_blocks 与函数末尾隐式 return 同时争抢；原则 4（父引用子入口）

### Bug R25-12: if-elif-else 三分支各自含 try-finally 时 elif 分支 finally cleanup 丢失
- 测试文件: tests/exhaustive/if_region/test_r25_try_finally_raise_each_branch.py
- 源码:
  ```python
  def f(x):
      if x > 0:
          try:
              r = process(x)
          finally:
              cleanup()
          return r
      elif x < 0:
          try:
              r = process(-x)
          finally:
              cleanup()
          return r
      else:
          raise ValueError('zero')
  ```
- 期望: 保留 if-elif-else 三分支，每分支含 try-finally
- 实际: elif 分支的 `finally: cleanup()` 被替换为 `finally: pass`（cleanup 调用丢失）。指令数 53 vs 45（少 8 条，elif 分支的 cleanup 调用链丢失）
- 根因猜测: 与 R25-09 同源（C4），但无 except/else 子句，仅 try-finally。TryExceptRegion（finally only）的 finally_blocks 含 cleanup 调用，但 elif 分支的 finally 块被 IfRegion.elif_bodies 与 TryExceptRegion.finally_blocks 争抢，最终 elif 的 cleanup 丢失
- 算法原则违反: 原则 2（每块唯一归属）— finally cleanup 块被两个区域同时争抢

### Bug R25-13: if-elif-else 条件含 ternary + boolop 在 elif 时 else 分支结构与指令错乱
- 测试文件: tests/exhaustive/if_region/test_r25_ternary_boolop_in_elif_cond.py
- 源码:
  ```python
  def f(a, c, d, b):
      if a > 0:
          return 1
      elif (a if c else d) and b:
          return 2
      else:
          return 3
  ```
- 期望: elif 条件 `(a if c else d) and b`，else 分支 `return 3`
- 实际: `elif (a if c else d and b):` — 三元的 orelse 被错误地包含 `d and b`（运算符优先级错误：`a if c else (d and b)` 而非 `(a if c else d) and b`），且 else 分支 body 变为 `pass` 而非 `return 3`。指令数 14 vs 18（多 4 条，多出 2 个 `LOAD_CONST None, RETURN_VALUE` 隐式 return）
- 根因猜测: TernaryRegion 在 elif 条件上下文中，`(a if c else d) and b` 的 BoolOpRegion op_chain 收集时，把 ternary 的 false_value（`d`）与 BoolOp 的第二操作数（`b`）合并，导致 ternary 的 orelse 被错误扩展为 `d and b`。同时 else 分支的 `return 3` 被剥离，生成 `pass` + 隐式 return None。与 R21-03 同源（C1），但此前在 if 条件，本次在 elif 条件且 BoolOp 包裹整个 ternary
- 算法原则违反: 原则 1（自底向上归约）— BoolOp 应通过 op_chain 引用 ternary entry，不应修剪 ternary 的 value 块；原则 4（父引用子入口）

---

## 附加发现（SKIPPED，反编译器生成非法 Python，不计入失败但为真实 bug）

### Skip-01: dictcomp 内 walrus 被错误添加为迭代变量
- 测试文件: tests/exhaustive/if_region/test_r25_dictcomp_walrus_each_branch.py
- 源码: `{k: v for k, v in items if (n := v) > 0}`
- 实际: `{k: v for k, v, n in items if (n := v) > 0}` — walrus 变量 `n` 被错误添加为 comprehension 迭代变量，导致重编译失败（`assignment expression cannot rebind comprehension iteration variable`）
- 根因猜测: dictcomp 的 walrus `n := v` 在 BUILD_MAP 上下文中，反编译器把 walrus 的 STORE_FAST 块误识别为 comprehension 的 UNPACK/STORE 迭代目标

### Skip-02: genexp 内 walrus 被错误添加为迭代变量
- 测试文件: tests/exhaustive/if_region/test_r25_genexp_walrus_each_branch.py
- 实际: `sum((n := x) for x, n in items if n > 0)` — 同 Skip-01，`n` 被添加为迭代变量

### Skip-03: listcomp 内双 if 过滤被合并为 and
- 测试文件: tests/exhaustive/if_region/test_r25_listcomp_nested_ternary_filter.py
- 实际: `[x for x, y in items if (y := x) > 0 and y < 100]` — 双 `if` 过滤（`if (y := x) > 0 if y < 100`）被合并为单个 `if ... and ...`，且 walrus 变量 `y` 被添加为迭代变量

### Skip-04: async with + async for 在 elif body 时重编译失败
- 测试文件: tests/exhaustive/if_region/test_r25_async_with_async_for_in_elif.py
- 实际: 反编译结果含非法 Python，重编译失败

---

## 跨测试根因汇总表

| 根因簇 | 涉及 Finding | 涉及测试数 | 优先级 | 关键源码位置 |
|--------|--------------|------------|--------|--------------|
| R25-A: if-elif-else 头坍塌为三元（await/f-string/ternary+boolop 在 elif 或 body 值上下文） | R25-01, 03, 04, 13 | 4 | P0 | region_analyzer.py: _collect_await_predecessor_chain (4425), _identify_conditional_regions (10315-10337) |
| R25-B: 嵌套 for-else / try-else-finally / with / global+del 的 else/cleanup 子句在三分支内归属错位 | R25-02, 05, 07, 09, 11, 12 | 6 | P0 | region_analyzer.py: _collect_branch_blocks (10646-10714), _identify_with_regions (7237-7265) |
| R25-C: 多目标赋值 / tuple return 中表达式归约失败 | R25-06, 10 | 2 | P1 | region_ast_generator.py: _generate_ternary (18747), _collect_branch_blocks |
| R25-D: lambda IIFE 在 elif 条件中递归反编译 body 退化 | R25-08 | 1 | P1 | 递归 code object 反编译路径 |

---

## 关键算法原则违反统计

| 原则 | 违反次数 | 主要场景 |
|------|----------|----------|
| 原则 1（自底向上归约） | 5 | await setup+poll 未完整收集；ternary+boolop 抢占 elif 头；lambda body 退化 |
| 原则 2（每块唯一归属） | 7 | for-else/try-else/try-finally 的 else/cleanup 块被 IfRegion 与 Loop/Try 同时争抢；continue 块被多区域争抢；global+del 的 else 分支 return 被剥离 |
| 原则 3（嵌套即抽象节点） | 4 | ForLoop/WhileLoop/TryExcept 在 then_blocks 中被 BFS 拆解；comprehension 在 tuple 中被拆解；嵌套 with 被平铺 |
| 原则 4（父引用子入口） | 5 | IfRegion 未通过 entry 引用 await/ternary 子节点；multi-target STORE 后的 return 未被引用；global+del 的 else return 未被引用 |

---

## 验证

```bash
cd /workspace && timeout 280 python -m pytest tests/exhaustive/if_region/test_r25_*.py --tb=no -q
```
结果: 13 failed, 20 passed, 4 skipped

## 修复优先级建议

1. **P0 - 先修 R25-B**（覆盖 6 个测试）: 嵌套 for-else / try-else-finally / with 的 else/cleanup 子句在三分支内归属错位。`_collect_branch_blocks` 应把 LoopRegion/TryExceptRegion/WithRegion 作为整体子节点，不沿 fallthrough 拆解其内部 blocks
2. **P0 - 再修 R25-A**（覆盖 4 个测试）: if-elif-else 头坍塌为三元。`_collect_await_predecessor_chain` 应沿前驱链完整收集所有 await setup+poll 对；f-string/ternary 在 body 值上下文时不应抢占 if 头
3. **P1 - 修 R25-C + R25-D**（覆盖 3 个测试）: multi-target 赋值 + ternary 在 elif body 的 return 丢失；lambda IIFE 在 elif 递归反编译退化
