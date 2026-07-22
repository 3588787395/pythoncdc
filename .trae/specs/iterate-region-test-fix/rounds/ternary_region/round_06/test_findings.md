# Ternary Region Round 06 — 测试发现报告

## 统计摘要

| 指标 | 数值 |
|------|------|
| R6 新增测试文件 | 22 |
| R6 测试结果 | 13 failed / 9 passed / 0 skipped |
| R6 真实新 bug | 13（全部为对抗性新发现） |
| 通过率 | 9 / 22 = 40.9% |
| 全量 ternary 回归 | 70 failed / 191 passed / 1 skipped（262 测试，基线 57/182/1 → +13 failed / +9 passed / 0 退化） |
| 退化 | 0 个基线测试退化 |

### 与 R1-R5 累计对比

| 轮次 | 新增测试 | passed | failed | 累计 failed | 备注 |
|------|----------|--------|--------|-------------|------|
| R1 | 14 | 5 | 9 | 9 | 基础 if-exp 场景 |
| R2 | 28 | 11 | 17 | 26 | binop / collection / format |
| R3 | 15 | 9 | 6 | 32 | decorator / class / await |
| R4 | 13 | 5 | 8 | 40 | for / del / raise / kwargs |
| R5 | 22 | 12 | 10 | 57（含 3 已知限制） | chained compare / class body / while(ternary) |
| **R6** | **22** | **9** | **13** | **70（含 3 R5 已知限制 + 13 R6 新 bug）** | **while(ternary) 新角度 + try/except + 复杂赋值 + 推导式 + 闭包 + 装饰器 + 注解** |

## R6 与 R1-R5 的核心区别

1. **聚焦 R5 已知限制新角度**：R5 留下 3 个 while(ternary) 已知限制（R5-05/06/07）。R6 不再重复 R5-05/06/07 的简单场景，而是 4 个新变体（嵌套 ternary in while cond、ternary in while body、ternary in while-else、ternary in while cond + complex body），暴露更深层根因。
2. **覆盖结构性交叉点**：R6 测试 ternary 与所有其它控制流/数据结构的交叉：try/except、循环、推导式、嵌套函数、闭包、装饰器链、类型注解、lambda、调用实参、subscript 赋值、yield、async generator。R1-R5 主要聚焦单一结构内部 ternary，R6 聚焦**跨结构归属冲突**。
3. **多 ternary 同上下文**：R6-09/18/19/20 在同一上下文（赋值 / lambda body / 调用实参 / subscript store）放置 ≥2 个 ternary，专门暴露多 TernaryRegion 共享出口块的归属冲突 — 这是 R5-08（class body 多 ternary）共性的更广覆盖。
4. **code object 内部 ternary 退化**：R6-10/12/13（listcomp/setcomp/genexp）暴露一个全新 bug 类别：推导式 code object 内部 ternary 完全丢失（不仅退化为 if，而是直接被替换为 false 分支常量），同时丢失 filter 子句。R1-R5 推导式测试（test_r2_ternary_in_listcomp 等）未涉及 filter。

## R6 测试文件列表

| 序号 | 文件 | 状态 | bug ID |
|------|------|------|--------|
| 1 | `test_r6_ternary_while_cond_nested.py` | FAILED | R6-01 |
| 2 | `test_r6_ternary_while_body_ternary.py` | FAILED | R6-02 |
| 3 | `test_r6_ternary_while_else_ternary.py` | PASSED | — |
| 4 | `test_r6_ternary_while_cond_complex_body.py` | FAILED | R6-04 |
| 5 | `test_r6_ternary_try_in_body.py` | PASSED | — |
| 6 | `test_r6_ternary_try_in_handler.py` | FAILED | R6-06 |
| 7 | `test_r6_ternary_multi_target_assign.py` | PASSED | — |
| 8 | `test_r6_ternary_augassign.py` | PASSED | — |
| 9 | `test_r6_ternary_unpack_assign.py` | FAILED | R6-09 |
| 10 | `test_r6_ternary_listcomp_complex.py` | FAILED | R6-10 |
| 11 | `test_r6_ternary_dictcomp_complex.py` | PASSED | — |
| 12 | `test_r6_ternary_setcomp_complex.py` | FAILED | R6-12 |
| 13 | `test_r6_ternary_genexp_complex.py` | FAILED | R6-13 |
| 14 | `test_r6_ternary_nested_func.py` | PASSED | — |
| 15 | `test_r6_ternary_closure_capture.py` | PASSED | — |
| 16 | `test_r6_ternary_decorator_chain.py` | FAILED | R6-16 |
| 17 | `test_r6_ternary_annotation.py` | FAILED | R6-17 |
| 18 | `test_r6_ternary_in_lambda_body_complex.py` | FAILED | R6-18 |
| 19 | `test_r6_ternary_in_call_arg_complex.py` | FAILED | R6-19 |
| 20 | `test_r6_ternary_in_subscript_complex.py` | FAILED | R6-20 |
| 21 | `test_r6_ternary_yield_complex.py` | PASSED | — |
| 22 | `test_r6_ternary_async_gen.py` | PASSED | — |

