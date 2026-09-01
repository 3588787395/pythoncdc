# LOOP 区域 Round 02 测试发现报告

## 基线

- **反编译器**：pythoncdc（`core/cfg/region_analyzer.py` + `core/cfg/region_ast_generator.py`）
- **运行环境**：Python 3.11.15
- **测试框架**：`tests/exhaustive/base.py::ExhaustiveTestCase.verify_decompilation()`
  （编译 → 反编译 → 语法检查 → 重编译 → `_compare_code_objects` 字节码等价比较）
- **Round 01 状态**：已修复 9 个 bug；已知限制 5 个（#5 while 三元条件 / #10 try-except-else-finally / #13 continue 嵌套 if / #14 四操作数链式比较 / #15 嵌套 for-else）。
- **本 Round 范围**：仅覆盖与 R01 16 个模式及 5 个已知限制不同的新模式；不修改反编译器源代码。
- **验证命令**：`timeout 240 python -m pytest tests/exhaustive/loop/round_02/ -q`
- **结果**：`12 failed`（全部为真实反编译错误，0 skip / 0 pass）。

测试目录：`/workspace/tests/exhaustive/loop/round_02/`

字节码 diff 说明：过滤跳转/对齐指令（JUMP_*/FOR_ITER/SEND/NOP/CACHE/POP_JUMP_*）后比较操作码序列。`ORIG` 为源码编译结果，`RECOMP` 为反编译结果重编译结果。

---

## 错误 01 — for-else + break（模块级，else 被丢弃）

- **测试文件**：`tests/exhaustive/loop/round_02/test_r2_for_else_break_module.py`
- **REGION_TYPE**：FOR_LOOP
- **源码**：
  ```python
  for i in r:
      if i:
          break
  else:
      x = 1
  ```
- **反编译结果**：
  ```python
  for i in r:
      if i:
          break
  x = 1
  ```
- **失败类型**：字节码不匹配（指令 6 参数 None vs 1，LOAD_CONST）。`else` 子句被丢弃，`x = 1` 退化为循环后的顺序语句。
- **字节码 diff**：
  - ORIG (12): `RESUME LOAD_NAME GET_ITER STORE_NAME LOAD_NAME POP_TOP LOAD_CONST RETURN_VALUE LOAD_CONST STORE_NAME LOAD_CONST RETURN_VALUE`
  - RECOMP (10): `RESUME LOAD_NAME GET_ITER STORE_NAME LOAD_NAME POP_TOP LOAD_CONST STORE_NAME LOAD_CONST RETURN_VALUE`
  - 缺失：`else` 正常退出路径的 `LOAD_CONST None; RETURN_VALUE`（for_iter_exit → else 入口语义丢失）。
- **疑似根因**：`_find_loop_else`（region_analyzer.py:4010）for-loop 分支。模块级场景下 break 目标与 for_iter_exit 都汇入模块尾部的 `LOAD_CONST None; RETURN_VALUE` 块，`_break_hits_for_iter_exit` 判定为真（行 4039 `return None, natural_exit`），导致 else_blocks 返回 None；else 内容泄漏为顺序语句。违反「每块唯一归属」——else 块未被循环区域归属。

---

## 错误 02 — for-else + break（模块级，else 多语句，else 被丢弃）

- **测试文件**：`tests/exhaustive/loop/round_02/test_r2_for_else_multi_stmt_module.py`
- **REGION_TYPE**：FOR_LOOP
- **源码**：
  ```python
  for i in r:
      if i:
          break
  else:
      a = 1
      b = 2
  ```
- **反编译结果**：
  ```python
  for i in r:
      if i:
          break
  a = 1
  b = 2
  ```
- **失败类型**：字节码不匹配（指令 6 参数 None vs 1，LOAD_CONST）。else 多语句整体被丢弃，退化为顺序语句。
- **字节码 diff**：
  - ORIG (14): `... LOAD_NAME POP_TOP LOAD_CONST RETURN_VALUE LOAD_CONST STORE_NAME LOAD_CONST STORE_NAME LOAD_CONST RETURN_VALUE`
  - RECOMP (12): `... LOAD_NAME POP_TOP LOAD_CONST STORE_NAME LOAD_CONST STORE_NAME LOAD_CONST RETURN_VALUE`
