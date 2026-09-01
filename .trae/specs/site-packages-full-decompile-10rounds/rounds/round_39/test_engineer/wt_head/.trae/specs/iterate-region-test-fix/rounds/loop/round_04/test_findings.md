# LOOP 区域 Round 04 测试发现报告

## 基线

- **反编译器**：pythoncdc（`core/cfg/region_analyzer.py` + `core/cfg/region_ast_generator.py`）
- **运行环境**：Python 3.11.15
- **测试框架**：`tests/exhaustive/base.py::ExhaustiveTestCase.verify_decompilation()`
  （编译 → 反编译 → `ast.parse` 语法检查 → 重编译 → `_compare_code_objects` 字节码等价比较）
- **Round 01 状态**：已修复 9 个 bug；5 个已知限制未修。
- **Round 02 状态**：已修复 12 个 bug（for-else / while 回边重检 / break 归属 / for-iter walrus / for body del / while body await）。
- **Round 03 状态**：已修复 12 个 bug（aug subscript / match subject / UNPACK_EX / try-finally吞loop / continue-in-finally / with+return误判break / tuple unpack / 链式赋值 / 注解赋值 / del attr / import / 回边重检无If）。
- **本 Round 范围**：仅覆盖与 R01–R03 已修复/已知模式不同的新模式；不修改反编译器源代码。
- **验证命令**：`timeout 280 python -m pytest tests/exhaustive/loop/round_04/ -q`
- **结果**：`12 failed`（全部为真实反编译错误，0 skip / 0 pass / 0 error）。

测试目录：`/workspace/tests/exhaustive/loop/round_04/`

字节码 diff 说明：过滤跳转/对齐指令（JUMP_FORWARD/JUMP_BACKWARD/JUMP_ABSOLUTE/POP_JUMP_*/FOR_ITER/SEND/NOP/CACHE）后比较操作码序列。`ORIG` 为源码编译结果，`RECOMP` 为反编译结果重编译结果。函数级用例比较 f 协程体的嵌套 code object。

---

## 错误 01 — while + `from m import x`（IMPORT_FROM 丢失为 `('x',)` 元组 + `import m as y`）

- **测试文件**：`tests/exhaustive/loop/round_04/test_r4_while_import_from.py`
- **REGION_TYPE**：WHILE_LOOP
- **源码**：
  ```python
  while a:
      from m import x
      y = x
  ```
- **反编译结果**：
  ```python
  while a:
      ('x',)
      import m as y
  ```
- **失败类型**：字节码不匹配（语义错误：`from m import x` 完全错乱——fromlist 元组 `('x',)` 泄漏为裸 Expr，`IMPORT_FROM` + `STORE_NAME x` 丢失，`y = x` 被误重建为 `import m as y`）。
- **字节码 diff**（模块级，指令数 15 vs 11）：
  - ORIG (15): `RESUME LOAD_NAME LOAD_CONST LOAD_CONST IMPORT_NAME IMPORT_FROM STORE_NAME POP_TOP LOAD_NAME STORE_NAME LOAD_NAME LOAD_CONST RETURN_VALUE LOAD_CONST RETURN_VALUE`
  - RECOMP (11): `RESUME LOAD_NAME LOAD_CONST LOAD_CONST IMPORT_NAME STORE_NAME LOAD_NAME LOAD_CONST RETURN_VALUE LOAD_CONST RETURN_VALUE`
  - ORIG 含 `IMPORT_FROM; STORE_NAME x; POP_TOP`，RECOMP 缺 `IMPORT_FROM`，多出的 `STORE_NAME` 把 `import m` 当作 `import m as y`。
- **疑似根因**：`_extract_imports_from_block_prefix`（region_ast_generator.py:141）的 IMPORT_NAME+IMPORT_FROM+STORE 检测仅在前驱块前缀扫描中触发，**while 循环体块走 `_generate_block_statements`（region_ast_generator.py:29711）** 时未调用该前缀抽取。`LOAD_CONST 0; LOAD_CONST ('x',); IMPORT_NAME m; IMPORT_FROM x; STORE_NAME x; POP_TOP` 中 `IMPORT_FROM` 落入缓冲被忽略，fromlist 元组 `('x',)` 残留为孤立 Expr，`IMPORT_NAME m` + 末尾 `STORE_NAME y`（实为 `y = x` 的 STORE）被 `_build_store_statement` 误拼为 `import m as y`。与 R03 #10（`import os`，IMPORT_NAME 无 IMPORT_FROM）不同——本例为 `from ... import`，含 IMPORT_FROM 协议，且错乱为另一合法但语义全非的 import 语句。违反原则 2（IMPORT_FROM 指令被丢弃）。

---

## 错误 02 — for + `from m import *`（IMPORT_STAR 整条语句丢失）

