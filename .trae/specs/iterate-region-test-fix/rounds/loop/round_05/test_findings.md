# LOOP 区域 Round 05 测试发现报告

## 基线

- **反编译器**：pythoncdc（`core/cfg/region_analyzer.py` + `core/cfg/region_ast_generator.py` + `core/cfg/pattern_parser.py` + `core/cfg/code_generator.py`）
- **运行环境**：Python 3.11.15
- **测试框架**：`tests/exhaustive/base.py::ExhaustiveTestCase.verify_decompilation()`
  （编译 → 反编译 → `ast.parse` 语法检查 → 重编译 → `_compare_code_objects` 字节码等价比较）
- **Round 01–04 状态**：已修复 9+12+12+12 = 45 个 bug；5 个 R01 已知限制未修。
- **本 Round 范围**：仅覆盖与 R01–R04 已修复/已知模式不同的新模式；不修改反编译器源代码。
- **验证命令**：`timeout 280 python -m pytest tests/exhaustive/loop/round_05/ -q`
- **结果**：`13 failed`（全部为真实反编译错误，0 skip / 0 pass / 0 error）。

测试目录：`/workspace/tests/exhaustive/loop/round_05/`

字节码 diff 说明：过滤跳转/对齐指令（JUMP_FORWARD/JUMP_BACKWARD/JUMP_ABSOLUTE/POP_JUMP_*/FOR_ITER/SEND/NOP/CACHE）后比较操作码序列。`ORIG` 为源码编译结果，`RECOMP` 为反编译结果重编译结果。函数级用例比较 f 协程体的嵌套 code object。

---

## 错误 01 — for + match guard（`case _ if x > 0:` → `if (x > 0): y=1; continue`，match 退化为 if，subject `x` 被丢弃）

- **测试文件**：`tests/exhaustive/loop/round_05/test_r5_for_match_guard.py`
- **REGION_TYPE**：FOR_LOOP
- **源码**：
  ```python
  for i in r:
      match x:
          case _ if x > 0:
              y = 1
          case _:
              y = 2
  ```
- **反编译结果**：
  ```python
  for i in r:
      if (x > 0):
          y = 1
          continue
      y = 2
  ```
- **失败类型**：字节码不匹配（语义错误：`match x:` 退化为 `if (x > 0):`，subject `x` 的 `LOAD_NAME x; POP_TOP` 被丢弃；case `_:` 退化为 fall-through；case body 末尾插入虚假 `continue`）。
- **字节码 diff**（模块级，指令数 15 vs 13）：
  - ORIG (15): `RESUME LOAD_NAME GET_ITER STORE_NAME LOAD_NAME POP_TOP LOAD_NAME LOAD_CONST COMPARE_OP LOAD_CONST STORE_NAME LOAD_CONST STORE_NAME LOAD_CONST RETURN_VALUE`
  - RECOMP (13): `RESUME LOAD_NAME GET_ITER STORE_NAME LOAD_NAME LOAD_CONST COMPARE_OP LOAD_CONST STORE_NAME LOAD_CONST STORE_NAME LOAD_CONST RETURN_VALUE`
  - ORIG 含 `LOAD_NAME x; POP_TOP`（match subject 通配符 `_` 丢弃 subject），RECOMP 缺该对指令。
- **疑似根因**：`_identify_match_regions`（region_analyzer.py）对**带 guard 的通配符模式 `case _ if <guard>:`** 的识别。guard `x > 0` 的字节码 `LOAD_NAME x; LOAD_CONST 0; COMPARE_OP` 与 case body 赋值 `LOAD_CONST 1; STORE_NAME y` 之间，subject 的 `LOAD_NAME x; POP_TOP` 被误判为非 match 指令而丢弃，match 区域整体退化为 IfRegion（`if (x > 0)`），case body 末尾 fall-through 到回边被误识为 `continue`。R04 #03/#04 修复了 or-pattern 与 sequence pattern的捕获误判，但**guard（`case _ if cond:`）使 match 退化为 if**未覆盖。违反原则 2（subject 指令被丢弃）。

---

## 错误 02 — while + break in ternary condition（`if (x if cond else y): break` → `if (x if cond else y): pass`，break 丢失）

- **测试文件**：`tests/exhaustive/loop/round_05/test_r5_while_break_ternary.py`
- **REGION_TYPE**：WHILE_LOOP
- **源码**：
  ```python
  def f():
      while a:
          if (x if cond else y):
              break
  ```
- **反编译结果**：
  ```python
  def f():
      while a:
          if (x if cond else y):
              pass
  ```