- **疑似根因**：同错误 01，`_find_loop_else` for-loop 分支在模块级 break 场景误返 None。证实该缺陷与 else 内语句数量无关，是 else 识别本身失败。

---

## 错误 03 — for-else（else 含 return，无尾随语句，else 被丢弃）

- **测试文件**：`tests/exhaustive/loop/round_02/test_r2_for_else_return_no_trailing.py`
- **REGION_TYPE**：FOR_LOOP
- **源码**：
  ```python
  def f():
      for i in r:
          if i:
              break
      else:
          return 1
  ```
- **反编译结果**：
  ```python
  def f():
      for i in r:
          if i:
              break
      return 1
  ```
- **失败类型**：字节码不匹配（嵌套 code object 指令 6 参数 None vs 1）。`else: return 1` 被提升为函数体的普通 return，break 跳过 else 的语义丢失。
- **字节码 diff**（f 函数体）：
  - ORIG (10): `RESUME LOAD_GLOBAL GET_ITER STORE_FAST LOAD_FAST POP_TOP LOAD_CONST RETURN_VALUE LOAD_CONST RETURN_VALUE`
  - RECOMP (8): `RESUME LOAD_GLOBAL GET_ITER STORE_FAST LOAD_FAST POP_TOP LOAD_CONST RETURN_VALUE`
  - 缺失：break 路径的隐式 `return None`（LOAD_CONST None; RETURN_VALUE）。
- **疑似根因**：`_find_loop_else` while/for 通用尾部逻辑。else 块以 `return 1` 结尾，break 出口为函数隐式 `return None`；else 块被 `_is_early_return_block`（region_analyzer.py:4206）误判为早返回块而过滤（else_blocks → None）。注意：当 else 后有尾随语句时（如同源 `for_else_return` 加 `return 2`）则通过——说明缺陷特定于「else 以 return 结束且无尾随代码」结构。与 R01 `while_else_return`（while-else-return，已修复）不同，本例为 for-else-return。

---

## 错误 04 — for-else + continue + break（else 被丢弃，if/elif 错误合并）

- **测试文件**：`tests/exhaustive/loop/round_02/test_r2_for_else_continue_break.py`
- **REGION_TYPE**：FOR_LOOP
- **源码**：
  ```python
  for i in r:
      if i:
          continue
      if i > 3:
          break
  else:
      x = 1
  ```
- **反编译结果**：
  ```python
  for i in r:
      if i:
          continue
      elif (i > 3):
          break
  x = 1
  ```
- **失败类型**：字节码不匹配（指令 9 参数 None vs 1，LOAD_CONST）。两个独立 `if` 被错误合并为 `if/elif`，且 else 丢弃。
- **字节码 diff**：
  - ORIG (15): `... LOAD_NAME LOAD_CONST COMPARE_OP POP_TOP LOAD_CONST RETURN_VALUE LOAD_CONST STORE_NAME LOAD_CONST RETURN_VALUE`
  - RECOMP (13): `... LOAD_NAME LOAD_CONST COMPARE_OP POP_TOP LOAD_CONST STORE_NAME LOAD_CONST RETURN_VALUE`
- **疑似根因**：两处缺陷叠加：(1) 循环体内两个顺序 `if`（第一个以 continue 结束）被 IfRegion 归约误合并为 if/elif 链——continue 的跳转目标与第二个 if 的入口重合，触发 elif 合并；(2) else 同错误 01 被丢弃。违反「每块唯一归属」与「父引用子入口」。

---

## 错误 05 — while + break 在 if/elif 中（回边重检块泄漏为多余分支）

- **测试文件**：`tests/exhaustive/loop/round_02/test_r2_while_break_if_elif.py`
- **REGION_TYPE**：WHILE_LOOP
- **源码**：
  ```python
  def f():
      while a:
          if b:
              break
          elif c:
              break
      return 1
  ```
- **反编译结果**：
  ```python
  def f():
      while a:
          if b:
              break
          elif c:
              break
          elif a:
              pass
          else:
              break
  ```
