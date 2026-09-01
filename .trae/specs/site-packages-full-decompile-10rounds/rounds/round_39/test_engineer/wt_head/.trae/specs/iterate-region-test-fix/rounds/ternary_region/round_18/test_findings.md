# Ternary Round 18 测试发现

## 基线
- ternary: 46 failed / 499 passed / 9 skipped
  （运行 `timeout 280 python -m pytest tests/exhaustive/ternary/ -q --tb=no` 验证）
- 添加 R18 测试后: 59 failed / 499 passed / 9 skipped
  （13 个新测试全部真实失败，无 PASS / SKIP 误判）

## 调试产物
- 探索脚本: `/workspace/.trae/specs/iterate-region-test-fix/rounds/ternary_region/round_18/_explore.py`
  （批量验证 50+ 候选模式，定位真实字节码 diff）
- 反编译输出检查: `/workspace/.trae/specs/iterate-region-test-fix/rounds/ternary_region/round_18/_show.py`

## 发现的 bug（13 个）

### Bug R18-01: slice 三段 (lower/upper/step) 均为 ternary
- 测试文件: `tests/exhaustive/ternary/test_r18_ternary_slice_three_ternary.py`
- 源码: `x[(a if c else b):(d if e else f):(g if h else i)]`
- 失败原因: 单一 BINARY_SUBSCR 中 BUILD_SLICE 3 的 lower/upper/step 三个操作数都是 ternary。
  三个 ternary 的 merge 块与 BUILD_SLICE 消费链协调失败，反编译退化为三段独立
  POP_TOP 表达式，BUILD_SLICE/BINARY_SUBSCR 整体丢失。
- 验证: FAILED `指令数不匹配: 16 vs 18`
  原始: `['RESUME', 'LOAD_NAME'×10, 'BUILD_SLICE', 'BINARY_SUBSCR', 'POP_TOP', 'LOAD_CONST', 'RETURN_VALUE']`
  重编: `['RESUME', 'LOAD_NAME'×3, 'POP_TOP', ... ×3 段独立表达式]`

### Bug R18-02: await g(ternary) — await 调用，参数为 ternary
- 测试文件: `tests/exhaustive/ternary/test_r18_ternary_await_call_ternary_arg.py`
- 源码: `async def f():\n    await g(a if c else b)`
- 失败原因: await 表达式消费一个函数调用 g(...)，g 的唯一位置参数是 ternary。
  ternary merge 块的 PRECALL+CALL 之后还需 GET_AWAITABLE+SEND+YIELD_VALUE 协程
  调度轮询循环。反编译完全丢失 ternary 参数与 await 包装，退化为 `await g()`。
- 验证: FAILED `嵌套code object不匹配 (指令1): 指令数不匹配: 17 vs 14`

### Bug R18-03: await g(t1, t2) — await 调用，两个 ternary 参数
- 测试文件: `tests/exhaustive/ternary/test_r18_ternary_await_call_two_ternary_args.py`
- 源码: `async def f():\n    await g(a if c else b, d if e else f)`
- 失败原因: await 调用 g(...) 的两个位置参数都是 ternary。两个 ternary 的 merge
  块先后汇聚到同一 PRECALL+CALL，再被 GET_AWAITABLE+SEND 协程调度消费。
  第二个 ternary 的 merge 块归属与第一个 ternary 的 merge 块协调失败。
- 验证: FAILED `嵌套code object不匹配 (指令1): 指令数不匹配: 20 vs 15`

### Bug R18-04: match case _ if (ternary) — 通配符 case guard 是 ternary
- 测试文件: `tests/exhaustive/ternary/test_r18_ternary_match_guard_wildcard.py`
- 源码: `match x:\n    case _ if (a if c else b):\n        pass`
- 失败原因: match 通配符 case _ 的 guard 是 ternary。R9 match_guard 测过
  `case 1 if (ternary)` (具体字面量，MATCH_VALUE 路径) 已通过。本用例 case _
  不产生 MATCH_VALUE，guard 的 ternary 直接挂在 case body 入口前，case_body
  块与 ternary 的 condition/true/false/merge 块归属冲突。
