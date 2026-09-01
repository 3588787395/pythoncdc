# match_region 测试失败根因分析报告

**生成时间**: 2026-07-14
**分析范围**: `tests/exhaustive/match_region/` 下 44 个失败测试
**分析方式**: 仅分析，不修改任何代码（本报告为唯一产出物）

---

## 一、失败用例汇总表

### 1.1 错误类型统计

| 错误类型 | 数量 | 占比 |
|---------|------|------|
| INSTRUCTION_COUNT_MISMATCH（指令数不匹配） | 34 | 77.3% |
| TEST_FAILURE（指令参数不匹配） | 6 | 13.6% |
| SYNTAX_ERROR（语法错误） | 4 | 9.1% |
| **合计** | **44** | **100%** |

### 1.2 失败用例明细表

> 根因类别缩写：RC1=模式检查块误入body / RC2=guard块未跳过 / RC3=默认case丢失 / RC4=`<MatchClass>`占位符 / RC5=星号模式错误 / RC6=class跳转参数偏移

| # | 测试名 | 模式类型 | 错误类型 | 指令数(orig→recomp) | 根因类别 | SOURCE_CODE 摘要 |
|---|--------|---------|---------|--------------------|---------|-----------------|
| 1 | m043 | Mapping | INSTRUCTION_COUNT_MISMATCH | 53→61 | RC1+RC3 | 两case映射 + 默认case |
| 2 | m047 | Mapping | INSTRUCTION_COUNT_MISMATCH | 28→30 | RC1 | 单case多键映射 |
| 3 | m048 | Mapping | SYNTAX_ERROR | — | RC4 | `Point(x=1,y=2) \| Point(x=2,y=1)` OR模式 |
| 4 | m05matchmapping_a | Mapping | INSTRUCTION_COUNT_MISMATCH | 22→26 | RC1 | `{'key': 1}` |
| 5 | m05matchmapping_n | Mapping | INSTRUCTION_COUNT_MISMATCH | 22→26 | RC1 | 同上(负数变体) |
| 6 | m05matchmapping_x | Mapping | INSTRUCTION_COUNT_MISMATCH | 22→26 | RC1 | 同上(变量变体) |
| 7 | m15matchmappingkey_a | Mapping | INSTRUCTION_COUNT_MISMATCH | 42→50 | RC1+RC3 | 两case键映射 |
| 8 | m15matchmappingkey_n | Mapping | INSTRUCTION_COUNT_MISMATCH | 42→50 | RC1+RC3 | 同上 |
| 9 | m15matchmappingkey_x | Mapping | INSTRUCTION_COUNT_MISMATCH | 42→50 | RC1+RC3 | 同上 |
| 10 | m06matchguard_a | Guard | INSTRUCTION_COUNT_MISMATCH | 18→23 | RC2 | `case int() if x>0` |
| 11 | m06matchguard_n | Guard | INSTRUCTION_COUNT_MISMATCH | 18→23 | RC2 | 同上 |
| 12 | m06matchguard_x | Guard | INSTRUCTION_COUNT_MISMATCH | 18→23 | RC2 | 同上 |
| 13 | m16matchguardcomplex_a | Guard | INSTRUCTION_COUNT_MISMATCH | 23→33 | RC2 | `case int() if x>0 and x<100` |
| 14 | m16matchguardcomplex_n | Guard | INSTRUCTION_COUNT_MISMATCH | 23→33 | RC2 | 同上 |
| 15 | m16matchguardcomplex_x | Guard | INSTRUCTION_COUNT_MISMATCH | 23→33 | RC2 | 同上 |
| 16 | m106matchguardboolop | Guard | INSTRUCTION_COUNT_MISMATCH | 24→39 | RC2+RC3 | 多case带boolop guard |
| 17 | m13matchclassargs_a | Class | TEST_FAILURE | 30→30 | RC6 | `case int(1)` 两case |
| 18 | m13matchclassargs_n | Class | TEST_FAILURE | 30→30 | RC6 | 同上 |
| 19 | m13matchclassargs_x | Class | TEST_FAILURE | 30→30 | RC6 | 同上 |
| 20 | m30matchclassmultiattr_a | Class | TEST_FAILURE | 17→17 | RC6 | `case int(x=1)` |
| 21 | m30matchclassmultiattr_n | Class | TEST_FAILURE | 17→17 | RC6 | 同上 |
| 22 | m30matchclassmultiattr_x | Class | TEST_FAILURE | 17→17 | RC6 | 同上 |
| 23 | m013 | Sequence | INSTRUCTION_COUNT_MISMATCH | 20→18 | RC1+RC3 | `case (1,2)` |
| 24 | m026 | Sequence | SYNTAX_ERROR | — | RC5 | `case [1,2]` + `case [1,*rest]` |
| 25 | m027 | Mapping | INSTRUCTION_COUNT_MISMATCH | 26→30 | RC1+RC3 | `case {'key': val}` |
| 26 | m028 | Class | SYNTAX_ERROR | — | RC4 | `Point(x=0,y=0)` 多case |
| 27 | m029 | Sequence | INSTRUCTION_COUNT_MISMATCH | 27→25 | RC1+RC3 | `case [1,[2,3]]` 嵌套 |
| 28 | m036 | Mapping | INSTRUCTION_COUNT_MISMATCH | 32→36 | RC1+RC3 | 双键映射多case |
| 29 | m038 | Class | INSTRUCTION_COUNT_MISMATCH | 19→17 | RC1+RC3 | `case Point(x=0)` |
| 30 | m039 | Class | INSTRUCTION_COUNT_MISMATCH | 22→27 | RC1+RC3 | `case Point(x,y)` |
| 31 | m040 | Sequence | INSTRUCTION_COUNT_MISMATCH | 34→32 | RC1+RC3 | `case [1,2]\|[3,4]` OR模式 |
| 32 | m041 | Sequence | INSTRUCTION_COUNT_MISMATCH | 36→32 | RC1+RC3 | `case [1,2]\|[3,4]` 带body |
| 33 | m042 | Sequence+Guard | INSTRUCTION_COUNT_MISMATCH | 20→25 | RC2+RC3 | `case [a] if a>0` |
| 34 | m080 | Mapping+Guard | INSTRUCTION_COUNT_MISMATCH | 59→72 | RC1+RC2+RC3 | 多case映射+guard |
| 35 | m083 | Class+Guard | INSTRUCTION_COUNT_MISMATCH | 99→121 | RC1+RC2+RC3 | 多case类+guard |
| 36 | m084 | Sequence+Guard | INSTRUCTION_COUNT_MISMATCH | 83→69 | RC1+RC3 | 5个case序列 |
| 37 | m093 | Mapping | INSTRUCTION_COUNT_MISMATCH | 48→54 | RC1+RC3 | 双键映射多case |
| 38 | m094 | Class | INSTRUCTION_COUNT_MISMATCH | 34→30 | RC1+RC3 | 类模式多case |
| 39 | m096 | Sequence | INSTRUCTION_COUNT_MISMATCH | 53→47 | RC1+RC3 | 序列OR模式多case |
| 40 | m098 | Mapping | INSTRUCTION_COUNT_MISMATCH | 29→38 | RC1+RC3 | 映射+比较 |
| 41 | m100 | Mapping | INSTRUCTION_COUNT_MISMATCH | 32→37 | RC1+RC5 | `case {'a':1, **rest}` 双星号 |
| 42 | m101 | Class+Guard | SYNTAX_ERROR | — | RC4 | `Point(x=x,y=y) if x>0 and y>0` |
| 43 | m104 | Mapping | INSTRUCTION_COUNT_MISMATCH | 48→56 | RC1+RC3 | 两case映射 |
| 44 | m107matchinfuncreturn | 综合 | INSTRUCTION_COUNT_MISMATCH | 74→100 | RC1+RC2+RC3 | 函数内多case混合 |

