# LOOP 区域 Round 03 测试发现报告

## 基线

- **反编译器**：pythoncdc（`core/cfg/region_analyzer.py` + `core/cfg/region_ast_generator.py`）
- **运行环境**：Python 3.11.15
- **测试框架**：`tests/exhaustive/base.py::ExhaustiveTestCase.verify_decompilation()`
  （编译 → 反编译 → 语法检查 → 重编译 → `_compare_code_objects` 字节码等价比较）
- **Round 01 状态**：已修复 9 个 bug；已知限制 5 个（#5 while 三元条件 / #10 try-except-else-finally / #13 continue 嵌套 if / #14 四操作数链式比较 / #15 嵌套 for-else）。
- **Round 02 状态**：已修复 12 个 bug（6 类根因 A–F）。
- **本 Round 范围**：仅覆盖与 R01 16 个模式、5 个已知限制及 R02 12 个模式不同的新模式；不修改反编译器源代码。
- **验证命令**：`timeout 280 python -m pytest tests/exhaustive/loop/round_03/ -q`
- **结果**：`12 failed`（全部为真实反编译错误，0 skip / 0 pass / 0 error）。

测试目录：`/workspace/tests/exhaustive/loop/round_03/`

字节码 diff 说明：过滤跳转/对齐指令（JUMP_*/FOR_ITER/SEND/NOP/CACHE/POP_JUMP_*）后比较操作码序列。`ORIG` 为源码编译结果，`RECOMP` 为反编译结果重编译结果。

---

## 错误 01 — for + try/finally + break（函数级，整个 for 循环丢失）

- **测试文件**：`tests/exhaustive/loop/round_03/test_r3_for_try_finally_break_func.py`
- **REGION_TYPE**：FOR_LOOP
- **源码**：
  ```python
  def f():
      for i in r:
          try:
              if i:
                  break
          finally:
              cleanup()
  ```
- **反编译结果**：
  ```python
  def f():
      try:
          if i:
              cleanup()
              return None
      finally: cleanup()
  ```
- **失败类型**：字节码不匹配（语义错误：**for 循环完全消失**，`break` 退化为 `return None`，`cleanup()` 被当作 if 体，循环变量 `i` 变成自由全局）。
- **字节码 diff**（f 函数体嵌套 code object，指令数同为 27，但操作码序列不同）：
  - ORIG (27): `RESUME LOAD_GLOBAL GET_ITER STORE_FAST LOAD_FAST LOAD_GLOBAL PRECALL CALL POP_TOP POP_TOP LOAD_CONST RETURN_VALUE LOAD_GLOBAL PRECALL CALL POP_TOP PUSH_EXC_INFO LOAD_GLOBAL PRECALL CALL POP_TOP RERAISE COPY POP_EXCEPT RERAISE LOAD_CONST RETURN_VALUE`
  - RECOMP (27): `RESUME LOAD_GLOBAL LOAD_GLOBAL PRECALL CALL POP_TOP LOAD_GLOBAL PRECALL CALL POP_TOP LOAD_CONST RETURN_VALUE LOAD_GLOBAL PRECALL CALL POP_TOP LOAD_CONST RETURN_VALUE PUSH_EXC_INFO LOAD_GLOBAL PRECALL CALL POP_TOP RERAISE COPY POP_EXCEPT RERAISE`
  - ORIG 含 `GET_ITER/STORE_FAST/LOAD_FAST`（for 循环指令），RECOMP 完全缺失循环指令。
- **疑似根因**：try-finally 区域先于 loop 归约（`_identify_try_except_regions` region_analyzer.py:5281 在 `_identify_loop_regions` region_analyzer.py:2904 之前调用）。与 R01 #3（**模块级** `for+try/finally+break`，已修复）不同，本例为**函数级**：函数尾部的隐式 `return None`（`LOAD_CONST None; RETURN_VALUE`）使 break 目标与 try-finally 的自然出口在函数级 CFG 尾部汇聚，try-finally 把含 break 的循环体吞为自身 body，LoopRegion 不再识别（违反原则 1「自底向上」+ 原则 2「每块唯一归属」）。R01 #3 修复仅覆盖模块级尾部 `return None` 模式，未覆盖函数级 break 内联。

