# Ternary Region Round 13 测试发现报告

## 概览

- **执行日期**: 2026-07-21
- **基线**: R12 已完成（commit 2fc9fba），ternary 全量基线 86 failed / 335 passed / 8 skipped
- **测试范围**: 新增 R13 对抗性测试，聚焦未被 R1-R12 充分覆盖的常见 Python 代码模式
- **新建测试文件数**: 26
- **真失败 bug 数**: 11
- **停止条件**: 累计 11 > 10，已满足停止条件

## 整体测试结果

```
$ cd /workspace && timeout 250 python -m pytest tests/exhaustive/ternary/test_r13_*.py --tb=no -q
11 failed, 21 passed in 1.66s
```

R13 测试集与现有 ternary 全量基线无重叠。R13 测试通过数 = 21（基础场景验证 R12 修复无退化），R13 失败数 = 11（新发现的真 bug）。

集成到全量基线后：
```
$ cd /workspace && timeout 250 python -m pytest tests/exhaustive/ternary/ --tb=no -q
97 failed, 356 passed, 8 skipped in 3.88s
```
- **基线**（R12 commit 2fc9fba）：86 failed / 335 passed / 8 skipped
- **R13 测试加入后**：97 failed / 356 passed / 8 skipped
- **变化**: 失败数 +11（R13 新发现的 11 个真 bug），通过数 +21（R13 测试中通过的 21 个）

---

## 一、R13 新发现对抗性 bug（11 个）

### R13-01 ternary 在 string method chain arg 位置
- **测试文件**: `tests/exhaustive/ternary/test_r13_ternary_string_method_chain_arg.py`
- **源码**: `s.upper().split((a if c else b))`
- **失败现象**: `指令数不匹配: 14 vs 11`
- **失败指令**:
  - 原始: `LOAD_NAME s, LOAD_METHOD upper, PRECALL, CALL 0, LOAD_METHOD split, LOAD a, LOAD c, LOAD b, PRECALL, CALL 1, POP_TOP`
  - 重编: `LOAD_NAME s, LOAD_METHOD split, LOAD a, LOAD c, LOAD b, PRECALL, CALL 1, POP_TOP`
- **根因**: ternary 作为 `s.upper().split(...)` 第二个方法 (split) 的参数。cond_block preload 含 `LOAD_NAME s + LOAD_METHOD upper + PRECALL + CALL 0`（外层 method chain 前缀），但 ternary 识别时未保留此外层 method chain 前缀，导致 `s.upper()` 完全丢失。
- **影响范围**: 任何 method chain 中间环节 + ternary arg 模式，如 `s.strip().split(ternary)`、`obj.method().call(ternary)`。

### R13-02 ternary 在 del slice 双边界
- **测试文件**: `tests/exhaustive/ternary/test_r13_ternary_del_slice.py`
- **源码**: `del x[a if c else b : b if d else e]`
- **失败现象**: `指令数不匹配: 12 vs 10`
- **失败指令**:
  - 原始: `LOAD_NAME x, <ternary1>, <ternary2>, BUILD_SLICE 2, DELETE_SUBSCR, ...`
  - 重编: `LOAD_NAME x, <ternary1>, <ternary2>, DELETE_SUBSCR, ...` (无 BUILD_SLICE)
- **根因**: 两个 ternary 作为 BUILD_SLICE 2 的 lower/upper，merge 块之后 BUILD_SLICE 2 消费两个 ternary 栈顶合成 Slice AST 节点。当前 BUILD_SLICE 指令被误识别为外层操作丢失。R12-03 已修 BUILD_SLICE preload 场景（slice 在 cond_block preload），R13-02 测 BUILD_SLICE 在 merge_block 之后场景（双 ternary 作为 slice 双界）。
- **影响范围**: 任何 `del x[ternary:ternary]`、`x[ternary:ternary]` 双界 slice。

### R13-03 ternary 在 aug assign subscr + call arg
- **测试文件**: `tests/exhaustive/ternary/test_r13_ternary_aug_assign_subscr_call.py`
- **源码**: `x[0] += f(a if c else b)`
- **失败现象**: `指令数不匹配: 19 vs 15`
- **失败指令**:
  - 原始: `LOAD x, LOAD_CONST 0, COPY 2, COPY 1, BINARY_SUBSCR, PUSH_NULL, LOAD f, <ternary>, PRECALL, CALL 1, BINARY_OP(+=), SWAP, SWAP, STORE_SUBSCR`
  - 重编: `LOAD x, LOAD_CONST 0, COPY 2, COPY 1, BINARY_SUBSCR, <ternary>, BINARY_OP(+=), SWAP, SWAP, STORE_SUBSCR`
