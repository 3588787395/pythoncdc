# Ternary Region Round 14 测试发现报告

## 概览

- **执行日期**: 2026-07-21
- **基线**: R13 已完成（commit 46d82ea），ternary 全量基线 88 failed / 365 passed / 8 skipped
- **测试范围**: 新增 R14 对抗性测试，聚焦未被 R1-R13 充分覆盖的常见 Python 代码模式
- **新建测试文件数**: 22
- **真失败 bug 数**: 11
- **停止条件**: 累计 11 > 10，已满足停止条件

## 整体测试结果

```
$ cd /workspace && timeout 250 python -m pytest tests/exhaustive/ternary/test_r14_*.py --tb=no -q
11 failed, 14 passed in 1.55s
```

R14 测试集与现有 ternary 全量基线无重叠。R14 测试通过数 = 14（基础场景验证 R13 修复无退化），R14 失败数 = 11（新发现的真 bug）。

集成到全量基线后：
```
$ cd /workspace && timeout 250 python -m pytest tests/exhaustive/ternary/ --tb=no -q
99 failed, 379 passed, 8 skipped in 3.94s
```
- **基线**（R13 commit 46d82ea）：88 failed / 365 passed / 8 skipped
- **R14 测试加入后**：99 failed / 379 passed / 8 skipped
- **变化**: 失败数 +11（R14 新发现的 11 个真 bug），通过数 +14（R14 测试中通过的 14 个）

---

## 一、R14 新发现对抗性 bug（11 个）

### R14-01 ternary 在 while 条件中含 COMPARE_OP
- **测试文件**: `tests/exhaustive/ternary/test_r14_ternary_while_cond_compare.py`
- **源码**: `while (a if c else b) > 0:\n    pass`
- **失败现象**: `指令数不匹配: 15 vs 3`
- **失败指令**:
  - 原始: `RESUME, LOAD a, LOAD c, LOAD b, LOAD_CONST 0, COMPARE_OP, LOAD a, LOAD c, LOAD b, LOAD_CONST 0, COMPARE_OP, LOAD_CONST None, RETURN_VALUE, LOAD_CONST None, RETURN_VALUE`
  - 重编: `RESUME, LOAD_CONST None, RETURN_VALUE`（整个 while 循环丢失！）
- **根因**: while 条件是 ternary 与常量比较（COMPARE_OP）。R3 ternary_while_cond 已测过 `while (ternary): pass`（直接条件），但加 `> 0` COMPARE_OP 后，ternary merge 块的栈顶先经 COMPARE_OP + POP_JUMP_IF_FALSE 跳回 while 顶。反编译器可能因 COMPARE_OP 后续跳转路径不识别 ternary region，整个 while 循环被丢弃，仅保留 RESUME + RETURN_VALUE None。
- **影响范围**: 任何 `while (ternary) > <const>:`、`while (ternary) == <val>:` 比较 while 条件 + ternary。

### R14-02 ternary 在 while 条件 + walrus 赋值
- **测试文件**: `tests/exhaustive/ternary/test_r14_ternary_walrus_in_while_cond.py`
- **源码**: `while (n := (a if c else b)) > 0:\n    pass`
- **失败现象**: `指令数不匹配: 19 vs 3`
- **失败指令**:
  - 原始: 19 条指令，含 `LOAD a, LOAD c, LOAD b, COPY, STORE_NAME n, LOAD_CONST 0, COMPARE_OP` polling 循环
  - 重编: `RESUME, LOAD_CONST None, RETURN_VALUE`（整个 while 循环 + walrus + ternary 全部丢失！）
- **根因**: while 条件含 walrus 表达式，walrus value 是 ternary，与 R14-01 同样问题但更严重。ternary merge 之后 STORE_NAME n (walrus) + COMPARE_OP + POP_JUMP_IF_FALSE，反编译器不识别 ternary region，整个 while 循环丢失。
- **影响范围**: 任何 `while (n := (ternary)) <compare>:` walrus + ternary + compare 组合。

### R14-03 ternary 在 elif 条件中
- **测试文件**: `tests/exhaustive/ternary/test_r14_ternary_elif_cond.py`
- **源码**: `if x:\n    pass\nelif (a if c else b):\n    pass`
- **失败现象**: `反编译结果中未找到预期的区域类型 TERNARY (期望AST节点: ['IfExp'])`
- **反编译结果**:
  ```
  if x:
      pass
  elif c:
      if a:
          pass
  elif b:
      pass
  ```