- **失败类型**：字节码不匹配（语义错误：`if (ternary): break` 中的 break 完全丢失，if 体退化为 `pass`——循环变为无限循环）。
- **字节码 diff**（f 函数体嵌套 code object，指令数 12 vs 10）：
  - ORIG (12): `RESUME LOAD_GLOBAL LOAD_GLOBAL LOAD_GLOBAL LOAD_GLOBAL LOAD_CONST RETURN_VALUE LOAD_GLOBAL LOAD_CONST RETURN_VALUE LOAD_CONST RETURN_VALUE`
  - RECOMP (10): `RESUME LOAD_GLOBAL LOAD_GLOBAL LOAD_GLOBAL LOAD_GLOBAL LOAD_GLOBAL LOAD_CONST RETURN_VALUE LOAD_CONST RETURN_VALUE`
  - ORIG 含 `LOAD_CONST None; RETURN_VALUE`（break 出口的隐式 return None）+ 末尾 `LOAD_CONST None; RETURN_VALUE`，RECOMP 缺 break 出口（仅 10 条），ternary 条件 `cond? x: y` 后直接 LOAD_GLOBAL a 重检，break 退出语义丢失。
- **疑似根因**：`_detect_break_continue`（region_analyzer.py）对 **if 条件为 ternary（`IfExp`）时的 break 归属**。ternary 条件 `x if cond else y` 的字节码为 `LOAD_GLOBAL cond; POP_JUMP_IF_FALSE L1; LOAD_GLOBAL x; JUMP L2; L1: LOAD_GLOBAL y; L2: POP_JUMP_IF_FALSE Lbreak`，break 块 `LOAD_CONST None; RETURN_VALUE` 在 Lbreak 目标。ternary 的内部分支跳转（`POP_JUMP_IF_FALSE` 到 L1）与 break 的条件跳转（L2 处 POP_JUMP_IF_FALSE 到 Lbreak）混淆，break 块未被识别为 BREAK 角色，break 作为语句被丢弃，if 体退化为 `pass`。R01 #5（while ternary cond）是 ternary 作为 while **条件**的已知限制；本例为 ternary 作为 if **体条件**——break 在 ternary 条件分支后被丢弃，方向不同。违反原则 2（break 指令被丢弃）。

---

## 错误 03 — for + try/except + break in except（`except E: if i: break` → `except E: pass`，break 丢失）

- **测试文件**：`tests/exhaustive/loop/round_05/test_r5_for_try_except_break_in_except.py`
- **REGION_TYPE**：FOR_LOOP
- **源码**：
  ```python
  def f():
      for i in r:
          try:
              do()
          except E:
              if i:
                  break
  ```
- **反编译结果**：
  ```python
  def f():
      for i in r:
          try:
              do()
          except E: pass
  ```
- **失败类型**：字节码不匹配（语义错误：except handler `if i: break` 的 break 完全丢失，handler 退化为 `pass`）。
- **字节码 diff**（f 函数体嵌套 code object，指令数 24 vs 19）：
  - ORIG (24): `RESUME LOAD_GLOBAL GET_ITER STORE_FAST LOAD_GLOBAL PRECALL CALL POP_TOP PUSH_EXC_INFO LOAD_GLOBAL CHECK_EXC_MATCH POP_TOP LOAD_FAST i POP_EXCEPT POP_TOP LOAD_CONST RETURN_VALUE POP_EXCEPT RERAISE COPY POP_EXCEPT RERAISE LOAD_CONST RETURN_VALUE`
  - RECOMP (19): `RESUME LOAD_GLOBAL GET_ITER STORE_FAST LOAD_GLOBAL PRECALL CALL POP_TOP PUSH_EXC_INFO LOAD_GLOBAL CHECK_EXC_MATCH POP_TOP POP_EXCEPT RERAISE COPY POP_EXCEPT RERAISE LOAD_CONST RETURN_VALUE`
  - ORIG 含 `LOAD_FAST i; POP_EXCEPT; POP_TOP; LOAD_CONST None; RETURN_VALUE`（break 在 except handler 内的退出路径，POP_EXCEPT 清理 + break 出口），RECOMP 缺该 5 条，handler 退化为 `pass`。
- **疑似根因**：`_detect_break_continue`（region_analyzer.py）+ `_identify_try_except_regions`（region_analyzer.py）对 **except handler 内 break** 的归属。except handler 的 `if i: break` 中 break 块带 except 清理（`POP_EXCEPT`），break 块未被识别为 BREAK 角色，break 被丢弃，handler 退化为 `pass`。R03/R04 修复了 try body 内 break/continue（finally 复制污染），但 **except handler 内 break** 未覆盖。违反原则 2（break 指令被丢弃）。

---

## 错误 04 — for + try/except + continue in except（`except E: if i: continue; x = i` → `except E: pass; x = i`，continue 丢失）

- **测试文件**：`tests/exhaustive/loop/round_05/test_r5_for_continue_in_except.py`
- **REGION_TYPE**：FOR_LOOP
- **源码**：
  ```python
  def f():
      for i in r:
          try:
              do()
          except E:
              if i:
                  continue
          x = i
  ```
- **反编译结果**：
  ```python
  def f():
      for i in r:
          try:
              do()
          except E: pass
          x = i
  ```