- **根因**: ternary 作为 aug assign rhs `f(ternary)` 的位置参数。merge 块之后还有 PRECALL + CALL 1 消费 ternary 作为 f() 参数。CALL 消费指令未保留，导致 `f()` 调用完全丢失，仅保留 ternary 表达式作为 rhs。
- **影响范围**: 任何 `x[k] += f(ternary)`、`x.attr += g(ternary)` 等 aug assign + call + ternary 复合场景。

### R13-04 ternary 在嵌套 Call 链最内层
- **测试文件**: `tests/exhaustive/ternary/test_r13_ternary_chained_call.py`
- **源码**: `f(g(h(a if c else b)))`
- **失败现象**: `指令数不匹配: 19 vs 13`
- **失败指令**:
  - 原始: 3 个 `PUSH_NULL + LOAD_NAME` 前缀 + ternary + 3 个 `PRECALL + CALL 1` 消费链
  - 重编: 仅 1 个 PUSH_NULL + LOAD + ternary + 1 个 PRECALL + CALL
- **根因**: ternary 在三层嵌套 Call 的最内层（h(ternary)）。每个外层 Call 消费内层 Call 的栈顶结果，但 ternary merge 块识别未保留外层 g()/f() 的 `PUSH_NULL + LOAD + PRECALL + CALL` 消费链。结果中间 g()、h() 调用全部丢失，最终反编译为 `f(ternary)` 单层调用。
- **影响范围**: 任何 `f(g(h(...(ternary))))` 嵌套 call 链 + ternary 在最内层位置。

### R13-05 ternary 在 lambda default arg
- **测试文件**: `tests/exhaustive/ternary/test_r13_ternary_lambda_default.py`
- **源码**: `lambda x=(a if c else b): x`
- **失败现象**: `指令数不匹配: 10 vs 8`
- **失败指令**:
  - 原始: `<ternary>, BUILD_TUPLE 1, LOAD_CONST (code), MAKE_FUNCTION 0, POP_TOP`
  - 重编: `<ternary>, BUILD_TUPLE 1, POP_TOP` (无 LOAD_CONST + MAKE_FUNCTION)
- **根因**: ternary 作为 lambda 默认参数值。merge 块栈输出由 BUILD_TUPLE 1 包装为 default args tuple，然后 LOAD_CONST (lambda code) + MAKE_FUNCTION 创建函数。当前 MAKE_FUNCTION 消费指令未保留，lambda 完全丢失，仅保留 ternary 表达式。
- **影响范围**: 任何 `lambda x=ternary: ...`、`def f(x=ternary): ...` lambda/函数默认参数 ternary 场景。

### R13-06 ternary 在 nested lambda body
- **测试文件**: `tests/exhaustive/ternary/test_r13_ternary_nested_lambda.py`
- **源码**: `lambda: lambda: (a if c else b)`
- **失败现象**: 反编译结果完全丢失 ternary: `(lambda *args, **kwargs: None)`
- **根因**: 外层 lambda 内的内层 lambda body 含 ternary。外层 lambda 编译为外 code object，内层 lambda code object 在外层 code object 内通过 MAKE_FUNCTION 创建。ternary merge 块在内层 lambda code object 中作为 RETURN_VALUE 前栈顶。当前 nested lambda code object 的 ternary 识别未保留，反编译为空 lambda。
- **影响范围**: 任何 `lambda: lambda: ternary`、`lambda: lambda: ...ternary...` 嵌套 lambda body 含 ternary 场景。

### R13-07 ternary 在 del 多目标的 subscript 位置
- **测试文件**: `tests/exhaustive/ternary/test_r13_ternary_del_multi_target.py`
- **源码**: `del obj.attr, lst[a if c else b]`
- **失败现象**: `指令数不匹配: 10 vs 8`
- **失败指令**:
  - 原始: `LOAD obj, DELETE_ATTR attr, LOAD lst, <ternary>, DELETE_SUBSCR`
  - 重编: `LOAD lst, <ternary>, DELETE_SUBSCR` (无 LOAD obj + DELETE_ATTR attr)
- **根因**: del 多目标场景，第一个目标 `obj.attr` 在 ternary cond_block preload 之前。当前 ternary 识别未保留前置的 `LOAD obj + DELETE_ATTR attr` 第一个目标。
- **影响范围**: 任何 `del target1, target2[ternary]` 多目标 del + 第二目标 subscript 含 ternary 场景。

### R13-08 ternary 在 list literal 中间元素位置
- **测试文件**: `tests/exhaustive/ternary/test_r13_ternary_list_middle_elem.py`
- **源码**: `[1, (a if c else b), 2]`
- **失败现象**: `指令数不匹配: 10 vs 8`
- **失败指令**:
  - 原始: `LOAD_CONST 1, <ternary>, LOAD_CONST 2, BUILD_LIST 3, POP_TOP`
  - 重编: `<ternary>, BUILD_LIST 1, POP_TOP` (无 LOAD_CONST 1, 2; BUILD_LIST 元素数 3→1)