---

## 错误 02 — while + try/finally + continue（while 循环被并入 finally 块）

- **测试文件**：`tests/exhaustive/loop/round_03/test_r3_while_try_finally_continue.py`
- **REGION_TYPE**：WHILE_LOOP
- **源码**：
  ```python
  while a:
      try:
          do()
      finally:
          if b:
              continue
  ```
- **反编译结果**：
  ```python
  try:
      pass
  finally:
      if b:
          pass
  while a:
      if b:
          continue
  ```
- **失败类型**：字节码不匹配（语义错误：**while 循环被移入 finally 块内部**，try 体退化为 `pass`，`do()` 丢失，finally 的 `if b: continue` 退化为 `if b: pass`，循环体被剥离）。
- **字节码 diff**：
  - ORIG (21): `RESUME LOAD_NAME PUSH_NULL LOAD_NAME PRECALL CALL POP_TOP LOAD_NAME PUSH_EXC_INFO LOAD_NAME POP_TOP POP_EXCEPT RERAISE COPY POP_EXCEPT RERAISE LOAD_NAME LOAD_CONST RETURN_VALUE LOAD_CONST RETURN_VALUE`
  - RECOMP (18): `RESUME LOAD_NAME LOAD_NAME LOAD_NAME LOAD_NAME LOAD_CONST RETURN_VALUE LOAD_CONST RETURN_VALUE PUSH_EXC_INFO LOAD_NAME LOAD_NAME LOAD_NAME LOAD_NAME RERAISE COPY POP_EXCEPT RERAISE`
  - ORIG 含 `PUSH_NULL/LOAD_NAME do/PRECALL/CALL/POP_TOP`（try 体 `do()`），RECOMP 完全缺失。
- **疑似根因**：try-finally 区域归约（`_identify_try_except_regions` region_analyzer.py:5281）把 while 的 header/body 块并入 finally handler。continue 在 finally 块内的归属（`_detect_break_continue` region_analyzer.py:4262）与 try-finally 自然出口混淆，导致 while LoopRegion（`_identify_loop_regions` region_analyzer.py:2904）的 header 被吞，循环被推到 try-finally 之外但 body 错位。与 R01 #1（`while True + continue`，已修复）和 R01 #2（`for + try/except + break/continue`，已修复）均不同——本例为 **try/finally（无 except）+ continue 在 finally 块内**。

---

## 错误 03 — for + match 语句（match subject 丢失为 `_`，case 绑定错乱）

- **测试文件**：`tests/exhaustive/loop/round_03/test_r3_for_match_body.py`
- **REGION_TYPE**：FOR_LOOP
- **源码**：
  ```python
  for i in r:
      match i:
          case 1:
              x = 1
          case _:
              y = 2
  ```
- **反编译结果**：
  ```python
  for i in r:
      match _:
          case 1 as x:
              x = 1
              continue
          case _:
              y = 2
  ```
- **失败类型**：字节码不匹配（语义错误：**match subject `i` 丢失为 `_`**，`case 1:` 错误添加 `as x` 绑定并插入虚假 `continue`）。
- **字节码 diff**：
  - ORIG (13): `RESUME LOAD_NAME GET_ITER STORE_NAME LOAD_NAME LOAD_CONST COMPARE_OP LOAD_CONST STORE_NAME LOAD_CONST STORE_NAME LOAD_CONST RETURN_VALUE`
  - RECOMP (16): `RESUME LOAD_NAME GET_ITER STORE_NAME LOAD_NAME COPY LOAD_CONST COMPARE_OP STORE_NAME LOAD_CONST STORE_NAME POP_TOP LOAD_CONST STORE_NAME LOAD_CONST RETURN_VALUE`
  - RECOMP 多出 `COPY ... STORE_NAME`（虚假绑定 `as x`）与 `POP_TOP`（虚假 continue）。
