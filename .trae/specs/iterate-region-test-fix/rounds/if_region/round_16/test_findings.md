# Round 16 — IF 区域反编译器测试发现

**日期**: 2026-07-18
**测试工程师**: R16 自动探索
**测试范围**: IF 区域内嵌套 match 语句（match 在 if body 内的各种模式：
or-pattern、class pattern kwargs/positional/mixed/wildcard/guard/nested、
mapping pattern、literal+guard），以及探索 walrus 嵌套、字符串方法链、
星号字典构造、try/except/else/finally 等 9 个未覆盖方向的初步验证

---

## 统计摘要

| 指标 | 数量 |
|------|------|
| 测试文件总数 | 15 |
| 失败（FAILED） | 10 |
| 跳过（SKIPPED，反编译产出非法语法） | 1 |
| 通过（PASSED） | 4 |
| **新错误总数** | **11** |

运行命令:
```
cd /workspace && python -m pytest tests/exhaustive/if_region/test_adv16_*.py --tb=short -q
```

结果: `10 failed, 4 passed, 1 skipped in 1.19s`

---

## 测试文件列表

| # | 文件 | 状态 | 错误类别 |
|---|------|------|----------|
| 1 | `test_adv16_match_or_pattern_in_if.py` | FAILED | `case _: pass` 丢失（or 模式 + 字面量） |
| 2 | `test_adv16_match_or_string_in_if.py` | FAILED | `case _: pass` 丢失（or 模式 + 字符串字面量） |
| 3 | `test_adv16_match_or_multi_value_in_if.py` | FAILED | `case _: pass` 丢失（or 模式 + 3 值） |
| 4 | `test_adv16_match_class_pattern_in_if.py` | FAILED | `case _: pass` 丢失（class kwargs） |
| 5 | `test_adv16_match_class_positional_in_if.py` | FAILED | `case _: pass` 丢失（class positional） |
| 6 | `test_adv16_match_class_mixed_args_in_if.py` | FAILED | `case _: pass` 丢失（class 混合 args） |
| 7 | `test_adv16_match_class_wildcard_pos_in_if.py` | FAILED | `Point(_, _)` 通配符位置参数丢失 |
| 8 | `test_adv16_match_class_guard_in_if.py` | FAILED | class pattern + guard → guard `if z` 丢失 |
| 9 | `test_adv16_match_class_nested_in_if.py` | FAILED | 嵌套 class pattern → 非法语法（`<MatchClass>` 占位符泄漏） |
| 10 | `test_adv16_match_guard_in_if.py` | FAILED | literal + guard → guard 丢失 + match 提升出 if body |
| 11 | `test_adv16_match_mapping_pattern_in_if.py` | SKIPPED | `**rest` 重命名为 `**v`（变量冲突编译失败） |
| 12 | `test_adv16_nested_walrus_chain.py` | PASSED | 三层嵌套 walrus（探索方向 #1 验证） |
| 13 | `test_adv16_string_method_chain_compare.py` | PASSED | 字符串方法链比较（探索方向 #2 验证） |
| 14 | `test_adv16_starred_dict_compare.py` | PASSED | `{**a, **b}` 比较（探索方向 #4 验证） |
| 15 | `test_adv16_try_except_else_finally_in_if.py` | PASSED | 完整 try/except/else/finally（探索方向 #6 验证） |

---

## 详细发现

### Bug 1: match or-pattern + case _ → `case _: pass` 丢失

**文件**: `test_adv16_match_or_pattern_in_if.py`
**状态**: FAILED（指令10操作码不匹配: POP_TOP vs LOAD_CONST）

**源码**:
```python
if c:
    match x:
        case 1 | 2:
            pass
        case _:
            pass
```

**反编译结果**:
```python
if c:
    match x:
        case 1 | 2:
            pass
```

**问题**: 当 match 语句同时含有 or-pattern 的 case 和 `case _: pass` 通配
fallback 时，反编译器将 `case _: pass` 整体丢弃。这导致原始字节码中
对应 `case _` body 的 `LOAD_CONST None / RETURN_VALUE` 路径在反编译产出
中不存在，重编后该位置变为 `LOAD_CONST None`（用于 or-pattern 不匹配
的隐式 fallthrough），与原始 `POP_TOP`（消费 COPY 副本）不匹配。