### 1.3 根因类别命中统计

| 根因类别 | 命中测试数 | 占比 | 严重程度 |
|---------|-----------|------|---------|
| RC1 模式检查块误入body | ~30 | 68% | 高（核心缺陷） |
| RC3 默认case body丢失 | ~22 | 50% | 高（RC1的连带后果） |
| RC2 guard块未跳过 | ~10 | 23% | 中 |
| RC6 class跳转参数偏移 | 6 | 14% | 低（仅参数差2字节） |
| RC4 `<MatchClass>`占位符 | 4 | 9% | 高（语法错误） |
| RC5 星号模式错误 | 2 | 5% | 中（语法错误） |

> 注：RC1 与 RC3 高度耦合（RC3 是 RC1 的直接连带后果），合计独立影响 ~36 个测试，占 82%。

---

## 二、根因分析

### 根因 RC1：模式检查块被错误地包含进 case body（核心缺陷）

**影响测试**: ~30 个（m027, m013, m038, m043, m047, m05*, m15*, m029, m036, m039, m040, m041, m080, m083, m084, m093, m094, m096, m098, m100, m104, m107 等）

**根因位置**:
- 文件: `core/cfg/region_analyzer.py`
- 方法: `_mr_collect_case_body()` (第 7774 行)
- 关键代码: 第 7883-7891 行调用 `_collect_blocks_on_path()`
- 底层方法: `_collect_blocks_on_path()` (第 926 行)

