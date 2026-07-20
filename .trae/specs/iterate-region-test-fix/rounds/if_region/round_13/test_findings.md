# IF Region Round 13 — 测试发现报告

## 轮次范围

R13 聚焦 R1-R12 未充分探索的深层边缘场景，重点探索方向：
- 复杂 walrus 在 if 条件中（walrus 绑定推导式 / 属性链 / len 复用）
- f-string 在 if 条件中（== 比较 / in 操作 / call arg）
- 切片与下标嵌套（三层 subscr / 切片比较 / 切片后下标）
- lambda 在 if 条件中（immediate call / any(map(...)) / walrus 绑定 lambda）
- 装饰器/嵌套函数在 if 体内（async def / decorated async def）
- 复杂布尔表达式归约（嵌套 not / 分组 and/or / 三元组合 boolop）
- 条件表达式 + 副作用（walrus 链式依赖 / 方法调用 + or）
- 复杂链式比较（4 段链式 / 多段相等 / is not + attr 链）
- **三元 + 推导式/f-string/BINARY_OP 组合**（R12 修复 _WRAPPING_OPS 后的新边界）

共发现 **11 个真实失败**的反编译错误，全部通过 `python -m pytest tests/exhaustive/if_region/test_adv13_*.py --tb=short -q` 验证（11 failed, 4 passed）。

## 错误清单（共 11 个真实失败）

### Error 1: walrus 绑定 listcomp 结果时丢失 filter
- **测试文件**: `test_adv13_walrus_listcomp_cond.py`
- **源码**:
  ```python
  if (x := [i for i in range(10) if i > 5]):
      pass
  ```
- **失败信息**: `AssertionError: 嵌套code object不匹配 (指令1): 指令数不匹配: 10 vs 7`
  - 原始 listcomp code object: `['RESUME', 'BUILD_LIST', 'LOAD_FAST', 'STORE_FAST', 'LOAD_FAST', 'LOAD_CONST', 'COMPARE_OP', 'LOAD_FAST', 'LIST_APPEND', 'RETURN_VALUE']` (10 条)
  - 重编 listcomp code object: `['RESUME', 'BUILD_LIST', 'LOAD_FAST', 'STORE_FAST', 'LOAD_FAST', 'LIST_APPEND', 'RETURN_VALUE']` (7 条)
- **反编译输出**:
  ```python
  if (x := [i for i in range(10)]):
      pass
  ```
- **根因分析**: 当 walrus 绑定的值是带 filter 的 listcomp `[i for i in range(10) if i > 5]` 时，反编译器在重建 listcomp code object 时丢失了 `if i > 5` 过滤条件。原始 listcomp 嵌套 code object 包含 `LOAD_CONST 5 / COMPARE_OP > / POP_JUMP_IF_FALSE` 实现过滤；反编译后 listcomp 变为 `[i for i in range(10)]`，COMPARE_OP 指令完全消失。R5 listcomp_if_filter 已覆盖 if body 中的 listcomp filter，但 walrus 绑定 listcomp 作为 if 条件时 filter 丢失，说明 walrus 上下文中 listcomp code object 重建路径与普通 listcomp 不同。

### Error 2: dictcomp 直接作 if 条件产生语法错误
- **测试文件**: `test_adv13_dictcomp_direct_cond.py`
- **源码**:
  ```python
  if {k: v for k, v in items}:
      pass
  ```
- **失败信息**: `AssertionError: 反编译结果语法错误: invalid syntax (<unknown>, line 1)`
- **反编译输出**:
  ```python
  if {<>: <> for k in items}:
      pass
  ```
- **根因分析**: 当 dictcomp `{k: v for k, v in items}` 直接作为 if 条件时，反编译器将 key 与 value 表达式替换为占位符 `<>`，输出 `if {<>: <> for k in items}:` 导致语法错误。原始字节码 dictcomp 嵌套 code object 使用 `UNPACK_SEQUENCE 2` 解包 `(k, v)` 对，再 `STORE_FAST k / STORE_FAST v / MAP_ADD`；反编译器未能从 UNPACK_SEQUENCE 重建 key/value 表达式，用 `<>` 占位。R5 dictcomp_walrus 已覆盖 walrus 上下文中的 dictcomp，但 dictcomp 直接作 if 条件（无 walrus 包裹）时 key/value 重建失败。