**字节码对比**（filtered，跳过 jump 指令）:
- 原始 17 条 / 重编 17 条
- 差异点 10: 原始 `POP_TOP`（消费 or-pattern 的 COPY 副本）vs 重编 `LOAD_CONST None`

**根因推测**: or-pattern 的 `MATCH_SEQUENCE` / `COPY` / `COMPARE_OP` 链
处理完后，反编译器未能正确生成 `case _` 通配分支，导致 `case _` 被吞并。

---

### Bug 2: match or-pattern（字符串字面量）+ case _ → `case _: pass` 丢失

**文件**: `test_adv16_match_or_string_in_if.py`
**状态**: FAILED（指令10操作码不匹配: POP_TOP vs LOAD_CONST）

**源码**:
```python
if c:
    match s:
        case "a" | "b":
            pass
        case _:
            pass
```

**反编译结果**:
```python
if c:
    match s:
        case 'a' | 'b':
            pass
```

**问题**: 与 Bug 1 同源，区别在于 or-pattern 的字面量是字符串而非整数。
`case _: pass` 同样丢失，字节码差异点 10 同样为 `POP_TOP` vs `LOAD_CONST`。
说明该 bug 与 or-pattern 的字面量类型无关，是 or-pattern + case _ 通配
组合的共性问题。

---

### Bug 3: match or-pattern（3 值）+ case _ → `case _: pass` 丢失

**文件**: `test_adv16_match_or_multi_value_in_if.py`
**状态**: FAILED（指令13操作码不匹配: POP_TOP vs LOAD_CONST）

**源码**:
```python
if c:
    match x:
        case 1 | 2 | 3:
            pass
        case _:
            pass
```

**反编译结果**:
```python
if c:
    match x:
        case 1 | 2 | 3:
            pass
```

**问题**: 与 Bug 1 同源，or-pattern 扩展到 3 个值。字节码差异点变为 13
（因为多一个 `COPY / LOAD_CONST / COMPARE_OP`），同样是 `POP_TOP` vs
`LOAD_CONST`。说明 bug 随 or-pattern 值数线性扩展，与值数量无关。

---

### Bug 4: match class pattern（kwargs）+ case _ → `case _: pass` 丢失

**文件**: `test_adv16_match_class_pattern_in_if.py`
**状态**: FAILED（指令数不匹配: 20 vs 22）

**源码**:
```python
if c:
    match p:
        case Point(x=1, y=2):
            pass
        case _:
            pass
```

**反编译结果**:
```python
if c:
    match p:
        case Point(x=1, y=2):
            pass
```

**问题**: 当 match 语句同时含有 class pattern 的 case（带 kwargs）和
`case _: pass` 通配 fallback 时，反编译器将 `case _: pass` 整体丢弃。
重编后字节码反而多出 2 条 `LOAD_CONST None / RETURN_VALUE`（位置 20-21），
表明反编译器在丢失 `case _` 后，重编时 Python 编译器仍生成了隐式 fallthrough
返回路径，与原始显式 `case _: pass` 的字节码布局不等价。

**字节码对比**:
- 原始 20 条 / 重编 22 条
- 重编在尾部多出 `LOAD_CONST None / RETURN_VALUE`（位置 20-21）

**根因推测**: `MATCH_CLASS` 的 `POP_JUMP_FORWARD_IF_NONE` 跳转目标在
反编译器归约时未能正确指向 `case _` body，导致 `case _` 被视为不可达
而丢弃。

---

### Bug 5: match class pattern（positional）+ case _ → `case _: pass` 丢失

**文件**: `test_adv16_match_class_positional_in_if.py`
**状态**: FAILED（指令数不匹配: 20 vs 22）

**源码**:
```python
if c:
    match p:
        case Point(1, 2):
            pass
        case _:
            pass
```

**反编译结果**:
```python
if c:
    match p:
        case Point(1, 2):
            pass
```

**问题**: 与 Bug 4 同源，区别在于 class pattern 使用位置参数而非关键字参数
（`MATCH_CLASS 2` 的 arg=2 表示 2 个 positional args）。
`case _: pass` 同样丢失，重编字节码多 2 条 `LOAD_CONST None / RETURN_VALUE`。

---

### Bug 6: match class pattern（混合 positional + kwargs）+ case _ → `case _: pass` 丢失