- **失败类型**：字节码不匹配（语义错误：except handler `if i: continue` 的 continue 完全丢失，handler 退化为 `pass`，`x = i` 不再被 continue 跳过）。
- **字节码 diff**（f 函数体嵌套 code object，指令数 23 vs 21）：
  - ORIG (23): `RESUME LOAD_GLOBAL GET_ITER STORE_FAST LOAD_GLOBAL PRECALL CALL POP_TOP PUSH_EXC_INFO LOAD_GLOBAL CHECK_EXC_MATCH POP_TOP LOAD_FAST i POP_EXCEPT POP_EXCEPT RERAISE COPY POP_EXCEPT RERAISE LOAD_FAST i STORE_FAST LOAD_CONST RETURN_VALUE`
  - RECOMP (21): `RESUME LOAD_GLOBAL GET_ITER STORE_FAST LOAD_GLOBAL PRECALL CALL POP_TOP PUSH_EXC_INFO LOAD_GLOBAL CHECK_EXC_MATCH POP_TOP POP_EXCEPT RERAISE COPY POP_EXCEPT RERAISE LOAD_FAST i STORE_FAST LOAD_CONST RETURN_VALUE`
  - ORIG 含 `LOAD_FAST i; POP_EXCEPT; POP_EXCEPT; RERAISE`（continue 在 except handler 内的回边路径，POP_EXCEPT 清理 + RERAISE 回到循环头），RECOMP 缺该 4 条，handler 退化为 `pass`。
- **疑似根因**：同错误 03，`_detect_break_continue` + `_identify_try_except_regions` 对 **except handler 内 continue** 的归属。continue 块带 except 清理（`POP_EXCEPT`），未被识别为 CONTINUE 角色，continue 被丢弃。与错误 03 证实 except handler 内 break/continue 均存在归属缺口。违反原则 2（continue 指令被丢弃）。

---

## 错误 05 — for + nested try in except（内层 try 被提升到 try body，handler 错位）

- **测试文件**：`tests/exhaustive/loop/round_05/test_r5_for_nested_try_in_except.py`
- **REGION_TYPE**：FOR_LOOP
- **源码**：
  ```python
  for i in r:
      try:
          do()
      except E:
          try:
              x = 1
          except E2:
              y = 2
  ```
- **反编译结果**：
  ```python
  for i in r:
      try:
          try:
              x = 1
          except E2: y = 2
          do()
      except E: x = 1
  ```
- **失败类型**：字节码不匹配（语义错误：内层 try（在 except E handler 内）被提升到外层 try body 之前，`do()` 被挤到内层 try 之后；外层 `except E: x = 1` 的 handler body 被改为 `x = 1`（与内层 try body 重名混淆））。
- **字节码 diff**（模块级，指令数 33 vs 35）：
  - ORIG (33): `RESUME LOAD_NAME GET_ITER STORE_NAME PUSH_NULL LOAD_NAME PRECALL CALL POP_TOP PUSH_EXC_INFO LOAD_NAME CHECK_EXC_MATCH POP_TOP LOAD_CONST STORE_NAME PUSH_EXC_INFO LOAD_NAME CHECK_EXC_MATCH POP_TOP LOAD_CONST STORE_NAME POP_EXCEPT RERAISE COPY POP_EXCEPT RERAISE POP_EXCEPT RERAISE COPY POP_EXCEPT RERAISE LOAD_CONST RETURN_VALUE`
  - RECOMP (35): `RESUME LOAD_NAME GET_ITER STORE_NAME LOAD_CONST STORE_NAME PUSH_EXC_INFO LOAD_NAME CHECK_EXC_MATCH POP_TOP LOAD_CONST STORE_NAME POP_EXCEPT RERAISE COPY POP_EXCEPT RERAISE PUSH_NULL LOAD_NAME PRECALL CALL POP_TOP PUSH_EXC_INFO LOAD_NAME CHECK_EXC_MATCH POP_TOP LOAD_CONST STORE_NAME POP_EXCEPT RERAISE COPY POP_EXCEPT RERAISE LOAD_CONST RETURN_VALUE`
  - ORIG 顺序：`do()` → `except E` handler → 内层 try (`x=1; except E2: y=2`)；RECOMP 顺序：内层 try (`x=1; except E2: y=2`) → `do()` → `except E: x=1`，内层 try 被提升、`do()` 后移、外层 handler body 变 `x=1`。
- **疑似根因**：`_identify_try_except_regions`（region_analyzer.py）对 **except handler 内嵌套 try** 的归约。内层 try（在 except E handler 内）被识别为独立 TryRegion 后，归约顺序错位——内层 try 被提升为外层 try body 的首语句，`do()` 被挤到内层 try 之后，外层 handler 的 body（本应含内层 try）被压缩为 `x = 1`。R04 #05 修复了 try body 内嵌套 try（try-in-try-body）的 handler 边界错位，但 **except handler 内嵌套 try**（try-in-except-handler）的边界错位未覆盖。违反原则 2（内层 try 块归属错位）+ 原则 3（嵌套 try 应作抽象节点）。

---

## 错误 06 — while-else + match in else（else 内 match case body 丢失，case `_:` 丢失）

- **测试文件**：`tests/exhaustive/loop/round_05/test_r5_while_match_in_else.py`
- **REGION_TYPE**：WHILE_LOOP
- **源码**：
  ```python
  def f():
      while a:
          if b:
              break
      else:
          match x:
              case 1:
                  y = 1
              case _:
                  y = 2
  ```