**机制分析**:

CPython 编译 match-case 时，每个 case 的模式检查（pattern check）与 body 在字节码层面是交织的。例如映射模式 `case {'key': val}` 的字节码结构为：

```
[MATCH_MAPPING, GET_LEN, LOAD_CONST(1), COMPARE_OP(>=)]   <- 长度检查
[LOAD_CONST(('key',)), MATCH_KEYS, COPY, POP_JUMP_FORWARD_IF_NONE]  <- 键检查(模式检查块)
[UNPACK_SEQUENCE, SWAP, POP_TOP, POP_TOP, STORE_NAME(val)]  <- 真正的body
[LOAD_NAME(val), STORE_NAME(y), LOAD_CONST(None), RETURN_VALUE]  <- body续
```

`_mr_collect_case_body()` 通过 `_collect_blocks_on_path(resolved_success, jt, stop_set)` 用 BFS 从 body 入口收集所有可达块。问题在于：

1. **stop_set 构造不完整**（第 7885 行）: `stop_set = visited | {jt} | pattern_jump_targets`。`pattern_jump_targets` 仅收集了已识别的 pattern 跳转目标，但当前 case 自身的模式检查块（如上述 `LOAD_CONST(('key',)) + MATCH_KEYS + COPY + POP_JUMP_FORWARD_IF_NONE`）并不在 `visited` 中，也未作为 stop_set 成员排除。

2. **`_collect_blocks_on_path` 不区分块类型**（第 926-944 行）: 该方法纯 BFS，遇到可达且不在 stop_set 的块就加入 `result`。它不识别"模式检查块"（含 `MATCH_KEYS`/`MATCH_CLASS`/`MATCH_SEQUENCE` + `COMPARE_OP`/`POP_JUMP_IF_*` 的块）与"body 块"的差异。

**字节码证据**（来自 m027 的 MatchRegion 内部结构，`_phase3d_output.txt`）:

```
Case 0:
  case_block offset=0: [RESUME, LOAD_NAME(x), MATCH_MAPPING, POP_JUMP_FORWARD_IF_FALSE(52)]
  body blocks (2):                       <- 应该只有1个body块
    block offset=20: [LOAD_CONST(('key',)), MATCH_KEYS, COPY, POP_JUMP_FORWARD_IF_NONE(48)]  <- 错误！这是模式检查块
    block offset=28: [UNPACK_SEQUENCE, SWAP, POP_TOP, POP_TOP, STORE_NAME(val), ...]          <- 真正的body
```

offset=20 的块是 `MATCH_KEYS` 模式检查块，被错误归入 body。反编译时它被当作 `if (('key',) is not None):` 生成，导致指令数从 26 涨到 30。

**反编译症状**: body 前出现多余的 `if (('key',) is not None):`、`if 2:`、`if 0:` 等条件判断，这些其实是模式检查字节码被误解为 if 语句。

---

### 根因 RC2：guard 条件块因 IfRegion 抢占而未被跳过

**影响测试**: ~10 个（m06guard_a/n/x, m16guardcomplex_a/n/x, m042, m080, m083, m106, m107）

**根因位置**:
- 文件: `core/cfg/region_ast_generator.py`
- 方法: `_generate_match()` (第 11164 行)
- 关键代码: 第 11860-11872 行 guard 块过滤逻辑

**机制分析**:

带 guard 的 case（`case X if guard:`）字节码结构为：

```
[MATCH_CLASS, COPY, POP_JUMP_FORWARD_IF_NONE]  <- 模式匹配
[UNPACK_SEQUENCE, LOAD_NAME(x), LOAD_CONST(0), COMPARE_OP(>), POP_JUMP_FORWARD_IF_FALSE]  <- guard计算块
[LOAD_CONST(None), RETURN_VALUE]  <- body
```

`_collect_guard_pattern_blocks()`（第 12467 行）能正确识别 guard 计算块（offset=14）。但 `_generate_match()` 中的过滤逻辑存在缺陷：