### Error 3: walrus 绑定 dictcomp 产生语法错误
- **测试文件**: `test_adv13_walrus_dictcomp_cond.py`
- **源码**:
  ```python
  if (x := {k: v for k, v in items}):
      pass
  ```
- **失败信息**: `AssertionError: 反编译结果语法错误: invalid syntax (<unknown>, line 1)`
- **反编译输出**:
  ```python
  if (x := {<>: <> for k in items}):
      pass
  ```
- **根因分析**: 与 Error 2 同根因，但多了 walrus 包裹。walrus 绑定 dictcomp 时，dictcomp 的 key/value 仍被替换为 `<>` 占位符。这说明 dictcomp 的 key/value 重建缺陷不仅存在于直接 if 条件，也存在于 walrus 上下文。R5 dictcomp_walrus 标记为已覆盖，但实际 walrus + dictcomp 在 if 条件中仍失败（可能是 R5 测试使用简单 key/value 如 `{x: y for ...}` 而非解包形式 `{k: v for k, v in ...}`）。

### Error 4: setcomp 直接作 if 条件丢失 filter
- **测试文件**: `test_adv13_setcomp_direct_cond.py`
- **源码**:
  ```python
  if {x for x in y if x > 0}:
      pass
  ```
- **失败信息**: `AssertionError: 嵌套code object不匹配 (指令1): 指令数不匹配: 10 vs 7`
  - 原始 setcomp code object: `['RESUME', 'BUILD_SET', 'LOAD_FAST', 'STORE_FAST', 'LOAD_FAST', 'LOAD_CONST', 'COMPARE_OP', 'LOAD_FAST', 'SET_ADD', 'RETURN_VALUE']` (10 条)
  - 重编 setcomp code object: `['RESUME', 'BUILD_SET', 'LOAD_FAST', 'STORE_FAST', 'LOAD_FAST', 'SET_ADD', 'RETURN_VALUE']` (7 条)
- **反编译输出**:
  ```python
  if {x for x in y}:
      pass
  ```
- **根因分析**: 与 Error 1 同根因，但作用于 setcomp。当 setcomp `{x for x in y if x > 0}` 直接作 if 条件时，filter `if x > 0` 被丢失，反编译为 `{x for x in y}`。原始 setcomp code object 含 `LOAD_CONST 0 / COMPARE_OP > / POP_JUMP_IF_FALSE` 实现过滤；反编译后 COMPARE_OP 消失。R6 setcomp_nested、R7 setcomp_multi_for 已覆盖 if body 中的 setcomp，但 setcomp 直接作 if 条件时 filter 丢失。

### Error 5: 三元 in f-string 丢失 f-string 包裹
- **测试文件**: `test_adv13_ternary_in_fstring_cond.py`
- **源码**:
  ```python
  if f"{a if c else b}" == "x":
      pass
  ```
- **失败信息**: `AssertionError: 指令数不匹配: 11 vs 10`
  - 原始: `['RESUME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'FORMAT_VALUE', 'LOAD_CONST', 'COMPARE_OP', 'LOAD_CONST', 'RETURN_VALUE', 'LOAD_CONST', 'RETURN_VALUE']` (11 条)
  - 重编: `['RESUME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_CONST', 'COMPARE_OP', 'LOAD_CONST', 'RETURN_VALUE', 'LOAD_CONST', 'RETURN_VALUE']` (10 条)
- **反编译输出**:
  ```python
  if ((a if c else b) == 'x'):
      pass
  ```
- **根因分析**: 当 if 条件为 `f"{a if c else b}" == "x"` 时，反编译器丢失了 f-string 的 `FORMAT_VALUE` 指令，将三元表达式直接与字符串常量比较，输出 `(a if c else b) == 'x'`。原始字节码在三元 merge_block 后执行 `FORMAT_VALUE 0` 将三元结果转为字符串，再 `LOAD_CONST 'x' / COMPARE_OP ==`；反编译器跳过了 FORMAT_VALUE，因为 FORMAT_VALUE 不在 R12 扩展的 `_WRAPPING_OPS` 集合中（R12 新增了 CALL_FUNCTION_EX/DICT_MERGE/BUILD_MAP/CONTAINS_OP/IS_OP，但未包含 FORMAT_VALUE）。R10 fstring_ternary 已覆盖 if body 中的 f-string + 三元，但 if 条件中 f-string 包裹三元时 FORMAT_VALUE 丢失。

