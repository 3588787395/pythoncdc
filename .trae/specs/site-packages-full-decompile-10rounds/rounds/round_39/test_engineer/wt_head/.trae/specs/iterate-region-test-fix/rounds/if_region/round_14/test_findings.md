# IF 区域 Round 14 测试发现报告

## 概述

- **测试文件数**: 15 个（`tests/exhaustive/if_region/test_adv14_*.py`）
- **失败测试数**: 11 个
- **通过测试数**: 4 个
- **探索方向**: 深层 walrus 模式、复杂 slicing、复杂容器字面量、复杂 boolop 比较、三元作切片/属性/下标操作数
- **运行命令**: `cd /workspace && python -m pytest tests/exhaustive/if_region/test_adv14_*.py --tb=short -q`

## 失败统计

```
11 failed, 4 passed, 1 warning in 1.39s
```

## 通过的测试（4 个，作为对照基线）

| 测试文件 | 源码 | 说明 |
|---------|------|------|
| test_adv14_walrus_call_attr.py | `if (x := f(a, b)).field > 0: pass` | walrus 绑定 call 结果取属性 |
| test_adv14_multidim_tuple_slice.py | `if d[a:b, c:d] > 0: pass` | 多维切片（tuple key） |
| test_adv14_nested_not_boolop.py | `if not (a or b) and not (c or d): pass` | 嵌套 not boolop |
| test_adv14_fstring_conversion_compare.py | `if f"{a!r}" == "x": pass` | f-string conversion |

---

## 失败测试详情

### 类别 A：boolop 结果作比较操作数（2 个错误）

反编译器在 boolop（and/or）结果作为 `COMPARE_OP` 操作数时，无法正确还原比较表达式，导致 `==` 右侧操作数或整个比较被丢弃。

---

#### 错误 1: test_adv14_boolop_result_compare

- **源码**:
  ```python
  if (a and b) == (c and d):
      pass
  ```
- **反编译结果**:
  ```python
  if (a and c):
      pass
  ```
- **现象**: 完全丢失了 `b`、`d` 两个操作数，且 `==` 比较运算符被丢弃，两个独立的 `and` 被错误合并为一个。整个 `if` 条件的语义被彻底破坏。
- **指令数对比**: 原始 12 条 vs 重编 9 条
  - 原始: `['RESUME', 'LOAD_NAME', 'JUMP_IF_FALSE_OR_POP', 'LOAD_NAME', 'LOAD_NAME', 'JUMP_IF_FALSE_OR_POP', 'LOAD_NAME', 'COMPARE_OP', 'LOAD_CONST', 'RETURN_VALUE', 'LOAD_CONST', 'RETURN_VALUE']`
  - 重编: `['RESUME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_CONST', 'RETURN_VALUE', 'LOAD_CONST', 'RETURN_VALUE', 'LOAD_CONST', 'RETURN_VALUE']`
- **根因分析**: boolop 的 `JUMP_IF_FALSE_OR_POP` 短路跳转结构在条件归约中被误判。反编译器将两个 `and` 的 cond_block 链合并，丢弃了 `COMPARE_OP ==` 及其右侧的 `and` 表达式。boolop 结果作为 `COMPARE_OP` 操作数的归约逻辑缺失，无法将 `JUMP_IF_FALSE_OR_POP` 的结果正确包装为带括号的子表达式后再参与 `COMPARE_OP`。

---

#### 错误 2: test_adv14_boolop_single_compare

- **源码**:
  ```python
  if (a or b) == c:
      pass
  ```
- **反编译结果**:
  ```python
  if (a or b):
      pass
  ```
- **现象**: `== c` 比较部分被完全丢弃，boolop 结果直接作为 `if` 条件，而非参与 `==` 比较。
- **指令数对比**: 原始 10 条 vs 重编 7 条
  - 原始: `['RESUME', 'LOAD_NAME', 'JUMP_IF_TRUE_OR_POP', 'LOAD_NAME', 'LOAD_NAME', 'COMPARE_OP', 'LOAD_CONST', 'RETURN_VALUE', 'LOAD_CONST', 'RETURN_VALUE']`
  - 重编: `['RESUME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_CONST', 'RETURN_VALUE', 'LOAD_CONST', 'RETURN_VALUE']`
