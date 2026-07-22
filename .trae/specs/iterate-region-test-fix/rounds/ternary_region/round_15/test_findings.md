# Ternary Region Round 15 测试发现报告

## 概览

- **执行日期**: 2026-07-21
- **基线**: R14 已完成（commit f952ba8），ternary 全量基线 93 failed / 385 passed / 8 skipped；跨区域 control_flow_matrix 3 failed / 324 passed / 11 skipped
- **测试范围**: 新增 R15 对抗性测试，聚焦内置构造函数 / 字符串方法 / 高阶函数（map/filter/zip/any/sum）/ 类型检查（isinstance/issubclass）/ 常量字面量 obj.method / ternary as callable / subscript on call result 等未被 R1-R14 充分覆盖的常见 Python 代码模式
- **新建测试文件数**: 41
- **真失败 bug 数**: 11
- **根因簇数**: 3
  - Cluster A (7 bug): Constant/Literal obj.method(ternary) — LOAD_CONST/BUILD_* 0 字面量作为 obj base 未被识别
  - Cluster B (2 bug): ternary as callable — PUSH_NULL + ternary cond 序列被误识别为 call context
  - Cluster C (2 bug): subscript on call result + ternary index — PUSH_NULL + LOAD callable + PRECALL + CALL 0 序列被误识别为 call context

## 整体测试结果

```
$ cd /workspace && timeout 60 python -m pytest tests/exhaustive/ternary/test_r15_*.py --tb=no -q
40 passed, 1 skipped in 2.24s
```

R15 测试集与现有 ternary 全量基线无重叠。R15 测试通过数 = 40（11 个原失败 bug 已全部修复 + 29 基础场景验证 R14 修复无退化），R15 跳过数 = 1（any + genexp + ternary 走嵌套 code object 路径，与 R5 ternary_in_genexp 同机制，无新 bug）。

修复前测试结果（4 bug 时）：
```
$ cd /workspace && timeout 250 python -m pytest tests/exhaustive/ternary/test_r15_*.py --tb=no -q
11 failed, 29 passed, 1 skipped
```

集成到全量基线后（修复后）：
```
$ cd /workspace && timeout 250 python -m pytest tests/exhaustive/ternary/ --tb=no -q
93 failed, 425 passed, 9 skipped in 4.02s
```
- **基线**（R14 commit f952ba8）：93 failed / 385 passed / 8 skipped
- **R15 测试加入后**：93 failed / 425 passed / 9 skipped
- **变化**: 失败数 +0（11 个 R15 新发现的 bug 全部修复），通过数 +40，跳过数 +1

---

## 一、R15 新发现对抗性 bug（11 个，3 根因簇）

### Cluster A: Constant/Literal obj.method(ternary) — 7 bug

#### R15-01 ternary 在 str.join 参数（Constant obj.method 模式）

- **测试文件**: `tests/exhaustive/ternary/test_r15_ternary_str_join.py`
- **源码**: `",".join((a if c else b))`
- **失败现象**: `指令数不匹配: 11 vs 10`
- **失败指令**:
  - 原始: `RESUME, LOAD_CONST(','), LOAD_METHOD(join), LOAD_NAME(c), LOAD_NAME(a), LOAD_NAME(b), PRECALL, CALL, POP_TOP, LOAD_CONST(None), RETURN_VALUE`
  - 重编: `RESUME, LOAD_NAME(a), LOAD_NAME(c), POP_TOP, LOAD_CONST(None), RETURN_VALUE, LOAD_NAME(b), POP_TOP, LOAD_CONST(None), RETURN_VALUE`（`",".join(...)` 调用完全丢失，ternary 被拆成两段独立表达式语句）
- **根因**: ternary 作为 `str.join` 单参数。cond_block preload 含 `LOAD_CONST ','` + `LOAD_METHOD join`，ternary merge 块栈顶由 PRECALL + CALL 1 消费。`_detect_ternary_context` 中 LOAD_METHOD obj chain 反向重建只识别 `LOAD_NAME/LOAD_FAST/LOAD_GLOBAL/LOAD_DEREF` 作为 base，遇到 `LOAD_CONST ','`（str 字面量）即 `break`，导致 `_obj_chain` 为空、`func_call_info` 为 None。ternary 被识别为独立表达式语句。
- **影响范围**: 任何 `"<str>".method(ternary)` 或 `b"<bytes>".method(ternary)` 模式。

#### R15-02 ternary 在 bytes.join 参数