- **疑似根因**：`_identify_match_regions`（region_analyzer.py:8585）在 for 循环体内归约时，把 for-target 块的 `STORE_NAME i` 与 match subject 的 `LOAD_NAME i` 混淆，subject 退化为 `MATCH_NONE`（输出 `_`）。case pattern 的 `COMPARE_OP` 后的 `STORE_NAME x`（case 体赋值）被误识别为 case 绑定 `as x`，case 末尾 fall-through 到回边被误识为 `continue`。违反原则 2（每块唯一归属）——for-target 指令被 match 区域与循环体块双重归属。

---

## 错误 04 — while + 元组解包赋值（`x, y = pair` 退化为 `x = pair`）

- **测试文件**：`tests/exhaustive/loop/round_03/test_r3_while_tuple_unpack_body.py`
- **REGION_TYPE**：WHILE_LOOP
- **源码**：
  ```python
  while a:
      x, y = pair
  ```
- **反编译结果**：
  ```python
  while a:
      x = pair
  ```
- **失败类型**：字节码不匹配（语义错误：**`UNPACK_SEQUENCE` 丢失**，`y` 目标丢失，元组解包退化为单目标赋值）。
- **字节码 diff**：
  - ORIG (11): `RESUME LOAD_NAME LOAD_NAME UNPACK_SEQUENCE STORE_NAME STORE_NAME LOAD_NAME LOAD_CONST RETURN_VALUE LOAD_CONST RETURN_VALUE`
  - RECOMP (9): `RESUME LOAD_NAME LOAD_NAME STORE_NAME LOAD_NAME LOAD_CONST RETURN_VALUE LOAD_CONST RETURN_VALUE`
  - ORIG 含 `UNPACK_SEQUENCE` + 两个 `STORE_NAME`，RECOMP 缺 `UNPACK_SEQUENCE` 与第二个 `STORE_NAME y`。
- **疑似根因**：while 循环体块走 `_generate_block_statements`（region_ast_generator.py:29410）→ `_build_statement`（region_ast_generator.py:32426）。该方法仅识别末尾 `STORE_*` 为单目标赋值，**未识别 `UNPACK_SEQUENCE` 多目标解包**：`LOAD pair; UNPACK_SEQUENCE; STORE x; STORE y` 中，`UNPACK_SEQUENCE` 落入缓冲被忽略，前导 `LOAD pair` 与首个 `STORE x` 重建为 `x = pair`，`STORE y` 丢失。表达式重建器 `expr_reconstructor.reconstruct` 不识别 `UNPACK_SEQUENCE`。违反原则 2（每块唯一归属）——`y` 目标的 STORE 指令被丢弃。

---

## 错误 05 — for + starred 解包赋值（`a, *b = c` 退化为 `a = c`）

- **测试文件**：`tests/exhaustive/loop/round_03/test_r3_for_star_unpack_body.py`
- **REGION_TYPE**：FOR_LOOP
- **源码**：
  ```python
  for i in r:
      a, *b = c
  ```
- **反编译结果**：
  ```python
  for i in r:
      a = c
  ```
- **失败类型**：字节码不匹配（语义错误：**`UNPACK_EX` 与 `*b` 目标丢失**，starred 解包退化为单目标赋值）。
- **字节码 diff**：
  - ORIG (10): `RESUME LOAD_NAME GET_ITER STORE_NAME LOAD_NAME UNPACK_EX STORE_NAME STORE_NAME LOAD_CONST RETURN_VALUE`
  - RECOMP (8): `RESUME LOAD_NAME GET_ITER STORE_NAME LOAD_NAME STORE_NAME LOAD_CONST RETURN_VALUE`
  - ORIG 含 `UNPACK_EX` + 两个 `STORE_NAME`，RECOMP 缺 `UNPACK_EX` 与第二个 `STORE_NAME b`。