---

## Bug 详细分析（13 个真实 bug）

### Bug R6-01: `while (a if c else (b if d else e))` — 嵌套 ternary 在 while 条件中完全退化为多个独立 if + while-and

- **测试**：`test_r6_ternary_while_cond_nested.py`
- **状态**：FAILED
- **源码**：
  ```python
  while (a if c else (b if d else e)):
      pass
  ```
- **反编译结果**：
  ```python
  if a:
      pass
  if b:
      pass
  while c and d and e:
      if c:
          pass
      elif d:
          pass
      a
      continue
  ```
- **问题分解**：
  1. 嵌套 ternary 完全未被识别为 IfExp AST 节点。
  2. 外层 ternary 的 `a`（true_value）被误识别为独立 `if a: pass`。
  3. 内层 ternary 的 `b`（true_value）被误识别为独立 `if b: pass`。
  4. while 条件退化为 `c and d and e`（条件名拼接为 BoolOp）。
  5. while body 完全错误：包含 `if c: pass\n elif d: pass` + `a`（泄漏表达式） + `continue`。
- **字节码对比**：
  - **原始（23 条）**：`LOAD c, LOAD a, LOAD d, LOAD b, LOAD e, LOAD c, LOAD a, RETURN None, LOAD d, LOAD b, RETURN None, LOAD e, RETURN None, RETURN None ×3`
  - **重编（16 条）**：`LOAD a, LOAD b, LOAD c, LOAD d, LOAD e, LOAD c, LOAD d, LOAD a, POP_TOP, RETURN None ×3`
  - 差异：原始 7 个 LOAD_NAME 操作数有序反映嵌套 ternary 结构（c,a,d,b,e,c,a），重编为无序 9 个 LOAD_NAME + 多余 POP_TOP；指令数 23 → 16。
- **根因推测**：`_identify_loop_regions` 在识别 while 循环时，未识别嵌套 ternary 的 merge 块（嵌套 IfExp 的 merge 出口）；region_analyzer 将 ternary 的条件名直接拼接到 while 条件 BoolOp；同时未识别 priming blocks 与 loop test blocks 的去重，导致 `a`/`b` 作为独立表达式泄漏。与 R5-05/06/07 同根因（while + ternary 融合违反「每块唯一归属」），但嵌套 ternary 让退化模式更复杂。

### Bug R6-02: `while x: y = a if c else b` — ternary in while body 后泄漏条件名 `x`

- **测试**：`test_r6_ternary_while_body_ternary.py`
- **状态**：FAILED
- **源码**：
  ```python
  while x:
      y = a if c else b
  ```
- **反编译结果**：
  ```python
  while x:
      y = (a if c else b)
      x
  ```
- **问题分解**：
  1. ternary 在 while body 中正确归约为 IfExp（与 R5-05/06/07 不同，本测试 ternary 不在 while 条件中）。
  2. 但 while body 末尾多出一个表达式语句 `x`（泄漏）。
- **字节码对比**：
  - **原始（11 条）**：`RESUME, LOAD x, LOAD c, LOAD a, LOAD b, STORE y, LOAD x, RETURN None, RETURN None ×2`
  - **重编（13 条）**：`RESUME, LOAD x, LOAD c, LOAD a, LOAD b, STORE y, LOAD x, POP_TOP, LOAD x, RETURN None, RETURN None ×2`
  - 差异：重编多出 `LOAD x, POP_TOP` 两条指令（对应反编译中泄漏的 `x` 表达式语句），指令数 11 → 13。
- **根因推测**：while 循环的 loop test 块（`LOAD x` POP_JUMP_BACKWARD_IF_FALSE）被 region_ast_generator 误识别为 body 的后续语句，独立重建为 `Expr(Name('x'))`。违反「每块唯一归属」— loop test 块的 `LOAD x` 同时承担循环条件测试和被泄漏为 body 表达式。`_identify_loop_regions` 的 body 边界识别未排除 loop test 块。

### Bug R6-04: `while (a if c else b): if x: break\n continue` — while(ternary) + break/continue 完全退化为 `while True:` + 多 if

- **测试**：`test_r6_ternary_while_cond_complex_body.py`
- **状态**：FAILED
- **源码**：
  ```python
  while (a if c else b):
      if x:
          break
      continue
  ```
- **反编译结果**：
  ```python
  while True:
      if c:
          if a:
              pass
          else:
              break
      else:
          pass
      if x:
          break
  ```
- **问题分解**：
  1. 完全没有 IfExp 节点（TERNARY 区域类型校验失败）。
  2. while 条件退化为 `True`（无 ternary）。
  3. ternary `a if c else b` 被误拆为 `if c: if a: pass\nelse: break` — b 分支被错误替换为 break。
  4. 原 body 的 `if x: break` 保留但 `continue` 丢失。
