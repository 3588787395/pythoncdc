# LOOP Region Round 01 测试发现报告

## 基线

现有 `tests/exhaustive/while_loop/` + `tests/exhaustive/for_loop/` 共 313 个测试，
**18 failed / 295 passed**（`python -m pytest tests/exhaustive/while_loop/ tests/exhaustive/for_loop/`）。

已知失败（不计为本轮发现）：
- `for-else + break` 简单组合：`test_fl13forbreakelse_*`、`test_l05forelse_break_*`、`test_fl49forelsebreakassign_*`、`test_for06_for_else`、`test_fl40forbreakcontelse_*`
- `while True + break`（简单计数）：`test_l15whiletruebreak_*`
- `while + break in try`（无 else/finally）：`test_wl30whilebreakintry_*`
- `while + 多个 break`：`test_wl32whilemultibreak_*`

本轮新增测试目录：`tests/exhaustive/loop/round_01/`（16 个 `test_r1_*.py`）。
全部 16 个测试经 **官方 `ExhaustiveTestCase.verify_decompilation()` 框架**（编译→反编译→重编译→`_compare_code_objects` 字节码比对）验证为 **真实失败**：
`python -m pytest tests/exhaustive/loop/round_01/` → **16 failed / 0 passed**。

Python 版本：3.11.15。反编译路径：`CFGBuilder → RegionAnalyzer → RegionASTGenerator → CodeGenerator`
（与 `tests/control_flow_matrix/base.py` 中 `decompile()` 一致）。

---

## 发现的错误（共 16 个）

### 错误 1: while True + continue 丢失循环体（continue 被当作 else 分支）
- **测试文件**: tests/exhaustive/loop/round_01/test_r1_while_true_continue_only.py
- **源码**:
```python
while True:
    if a:
        continue
    b = 1
```
- **反编译输出**:
```python
while True:
    if a:
        continue
    else:
        continue
```
- **失败类型**: 字节码不匹配（且语义错误：`b = 1` 整条语句丢失，被替换为 `else: continue`）
- **字节码 diff 摘要**: 原始 4 条 `RESUME, LOAD_NAME, LOAD_CONST, STORE_NAME` → 重编 2 条 `RESUME, LOAD_NAME`（`STORE_NAME b` 丢失）
- **疑似算法根因**: while-true 模式下 continue 处理。`_loop_handle_continue`（region_ast_generator.py:6653）将 if 之后 fall-through 到回边块的路径错误识别为 continue；`_detect_break_continue`（region_analyzer.py:4127）把 if-then 之后的顺序块（`b=1`）并入回边，导致 body 顺序语句丢失。

### 错误 2: for + try/except 中 break/continue 被吞、return 被提到循环外
- **测试文件**: tests/exhaustive/loop/round_01/test_r1_for_try_except_break_continue.py
- **源码**:
```python
def f():
    for i in items:
        try:
            if i == 0:
                break
        except ValueError:
            continue
    return i
```
- **反编译输出**:
```python
def f():
    for i in items:
        try:
            if (i == 0):
                pass
        except ValueError: pass
        return i
```
- **失败类型**: 字节码不匹配（语义错误：`break` 变成 `pass`，`continue` 丢失，`return i` 被错误地放进循环体）
- **字节码 diff 摘要**: 嵌套 code object 指令数 19 vs 22；多出 `SWAP/POP_TOP/RETURN_CONST`，`POP_TOP`（break）位置错乱
- **疑似算法根因**: try-in-loop 归约顺序。`_detect_break_continue`（region_analyzer.py:4127）未把 try-body 内的 `break`（跳到循环外）识别为 break_blocks（被 PUSH_EXC_INFO 异常块过滤逻辑 4198 行误排除）；`_loop_handle_back_edge`（region_ast_generator.py:6668）把循环后的 `return i` 拉进循环体。