**文件**: `test_adv16_match_class_mixed_args_in_if.py`
**状态**: FAILED（指令数不匹配: 20 vs 22）

**源码**:
```python
if c:
    match p:
        case Point(1, y=2):
            pass
        case _:
            pass
```

**反编译结果**:
```python
if c:
    match p:
        case Point(1, y=2):
            pass
```

**问题**: 与 Bug 4 同源，class pattern 同时含 positional 和 keyword 参数。
`case _: pass` 同样丢失。说明该 bug 与 class pattern 的参数形式（positional /
kwargs / mixed）无关，是 class pattern + case _ 通配组合的共性问题。

---

### Bug 7: match class pattern 带通配符位置参数 `_` → 通配符丢失

**文件**: `test_adv16_match_class_wildcard_pos_in_if.py`
**状态**: FAILED（指令数不匹配: 18 vs 16）

**源码**:
```python
if c:
    match p:
        case Point(_, _):
            pass
        case _:
            pass
```

**反编译结果**:
```python
if c:
    match p:
        case Point():
            pass
```

**问题**: 当 class pattern 的位置参数为通配符 `_`（即 `Point(_, _)`）时，
反编译器将两个 `_` 通配符全部丢弃，产出 `Point()`（无参数形式）。这导致
原始字节码中对应两个 `_` 的 `POP_TOP / POP_TOP`（消费 UNPACK_SEQUENCE
拆出的两个值）在反编译产出中不存在，重编字节码少 2 条。

**字节码对比**:
- 原始 18 条 / 重编 16 条
- 原始多出位置 9-10 的 `POP_TOP / POP_TOP`（消费两个 `_` 通配符）

**根因推测**: 反编译器将 `_` 通配符的位置参数视为"无参数"，错误地生成
`Point()`，未能保留 `_` 占位以触发 `UNPACK_SEQUENCE` + `POP_TOP`。

---

### Bug 8: match class pattern + guard → guard 丢失

**文件**: `test_adv16_match_class_guard_in_if.py`
**状态**: FAILED（指令数不匹配: 21 vs 22）

**源码**:
```python
if c:
    match p:
        case Point(x=1, y=2) if z:
            pass
        case _:
            pass
```

**反编译结果**:
```python
if c:
    match p:
        case Point(x=1, y=2):
            pass
```

**问题**: 当 class pattern 带守卫（`if z`）时，反编译器将守卫整体丢弃。
原始字节码中对应守卫的 `LOAD_NAME z / POP_JUMP_IF_FALSE` 在反编译产出中
不存在。同时 `case _: pass` 也丢失（与 Bug 4 同源）。

**字节码对比**:
- 原始 21 条 / 重编 22 条
- 原始位置 14 为 `LOAD_NAME z`（守卫变量），重编此处缺失，后续指令整体前移

**根因推测**: 反编译器在 `MATCH_CLASS` + `COMPARE_OP` 链归约后，未能正确
识别 `POP_JUMP_IF_FALSE` 作为 guard 的条件跳转，将 guard 视为多余指令丢弃。

---

### Bug 9: match 嵌套 class pattern → 非法语法（`<MatchClass>` 占位符泄漏）

**文件**: `test_adv16_match_class_nested_in_if.py`
**状态**: FAILED（反编译结果语法错误: `invalid syntax (<unknown>, line 4)`）

**源码**:
```python
if c:
    match p:
        case Outer(x=Inner(1)):
            pass
        case _:
            pass
```

**反编译结果**:
```python
if c:
    match p:
        case Outer(1):
            if (<MatchClass> is not None and 1):
                pass
```

**问题**: 当 class pattern 的属性值本身是嵌套 class pattern（即
`Outer(x=Inner(1))`）时，反编译器完全破坏了结构：
1. 外层 `Outer(x=Inner(1))` 被错误简化为 `Outer(1)`（丢失 `x=` 关键字
   和内层 `Inner(` 包装）
2. 内层 `Inner(1)` 被拆出为独立 `if` 语句
3. 该 `if` 语句的条件包含 `<MatchClass>` 字面字符串占位符（明显是内部
   节点对象的 repr 泄漏到输出中），导致 `ast.parse` 直接抛 SyntaxError

**根因推测**: 反编译器对嵌套 `MATCH_CLASS` 的归约未实现，遇到内层
`MATCH_CLASS` 时回退到占位符输出，且将内层 match 的 COMPARE_OP 部分错误
提升为外层 if 语句。