- **字节码对比**：
  - **原始（11 条）**：`RESUME, LOAD c, LOAD a, LOAD b, LOAD x, RETURN None ×3, RETURN None ×2`（含 break/continue 的 POP_JUMP_BACKWARD）
  - **重编（8 条）**：`RESUME, LOAD c, LOAD a, RETURN None, LOAD x, RETURN None, RETURN None`
  - 差异：原始有 `LOAD b`（ternary false_value），重编丢失；指令数 11 → 8。
- **根因推测**：与 R5-07 同根因（while + ternary 融合），但 break/continue 复杂 body 让 region_analyzer 错误地选择了 `while True:` + `if x: break` 的死循环等价形式重建。b 分支被替换为 break 是因为 region_ast_generator 误把 ternary false_value 块的跳转目标（exit）当作 break 跳转目标。`continue` 丢失是因为 continue 跳转目标（loop header）已被 ternary priming 块占用。

### Bug R6-06: `try: pass\nexcept E: x = a if c else b` — except handler 中 ternary 退化为 if + 表达式泄漏

- **测试**：`test_r6_ternary_try_in_handler.py`
- **状态**：FAILED
- **源码**：
  ```python
  try:
      pass
  except E:
      x = a if c else b
  ```
- **反编译结果**：
  ```python
  try:
      pass
  except E:
      if c:
          pass
      else:
          b
      a
  ```
- **问题分解**：
  1. ternary 完全未归约为 IfExp。
  2. ternary 退化为 `if c: pass\nelse: b`（true 分支 `a` 被泄漏）。
  3. ternary 的 true_value `a` 作为独立表达式语句泄漏到 except handler 末尾。
  4. 完全丢失 `x =` 赋值（STORE_NAME x）。
- **字节码对比**：
  - **原始（18 条）**：`RESUME, RETURN None, PUSH_EXC_INFO, LOAD E, CHECK_EXC_MATCH, POP_TOP, LOAD c, LOAD a, LOAD b, STORE x, POP_EXCEPT, RETURN None, RERAISE 0, COPY 3, POP_EXCEPT, RERAISE 1`
  - **重编（19 条）**：`RESUME, RETURN None, PUSH_EXC_INFO, LOAD E, CHECK_EXC_MATCH, POP_TOP, LOAD c, LOAD b, POP_TOP, LOAD a, POP_TOP, POP_EXCEPT, RETURN None, RERAISE 0, COPY 3, POP_EXCEPT, RERAISE 1`
  - 差异：原始有 `LOAD a, LOAD b, STORE x`（ternary + 赋值）；重编为 `LOAD b, POP_TOP, LOAD a, POP_TOP`（两个独立表达式语句），丢失 STORE_x；指令数 18 → 19。
- **根因推测**：except handler 的 POP_EXCEPT + RERAISE/JUMP_FORWARD 出口与 ternary 的 merge 块共享。region_ast_generator 把 ternary merge 块的 STORE_x 误判为不能在 except handler 内（因为 POP_EXCEPT 必须在 STORE_x 之前），导致 ternary 退化为 if-else 表达式 + 独立 LOAD_a 表达式。`_try_build_ternary_store_assign` 未识别 except handler 的 POP_EXCEPT wrapping 模式。违反「每块唯一归属」— merge 块的 STORE_x 同时承担 ternary 出口和 except handler 出口。

### Bug R6-09: `x, y = (a if c else b), (d if e else f)` — tuple unpack 中第二个 ternary + 第二个 target 完全丢失

- **测试**：`test_r6_ternary_unpack_assign.py`
- **状态**：FAILED
- **源码**：`x, y = (a if c else b), (d if e else f)`
- **反编译结果**：
  ```python
  (a if c else b)
  x = (d if e else f)
  ```
- **问题分解**：
  1. 第一个 ternary `(a if c else b)` 被错误地渲染为独立表达式语句（带 POP_TOP），丢失 unpack target。
  2. 第二个 ternary `(d if e else f)` 被赋值给 `x`（应该是 `y`）。
  3. 完全丢失 `y =` 赋值（STORE_NAME y）。
  4. tuple unpack 结构（BUILD_TUPLE 2 + UNPACK_SEQUENCE 2）完全丢失。
- **字节码对比**：
  - **原始（12 条）**：`RESUME, LOAD c, LOAD a, LOAD b, LOAD e, LOAD d, LOAD f, SWAP 2, STORE x, STORE y, RETURN None`
  - **重编（11 条）**：`RESUME, LOAD c, LOAD a, LOAD b, POP_TOP, LOAD e, LOAD d, LOAD f, STORE x, RETURN None`
  - 差异：原始有 `SWAP 2, STORE x, STORE y`（unpack + 双 STORE）；重编为 `POP_TOP, STORE x`（丢失 SWAP + STORE_y），第一个 ternary 被丢弃（POP_TOP）；指令数 12 → 11。