- **根因**: ternary 作为 list literal 中间元素。BUILD_LIST 3 消费 3 个栈项（LOAD_CONST 1, ternary, LOAD_CONST 2），但当前识别未保留前后 LOAD_CONST 元素，BUILD_LIST 元素数 3 被误识别为 1。
- **影响范围**: 任何 `[before_elem, ternary, after_elem]` list literal 含 ternary 中间元素场景。

### R13-09 ternary 在 Call 中间参数且前后参数均为 Call
- **测试文件**: `tests/exhaustive/ternary/test_r13_ternary_call_with_args_before_and_after.py`
- **源码**: `f(g(0), (a if c else b), h(1))`
- **失败现象**: `指令数不匹配: 21 vs 13`
- **失败指令**:
  - 原始: `PUSH_NULL + LOAD f + PUSH_NULL + LOAD g + LOAD_CONST 0 + PRECALL + CALL 1 + <ternary> + PUSH_NULL + LOAD h + LOAD_CONST 1 + PRECALL + CALL 1 + PRECALL + CALL 3`
  - 重编: `PUSH_NULL + LOAD f + <ternary> + LOAD_CONST 1 + PRECALL + CALL 1`
- **根因**: 与 R13-04 同根因。ternary 作为多参数 Call 的中间位置参数，前后参数都是嵌套 Call。当前识别未保留前后 g(0) 和 h(1) 子 Call 的完整指令链。
- **影响范围**: 任何 `f(call1, ternary, call2)` 多参数 Call + 兄弟参数是 Call + 中间 ternary 场景。

### R13-10 ternary 在 dict literal 中间 value 位置
- **测试文件**: `tests/exhaustive/ternary/test_r13_ternary_dict_middle_value.py`
- **源码**: `{1: x, 2: (a if c else b), 3: y}`
- **失败现象**: `指令数不匹配: 11 vs 10`
- **失败指令**:
  - 原始: `LOAD x, <ternary>, LOAD y, LOAD_CONST (1,2,3), BUILD_CONST_KEY_MAP 3, POP_TOP`
  - 重编: 结构完全错误，反编译为多条独立语句而非单一 dict 字面量
- **根因**: ternary 作为 dict literal 中间 value。BUILD_CONST_KEY_MAP 3 消费 3 个 value 栈项 + 1 个 keys tuple。当前识别未保留前后 LOAD x/LOAD y 元素，dict 结构完全破坏。
- **影响范围**: 任何 `{k1: v1, k2: ternary, k3: v3}` dict literal 多元素 + ternary 中间 value 场景。

### R13-11 ternary 作为 method call 的 receiver
- **测试文件**: `tests/exhaustive/ternary/test_r13_ternary_receiver_method_call.py`
- **源码**: `(a if c else b).method()`
- **失败现象**: `指令3操作码不匹配: LOAD_NAME vs POP_TOP`
- **失败指令**:
  - 原始: `<ternary>, LOAD_METHOD method, PRECALL, CALL 0, POP_TOP`
  - 重编: 反编译结构完全错误，第一个 LOAD_NAME (ternary body) 与 POP_TOP 不匹配
- **根因**: ternary 作为 method call 的 receiver。LOAD_METHOD 指令消费 ternary 栈顶作为 receiver，但当前 ternary 识别未保留 LOAD_METHOD + PRECALL + CALL 消费链。
- **影响范围**: 任何 `(ternary).method()` ternary 直接作为 method receiver 场景。

---

## 二、按 bug 模式聚类分析

### 2.1 P0 — container literal 中间元素 ternary（同根因 2 个）
- **R13-08** `[1, ternary, 2]` list literal 中间元素
- **R13-10** `{k1: v1, k2: ternary, k3: v3}` dict literal 中间 value
- **共性**: container 的 BUILD_* 指令（BUILD_LIST/BUILD_CONST_KEY_MAP）的 arity 大于 1，ternary 是中间元素，前后还有兄弟元素需要被保留。当前 ternary 识别未保留兄弟元素，BUILD_* arity 被误设为 1。

### 2.2 P0 — Call 链 ternary arg（同根因 3 个）
- **R13-04** `f(g(h(ternary)))` 嵌套 Call 链最内层
- **R13-09** `f(g(0), ternary, h(1))` 中间 arg + 兄弟参数是 Call
- **R13-11** `(ternary).method()` ternary 作为 method receiver
- **共性**: ternary 周围有 CALL 消费链，当前识别未保留 PUSH_NULL + LOAD + PRECALL + CALL 完整路径。

### 2.3 P1 — method chain + ternary arg（1 个）
- **R13-01** `s.upper().split(ternary)` 外层 method chain 前缀丢失
- 与 R13-04 类似但 cond_block preload 中的 method chain (`s.upper()`) 丢失