```python
# region_ast_generator.py 第 11864-11872 行
if block in guard_pattern_blocks:
    _gpn = self.region_analyzer.get_entry_region_for_block(block)
    if not _gpn:
        _gpn = self.region_analyzer.get_region_for_block(block)
    if _gpn and _gpn is not region and not isinstance(_gpn, MatchRegion):
        pass   # BUG: 当 IfRegion 抢占了 guard 块时，_gpn 是 IfRegion，走此分支不跳过
    else:
        self.generated_blocks.add(block)
        continue
```

当 IfRegion 抢占了 guard 计算块时，`_gpn` 返回 IfRegion（不是 MatchRegion），条件 `_gpn is not region and not isinstance(_gpn, MatchRegion)` 为 True，执行 `pass`（不跳过），导致 guard 块被当作普通 body 块再次生成。

**字节码证据**（m06guard，`_phase3d_output.txt`）:

```
Case 0:
  guard: {'type': 'Compare', ...}   <- guard已正确识别
  body blocks (2):
    block offset=14: [UNPACK_SEQUENCE, LOAD_NAME(x), LOAD_CONST(0), COMPARE_OP(>), POP_JUMP_FORWARD_IF_FALSE(40)]  <- guard计算块，错误入body
    block offset=30: [LOAD_CONST(None), RETURN_VALUE]
```

**反编译症状**: guard 被重复生成，`case int() if (x > 0):` 之后又出现 `if (x > 0): pass`。指令数从 18 涨到 23。

---

### 根因 RC3：默认 case body 丢失 / 多 case 被合并进 if-else

**影响测试**: ~22 个（RC1 的直接连带后果）

**根因位置**: 同 RC1（`_mr_collect_case_body` + `_collect_blocks_on_path`）

**机制分析**:

这是 RC1 的连带后果。模式检查块内含 `POP_JUMP_FORWARD_IF_FALSE` 跳向下一个 case（或默认 case）。当模式检查块被错误纳入当前 case 的 body 后，这条跳转被 IfRegion 解读为 if-else 分支：then 分支是当前 body，else 分支顺着跳转目标进入下一个 case 的 body。

结果：
- 下一个 case 的 body 被"偷"进当前 case 的 else 分支
- 默认 case (`case _:`) 的 body 丢失，反编译显示 `pass`
- 多 case 结构被压扁成嵌套 if-else

**反编译症状**（m027）:

```
# 源码
case {'key': val}: y = val
case _: y = 0

# 反编译（错误）
case {'key': val}:
    if (('key',) is not None):   <- RC1: 模式检查块
        y = val
    else:
        y = 0                     <- RC3: 默认case body被偷进else
case _:
    pass                          <- RC3: 默认case body丢失
```

---

### 根因 RC4：class 模式多 case 时 IfRegion 抢占产生 `<MatchClass>` 占位符

**影响测试**: 4 个（m028, m048, m101, 以及部分 m039/m094 的情况）

**根因位置**:
- IfRegion 识别逻辑（`region_analyzer.py` 中 `_identify_*` 系列）
- 间接位置: `core/cfg/ast_generator_v2.py` 第 1488-1502 行 `MATCH_CLASS` 指令处理

**机制分析**:

当 class 模式存在多个 case 时，后续 case 的 `MATCH_CLASS` 指令所在块被 IfRegion 抢占（IfRegion 识别优先级高于 MatchRegion 对未归约块的处理）。IfRegion 处理 `MATCH_CLASS` 指令时，将其转为 `{'type': 'MatchClass', ...}` 字典，最终 `str()` 输出为字面量 `<MatchClass>`，导致语法错误。

**反编译症状**（m028）:

```
case Point(x=0, y=0):
    if 0:
        y = 1
    else:
        if <MatchClass>:     <- RC4: 占位符，语法错误
            y = (x + y)
            return None
        y = 0
```

---

### 根因 RC5：星号模式（star pattern）处理错误

**影响测试**: 2 个（m026, m100）

**根因位置**:
- `core/cfg/pattern_parser.py`（星号模式解析）
- `core/cfg/code_generator.py`（星号模式代码生成）

**机制分析**:

`case [1, *rest]` 的星号模式在解析或代码生成阶段出错。m026 产生 `() = ` 空赋值（语法错误），m100 产生 `(rest,) = {}` 错误赋值。根因在于星号模式的 `MatchStar` 节点在重组 body 字节码时与 `UNPACK_SEQUENCE`/`BUILD_MAP` 的栈操作错位。