### Error 6: 三元 in listcomp 丢失三元（变常量 b）
- **测试文件**: `test_adv13_ternary_in_listcomp_cond.py`
- **源码**:
  ```python
  if [a if c else b for x in y]:
      pass
  ```
- **失败信息**: `AssertionError: 嵌套code object不匹配 (指令1): 指令数不匹配: 9 vs 7`
  - 原始 listcomp code object: `['RESUME', 'BUILD_LIST', 'LOAD_FAST', 'STORE_FAST', 'LOAD_GLOBAL', 'LOAD_GLOBAL', 'LOAD_GLOBAL', 'LIST_APPEND', 'RETURN_VALUE']` (9 条)
  - 重编 listcomp code object: `['RESUME', 'BUILD_LIST', 'LOAD_FAST', 'STORE_FAST', 'LOAD_GLOBAL', 'LIST_APPEND', 'RETURN_VALUE']` (7 条)
- **反编译输出**:
  ```python
  if [b for x in y]:
      pass
  ```
- **根因分析**: 当 listcomp 元素为三元 `a if c else b` 时，反编译器在重建 listcomp code object 时丢失了整个三元表达式，只保留 false 分支的 `b`。原始 listcomp code object 含 `LOAD_GLOBAL c / POP_JUMP_IF_FALSE / LOAD_GLOBAL a / JUMP / LOAD_GLOBAL b` 实现三元；反编译后只剩 `LOAD_GLOBAL b / LIST_APPEND`，三元条件与 true 分支 `a` 完全消失。R6 listcomp_with_if_else 已覆盖 if body 中 listcomp 含三元元素，但 listcomp 直接作 if 条件时三元元素退化为 false 分支常量。

### Error 7: 两个三元作 and 操作数产生额外 and 子句与额外 if
- **测试文件**: `test_adv13_ternary_and_ternary_boolop.py`
- **源码**:
  ```python
  if (a if c else b) and (d if e else f):
      pass
  ```
- **失败信息**: `AssertionError: 指令7操作码不匹配: LOAD_CONST vs LOAD_NAME`
  - 原始 (filtered): 17 条指令（RESUME + 6 LOAD_NAME + 5 对 LOAD_CONST/RETURN_VALUE）
  - 重编 (filtered): 17 条指令（RESUME + 9 LOAD_NAME + 4 对 LOAD_CONST/RETURN_VALUE）
  - 指令 7: 原始 `LOAD_CONST None` vs 重编 `LOAD_NAME 'd'`
- **反编译输出**:
  ```python
  if ((a if c else b) and (d if e else f) and d):
      pass
  if (d if e else f):
      pass
  ```
- **根因分析**: 当两个三元表达式 `(a if c else b)` 和 `(d if e else f)` 作 and 操作数时，反编译器在第一个 if 条件末尾凭空插入额外的 `and d` 子句，并生成一条完全多余的第二个 `if (d if e else f): pass` 语句。原始字节码只有单个 if（条件求值后 POP_JUMP_IF_FALSE 到 pass/结束两个分支），重编字节码多了 3 个 LOAD_NAME（d/e/d/f）对应额外的三元求值。R2 ternary_in_boolop_and 已覆盖 `(a if c else d) and b`（三元 + 普通变量），但两个独立三元作 and 操作数时，第二个三元的 merge_block 被误识别为新 if 的 cond_block，导致生成额外 if。

### Error 8: 三元 + 普通变量 + 三元 作 and 产生额外 and 子句与额外 if
- **测试文件**: `test_adv13_ternary_plain_ternary_and.py`
- **源码**:
  ```python
  if (a if c else b) and d and (e if f else g):
      pass
  ```
- **失败信息**: `AssertionError: 指令数不匹配: 20 vs 18`
  - 原始: 20 条指令
  - 重编: 18 条指令