- 验证: FAILED `反编译结果中未找到预期的区域类型 TERNARY`
  反编译输出为破碎的嵌套 if:
  ```
  match x:
      case _:
          if a:
              pass
          if c:
              pass
          elif b:
              pass
  ```

### Bug R18-05: async for x in y[(ternary)] — async for iter 是 subscript 含 ternary
- 测试文件: `tests/exhaustive/ternary/test_r18_ternary_async_for_subscr.py`
- 源码: `async def f():\n    async for x in y[(a if c else b)]:\n        pass`
- 失败原因: async for 的 iter 是 y[(ternary)] —— subscript 下标是 ternary。
  R8 async_for_iter 测过 `async for x in (ternary)` (ternary 直接作 iter)。
  本用例 ternary 是 subscript 下标，merge 块的 BINARY_SUBSCR 后才走
  GET_AITER + GET_ANEXT + YIELD_VALUE 轮询，反编译丢失 subscript 与 ternary。
- 验证: FAILED `嵌套code object不匹配 (指令1): 指令数不匹配: 18 vs 16`

### Bug R18-06: x[(await y) if c else b] = 1 — subscript target 含 await+ternary
- 测试文件: `tests/exhaustive/ternary/test_r18_ternary_await_in_subscr_target.py`
- 源码: `async def f():\n    x[(await y) if c else b] = 1`
- 失败原因: STORE_SUBSCR 的下标 target 是 ternary，且 ternary 的 true 值是
  await y (协程调度)。await 在 ternary body 且整体作为 subscript target：
  ternary true_value 块含 GET_AWAITABLE+SEND+YIELD_VALUE 轮询，与 ternary
  merge 块的 STORE_SUBSCR 归属冲突。
- 验证: FAILED `嵌套code object不匹配 (指令1): 指令数不匹配: 16 vs 11`

### Bug R18-07: dictcomp key 与 value 均为 ternary
- 测试文件: `tests/exhaustive/ternary/test_r18_ternary_dictcomp_key_value_ternary.py`
- 源码: `x = {(a if c else b): (d if e else f) for k in y}`
- 失败原因: dict comprehension 的 key 和 value 都是 ternary。R6 dictcomp_complex
  测过 value 为 ternary (key 是简单变量)。本用例 key 也是 ternary：MAP_ADD
  消费栈顶 (value) 与次栈顶 (key)，两个 ternary 的 merge 块先后汇聚到同一
  MAP_ADD，反编译丢失 key ternary (保留 value ternary)。
- 验证: FAILED `嵌套code object不匹配 (指令1): 指令数不匹配: 12 vs 10`

### Bug R18-08: x[t1][t2] = 1 — chained subscript target 含两个 ternary
- 测试文件: `tests/exhaustive/ternary/test_r18_ternary_subscr_chain_assign.py`
- 源码: `x[a if c else b][d if e else f] = 1`
- 失败原因: STORE_SUBSCR 的 target 是链式 subscript x[ternary1][ternary2]，
  两个 ternary 分别是两层 BINARY_SUBSCR 的下标。R17 subscr_target_and_value
  测过单层 subscript target + value 均为 ternary。本用例 target 是两层
  subscript 各含一个 ternary，反编译退化为两段独立 POP_TOP 表达式。
- 验证: FAILED `指令数不匹配: 13 vs 10`

### Bug R18-09: for x in y[(ternary)] — for iter 是 subscript 含 ternary
- 测试文件: `tests/exhaustive/ternary/test_r18_ternary_for_iter_subscr.py`
- 源码: `for x in y[(a if c else b)]:\n    pass`
- 失败原因: for 循环的 iter 表达式是 y[(ternary)] —— subscript 下标是 ternary。
  R2 for_iter 测过 `for x in (ternary)`，R14 for_iter_list_middle 测过
  `for x in [1, (ternary), 2]`。本用例 ternary 是 subscript 下标，merge 块的
  BINARY_SUBSCR 之后才走 GET_ITER + FOR_ITER，反编译丢失 subscript 与 ternary。