- **失败类型**：字节码不匹配（嵌套 code object 指令 3 操作码 LOAD_GLOBAL vs LOAD_CONST）。多出虚假 `elif a: pass / else: break` 分支。
- **字节码 diff**（f 函数体）：
  - ORIG (7): `RESUME LOAD_GLOBAL LOAD_GLOBAL LOAD_GLOBAL LOAD_GLOBAL LOAD_CONST RETURN_VALUE`
  - RECOMP (16): `RESUME LOAD_GLOBAL LOAD_GLOBAL LOAD_CONST RETURN_VALUE LOAD_GLOBAL LOAD_CONST RETURN_VALUE LOAD_GLOBAL LOAD_CONST RETURN_VALUE LOAD_GLOBAL LOAD_CONST RETURN_VALUE LOAD_CONST RETURN_VALUE`
- **疑似根因**：while 条件 `a` 在回边处的重检块（`LOAD a; POP_JUMP_FORWARD_IF_FALSE → exit`）未被抑制，被 `_loop_generate_body`/`_generate_block_statements` 当作循环体内的 if 语句发射。重检块的条件 `a` 被解释为 `elif a:`，其假出口（循环退出）被解释为 `else: break`。`_loop_generate_while` 的回边重检抑制逻辑（参考 ternary 的 `_ternary_cond_names` 抑制）未覆盖普通 while + body-break 场景。

---

## 错误 06 — while + 两个顶层 break（回边重检块泄漏为多余分支）

- **测试文件**：`tests/exhaustive/loop/round_02/test_r2_while_two_break_top_level.py`
- **REGION_TYPE**：WHILE_LOOP
- **源码**：
  ```python
  while a:
      if b:
          break
      if c:
          break
  ```
- **反编译结果**：
  ```python
  while a:
      if b:
          break
      elif c:
          break
      elif a:
          pass
      else:
          break
  ```
- **失败类型**：字节码不匹配（指令 11 操作码 LOAD_CONST vs LOAD_NAME）。两个独立 `if b`/`if c` 被合并为 if/elif，并多出虚假 `elif a: pass / else: break`。
- **字节码 diff**：
  - ORIG (13): `RESUME LOAD_NAME LOAD_NAME LOAD_CONST RETURN_VALUE LOAD_NAME LOAD_CONST RETURN_VALUE LOAD_NAME LOAD_CONST RETURN_VALUE LOAD_CONST RETURN_VALUE`
  - RECOMP (16): `RESUME LOAD_NAME LOAD_NAME LOAD_CONST RETURN_VALUE LOAD_NAME LOAD_CONST RETURN_VALUE LOAD_NAME LOAD_CONST RETURN_VALUE LOAD_NAME LOAD_CONST RETURN_VALUE LOAD_CONST RETURN_VALUE`
- **疑似根因**：同错误 05 的回边重检块泄漏，叠加两个 break-if 被 elif 合并。证实该根因与 break 数量、是否 elif 无关，是 while 回边重检抑制缺失的共性缺陷。

---

## 错误 07 — while-else + break + continue（回边重检块泄漏，else 丢失）

- **测试文件**：`tests/exhaustive/loop/round_02/test_r2_while_else_break_continue.py`
- **REGION_TYPE**：WHILE_LOOP
- **源码**：
  ```python
  def f():
      while a:
          if b:
              break
          if c:
              continue
      else:
          x = 1
      return x
  ```
- **反编译结果**：
  ```python
  def f():
      while a:
          if b:
              break
          elif c:
              continue
          elif a:
              pass
          else:
              break
      return x
  ```
- **失败类型**：字节码不匹配（嵌套 code object 指令 5 操作码 LOAD_CONST vs LOAD_GLOBAL）。else 子句（`x = 1`）丢失，并多出虚假分支。
- **字节码 diff**（f 函数体）：
  - ORIG (9): `RESUME LOAD_GLOBAL LOAD_GLOBAL LOAD_GLOBAL LOAD_GLOBAL LOAD_CONST STORE_FAST LOAD_FAST RETURN_VALUE`
  - RECOMP (8): `RESUME LOAD_GLOBAL LOAD_GLOBAL LOAD_GLOBAL LOAD_GLOBAL LOAD_GLOBAL LOAD_GLOBAL RETURN_VALUE`