- **疑似根因**：for 循环回边块走 `_generate_stmts_from_instrs`（region_ast_generator.py:32176）。该方法处理 `STORE_SUBSCR/STORE_ATTR/DELETE_*/STORE_FAST/POP_TOP`，**未处理 `UNPACK_EX`/`UNPACK_SEQUENCE`**。`LOAD c; UNPACK_EX; STORE a; STORE b` 中 `UNPACK_EX` 落入缓冲，`STORE a` 触发 `_build_store_statement` 重建为 `a = c`，`STORE b` 丢失。与错误 04（while 路径）证实该缺陷跨 for/while 两条语句生成路径共存。违反原则 2。

---

## 错误 06 — for + augmented subscript 赋值（`d[k] += 1` 错乱为 `k[1] = d`）

- **测试文件**：`tests/exhaustive/loop/round_03/test_r3_for_augsubscript_body.py`
- **REGION_TYPE**：FOR_LOOP
- **源码**：
  ```python
  for i in r:
      d[k] += 1
  ```
- **反编译结果**：
  ```python
  for i in r:
      k[1] = d
  ```
- **失败类型**：字节码不匹配（语义错误：**augmented subscript 赋值完全错乱**——容器/索引/值三者颠倒，`+= 1` 退化为 `k[1] = d`）。
- **字节码 diff**：
  - ORIG (16): `RESUME LOAD_NAME GET_ITER STORE_NAME LOAD_NAME LOAD_NAME COPY COPY BINARY_SUBSCR LOAD_CONST BINARY_OP SWAP SWAP STORE_SUBSCR LOAD_CONST RETURN_VALUE`
  - RECOMP (10): `RESUME LOAD_NAME GET_ITER STORE_NAME LOAD_NAME LOAD_NAME LOAD_CONST STORE_SUBSCR LOAD_CONST RETURN_VALUE`
  - ORIG 含 `COPY; COPY; BINARY_SUBSCR; LOAD_CONST 1; BINARY_OP +=; SWAP; SWAP; STORE_SUBSCR`（aug subscript 协议），RECOMP 缺 `COPY/COPY/BINARY_SUBSCR/BINARY_OP/SWAP/SWAP`，仅剩 `LOAD d; LOAD k; LOAD_CONST 1; STORE_SUBSCR`。
- **疑似根因**：`_generate_stmts_from_instrs`（region_ast_generator.py:32176）的 `STORE_SUBSCR` 分支（行 32227）用 `_split_subscr_operands` 把缓冲切分为 value/container/index。但 aug subscript 的 `COPY; COPY; BINARY_SUBSCR; BINARY_OP` 序列使缓冲切分错位：`d`（value）被当作 index，`k`（container）被当作 value，常量 `1`（BINARY_OP 右操作数）被当作 index，重建为 `k[1] = d`。该方法**未识别 augmented subscript 的 COPY/BINARY_OP 协议**，未重建为 `AugAssign(targets=[Subscript], op=Add, value=Constant(1))`。违反原则 2。

---

## 错误 07 — while + 链式赋值（`x = y = 1` 退化为 `x = 1`）

- **测试文件**：`tests/exhaustive/loop/round_03/test_r3_while_chained_assign.py`
- **REGION_TYPE**：WHILE_LOOP
- **源码**：
  ```python
  while a:
      x = y = 1
  ```
- **反编译结果**：
  ```python
  while a:
      x = 1
  ```
- **失败类型**：字节码不匹配（语义错误：**`COPY` 链式赋值丢失**，第二个目标 `y` 丢失）。
- **字节码 diff**：
  - ORIG (11): `RESUME LOAD_NAME LOAD_CONST COPY STORE_NAME STORE_NAME LOAD_NAME LOAD_CONST RETURN_VALUE LOAD_CONST RETURN_VALUE`
  - RECOMP (9): `RESUME LOAD_NAME LOAD_CONST STORE_NAME LOAD_NAME LOAD_CONST RETURN_VALUE LOAD_CONST RETURN_VALUE`
  - ORIG 含 `LOAD_CONST 1; COPY; STORE x; STORE y`，RECOMP 缺 `COPY` 与第二个 `STORE_NAME y`。
