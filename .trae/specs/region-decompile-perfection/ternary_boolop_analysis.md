# ternary / boolop 区域失败分析报告

**生成时间**: 2026-07-11
**失败用例数**: 12 (10 ternary + 2 boolop)

## 失败模式分类

| 模式 | 数量 | 典型用例 | 根因摘要 |
|------|------|----------|----------|
| T1: 三元区域边界贪婪 — 吞噬周围上下文 | 6 | ternary18, 04ternaryfuncarg | 三元区域识别时将周围的函数调用参数/算术操作数错误地纳入三元区域，导致优先级丢失、变量名替换 |
| T2: 三元未识别 — 误识别为其他结构 | 2 | ternary10, ternary12 | 三元在函数默认参数 / while 条件中时未被识别为 TERNARY 区域，被错误地反编译为 lambda / if-while-if |
| T3: AST 反解析失败 | 1 | ternary20 | f-string (JoinedStr) 节点在三元表达式中未被正确反解析，输出 `<JoinedStr>` 字面文本 → SyntaxError |
| T4: 三元内 boolop 括号丢失 + 孤儿表达式 | 1 | ternary14 | `(a and b) if flag else (c or d)` → 括号丢失 + `b` `d` 作为独立语句泄漏到外层 |
| B1: 列表推导中的 boolop 未识别 | 1 | bo42 | `if x > 0 and x < 100` → 拆分为两个 `if` 过滤子句，且外层多了 `return` |
| B2: 复杂 not/and/or 结构丢失 | 1 | bo43 | `not (a and b) or (c and not d)` → `or` 丢失、变量 `b` 丢失、两组 AND 合并、`not` 作用域错误 |

## 详细分析

### 模式 T1: 三元区域边界贪婪（6 个，最大类别）

**受影响用例**:
- test_ternary18_math_expr.py
- test_04ternaryfuncarg_a_b.py
- test_te04ternaryfuncparam_a.py
- test_te04ternaryfuncparam_n.py
- test_ternary09_in_dict.py
- test_ternary19_string_expr.py

**典型用例 1**: test_ternary18_math_expr.py

原始源码:
```python
result = base * (multiplier if scale else 1) + offset
```

错误反编译结果:
```python
result = base * multiplier if scale else 1 + offset
```

字节码差异:
- 原始 13 指令，重编 13 指令（数量相同但语义不同）
- 原始: `LOAD base → LOAD scale → POP_JUMP_IF_FALSE → LOAD multiplier → JUMP → LOAD_CONST 1 → BINARY_OP * → LOAD offset → BINARY_OP + → STORE result`
  - 即 `base * (ternary_result) + offset`，三元在乘法内部
- 重编: `LOAD scale → POP_JUMP_IF_FALSE → LOAD base → LOAD multiplier → BINARY_OP * → JUMP → LOAD_CONST 1 → LOAD offset → BINARY_OP + → STORE result`
  - 即 `(base * multiplier) if scale else (1 + offset)`，三元提升到顶层

**典型用例 2**: test_04ternaryfuncarg_a_b.py

原始源码:
```python
result = func(a if a > 0 else b)
```

错误反编译结果:
```python
result = a(a if a > 0 else b)
```

字节码差异:
- 仅指令 2 参数不匹配: `func` vs `a` (op=LOAD_NAME)
- 原始: `PUSH_NULL → LOAD_NAME func → LOAD_NAME a → LOAD_CONST 0 → COMPARE_OP > → POP_JUMP_IF_FALSE → LOAD_NAME a → JUMP → LOAD_NAME b → PRECALL 1 → CALL 1 → STORE result`
  - 即 `func(ternary_result)`，三元是函数参数
- 重编: `PUSH_NULL → LOAD_NAME a → ...` — `func` 被替换为 `a`

**根因**:
1. `_identify_ternary_regions` 的区域边界识别过于贪婪
2. 三元区域的入口块被错误地向前扩展，包含了 `LOAD_NAME func` / `LOAD_NAME base` 等属于外层表达式的指令
3. 违反「每块唯一归属」原则 — 外层表达式块被同时分配给 TernaryRegion 和外层 SequenceRegion
4. 三元在表达式中的位置（作为函数参数、算术操作数）未被正确处理

**修复方向**:
- 三元区域的入口块应严格从 `POP_JUMP_FORWARD_IF_FALSE`（条件测试）开始
- 三元的 then/else 分支应只包含 `LOAD_NAME multiplier` / `LOAD_CONST 1`，不包括 `LOAD_NAME base` / `LOAD_NAME offset`
- 归约后三元在父区域中作为单个抽象节点，父区域的表达式重建应保持原始嵌套关系

### 模式 T2: 三元未识别 — 误识别为其他结构（2 个）

**受影响用例**:
- test_ternary10_as_default.py
- test_ternary12_in_while.py