- **疑似根因**：回边重检块泄漏（同错误 05）+ while-else 识别失败。while-else 的 else 块（`x=1`）被回边重检的假分支覆盖/被 `_find_loop_else` while 分支的 `_else_is_skipped_by_break` 逻辑误判而丢弃。与 R01 `while_else_return`（仅 break+else return，已修复）不同，本例含 continue。

---

## 错误 08 — while + 多个不同嵌套层级的 break（回边重检块泄漏，条件被错误合并为 BoolOp）

- **测试文件**：`tests/exhaustive/loop/round_02/test_r2_while_multi_break_nested.py`
- **REGION_TYPE**：WHILE_LOOP
- **源码**：
  ```python
  def f():
      while a:
          if b:
              if c:
                  break
          if d:
              break
      return 1
  ```
- **反编译结果**：
  ```python
  def f():
      while a:
          if (b and c):
              break
          elif d:
              break
          elif a:
              if b:
                  pass
          else:
              break
  ```
- **失败类型**：字节码不匹配（嵌套 code object 指令 4 操作码 LOAD_GLOBAL vs LOAD_CONST）。嵌套 `if b: if c:` 被错误合并为 `if (b and c):`，并多出虚假分支。
- **字节码 diff**（f 函数体）：
  - ORIG (8): `RESUME LOAD_GLOBAL LOAD_GLOBAL LOAD_GLOBAL LOAD_GLOBAL LOAD_GLOBAL LOAD_CONST RETURN_VALUE`
  - RECOMP (18): `RESUME LOAD_GLOBAL LOAD_GLOBAL LOAD_GLOBAL LOAD_CONST RETURN_VALUE LOAD_GLOBAL LOAD_CONST RETURN_VALUE LOAD_GLOBAL LOAD_GLOBAL LOAD_CONST RETURN_VALUE LOAD_GLOBAL LOAD_CONST RETURN_VALUE LOAD_CONST RETURN_VALUE`
- **疑似根因**：同错误 05 回边重检泄漏；额外地，嵌套 `if b: if c: break` 被 BoolOpRegion 误识别为 `if (b and c):`（b 的真分支直接进 c 的判断，被当成短路 and 链）。违反「嵌套即抽象节点」——嵌套 if 被压平为 BoolOp。

---

## 错误 09 — while-True + break + continue 混合（break 脱离 if 体）

- **测试文件**：`tests/exhaustive/loop/round_02/test_r2_while_true_break_continue_mix.py`
- **REGION_TYPE**：WHILE_LOOP
- **源码**：
  ```python
  while True:
      if a:
          continue
      if b:
          break
      x = 1
  ```
- **反编译结果**：
  ```python
  while True:
      if a:
          continue
      if b:
          pass
      break
      x = 1
  ```
- **失败类型**：字节码不匹配（指令数 7 vs 5）。`if b: break` 被拆成 `if b: pass` + 独立 `break`，且 `x = 1` 被挤到 break 之后（死代码）。
- **字节码 diff**：
  - ORIG (7): `RESUME LOAD_NAME LOAD_NAME LOAD_CONST RETURN_VALUE LOAD_CONST STORE_NAME`
  - RECOMP (5): `RESUME LOAD_NAME LOAD_NAME LOAD_CONST RETURN_VALUE`
- **疑似根因**：`_detect_break_continue`/`_loop_generate_body` 对 break 的归属处理。break 块（`if b` 的真分支）被识别为独立 break_blocks 出口，break 作为独立语句发射，而原 `if b` 的 body 退化为 `pass`。break 未作为 IfRegion 子节点嵌套入 if 体（违反「父引用子入口」）。与 R01 `while_true_continue_only`（仅 continue，已修复）不同，本例 break+continue 共存触发 break 归属错误。

---

## 错误 10 — for iter 含 walrus（双重求值）

- **测试文件**：`tests/exhaustive/loop/round_02/test_r2_for_iter_walrus.py`
- **REGION_TYPE**：FOR_LOOP
- **源码**：
  ```python
  def f():
      for x in (n := g()):
          y = x
  ```