- **根因**: elif 条件本身是 ternary。R3 ternary_in_cond 已测过 if 条件是 ternary，R14 测 elif 变体。反编译器把 `elif (a if c else b): pass` 错误展开为 `elif c: if a: pass` + `elif b: pass` 三层 if-elif 链，丢失 ternary IfExp 结构。ternary region 与 elif region 边界归属冲突。
- **影响范围**: 任何 `if X: ... elif (ternary): ...` elif 条件是 ternary 场景。

### R14-04 ternary 在 for iter list literal 中间元素
- **测试文件**: `tests/exhaustive/ternary/test_r14_ternary_for_iter_list_middle.py`
- **源码**: `for x in [1, (a if c else b), 2]:\n    pass`
- **失败现象**: `指令数不匹配: 11 vs 8`
- **失败指令**:
  - 原始: `RESUME, LOAD_CONST 1, LOAD a, LOAD c, LOAD b, LOAD_CONST 2, BUILD_TUPLE 3, GET_ITER, STORE_NAME x, LOAD_CONST None, RETURN_VALUE`
  - 重编: `RESUME, LOAD a, LOAD c, LOAD b, GET_ITER, STORE_NAME x, LOAD_CONST None, RETURN_VALUE`（前后 LOAD_CONST 元素 + BUILD_TUPLE 3 全丢失）
- **根因**: for 循环的 iter 表达式是 list literal，list 中间元素是 ternary。R13-08 修复了 `[1, ternary, 2]` 单语句场景，R14 在 for iter 消费链下未正确归约。BUILD_TUPLE 3 + sibling LOAD_CONST 1/2 全丢失，仅保留 ternary 表达式。可能是 for 循环的 GET_ITER + FOR_ITER polling 与 BUILD_TUPLE 归属冲突。
- **影响范围**: 任何 `for x in [t1, ternary, t2]:` for iter list literal + 中间 ternary 场景。

### R14-05 ternary 在 raise 异常类型位置 + from
- **测试文件**: `tests/exhaustive/ternary/test_r14_ternary_raise_ternary_type_from.py`
- **源码**: `raise (a if c else b) from E2`
- **失败现象**: `指令数不匹配: 6 vs 10`
- **失败指令**:
  - 原始: `RESUME, LOAD E2, LOAD a, LOAD c, LOAD b, RAISE_VARARGS 2`
  - 重编: `RESUME, LOAD E2, LOAD a, POP_TOP, LOAD_CONST None, RETURN_VALUE, LOAD E2, POP_TOP, LOAD_CONST None, RETURN_VALUE`（raise 完全丢失，仅保留两个独立 LOAD E2 + LOAD a 语句）
- **根因**: raise from 的异常类型本身是 ternary（与 R8 ternary_cause 不同，R14 测异常类型位置）。R7 raise_no_from 测过 `raise (ternary)` 不带 from，R14 加 `from E2` 后变体未正确归约。ternary merge 块栈顶作为 RAISE_VARARGS 2 第一参数，但 ternary region 与 RAISE_VARARGS region 边界冲突导致 raise 完全丢失。
- **影响范围**: 任何 `raise (ternary) from E:` raise 异常类型是 ternary + from cause 场景。

### R14-06 ternary 在 raise arg 与 cause 共存
- **测试文件**: `tests/exhaustive/ternary/test_r14_ternary_raise_arg_and_cause.py`
- **源码**: `raise E(a if c else b) from (d if e else f)`
- **失败现象**: `指令数不匹配: 12 vs 14`
- **失败指令**:
  - 原始: `RESUME, PUSH_NULL, LOAD E, LOAD c, LOAD a, LOAD b, PRECALL, CALL 1, LOAD e, LOAD d, LOAD f, RAISE_VARARGS 2`
  - 重编: `RESUME, PUSH_NULL, LOAD E, LOAD c, LOAD a, LOAD b, LOAD e, LOAD d, LOAD f, PRECALL, CALL 1, POP_TOP, LOAD_CONST None, RETURN_VALUE`（两个 ternary 都丢失 IfExp 结构，最终 call 没参数 + raise 完全丢失）
- **根因**: raise 同时含两个 ternary：第一个 ternary 在 E() 调用 args，第二个 ternary 在 from cause 位置。R7 raise_from_complex 已测 raise E + ternary arg，R8 测 raise from ternary cause，R14 测两个 ternary 共存场景。两个 ternary region 同时归约时 chained ternary 识别冲突，CALL 与 RAISE_VARARGS 都未正确归约。
- **影响范围**: 任何 `raise E(ternary) from (ternary):` 两个 ternary 共存于 raise 场景。