---

### Bug 10: match literal + guard → guard 丢失 + match 提升出 if body

**文件**: `test_adv16_match_guard_in_if.py`
**状态**: FAILED（指令数不匹配: 14 vs 9）

**源码**:
```python
if c:
    match x:
        case 1 if y > 0:
            pass
        case _:
            pass
```

**反编译结果**:
```python
if c:
    pass
match x:
    case 1:
        pass
```

**问题**: 这是 R16 发现的最严重 bug。当 match 语句在 if body 内、且 case
带 guard（`case 1 if y > 0`）时，反编译器：
1. 将整个 `match x:` 语句从 if body 内部提升到 if body 外部（与 if 同级）
2. if body 内仅保留 `pass`
3. 守卫 `if y > 0` 完全丢失
4. `case _: pass` 通配 fallback 完全丢失
5. 重编字节码从 14 条锐减到 9 条（丢失 5 条指令：`LOAD_NAME y` /
   `LOAD_CONST 0` / `COMPARE_OP >` / `LOAD_CONST None` / `RETURN_VALUE`）

**字节码对比**:
- 原始 14 条 / 重编 9 条
- 重编缺失位置 5-9 的守卫判断 + `case _` body 路径

**根因推测**: 反编译器在 if body 内遇到 `MATCH` + 守卫的 `POP_JUMP_IF_FALSE`
时，将该跳转误识别为 if body 的边界（提前结束 if），导致 match 语句整体
"逃逸"出 if body。守卫和 `case _` 也一并丢失。

---

### Bug 11: match mapping pattern + `**rest` → `**rest` 重命名为 `**v`（编译失败）

**文件**: `test_adv16_match_mapping_pattern_in_if.py`
**状态**: SKIPPED（反编译产出 `case {'k': v, **v}: pass`，重编译抛 SyntaxError）

**源码**:
```python
if c:
    match d:
        case {"k": v, **rest}:
            pass
        case _:
            pass
```

**反编译结果**:
```python
if c:
    match d:
        case {'k': v, **v}:
            pass
```

**问题**: 当 match mapping pattern 同时含字面量键值绑定（`"k": v`）和
双星号捕获（`**rest`）时，反编译器将 `**rest` 错误重命名为 `**v`，与
字面量键值绑定的 `v` 变量名冲突。Python 3.11 不允许在同一 mapping pattern
中用同名变量既作值绑定又作 `**` 捕获目标，`compile` 抛 SyntaxError，
测试框架 `verify_bytecode_equivalence` 调用 `self.skipTest("重编译失败")` 跳过。

**根因推测**: 反编译器在 `MATCH_MAPPING` 的 `**rest` 捕获目标还原时，
错误地复用了前一个键值绑定变量 `v` 的名称，未能从字节码的 `STORE_NAME`
指令中正确恢复 `rest` 这个独立变量名。

---

## 错误模式归类

### 模式 A: match + `case _: pass` 通配 fallback 丢失（6 个）

这是 R16 发现的主要错误模式。当 match 语句同时含有非通配 case（or-pattern
或 class pattern）和 `case _: pass` 通配 fallback 时，反编译器将 `case _: pass`
整体丢弃。原始字节码中对应 `case _` body 的 `LOAD_CONST None / RETURN_VALUE`
路径在反编译产出中不存在或被错误归并，导致重编字节码与原始不等价。

**涉及测试**: Bug 1, 2, 3, 4, 5, 6（6 个）

### 模式 B: match class pattern 通配符位置参数 `_` 丢失（1 个）

class pattern 的位置参数为 `_`（通配符）时，反编译器将 `_` 视为"无参数"，
产出 `Point()`，丢失 `UNPACK_SEQUENCE` + `POP_TOP` 拆包消费指令。

**涉及测试**: Bug 7（1 个）

### 模式 C: match guard 守卫丢失（2 个）

case 带守卫（`if <cond>`）时，反编译器将守卫整体丢弃。其中 Bug 8 是
class pattern + guard，Bug 10 是 literal + guard。Bug 10 还伴随 match 语句
整体提升出 if body 的更严重问题。

**涉及测试**: Bug 8, 10（2 个）

### 模式 D: match 嵌套 class pattern 导致结构破坏 + 占位符泄漏（1 个）