- **根因分析**: `JUMP_IF_TRUE_OR_POP` 的跳转目标在条件归约时被识别为 `if` 条件的判断点，导致 `LOAD_NAME c` 与 `COMPARE_OP ==` 被当作 `if` 体外语句丢弃。反编译器未识别 boolop 结果需作为 `COMPARE_OP` 左操作数的情况，无法在 boolop merge_block 后继续归约 `COMPARE_OP`。

---

### 类别 B：三元作容器字面量元素（3 个错误）

当三元表达式作为 `tuple`/`list`/`set` 字面量的元素时，反编译器只保留了三元元素，丢失了字面量中的其他元素以及整个 `if` 语句结构。

---

#### 错误 3: test_adv14_ternary_in_tuple_literal

- **源码**:
  ```python
  if (a if c else b, d):
      pass
  ```
- **反编译结果**:
  ```python
  (a if c else b,)
  ```
- **现象**: 丢失了元素 `d`，且整个 `if` 语句被丢弃，反编译结果只是一个表达式语句（单元素 tuple）。三元 merge_block 的结果被单独提取，`BUILD_TUPLE 2` 的第二个操作数 `d` 丢失。
- **指令数对比**: 原始 10 条 vs 重编 8 条
  - 原始: `['RESUME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'BUILD_TUPLE', 'LOAD_CONST', 'RETURN_VALUE', 'LOAD_CONST', 'RETURN_VALUE']`
  - 重编: `['RESUME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'BUILD_TUPLE', 'POP_TOP', 'LOAD_CONST', 'RETURN_VALUE']`
- **根因分析**: 三元 TernaryRegion 的检测与归约在 `BUILD_TUPLE` 上下文中出错。反编译器将三元结果从 `BUILD_TUPLE` 栈中单独提取为顶层表达式，导致后续的 `BUILD_TUPLE`、`POP_JUMP_IF_FALSE`（即 `if` 条件判断）均被丢弃。三元作为容器字面量元素的栈位置归约逻辑缺失。

---

#### 错误 4: test_adv14_ternary_list_elem

- **源码**:
  ```python
  if [a if c else b, d]:
      pass
  ```
- **反编译结果**:
  ```python
  [a if c else b]
  ```
- **现象**: 与错误 3 同构。丢失了元素 `d`，`if` 语句被丢弃，只剩一个表达式语句（单元素 list）。
- **指令数对比**: 原始 10 条 vs 重编 8 条
  - 原始: `['RESUME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'BUILD_LIST', 'LOAD_CONST', 'RETURN_VALUE', 'LOAD_CONST', 'RETURN_VALUE']`
  - 重编: `['RESUME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'BUILD_LIST', 'POP_TOP', 'LOAD_CONST', 'RETURN_VALUE']`
- **根因分析**: 与错误 3 同根因。`BUILD_LIST` 上下文中的三元元素归约错误，三元结果被提升为顶层表达式，破坏了 list 字面量的完整性与 `if` 结构。

---

#### 错误 5: test_adv14_ternary_in_set_literal

- **源码**:
  ```python
  if {a if c else b, d}:
      pass
  ```
- **反编译结果**:
  ```python
  {a if c else b}
  ```
- **现象**: 与错误 3、4 同构。丢失了元素 `d`，`if` 语句被丢弃，只剩一个表达式语句（单元素 set）。
- **指令数对比**: 原始 10 条 vs 重编 8 条
  - 原始: `['RESUME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'BUILD_SET', 'LOAD_CONST', 'RETURN_VALUE', 'LOAD_CONST', 'RETURN_VALUE']`
  - 重编: `['RESUME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'BUILD_SET', 'POP_TOP', 'LOAD_CONST', 'RETURN_VALUE']`
- **根因分析**: 与错误 3、4 同根因。`BUILD_SET` 上下文中的三元元素归约错误。此问题影响所有容器字面量（tuple/list/set）中包含三元元素的情况，是一个系统性缺陷。

---

### 类别 C：walrus 绑定三元后接操作（4 个错误，同一根因）

当 `(x := a if c else b)` 绑定三元结果后，其后接属性访问/下标/方法调用/二元运算时，反编译器将 walrus 提取为独立的赋值语句，丢弃了后续的所有操作及整个 `if` 语句。