**反编译症状**（m026）:

```
if 1:
    () =        <- RC5: 空赋值，语法错误
```

---

### 根因 RC6：class 模式跳转参数偏移 2 字节

**影响测试**: 6 个（m13matchclassargs_a/n/x, m30matchclassmultiattr_a/n/x）

**根因位置**: class 模式 body 字节码重组时的跳转目标计算

**机制分析**:

这 6 个测试的指令数完全一致（如 m13: 30→30），但 `POP_JUMP_FORWARD_IF_NONE` 的 argval 偏移 2 字节（如 36 vs 38, 32 vs 34）。原因是 class 模式的模式检查块重组时，多出或少算了一条 2 字节指令的偏移，导致跳转目标地址整体平移。

**错误信息**（m13）:

```
AssertionError: 指令6参数不匹配: 36 vs 38 (op=POP_JUMP_FORWARD_IF_NONE)
```

这是最轻微的缺陷，指令序列完全正确，仅跳转参数差 2 字节。

---

## 三、代表性字节码对比

### 对比 1: m027（Mapping 模式，RC1+RC3）

**源码**:
```python
match x:
    case {'key': val}:
        y = val
    case _:
        y = 0
```

**反编译结果（错误）**:
```python
match x:
    case {'key': val}:
        if (('key',) is not None):   # RC1: 模式检查块(MATCH_KEYS)被当作if条件
            y = val
        else:
            y = 0                     # RC3: 默认case body被偷进else
    case _:
        pass                          # RC3: 默认case body丢失
```

**字节码对比**（orig=26, recomp=30，多4条）:

```
 9: POP_JUMP_FORWARD_IF_NONE(48)  | POP_JUMP_FORWARD_IF_NONE(60)   * argval diff *
...
15: LOAD_NAME(val)                 | LOAD_CONST(('key',))            *** OPCODE DIFF ***  <- RC1: 模式检查块插入
16: STORE_NAME(y)                  | POP_JUMP_FORWARD_IF_NONE(52)    *** OPCODE DIFF ***
17: LOAD_CONST(None)               | LOAD_NAME(val)                  *** OPCODE DIFF ***
18: RETURN_VALUE(None)             | STORE_NAME(y)                   *** OPCODE DIFF ***
19: POP_TOP(None)                  | LOAD_CONST(None)                *** OPCODE DIFF ***
20: POP_TOP(None)                  | RETURN_VALUE(None)              *** OPCODE DIFF ***
21: POP_TOP(None)                  | LOAD_CONST(0)                   *** OPCODE DIFF ***  <- RC3: 默认body平移
22: LOAD_CONST(0)                  | STORE_NAME(y)                   *** OPCODE DIFF ***
```

---

### 对比 2: m06guard（Guard 模式，RC2）

**源码**:
```python
match x:
    case int() if x > 0:
        pass
```

**反编译结果（错误）**:
```python
match x:
    case int() if (x > 0):
        if (x > 0):    # RC2: guard重复生成
            pass
```

**字节码对比**（orig=18, recomp=23，多5条）:

```
10: COMPARE_OP(>)                  | COMPARE_OP(>)
11: LOAD_CONST(None)               | LOAD_NAME(x)                   *** OPCODE DIFF ***  <- RC2: guard重复
12: RETURN_VALUE(None)             | LOAD_CONST(0)                  *** OPCODE DIFF ***
13: POP_TOP(None)                  | COMPARE_OP(>)                  *** OPCODE DIFF ***
14: LOAD_CONST(None)               | LOAD_CONST(None)
15: RETURN_VALUE(None)             | RETURN_VALUE(None)
```

---

### 对比 3: m028（Class 多 case，RC4 语法错误）

**源码**:
```python
match x:
    case Point(x=0, y=0):
        y = 1
    case Point(x=x, y=y):
        y = x + y
    case _:
        y = 0
```

**反编译结果（语法错误）**:
```python
match x:
    case Point(x=0, y=0):
        if 0:
            y = 1
        else:
            if <MatchClass>:    # RC4: 占位符，SyntaxError
                y = (x + y)
                return None
            y = 0
    case Point(x=x, y=y):
        pass
    case _:
        pass
```

无法进行字节码对比（重编译失败）。

---

### 对比 4: m013（Sequence 模式，RC1+RC3）

**源码**:
```python
match x:
    case (1, 2):
        y = 1
    case _:
        y = 0
```