- **测试文件**：`tests/exhaustive/loop/round_04/test_r4_for_import_star.py`
- **REGION_TYPE**：FOR_LOOP
- **源码**：
  ```python
  for i in r:
      from m import *
      z = x
  ```
- **反编译结果**：
  ```python
  for i in r:
      z = x
  ```
- **失败类型**：字节码不匹配（语义错误：`from m import *` 整条语句消失，后续 `z = x` 取到未定义全局）。
- **字节码 diff**（模块级，指令数 12 vs 8）：
  - ORIG (12): `RESUME LOAD_NAME GET_ITER STORE_NAME LOAD_CONST LOAD_CONST IMPORT_NAME IMPORT_STAR LOAD_NAME STORE_NAME LOAD_CONST RETURN_VALUE`
  - RECOMP (8): `RESUME LOAD_NAME GET_ITER STORE_NAME LOAD_NAME STORE_NAME LOAD_CONST RETURN_VALUE`
  - ORIG 含 `LOAD_CONST 0; LOAD_CONST None; IMPORT_NAME; IMPORT_STAR`，RECOMP 缺 `LOAD_CONST×2; IMPORT_NAME; IMPORT_STAR`，整条星导入消失。
- **疑似根因**：`_generate_stmts_from_instrs`（region_ast_generator.py:32535，for 回边块路径）与 `_generate_block_statements`（region_ast_generator.py:29711）均**未识别 `IMPORT_STAR` 操作码**。`from m import *` 的字节码 `LOAD_CONST 0; LOAD_CONST None; IMPORT_NAME m; IMPORT_STAR` 中，`IMPORT_STAR` 不产生 STORE（直接把名字注入命名空间），无 STORE 触发语句重建，整条指令序列落入缓冲被全部丢弃。与错误 01（IMPORT_FROM）及 R03 #10（IMPORT_NAME+STORE）证实 import 协议三形态（IMPORT_NAME 单名 / IMPORT_NAME+IMPORT_FROM+STORE / IMPORT_NAME+IMPORT_STAR）在循环体内均存在重建缺口。违反原则 2（IMPORT_STAR 指令被丢弃）。

---

## 错误 03 — for + match 或模式（`case 1 | 2:` → `case 1 as y | 2 as y:` 语法错误）

- **测试文件**：`tests/exhaustive/loop/round_04/test_r4_for_match_or_pattern.py`
- **REGION_TYPE**：FOR_LOOP
- **源码**：
  ```python
  for i in r:
      match x:
          case 1 | 2:
              y = 1
          case _:
              y = 2
  ```
- **反编译结果**：
  ```python
  for i in r:
      match x:
          case 1 as y | 2 as y:
              y = 1
          case _:
              y = 2
              continue
  ```
- **失败类型**：语法错误（`case 1 as y | 2 as y:` 中同一名字 `y` 在 or-pattern 内重复绑定，且 `as` 绑定来自 case 体赋值而非模式捕获，CPython 拒绝）。
- **字节码 diff**：反编译结果无法重编译（`SyntaxError: invalid syntax`），无 RECOMP 序列。
- **疑似根因**：`_identify_match_regions`（region_analyzer.py:8636）+ `_is_wildcard_match_block`（region_analyzer.py:9528）对 or-pattern（`MatchOr`）的重建。or-pattern `1 | 2` 的字节码为 `COPY; LOAD_CONST 1; COMPARE_OP; COPY; LOAD_CONST 2; COMPARE_OP; POP_TOP; POP_TOP`（两个值模式短路或）。case 体的 `LOAD_CONST 1; STORE_NAME y`（`y = 1`）中 `STORE_NAME y` 被误识别为模式捕获 `as y`，附加到每个 or 分支（`1 as y | 2 as y`），且 case 末尾 fall-through 被误识为 `continue`。R03 #3 修复了字面量 `case 1:` 的 subject 丢失，但 or-pattern 的多 COMPARE_OP 链 + 捕获误判未覆盖。违反原则 2（case 体 STORE 被误为模式捕获）。

---

## 错误 04 — for + match 序列模式（`case [a, *b]:` → `case [a, *b] as i:` + 虚假 continue + 多余 STORE）

- **测试文件**：`tests/exhaustive/loop/round_04/test_r4_for_match_sequence.py`
- **REGION_TYPE**：FOR_LOOP
- **源码**：
  ```python
  for i in r:
      match s:
          case [a, *b]:
              x = a
          case _:
              x = 0
  ```
- **反编译结果**：
  ```python
  for i in r:
      match s:
          case [a, *b] as i:
              x = a
              continue
          case _:
              x = 0
              continue
  ```