---

#### 错误 6: test_adv14_walrus_ternary_attr

- **源码**:
  ```python
  if (x := a if c else b).field > 0:
      pass
  ```
- **反编译结果**:
  ```python
  x = (a if c else b)
  ```
- **现象**: walrus 绑定的三元被提升为独立赋值语句，`.field > 0` 与整个 `if` 结构被丢弃。
- **指令数对比**: 原始 13 条 vs 重编 7 条
  - 原始: `['RESUME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'COPY', 'STORE_NAME', 'LOAD_ATTR', 'LOAD_CONST', 'COMPARE_OP', 'LOAD_CONST', 'RETURN_VALUE', 'LOAD_CONST', 'RETURN_VALUE']`
  - 重编: `['RESUME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'STORE_NAME', 'LOAD_CONST', 'RETURN_VALUE']`
- **根因分析**: walrus 的 `COPY`/`STORE_NAME` 在三元 merge_block 之后，反编译器检测到 `STORE_NAME x` 后将其归约为独立赋值语句，但未识别栈上仍保留的 `COPY` 副本需继续参与 `LOAD_ATTR`/`COMPARE_OP`。三元 + walrus 的组合导致 merge_block 的归约终点被错误设定为 `STORE_NAME`，后续 `LOAD_ATTR field`、`COMPARE_OP >`、`POP_JUMP_IF_FALSE` 全部丢失。

---

#### 错误 7: test_adv14_walrus_ternary_subscr

- **源码**:
  ```python
  if (x := a if c else b)[0] > 0:
      pass
  ```
- **反编译结果**:
  ```python
  x = (a if c else b)
  ```
- **现象**: 与错误 6 同构。walrus + 三元后接 `BINARY_SUBSCR` 被丢弃。
- **指令数对比**: 原始 14 条 vs 重编 7 条
  - 原始: `['RESUME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'COPY', 'STORE_NAME', 'LOAD_CONST', 'BINARY_SUBSCR', 'LOAD_CONST', 'COMPARE_OP', 'LOAD_CONST', 'RETURN_VALUE', 'LOAD_CONST', 'RETURN_VALUE']`
  - 重编: `['RESUME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'STORE_NAME', 'LOAD_CONST', 'RETURN_VALUE']`
- **根因分析**: 与错误 6 同根因。`BINARY_SUBSCR` 操作数（`LOAD_CONST 0`、`BINARY_SUBSCR`、`COMPARE_OP`）在 walrus `STORE_NAME` 之后被全部丢弃。

---

#### 错误 8: test_adv14_walrus_ternary_method

- **源码**:
  ```python
  if (x := a if c else b).method() > 0:
      pass
  ```
- **反编译结果**:
  ```python
  x = (a if c else b)
  ```
- **现象**: 与错误 6 同构。walrus + 三元后接方法调用 `LOAD_METHOD`/`CALL` 被丢弃。
- **指令数对比**: 原始 15 条 vs 重编 7 条
  - 原始: `['RESUME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'COPY', 'STORE_NAME', 'LOAD_METHOD', 'PRECALL', 'CALL', 'LOAD_CONST', 'COMPARE_OP', 'LOAD_CONST', 'RETURN_VALUE', 'LOAD_CONST', 'RETURN_VALUE']`
  - 重编: `['RESUME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'STORE_NAME', 'LOAD_CONST', 'RETURN_VALUE']`
- **根因分析**: 与错误 6 同根因。`LOAD_METHOD`/`PRECALL`/`CALL`/`COMPARE_OP` 在 walrus `STORE_NAME` 之后被全部丢弃。

---

#### 错误 9: test_adv14_walrus_ternary_binary_op

- **源码**:
  ```python
  if (x := a if c else b) + 1 > 0:
      pass
  ```
- **反编译结果**:
  ```python
  x = (a if c else b)
  ```