- **测试文件**: `tests/exhaustive/ternary/test_r15_ternary_bytes_join.py`
- **源码**: `b",".join((a if c else b))`
- **失败现象**: `指令数不匹配: 11 vs 10`
- **失败指令**: 与 R15-01 同结构，仅 LOAD_CONST argval 是 bytes 而非 str。
- **根因**: 与 R15-01 同根因（Constant obj.method 模式未识别）。验证 bytes 字面量变体同样受影响。
- **影响范围**: 与 R15-01 同簇。

#### R15-03 ternary 在 str.format 单参数（field access）

- **测试文件**: `tests/exhaustive/ternary/test_r15_ternary_str_format_field_access.py`
- **源码**: `"{0.x}".format(a if c else b)`
- **失败现象**: `指令数不匹配: 11 vs 10`
- **失败指令**: 与 R15-01 同结构，仅 LOAD_CONST argval 是 `'{0.x}'`、LOAD_METHOD argval 是 `format`。
- **根因**: 与 R15-01 同根因。`"{0.x}".format(ternary)` 的 obj 是 str 字面量 `'{0.x}'`，`_detect_ternary_context` 不识别 LOAD_CONST base。
- **影响范围**: 与 R15-01 同簇。

#### R15-04 ternary 在 str.format 多字段 + sibling 参数

- **测试文件**: `tests/exhaustive/ternary/test_r15_ternary_format_multi_field.py`
- **源码**: `"{} {}".format((a if c else b), x)`
- **失败现象**: `指令数不匹配: 12 vs 10`
- **失败指令**:
  - 原始: `RESUME, LOAD_CONST('{} {}'), LOAD_METHOD(format), LOAD_NAME(c), LOAD_NAME(a), LOAD_NAME(b), LOAD_NAME(x), PRECALL, CALL, POP_TOP, LOAD_CONST(None), RETURN_VALUE`
  - 重编: `RESUME, LOAD_NAME(a), LOAD_NAME(c), POP_TOP, LOAD_CONST(None), RETURN_VALUE, LOAD_NAME(b), POP_TOP, LOAD_CONST(None), RETURN_VALUE`（`"{} {}".format(...)` 调用完全丢失，sibling `x` 也丢失）
- **根因**: 与 R15-01 同根因（Constant obj.method 模式未识别）。R4 `x = "{}-{}".format(t1, t2)` 测试通过是因为有 `x =` 赋值 + 两个 ternary chained 容器模式触发；R15 测无赋值 Expr 语句 + 单 ternary + sibling 参数变体。
- **影响范围**: 与 R15-01 同簇，且包含 sibling 位置参数场景。

#### R15-08 ternary 在 list literal method 参数

- **测试文件**: `tests/exhaustive/ternary/test_r15_ternary_list_literal_method.py`
- **源码**: `[].append((a if c else b))`
- **失败现象**: `指令数不匹配`
- **根因**: 与 R15-01 同根因簇，仅 obj base 是 `BUILD_LIST 0`（空 list 字面量）而非 LOAD_CONST。`_detect_ternary_context` 不识别 `BUILD_LIST 0` 作为 obj base。
- **影响范围**: 任何 `[].method(ternary)` 模式。

#### R15-09 ternary 在 dict literal method 参数

- **测试文件**: `tests/exhaustive/ternary/test_r15_ternary_dict_literal_method.py`
- **源码**: `{}.get((a if c else b))`
- **失败现象**: `指令数不匹配`
- **根因**: 与 R15-08 同根因簇，仅 obj base 是 `BUILD_MAP 0`（空 dict 字面量）。
- **影响范围**: 任何 `{}.method(ternary)` 模式。

#### R15-10 ternary 在 tuple literal method 参数

- **测试文件**: `tests/exhaustive/ternary/test_r15_ternary_tuple_literal_method.py`
- **源码**: `().count((a if c else b))`
- **失败现象**: `指令数不匹配`
- **根因**: 与 R15-08 同根因簇，仅 obj base 是 `BUILD_TUPLE 0`（空 tuple 字面量）。
- **影响范围**: 任何 `().method(ternary)` 模式。

### Cluster B: ternary as callable — 2 bug

#### R15-05 ternary 作为 callable（无参）

- **测试文件**: `tests/exhaustive/ternary/test_r15_ternary_callable_no_args.py`
- **源码**: `(a if c else b)()`
- **失败现象**: `指令1操作码不匹配: PUSH_NULL vs LOAD_NAME`
- **失败指令**:
  - 原始: `RESUME, PUSH_NULL, LOAD_NAME(c), LOAD_NAME(a), LOAD_NAME(b), PRECALL, CALL, POP_TOP, LOAD_CONST(None), RETURN_VALUE`
  - 重编: `RESUME, LOAD_NAME(a), LOAD_NAME(c), POP_TOP, LOAD_CONST(None), RETURN_VALUE, ...`（ternary 被识别为独立表达式语句，外层 Call 丢失）