### 错误 3: for + try/finally + break 整个 for 循环丢失
- **测试文件**: tests/exhaustive/loop/round_01/test_r1_for_try_finally_break.py
- **源码**:
```python
for i in r:
    try:
        if i:
            break
    finally:
        cleanup()
```
- **反编译输出**:
```python
try:
    if i:
        cleanup()
finally: cleanup()
```
- **失败类型**: 字节码不匹配（语义错误：**for 循环完全消失**，`break` 丢失，`cleanup()` 被当作 if 体）
- **字节码 diff 摘要**: 原始 30 条（含 `GET_ITER/FOR_ITER/STORE_NAME` 循环指令）→ 重编 24 条（无任何循环指令）
- **疑似算法根因**: try-finally 区域先于 loop 归约（`_identify_try_except_regions` 在 `_identify_loop_regions` 之前调用），try-finally 把含 break 的循环体吞为自身 body，导致 LoopRegion 不再识别（违反原则 1「自底向上」：try-finally 不应跨越 for 循环 header）。

### 错误 4: while 链式比较条件被拆成 if + while 常量
- **测试文件**: tests/exhaustive/loop/round_01/test_r1_while_chained_compare_cond.py
- **源码**:
```python
while 0 < x < 10:
    x += 1
```
- **反编译输出**:
```python
if (0 < x < 10):
    pass
while 10:
    x += 1
    if (not 0 < x):
        break
```
- **失败类型**: 字节码不匹配（语义错误：循环结构被破坏，条件 `0 < x` 变成 break 守卫）
- **字节码 diff 摘要**: 原始 29 条 → 重编 18 条；多出独立的 `if ...: pass`，`while 10` 用常量作条件
- **疑似算法根因**: `_identify_chained_compare_regions`（region_analyzer.py:10641）与 LOOP 归约争抢 header 块。链式比较的中间比较块被识别为独立 IfRegion（`if (0 < x < 10): pass`），while 条件块被拆，`condition_block` 退化为常量 `10`。

### 错误 5: while 三元条件丢失循环体（变 if）
- **测试文件**: tests/exhaustive/loop/round_01/test_r1_while_ternary_cond.py
- **源码**:
```python
while (a if c else b):
    x = 1
```
- **反编译输出**:
```python
if (a if c else b):
    pass
```
- **失败类型**: 字节码不匹配（语义错误：while 循环体 `x = 1` 完全丢失，循环本身降级为 if）
- **字节码 diff 摘要**: 原始 17 条 → 重编 10 条；缺少 `STORE_NAME x` 及回边重检块
- **疑似算法根因**: fused ternary-loop 识别。`_identify_loop_regions` Step 7(d)（region_analyzer.py:3069-3091）`_is_fused_ternary_false_value_block`（region_analyzer.py:16546）跳过 false_value 块使 `condition_block=None`，循环以 while_true 识别；但 `_loop_generate_while` 的三元消费（region_ast_generator.py:3535）把循环体当三元 merge 块抑制，导致 body 丢失。

### 错误 6: while `not a and b` 丢失 `not a` 操作数
- **测试文件**: tests/exhaustive/loop/round_01/test_r1_while_not_and_boolop.py
- **源码**:
```python
while not a and b:
    x = 1
```
- **反编译输出**:
```python
while b:
    x = 1
```
- **失败类型**: 字节码不匹配（语义错误：复合条件首操作数 `not a` 丢失）
- **字节码 diff 摘要**: 原始 15 条（含 `LOAD_NAME a` 的 `UNARY_NOT` 短路链）→ 重编 9 条
- **疑似算法根因**: `_detect_while_condition_boolop_chain`（region_analyzer.py:16382）回溯复合 `and` 条件链时，`not a` 这一前导操作数的块未并入 condition_block。回溯起点（region_analyzer.py:3173-3220）的「等价出口」计数 `_back_edge_recheck_count` 对 `not` 前缀块计数不足，首操作数被泄漏为外层 IfRegion 或直接丢弃。