- **反编译输出**:
  ```python
  if ((a if c else b) and d and (e if f else g) and e):
      pass
  if (e if f else g):
      pass
  ```
- **根因分析**: 与 Error 7 同根因，但 and 链中夹了一个普通变量 `d`。反编译器在第一个 if 条件末尾插入额外的 `and e`（取第二个三元的 true 分支），并生成多余的第二个 `if (e if f else g): pass`。两个三元被普通变量 d 隔开时，第二个三元的 merge_block 仍被误识别为新 if 的 cond_block。这证实 Error 7 的缺陷不限于连续两个三元，三元被普通变量隔开同样失败。

### Error 9: 三个三元作 or 产生完全错误的嵌套 if 结构
- **测试文件**: `test_adv13_ternary_three_or_cond.py`
- **源码**:
  ```python
  if (a if c else b) or (d if e else f) or (g if h else i):
      pass
  ```
- **失败信息**: `AssertionError: 指令数不匹配: 16 vs 25`
  - 原始: 16 条指令（RESUME + 9 LOAD_NAME + 3 对 LOAD_CONST/RETURN_VALUE）
  - 重编: 25 条指令（含额外 4 个 LOAD_NAME 与 1 个额外 LOAD_CONST/RETURN_VALUE 对）
- **反编译输出**:
  ```python
  if ((a if c else b) or e):
      if (not (b or e and d) and g and ((a if c else b) or e)):
          pass
  ```
- **根因分析**: 当三个三元表达式作 or 操作数时，反编译器产生完全错误的嵌套 if 结构：丢失第二个三元的条件 `e` 与 false 分支 `f`，丢失第三个三元的条件 `h` 与 false 分支 `i`，并生成一条嵌套 if 含复杂的 `not (b or e and d)` 表达式。原始字节码是单层 if 含三段独立三元 merge_block 由 or 短路连接；反编译后变成双层嵌套 if，第二层条件引用了未定义的 `e`/`d`/`g` 等变量。R12 修复了"嵌套三元选最外层"（共享 cond_block 的嵌套三元），但三个独立三元作 or 操作数（非嵌套，而是并列）时 merge_block 归并完全错乱。

### Error 10: 三元 + BINARY_OP 丢失 BINARY_OP
- **测试文件**: `test_adv13_ternary_binary_op_cond.py`
- **源码**:
  ```python
  if (a if c else b) + 1 > 0:
      pass
  ```
- **失败信息**: `AssertionError: 指令数不匹配: 12 vs 10`
  - 原始: `['RESUME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_CONST', 'BINARY_OP', 'LOAD_CONST', 'COMPARE_OP', 'LOAD_CONST', 'RETURN_VALUE', 'LOAD_CONST', 'RETURN_VALUE']` (12 条)
  - 重编: `['RESUME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_NAME', 'LOAD_CONST', 'COMPARE_OP', 'LOAD_CONST', 'RETURN_VALUE', 'LOAD_CONST', 'RETURN_VALUE']` (10 条)
- **反编译输出**:
  ```python
  if ((a if c else b) > 0):
      pass
  ```
- **根因分析**: 当 if 条件为 `(a if c else b) + 1 > 0` 时，反编译器丢失了 `+ 1` BINARY_OP 操作，将三元结果直接与 0 比较，输出 `(a if c else b) > 0`。原始字节码在三元 merge_block 后执行 `LOAD_CONST 1 / BINARY_OP +` 再 `LOAD_CONST 0 / COMPARE_OP >`；反编译器跳过了 `LOAD_CONST 1 / BINARY_OP +`，因为 BINARY_OP 不在 R12 扩展的 `_WRAPPING_OPS` 集合中。R8 augassign_binop_rhs 已覆盖 BINARY_OP 作 augassign 右值，但三元 merge_block 后的 BINARY_OP 包裹（作为比较操作数）未被识别。

### Error 11: 嵌套三元（无外层括号）作 if 条件丢失 if
- **测试文件**: `test_adv13_nested_ternary_bare_cond.py`
- **源码**:
  ```python
  if a if b else c if d else e:
      pass
  ```
  （Python 解析为 `if (a if b else (c if d else e)): pass`）
- **失败信息**: `AssertionError: 反编译结果中未找到预期的区域类型 IF_REGION (期望AST节点: ['If'])`
- **反编译输出**:
  ```python
  (a if b else c if d else e)
  ```