- **反编译结果**：
  ```python
  def f():
      while a:
          if b:
              break
      else:
          match x:
              case 1:
                  pass
  ```
- **失败类型**：字节码不匹配（语义错误：while-else 的 else 块内 match 的 `case 1: y = 1` body 退化为 `pass`，`case _:` 整个 case 丢失）。
- **字节码 diff**（f 函数体嵌套 code object，指令数 17 vs 13）：
  - ORIG (17): `RESUME LOAD_GLOBAL LOAD_GLOBAL LOAD_CONST RETURN_VALUE LOAD_GLOBAL LOAD_GLOBAL LOAD_CONST COMPARE_OP LOAD_CONST STORE_FAST LOAD_CONST RETURN_VALUE LOAD_CONST STORE_FAST LOAD_CONST RETURN_VALUE`
  - RECOMP (13): `RESUME LOAD_GLOBAL LOAD_GLOBAL LOAD_CONST RETURN_VALUE LOAD_GLOBAL LOAD_GLOBAL LOAD_CONST COMPARE_OP LOAD_CONST RETURN_VALUE LOAD_CONST RETURN_VALUE`
  - ORIG 含 `LOAD_CONST 1; STORE_FAST y`（case 1 body）+ `LOAD_CONST 2; STORE_FAST y`（case _ body）；RECOMP 缺这两对，case 1 body 退化为 `pass`，case _ 整个丢失。
- **疑似根因**：`_find_loop_else`（region_analyzer.py）+ `_identify_match_regions` 对 **else 块内 match** 的归约。while-else 的 else 块内 match 的 case body 赋值（`LOAD_CONST 1; STORE_FAST y`）与 case header 的 `LOAD_CONST 1; COMPARE_OP`（值模式匹配）混淆，case body STORE 被丢弃，case `_:` 的 fall-through 被丢弃。R04 #08 修复了 else 内嵌套循环识别，R04 #03/#04 修复了循环体内 match 模式，但 **else 块内 match**（match 在 while-else 的 else）未覆盖。违反原则 2（case body 指令被丢弃）。

---

## 错误 07 — for + match or-pattern + guard（`case 1 | 2 if i > 0:` → 拆为两个 case，guard 重复，body 丢失）

- **测试文件**：`tests/exhaustive/loop/round_05/test_r5_for_match_or_guard.py`
- **REGION_TYPE**：FOR_LOOP
- **源码**：
  ```python
  for i in r:
      match x:
          case 1 | 2 if i > 0:
              y = 1
          case _:
              y = 0
  ```
- **反编译结果**：
  ```python
  for i in r:
      match x:
          case 1 if (i > 0):
              pass
          case 2 if (i > 0):
              pass
          case _:
              y = 0
  ```
- **失败类型**：字节码不匹配（语义错误：or-pattern `1 | 2` 被拆为两个独立 case `case 1 if (i > 0)` 与 `case 2 if (i > 0)`，guard 重复；case body `y = 1` 完全丢失，两个拆分 case body 退化为 `pass`）。
- **字节码 diff**（模块级，指令数 22 vs 21）：
  - ORIG (22): `RESUME LOAD_NAME GET_ITER STORE_NAME LOAD_NAME COPY LOAD_CONST COMPARE_OP COPY LOAD_CONST COMPARE_OP POP_TOP POP_TOP LOAD_NAME LOAD_CONST COMPARE_OP LOAD_CONST STORE_NAME LOAD_CONST STORE_NAME LOAD_CONST RETURN_VALUE`
  - RECOMP (21): `RESUME LOAD_NAME GET_ITER STORE_NAME LOAD_NAME COPY LOAD_CONST COMPARE_OP LOAD_NAME LOAD_CONST COMPARE_OP POP_TOP LOAD_CONST COMPARE_OP LOAD_NAME LOAD_CONST COMPARE_OP LOAD_CONST STORE_NAME LOAD_CONST RETURN_VALUE`
  - ORIG 含 `COPY; LOAD_CONST 2; COMPARE_OP; POP_TOP; POP_TOP`（or-pattern 第二分支 + 合并），RECOMP 把 or-pattern 拆为两 case，缺 `POP_TOP`，case body `LOAD_CONST 1; STORE_NAME y` 丢失。
- **疑似根因**：`_identify_match_regions`（region_analyzer.py）对 **or-pattern + guard**（`case 1 | 2 if guard:`）的归约。or-pattern `1 | 2` 的字节码 `COPY; LOAD_CONST 1; COMPARE_OP; COPY; LOAD_CONST 2; COMPARE_OP; POP_TOP; POP_TOP`（两值模式短路或 + 合并）后接 guard `LOAD_NAME i; COMPARE_OP`。guard 的存在使 or-pattern 的合并 `POP_TOP; POP_TOP` 被拆，or 被误拆为两个独立 case，guard 重复附加到每个拆分 case，原 case body `y = 1` 被丢弃。R04 #03 修复了 or-pattern（无 guard）的捕获误判，但 **or-pattern + guard** 未覆盖。违反原则 2（or-pattern 被拆、body 丢失）。

---

## 错误 08 — while + try/finally + raise in finally（while 退化为 if，finally 拆为 except+else，raise 重复）