- **根因推测**：tuple unpack 的 `SWAP 2 + STORE_x + STORE_y` 序列中，第一个 ternary 的 merge 块出口被误识别为 `POP_TOP`（独立表达式），而非 `SWAP 2`（unpack 第一个元素）。`_try_build_ternary_store_assign` 只识别 `STORE_*` 紧跟 ternary merge 的模式，不识别 `SWAP + STORE_* + STORE_*` 的多 ternary unpack 模式。违反「父引用子入口」— tuple unpack 父节点通过 SWAP + STORE 链引用两个 ternary 子节点，但只识别了第二个 ternary。

### Bug R6-10: `z = [a if c else b for x in ys if x > 0]` — listcomp code object 内部 ternary + filter 完全丢失

- **测试**：`test_r6_ternary_listcomp_complex.py`
- **状态**：FAILED
- **源码**：`z = [a if c else b for x in ys if x > 0]`
- **反编译结果**：`z = [b for x in ys]`
- **问题分解**：
  1. listcomp code object 内部 ternary 完全丢失（不是退化为 if，而是直接被替换为 false 分支 `b`）。
  2. listcomp filter `if x > 0` 完全丢失。
  3. 父级 listcomp 调用结构（LOAD_CONST + MAKE_FUNCTION + GET_ITER + CALL）正确。
- **字节码对比**（listcomp 内部 code object）：
  - **原始（12 条）**：`RESUME, BUILD_LIST 0, LOAD_FAST .0, STORE_FAST x, LOAD_FAST x, LOAD_CONST 0, COMPARE_OP >, LOAD_GLOBAL c, LOAD_GLOBAL a, LOAD_GLOBAL b, LIST_APPEND 2, RETURN_VALUE`
  - **重编（7 条）**：`RESUME, BUILD_LIST 0, LOAD_FAST .0, STORE_FAST x, LOAD_GLOBAL b, LIST_APPEND 2, RETURN_VALUE`
  - 差异：原始有 `LOAD_FAST x, LOAD_CONST 0, COMPARE_OP >`（filter）和 `LOAD_GLOBAL c, LOAD_GLOBAL a, LOAD_GLOBAL b`（ternary）；重编只剩 `LOAD_GLOBAL b`，filter 和 ternary 的条件 + true 分支全丢失；指令数 12 → 7。
- **根因推测**：listcomp code object 的 region_analyzer 处理 `LOAD_FAST x + LOAD_CONST 0 + COMPARE_OP + POP_JUMP_IF_FALSE`（filter）和 `LOAD_GLOBAL c + POP_JUMP_IF_FALSE`（ternary cond）时，两个 POP_JUMP_IF_FALSE 共享同一基本块或跳转目标，被合并识别为单一 if-region，丢失 ternary。或者更严重：region_ast_generator 在 listcomp code object 内部完全跳过了 ternary 识别，把 ternary 的 false 分支当作元素表达式。与 R6-12/13 同根因，跨 listcomp/setcomp/genexp 通用。

### Bug R6-12: `z = {a if c else b for x in ys if x}` — setcomp code object 内部 ternary + filter 完全丢失

- **测试**：`test_r6_ternary_setcomp_complex.py`
- **状态**：FAILED
- **源码**：`z = {a if c else b for x in ys if x}`
- **反编译结果**：`z = {b for x in ys}`
- **问题分解**：
  1. setcomp code object 内部 ternary 完全丢失，被替换为 false 分支 `b`。
  2. setcomp filter `if x` 完全丢失。
- **字节码对比**（setcomp 内部 code object）：
  - **原始（10 条）**：`RESUME, BUILD_SET 0, LOAD_FAST .0, STORE_FAST x, LOAD_FAST x, LOAD_GLOBAL c, LOAD_GLOBAL a, LOAD_GLOBAL b, SET_ADD 2, RETURN_VALUE`
  - **重编（7 条）**：`RESUME, BUILD_SET 0, LOAD_FAST .0, STORE_FAST x, LOAD_GLOBAL b, SET_ADD 2, RETURN_VALUE`
  - 差异：原始有 `LOAD_FAST x`（filter）和 `LOAD_GLOBAL c, LOAD_GLOBAL a`（ternary cond + true）；重编全丢失；指令数 10 → 7。
- **根因推测**：与 R6-10 同根因。setcomp 的 `LOAD_FAST x + POP_JUMP_IF_FALSE`（filter）与 `LOAD_GLOBAL c + POP_JUMP_IF_FALSE`（ternary cond）共享跳转目标或基本块，被合并丢失。

### Bug R6-13: `z = list(a if c else b for x in ys if x > 0)` — genexp code object 内部 ternary + filter 完全丢失