- **现象**: 与错误 6 同构。walrus + 三元后接 `BINARY_OP` 被丢弃。
- **指令数对比**: 原始 14 条 vs 重编 7 条
  - 原始: `['RESUME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'COPY', 'STORE_NAME', 'LOAD_CONST', 'BINARY_OP', 'LOAD_CONST', 'COMPARE_OP', 'LOAD_CONST', 'RETURN_VALUE', 'LOAD_CONST', 'RETURN_VALUE']`
  - 重编: `['RESUME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'STORE_NAME', 'LOAD_CONST', 'RETURN_VALUE']`
- **根因分析**: 与错误 6 同根因。`BINARY_OP`/`COMPARE_OP` 在 walrus `STORE_NAME` 之后被全部丢弃。

> **类别 C 总结**: 这是一个系统性缺陷——walrus 绑定三元表达式后，栈上 `COPY` 保留的副本需继续参与后续操作（属性/下标/方法/二元运算），但反编译器在三元的 merge_block 归约时，将 `STORE_NAME` 视为表达式终点，丢弃了 walrus 副本上的所有后续运算。4 个测试覆盖了 `LOAD_ATTR`、`BINARY_SUBSCR`、`LOAD_METHOD/CALL`、`BINARY_OP` 四种后续操作形式，全部失败。

---

### 类别 D：三元作切片操作数（2 个错误）

三元表达式作为切片的 base 或 step 时，反编译器无法正确合并。

---

#### 错误 10: test_adv14_ternary_slice_operand

- **源码**:
  ```python
  if (a if c else b)[0:5] > 0:
      pass
  ```
- **反编译结果**:
  ```python
  if (0[5] > 0):
      pass
  ```
- **现象**: 三元表达式 `(a if c else b)` 被完全丢弃，切片的起始值 `0` 被误当作切片的 base，导致 `0[5]` 这种语法上合法但语义错误的代码。还触发 `SyntaxWarning: 'int' object is not subscriptable`。
- **指令数对比**: 原始 14 条 vs 重编 10 条
  - 原始: `['RESUME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_CONST', 'LOAD_CONST', 'BUILD_SLICE', 'BINARY_SUBSCR', 'LOAD_CONST', 'COMPARE_OP', 'LOAD_CONST', 'RETURN_VALUE', 'LOAD_CONST', 'RETURN_VALUE']`
  - 重编: `['RESUME', 'LOAD_CONST', 'LOAD_CONST', 'BINARY_SUBSCR', 'LOAD_CONST', 'COMPARE_OP', 'LOAD_CONST', 'RETURN_VALUE', 'LOAD_CONST', 'RETURN_VALUE']`
- **根因分析**: 三元 merge_block 的结果作为 `BINARY_SUBSCR` 的 base（栈底），反编译器在归约 `BUILD_SLICE`/`BINARY_SUBSCR` 时，未能将三元结果保留在栈底，而是用切片的起始常量 `0` 替代了三元结果作为 base。`BUILD_SLICE` 的栈归约与三元 merge_block 的交互存在缺陷——三元的 cond/merge 跳转破坏了 `BUILD_SLICE` 所需的连续栈布局。

---

#### 错误 11: test_adv14_ternary_slice_step

- **源码**:
  ```python
  if a[1:10:(b if c else 2)] > 0:
      pass
  ```
- **反编译结果**:
  ```python
  (b if c else 2)
  ```
- **现象**: 整个切片 `a[1:10:...]` 与 `> 0` 比较及 `if` 结构全部丢失，只剩三元表达式作为顶层表达式语句。
- **指令数对比**: 原始 15 条 vs 重编 10 条
  - 原始: `['RESUME', 'LOAD_NAME', 'LOAD_CONST', 'LOAD_CONST', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_CONST', 'BUILD_SLICE', 'BINARY_SUBSCR', 'LOAD_CONST', 'COMPARE_OP', 'LOAD_CONST', 'RETURN_VALUE', 'LOAD_CONST', 'RETURN_VALUE']`
  - 重编: `['RESUME', 'LOAD_NAME', 'LOAD_NAME', 'POP_TOP', 'LOAD_CONST', 'RETURN_VALUE', 'LOAD_CONST', 'POP_TOP', 'LOAD_CONST', 'RETURN_VALUE']`