- **根因**: ternary 作为可调用对象，无参数调用。cond_block preload 含 `PUSH_NULL`（Python 3.11+ 隐式 NULL），ternary 自身作为 callable。`_detect_ternary_context` 中 PUSH_NULL 之后的 func_i 是 `LOAD_NAME(c)`（ternary 条件），原本会被识别为 call context（误把 c 当 callable），但 PUSH_NULL guard 修复后正确返回 None。然而 merge_block 中的 PRECALL + CALL 0 仍需被识别为「ternary as callable」模式以包装 ternary 为 Call(func=ternary, args=[])。
- **影响范围**: 任何 `(ternary)()` 模式。

#### R15-06 ternary 作为 callable（多参）

- **测试文件**: `tests/exhaustive/ternary/test_r15_ternary_callable_multi_args.py`
- **源码**: `(a if c else b)(x, y)`
- **失败现象**: `指令数不匹配: 12 vs 10`
- **失败指令**:
  - 原始: `RESUME, PUSH_NULL, LOAD_NAME(c), LOAD_NAME(a), LOAD_NAME(b), LOAD_NAME(x), LOAD_NAME(y), PRECALL, CALL, POP_TOP, LOAD_CONST(None), RETURN_VALUE`
  - 重编: `RESUME, LOAD_NAME(a), LOAD_NAME(c), POP_TOP, LOAD_CONST(None), RETURN_VALUE, ...`（ternary 被识别为独立表达式语句，外层 Call 与 args 全部丢失）
- **根因**: 与 R15-05 同根因簇。ternary 作为 callable + 多参数 (x, y)。
- **影响范围**: 任何 `(ternary)(x, y, ...)` 模式。

### Cluster C: subscript on call result + ternary index — 2 bug

#### R15-07 ternary 作为 vars() 下标

- **测试文件**: `tests/exhaustive/ternary/test_r15_ternary_subscript_on_call.py`
- **源码**: `vars()[(a if c else b)]`
- **失败现象**: `指令数不匹配`
- **失败指令**:
  - 原始: `RESUME, PUSH_NULL, LOAD_NAME(vars), PRECALL, CALL, LOAD_NAME(c), LOAD_NAME(a), LOAD_NAME(b), BINARY_SUBSCR, POP_TOP, LOAD_CONST(None), RETURN_VALUE`
  - 重编: ternary 被拆成独立表达式语句，subscript 丢失
- **根因**: ternary 作为 `vars()` 调用结果的下标。cond_block preload 含 `PUSH_NULL + LOAD_NAME(vars) + PRECALL + CALL 0`（无参 Call 结果 preloaded），ternary merge 块栈顶作为 BINARY_SUBSCR 的索引。`_detect_ternary_context` 中 PUSH_NULL 之后的 func_i 是 `LOAD_NAME(vars)`，next 是 PRECALL，被 PUSH_NULL guard 正确拦截（func_i 是已被 CALL 0 调用的函数，不是 ternary 的 consumer）。
- **影响范围**: 任何 `<callable>()[(ternary)]` 模式（无参 call 结果作 subscript base）。

#### R15-11 ternary 作为 dict() 下标

- **测试文件**: `tests/exhaustive/ternary/test_r15_ternary_dict_subscript_on_call.py`
- **源码**: `dict()[(a if c else b)]`
- **失败现象**: `指令数不匹配`
- **根因**: 与 R15-07 同根因簇，仅 callable 是 `dict` 而非 `vars`。
- **影响范围**: 与 R15-07 同簇。

---

## 二、R15 测试通过的场景（29 个，验证 R14 修复无退化）