### 错误 7: for iter 为 boolop 表达式时被泄漏为语句 + `for x in None`
- **测试文件**: tests/exhaustive/loop/round_01/test_r1_for_iter_boolop.py
- **源码**:
```python
for x in (a or b):
    y = x
```
- **反编译输出**:
```python
(a or b)
for x in None:
    y = x
```
- **失败类型**: 字节码不匹配（语义错误：迭代表达式 `(a or b)` 被当作独立语句泄漏，iter 目标变成 `None`）
- **字节码 diff 摘要**: 原始 10 条（`JUMP_IF_TRUE_OR_POP` 后直接 `GET_ITER`）→ 重编 12 条（多出 `POP_TOP` 与 `LOAD_CONST None`）
- **疑似算法根因**: `_loop_generate_for`（region_ast_generator.py:3130）取 for 的 iter 表达式时，未识别 preheader 中 `GET_ITER` 之前的 boolop 短路链（`JUMP_IF_TRUE_OR_POP`），把 boolop 块作为独立语句生成，iter 回退为 `None`。

### 错误 8: while 链式比较 + break 整个循环降级为单 if
- **测试文件**: tests/exhaustive/loop/round_01/test_r1_while_chained_compare_break.py
- **源码**:
```python
while 0 <= x < 10:
    if x == 5:
        break
    x += 1
```
- **反编译输出**:
```python
if (0 <= x < 10 and x == 5):
    pass
```
- **失败类型**: 字节码不匹配（语义错误：循环与 break 合并为单个 if，循环体 `x += 1` 与回边全丢失）
- **字节码 diff 摘要**: 原始 34 条 → 重编 20 条；无任何 `JUMP_BACKWARD`/回边重检
- **疑似算法根因**: 链式比较条件 + break 同时存在时，`_identify_chained_compare_regions`（region_analyzer.py:10641）把条件块与 break 守卫块合并为一个 IfRegion，LoopRegion 的 header 被吞，整个循环被识别为单 if（违反原则 2「每块唯一归属」与原则 1）。

### 错误 9: while-else 中 else 的 return 被提升为循环后无条件 return
- **测试文件**: tests/exhaustive/loop/round_01/test_r1_while_else_return.py
- **源码**:
```python
def f():
    while a:
        if b:
            break
    else:
        return 1
    return 2
```
- **反编译输出**:
```python
def f():
    while a:
        if b:
            break
    return 1
```
- **失败类型**: 字节码不匹配（语义错误：`else: return 1` 被降级为循环后无条件 `return 1`，`return 2` 丢失，for-else 语义被破坏）
- **字节码 diff 摘要**: 嵌套 code object 指令数 8 vs 6；缺少 `return 2` 对应的 `LOAD_CONST/RETURN_VALUE`
- **疑似算法根因**: `_find_loop_else` 的 while 分支（region_analyzer.py:3864-3867）。当 else 块是 `return` 时，natural_exit 与 else 块的 post-dominator 边界混淆：`return 1`（else）和 `return 2`（循环后）未被区分，else 块未被识别，导致 `return 1` 被当作循环后顺序语句。

### 错误 10: while + try/except/else/finally + break 结构错乱
- **测试文件**: tests/exhaustive/loop/round_01/test_r1_while_try_except_else_finally_break.py
- **源码**:
```python
while a:
    try:
        x = 1
    except E:
        break
    else:
        y = 2
    finally:
        z = 3
```
- **反编译输出**:
```python
while a:
    try:
        x = 1
    except E:
        z = 3
        break
    else: y = 2
    finally: z = 3
```
- **失败类型**: 字节码不匹配（语义错误：`finally: z = 3` 被复制进 `except` 分支，`break` 路径错位）
- **字节码 diff 摘要**: 原始 33 条 → 重编 35 条；except 分支多出 `LOAD_CONST/STORE_NAME z`，`RERAISE` 顺序错乱
- **疑似算法根因**: try-except-else-finally 在循环内的归约。`finally` 块被同时归入 except handler 与外层 finally（违反原则 2「每块唯一归属」）；`_detect_break_continue`（region_analyzer.py:4127）把 except 内 break 与 finally 清理块耦合。