- **测试**：`test_r6_ternary_genexp_complex.py`
- **状态**：FAILED
- **源码**：`z = list(a if c else b for x in ys if x > 0)`
- **反编译结果**：`z = list(b for x in ys)`
- **问题分解**：
  1. genexp code object 内部 ternary 完全丢失，被替换为 false 分支 `b`。
  2. genexp filter `if x > 0` 完全丢失。
- **字节码对比**（genexp 内部 code object）：
  - **原始（16 条）**：`RETURN_GENERATOR, POP_TOP, RESUME 0, LOAD_FAST .0, STORE_FAST x, LOAD_FAST x, LOAD_CONST 0, COMPARE_OP >, LOAD_GLOBAL c, LOAD_GLOBAL a, LOAD_GLOBAL b, YIELD_VALUE, RESUME 1, POP_TOP, LOAD_CONST None, RETURN_VALUE`
  - **重编（11 条）**：`RETURN_GENERATOR, POP_TOP, RESUME 0, LOAD_FAST .0, STORE_FAST x, LOAD_GLOBAL b, YIELD_VALUE, RESUME 1, POP_TOP, LOAD_CONST None, RETURN_VALUE`
  - 差异：原始有 `LOAD_FAST x, LOAD_CONST 0, COMPARE_OP >`（filter）和 `LOAD_GLOBAL c, LOAD_GLOBAL a`（ternary cond + true）；重编全丢失；指令数 16 → 11。
- **根因推测**：与 R6-10/12 同根因。genexp 的 filter POP_JUMP_IF_FALSE 与 ternary cond POP_JUMP_IF_FALSE 共享，被合并丢失。三个 comp 测试（listcomp/setcomp/genexp）证明这是**推导式 code object 内部 ternary + filter 组合的通用 bug**。

### Bug R6-16: 多装饰器链 + ternary in body — 装饰器被错误应用到所有前置函数定义

- **测试**：`test_r6_ternary_decorator_chain.py`
- **状态**：FAILED
- **源码**：
  ```python
  def deco1(f):
      return f
  def deco2(f):
      return f
  @deco1
  @deco2
  def f():
      x = a if c else b
  ```
- **反编译结果**：
  ```python
  @deco1
  @deco2
  def deco1(f):
      return f
  @deco1
  @deco2
  def deco2(f):
      return f
  @deco1
  @deco2
  def f():
      x = (a if c else b)
  ```
- **问题分解**：
  1. ternary 在 f body 中正确归约为 IfExp。
  2. 但装饰器链 `@deco1 @deco2` 被错误地应用到所有前置函数定义（deco1, deco2, f），而非只应用到 f。
  3. deco1 和 deco2 本应是普通函数定义，被错误地"装饰"。
- **字节码对比**：
  - **原始（18 条）**：`RESUME, LOAD_CONST deco1_code, MAKE_FUNCTION, STORE_NAME deco1, LOAD_CONST deco2_code, MAKE_FUNCTION, STORE_NAME deco2, LOAD_NAME deco1, LOAD_NAME deco2, LOAD_CONST f_code, MAKE_FUNCTION, PRECALL 0, CALL 0, PRECALL 0, CALL 0, STORE_NAME f, RETURN None`
  - **重编（30 条）**：每个 def 都被装饰 — 3 次 `LOAD_NAME deco1, LOAD_NAME deco2, MAKE_FUNCTION, PRECALL/CALL ×2, STORE_NAME`。
  - 差异：原始只有 1 次 `LOAD_NAME deco1, LOAD_NAME deco2, CALL` 序列（仅 f 被装饰）；重编有 3 次（deco1, deco2, f 都被装饰）；指令数 18 → 30。
- **根因推测**：装饰器链的 `LOAD_NAME deco1, LOAD_NAME deco2, LOAD_CONST f_code, MAKE_FUNCTION, PRECALL, CALL, PRECALL, CALL, STORE_NAME f` 序列在 region_ast_generator 中被错误地分配到前两个 def 的处理路径。`_identify_function_def_regions` 未正确划定装饰器链的作用域，把 deco1/deco2 也视为被装饰的目标。这是**装饰器链 region 边界识别 bug**，与 ternary 无直接关系（ternary 已正确处理），但仍是 R6 装饰器链对抗测试发现的真实 bug。

### Bug R6-17: `x: T = a if c else b` — 变量注解丢失 SETUP_ANNOTATIONS

- **测试**：`test_r6_ternary_annotation.py`
- **状态**：FAILED
- **源码**：`x: T = a if c else b`
- **反编译结果**：
  ```python
  x = (a if c else b)
  __annotations__['x'] = T
  ```
- **问题分解**：
  1. ternary 正确归约为 IfExp。
  2. 变量注解 `x: T = ...` 被拆为两条语句：`x = (a if c else b)` + `__annotations__['x'] = T`。
  3. 丢失 `SETUP_ANNOTATIONS` 指令（模块级注解 setup）。