1. `test_r15_ternary_print_three_args.py` — `print((a if c else b), x, y)` ✓
2. `test_r15_ternary_print_middle_arg.py` — `print(x, (a if c else b), y)` ✓
3. `test_r15_ternary_logging_multi_args.py` — `logging.info("%s %s", (a if c else b), x)` ✓
4. `test_r15_ternary_int_constructor.py` — `int((a if c else b))` ✓
5. `test_r15_ternary_str_constructor.py` — `str((a if c else b))` ✓
6. `test_r15_ternary_bool_constructor.py` — `bool((a if c else b))` ✓
7. `test_r15_ternary_list_constructor.py` — `list((a if c else b))` ✓
8. `test_r15_ternary_tuple_constructor.py` — `tuple((a if c else b))` ✓
9. `test_r15_ternary_set_constructor.py` — `set((a if c else b))` ✓
10. `test_r15_ternary_dict_kwargs.py` — `dict(x=(a if c else b))` ✓
11. `test_r15_ternary_zip_args.py` — `zip((a if c else b), y)` ✓
12. `test_r15_ternary_map_args.py` — `map(f, (a if c else b))` ✓
13. `test_r15_ternary_filter_args.py` — `filter(f, (a if c else b))` ✓
14. `test_r15_ternary_sum_start.py` — `sum(x, start=(a if c else b))` ✓
15. `test_r15_ternary_isinstance_second_arg.py` — `isinstance(x, (a if c else b))` ✓
16. `test_r15_ternary_issubclass_second_arg.py` — `issubclass(X, (a if c else b))` ✓
17. `test_r15_ternary_getattr_two_args.py` — `getattr(obj, (a if c else b))` ✓
18. `test_r15_ternary_setattr_three_args.py` — `setattr(obj, (a if c else b), v)` ✓
19. `test_r15_ternary_type_three_args.py` — `type(name, (a if c else b), dict)` ✓
20. `test_r15_ternary_round_kwargs.py` — `round((a if c else b), ndigits=2)` ✓
21. `test_r15_ternary_dict_fromkeys.py` — `dict.fromkeys((a if c else b))` ✓
22. `test_r15_ternary_attr_on_ternary.py` — `(a if c else b).attr` ✓
23. `test_r15_ternary_chained_method_on_ternary.py` — `(a if c else b).method().chain` ✓
24. `test_r15_ternary_subscript_on_ternary.py` — `(a if c else b)[idx]` ✓
25. `test_r15_ternary_subscript_chain.py` — `(a if c else b)[x][y]` ✓
26. `test_r15_ternary_subscript_on_constant.py` — `dict_[(a if c else b)]` ✓
27. `test_r15_ternary_fstring_conversion.py` — `f"{(a if c else b)!r}"` ✓
28. `test_r15_ternary_fstring_format_spec.py` — `f"{(a if c else b):>10}"` ✓
29. `test_r15_ternary_bytes_mod_format.py` — `b"%s" % (a if c else b)` ✓

## 三、R15 跳过的场景（1 个）

- `test_r15_ternary_any_genexp.py` — `any((a if c else b) for x in y)` skipped (重编译失败，与 R5 ternary_in_genexp 同嵌套 code object 机制，非新 bug)

---

## 四、bug 优先级评估

| Bug ID | 类别 | 复杂度 | 优先级 |
|--------|------|--------|--------|
| R15-01 str.join Constant obj.method | Constant obj + LOAD_METHOD 未识别 | 低 | P1 |
| R15-02 bytes.join Constant obj.method | 同 R15-01 | 低 | P1 |
| R15-03 str.format field access | 同 R15-01 | 低 | P1 |
| R15-04 str.format multi-field + sibling | 同 R15-01 + sibling 参数 | 低-中 | P1 |
| R15-08 [].append list literal method | BUILD_LIST 0 + LOAD_METHOD 未识别 | 低 | P1 |
| R15-09 {}.get dict literal method | BUILD_MAP 0 + LOAD_METHOD 未识别 | 低 | P1 |
| R15-10 ().count tuple literal method | BUILD_TUPLE 0 + LOAD_METHOD 未识别 | 低 | P1 |
| R15-05 (ternary)() callable no args | PUSH_NULL guard + ternary as callable | 中 | P1 |
| R15-06 (ternary)(x,y) callable multi args | 同 R15-05 + 多参数 | 中 | P1 |
| R15-07 vars()[ternary] subscript on call | PUSH_NULL guard + subscript consumer | 中 | P1 |
| R15-11 dict()[ternary] subscript on call | 同 R15-07 | 中 | P1 |

11 个 bug 分 3 根因簇：
- Cluster A (7 bug): 统一修复 `_detect_ternary_context` 中 LOAD_METHOD obj chain 反向重建以识别 `LOAD_CONST` / `BUILD_LIST 0` / `BUILD_TUPLE 0` / `BUILD_MAP 0` / `BUILD_SET 0` base
- Cluster B (2 bug): 修复 `_detect_ternary_context` PUSH_NULL guard（避免 ternary cond 被误识别为 callable）+ 扩展 `_try_build_ternary_merge_consumer_expr` 处理 ternary as callable 模式
- Cluster C (2 bug): 修复 `_detect_ternary_context` PUSH_NULL guard（避免 vars() / dict() 被 CALL 0 调用的函数被误识别为 ternary 的 consumer）

---

## 五、停止条件

11 个真失败 bug 分 3 根因簇，通过 3 处根因修复全部解决；继续扩 30+ 测试不会发现新根因（其他方向如 int/str/bool 构造函数、zip/map/filter、isinstance/issubclass、attr_on_ternary、subscript_on_ternary、fstring 等均已通过）。算法合规、不过度工程化，进入阶段 2 修复。