- **测试文件**：`tests/exhaustive/loop/round_05/test_r5_while_raise_finally.py`
- **REGION_TYPE**：WHILE_LOOP
- **源码**：
  ```python
  while a:
      try:
          do()
      finally:
          raise E()
  ```
- **反编译结果**：
  ```python
  if a:
      try:
          do()
      except: raise E()
      else: raise E()
  ```
- **失败类型**：字节码不匹配（语义错误：while 循环退化为 `if a:`，finally 块 `raise E()` 被拆为 `except: raise E()` + `else: raise E()`，raise 被重复两次）。
- **字节码 diff**（模块级，指令数 23 vs 24）：
  - ORIG (23): `RESUME LOAD_NAME PUSH_NULL LOAD_NAME PRECALL CALL POP_TOP PUSH_NULL LOAD_NAME PRECALL CALL RAISE_VARARGS PUSH_EXC_INFO PUSH_NULL LOAD_NAME PRECALL CALL RAISE_VARARGS COPY POP_EXCEPT RERAISE LOAD_CONST RETURN_VALUE`
  - RECOMP (24): `RESUME LOAD_NAME PUSH_NULL LOAD_NAME PRECALL CALL POP_TOP PUSH_NULL LOAD_NAME PRECALL CALL RAISE_VARARGS PUSH_EXC_INFO POP_TOP PUSH_NULL LOAD_NAME PRECALL CALL RAISE_VARARGS COPY POP_EXCEPT RERAISE LOAD_CONST RETURN_VALUE`
  - RECOMP 多出 `POP_TOP`（PUSH_EXC_INFO 后的虚假 POP_TOP，finally cleanup 被拆为 except handler），while 退化为 if（无回边重检块）。
- **疑似根因**：`_loop_generate_while`（region_ast_generator.py）+ try-finally 归约对 **finally 块内 raise** 的处理。finally 块 `raise E()` 的字节码 `PUSH_NULL; LOAD_NAME E; PRECALL; CALL; RAISE_VARARGS` 既是正常路径出口又是异常路径出口（raise 必触发异常），finally 归约把 raise 误判为 except handler 的 body（`except: raise E()`）+ else body（`else: raise E()`），raise 被重复；同时 finally 内 raise 使循环正常退出路径不可达，while 回边重检块被吞，while 退化为 if。R04 #06/#12 修复了 try body 内 return/continue 的 finally 复制污染，但 **finally 块内 raise**（raise 使正常路径不可达）未覆盖。违反原则 2（raise 被复制）+ 原则 3（try-finally 应作抽象节点）。

---

## 错误 09 — while + try/except + continue in except（`except E: if b: continue; x = 1` → `except E: pass; x = 1`，continue 丢失）

- **测试文件**：`tests/exhaustive/loop/round_05/test_r5_while_continue_in_except.py`
- **REGION_TYPE**：WHILE_LOOP
- **源码**：
  ```python
  def f():
      while a:
          try:
              do()
          except E:
              if b:
                  continue
          x = 1
  ```
- **反编译结果**：
  ```python
  def f():
      while a:
          try:
              do()
          except E: pass
          x = 1
  ```
- **失败类型**：字节码不匹配（语义错误：except handler `if b: continue` 的 continue 完全丢失，handler 退化为 `pass`，`x = 1` 不再被 continue 跳过）。
- **字节码 diff**（f 函数体嵌套 code object，指令数 24 vs 22）：
  - ORIG (24): `RESUME LOAD_GLOBAL LOAD_GLOBAL PRECALL CALL POP_TOP PUSH_EXC_INFO LOAD_GLOBAL CHECK_EXC_MATCH POP_TOP LOAD_GLOBAL POP_EXCEPT POP_EXCEPT RERAISE COPY POP_EXCEPT RERAISE LOAD_CONST STORE_FAST LOAD_GLOBAL LOAD_CONST RETURN_VALUE LOAD_CONST RETURN_VALUE`
  - RECOMP (22): `RESUME LOAD_GLOBAL LOAD_GLOBAL PRECALL CALL POP_TOP PUSH_EXC_INFO LOAD_GLOBAL CHECK_EXC_MATCH POP_TOP POP_EXCEPT RERAISE COPY POP_EXCEPT RERAISE LOAD_CONST STORE_FAST LOAD_GLOBAL LOAD_CONST RETURN_VALUE LOAD_CONST RETURN_VALUE`
  - ORIG 含 `LOAD_GLOBAL b; POP_EXCEPT; POP_EXCEPT; RERAISE`（continue 在 except handler 内的回边路径），RECOMP 缺该 4 条，handler 退化为 `pass`。
- **疑似根因**：同错误 04，`_detect_break_continue` + `_identify_try_except_regions` 对 **except handler 内 continue（while 版）** 的归属。与错误 04（for 版）同根因——except handler 内 continue 块带 `POP_EXCEPT` 清理，未被识别为 CONTINUE 角色。违反原则 2（continue 指令被丢弃）。

---

## 错误 10 — while + try/except/finally + break in except（cleanup 被复制进 except break 路径）