- **反编译结果**：
  ```python
  def f():
      n = g()
      for x in (n := g()):
          y = x
  ```
- **失败类型**：字节码不匹配（嵌套 code object 指令 4 操作码 COPY vs STORE_FAST）。`g()` 被调用两次（双重求值），违反原语义。
- **字节码 diff**（f 函数体）：
  - ORIG (12): `RESUME LOAD_GLOBAL PRECALL CALL COPY STORE_FAST GET_ITER STORE_FAST LOAD_FAST STORE_FAST LOAD_CONST RETURN_VALUE`
  - RECOMP (16): `RESUME LOAD_GLOBAL PRECALL CALL STORE_FAST LOAD_GLOBAL PRECALL CALL COPY STORE_FAST GET_ITER STORE_FAST LOAD_FAST STORE_FAST LOAD_CONST RETURN_VALUE`
  - RECOMP 多出一次 `LOAD_GLOBAL PRECALL CALL`（第二次调用 g()）。
- **疑似根因**：`_loop_generate_for` 的 for_iter_setup 处理。walrus 的 `COPY; STORE_FAST n` 既被 `_loop_extract_for_iter_pre_stmts` 当作 pre_stmt 发射为 `n = g()`，又被 iter 表达式重建为 `(n := g())`。for_iter_setup 块被双重归属（违反「每块唯一归属」）。与 R01 `while_walrus_break`（while 条件 walrus，已修复）不同，本例为 for-iter walrus。

---

## 错误 11 — for body 含 del（DELETE_SUBSCR 未重建）

- **测试文件**：`tests/exhaustive/loop/round_02/test_r2_for_body_del.py`
- **REGION_TYPE**：FOR_LOOP
- **源码**：
  ```python
  def f():
      for i in r:
          del m[i]
  ```
- **反编译结果**：
  ```python
  def f():
      for i in r:
          i
  ```
- **失败类型**：字节码不匹配（嵌套 code object 指令 4 操作码 LOAD_GLOBAL vs LOAD_FAST）。`del m[i]` 退化为裸表达式 `i`，`DELETE_SUBSCR` 完全丢失。
- **字节码 diff**（f 函数体）：
  - ORIG (9): `RESUME LOAD_GLOBAL GET_ITER STORE_FAST LOAD_GLOBAL LOAD_FAST DELETE_SUBSCR LOAD_CONST RETURN_VALUE`
  - RECOMP (8): `RESUME LOAD_GLOBAL GET_ITER STORE_FAST LOAD_FAST POP_TOP LOAD_CONST RETURN_VALUE`
  - ORIG 的 `LOAD_GLOBAL m; LOAD_FAST i; DELETE_SUBSCR` 在 RECOMP 中只剩 `LOAD_FAST i; POP_TOP`。
- **疑似根因**：`_generate_block_statements`/`_build_statement` 在循环体块上下文未将 `DELETE_SUBSCR` 重建为 `ast.Delete`。`LOAD_GLOBAL m; LOAD_FAST i; DELETE_SUBSCR` 序列中，`m` 被忽略、`i` 作为裸 Expr 发射、DELETE_SUBSCR 丢失。表达式重建器对 DELETE_SUBSCR 的 Delete 语句映射缺失。

---

## 错误 12 — while body 含 await（循环退化为 if）

- **测试文件**：`tests/exhaustive/loop/round_02/test_r2_while_body_await.py`
- **REGION_TYPE**：WHILE_LOOP
- **源码**：
  ```python
  async def f():
      while a:
          await g()
  ```
- **反编译结果**：
  ```python
  async def f():
      if (a and await g()):
          return None
  ```