- **疑似根因**：`_generate_block_statements`（region_ast_generator.py:29410）→ `_build_statement` 不识别 `COPY` 链式赋值。`LOAD_CONST 1; COPY; STORE x; STORE y` 中，`COPY` 落入缓冲被忽略，`STORE x` 触发重建为 `x = 1`（值取 `LOAD_CONST 1`），`STORE y` 丢失。表达式重建器未把 `COPY` 解释为链式赋值的值共享。违反原则 2（`y` 目标丢失）。

---

## 错误 08 — while + 带注解赋值（`x: int = 1` 注解丢失）

- **测试文件**：`tests/exhaustive/loop/round_03/test_r3_while_annot_assign.py`
- **REGION_TYPE**：WHILE_LOOP
- **源码**：
  ```python
  while a:
      x: int = 1
  ```
- **反编译结果**：
  ```python
  while a:
      x = 1
  ```
- **失败类型**：字节码不匹配（语义错误：**`SETUP_ANNOTATIONS` 与注解存储丢失**，`x: int` 退化为 `x`）。
- **字节码 diff**：
  - ORIG (14): `RESUME SETUP_ANNOTATIONS LOAD_NAME LOAD_CONST STORE_NAME LOAD_NAME LOAD_NAME LOAD_CONST STORE_SUBSCR LOAD_NAME LOAD_CONST RETURN_VALUE LOAD_CONST RETURN_VALUE`
  - RECOMP (9): `RESUME LOAD_NAME LOAD_CONST STORE_NAME LOAD_NAME LOAD_CONST RETURN_VALUE LOAD_CONST RETURN_VALUE`
  - ORIG 含 `SETUP_ANNOTATIONS; LOAD_NAME int; STORE_NAME __annotations__[?]; ...; STORE_SUBSCR`（注解存储协议），RECOMP 缺 `SETUP_ANNOTATIONS`、`LOAD_NAME int`、`STORE_SUBSCR`（注解写入）。
- **疑似根因**：`_generate_block_statements`（region_ast_generator.py:29410）不识别 `SETUP_ANNOTATIONS` 前缀。带注解赋值在字节码中先 `SETUP_ANNOTATIONS`，再 `LOAD int; STORE_NAME __annotations__['x']`（或 `STORE_SUBSCR` 写入 `__annotations__` 字典），再 `LOAD_CONST 1; STORE_NAME x`。该方法把 `SETUP_ANNOTATIONS` 与 `LOAD int`/`STORE_SUBSCR` 当作噪声丢弃，仅保留 `LOAD_CONST 1; STORE x` 重建为 `x = 1`，注解 `: int` 完全丢失。未映射为 `AnnAssign(target=Name('x'), annotation=Name('int'), value=Constant(1))`。违反原则 2（注解指令被丢弃）。

---

## 错误 09 — while + del 属性（`del obj.attr` 退化为 `obj`）

- **测试文件**：`tests/exhaustive/loop/round_03/test_r3_while_del_attr.py`
- **REGION_TYPE**：WHILE_LOOP
- **源码**：
  ```python
  while a:
      del obj.attr
  ```
- **反编译结果**：
  ```python
  while a:
      obj
  ```
- **失败类型**：字节码不匹配（语义错误：**`DELETE_ATTR` 退化为 `POP_TOP`**，`del` 语句丢失，`obj` 变为裸表达式）。
- **字节码 diff**（指令数同为 9，但操作码不同）：
  - ORIG (9): `RESUME LOAD_NAME LOAD_NAME DELETE_ATTR LOAD_NAME LOAD_CONST RETURN_VALUE LOAD_CONST RETURN_VALUE`
  - RECOMP (9): `RESUME LOAD_NAME LOAD_NAME POP_TOP LOAD_NAME LOAD_CONST RETURN_VALUE LOAD_CONST RETURN_VALUE`
  - 指令 3：ORIG `DELETE_ATTR` vs RECOMP `POP_TOP`。