- **失败类型**：字节码不匹配（语义错误：序列模式 `[a, *b]` 错误附加 `as i` 绑定（`i` 为 for-target），每个 case 体末尾插入虚假 `continue`，并多出一条 `STORE_NAME`）。
- **字节码 diff**（模块级，指令数 19 vs 22）：
  - ORIG (19): `RESUME LOAD_NAME GET_ITER STORE_NAME LOAD_NAME MATCH_SEQUENCE GET_LEN LOAD_CONST COMPARE_OP UNPACK_EX STORE_NAME STORE_NAME LOAD_NAME STORE_NAME POP_TOP LOAD_CONST STORE_NAME LOAD_CONST RETURN_VALUE`
  - RECOMP (22): `RESUME LOAD_NAME GET_ITER STORE_NAME LOAD_NAME COPY MATCH_SEQUENCE GET_LEN LOAD_CONST COMPARE_OP UNPACK_EX STORE_NAME STORE_NAME STORE_NAME LOAD_NAME STORE_NAME POP_TOP POP_TOP LOAD_CONST STORE_NAME LOAD_CONST RETURN_VALUE`
  - RECOMP 多出 `COPY`（虚假 `as i` 绑定）、一条 `STORE_NAME`、一条 `POP_TOP`（虚假 continue）。
- **疑似根因**：`_identify_match_regions`（region_analyzer.py:8636）对序列模式（`MATCH_SEQUENCE + GET_LEN + COMPARE_OP + UNPACK_EX`）的归约。for-target 块的 `STORE_NAME i` 与 match subject 的 `LOAD_NAME s` / 序列捕获的 `STORE_NAME a/b` 混淆，序列模式被误附加 `as i` 捕获（`COPY ... STORE_NAME`），case 末尾 fall-through 到回边被误识为 `continue`（`POP_TOP`）。R03 #3 修复字面量模式 subject，序列模式的 MATCH_SEQUENCE/UNPACK_EX 捕获归属未覆盖。违反原则 2（for-target 指令被 match 区域与捕获误归属）。

---

## 错误 05 — while + 嵌套 try/except（内层 try 被拆为 `else:` 块 + 外层 except 退化为 `if` → 语法错误）

- **测试文件**：`tests/exhaustive/loop/round_04/test_r4_while_nested_try.py`
- **REGION_TYPE**：WHILE_LOOP
- **源码**：
  ```python
  while a:
      try:
          try:
              do()
          except E1:
              x = 1
      except E2:
          y = 2
  ```
- **反编译结果**：
  ```python
  while a:
      try:
          do()
      except E1: x = 1
      else:
          try:
              pass
      if E2:
          pass
  ```
- **失败类型**：语法错误（`else:` 下 `try: pass` 缺 except/finally；外层 `except E2` 退化为独立 `if E2:`）。
- **字节码 diff**：反编译结果无法重编译（`SyntaxError: expected 'except' or 'finally' block`），无 RECOMP 序列。
- **疑似根因**：`_identify_try_except_regions`（region_analyzer.py:5303）对**嵌套 try（try 内含 try/except）**的归约。内层 try 的 except handler（`E1`）被提升为外层 try 的 handler，内层 try body 退化为 `do()`；外层 try 的 `except E2` handler 被剥离为独立 `if E2: pass`，外层 try body 末尾插入虚假 `else:` 子句（内含空 `try: pass`）。即嵌套 try 的内外层 handler 边界在循环体内被错位归并——内层 handler 被外层吞并、外层 handler 被外推为 if。R01 #10（try-except-else-finally）与 R03 #1/#2（try-finally吞loop）均未覆盖嵌套 try-except 的 handler 边界错位。违反原则 2（handler 块归属错位）+ 原则 3（嵌套 try 应作为抽象节点）。

---

## 错误 06 — while + try/finally + return（return 值路径被复制进 try body + finally 重复）

- **测试文件**：`tests/exhaustive/loop/round_04/test_r4_while_try_finally_return.py`
- **REGION_TYPE**：WHILE_LOOP
- **源码**：
  ```python
  def f():
      while a:
          try:
              if b:
                  return 1
          finally:
              cleanup()
  ```
- **反编译结果**：
  ```python
  def f():
      while a:
          try:
              if b:
                  cleanup()
                  return 1
              else:
                  cleanup()
          finally: cleanup()
  ```