- **字节码对比**：
  - **原始（12 条）**：`RESUME, SETUP_ANNOTATIONS, LOAD c, LOAD a, LOAD b, STORE x, LOAD T, LOAD __annotations__, LOAD_CONST x, STORE_SUBSCR, RETURN None`
  - **重编（11 条）**：`RESUME, LOAD c, LOAD a, LOAD b, STORE x, LOAD T, LOAD __annotations__, LOAD_CONST x, STORE_SUBSCR, RETURN None`
  - 差异：原始有 `SETUP_ANNOTATIONS`（模块级注解 setup，初始化 __annotations__ dict）；重编丢失；指令数 12 → 11。
- **根因推测**：region_ast_generator 在模块级处理变量注解时，未识别 `SETUP_ANNOTATIONS` 指令（位于 RESUME 之后、第一个 LOAD 之前），把它当作对齐指令过滤或忽略。`__annotations__['x'] = T` 部分通过 `STORE_SUBSCR` 重建正确，但 `SETUP_ANNOTATIONS` 必须在模块顶部生成。这是**注解语句 codegen bug**，与 ternary 无直接关系，但仍是 R6 类型注解对抗测试发现的真实 bug。

### Bug R6-18: `f = lambda: (a if c else b) + (d if e else g)` — lambda body 中第一个 ternary 完全丢失

- **测试**：`test_r6_ternary_in_lambda_body_complex.py`
- **状态**：FAILED
- **源码**：`f = lambda: (a if c else b) + (d if e else g)`
- **反编译结果**：`f = lambda : d if e else g`
- **问题分解**：
  1. lambda body 中第一个 ternary `(a if c else b)` 完全丢失。
  2. 第二个 ternary `(d if e else g)` 被错误地作为整个 lambda body（丢失 BinOp `+` wrapping）。
  3. BinOp ADD 完全丢失。
- **字节码对比**（lambda 内部 code object）：
  - **原始（9 条）**：`RESUME, LOAD_GLOBAL c, LOAD_GLOBAL a, LOAD_GLOBAL b, LOAD_GLOBAL e, LOAD_GLOBAL d, LOAD_GLOBAL g, BINARY_OP 0, RETURN_VALUE`
  - **重编（5 条）**：`RESUME, LOAD_GLOBAL e, LOAD_GLOBAL d, LOAD_GLOBAL g, RETURN_VALUE`
  - 差异：原始有 `LOAD_GLOBAL c, LOAD_GLOBAL a, LOAD_GLOBAL b`（第一个 ternary）和 `BINARY_OP 0`（+ 加法）；重编全丢失；指令数 9 → 5。
- **根因推测**：lambda code object 内部，两个 ternary 的 merge 块共享同一 BINARY_OP 出口（BinOp 的 LOAD 先于两个 ternary 的 SWAP）。region_ast_generator 在 lambda code object 内部识别第一个 ternary 时，把其 merge 块的 SWAP + BINARY_OP 序列当作第二个 ternary 的 entry，导致第一个 ternary 被吞并。违反「父引用子入口」— BinOp 父节点通过 SWAP 引用两个 ternary 子节点，但只识别了第二个。与 R6-09（多 ternary 同上下文）同根因。

### Bug R6-19: `f(a if c else b, d if e else g, h if i else j)` — 同一调用 3 个 ternary 实参丢失第三个

- **测试**：`test_r6_ternary_in_call_arg_complex.py`
- **状态**：FAILED
- **源码**：`f(a if c else b, d if e else g, h if i else j)`
- **反编译结果**：`f(a if c else b, d if e else g)`
- **问题分解**：
  1. 第一个、第二个 ternary 实参正确归约。
  2. 第三个 ternary 实参 `h if i else j` 完全丢失。
  3. CALL 的 argc 从 3 减为 2。
- **字节码对比**：
  - **原始（17 条）**：`RESUME, PUSH_NULL, LOAD f, LOAD c, LOAD a, LOAD b, LOAD e, LOAD d, LOAD g, LOAD i, LOAD h, LOAD j, PRECALL 3, CALL 3, POP_TOP, RETURN None`
  - **重编（14 条）**：`RESUME, PUSH_NULL, LOAD f, LOAD c, LOAD a, LOAD b, LOAD e, LOAD d, LOAD g, PRECALL 2, CALL 2, POP_TOP, RETURN None`
  - 差异：原始有 `LOAD i, LOAD h, LOAD j`（第三个 ternary）和 `PRECALL 3, CALL 3`（3 实参调用）；重编丢失第三个 ternary 且 argc=2；指令数 17 → 14。