**典型用例 1**: test_ternary10_as_default.py

原始源码:
```python
def fn(x, y=DEFAULT if FLAG else ALT):
    pass
```

错误反编译结果:
```python
fn = (lambda *args, **kwargs: None)
```

字节码差异:
- 原始 12 指令，重编 6 指令（丢失 6 条指令）
- 原始有 `LOAD_NAME FLAG → POP_JUMP_IF_FALSE → LOAD_NAME DEFAULT → JUMP → LOAD_NAME ALT → BUILD_TUPLE → LOAD_CONST <code> → MAKE_FUNCTION 1`
  - `MAKE_FUNCTION arg=1` 表示有默认参数
- 重编只有 `LOAD_CONST <code> → MAKE_FUNCTION 0`
  - `MAKE_FUNCTION arg=0` 表示无默认参数

**根因**:
1. `_identify_ternary_regions` 未扫描函数定义的默认参数上下文
2. 三元在 `MAKE_FUNCTION` 前的 `BUILD_TUPLE` 中时未被识别
3. 整个函数定义被错误地反编译为 lambda 赋值

**典型用例 2**: test_ternary12_in_while.py

原始源码:
```python
while (next_item() if has_more() else None):
    pass
```

错误反编译结果:
```python
if has_more() and next_item():
    while next_item():
        if has_more():
            pass
```

字节码差异:
- 原始 31 指令，重编 35 指令
- 原始结构: while 条件 = 三元表达式 `next_item() if has_more() else None`
  - `has_more()` → `POP_JUMP_IF_FALSE` → (false) `LOAD_CONST None, RETURN_VALUE` (else 分支)
  - `next_item()` → `POP_JUMP_IF_FALSE` → (false) 退出 while
  - `JUMP_FORWARD` → while 循环体
- 重编结构: if-while-if 三层嵌套
  - 完全丢失了三元表达式的语义

**根因**:
1. `_identify_ternary_regions` 未在 while 条件中识别三元
2. while 循环的回边检测与三元条件测试混淆
3. 三元的 `POP_JUMP_IF_FALSE` 被误认为 while 的循环条件测试

**修复方向**:
- 三元识别应独立于上下文（函数默认参数、while 条件、字典值等）
- 三元的字节码模式: `LOAD condition → POP_JUMP_FORWARD_IF_FALSE → LOAD then → JUMP_FORWARD → LOAD else`
- 无论出现在什么上下文中，这个模式都应被识别为三元

### 模式 T3: AST 反解析失败（1 个）

**受影响用例**: test_ternary20_complex_practical.py

原始源码:
```python
def format_size(bytes_val):
    if bytes_val < 1024:
        return f"{bytes_val} B"
    elif bytes_val < 1048576:
        return f"{bytes_val/1024:.1f} KB" if bytes_val % 1024 == 0 else f"{bytes_val//1024} KB"
    else:
        return f"{bytes_val/1048576:.1f} MB" if bytes_val % 1048576 == 0 else f"{bytes_val//1048576} MB"
```

错误反编译结果:
```python
def format_size(bytes_val):
    <JoinedStr> if bytes_val < 1024 else (<JoinedStr> if bytes_val % 1024 == 0 else <JoinedStr>) if bytes_val < 1048576 else <JoinedStr> if bytes_val % 1048576 == 0 else <JoinedStr>
```

错误: `SyntaxError: invalid syntax` — `<JoinedStr>` 是 AST 节点类型名，不是有效的 Python 源码

**根因**:
1. `_generate_ternary` 在生成 IfExp 节点时，其 then/else 子表达式为 f-string (JoinedStr) 节点
2. AST 反解析器（unparse）未能正确处理 JoinedStr 节点，直接输出了 `<JoinedStr>` 字面文本
3. 同时 if-elif-else 结构被错误地折叠为嵌套三元表达式

**修复方向**:
- 修复 AST 反解析器对 JoinedStr 节点的处理
- 或修复 `_generate_if` / `_generate_ternary` 的边界，不要将 if-elif-else 错误折叠为三元

### 模式 T4: 三元内 boolop 括号丢失 + 孤儿表达式（1 个）

**受影响用例**: test_ternary14_with_boolop.py

原始源码:
```python
x = (a and b) if flag else (c or d)
```

错误反编译结果:
```python
x = a and b if flag else c or d
b
d
```

字节码差异:
- 原始 13 指令，重编 17 指令（多 4 条）
- 主赋值部分指令相同（0-10）
- 重编多了: `LOAD_NAME b → POP_TOP → LOAD_NAME d → POP_TOP → LOAD_CONST None → RETURN_VALUE`
  - 即 `b` 和 `d` 作为独立表达式语句泄漏到外层