### 错误 11: while 循环体内 walrus + break 被替换为 pass
- **测试文件**: tests/exhaustive/loop/round_01/test_r1_while_walrus_break.py
- **源码**:
```python
while a:
    if (n := f()):
        break
```
- **反编译输出**:
```python
while a:
    pass
```
- **失败类型**: 字节码不匹配（语义错误：walrus 赋值与 if-break 整条语句丢失，循环体变 `pass`）
- **字节码 diff 摘要**: 原始 15 条（`PRECALL/CALL/COPY/STORE_NAME` + break 路径）→ 重编 7 条
- **疑似算法根因**: 循环体内含 walrus 的 if-break 块。walrus 的 `COPY/STORE` 指令使该块被 `_detect_break_continue`（region_analyzer.py:4232-4239）的 continue 判定误捕，或被 if-break 区域识别时 whole-sale 抑制，body 退化为 pass。

### 错误 12: while + yield from 被替换为 None 表达式
- **测试文件**: tests/exhaustive/loop/round_01/test_r1_while_yield_from.py
- **源码**:
```python
def g():
    while a:
        yield from inner()
```
- **反编译输出**:
```python
def g():
    while a:
        None
```
- **失败类型**: 字节码不匹配（语义错误：`yield from inner()` 被替换为 `None` 表达式）
- **字节码 diff 摘要**: 嵌套 code object 指令数 18 vs 7；缺少 `GET_YIELD_FROM_ITER/YIELD_VALUE/JUMP_BACKWARD_NO_INTERRUPT` 整条 yield-from 链
- **疑似算法根因**: `yield from` 隐式循环（`_identify_loop_regions` 模式 E，region_analyzer.py:2911 `is_yield_from`）。`yield from inner()` 的 SEND+YIELD_VALUE 自循环未被识别为 yield-from 表达式，循环体被当作普通块生成，`GET_YIELD_FROM_ITER` 链丢失为 `None`。

### 错误 13: for + try 内嵌套 if 的 continue 守卫丢失、continue 提前
- **测试文件**: tests/exhaustive/loop/round_01/test_r1_for_try_continue_nested_if.py
- **源码**:
```python
for i in r:
    try:
        if a:
            if b:
                continue
        x = 1
    except E:
        pass
```
- **反编译输出**:
```python
for i in r:
    try:
        continue
        x = 1
    except E: pass
```
- **失败类型**: 字节码不匹配（语义错误：`if a: if b:` 双层守卫丢失，`continue` 变无条件，`x = 1` 变死代码）
- **字节码 diff 摘要**: 原始 19 条 → 重编 15 条；缺少 `LOAD_NAME a/b` 的条件跳转链
- **疑似算法根因**: 嵌套 if 中的 continue 在 try-body 内归约。`_loop_handle_continue`（region_ast_generator.py:6653）与 try 区域归约交互时，内层 `if b: continue` 的条件块被吞为 continue 入口，外层 `if a` 守卫被抑制。

### 错误 14: while 三元链式比较条件产生语法错误（`<copy_placeholder_2>`）
- **测试文件**: tests/exhaustive/loop/round_01/test_r1_while_chained_compare_three.py
- **源码**:
```python
while 0 < x < y < 100:
    x += 1
```
- **反编译输出**:
```python
if (0 < x and y < <copy_placeholder_2> and 0 < x < y < 100):
    pass
while 100:
    x += 1
    if (not 0 < x):
        break
    if (y < <copy_placeholder_2>):
        pass
    else:
        break
```
- **失败类型**: 语法错误（`verify_syntax` 失败：`invalid syntax`，含未替换的 `<copy_placeholder_2>` 占位符）
- **字节码 diff 摘要**: 无法重编译；反编译输出含 `<copy_placeholder_2>` 占位符且 `not 0 < x` 优先级错乱
- **疑似算法根因**: 三元链式比较（4 操作数 `0 < x < y < 100`）的 chained_compare 区域识别泄漏了 COPY 占位符。`_identify_chained_compare_regions`（region_analyzer.py:10641）对 3 段以上链式比较的中间值 `COPY` 指令未正确物化为临时变量，输出占位符字面量。