- **疑似根因**：R02 簇 E 修复在 `_generate_stmts_from_instrs`（region_ast_generator.py:32176，**for 回边块路径**）新增了 `DELETE_SUBSCR/DELETE_ATTR` → `_build_delete_stmt` 重建（行 32279）。但 **while 循环体块走 `_generate_block_statements`（region_ast_generator.py:29410）路径，该方法未镜像该修复**：`LOAD obj; DELETE_ATTR attr` 中 `DELETE_ATTR` 被当作未知指令，前驱 `LOAD obj` 残留缓冲被重建为孤立 `Expr(Name('obj'))`，`DELETE_ATTR` 退化为 `POP_TOP`。即 R02 簇 E 修复未传播到 while-body 语句生成路径。违反原则 2。

---

## 错误 10 — while + import 语句（`import os` 退化为 `os = None`）

- **测试文件**：`tests/exhaustive/loop/round_03/test_r3_while_import_body.py`
- **REGION_TYPE**：WHILE_LOOP
- **源码**：
  ```python
  while a:
      import os
      x = os
  ```
- **反编译结果**：
  ```python
  while a:
      os = None
      x = os
  ```
- **失败类型**：字节码不匹配（语义错误：**`IMPORT_NAME` 退化为 `LOAD_CONST None; STORE_NAME`**，import 语句丢失为 `os = None`，后续 `x = os` 取到 None）。
- **字节码 diff**：
  - ORIG (13): `RESUME LOAD_NAME LOAD_CONST LOAD_CONST IMPORT_NAME STORE_NAME LOAD_NAME STORE_NAME LOAD_NAME LOAD_CONST RETURN_VALUE LOAD_CONST RETURN_VALUE`
  - RECOMP (11): `RESUME LOAD_NAME LOAD_CONST STORE_NAME LOAD_NAME STORE_NAME LOAD_NAME LOAD_CONST RETURN_VALUE LOAD_CONST RETURN_VALUE`
  - ORIG 含 `LOAD_CONST 0; LOAD_CONST None; IMPORT_NAME os; STORE_NAME os`（import 协议），RECOMP 缺 `IMPORT_NAME` 与前导 `LOAD_CONST`，仅 `LOAD_CONST None; STORE_NAME os`。
- **疑似根因**：`_generate_block_statements`（region_ast_generator.py:29410）→ `_build_statement` 不识别 `IMPORT_NAME`/`IMPORT_FROM`。`import os` 的字节码 `LOAD_CONST 0; LOAD_CONST None; IMPORT_NAME os; STORE_NAME os` 中，`IMPORT_NAME` 落入缓冲被忽略，前导两个 `LOAD_CONST` 与末尾 `STORE_NAME os` 重建为 `os = None`（值取最后的 `LOAD_CONST None`）。未映射为 `ast.Import(names=[alias(name='os')])`。违反原则 2（import 指令被误为赋值）。

---

## 错误 11 — while + with 体内 return（`return 1` 退化为 `break`）

- **测试文件**：`tests/exhaustive/loop/round_03/test_r3_while_with_return_body.py`
- **REGION_TYPE**：WHILE_LOOP
- **源码**：
  ```python
  def f():
      while a:
          with ctx() as c:
              return 1
  ```
- **反编译结果**：
  ```python
  def f():
      while a:
          with ctx() as c: break
  ```
- **失败类型**：字节码不匹配（嵌套 code object 指令 13 参数 `1` vs `None`，`LOAD_CONST`）。
- **字节码 diff**（f 函数体嵌套 code object，指令 13 `LOAD_CONST` 的 argval）：
  - ORIG：`... LOAD_CONST 1; RETURN_VALUE`（return 1）
  - RECOMP：`... LOAD_CONST None; RETURN_VALUE`（break 隐式 return None）
  - `return 1` 退化为 `break`，返回值 `1` 丢失。