- **失败类型**：字节码不匹配（语义错误：`finally: cleanup()` 被复制进 try body 的 `if b:` 真分支与 `else:` 分支，外层 `finally` 保留，导致 cleanup 被调用次数与原语义不符；return 值路径被错位）。
- **字节码 diff**（f 函数体嵌套 code object，指令数 27 vs 35）：
  - ORIG (27): `RESUME LOAD_GLOBAL LOAD_GLOBAL LOAD_GLOBAL PRECALL CALL POP_TOP LOAD_CONST RETURN_VALUE LOAD_GLOBAL PRECALL CALL POP_TOP PUSH_EXC_INFO LOAD_GLOBAL PRECALL CALL POP_TOP RERAISE COPY POP_EXCEPT RERAISE LOAD_GLOBAL LOAD_CONST RETURN_VALUE LOAD_CONST RETURN_VALUE`
  - RECOMP (35): `RESUME LOAD_GLOBAL LOAD_GLOBAL LOAD_GLOBAL PRECALL CALL POP_TOP LOAD_GLOBAL PRECALL CALL POP_TOP LOAD_CONST RETURN_VALUE LOAD_GLOBAL PRECALL CALL POP_TOP LOAD_GLOBAL PRECALL CALL POP_TOP PUSH_EXC_INFO LOAD_GLOBAL PRECALL CALL POP_TOP RERAISE COPY POP_EXCEPT RERAISE LOAD_GLOBAL LOAD_CONST RETURN_VALUE LOAD_CONST RETURN_VALUE`
  - RECOMP 多出两次 `LOAD_GLOBAL cleanup; PRECALL; CALL; POP_TOP`（cleanup 被复制进 try body），`LOAD_CONST RETURN_VALUE`（return）位置错位。
- **疑似根因**：`_identify_try_except_regions`（region_analyzer.py:5303）+ try-finally 归约对 **try body 内 `return`** 的处理。finally 块的清理代码（`LOAD_GLOBAL cleanup; CALL`）被复制到 try body 的 if 分支（`if b: cleanup(); return 1` 与 `else: cleanup()`），与外层 `finally: cleanup()` 共存，cleanup 调用翻倍。R03 #1（for+try/finally+break）修复了 break 被吞的场景，R03 #2（while+try/finally+continue）修复了 continue-in-finally；本例为 **try body 内 return**——return 的值栈与 finally 清理块的复制交互未覆盖，return 路径被 finally 复制污染。违反原则 2（finally 块被复制进 try body）。

---

## 错误 07 — while + try/finally + break 在 finally 块内（break 脱离 if 体）

- **测试文件**：`tests/exhaustive/loop/round_04/test_r4_while_try_finally_break_in_finally.py`
- **REGION_TYPE**：WHILE_LOOP
- **源码**：
  ```python
  while a:
      try:
          do()
      finally:
          if b:
              break
  ```
- **反编译结果**：
  ```python
  while a:
      try:
          do()
      finally:
          if b:
              pass
          break
  ```
- **失败类型**：字节码不匹配（语义错误：`if b: break` 中的 break 脱离 if 真分支，退化为独立 `break`，if 体退化为 `pass`——即 break 无条件执行，原条件 break 变为无条件 break）。
- **字节码 diff**（模块级，指令数 25 vs 21）：
  - ORIG (25): `RESUME LOAD_NAME PUSH_NULL LOAD_NAME PRECALL CALL POP_TOP LOAD_NAME LOAD_CONST RETURN_VALUE PUSH_EXC_INFO LOAD_NAME POP_TOP POP_EXCEPT LOAD_CONST RETURN_VALUE RERAISE COPY POP_EXCEPT RERAISE LOAD_NAME LOAD_CONST RETURN_VALUE LOAD_CONST RETURN_VALUE`
  - RECOMP (21): `RESUME LOAD_NAME PUSH_NULL LOAD_NAME PRECALL CALL POP_TOP LOAD_NAME LOAD_CONST RETURN_VALUE PUSH_EXC_INFO LOAD_NAME POP_TOP POP_EXCEPT LOAD_CONST RETURN_VALUE COPY POP_EXCEPT RERAISE LOAD_CONST RETURN_VALUE`
  - ORIG 含 `LOAD_NAME b; LOAD_CONST RETURN_VALUE ... LOAD_NAME LOAD_CONST RETURN_VALUE`（条件 break 跳转 + finally break 出口）；RECOMP 把 break 的 `LOAD_CONST RETURN_VALUE` 提前到 `POP_EXCEPT` 后无条件执行，缺条件跳转与 finally 的 break 出口块。
- **疑似根因**：`_detect_break_continue`（region_analyzer.py:4262）对 **finally 块内 break** 的归属处理。finally 块内 `if b: break` 的 break 块被识别为独立 break 出口，break 作为独立语句发射，原 `if b:` body 退化为 `pass`。finally 的异常清理路径（`PUSH_EXC_INFO ... RERAISE`）与 break 出口的 `LOAD_CONST None; RETURN_VALUE` 交互使 break 被从 if 体剥离为无条件 break。R03 #2（continue-in-finally）修复了 continue 场景，本例为 **break-in-finally**——break 的循环退出语义与 finally 清理的交互未覆盖。违反原则 2（break 脱离 if 体）。

---

## 错误 08 — while-else + else 内含 for 循环（else 块被丢弃，for 提升为循环后顺序语句）