### 错误 15: 嵌套 for + 内层 else + 外层 break 丢失外层 break 与 else
- **测试文件**: tests/exhaustive/loop/round_01/test_r1_nested_for_inner_else_outer_break.py
- **源码**:
```python
for i in r:
    for j in s:
        if j:
            break
    else:
        continue
    break
```
- **反编译输出**:
```python
for i in r:
    for j in s:
        if j:
            break
        continue
```
- **失败类型**: 字节码不匹配（语义错误：内层 `else: continue` 降级为内层循环体顺序 `continue`，外层 `break` 与内层 else 边界全丢失）
- **字节码 diff 摘要**: 原始 14 条 → 重编 11 条；缺少外层 break 的 `POP_TOP` 与 else 汇聚块
- **疑似算法根因**: 嵌套循环 else 边界。`_find_loop_else`（region_analyzer.py:3847）对内层 for-else 的 else 块（`continue`）与外层 break 目标的 post-dominator 计算混淆，内层 else 被并入内层循环体，外层 break 被丢弃（违反原则 3「嵌套区域作为单个抽象节点」）。

### 错误 16: while 三操作数 `and` 条件首操作数泄漏为循环后 if-break
- **测试文件**: tests/exhaustive/loop/round_01/test_r1_while_boolop_three_and.py
- **源码**:
```python
while a and b and c:
    x = 1
```
- **反编译输出**:
```python
while b and c:
    x = 1
    if a:
        pass
    else:
        break
```
- **失败类型**: 字节码不匹配（语义错误：`a` 操作数从 while 条件泄漏为循环体末尾的 `if a: pass else: break`，复合条件被拆散）
- **字节码 diff 摘要**: 原始 21 条 → 重编 18 条；多出循环体内的 `if a ... else break` 块
- **疑似算法根因**: `_detect_while_condition_boolop_chain`（region_analyzer.py:16382）对 3 操作数 `and` 链回溯不完整。`_back_edge_recheck_count`（region_analyzer.py:3161-3171）只计部分等价出口，首操作数 `a` 的回边重检块未并入 condition_block，泄漏为循环体末尾的 IfRegion（违反原则 2）。

---

## 小结

- **本轮新增真实错误**：16 个（均经官方测试框架验证为 FAIL，非已知基线失败）。
- **覆盖任务重点模式**：while-true+continue（#1）、for-else/while-else 边界（#9/#15）、break-else 复合（#9）、嵌套循环（#15）、try/with 在循环内（#2/#3/#10/#13）、continue 在嵌套结构（#13）、循环条件含三元/boolop/链式比较（#4/#5/#6/#8/#14/#16）、循环体含 walrus/yield（#11/#12）、for iter 复杂表达式（#7）。
- **失败类型分布**：字节码不匹配 15 个、语法错误 1 个（#14）。所有案例的反编译输出均存在可观察的语义错误（语句丢失 / 结构降级 / 占位符泄漏），非「语义等价但字节码不同」的良性差异。
- **算法根因集中点**：
  - `region_analyzer.py:_identify_loop_regions` Step 7 条件块回溯（3069-3220）
  - `region_analyzer.py:_detect_break_continue`（4127）对 try/with/walrus 内 break/continue 的过滤
  - `region_analyzer.py:_find_loop_else`（3847）while-else 与 return/嵌套 else 边界
  - `region_analyzer.py:_identify_chained_compare_regions`（10641）与 LOOP 争抢 header
  - `region_analyzer.py:_detect_while_condition_boolop_chain`（16382）多操作数 and/or 回溯
  - `region_ast_generator.py:_loop_generate_while`（3462）/`_loop_generate_for`（3130）三元/yield-from/boolop iter 消费
  - `region_ast_generator.py:_loop_handle_continue`（6653）/`_loop_handle_back_edge`（6668）while-true continue 与顺序块归属