**反编译结果（错误）**:
```python
match x:
    case [1, 2]:
        if 2:            # RC1: 序列模式检查块(LOAD_CONST 2, COMPARE_OP ==)被当作if条件
            y = 1
        else:
            y = 0        # RC3: 默认body被偷进else
    case _:
        pass
```

**字节码对比**（orig=20, recomp=18，少2条 — 默认body被吞）:

```
10: COMPARE_OP(==)                 | COMPARE_OP(==)
11: LOAD_CONST(1)                  | LOAD_CONST(1)
12: STORE_NAME(y)                  | STORE_NAME(y)
13: LOAD_CONST(None)               | LOAD_CONST(None)
14: RETURN_VALUE(None)             | RETURN_VALUE(None)
15: POP_TOP(None)                  | POP_TOP(None)
16: LOAD_CONST(0)                  | LOAD_CONST(None)               * argval diff *  <- RC3: 默认body丢失
17: STORE_NAME(y)                  | RETURN_VALUE(None)             *** OPCODE DIFF ***
18: LOAD_CONST(None)               | <none>                         *** LENGTH DIFF ***
19: RETURN_VALUE(None)             | <none>                         *** LENGTH DIFF ***
```

---

### 对比 5: m026（Sequence 星号模式，RC5 语法错误）

**源码**:
```python
match x:
    case [1, 2]:
        y = 1
    case [1, *rest]:
        y = 2
    case _:
        y = 0
```

**反编译结果（语法错误）**:
```python
match x:
    case [1, 2]:
        if 2:
            y = 1
        else:
            if True:
                if 1:
                    () =       # RC5: 星号模式生成空赋值，SyntaxError
            y = 2
            y = 0
    case [1, *rest]:
        pass
    case _:
        pass
```

无法进行字节码对比（重编译失败）。

---

### 对比 6: m084（多 case Sequence，RC1+RC3 复合）

**源码**:
```python
match data:
    case ['add', x, y]: result = x + y
    case ['sub', x, y]: result = x - y
    case ['mul', x, y]: result = x * y
    case ['div', x, y] if y != 0: result = x / y
    case _: result = None
```

**反编译结果（错误）**:
```python
match data:
    case ['add', x, y]:
        if 'add':                # RC1
            result = (x + y)
        else:
            if True: pass
            elif True: pass
            elif True: pass
            if 'sub':            # RC3: 后续case被偷进else
                result = (x - y)
            elif 'mul':
                result = (x * y)
            elif 'div':
                if (y != 0):     # RC2: guard重复
                    result = (x / y)
                else:
                    result = None
    case ['sub', x, y]: pass     # RC3: body丢失
    ...
```

**字节码对比**（orig=83, recomp=69）: 从指令32开始全面错位，后续 case 的 body 被前置进 else 分支。

---

### 对比 7: m13matchclassargs_x（Class 模式，RC6 参数偏移）

**源码**:
```python
match x:
    case int(1):
        pass
    case int(2):
        pass
```

**字节码对比**（orig=30, recomp=30，指令数一致）:

```
 7: POP_JUMP_FORWARD_IF_NONE(36)  | POP_JUMP_FORWARD_IF_NONE(38)    * argval diff *  <- RC6: 偏移2字节
19: POP_JUMP_FORWARD_IF_NONE(66)  | POP_JUMP_FORWARD_IF_NONE(68)    * argval diff *  <- RC6: 偏移2字节
```

指令序列完全匹配，仅跳转参数差 2。

---

## 四、修复建议（文件 / 方法 / 行号）

### 修复 RC1：在 `_collect_blocks_on_path` 或 `_mr_collect_case_body` 中过滤模式检查块

**文件**: `core/cfg/region_analyzer.py`
**方法**: `_mr_collect_case_body()` (第 7774 行) 与 `_collect_blocks_on_path()` (第 926 行)
**关键行**: 7883-7891（stop_set 构造）、7890（BFS 调用）

**建议方案**（二选一）:

**方案 A（推荐，改 stop_set 构造）**: 在第 7885 行构造 stop_set 时，显式将当前 case 的模式检查块加入 stop_set。模式检查块的识别特征：块内含 `MATCH_KEYS`/`MATCH_CLASS`/`MATCH_SEQUENCE`/`MATCH_MAPPING` 且以 `POP_JUMP_FORWARD_IF_NONE`/`POP_JUMP_FORWARD_IF_FALSE` 结尾，且这些块在 `case_blocks` 已收集的 pattern 计算路径上。