- **测试文件**：`tests/exhaustive/loop/round_05/test_r5_while_try_finally_break_except.py`
- **REGION_TYPE**：WHILE_LOOP
- **源码**：
  ```python
  def f():
      while a:
          try:
              do()
          except E:
              if b:
                  break
          finally:
              cleanup()
  ```
- **反编译结果**：
  ```python
  def f():
      while a:
          try:
              do()
          except E:
              cleanup()
              break
          finally: cleanup()
  ```
- **失败类型**：字节码不匹配（语义错误：finally 块 `cleanup()` 被复制进 except handler 的 break 路径（`except E: cleanup(); break`），与外层 `finally: cleanup()` 共存，cleanup 调用翻倍）。
- **字节码 diff**（f 函数体嵌套 code object，指令数 41 vs 43）：
  - ORIG (41): `RESUME LOAD_GLOBAL LOAD_GLOBAL PRECALL CALL POP_TOP PUSH_EXC_INFO LOAD_GLOBAL CHECK_EXC_MATCH POP_TOP LOAD_GLOBAL b POP_EXCEPT LOAD_GLOBAL PRECALL CALL POP_TOP LOAD_CONST RETURN_VALUE POP_EXCEPT RERAISE COPY POP_EXCEPT RERAISE LOAD_GLOBAL PRECALL CALL POP_TOP PUSH_EXC_INFO LOAD_GLOBAL PRECALL CALL POP_TOP RERAISE COPY POP_EXCEPT RERAISE LOAD_GLOBAL LOAD_CONST RETURN_VALUE LOAD_CONST RETURN_VALUE`
  - RECOMP (43): 多出一次 `LOAD_GLOBAL cleanup; PRECALL; CALL; POP_TOP`（cleanup 被复制进 except handler 的 break 路径）。
- **疑似根因**：`_identify_try_except_regions`（region_analyzer.py）+ try-finally 归约对 **except handler 内 break** 的处理。finally 块的清理代码（`LOAD_GLOBAL cleanup; CALL`）被复制到 except handler 的 break 路径（`except E: cleanup(); break`），与外层 `finally: cleanup()` 共存。R04 #06/#12 修复了 try body 内 return/continue 的 finally 复制污染，R04 #03/#04 修复了 except handler 内 break/continue 丢失，但 **except handler 内 break + finally**（finally 复制进 except break 路径）未覆盖。违反原则 2（finally 块被复制进 except handler）。

---

## 错误 11 — for + match class pattern no args（`case P():` → `case P() as y:` + 虚假 continue，y 为 case body 赋值）

- **测试文件**：`tests/exhaustive/loop/round_05/test_r5_for_match_class_no_args.py`
- **REGION_TYPE**：FOR_LOOP
- **源码**：
  ```python
  for i in r:
      match x:
          case P():
              y = 1
          case _:
              y = 0
  ```
- **反编译结果**：
  ```python
  for i in r:
      match x:
          case P() as y:
              y = 1
              continue
          case _:
              y = 0
  ```
- **失败类型**：字节码不匹配（语义错误：class pattern `P()` 错误附加 `as y` 绑定（`y` 为 case body 赋值），case body 末尾插入虚假 `continue`）。
- **字节码 diff**（模块级，指令数 18 vs 21）：
  - ORIG (18): `RESUME LOAD_NAME GET_ITER STORE_NAME LOAD_NAME LOAD_NAME LOAD_CONST MATCH_CLASS COPY POP_JUMP_FORWARD_IF_NONE UNPACK_SEQUENCE LOAD_CONST STORE_NAME POP_TOP LOAD_CONST STORE_NAME LOAD_CONST RETURN_VALUE`
  - RECOMP (21): `RESUME LOAD_NAME GET_ITER STORE_NAME LOAD_NAME COPY LOAD_NAME LOAD_CONST MATCH_CLASS COPY POP_JUMP_FORWARD_IF_NONE UNPACK_SEQUENCE STORE_NAME LOAD_CONST STORE_NAME POP_TOP POP_TOP LOAD_CONST STORE_NAME LOAD_CONST RETURN_VALUE`
  - RECOMP 多出 `COPY`（虚假 `as y` 绑定）、一条 `STORE_NAME`（as 绑定）、一条 `POP_TOP`（虚假 continue）。
- **疑似根因**：`_identify_match_regions`（region_analyzer.py）+ `_find_store_in_successors`（pattern_parser.py）对 **class pattern 无参数（`P()`）** 的捕获归属。class pattern `P()` 的字节码 `LOAD_NAME P; LOAD_CONST (); MATCH_CLASS 0; COPY; POP_JUMP_IF_NONE; UNPACK_SEQUENCE 0`（MATCH_CLASS 参数 0 = 无位置参数），case body `y = 1` 的 `STORE_NAME y` 被误识别为 as 绑定（`P() as y`），case 末尾 fall-through 被误识为 `continue`。R04 #04 修复了 sequence pattern 的 as 误判（`seen_pattern_instr` 守卫），但 **class pattern 无参数**（MATCH_CLASS 参数 0，无 UNPACK_SEQUENCE 之后的 STORE 捕获）的归属未覆盖。违反原则 2（case body STORE 被误为 as 绑定）。