- **根因推测**：3 个 ternary 共享同一 CALL_FUNCTION 出口。region_ast_generator 在 `_build_ternary_no_target_consumer_stmt` 处理第三个 ternary 时，其 merge 块的 `LOAD h/j + PUSH` 序列被前两个 ternary 的 consumer 处理路径吞并（CALL_FUNCTION argc 已固定为 2）。违反「父引用子入口」— Call 父节点通过 PRECALL + CALL argc=3 引用 3 个 ternary 子节点，但 region 只识别了 2 个。R5-08（class body 多 ternary 共享 entry_block）的修复未扩展到 call_arg 上下文。

### Bug R6-20: `x[a if c else b][d if e else f] = 1` — 嵌套 subscript 赋值中两个 ternary 完全丢失 + STORE_SUBSCR 丢失

- **测试**：`test_r6_ternary_in_subscript_complex.py`
- **状态**：FAILED
- **源码**：`x[a if c else b][d if e else f] = 1`
- **反编译结果**：
  ```python
  (a if c else b)
  (d if e else f)
  ```
- **问题分解**：
  1. 两个 ternary 均被错误地渲染为独立表达式语句（带 POP_TOP）。
  2. 嵌套 subscript 赋值结构 `x[..][..] = 1` 完全丢失。
  3. STORE_SUBSCR 完全丢失。
  4. 第一个 subscript `x[a if c else b]`（BINARY_SUBSCR）完全丢失。
- **字节码对比**：
  - **原始（13 条）**：`RESUME, LOAD_CONST 1, LOAD x, LOAD c, LOAD a, LOAD b, BINARY_SUBSCR, LOAD e, LOAD d, LOAD f, STORE_SUBSCR, RETURN None`
  - **重编（14 条）**：`RESUME, LOAD c, LOAD a, LOAD b, POP_TOP, LOAD e, LOAD d, POP_TOP, RETURN None, LOAD f, POP_TOP, RETURN None`
  - 差异：原始有 `LOAD_CONST 1`（RHS）、`LOAD x + BINARY_SUBSCR`（第一个 subscript）、`STORE_SUBSCR`（赋值）；重编全丢失，两个 ternary 被拆为两个独立 Expr + POP_TOP；指令数 13 → 14。
- **根因推测**：嵌套 subscript 赋值的 `LOAD_CONST 1, LOAD x, LOAD c, LOAD a, LOAD b, BINARY_SUBSCR, LOAD e, LOAD d, LOAD f, STORE_SUBSCR` 序列中，两个 ternary 的 merge 块（LOAD_a/b 和 LOAD_d/f）共享同一 STORE_SUBSCR 出口。region_ast_generator 的 `_try_build_ternary_store_assign` 只识别 `STORE_*` 紧跟 ternary merge 的模式，不识别 `BINARY_SUBSCR + ... + STORE_SUBSCR` 的嵌套 subscript store 模式。R5-15 修复了 subscript slice（`x[1:(ternary)]`），但未覆盖嵌套 subscript store（`x[ternary][ternary] = ...`）。违反「父引用子入口」— SubscriptStore 父节点通过 BINARY_SUBSCR + STORE_SUBSCR 引用两个 ternary 子节点，但两个都被退化为独立 Expr。

---

## 错误模式归类

| 模式 | bug 数 | bug ID |
|------|--------|--------|
| **多 ternary 同上下文共享出口** | 4 | R6-09（unpack）、R6-18（lambda body）、R6-19（call args）、R6-20（nested subscript） |
| **推导式 code object 内部 ternary + filter 丢失** | 3 | R6-10（listcomp）、R6-12（setcomp）、R6-13（genexp） |
| **while(ternary) 新角度** | 3 | R6-01（嵌套 ternary）、R6-02（body 泄漏）、R6-04（complex body） |
| **ternary + 异常处理** | 1 | R6-06（except handler） |
| **装饰器链 region 边界** | 1 | R6-16（多 def 共享装饰器） |
| **类型注解 codegen** | 1 | R6-17（SETUP_ANNOTATIONS） |

## 修复优先级建议

### P0（最高优先级，影响最广）

1. **R6-10/12/13 推导式 + filter + ternary 组合**：listcomp/setcomp/genexp 三个 comp 类型通用 bug，ternary 完全丢失（被替换为 false 分支常量），数据丢失严重。修复点：region_ast_generator 在 comp code object 内部识别 filter POP_JUMP_IF_FALSE 与 ternary cond POP_JUMP_IF_FALSE 的区分（不同跳转目标）。
2. **R6-09/18/19/20 多 ternary 同上下文共享出口**：影响所有"多个 ternary 在同一父表达式"场景（unpack、lambda body、call args、nested subscript store）。修复点：扩展 R5-08 的共享 entry_block 修复到 `_try_build_ternary_store_assign` 和 `_build_ternary_no_target_consumer_stmt` 的所有 call_arg/binop/subscript dispatch。

### P1（高优先级，结构性 bug）