### R14-07 ternary 在 return + method chain
- **测试文件**: `tests/exhaustive/ternary/test_r14_ternary_return_method_chain.py`
- **源码**: `def f():\n    return (a if c else b).method()`
- **失败现象**: `嵌套code object不匹配 (指令1): 指令数不匹配: 8 vs 10`
- **失败指令**:
  - 原始: `RESUME, LOAD_GLOBAL a, LOAD_GLOBAL c, LOAD_GLOBAL b, LOAD_METHOD method, PRECALL, CALL 0, RETURN_VALUE`
  - 重编: `RESUME, LOAD_GLOBAL a, LOAD_GLOBAL c, LOAD_GLOBAL b, LOAD_METHOD method, PRECALL, CALL 0, POP_TOP, LOAD_CONST None, RETURN_VALUE`（return 表达式被丢弃，仅保留 ternary + method call 但 POP_TOP 后 RETURN_VALUE None）
- **根因**: return 表达式是 ternary + method chain。R13-01 修复了 `s.upper().split(ternary)` method chain + ternary arg。R14 测 return ternary + method chain 变体：ternary merge 之后 LOAD_METHOD + PRECALL + CALL 0 消费链作为 RETURN_VALUE 栈顶。反编译器丢失 RETURN_VALUE 消费链，将表达式语句 POP_TOP 替换为 return 语句。
- **影响范围**: 任何 `return (ternary).method():` return + ternary + method chain 场景。

### R14-08 ternary 在 multi-with 第二 item + as 别名
- **测试文件**: `tests/exhaustive/ternary/test_r14_ternary_with_multiple_second_as.py`
- **源码**: `with a as x, (b if c else d) as y:\n    pass`
- **失败现象**: `反编译结果中未找到预期的区域类型 TERNARY (期望AST节点: ['IfExp'])`
- **反编译结果**:
  ```
  with a as x: pass
  ```
- **根因**: with 多 item，第二个 item 的 context manager 是 ternary 且带 as 别名。R3 with_as 测单 with ternary + as，R7 with_multiple 测 multi-with + body 内 ternary 赋值（不是 ctx mgr 位置 ternary）。R14 测 multi-with 第二 item ctx mgr 是 ternary + as 别名完整变体。BUILD_TUPLE 2 + BEFORE_WITH + WITH_EXIT 链与 ternary region 边界冲突，第二个 with item 完全丢失。
- **影响范围**: 任何 `with X as a, (ternary) as b:` multi-with 第二 item ctx mgr 是 ternary 场景。

### R14-09 ternary 在 yield from + method chain
- **测试文件**: `tests/exhaustive/ternary/test_r14_ternary_yield_from_with_method.py`
- **源码**: `def gen():\n    yield from (a if c else b).items()`
- **失败现象**: `反编译结果中未找到预期的区域类型 TERNARY (期望AST节点: ['IfExp'])`
- **反编译结果**:
  ```
  def gen():
      None
  ```
- **根因**: yield from 表达式是 ternary 后接 .items() 方法调用。R8 yield_from_assign 已测 yield from (ternary) + 赋值，R13 yield_from 重测同步 yield from。R14 测 yield from ternary + method 链变体：ternary merge 之后 LOAD_METHOD items + PRECALL + CALL 0 消费链作为 GET_YIELD_FROM_ITER + SEND + YIELD_VALUE polling 循环输入。反编译器不识别 ternary region，整个 gen 函数体反编译为 None。
- **影响范围**: 任何 `yield from (ternary).method():` yield from + ternary + method chain 场景。

### R14-10 ternary 在 slice assign 双边界
- **测试文件**: `tests/exhaustive/ternary/test_r14_ternary_slice_assign_both_bounds.py`
- **源码**: `x[(a if c else b):(d if e else f)] = 1`
- **失败现象**: `指令数不匹配: 13 vs 14`
- **失败指令**:
  - 原始: `RESUME, LOAD_CONST 1, LOAD x, LOAD c, LOAD a, LOAD b, LOAD e, LOAD d, LOAD f, BUILD_SLICE 2, STORE_SUBSCR, LOAD_CONST None, RETURN_VALUE`
  - 重编: `RESUME, LOAD x, LOAD c, LOAD a, POP_TOP, LOAD d, LOAD f, POP_TOP, LOAD_CONST None, RETURN_VALUE, LOAD x, POP_TOP, LOAD_CONST None, RETURN_VALUE`（BUILD_SLICE 2 + STORE_SUBSCR + 两个 ternary 全部丢失）
- **根因**: subscript slice assign，slice 上下界都是 ternary。R13-02 修复了 `del x[t:t]` 双 ternary del slice，但 R14 测 slice assign 双 ternary 变体未正确归约。BUILD_SLICE 2 + STORE_SUBSCR 与 chained ternary 归属冲突，整个 slice assign 丢失。
- **影响范围**: 任何 `x[(ternary):(ternary)] = val:` slice assign 双 ternary 边界场景。