- **疑似根因**：`_identify_with_regions`（region_analyzer.py:8017）归约 with 块时，with body 内的 `return 1` 在循环上下文中被 `_detect_break_continue`（region_analyzer.py:4262）的 break 检测误判：with 的 `__exit__` 清理块 + `RETURN_VALUE` 模式被识别为循环 break（`POP_TOP + LOAD_CONST None + RETURN_VALUE` = break 的内联模式），而 `LOAD_CONST 1` 的真实 return 被丢弃。with-as 的 `STORE_FAST c` 与 return 的值栈交互使 return 被降级为 break。违反原则 2（return 值指令被丢弃）+ 原则 3（with 应作为抽象节点，return 嵌套入 with body 而非被循环 break 逻辑捕获）。

---

## 错误 12 — while + BoolOp 赋值体（回边重检块泄漏为裸 `a` 表达式语句）

- **测试文件**：`tests/exhaustive/loop/round_03/test_r3_while_boolop_body.py`
- **REGION_TYPE**：WHILE_LOOP
- **源码**：
  ```python
  while a:
      x = b or c
  ```
- **反编译结果**：
  ```python
  while a:
      x = (b or c)
      a
  ```
- **失败类型**：字节码不匹配（指令数 11 vs 13，RECOMP 多出 `LOAD_NAME a; POP_TOP`）。循环体末尾多出一条裸表达式语句 `a`。
- **字节码 diff**：
  - ORIG (11): `RESUME LOAD_NAME LOAD_NAME JUMP_IF_TRUE_OR_POP LOAD_NAME STORE_NAME LOAD_NAME LOAD_CONST RETURN_VALUE LOAD_CONST RETURN_VALUE`
  - RECOMP (13): `RESUME LOAD_NAME LOAD_NAME JUMP_IF_TRUE_OR_POP LOAD_NAME STORE_NAME LOAD_NAME POP_TOP LOAD_NAME LOAD_CONST RETURN_VALUE LOAD_CONST RETURN_VALUE`
  - RECOMP 多出 `LOAD_NAME a; POP_TOP`（裸 `a` 表达式语句）。
- **疑似根因**：while 条件 `a` 在回边处的重检块（`LOAD a; POP_JUMP_BACKWARD → header`）未被抑制，被 `_generate_block_statements`（region_ast_generator.py:29410）当作循环体末尾的独立表达式语句发射为 `Expr(Name('a'))`。R02 簇 B 修复仅覆盖**重检块被 IfRegion 吸收为 elif/else 分支**的场景（`_check_elif_chain` 过滤 BACKWARD 条件跳转块）；本例循环体**无 IfRegion**（仅 `x = b or c`），重检块不被 IfRegion 逻辑过滤，直接泄漏为裸 Expr。即 R02 簇 B 修复对「无 if 的 while body」回边重检抑制不完整。与 R02 簇 B（break in if/elif → 重检泄漏为 `elif a: pass / else: break`）触发与表现均不同：本例无 break、无 if/elif，泄漏为裸 `a` Expr。

---

## 汇总

| # | 错误描述 | 测试文件 | 根因分类 |
|---|---------|---------|---------|
| 01 | for+try/finally+break（函数级）for 循环丢失 | test_r3_for_try_finally_break_func | try-finally 吞 loop（函数级） |
| 02 | while+try/finally+continue while 被并入 finally | test_r3_while_try_finally_continue | try-finally 吞 loop + continue 归属 |
| 03 | for+match subject 丢失为 `_` + case 绑定错乱 | test_r3_for_match_body | match subject 归属 |
| 04 | while+元组解包 `x,y=pair`→`x=pair` | test_r3_while_tuple_unpack_body | UNPACK_SEQUENCE 重建缺失（while 路径） |
| 05 | for+starred 解包 `a,*b=c`→`a=c` | test_r3_for_star_unpack_body | UNPACK_EX 重建缺失（for 路径） |
| 06 | for+aug subscript `d[k]+=1`→`k[1]=d` | test_r3_for_augsubscript_body | aug subscript COPY/BINARY_OP 协议未识别 |
| 07 | while+链式赋值 `x=y=1`→`x=1` | test_r3_while_chained_assign | COPY 链式赋值未识别 |
| 08 | while+注解赋值 `x:int=1`→`x=1` | test_r3_while_annot_assign | SETUP_ANNOTATIONS/注解存储未识别 |
| 09 | while+del 属性 `del obj.attr`→`obj` | test_r3_while_del_attr | DELETE_ATTR 修复未传播到 while 路径 |
| 10 | while+import `import os`→`os=None` | test_r3_while_import_body | IMPORT_NAME 未识别 |
| 11 | while+with 体内 return `return 1`→`break` | test_r3_while_with_return_body | with+return 被循环 break 误判 |
| 12 | while+BoolOp 赋值体 回边重检泄漏为裸 `a` Expr | test_r3_while_boolop_body | 回边重检抑制不完整（无 if 场景） |