- 验证: FAILED `指令数不匹配: 10 vs 8`

### Bug R18-10: del (ternary).x — del attr 直接作用在 ternary 上
- 测试文件: `tests/exhaustive/ternary/test_r18_ternary_del_attr_on_ternary.py`
- 源码: `del (a if c else b).x`
- 失败原因: DELETE_ATTR 的对象表达式是 ternary。R8 del_attr_chain 测过
  `del obj[ternary].attr`，R8 del_subscript_both 测过 `del (ternary)[ternary]`。
  本用例 ternary 直接是 DELETE_ATTR 的对象：ternary merge 块的 LOAD_ATTR x +
  DELETE_ATTR 消费链未被 _try_build_ternary_store_assign 处理 (它处理
  STORE_ATTR/STORE_SUBSCR，不处理 DELETE_ATTR)，反编译退化为破碎多段 POP_TOP。
- 验证: FAILED `指令数不匹配: 7 vs 10`

### Bug R18-11: f(*(ternary), other) — starred ternary + 位置参数
- 测试文件: `tests/exhaustive/ternary/test_r18_ternary_starred_call_with_pos_arg.py`
- 源码: `f(*(a if c else b), other)`
- 失败原因: 函数调用中 *-starred 参数是 ternary，同时还有一个普通位置参数 other。
  R8 starred_call 测过 `f(*(ternary))` (仅 starred)，R17 starred_kwarg_call
  测过 `f(*(ternary), key=val)` (starred + kwarg)。本用例 starred + 位置参数：
  CALL_FUNCTION_EX 的 LIST_EXTEND (消费 starred ternary) 与 LIST_APPEND
  (消费 other) 协调失败，反编译完全丢失 ternary 与 other 参数，退化为 `f()`。
- 验证: FAILED `指令数不匹配: 15 vs 9`

### Bug R18-12: x = (await g() if c else b) — ternary body 是 await 调用
- 测试文件: `tests/exhaustive/ternary/test_r18_ternary_body_await_method.py`
- 源码: `async def f():\n    x = (await g() if c else b)`
- 失败原因: ternary 的 true_value (body) 是 await g()。R17 await_in_cond 测过
  await 在 ternary 条件中，R14 await_attr_method 测过 await (ternary).m()。
  本用例 await 在 ternary body：true_value 块含 GET_AWAITABLE+SEND+YIELD_VALUE
  协程调度轮询，与 ternary merge 块的 STORE_FAST x 归属冲突，反编译退化为
  `x = b`。
- 验证: FAILED `嵌套code object不匹配 (指令1): 指令数不匹配: 16 vs 9`

### Bug R18-13: x = (ternary)(key=val) — ternary 作 callable 带 kwargs
- 测试文件: `tests/exhaustive/ternary/test_r18_ternary_body_call_with_kwargs.py`
- 源码: `x = (a if c else b)(key=val)`
- 失败原因: ternary 本身是函数调用 (a if c else b)(...) 的 callable，且调用
  含 keyword 参数 key=val。R15 callable_no_args 测过 `(ternary)()`，
  R15 callable_multi_args 测过 `(ternary)(x, y)` (位置参数)。本用例含 kwargs：
  merge 块的 KW_NAMES + PRECALL + CALL 消费链与 ternary 的 func 槽位归属冲突，
  反编译丢失 ternary callable 与 kwarg，退化为 `x = b`。
- 验证: FAILED `指令数不匹配: 12 vs 7`

## 共性根因分析

13 个 bug 可归为 4 类共性根因：

### 根因 A: ternary merge 块消费链与协程调度 (await/async for) 冲突 (5 个)
- R18-02, R18-03, R18-05, R18-06, R18-12
- 当 ternary 的 condition/merge/true_value 块与 GET_AWAITABLE+SEND+YIELD_VALUE
  协程调度轮询循环嵌套时，ternary 区域归约无法捕获跨块的 await 轮询指令，
  导致 await / async for / subscript+await 整体丢失。