- **根因分析**: 三元作为 `BUILD_SLICE 3` 的 step 参数（栈顶），反编译器将三元结果从 `BUILD_SLICE` 栈中单独提取为顶层表达式，导致 `BUILD_SLICE`、`BINARY_SUBSCR`、`COMPARE_OP`、`POP_JUMP_IF_FALSE` 全部丢失。与类别 B（三元作容器字面量元素）同构——三元作为 `BUILD_*` 指令的操作数时，均被错误地提升为独立表达式。

---

## 根因归类总结

| 根因类别 | 影响错误数 | 错误编号 | 核心问题 |
|---------|-----------|---------|---------|
| A. boolop 结果作 `COMPARE_OP` 操作数 | 2 | 1, 2 | `JUMP_IF_*_OR_POP` 短路跳转被误判为 `if` 条件判断点，`COMPARE_OP` 及其操作数丢失 |
| B. 三元作 `BUILD_*` 容器字面量元素 | 3 | 3, 4, 5 | 三元结果从 `BUILD_TUPLE/LIST/SET` 栈中被单独提取为顶层表达式，破坏容器完整性与 `if` 结构 |
| C. walrus 绑定三元后接操作 | 4 | 6, 7, 8, 9 | walrus `COPY`/`STORE_NAME` 在三元 merge_block 后被视为表达式终点，栈上副本的后续运算（attr/subscr/method/binop）全部丢失 |
| D. 三元作切片 `BUILD_SLICE` 操作数 | 2 | 10, 11 | 三元结果作 `BUILD_SLICE` 的 base 或 step 时被丢弃或单独提取，切片与比较结构被破坏 |

**合计**: 11 个错误，4 个根因类别。

## 建议修复方向

1. **类别 A**: 在条件归约中识别 `JUMP_IF_FALSE_OR_POP`/`JUMP_IF_TRUE_OR_POP` 后紧跟 `COMPARE_OP` 的模式，将 boolop 结果包装为带括号的子表达式后再作为 `COMPARE_OP` 操作数。
2. **类别 B/D**: 统一处理三元作为 `BUILD_TUPLE`/`BUILD_LIST`/`BUILD_SET`/`BUILD_SLICE`/`BUILD_MAP` 操作数的情况——三元 merge_block 的结果应保留在 `BUILD_*` 的栈位置，不应提升为顶层表达式。这可能与三元的 cond/merge 跳转破坏 `BUILD_*` 连续栈布局有关。
3. **类别 C**: 在三元 merge_block 归约时，检测 walrus 的 `COPY`/`STORE_NAME` 模式，识别 `STORE_NAME` 后栈上仍有 `COPY` 副本需继续参与后续运算（`LOAD_ATTR`/`BINARY_SUBSCR`/`LOAD_METHOD`/`BINARY_OP`），不应将 `STORE_NAME` 视为表达式终点。

## 测试文件清单（15 个）

### 失败测试（11 个）
1. `tests/exhaustive/if_region/test_adv14_boolop_result_compare.py`
2. `tests/exhaustive/if_region/test_adv14_boolop_single_compare.py`
3. `tests/exhaustive/if_region/test_adv14_ternary_in_tuple_literal.py`
4. `tests/exhaustive/if_region/test_adv14_ternary_list_elem.py`
5. `tests/exhaustive/if_region/test_adv14_ternary_in_set_literal.py`
6. `tests/exhaustive/if_region/test_adv14_walrus_ternary_attr.py`
7. `tests/exhaustive/if_region/test_adv14_walrus_ternary_subscr.py`
8. `tests/exhaustive/if_region/test_adv14_walrus_ternary_method.py`
9. `tests/exhaustive/if_region/test_adv14_walrus_ternary_binary_op.py`
10. `tests/exhaustive/if_region/test_adv14_ternary_slice_operand.py`
11. `tests/exhaustive/if_region/test_adv14_ternary_slice_step.py`

### 通过测试（4 个，对照基线）
12. `tests/exhaustive/if_region/test_adv14_walrus_call_attr.py` — walrus 绑定 call 结果取属性
13. `tests/exhaustive/if_region/test_adv14_multidim_tuple_slice.py` — 多维切片
14. `tests/exhaustive/if_region/test_adv14_nested_not_boolop.py` — 嵌套 not boolop
15. `tests/exhaustive/if_region/test_adv14_fstring_conversion_compare.py` — f-string conversion