**根因**:
1. 三元区域内的 boolop 子区域的块被部分泄漏到外层 SequenceRegion
2. 违反「每块唯一归属」原则
3. 括号丢失导致优先级变化: `(a and b) if flag else (c or d)` ≠ `a and b if flag else c or d`

**修复方向**:
- boolop 子区域的块应完全属于 TernaryRegion 的 then/else 分支
- 归约后三元在父区域中作为单个抽象节点，`b` 和 `d` 不应作为独立语句出现

### 模式 B1: 列表推导中的 boolop 未识别（1 个）

**受影响用例**: test_bo42boolopinlistcomp_items.py

原始源码:
```python
[x for x in items if x > 0 and x < 100]
```

错误反编译结果:
```python
return [x for x in items if x > 0 if x < 100]
```

错误: `SyntaxError: 'return' outside function` — 模块级 `return`

字节码差异:
- 原始在嵌套 code object `<listcomp>` 中
- `and` 被拆分为两个 `if` 过滤子句（语法等价但 BOOL_OP 区域未识别）

**根因**:
1. `_identify_boolop_regions` 未扫描列表推导的嵌套 code object
2. boolop 在 comprehension 条件中时未被识别
3. 外层表达式被错误添加 `return`

### 模式 B2: 复杂 not/and/or 结构丢失（1 个）

**受影响用例**: test_bo43complexnotandor_a_b_c_d.py

原始源码:
```python
not (a and b) or (c and not d)
```

错误反编译结果:
```python
not (a and c and not d)
```

字节码差异:
- 原始 19 指令，重编 11 指令（少 8 条）
- 原始有 3 个退出路径（`POP_TOP + LOAD_CONST + RETURN_VALUE` × 3），对应 `or` 的 3-way 短路
- 重编只有 1 个退出路径，`or` 结构完全丢失
- 变量 `b` 完全丢失
- 两个 AND 组 `(a and b)` 和 `(c and not d)` 被错误合并为 `(a and c and not d)`

**根因**:
1. `_identify_boolop_regions` 未能正确处理 `not (a and b) or (c and not d)` 的嵌套结构
2. `or` 的短路分支未被识别为独立的 boolop 子区域
3. `not` 的作用域未正确限定 — 原始 `not` 只作用于 `(a and b)`，重编 `not` 作用于整个表达式

**修复方向**:
- boolop 识别应递归处理嵌套的 and/or/not
- `JUMP_IF_TRUE_OR_POP` 标记 `or` 的短路分支
- `JUMP_IF_FALSE_OR_POP` 标记 `and` 的短路分支
- `UNARY_NOT` 的作用域应由其后的跳转指令确定

## 修复优先级

1. **P0: 模式 T1（6 个）** — 影响面最大，根因明确（三元区域边界贪婪）
2. **P0: 模式 T2（2 个）** — 三元完全未识别，需扩展识别上下文
3. **P1: 模式 T4 + B2（2 个）** — boolop 块归属 + 嵌套 boolop 结构
4. **P1: 模式 T3（1 个）** — AST 反解析 bug，可能需修复 unparser
5. **P2: 模式 B1（1 个）** — 列表推导中的 boolop，嵌套 code object 扫描

## 修复建议

### 对 `_identify_ternary_regions` 的修改

1. **严格入口块定义**: 三元区域的入口块应从 `POP_JUMP_FORWARD_IF_FALSE`（条件测试）开始，不包括之前的 `LOAD_NAME` / `PUSH_NULL` 等外层表达式指令
2. **then/else 分支边界**: then 分支 = 条件为真后的块到 `JUMP_FORWARD` 为止；else 分支 = `JUMP_FORWARD` 目标之后的块到合并点为止
3. **上下文无关识别**: 无论三元出现在赋值右侧、函数参数、while 条件、函数默认参数中，都应被识别为 TERNARY 区域
4. **归约语义**: 归约后三元在父区域中作为单个抽象节点，父区域的表达式重建应保持原始嵌套关系

### 对 `_generate_ternary` 的修改

1. **IfExp 生成**: 生成 `ast.IfExp(test, body, orelse)` 节点
2. **括号处理**: 当三元出现在表达式中间时，应生成带括号的源码以保持优先级
3. **JoinedStr 处理**: 确保 f-string 子表达式被正确反解析

### 对 `_identify_boolop_regions` 的修改

1. **嵌套 code object 扫描**: 递归扫描列表推导、生成器、lambda 中的 boolop
2. **嵌套 and/or/not 处理**: 递归识别 `not (a and b) or (c and not d)` 的结构
3. **短路分支识别**: `JUMP_IF_TRUE_OR_POP` = `or` 短路，`JUMP_IF_FALSE_OR_POP` = `and` 短路

### 对 docstring 的修改

按 6 节模板重写 `_identify_ternary_regions`、`_identify_boolop_regions` 的 docstring。
按 4 节模板重写 `_generate_ternary`、`_generate_boolop` 的 docstring。