- **根因分析**: 当 if 条件为嵌套三元 `a if b else c if d else e`（无外层括号）时，反编译器完全丢失了 `if` 关键字与条件分支，只剩孤立的 `(a if b else c if d else e)` Expr 语句。原始字节码 cond_block 末尾是 `POP_JUMP_FORWARD_IF_FALSE`（控制流跳转），但反编译器误判该模式为值上下文的三元表达式（类似 R11 walrus_ternary_if_cond 的退化模式）。R12 修复了"嵌套三元选最外层"用于 `(a if (b if c else d) else e)` 形式（内层三元作外层三元的 cond），但 `a if b else (c if d else e)` 形式（内层三元作外层三元的 else 分支）作为 if 条件时仍退化为 Expr。

## 共性根因

1. **`_WRAPPING_OPS` 集合不完整**：R12 扩展了 wrapping 指令集合（新增 CALL_FUNCTION_EX/DICT_MERGE/BUILD_MAP/CONTAINS_OP/IS_OP），但仍未包含：
   - `FORMAT_VALUE`（f-string）→ Error 5
   - `BINARY_OP`（二元运算）→ Error 10
   三元 merge_block 后的这些指令未被识别为 wrapping，导致三元结果后的运算被丢弃。

2. **推导式 code object 重建缺陷**：listcomp/setcomp/dictcomp 的嵌套 code object 在作为 if 条件（直接或经 walrus 包裹）时，filter 与 key/value/element 表达式重建失败：
   - listcomp/setcomp filter 丢失（Error 1, 4）
   - dictcomp key/value 变为 `<>` 占位符（Error 2, 3）
   - listcomp 三元元素退化为 false 分支常量（Error 6）

3. **多个独立三元在 boolop 中的归并错乱**：R12 修复了"嵌套三元选最外层"（一个三元作另一个三元的 cond/true/false 分支），但未处理多个独立三元作 boolop 操作数的场景：
   - 两个三元作 and → 额外 and 子句 + 额外 if（Error 7）
   - 三元 + 普通变量 + 三元作 and → 同上（Error 8）
   - 三个三元作 or → 完全错误的嵌套 if 结构（Error 9）
   第二个（及后续）三元的 merge_block 被误识别为新 if 的 cond_block。

4. **嵌套三元作 if 条件退化为 Expr**：`a if b else (c if d else e)`（内层三元作 else 分支）作为 if 条件时，整个 if 退化为孤立的 Expr 语句（Error 11）。R12 的嵌套三元选最外层修复仅覆盖 `(a if (b if c else d) else e)` 形式（内层作 cond），未覆盖内层作 else 分支的形式。

## 失败统计

- **总测试数**: 15 (11 failed + 4 passed)
- **失败率**: 73%
- **失败类别分布**:
  - 推导式 code object 重建（filter/key/value/element 丢失）: 5 (Errors 1-6 中的 1,2,3,4,6)
  - 三元 + boolop 归并错乱（额外 and/if 或嵌套结构）: 3 (Errors 7,8,9)
  - 三元 + wrapping 指令丢失（FORMAT_VALUE/BINARY_OP 不在 _WRAPPING_OPS）: 2 (Errors 5,10)
  - 嵌套三元作 if 条件退化: 1 (Error 11)

## 通过的测试（4 个，作为对照）

以下测试在 R13 中创建并通过，证明这些场景已被 R1-R12 覆盖或反编译器已正确处理：
- `test_adv13_fstring_eq_compare.py` — `if f"{x}" == "hello": pass`（f-string 直接作 == 左操作数，FORMAT_VALUE 在 cond_block 顶部，无需 wrapping 识别）
- `test_adv13_triple_subscr_chain.py` — `if d[a][b][c] > 0: pass`（多层 BINARY_SUBSCR 链在 if 条件中已支持）
- `test_adv13_slice_eq_slice_compare.py` — `if d[a:b] == d[c:d]: pass`（两个 BUILD_SLICE 在 if 条件中已支持）
- `test_adv13_isnot_attr_chain.py` — `if x is not None and x.field is not None: pass`（IS_OP + LOAD_ATTR 在 and 短路中已支持）