- **测试文件**：`tests/exhaustive/loop/round_04/test_r4_while_else_for_in_else.py`
- **REGION_TYPE**：WHILE_LOOP
- **源码**：
  ```python
  def f():
      while a:
          if b:
              break
      else:
          for j in s:
              x = j
  ```
- **反编译结果**：
  ```python
  def f():
      while a:
          if b:
              break
      for j in s:
          x = j
  ```
- **失败类型**：字节码不匹配（语义错误：while-else 的 else 块被完全丢弃，else 内的 for 循环被提升为 while 之后的顺序语句——break 跳过 else 的语义丢失）。
- **字节码 diff**（f 函数体嵌套 code object，指令数 13 vs 11）：
  - ORIG (13): `RESUME LOAD_GLOBAL LOAD_GLOBAL LOAD_CONST RETURN_VALUE LOAD_GLOBAL LOAD_GLOBAL GET_ITER STORE_FAST LOAD_FAST STORE_FAST LOAD_CONST RETURN_VALUE`
  - RECOMP (11): `RESUME LOAD_GLOBAL LOAD_GLOBAL LOAD_GLOBAL LOAD_GLOBAL GET_ITER STORE_FAST LOAD_FAST STORE_FAST LOAD_CONST RETURN_VALUE`
  - ORIG 含 `LOAD_GLOBAL a; LOAD_CONST None; RETURN_VALUE`（break 出口的隐式 return None，区分 else 路径），RECOMP 缺该 break 出口块，for 循环直接接在 while 后（else 语义丢失）。
- **疑似根因**：`_find_loop_else`（region_analyzer.py:3982）while 分支对 **else 块内含嵌套循环** 的识别。else 块内的 for 循环（`GET_ITER; STORE_FAST; ...; JUMP_BACKWARD`）的回边块与 while 的 break 出口在函数尾部汇聚，else 块被误判为「非 else 顺序代码」而丢弃，for 循环被外推为 while 之后的兄弟语句。R02 #07（while-else+break+continue，else 内为简单赋值）与 R01 #4（while-else-return）的 else 识别未覆盖 else 内嵌套 LoopRegion 的场景——else 内循环的 GET_ITER/回边使 `_else_is_skipped_by_break` 误判。违反原则 2（else 块未被循环区域归属）。

---

## 错误 09 — async while + async with + return（`return 1` 退化为 `break`）

- **测试文件**：`tests/exhaustive/loop/round_04/test_r4_while_async_with_return.py`
- **REGION_TYPE**：WHILE_LOOP
- **源码**：
  ```python
  async def f():
      while a:
          async with ctx() as c:
              return 1
  ```
- **反编译结果**：
  ```python
  async def f():
      while a:
          async with ctx() as c: break
  ```
- **失败类型**：字节码不匹配（语义错误：`return 1` 退化为 `break`，返回值 `1` 丢失，协程返回 None 而非 1）。
- **字节码 diff**（f 协程体嵌套 code object，指令数同为 47，但指令 23 `JUMP_BACKWARD_NO_INTERRUPT` 的 argval 88 vs 86 不匹配）：
  - ORIG 指令 23: `JUMP_BACKWARD_NO_INTERRUPT argval=88`（return 路径的 await 轮询回边偏移）
  - RECOMP 指令 23: `JUMP_BACKWARD_NO_INTERRUPT argval=86`（break 路径的回边偏移，少了 return 值栈布局）
  - 操作码序列相同，但 break vs return 的代码布局使回边偏移不同，`_compare_code_objects` 捕获 argval 差异。
- **疑似根因**：`_identify_with_regions`（region_analyzer.py:8068）+ `_detect_break_continue`（region_analyzer.py:4262）对 **async with body 内 return** 的处理。async with 的协议（`BEFORE_ASYNC_WITH; GET_AWAITABLE; YIELD_VALUE; JUMP_BACKWARD_NO_INTERRUPT` + `__aexit__` 清理 `WITH_EXCEPT_START`）与 return 的值栈交互，使 return 被误判为循环 break（`LOAD_CONST None; RETURN_VALUE` = break 内联模式），`LOAD_CONST 1` 的真实 return 被丢弃。R03 #11（sync with+return→break）修复了同步 `with` 协议（`BEFORE_WITH`），async with 的 `BEFORE_ASYNC_WITH` + `__aexit__` await 轮询未覆盖。违反原则 2（return 值指令被丢弃）+ 原则 3（async with 应作抽象节点）。

---

## 错误 10 — async while + try/finally + await（try body 末尾插入虚假 `continue`）

- **测试文件**：`tests/exhaustive/loop/round_04/test_r4_async_while_try_finally.py`
- **REGION_TYPE**：WHILE_LOOP
- **源码**：
  ```python
  async def f():
      while a:
          try:
              await do()
          finally:
              cleanup()
  ```
- **反编译结果**：
  ```python
  async def f():
      while a:
          try:
              await do()
              continue
          finally: cleanup()
  ```