**方案 B（改 BFS）**: 在 `_collect_blocks_on_path`（第 926 行）增加 `pattern_check_blocks` 参数，BFS 时跳过这些块。识别方式：块含 `MATCH_*` 指令或纯 `LOAD_CONST + COMPARE_OP + POP_JUMP_IF_*`（无 STORE 等副作用）。

**验证标准**: m027 的 Case 0 body blocks 应从 2 个（含 offset=20 模式检查块）降为 1 个（仅 offset=28 真正 body）。

---

### 修复 RC2：修正 `_generate_match` 中 guard 块的 IfRegion 抢占判断

**文件**: `core/cfg/region_ast_generator.py`
**方法**: `_generate_match()` (第 11164 行)
**关键行**: 11864-11872

**建议方案**: 第 11868 行的判断 `if _gpn and _gpn is not region and not isinstance(_gpn, MatchRegion): pass` 逻辑错误。当 guard 块被 IfRegion 抢占时，应仍然跳过该块（因为它已被识别为 guard，不应作为 body 重复生成）。

修改建议：将第 11868-11869 行的 `pass` 分支改为 `self.generated_blocks.add(block); continue`，即无论 guard 块被哪个区域抢占，只要它已在 `guard_pattern_blocks` 中就跳过。

**验证标准**: m06guard 反编译结果应仅为 `case int() if (x > 0): pass`，不再有重复的 `if (x > 0):`。

---

### 修复 RC3：随 RC1 修复自动消除

**说明**: RC3 是 RC1 的直接连带后果。模式检查块不再误入 body 后，其 `POP_JUMP_FORWARD_IF_FALSE` 跳转不会被误解为 if-else 分支，默认 case body 不再被偷进 else。无需独立修复。

**验证标准**: m027 反编译结果应恢复为 `case _: y = 0`（而非 `pass`）。

---

### 修复 RC4：阻止 IfRegion 抢占 MatchRegion 的 case 块

**文件**: `core/cfg/region_analyzer.py`
**方法**: IfRegion 识别逻辑（`_identify_*` 系列，需进一步定位具体识别方法）
**间接相关**: `core/cfg/ast_generator_v2.py` 第 1488-1502 行 `MATCH_CLASS` 处理

**建议方案**: 在 IfRegion 识别时，增加前置检查：若候选块含 `MATCH_CLASS`/`MATCH_KEYS`/`MATCH_SEQUENCE`/`MATCH_MAPPING` 指令，且该块属于某个待识别的 MatchRegion 范围，则 IfRegion 不应抢占该块。需让 MatchRegion 识别优先于 IfRegion，或在 IfRegion 识别时排除含 MATCH_* 指令的块。

**验证标准**: m028/m048/m101 反编译结果不再出现 `<MatchClass>` 字面量。

---

### 修复 RC5：修正星号模式（MatchStar）的解析与代码生成

**文件**: `core/cfg/pattern_parser.py`、`core/cfg/code_generator.py`
**方法**: 星号模式相关解析（`_extract_sequence_pattern` 第 980 行附近）与生成（`_generate_match_pattern` 第 2633 行附近）

**建议方案**: 排查 `MatchStar` 节点在 `[1, *rest]` 模式下的栈操作。`UNPACK_SEQUENCE` 后的星号捕获应生成 `STORE_NAME(rest)`，而非空赋值 `() =`。需检查 pattern dict 中 `MatchStar` 是否被正确传递到 code_generator，以及 body 重组时 `BUILD_MAP`/`UNPACK_SEQUENCE` 的栈深度计算。

**验证标准**: m026 反编译结果应生成 `case [1, *rest]: y = 2`，无 `() =` 语法错误。

---

### 修复 RC6：修正 class 模式跳转参数偏移

**文件**: `core/cfg/region_analyzer.py` 或 `core/cfg/code_generator.py`
**方法**: class 模式 body 重组时的跳转目标计算

**建议方案**: 排查 class 模式（`MATCH_CLASS`）在重组 case 字节码时，跳转目标地址的计算基准。偏移恒为 2 字节（一条指令宽度），疑为多算或少算了一条 `COPY`/`POP_TOP` 指令的偏移。需对比 m13 原始字节码与重组字节码在 `POP_JUMP_FORWARD_IF_NONE` 前的指令序列，定位多出的 2 字节来源。

**验证标准**: m13/m30 的 `POP_JUMP_FORWARD_IF_NONE` argval 应与原始一致（36/66 而非 38/68）。