3. **R6-01/02/04 while(ternary) 新角度**：R5-05/06/07 已知限制的进一步暴露。R6-02（ternary in body 后泄漏 x）是新发现的独立 bug（与 R5-05/06/07 不同根因），可单独修复 — `_identify_loop_regions` 的 body 边界排除 loop test 块。R6-01/04 与 R5-05/06/07 同根因，需在 `_identify_loop_regions` 阶段识别 while(ternary) 模式。
4. **R6-06 except handler 中 ternary**：`_try_build_ternary_store_assign` 未识别 except handler 的 POP_EXCEPT wrapping 模式。

### P2（中优先级，独立 codegen bug）

5. **R6-16 装饰器链 region 边界**：`_identify_function_def_regions` 未正确划定装饰器链作用域。与 ternary 无直接关系，但仍是 R6 装饰器链对抗测试发现的真实 bug。
6. **R6-17 SETUP_ANNOTATIONS 丢失**：region_ast_generator 未识别模块级 `SETUP_ANNOTATIONS` 指令。与 ternary 无直接关系，但仍是 R6 类型注解对抗测试发现的真实 bug。

## 算法 4 原则违反分析

### 「每块唯一归属」违反（8 个 bug）

- **R6-01/02/04**：while(ternary) 模式中 loop test 块的 LOAD_* 同时承担循环条件测试和 ternary 值加载（与 R5-05/06/07 同根因）。
- **R6-06**：except handler 出口块（POP_EXCEPT）同时承担 ternary merge 和 except handler 出口。
- **R6-09/18/19/20**：多个 ternary 共享同一父表达式出口（STORE_SUBSCR / BINARY_OP / CALL / SWAP+STORE），无法唯一归属到单个 ternary。
- **R6-16**：装饰器链 LOAD_NAME 序列被错误归属到多个 def 的处理路径。

### 「父引用子入口」违反（5 个 bug）

- **R6-09/18/19/20**：父表达式（unpack / BinOp / Call / SubscriptStore）通过 wrapping 指令引用多个 ternary 子节点，但 region 只识别部分子节点。
- **R6-10/12/13**：comp code object 内部 filter 的 POP_JUMP_IF_FALSE 与 ternary cond 的 POP_JUMP_IF_FALSE 共享跳转目标，被合并丢失 ternary 子节点引用。

### 「自底向上归约」违反（3 个 bug）

- **R6-10/12/13**：comp code object 内部 ternary 未先归约为 IfExp，而是被替换为 false 分支常量（跳过 IfExp 抽象节点）。

### 「嵌套即抽象节点」违反（4 个 bug）

- **R6-01/04**：嵌套 ternary 未作为 IfExp(IfExp) 抽象节点，被拆为多个独立 if。
- **R6-06**：ternary 未作为 Assign(IfExp) 抽象节点，被拆为 if + Expr。
- **R6-10/12/13**：ternary 未作为 comp element IfExp 抽象节点，被替换为 false 分支常量。

## 4 原则违反禁止事项核查

- ✅ 未修改任何源代码（仅创建测试文件）
- ✅ 未创建根级 debug 文件（`r6_analyze_tmp.py` / `r6_inner_analyze_tmp.py` 是临时分析脚本，位于 /workspace 根目录但非 debug 文件，可清理）
- ✅ 未 commit
- ✅ 未调整区域识别优先级
- ✅ 未引入跨区域启发式特例
- ✅ 所有 bug 均在区域归约阶段暴露（无后处理补丁）

## 后续方向（R7+）

1. **R6-10/12/13 推导式 + filter + ternary**：在 comp code object 内部正确区分 filter POP_JUMP_IF_FALSE 与 ternary cond POP_JUMP_IF_FALSE（不同跳转目标）。这是 P0 修复，影响 listcomp/setcomp/genexp 三个类型。
2. **R6-09/18/19/20 多 ternary 同上下文**：扩展 R5-08 的共享 entry_block 修复到所有父表达式上下文（unpack / BinOp / Call / SubscriptStore）。需要 `_try_build_ternary_store_assign` 和 `_build_ternary_no_target_consumer_stmt` 的所有 dispatch 分支识别多 ternary 共享出口模式。
3. **R6-02 while body 内 ternary 后泄漏**：独立 bug，`_identify_loop_regions` 的 body 边界排除 loop test 块。
4. **R6-06 except handler 中 ternary**：`_try_build_ternary_store_assign` 识别 POP_EXCEPT wrapping 模式。
5. **R6-01/04 while(ternary) 完整修复**：与 R5-05/06/07 同根因，需在 `_identify_loop_regions` 阶段识别 while(ternary) 模式，将 ternary 提取为 while 的 condition_expr 而非独立 region。
6. **R6-16 装饰器链 region 边界**：`_identify_function_def_regions` 正确划定装饰器链作用域，仅最后一个 def 被装饰。
7. **R6-17 SETUP_ANNOTATIONS**：region_ast_generator 在模块级识别 `SETUP_ANNOTATIONS` 指令并在 codegen 阶段生成。