## 测试运行命令

```bash
# 运行所有 R13 测试
cd /workspace && python -m pytest tests/exhaustive/if_region/test_adv13_*.py --tb=short -q

# 运行单个测试
cd /workspace && python -m pytest tests/exhaustive/if_region/test_adv13_<name>.py --tb=long
```

## 测试文件清单（15 个）

1. `/workspace/tests/exhaustive/if_region/test_adv13_dictcomp_direct_cond.py` — FAILED
2. `/workspace/tests/exhaustive/if_region/test_adv13_fstring_eq_compare.py` — PASSED
3. `/workspace/tests/exhaustive/if_region/test_adv13_isnot_attr_chain.py` — PASSED
4. `/workspace/tests/exhaustive/if_region/test_adv13_nested_ternary_bare_cond.py` — FAILED
5. `/workspace/tests/exhaustive/if_region/test_adv13_setcomp_direct_cond.py` — FAILED
6. `/workspace/tests/exhaustive/if_region/test_adv13_slice_eq_slice_compare.py` — PASSED
7. `/workspace/tests/exhaustive/if_region/test_adv13_ternary_and_ternary_boolop.py` — FAILED
8. `/workspace/tests/exhaustive/if_region/test_adv13_ternary_binary_op_cond.py` — FAILED
9. `/workspace/tests/exhaustive/if_region/test_adv13_ternary_in_fstring_cond.py` — FAILED
10. `/workspace/tests/exhaustive/if_region/test_adv13_ternary_in_listcomp_cond.py` — FAILED
11. `/workspace/tests/exhaustive/if_region/test_adv13_ternary_plain_ternary_and.py` — FAILED
12. `/workspace/tests/exhaustive/if_region/test_adv13_ternary_three_or_cond.py` — FAILED
13. `/workspace/tests/exhaustive/if_region/test_adv13_triple_subscr_chain.py` — PASSED
14. `/workspace/tests/exhaustive/if_region/test_adv13_walrus_dictcomp_cond.py` — FAILED
15. `/workspace/tests/exhaustive/if_region/test_adv13_walrus_listcomp_cond.py` — FAILED

## 结论

R13 共发现 11 个 IF 区域反编译真实错误，超过 10 个目标。这些错误集中在以下深层边缘场景：

1. **`_WRAPPING_OPS` 集合不完整**：FORMAT_VALUE（f-string）与 BINARY_OP（二元运算）未被识别为三元 merge_block 后的 wrapping 指令，导致三元结果后的 f-string 转换与 +1 运算被丢弃。R12 扩展了该集合但仍有遗漏。

2. **推导式 code object 重建在 if 条件上下文中失败**：listcomp/setcomp 的 filter、dictcomp 的 key/value、listcomp 的三元元素在作为 if 条件（直接或经 walrus 包裹）时全部丢失或退化为占位符。R5-R7 已覆盖 if body 中的推导式，但 if 条件上下文的推导式 code object 重建路径存在独立缺陷。

3. **多个独立三元在 boolop 中的归并错乱**：R12 修复了嵌套三元（一个三元作另一个三元的子表达式）的选层问题，但未处理多个独立三元作 boolop 并列操作数的场景。第二个（及后续）三元的 merge_block 被误识别为新 if 的 cond_block，导致生成额外的 and 子句、额外的 if 语句，甚至完全错误的嵌套 if 结构。

4. **嵌套三元（else 分支含内层三元）作 if 条件退化为 Expr**：R12 的嵌套三元选最外层修复仅覆盖内层三元作 cond 的形式 `(a if (b if c else d) else e)`，未覆盖内层三元作 else 分支的形式 `a if b else (c if d else e)`，后者作为 if 条件时整个 if 退化为孤立的 Expr 语句。

这些错误为后续 R14 修复提供了明确的靶向：
- 扩展 `_WRAPPING_OPS` 集合加入 FORMAT_VALUE / BINARY_OP
- 修复推导式 code object 重建在 if 条件上下文中的 filter/key/value/element 处理
- 修复多个独立三元在 boolop 中的 merge_block 归并逻辑
- 扩展嵌套三元选最外层修复覆盖 else 分支含内层三元的形式