- `_try_build_ternary_merge_consumer_expr` 的 `_consumer_extra_blocks` 机制
  (region_analyzer.py line 12471) 仅处理 `await (ternary)` / `yield from (ternary)`
  的简单形态，未覆盖「ternary 在 await 调用参数中」「await 在 ternary body 中」
  「async for iter 是 subscript 含 ternary」等复合形态。

### 根因 B: ternary merge 块消费链与 subscript/容器构造冲突 (4 个)
- R18-01, R18-07, R18-08, R18-09
- 当 ternary 的 merge 块消费链是 BUILD_SLICE / MAP_ADD / 链式 BINARY_SUBSCR /
  BINARY_SUBSCR+GET_ITER 时，`_detect_ternary_context` 仅识别 BUILD_LIST/
  BUILD_TUPLE/BUILD_SET/BUILD_MAP/DICT_UPDATE/LIST_EXTEND/SET_UPDATE + GET_ITER
  等有限模式，未覆盖 BUILD_SLICE 多段 ternary、MAP_ADD 双 ternary (key+value)、
  链式 subscript target 多 ternary、subscript+for_iter 复合。

### 根因 C: ternary merge 块消费链是 DELETE_ATTR (1 个)
- R18-10
- `_try_build_ternary_store_assign` 处理 STORE_ATTR/STORE_SUBSCR，但 DELETE_ATTR
  的消费链 (LOAD_ATTR x + DELETE_ATTR) 完全未处理，ternary 整体被丢弃。

### 根因 D: ternary 作 callable 含 kwargs + match case _ guard (3 个)
- R18-04, R18-11, R18-13
- ternary 作 callable 带 KW_NAMES (kwargs) 时，`_has_ternary_as_callable` 检测
  (region_ast_generator.py line 22632) 仅匹配 `_call_count == 1`，未识别
  KW_NAMES + PRECALL + CALL 模式。match case _ 通配符 guard 的 ternary 与
  MatchRegion 的 case_body 块归属冲突 (R9 case 1 已修复但 case _ 路径未覆盖)。

## 新建测试文件清单
1. `tests/exhaustive/ternary/test_r18_ternary_slice_three_ternary.py`
2. `tests/exhaustive/ternary/test_r18_ternary_await_call_ternary_arg.py`
3. `tests/exhaustive/ternary/test_r18_ternary_await_call_two_ternary_args.py`
4. `tests/exhaustive/ternary/test_r18_ternary_match_guard_wildcard.py`
5. `tests/exhaustive/ternary/test_r18_ternary_async_for_subscr.py`
6. `tests/exhaustive/ternary/test_r18_ternary_await_in_subscr_target.py`
7. `tests/exhaustive/ternary/test_r18_ternary_dictcomp_key_value_ternary.py`
8. `tests/exhaustive/ternary/test_r18_ternary_subscr_chain_assign.py`
9. `tests/exhaustive/ternary/test_r18_ternary_for_iter_subscr.py`
10. `tests/exhaustive/ternary/test_r18_ternary_del_attr_on_ternary.py`
11. `tests/exhaustive/ternary/test_r18_ternary_starred_call_with_pos_arg.py`
12. `tests/exhaustive/ternary/test_r18_ternary_body_await_method.py`
13. `tests/exhaustive/ternary/test_r18_ternary_body_call_with_kwargs.py`

## 验证命令
```bash
# 单独运行 R18 测试 (全部 FAILED)
timeout 60 python -m pytest tests/exhaustive/ternary/test_r18_*.py -v --tb=short

# 完整 ternary 套件 (59 failed = 46 baseline + 13 new)
timeout 280 python -m pytest tests/exhaustive/ternary/ -q --tb=no
```

## 约束遵循
- 未修改任何现有源代码 (`core/cfg/*.py`)
- 未创建根级 `_debug_*.py` 调试脚本 (调试脚本在
  `/workspace/.trae/specs/iterate-region-test-fix/rounds/ternary_region/round_18/` 下)
- 所有测试验证字节码完全匹配 (非语义等价)
- 未重复 R1-R17 已覆盖场景 (经 grep 核对 SOURCE_CODE)