---

## 五、优先级建议

### 优先级排序（按影响测试数 + 修复依赖关系）

| 优先级 | 根因 | 影响测试数 | 理由 |
|--------|------|-----------|------|
| **P0** | RC1 模式检查块误入body | ~30 | 核心缺陷，影响最多测试；修复后 RC3 自动消除，合计解决 ~36 个测试（82%） |
| **P1** | RC2 guard块未跳过 | ~10 | 独立缺陷，修复简单（改1处判断）；与 RC1 修复无依赖，可并行 |
| **P2** | RC4 `<MatchClass>`占位符 | 4 | 语法错误，影响严重但测试数少；依赖 IfRegion 抢占逻辑调整 |
| **P3** | RC5 星号模式错误 | 2 | 语法错误，需深入 pattern_parser；与 RC1-4 无依赖 |
| **P4** | RC6 跳转参数偏移 | 6 | 最轻微（指令序列正确，仅参数差2字节）；建议最后修复 |

### 修复路径建议

1. **第一轮**: 修复 RC1（P0）+ RC2（P1），预期解决 ~36 个测试
2. **第二轮**: 修复 RC4（P2），解决 4 个语法错误测试
3. **第三轮**: 修复 RC5（P3）+ RC6（P4），解决剩余 8 个测试
4. **验证**: 每轮修复后重跑 44 个测试，确认通过率提升

### 预期最终效果

- 修复 RC1+RC2: 通过率从 0/44 提升至 ~36/44 (82%)
- 修复 RC4: 通过率提升至 ~40/44 (91%)
- 修复 RC5+RC6: 通过率提升至 44/44 (100%)

---

## 六、附录：关键代码位置索引

| 文件 | 方法 | 行号 | 作用 |
|------|------|------|------|
| `region_analyzer.py` | `_collect_blocks_on_path` | 926 | BFS收集路径块（RC1底层） |
| `region_analyzer.py` | `_identify_match_regions` | 7073 | MatchRegion主识别 |
| `region_analyzer.py` | `_mr_collect_case_body` | 7774 | case body收集（RC1核心） |
| `region_analyzer.py` | `_mr_collect_case_body_by_offset` | 7628 | 按偏移收集body（备用路径） |
| `region_analyzer.py` | `_mr_compute_case_body_start_indices` | 7427 | 计算body起始索引 |
| `region_analyzer.py` | `_mr_find_case_jump_instruction` | 7555 | 查找case跳转指令 |
| `region_analyzer.py` | `_mr_resolve_or_guard_jump` | 7566 | OR guard短路跳转 |
| `region_analyzer.py` | `_mr_finalize_match_region` | 7677 | 合并OR模式 |
| `region_ast_generator.py` | `_generate_match` | 11164 | match AST生成（RC2核心） |
| `region_ast_generator.py` | `_collect_guard_pattern_blocks` | 12467 | guard块识别 |
| `region_ast_generator.py` | (guard过滤逻辑) | 11860-11872 | guard块过滤（RC2 bug点） |
| `ast_generator_v2.py` | (MATCH_CLASS处理) | 1488-1502 | MATCH_CLASS转dict（RC4间接） |
| `pattern_parser.py` | `parse_case_pattern` | 47 | 模式解析入口 |
| `pattern_parser.py` | `_extract_sequence_pattern` | 980 | 序列模式解析（RC5） |
| `pattern_parser.py` | `_extract_class_pattern` | 1259 | 类模式解析 |
| `pattern_parser.py` | `_extract_mapping_pattern` | 1466 | 映射模式解析 |
| `code_generator.py` | `_generate_match` | 2579 | match代码生成 |
| `code_generator.py` | `_generate_match_pattern` | 2633 | 模式字符串生成（RC5） |

---

## 七、分析过程说明

本报告基于以下分析脚本与输出（均为只读分析，未修改任何源码）:

- `_phase1_run_tests.py` / `_phase1_output.txt`: 批量运行 44 个测试，提取错误类型与失败信息
- `_phase2_analysis.py` / `_phase2_output.txt`: 22 个代表性测试的字节码逐条对比
- `_phase3_analysis.py` / `_phase3_output.txt`: 反编译结果与源码对比
- `_phase3d_analysis.py` / `_phase3d_output.txt`: MatchRegion 内部结构（case_blocks/bodies/patterns/guards）

所有根因结论均有字节码证据与 MatchRegion 内部结构数据支撑。