- **失败类型**：字节码不匹配（嵌套 code object 指令 12 操作码 POP_TOP vs LOAD_CONST）。while 循环完全消失，退化为 `if (a and await g()): return None`。
- **字节码 diff**（f 协程体）：
  - ORIG (18): `RETURN_GENERATOR POP_TOP RESUME LOAD_GLOBAL LOAD_GLOBAL PRECALL CALL GET_AWAITABLE LOAD_CONST YIELD_VALUE RESUME JUMP_BACKWARD_NO_INTERRUPT POP_TOP LOAD_GLOBAL LOAD_CONST RETURN_VALUE LOAD_CONST RETURN_VALUE`
  - RECOMP (18): `RETURN_GENERATOR POP_TOP RESUME LOAD_GLOBAL LOAD_GLOBAL PRECALL CALL GET_AWAITABLE LOAD_CONST YIELD_VALUE RESUME JUMP_BACKWARD_NO_INTERRUPT LOAD_CONST RETURN_VALUE LOAD_CONST RETURN_VALUE LOAD_CONST RETURN_VALUE`
  - ORIG 含 `JUMP_BACKWARD_NO_INTERRUPT`（await 轮询回边）+ `POP_TOP LOAD_GLOBAL ... RETURN_VALUE`（while 条件重检）；RECOMP 丢失循环回边语义。
- **疑似根因**：await 的轮询自循环（`GET_AWAITABLE + SEND/YIELD_VALUE + JUMP_BACKWARD_NO_INTERRUPT`）与外层 while 循环的回边混淆。`_is_await_polling_loop`（region_analyzer.py:3029）抑制 await 轮询自循环时，误将包含 await 的 while 循环本身也抑制/合并；while 条件 `a` 与 `await g()` 被融合为 BoolOp `a and await g()`（BoolOpRegion 误识别），while 退化为 if。违反「嵌套即抽象节点」——await 表达式应嵌套入 while body，而非并入条件。

---

## 汇总

| # | 错误描述 | 测试文件 | 根因分类 |
|---|---------|---------|---------|
| 01 | for-else+break（模块级）else 丢失 | test_r2_for_else_break_module | for-else 识别 |
| 02 | for-else+break（模块级多语句）else 丢失 | test_r2_for_else_multi_stmt_module | for-else 识别 |
| 03 | for-else（else 含 return 无尾随）else 丢失 | test_r2_for_else_return_no_trailing | for-else 识别 |
| 04 | for-else+continue+break else 丢失 + if/elif 合并 | test_r2_for_else_continue_break | for-else 识别 + if 合并 |
| 05 | while+break if/elif 回边重检泄漏 | test_r2_while_break_if_elif | while 回边重检 |
| 06 | while+两顶层 break 回边重检泄漏 | test_r2_while_two_break_top_level | while 回边重检 |
| 07 | while-else+break+continue 回边重检泄漏 + else 丢失 | test_r2_while_else_break_continue | while 回边重检 + else |
| 08 | while+多嵌套 break 回边重检泄漏 + BoolOp 误合并 | test_r2_while_multi_break_nested | while 回边重检 + BoolOp |
| 09 | while-True+break+continue break 脱离 if | test_r2_while_true_break_continue_mix | break 归属 |
| 10 | for-iter walrus 双重求值 | test_r2_for_iter_walrus | for-iter setup 双重归属 |
| 11 | for body del 未重建 | test_r2_for_body_del | DELETE_SUBSCR 重建缺失 |
| 12 | while body await 循环退化为 if | test_r2_while_body_await | await 轮询循环误抑制 |

**根因聚类**：
- **for-else 识别**（01/02/03/04）：`_find_loop_else` for-loop 分支在 break/return/continue 场景下误返 None，else 退化为顺序语句。
- **while 回边重检泄漏**（05/06/07/08）：while 条件在回边处的重检块未被抑制，泄漏为循环体内虚假 `if/elif/else`；常叠加 if-elif 合并或 else 丢失。
- **break 归属**（09）：break 块未嵌套入 IfRegion 子节点，break 独立发射。
- **for-iter setup 双重归属**（10）：walrus 的 COPY+STORE 被同时发射为 pre_stmt 与 iter 表达式。
- **DELETE_SUBSCR 重建缺失**（11）：循环体块内 `del m[i]` 未映射为 ast.Delete。
- **await 轮询循环误抑制**（12）：含 await 的 while 被误并为 BoolOp 条件，循环消失。

共发现 **12 个** 真实 LOOP 反编译错误（均通过 pytest 实测失败确认），覆盖 6 类根因，与 R01 已修复的 9 个 bug 及 5 个已知限制模式不重叠。