- **失败类型**：字节码不匹配（语义错误：try body 末尾 `await do()` 之后插入虚假 `continue`，使正常路径显式跳回循环头，与原隐式回边语义不符）。
- **字节码 diff**（f 协程体嵌套 code object，指令数 31 vs 28）：
  - ORIG (31): `RETURN_GENERATOR POP_TOP RESUME LOAD_GLOBAL LOAD_GLOBAL PRECALL CALL GET_AWAITABLE LOAD_CONST YIELD_VALUE RESUME JUMP_BACKWARD_NO_INTERRUPT POP_TOP LOAD_GLOBAL PRECALL CALL POP_TOP PUSH_EXC_INFO LOAD_GLOBAL PRECALL CALL POP_TOP RERAISE COPY POP_EXCEPT RERAISE LOAD_GLOBAL LOAD_CONST RETURN_VALUE LOAD_CONST RETURN_VALUE`
  - RECOMP (28): `RETURN_GENERATOR POP_TOP RESUME LOAD_GLOBAL LOAD_GLOBAL PRECALL CALL GET_AWAITABLE LOAD_CONST YIELD_VALUE RESUME JUMP_BACKWARD_NO_INTERRUPT POP_TOP LOAD_GLOBAL PRECALL CALL POP_TOP PUSH_EXC_INFO LOAD_GLOBAL PRECALL CALL POP_TOP RERAISE COPY POP_EXCEPT RERAISE LOAD_CONST RETURN_VALUE`
  - ORIG 含 `LOAD_GLOBAL a; LOAD_CONST None; RETURN_VALUE`（while 条件重检块 + 隐式回边）；RECOMP 缺该重检块，try body 末尾被插入虚假 `continue`（`LOAD_CONST RETURN_VALUE` 直接接在 try 后）。
- **疑似根因**：`_loop_generate_while`（region_ast_generator.py:3532）+ `_is_await_polling_loop`（region_analyzer.py:4744）对 **async while + try/finally + await** 的回边处理。await 的轮询自循环（`GET_AWAITABLE; YIELD_VALUE; JUMP_BACKWARD_NO_INTERRUPT`）与外层 while 的回边在 try/finally 上下文中混淆，while 条件重检块（`LOAD_GLOBAL a; ...; RETURN_VALUE`）被 try-finally 吞并/丢弃，try body 末尾被插入虚假 `continue` 替代隐式回边。R02 #12（while body await 退化为 if）修复了 await 轮询误抑制，本例为 **await 在 try/finally 内**——try-finally 把 await 轮询与 while 回边归并，重检块丢失、虚假 continue 插入。违反原则 2（重检块被吞）+ 原则 3（try-finally 应作抽象节点）。

---

## 错误 11 — while + with + break（`with ctx(): if b: break` 中 break 完全丢失）

- **测试文件**：`tests/exhaustive/loop/round_04/test_r4_while_with_break.py`
- **REGION_TYPE**：WHILE_LOOP
- **源码**：
  ```python
  def f():
      while a:
          with ctx() as c:
              if b:
                  break
      return 1
  ```
- **反编译结果**：
  ```python
  def f():
      while a:
          with ctx() as c:
              if b:
                  pass
  ```
- **失败类型**：字节码不匹配（语义错误：`with` body 内 `if b: break` 的 break 完全丢失，if 体退化为 `pass`——循环变为无限循环，原 break 退出语义丢失，函数尾的 `return 1` 也丢失）。
- **字节码 diff**（f 函数体嵌套 code object，指令数 33 vs 29）：
  - ORIG (33): `RESUME LOAD_GLOBAL LOAD_GLOBAL PRECALL CALL BEFORE_WITH STORE_FAST LOAD_GLOBAL LOAD_CONST LOAD_CONST LOAD_CONST PRECALL CALL POP_TOP LOAD_CONST LOAD_CONST LOAD_CONST PRECALL CALL POP_TOP PUSH_EXC_INFO WITH_EXCEPT_START RERAISE COPY POP_EXCEPT RERAISE POP_TOP POP_EXCEPT POP_TOP POP_TOP LOAD_GLOBAL LOAD_CONST RETURN_VALUE`
  - RECOMP (29): `RESUME LOAD_GLOBAL LOAD_GLOBAL PRECALL CALL BEFORE_WITH STORE_FAST LOAD_GLOBAL LOAD_CONST LOAD_CONST LOAD_CONST PRECALL CALL POP_TOP PUSH_EXC_INFO WITH_EXCEPT_START RERAISE COPY POP_EXCEPT RERAISE POP_TOP POP_EXCEPT POP_TOP POP_TOP LOAD_GLOBAL LOAD_CONST RETURN_VALUE LOAD_CONST RETURN_VALUE`
  - ORIG 含两次 `LOAD_CONST×3; PRECALL; CALL; POP_TOP`（with 的 `__exit__` 清理 + break 出口的 `ctx.__exit__`）；RECOMP 缺第二次 `__exit__` 调用（break 出口丢失），多出 `LOAD_CONST RETURN_VALUE`（隐式 return None 替代 break 退出后的 return 1）。