### R14-11 ternary 在 assert 测试含两 ternary + boolop
- **测试文件**: `tests/exhaustive/ternary/test_r14_ternary_assert_two_ternaries_boolop.py`
- **源码**: `assert (a if c else b) and (d if e else f)`
- **失败现象**: `指令数不匹配: 13 vs 14`
- **失败指令**:
  - 原始: `RESUME, LOAD c, LOAD a, LOAD b, LOAD e, LOAD d, LOAD f, LOAD_ASSERTION_ERROR, RAISE_VARARGS 1, LOAD_CONST None, RETURN_VALUE, LOAD_CONST None, RETURN_VALUE`
  - 重编: `RESUME, LOAD c, LOAD a, LOAD b, POP_TOP, LOAD e, LOAD d, LOAD f, LOAD_ASSERTION_ERROR, RAISE_VARARGS 1, LOAD_CONST None, RETURN_VALUE, LOAD_CONST None, RETURN_VALUE`（中间多了一个 POP_TOP — 第二个 ternary 后丢失 IfExp 结构，被识别为独立表达式语句）
- **根因**: assert 测试表达式是两个 ternary 通过 boolop AND 组合。R7/R8 已测 assert ternary msg。R14 测 assert 测试是 boolop(ternary, ternary) 变体：两个 ternary region 同时归约，第一个 ternary merge 之后 LOAD 短路测试 + 第二个 ternary merge + POP_JUMP_IF_TRUE 跳过 RAISE_VARARGS 1。第一个 ternary 后多出 POP_TOP，第二个 ternary IfExp 结构丢失。
- **影响范围**: 任何 `assert (ternary) and (ternary):` 两个 ternary + boolop 在 assert 测试场景。

---

## 二、R14 测试通过的场景（14 个，验证 R13 修复无退化）

1. `test_r14_ternary_yield_with_binop.py` — `yield (ternary) + 1` ✓
2. `test_r14_ternary_await_attr_method.py` — `await (ternary).method()` ✓
3. `test_r14_ternary_global_then_use.py` — `global x; x = (ternary); y = x` ✓
4. `test_r14_ternary_nonlocal_nested_func.py` — 嵌套函数 nonlocal + ternary ✓
5. `test_r14_ternary_match_subject.py` — `match (ternary):` ✓
6. `test_r14_ternary_except_as_type.py` — `except (ternary) as e:` ✓
7. `test_r14_ternary_assert_test_with_msg.py` — `assert (ternary), 'msg'` ✓
8. `test_r14_ternary_return_three_ternaries.py` — `return t1, t2, t3` ✓
9. `test_r14_ternary_for_else_body.py` — `for ... else: y = (ternary)` ✓
10. `test_r14_ternary_while_else_body.py` — `while ... else: y = (ternary)` ✓
11. `test_r14_ternary_try_else_body.py` — `try ... else: x = (ternary)` ✓
12. `test_r14_ternary_finally_body.py` — `try ... finally: x = (ternary)` ✓
13. `test_r14_ternary_yield_in_binop_chain.py` — `yield (ternary) * 2 + 1` ✓
14. `test_r14_ternary_async_return_with_binop.py` — `async def f(): return (ternary) + 1` ✓

---

## 三、bug 优先级评估

| Bug ID | 类别 | 复杂度 | 优先级 |
|--------|------|--------|--------|
| R14-01 while cond compare | while + ternary + COMPARE_OP | 中 | P1 |
| R14-02 walrus in while cond | while + walrus + ternary + COMPARE_OP | 中 | P1 |
| R14-03 elif cond ternary | elif + ternary region 边界 | 中 | P1 |
| R14-04 for iter list middle | for + BUILD_TUPLE + ternary sibling | 中 | P1 |
| R14-05 raise ternary type from | raise 异常类型 + ternary | 低-中 | P1 |
| R14-06 raise arg and cause | raise + 两 ternary | 中 | P2 |
| R14-07 return method chain | return + ternary + method chain | 中 | P1 |
| R14-08 multi-with second item as | multi-with + ternary + as 别名 | 中-高 | P2 |
| R14-09 yield from with method | yield from + ternary + method chain | 中-高 | P2 |
| R14-10 slice assign both bounds | slice assign + 双 ternary | 中 | P1 |
| R14-11 assert two ternaries boolop | assert + boolop + 两 ternary | 中 | P2 |

---

## 四、停止条件

累计 11 个真失败 bug > 10 个，已满足停止条件。下面进入阶段 2 修复。