---

## 错误 12 — while + try/except/else + continue in except（`except E: if b: continue else: x = 1` → `except E: pass else: x = 1`，continue 丢失）

- **测试文件**：`tests/exhaustive/loop/round_05/test_r5_while_try_except_else_continue.py`
- **REGION_TYPE**：WHILE_LOOP
- **源码**：
  ```python
  def f():
      while a:
          try:
              do()
          except E:
              if b:
                  continue
          else:
              x = 1
  ```
- **反编译结果**：
  ```python
  def f():
      while a:
          try:
              do()
          except E: pass
          else: x = 1
  ```
- **失败类型**：字节码不匹配（语义错误：except handler `if b: continue` 的 continue 完全丢失，handler 退化为 `pass`，else 的 `x = 1` 不再被 continue 跳过）。
- **字节码 diff**（f 函数体嵌套 code object，指令数 24 vs 22）：
  - ORIG (24): `RESUME LOAD_GLOBAL LOAD_GLOBAL PRECALL CALL POP_TOP LOAD_CONST STORE_FAST PUSH_EXC_INFO LOAD_GLOBAL CHECK_EXC_MATCH POP_TOP LOAD_GLOBAL POP_EXCEPT POP_EXCEPT RERAISE COPY POP_EXCEPT RERAISE LOAD_GLOBAL LOAD_CONST RETURN_VALUE LOAD_CONST RETURN_VALUE`
  - RECOMP (22): `RESUME LOAD_GLOBAL LOAD_GLOBAL PRECALL CALL POP_TOP LOAD_CONST STORE_FAST PUSH_EXC_INFO LOAD_GLOBAL CHECK_EXC_MATCH POP_TOP POP_EXCEPT RERAISE COPY POP_EXCEPT RERAISE LOAD_GLOBAL LOAD_CONST RETURN_VALUE LOAD_CONST RETURN_VALUE`
  - ORIG 含 `LOAD_GLOBAL b; POP_EXCEPT; POP_EXCEPT; RERAISE`（continue 在 except handler 内的回边路径），RECOMP 缺该 4 条，handler 退化为 `pass`。
- **疑似根因**：同错误 09，`_detect_break_continue` + `_identify_try_except_regions` 对 **except handler 内 continue（含 else 子句）** 的归属。与错误 09（无 else）同根因——except handler 内 continue 块带 `POP_EXCEPT` 清理，未被识别为 CONTINUE 角色。证实 except handler 内 break/continue 在有/无 else 子句时均存在归属缺口。违反原则 2（continue 指令被丢弃）。

---

## 错误 13 — while + match guard（`case _ if x > 0:` → `if (x > 0): y=1 else: y=2`，match 退化为 if，subject 丢弃）

- **测试文件**：`tests/exhaustive/loop/round_05/test_r5_while_match_guard.py`
- **REGION_TYPE**：WHILE_LOOP
- **源码**：
  ```python
  while a:
      match x:
          case _ if x > 0:
              y = 1
          case _:
              y = 2
  ```
- **反编译结果**：
  ```python
  while a:
      if (x > 0):
          y = 1
      else:
          y = 2
  ```
- **失败类型**：字节码不匹配（语义错误：`match x:` 退化为 `if (x > 0):`，subject `x` 的 `LOAD_NAME x; POP_TOP` 被丢弃；`case _:` 退化为 `else:`）。
- **字节码 diff**（模块级，指令数 16 vs 14）：
  - ORIG (16): `RESUME LOAD_NAME LOAD_NAME POP_TOP LOAD_NAME LOAD_CONST COMPARE_OP LOAD_CONST STORE_NAME LOAD_CONST STORE_NAME LOAD_NAME LOAD_CONST RETURN_VALUE LOAD_CONST RETURN_VALUE`
  - RECOMP (14): `RESUME LOAD_NAME LOAD_NAME LOAD_CONST COMPARE_OP LOAD_CONST STORE_NAME LOAD_CONST STORE_NAME LOAD_NAME LOAD_CONST RETURN_VALUE LOAD_CONST RETURN_VALUE`
  - ORIG 含 `LOAD_NAME x; POP_TOP`（match subject 通配符 `_` 丢弃 subject），RECOMP 缺该对指令。
- **疑似根因**：同错误 01，`_identify_match_regions`（region_analyzer.py）对 **带 guard 的通配符模式 `case _ if <guard>:`（while 版）** 的识别。与错误 01（for 版）同根因——guard 使 match 退化为 IfRegion，subject 的 `LOAD_NAME x; POP_TOP` 被丢弃。证实带 guard 的通配符模式在 for/while 循环体内均存在 match 退化。违反原则 2（subject 指令被丢弃）。

---

## 汇总