**根因聚类**：
- **try-finally 吞 loop（函数级/continue 场景）**（01/02）：`_identify_try_except_regions`（region_analyzer.py:5281）在 `_identify_loop_regions`（region_analyzer.py:2904）之前归约，把含 break/continue 的循环体吞为自身 body/handler；R01 #3 仅修复模块级 break 场景，函数级 break 与 continue-in-finally 未覆盖。
- **match subject 归属**（03）：`_identify_match_regions`（region_analyzer.py:8585）与 for-target 块的指令混淆。
- **UNPACK_SEQUENCE/UNPACK_EX 重建缺失**（04/05）：`_generate_block_statements`（while 路径）与 `_generate_stmts_from_instrs`（for 路径）均未处理解包赋值，跨两条语句生成路径共存。
- **aug subscript COPY/BINARY_OP 协议未识别**（06）：`_generate_stmts_from_instrs` 的 STORE_SUBSCR 切分对 aug subscript 的 COPY 链错位。
- **COPY 链式赋值未识别**（07）：`_generate_block_statements` 不识别 `COPY` 值共享。
- **SETUP_ANNOTATIONS/注解存储未识别**（08）：`_generate_block_statements` 不识别注解赋值协议，未映射为 `AnnAssign`。
- **DELETE_ATTR 修复未传播到 while 路径**（09）：R02 簇 E 修复仅作用于 for 回边块路径 `_generate_stmts_from_instrs`，while 路径 `_generate_block_statements` 未镜像。
- **IMPORT_NAME 未识别**（10）：`_generate_block_statements` 不识别 import 协议，未映射为 `ast.Import`。
- **with+return 被循环 break 误判**（11）：`_identify_with_regions`（region_analyzer.py:8017）+ `_detect_break_continue`（region_analyzer.py:4262）把 with body 内 return 误判为 break。
- **回边重检抑制不完整（无 if 场景）**（12）：R02 簇 B 修复仅覆盖重检块被 IfRegion 吸收的场景，无 IfRegion 的 while body 重检块直接泄漏为裸 Expr。

共发现 **12 个** 真实 LOOP 反编译错误（均通过 `timeout 280 python -m pytest tests/exhaustive/loop/round_03/ -q` 实测失败确认，0 pass / 0 skip / 0 error），覆盖 10 类根因，与 R01 已修复的 9 个 bug、5 个已知限制及 R02 已修复的 12 个 bug 模式不重叠。

---

## 回归验证

`timeout 280 python -m pytest tests/exhaustive/while_loop/ tests/exhaustive/for_loop/ tests/exhaustive/loop/round_01/ tests/exhaustive/loop/round_02/ -q` →
`10 failed, 329 passed, 2 skipped in 3.43s`

- `tests/exhaustive/while_loop/` + `tests/exhaustive/for_loop/`：5 failed（基线既有 `l15whiletruebreak`/`wl30whilebreakintry` 等，未被 R02 顺带修复）
- `tests/exhaustive/loop/round_01/`：5 failed（R01 已知限制 #5/#10/#13/#14/#15），2 skipped
- `tests/exhaustive/loop/round_02/`：0 failed（12/12 全通过）

本 Round 仅新增测试文件，**未修改任何反编译器源代码**，基线无退化。