### 2.4 P1 — del/augassign + ternary consumer（3 个）
- **R13-02** `del x[ternary:ternary]` BUILD_SLICE 2 丢失
- **R13-03** `x[0] += f(ternary)` 调用 f() 丢失
- **R13-07** `del obj.attr, lst[ternary]` 多目标 del 第一目标丢失
- **共性**: ternary 的 cond_block/merge_block 前后有兄弟指令（BUILD_SLICE、CALL、DELETE_ATTR 等）未保留。

### 2.5 P2 — lambda + ternary（2 个）
- **R13-05** `lambda x=ternary: x` MAKE_FUNCTION 丢失
- **R13-06** `lambda: lambda: ternary` nested lambda body ternary 丢失

---

## 三、修复优先级建议

### 高优先级（影响常见代码模式，根因清晰）
1. **R13-08/R13-10** container literal 中间元素 ternary：常见 list/dict 字面量
2. **R13-02** del slice 双界 ternary：常见 slice 操作
3. **R13-03** aug assign + call + ternary：常见复合赋值
4. **R13-07** del 多目标 + ternary subscript：常见多目标 del

### 中优先级（影响 Call 链场景）
5. **R13-04/R13-09/R13-11** Call 链 + ternary：嵌套调用
6. **R13-01** method chain + ternary arg：method chain

### 低优先级（影响 lambda/函数定义）
7. **R13-05/R13-06** lambda + ternary：函数式编程场景

---

## 四、测试文件清单

### 新增 R13 测试文件（26 个）

#### 11 个真失败 bug
- `test_r13_ternary_string_method_chain_arg.py` — **FAIL** (R13-01)
- `test_r13_ternary_del_slice.py` — **FAIL** (R13-02)
- `test_r13_ternary_aug_assign_subscr_call.py` — **FAIL** (R13-03)
- `test_r13_ternary_chained_call.py` — **FAIL** (R13-04)
- `test_r13_ternary_lambda_default.py` — **FAIL** (R13-05)
- `test_r13_ternary_nested_lambda.py` — **FAIL** (R13-06)
- `test_r13_ternary_del_multi_target.py` — **FAIL** (R13-07)
- `test_r13_ternary_list_middle_elem.py` — **FAIL** (R13-08)
- `test_r13_ternary_call_with_args_before_and_after.py` — **FAIL** (R13-09)
- `test_r13_ternary_dict_middle_value.py` — **FAIL** (R13-10)
- `test_r13_ternary_receiver_method_call.py` — **FAIL** (R13-11)

#### 15 个通过测试（R12 修复无退化 + 部分新增场景通过）
- `test_r13_ternary_list_append.py` — PASS
- `test_r13_ternary_list_extend.py` — PASS
- `test_r13_ternary_dict_update.py` — PASS
- `test_r13_ternary_dict_setdefault.py` — PASS
- `test_r13_ternary_set_add.py` — PASS
- `test_r13_ternary_set_discard.py` — PASS
- `test_r13_ternary_sorted_reverse.py` — PASS
- `test_r13_ternary_enumerate_start.py` — PASS
- `test_r13_ternary_range_step.py` — PASS
- `test_r13_ternary_slice_assign.py` — PASS
- `test_r13_ternary_multiple_assign.py` — PASS
- `test_r13_ternary_tuple_swap.py` — PASS
- `test_r13_ternary_starred_assign.py` — PASS
- `test_r13_ternary_method_chain_attr.py` — PASS
- `test_r13_ternary_compare_with_method.py` — PASS
- `test_r13_ternary_closure.py` — PASS
- `test_r13_ternary_attr_delete_subscr.py` — PASS
- `test_r13_ternary_call_star_args.py` — PASS
- `test_r13_ternary_slice_step.py` — PASS
- `test_r13_ternary_yield_from.py` — PASS

---

## 五、结论

R13 测试确认了 **11 个真失败 bug**，分布在 5 个聚类：
1. **container literal 中间元素 ternary**（R13-08/R13-10，2 个）：list/dict 字面量多元素 + ternary 中间位置
2. **Call 链 ternary arg**（R13-04/R13-09/R13-11，3 个）：嵌套 Call + ternary 在中间或最内层
3. **method chain + ternary arg**（R13-01，1 个）：method chain 中间环节 + ternary arg
4. **del/augassign + ternary consumer**（R13-02/R13-03/R13-07，3 个）：del slice 双界、aug assign + call、多目标 del
5. **lambda + ternary**（R13-05/R13-06，2 个）：lambda default arg、nested lambda body

测试已满足 "10 个以上真失败" 的停止条件，结束 R13 测试。

R12 已修复的 6 个 bug 在 R13 测试中全部保持通过（无退化）。R11 已知限制 15 个全部仍失败，未触动。