嵌套 class pattern（`Outer(x=Inner(1))`）触发反编译器的未实现路径，
产出包含 `<MatchClass>` 字面字符串占位符的非法 Python 语法。

**涉及测试**: Bug 9（1 个）

### 模式 E: match mapping pattern 的 `**rest` 变量名还原错误（1 个）

mapping pattern 的双星号捕获目标 `**rest` 被错误重命名为前一个值绑定
变量名，导致同名冲突编译失败。

**涉及测试**: Bug 11（1 个）

---

## 探索方向覆盖情况

R16 任务列出的 9 个探索方向的覆盖情况：

| # | 方向 | 测试数 | 失败 | 备注 |
|---|------|--------|------|------|
| 1 | 复杂赋值与 walrus 组合 | 1 | 0 | `nested_walrus_chain` 通过（三层嵌套 walrus） |
| 2 | 复杂 string 操作 | 1 | 0 | `string_method_chain_compare` 通过（`"abc".upper() == "ABC"`） |
| 3 | 复杂数值表达式 | 0 | 0 | 未保留（探索阶段验证全部通过，腾出位置给 match bug） |
| 4 | 复杂容器构造 | 1 | 0 | `starred_dict_compare` 通过（`{**a, **b} == c`） |
| 5 | 复杂 control flow 在 if 体内 | 0 | 0 | 未保留（async for / nested with 探索阶段通过） |
| 6 | 复杂异常处理 | 1 | 0 | `try_except_else_finally_in_if` 通过（完整 try/except/else/finally） |
| 7 | 复杂 with 语句 | 0 | 0 | 未保留（with open 探索阶段通过） |
| 8 | 复杂 match 语句 | 11 | 11 | **全部失败/跳过** — 主要 bug 集中区 |
| 9 | 复杂推导式边界 | 0 | 0 | 未保留（listcomp/dictcomp/setcomp/genexp 探索阶段通过） |

**结论**: R16 探索了全部 9 个方向，发现 bug **仅集中在方向 8（match 语句）**，
其他 8 个方向的初步验证均通过。match 语句在 if body 内的 11 个子模式全部
触发反编译器 bug，是 R16 的核心发现区。

---

## 与 R1-R15 的区别

R1-R15 主要覆盖三元表达式、walrus、boolop、字符串/数值/容器字面量在
if 条件或 if body 中的反编译。R16 新发现集中在：

1. **match 语句在 if body 内** — 此前 R6/R10 的 `match_guard` /
   `match_class_pattern_args` / `match_seq_star` / `match_destructure`
   都是 match 在**顶层**（不在 if body 内）。R16 首次系统覆盖 match 在
   if body 内的各种子模式，发现 11 个新 bug。
2. **match `case _: pass` 通配 fallback 在 if body 内丢失** — 此前未覆盖，
   R16 发现 6 个子模式均触发该 bug。
3. **match class pattern 的 `_` 通配符位置参数丢失** — 此前未覆盖。
4. **match guard 在 if body 内丢失** — 此前 R6 的 `match_guard` 在顶层
   通过，R16 发现 guard 在 if body 内会被丢弃（甚至伴随 match 提升出
   if body 的更严重问题）。
5. **match 嵌套 class pattern 触发占位符泄漏** — 此前未覆盖，是反编译器
   未实现路径的明确信号。
6. **match mapping pattern 的 `**rest` 变量名还原错误** — 此前未覆盖。

---

## 建议修复优先级

1. **最高**: Bug 10（match literal + guard → match 提升出 if body）— 控制
   流结构完全破坏，match 语句从 if body 内"逃逸"到外层，影响面最大。
2. **最高**: Bug 9（嵌套 class pattern → `<MatchClass>` 占位符泄漏）—
   产出非法语法，且暴露反编译器未实现的归约路径。
3. **高**: Bug 7（class pattern 通配符位置参数 `_` 丢失）— `Point(_, _)`
   变为 `Point()`，模式匹配语义改变。
4. **高**: Bug 8（class pattern + guard 丢失）— guard 丢失导致匹配条件
   错误放宽。
5. **高**: Bug 11（mapping pattern `**rest` 重命名）— 编译失败。
6. **中**: Bug 1-6（`case _: pass` 通配 fallback 丢失）— 6 个子模式共
   性问题，修复一处可同时解决。