- **疑似根因**：`_identify_with_regions`（region_analyzer.py:8068）+ `_detect_break_continue`（region_analyzer.py:4262）对 **with body 内 break** 的处理。with 的 `__exit__` 清理块 + break 的循环退出在 CFG 中共享 with 的 cleanup handler，break 块被 with 区域吞并为 with body 的一部分，break 作为语句被丢弃，`if b:` body 退化为 `pass`，函数尾 `return 1` 也丢失。R03 #11（with+return→break）是 return 被降级为 break；本例为 **with+break**——break 被完全丢弃（与 return 降级方向相反），with 的 `BEFORE_WITH` + `WITH_EXCEPT_START` 协议与 break 出口的 `__exit__` 调用交互未覆盖。违反原则 2（break 指令被丢弃）。

---

## 错误 12 — for + try/finally + continue（continue 路径复制 cleanup + finally 保留）

- **测试文件**：`tests/exhaustive/loop/round_04/test_r4_for_try_finally_continue_func.py`
- **REGION_TYPE**：FOR_LOOP
- **源码**：
  ```python
  def f():
      for i in r:
          try:
              if i:
                  continue
          finally:
              cleanup()
  ```
- **反编译结果**：
  ```python
  def f():
      for i in r:
          try:
              if i:
                  cleanup()
                  continue
          finally: cleanup()
  ```
- **失败类型**：字节码不匹配（语义错误：`finally: cleanup()` 被复制进 try body 的 `if i:` 真分支（`cleanup(); continue`），与外层 `finally: cleanup()` 共存，continue 路径的 cleanup 调用翻倍）。
- **字节码 diff**（f 函数体嵌套 code object，指令数 24 vs 28）：
  - ORIG (24): `RESUME LOAD_GLOBAL GET_ITER STORE_FAST LOAD_FAST LOAD_GLOBAL PRECALL CALL POP_TOP LOAD_GLOBAL PRECALL CALL POP_TOP PUSH_EXC_INFO LOAD_GLOBAL PRECALL CALL POP_TOP RERAISE COPY POP_EXCEPT RERAISE LOAD_CONST RETURN_VALUE`
  - RECOMP (28): `RESUME LOAD_GLOBAL GET_ITER STORE_FAST LOAD_FAST LOAD_GLOBAL PRECALL CALL POP_TOP LOAD_GLOBAL PRECALL CALL POP_TOP LOAD_GLOBAL PRECALL CALL POP_TOP PUSH_EXC_INFO LOAD_GLOBAL PRECALL CALL POP_TOP RERAISE COPY POP_EXCEPT RERAISE LOAD_CONST RETURN_VALUE`
  - RECOMP 多出一次 `LOAD_GLOBAL cleanup; PRECALL; CALL; POP_TOP`（cleanup 被复制进 try body 的 continue 路径）。
- **疑似根因**：`_identify_try_except_regions`（region_analyzer.py:5303）+ try-finally 归约对 **try body 内 continue** 的处理。finally 块的清理代码（`LOAD_GLOBAL cleanup; CALL`）被复制到 try body 的 continue 路径（`if i: cleanup(); continue`），与外层 `finally: cleanup()` 共存。R03 #1（for+try/finally+break）修复了 break 被吞的场景，R03 #2（while+try/finally+continue）修复了 while 路径的 continue-in-finally；本例为 **for + try/finally + continue（continue 在 try body 而非 finally）**——continue 的回边与 finally 清理块的复制交互未覆盖，cleanup 被复制进 continue 路径。与错误 06（while+try/finally+return）证实 try-finally 对 try body 内所有非顺序控制流（return/continue）均存在 cleanup 复制污染。违反原则 2（finally 块被复制进 try body）。

---

## 汇总