| # | 错误描述 | 测试文件 | 根因分类 |
|---|---------|---------|---------|
| 01 | for+match guard `case _ if x>0` → if，subject 丢弃 | test_r5_for_match_guard | match guard 退化 if |
| 02 | while+break in ternary cond → break 丢失 | test_r5_while_break_ternary | ternary 条件 + break 归属 |
| 03 | for+try/except+break in except → break 丢失 | test_r5_for_try_except_break_in_except | except handler 内 break 丢失 |
| 04 | for+try/except+continue in except → continue 丢失 | test_r5_for_continue_in_except | except handler 内 continue 丢失 |
| 05 | for+nested try in except → 内层 try 提升、handler 错位 | test_r5_for_nested_try_in_except | except handler 内嵌套 try 边界错位 |
| 06 | while-else+match in else → case body 丢失、case _ 丢失 | test_r5_while_match_in_else | else 内 match case body 丢失 |
| 07 | for+match or-pattern+guard → or 拆分、guard 重复、body 丢失 | test_r5_for_match_or_guard | or-pattern + guard 拆分 |
| 08 | while+try/finally+raise in finally → while 退化 if、raise 重复 | test_r5_while_raise_finally | finally 内 raise 使正常路径不可达 |
| 09 | while+try/except+continue in except → continue 丢失 | test_r5_while_continue_in_except | except handler 内 continue 丢失（while） |
| 10 | while+try/except/finally+break in except → cleanup 复制进 except | test_r5_while_try_finally_break_except | except 内 break + finally 复制污染 |
| 11 | for+match class pattern `P()` → `P() as y` + 虚假 continue | test_r5_for_match_class_no_args | class pattern 无参数 as 误判 |
| 12 | while+try/except/else+continue in except → continue 丢失 | test_r5_while_try_except_else_continue | except handler 内 continue 丢失（含 else） |
| 13 | while+match guard → if，subject 丢弃 | test_r5_while_match_guard | match guard 退化 if（while） |

**根因聚类**：
- **match guard 退化为 if（subject 丢弃）**（01/07/13）：`_identify_match_regions`（region_analyzer.py）对带 guard 的模式（`case _ if cond:` / `case 1|2 if cond:`）的识别，guard 的存在使 match 整体退化为 IfRegion，subject 的 `LOAD; POP_TOP` 被丢弃。R04 #03/#04 修复了 or-pattern / sequence pattern 的捕获误判，但 guard 使 match 退化未覆盖。
- **except handler 内 break/continue 丢失**（03/04/09/12）：`_detect_break_continue`（region_analyzer.py）+ `_identify_try_except_regions` 对 except handler 内 break/continue 的归属。except handler 内 break/continue 块带 `POP_EXCEPT` 清理，未被识别为 BREAK/CONTINUE 角色，break/continue 被丢弃，handler 退化为 `pass`。R03/R04 修复了 try body 内 break/continue，但 except handler 内未覆盖。
- **except handler 内嵌套 try 边界错位**（05）：`_identify_try_except_regions` 对 except handler 内嵌套 try 的归约，内层 try 被提升、`do()` 后移、外层 handler body 错位。R04 #05 修复了 try body 内嵌套 try，但 except handler 内嵌套 try 未覆盖。
- **else 内 match case body 丢失**（06）：`_find_loop_else` + `_identify_match_regions` 对 while-else 的 else 块内 match 的归约，case body 赋值与 case header 值模式匹配混淆，case body STORE 被丢弃、case `_:` 丢失。R04 #08 修复了 else 内嵌套循环，但 else 内 match 未覆盖。
- **finally 块内 raise 使正常路径不可达**（08）：`_loop_generate_while` + try-finally 归约对 finally 内 raise 的处理，finally raise 既是正常出口又是异常出口，finally 被拆为 except+else、raise 重复，while 退化为 if。R04 #06/#12 修复了 try body 内 return/continue 的 finally 复制，但 finally 内 raise 未覆盖。
- **except handler 内 break + finally 复制污染**（10）：try-finally 归约对 except handler 内 break 的处理，finally cleanup 被复制进 except 的 break 路径。R04 #06/#12 修复了 try body 内控制流的 finally 复制，但 except handler 内 break + finally 未覆盖。
- **ternary 条件 + break 归属**（02）：`_detect_break_continue` 对 if 条件为 ternary 时的 break 归属，ternary 内部分支跳转与 break 条件跳转混淆，break 被丢弃。R01 #5 是 ternary 作为 while 条件的已知限制，本例为 ternary 作为 if 体条件。
- **class pattern 无参数 as 误判**（11）：`_find_store_in_successors`（pattern_parser.py）对 class pattern 无参数（`P()`，MATCH_CLASS 参数 0）的 as 绑定归属。R04 #04 修复了 sequence pattern 的 as 误判，但 class pattern 无参数未覆盖。

共发现 **13 个** 真实 LOOP 反编译错误（均通过 `timeout 280 python -m pytest tests/exhaustive/loop/round_05/ -q` 实测失败确认，`13 failed` / 0 pass / 0 skip / 0 error），覆盖 8 类根因，与 R01 已修复 9 bug + 5 已知限制、R02/R03/R04 各 12 bug 模式不重叠。

---

## 回归验证

`timeout 60 python -m pytest tests/exhaustive/loop/round_04/ -q` →
`12 passed`（R04 修复无退化）

本 Round 仅新增测试文件与 findings 文档，**未修改任何反编译器源代码**，基线无退化。