| # | 错误描述 | 测试文件 | 根因分类 |
|---|---------|---------|---------|
| 01 | while+`from m import x` → `('x',)` + `import m as y` | test_r4_while_import_from | IMPORT_FROM 重建缺失（while 路径） |
| 02 | for+`from m import *` 整条语句丢失 | test_r4_for_import_star | IMPORT_STAR 重建缺失 |
| 03 | for+match 或模式 `1|2` → `1 as y|2 as y` 语法错误 | test_r4_for_match_or_pattern | or-pattern 捕获误判 |
| 04 | for+match 序列模式 `[a,*b]` → `[a,*b] as i` + 虚假 continue | test_r4_for_match_sequence | 序列模式捕获误判 |
| 05 | while+嵌套 try/except 内层 handler 错位 → 语法错误 | test_r4_while_nested_try | 嵌套 try handler 边界错位 |
| 06 | while+try/finally+return cleanup 被复制进 try body | test_r4_while_try_finally_return | try-finally + return 复制污染 |
| 07 | while+try/finally+break 在 finally 中 break 脱离 if | test_r4_while_try_finally_break_in_finally | break-in-finally 归属 |
| 08 | while-else+else 内 for 循环 else 被丢弃 | test_r4_while_else_for_in_else | else 内嵌套循环识别 |
| 09 | async while+async with+return → break | test_r4_while_async_with_return | async with+return 误判 break |
| 10 | async while+try/finally+await 插入虚假 continue | test_r4_async_while_try_finally | await 轮询 + try-finally 回边混淆 |
| 11 | while+with+break break 完全丢失 | test_r4_while_with_break | with+break 误判 |
| 12 | for+try/finally+continue cleanup 被复制进 try body | test_r4_for_try_finally_continue_func | try-finally + continue 复制污染 |

**根因聚类**：
- **import 协议重建缺失（循环体内）**（01/02）：`_extract_imports_from_block_prefix`（region_ast_generator.py:141）的 import 检测仅在前驱块前缀扫描触发，循环体块（while 走 `_generate_block_statements` region_ast_generator.py:29711，for 走 `_generate_stmts_from_instrs` region_ast_generator.py:32535）未调用。R03 #10 仅修复 IMPORT_NAME+STORE（`import os`）；IMPORT_FROM（`from m import x`）与 IMPORT_STAR（`from m import *`）协议均未覆盖，证实 import 三形态在循环体内全部缺口。
- **match 复杂模式捕获误判**（03/04）：`_identify_match_regions`（region_analyzer.py:8636）对 or-pattern（多 COMPARE_OP 链）与 sequence pattern（MATCH_SEQUENCE+UNPACK_EX）的捕获归属。case 体 `STORE_NAME` 被误识别为模式捕获 `as`，case 末尾 fall-through 被误识为 `continue`。R03 #3 仅修复字面量模式 subject，复杂模式未覆盖。
- **嵌套 try handler 边界错位**（05）：`_identify_try_except_regions`（region_analyzer.py:5303）对嵌套 try-except 的内外层 handler 归并错位，内层 handler 被外层吞并、外层 handler 外推为 if。
- **try-finally + try body 控制流复制污染**（06/12）：`_identify_try_except_regions`（region_analyzer.py:5303）对 try body 内 return/continue 的处理，finally 清理块被复制进 try body 的控制流分支，cleanup 调用翻倍。R03 #1（break 被吞）/#2（continue-in-finally）未覆盖 try body 内 return/continue 的复制污染。
- **break-in-finally 归属**（07）：`_detect_break_continue`（region_analyzer.py:4262）对 finally 块内 break，break 脱离 if 体为无条件 break。R03 #2（continue-in-finally）未覆盖 break-in-finally。
- **else 内嵌套循环识别**（08）：`_find_loop_else`（region_analyzer.py:3982）while 分支对 else 块内含 LoopRegion 的识别，else 被误判丢弃。R02 #07（else 内简单赋值）未覆盖 else 内嵌套循环。
- **async with + 控制流误判**（09/11）：`_identify_with_regions`（region_analyzer.py:8068）+ `_detect_break_continue`（region_analyzer.py:4262）对 with/async-with body 内 return/break 的处理。R03 #11（sync with+return→break）未覆盖 async with+return 与 sync with+break（break 被丢弃，与 return 降级方向相反）。
- **async + await 轮询 + try-finally 回边混淆**（10）：`_loop_generate_while`（region_ast_generator.py:3532）+ `_is_await_polling_loop`（region_analyzer.py:4744）对 await 在 try/finally 内的回边处理，重检块被吞、虚假 continue 插入。R02 #12（await 退化为 if）未覆盖 await 在 try-finally 内的场景。

共发现 **12 个** 真实 LOOP 反编译错误（均通过 `timeout 280 python -m pytest tests/exhaustive/loop/round_04/ -q` 实测失败确认，`12 failed` / 0 pass / 0 skip / 0 error），覆盖 8 类根因，与 R01 已修复 9 bug + 5 已知限制、R02 已修复 12 bug、R03 已修复 12 bug 模式不重叠。

---

## 回归验证

`timeout 100 python -m pytest tests/exhaustive/loop/round_02/ tests/exhaustive/loop/round_03/ -q` →
`24 passed in 0.34s`

- `tests/exhaustive/loop/round_02/`：12/12 全通过（R02 修复无退化）
- `tests/exhaustive/loop/round_03/`：12/12 全通过（R03 修复无退化）

本 Round 仅新增测试文件与 findings 文档，**未修改任何反编译器源代码**，基线无退化。
