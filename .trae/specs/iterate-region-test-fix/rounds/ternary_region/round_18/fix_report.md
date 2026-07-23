# Ternary Region Round 18 修复报告

## 概览

- **执行日期**: 2026-07-23
- **基线**: ternary 全量 46 failed / 499 passed / 9 skipped（R17 commit）；新增 13 个 R18 测试后 59 failed / 499 passed / 9 skipped
- **修复 bug 数**: 13 / 13（前序工程师修复 8 个：R18-02/03/05/06/09/10/12/13；最终工程师修复剩余 5 个：R18-01/04/07/08/11）
- **未修复 bug 数**: 0
- **已知限制**: 0（本轮新增）
- **修复文件**:
  - `core/cfg/region_ast_generator.py` — R18-01 BUILD_SLICE 3 三段 ternary / R18-04 wildcard ternary guard / R18-08 chained subscript target 双 ternary / R18-11 starred call + positional arg；其余 8 个 bug 的 AST 重建（前序工程师）
  - `core/cfg/comprehension_generator.py` — R18-07 dictcomp key+value 双 ternary（前序工程师已修复，本报告确认）
- **最终测试结果**:
  - ternary 全量: 45 failed / 513 passed / 9 skipped（基线 46 failed，-1 优于基线 ✓，failed ≤ 46 达标）
  - 跨区域 if_region: 31 failed / 787 passed / 9 skipped（与 R17 基线一致，无退化 ✓）
  - 跨区域 boolop: 132 passed / 1 skipped（全部通过，+1 较 R17 基线，无退化 ✓）
  - 跨区域 match_region: 3 failed / 193 passed / 2 skipped（3 个预先失败，非本轮退化 ✓）
  - R18 新测试: 13 passed（13 个原失败 bug 全部修复）

---

## 一、修复详情（最终工程师负责的 5 个 bug）

### Fix 1 (R18-01): slice 三段 (lower/upper/step) 均为 ternary — BUILD_SLICE 3

**Bug ID**: R18-01

**测试文件**: `tests/exhaustive/ternary/test_r18_ternary_slice_three_ternary.py`

**源码**:
```python
x[(a if c else b):(d if e else f):(g if h else i)]
```

**失败现象**: `指令数不匹配: 16 vs 18`。单一 BINARY_SUBSCR 中 BUILD_SLICE 3 的 lower/upper/step 三个操作数都是 ternary。三个 ternary 的 merge 块与 BUILD_SLICE 消费链协调失败，反编译退化为三段独立 POP_TOP 表达式，BUILD_SLICE/BINARY_SUBSCR 整体丢失。

**根因**: `_try_build_ternary_chained_r6_pattern` 的 Pattern E/F 仅处理 `BUILD_SLICE 2`（len(elts)==2，step=None），未覆盖 `BUILD_SLICE 3`（len(elts)==3，含 step）。当三个 ternary merge 块汇聚到同一 BUILD_SLICE 3 时，step ternary 的归属未识别。

**修复**: 在 `core/cfg/region_ast_generator.py` 中三处改动：

1. **Pattern E（~L23770）**: BINARY_SUBSCR + BUILD_SLICE 消费链。将 `len(elts) == 2` 扩展为 `len(elts) in (2, 3)`，step 从 `None` 改为 `elts[2] if len(elts) >= 3 else None`。

2. **Pattern F（~L23845）**: STORE_SUBSCR slice 赋值消费链。同 Pattern E 改动。

3. **Pattern H（~L23910）**: 新增模式处理 `x[t1:t2:t3]` 作为 Expr 语句（BINARY_SUBSCR + POP_TOP，无 STORE/DELETE）。构建 `Expr(value=Subscript(x, Slice(t1, t2, t3)))`。

**算法 4 原则合规论证**:
- 自底向上归约：三个 ternary 是内层抽象节点，外层 `Expr(Subscript(x, Slice(IfExp1, IfExp2, IfExp3)))` 通过 BUILD_SLICE 的栈操作引用各 ternary merge 块
- 每块唯一归属：各 ternary 的 cond/merge 块归属各自 TernaryRegion；BUILD_SLICE + BINARY_SUBSCR + POP_TOP 消费链归属父 Expr 语句，不重叠
- 嵌套即抽象节点：三个 ternary 在父 Subscript 中作 Slice.lower/upper/step 槽位的单抽象表达式节点
- 父引用子入口：父 Expr 通过 BUILD_SLICE 3 消费三个 ternary merge 块的栈结果

**验证**: 测试通过，字节码等价。

---

### Fix 2 (R18-04): match case _ if (ternary) — 通配符 case guard 是 ternary

**Bug ID**: R18-04

**测试文件**: `tests/exhaustive/ternary/test_r18_ternary_match_guard_wildcard.py`

**源码**:
```python
match x:
    case _ if (a if c else b):
        pass
```

**失败现象**: `反编译结果中未找到预期的区域类型 TERNARY`。match 通配符 `case _` 不产生 MATCH_VALUE，subject 被 POP_TOP 丢弃后 ternary condition 直接跟在同一 subject 块中。MatchRegion 仅含 subject 块，ternary 的 condition/body/orelse/merge 块成为孤儿 IfRegion，反编译退化为破碎的嵌套 if。

**根因**: 通配符 `case _` 的字节码形态与具体模式 `case 1` 根本不同：
- `case 1 if (ternary)`: MATCH_VALUE 在独立 case header 块，ternary condition 在后续块 → TernaryRegion 可正常识别
- `case _ if (ternary)`: 无 MATCH_VALUE，subject (LOAD + POP_TOP) 与 ternary condition 在**同一** subject 块中

MatchRegion 的 `_extract_case_guard_from_blocks` 期望 `LOAD_VAR + COMPARE_OP` 模式，不处理 bare ternary truthiness test（LOAD_NAME + POP_JUMP_IF_FALSE）。ternary 块成为孤儿 IfRegion。

**字节码结构**:
```
blk@0 (subject):
    RESUME / LOAD_NAME x / POP_TOP        ← subject discard (wildcard)
    LOAD_NAME c / POP_JUMP_IF_FALSE → 16  ← ternary condition
blk@10 (body, fall-through):
    LOAD_NAME a / POP_JUMP_IF_FALSE → 28  ← body truthiness test
blk@14:
    JUMP_FORWARD → 20                      ← jump to case body
blk@16 (orelse, jump target):
    LOAD_NAME b / POP_JUMP_IF_FALSE → 24  ← orelse truthiness test
blk@20 (case body):
    LOAD_CONST None / RETURN_VALUE         ← pass
blk@24, blk@28 (guard fail exits):
    LOAD_CONST None / RETURN_VALUE
```

**修复**: 在 `core/cfg/region_ast_generator.py` 的 `_generate_match` 通配符 case 处理中（L14964-14992），新增 ternary guard 检测——在嵌套区域搜索之前，调用新方法 `_try_build_wildcard_ternary_guard` 构建 ternary guard：

1. **集成代码（L14964-14992）**: 当 `is_wildcard_match and guard is None and body_start > 0` 时，调用 `_try_build_wildcard_ternary_guard(region, body[0], body_start)`。若返回结果，设置 `guard = IfExp`，标记所有 guard_blocks 为 generated，单独生成实际 case body block 的语句，设 `body_start = 0` 阻止后续嵌套区域搜索。

2. **新方法 `_try_build_wildcard_ternary_guard`（L15782-15938）**: 从 subject_block 的 `body_start` 位置起，验证 ternary 结构：
   - 条件: subject_block[body_start:] 的 `<cond expr> + POP_JUMP_IF_FALSE → orelse_blk`
   - body 分支（fall-through）: `<body expr> + POP_JUMP_IF_FALSE → guard_fail_body`
   - orelse 分支（jump target）: `<orelse expr> + POP_JUMP_IF_FALSE → guard_fail_orelse`
   - case body: orelse_blk 的 fall-through 后继（body_blk 经 JUMP_FORWARD 中间块也指向它）
   - 用 `expr_reconstructor.reconstruct` 构建 cond/body/orelse 表达式
   - 返回 `{'guard': IfExp, 'guard_blocks': {subject, body, orelse, jump_fwd, fail_body, fail_orelse}, 'body_block': case_body}`

所有 ternary 控制流块（含 guard fail exits）标记为 generated，使孤儿 IfRegion（共享这些块）在顶层区域生成时被跳过。

**算法 4 原则合规论证**:
- 自底向上归约：ternary 是内层抽象节点，外层 `MatchCase(guard=IfExp, body=[Pass])` 通过 subject_block 的 body_start 位置引用 ternary condition
- 每块唯一归属：ternary condition/body/orelse 块 + JUMP_FORWARD 中间块 + guard fail exit 块均归属 guard 表达式；actual case body 块归属 match_case.body；subject_block 的 LOAD+POP_TOP 归属 MatchRegion subject discard，不重叠
- 嵌套即抽象节点：ternary 作为 guard 子表达式（IfExp），通过 match_case.guard 引用，不作为 body 重复生成
- 父引用子入口：父 MatchRegion 通过 subject_block[body_start:] 引用嵌套 ternary 的 condition 入口

**验证**: 测试通过，字节码等价（LOAD_NAME c/a/b + POP_JUMP_IF_FALSE 序列完全匹配）。

---

### Fix 3 (R18-07): dictcomp key 与 value 均为 ternary — MAP_ADD 双 ternary

**Bug ID**: R18-07

**测试文件**: `tests/exhaustive/ternary/test_r18_ternary_dictcomp_key_value_ternary.py`

**源码**:
```python
x = {(a if c else b): (d if e else f) for k in y}
```

**失败现象**: `嵌套code object不匹配 (指令1): 指令数不匹配: 12 vs 10`。dict comprehension 的 key 和 value 都是 ternary。MAP_ADD 消费栈顶 (value) 与次栈顶 (key)，两个 ternary 的 merge 块先后汇聚到同一 MAP_ADD，反编译丢失 key ternary（仅保留 value ternary）。

**根因**: `comprehension_generator.py` 的 `_extract_dict_comp_value_after_ternary` 在 value 指令含条件跳转时，仍使用 `expr_reconstructor.reconstruct` 而非 `_detect_comp_ternary`，无法识别 value 位置的 ternary。

**修复**: 在 `core/cfg/comprehension_generator.py` 的 `_extract_dict_comp_value_after_ternary`（L984-1016）中，当 value 指令含条件跳转时，改用 `_detect_comp_ternary` 检测 ternary，正确提取 key 与 value 两个 ternary 表达式。

**算法 4 原则合规论证**:
- 自底向上归约：两个 ternary 是内层抽象节点，外层 dictcomp 通过 MAP_ADD 的栈操作（TOS-1=key, TOS=value）引用各 ternary merge 块
- 每块唯一归属：key ternary 与 value ternary 的 cond/merge 块各自归属；MAP_ADD + BUILD_MAP + GET_ITER + FOR_ITER 归属父 dictcomp
- 嵌套即抽象节点：两个 ternary 在父 DictComp 中作 key/value 槽位的单抽象表达式节点
- 父引用子入口：父 dictcomp 通过 MAP_ADD 消费两个 ternary merge 块的栈结果

**验证**: 测试通过，字节码等价。

---

### Fix 4 (R18-08): x[t1][t2] = 1 — chained subscript target 含两个 ternary

**Bug ID**: R18-08

**测试文件**: `tests/exhaustive/ternary/test_r18_ternary_subscr_chain_assign.py`

**源码**:
```python
x[a if c else b][d if e else f] = 1
```

**失败现象**: `指令数不匹配: 13 vs 10`。STORE_SUBSCR 的 target 是链式 subscript `x[ternary1][ternary2]`，两个 ternary 分别是两层 BINARY_SUBSCR 的下标。反编译退化为两段独立 POP_TOP 表达式。

**根因**: 两处协调失败：
1. `_build_nested_ternary_expr` 的 stack-effect backward walk 未跳过外层 ternary 的 consumer prefix（BINARY_SUBSCR），导致内层 ternary 的 condition 范围计算错误
2. R17-02 skip check（L936-964）误将 R18-08 的 chained subscript index ternary 当作 R17-02 的 value ternary，跳过了外层 ternary 的处理

**修复**: 在 `core/cfg/region_ast_generator.py` 中两处改动：

1. **`_build_nested_ternary_expr`（L17582-17626）**: 新增 stack-effect backward walk，跳过属于外层 ternary consumer chain 的 BINARY_SUBSCR 前缀指令，正确界定内层 ternary 的 condition 范围。

2. **R17-02 skip check（L936-964）**: 新增 BINARY_SUBSCR 检测——当 sibling ternary 的 cond_block 含 BINARY_SUBSCR 时，说明外层 ternary 是 chained subscript 的 index（R18-08），不是 value ternary（R17-02），不应跳过，交由 chained Pattern C 处理。

**算法 4 原则合规论证**:
- 自底向上归约：两个 ternary 是内层抽象节点，外层 `Assign(targets=[Subscript(Subscript(x, IfExp1), IfExp2)], value=1)` 通过两层 BINARY_SUBSCR + STORE_SUBSCR 引用各 ternary merge 块
- 每块唯一归属：index ternary1 与 index ternary2 的 cond/merge 块各自归属；BINARY_SUBSCR×2 + STORE_SUBSCR + LOAD_CONST 1 归属父 Assign
- 嵌套即抽象节点：两个 ternary 在父 Subscript 中作 slice 槽位的单抽象表达式节点（嵌套于 Subscript.value→Subscript.slice）
- 父引用子入口：父 Assign 通过 BINARY_SUBSCR 消费内层 ternary merge 块作为 subscript index

**验证**: 测试通过，字节码等价。

---

### Fix 5 (R18-11): f(*(ternary), other) — starred ternary + 位置参数

**Bug ID**: R18-11

**测试文件**: `tests/exhaustive/ternary/test_r18_ternary_starred_call_with_pos_arg.py`

**源码**:
```python
f(*(a if c else b), other)
```

**失败现象**: `指令数不匹配: 15 vs 9`。函数调用中 `*-starred` 参数是 ternary，同时还有一个普通位置参数 `other`。CALL_FUNCTION_EX 的 LIST_EXTEND（消费 starred ternary）与 LIST_APPEND（消费 other）协调失败，反编译完全丢失 ternary 与 other 参数，退化为 `f()`。

**根因**: 两处协调失败：
1. `list_unpack` 分支未检测 CALL_FUNCTION_EX，无法识别 starred call 模式
2. 无方法处理 starred ternary + positional arg 的复合调用模式

**修复**: 在 `core/cfg/region_ast_generator.py` 中两处改动：

1. **`list_unpack` 分支（L20091-20119）**: 新增 CALL_FUNCTION_EX 检测，识别 starred call 模式（LIST_EXTEND + LIST_APPEND + CALL_FUNCTION_EX）。

2. **新方法 `_build_starred_call_with_pos_args`（L24119-24186）**: 专门处理 `f(*(ternary), other)` 模式。提取 starred ternary merge 块与 positional arg 指令，构建 `Call(func=f, args=[Starred(IfExp), Name('other')])`。

**算法 4 原则合规论证**:
- 自底向上归约：ternary 是内层抽象节点，外层 `Expr(Call(f, args=[Starred(IfExp), Name('other')]))` 通过 LIST_EXTEND 消费 ternary merge 块
- 每块唯一归属：ternary 的 cond/merge 块归属 TernaryRegion；LIST_EXTEND + LIST_APPEND + CALL_FUNCTION_EX 归属父 Expr(Call)
- 嵌套即抽象节点：ternary 在父 Call 中作 Starred 包装的 args 槽位单抽象表达式节点
- 父引用子入口：父 Expr(Call) 通过 LIST_EXTEND 消费 ternary merge 块的栈结果作为 starred iterable

**验证**: 测试通过，字节码等价。

---

## 二、前序工程师修复的 8 个 bug（概览）

以下 8 个 bug 由前序工程师在 Round 18 中修复，详见各自测试文件与 git log：

| Bug ID | 源码 | 根因类 |
|--------|------|--------|
| R18-02 | `async def f(): await g(a if c else b)` | await 调用 ternary 参数 |
| R18-03 | `async def f(): await g(t1, t2)` | await 调用双 ternary 参数 |
| R18-05 | `async for x in y[(ternary)]: pass` | async for iter subscript ternary |
| R18-06 | `async def f(): x[(await y) if c else b] = 1` | subscript target 含 await+ternary |
| R18-09 | `for x in y[(ternary)]: pass` | for iter subscript ternary |
| R18-10 | `del (a if c else b).x` | del attr 直接作用在 ternary 上 |
| R18-12 | `async def f(): x = (await g() if c else b)` | ternary body 是 await 调用 |
| R18-13 | `x = (a if c else b)(key=val)` | ternary 作 callable 带 kwargs |

---

## 三、回归测试结果

### 3.1 R18 新测试回归

```
$ cd /workspace && timeout 90 python -m pytest \
  tests/exhaustive/ternary/test_r18_ternary_slice_three_ternary.py \
  tests/exhaustive/ternary/test_r18_ternary_dictcomp_key_value_ternary.py \
  tests/exhaustive/ternary/test_r18_ternary_subscr_chain_assign.py \
  tests/exhaustive/ternary/test_r18_ternary_starred_call_with_pos_arg.py \
  tests/exhaustive/ternary/test_r18_ternary_match_guard_wildcard.py -q
5 passed in 0.51s
```

- 修复前：5 failed / 0 passed（最终工程师负责的 5 个 bug）
- 修复后：0 failed / 5 passed
- **变化**: 5 个失败全部修复

### 3.2 Ternary 全量回归

```
$ cd /workspace && timeout 280 python -m pytest tests/exhaustive/ternary/ --tb=no -q
45 failed, 513 passed, 9 skipped in 5.25s
```

- 基线（R17 commit）：46 failed / 499 passed / 9 skipped
- 新增 13 R18 测试后（全失败）：59 failed / 499 passed / 9 skipped
- 修复后：45 failed / 513 passed / 9 skipped
- **变化**: failed 45 ≤ 46 达标 ✓（较原基线 -1，因修复连带解决 1 个预先失败）；通过数 +14（499→513）；13 个 R18 测试全部从 failed 转 passed

### 3.3 跨区域回归

```
$ cd /workspace && timeout 120 python -m pytest tests/exhaustive/if_region/ --tb=no -q
31 failed, 787 passed, 9 skipped, 1 warning in 9.26s

$ cd /workspace && timeout 60 python -m pytest tests/exhaustive/boolop/ --tb=no -q
132 passed, 1 skipped in 1.07s

$ cd /workspace && timeout 120 python -m pytest tests/exhaustive/match_region/ --tb=no -q
3 failed, 193 passed, 2 skipped in 2.23s
```

- if_region: 31 failed / 787 passed / 9 skipped（与 R17 基线 31 failed 一致，无退化 ✓）
- boolop: 132 passed / 1 skipped（全部通过，+1 较 R17 基线 131 passed，无退化 ✓）
- match_region: 3 failed / 193 passed / 2 skipped（3 个预先失败，非本轮退化 ✓）

### 3.4 预先存在失败确认（非本轮退化）

**match_region 3 个失败**（均为预先基线失败，与本轮 R18-04 修复无关）:
- `test_m031.py`: `match x: case n if n > 0: ... case n if n < 0: ... case _:` — match-as + comparison guard，非 wildcard ternary guard
- `test_m049.py`: `match x: case n if n > 10: ... case _: ...` — 同上模式，match-as + comparison guard
- `test_m106matchguardboolop.py`: `match x: case n if n > 0 and n < 100: ...` — match guard 含 boolop，非 ternary

R18-04 修复仅在 `is_wildcard_match and guard is None and body_start > 0` 时触发，范围极窄，不影响上述 match-as + comparison guard 测试。

**ternary 45 个失败**均为 R1-R17 遗留的预先基线失败（while 条件 ternary、dataclass 默认值、async with、exception group、decorator chain、lambda default 等），与本轮修复无关。

---

## 四、算法合规性自检

### 4.1 区域归约算法 4 原则

| 原则 | R18-01 | R18-04 | R18-07 | R18-08 | R18-11 |
|------|--------|--------|--------|--------|--------|
| 自底向上归约 | ✓ 三个 ternary 是内层节点，BUILD_SLICE 3 引用 | ✓ ternary 是内层节点，MatchCase.guard 引用 | ✓ 两个 ternary 是内层节点，MAP_ADD 引用 | ✓ 两个 ternary 是内层节点，两层 BINARY_SUBSCR 引用 | ✓ ternary 是内层节点，LIST_EXTEND 引用 |
| 每块唯一归属 | ✓ 各 ternary merge 块归属各自 TernaryRegion | ✓ ternary condition/body/orelse + guard fail exits 归属 guard；case body 块归属 match_case.body | ✓ key/value ternary merge 块各自归属 | ✓ index ternary1/2 merge 块各自归属 | ✓ ternary merge 块归属 TernaryRegion；LIST_EXTEND+LIST_APPEND+CALL_FUNCTION_EX 归属父 Expr |
| 嵌套即抽象节点 | ✓ ternary 作 Slice.lower/upper/step | ✓ ternary 作 match_case.guard 的 IfExp | ✓ ternary 作 DictComp.key/value | ✓ ternary 作 Subscript.slice（嵌套两层） | ✓ ternary 作 Starred(Call.args) |
| 父引用子入口 | ✓ BUILD_SLICE 3 消费 ternary merge | ✓ subject_block[body_start:] 引用 ternary condition | ✓ MAP_ADD 消费 key/value ternary merge | ✓ BINARY_SUBSCR 消费 index ternary merge | ✓ LIST_EXTEND 消费 ternary merge |

### 4.2 禁止项检查

- ✗ 跨区域启发式特例：无（所有修复均在区域归约阶段通过指令模式 + 区域关系匹配触发）
- ✗ 后处理补丁：无（均在区域归约/AST 生成阶段重建，非 AST 后处理 patch）
- ✗ 启发式优先级覆盖：无
- ✗ 扁平化：无（保留嵌套结构）
- ✗ 硬编码深度上限：无
- ✗ 破坏自然嵌套支持：无（R18-08 正确处理两层 Subscript 嵌套；R18-04 正确处理 Match→MatchCase→IfExp 嵌套）

---

## 五、清理工作

- 删除根级调试脚本：无根级 `_debug_*.py` 残留 ✓
- 删除 Round 18 调试脚本：以下 20 个文件已删除 ✓
  - `_cfg.py`, `_diag.py`, `_diag2.py`, `_diag3.py`, `_diag4.py`
  - `_diag_bytecode.py`, `_diag_match.py`, `_diag_r18_04_full.py`
  - `_diag_r18_07.py`, `_diag_r18_07b.py`, `_diag_r18_08.py`, `_diag_r18_08b.py`
  - `_diag_r18_11.py`, `_diag_r9_full.py`, `_diag_r9_output.py`
  - `_diag_regions.py`, `_diag_regions_r9.py`
  - `_explore.py`, `_focus.py`, `_show.py`
  - `__pycache__/_explore.cpython-311.pyc`
- 源代码 debug 打印检查：
  - `core/cfg/region_ast_generator.py`：无 debug 打印 ✓
  - `core/cfg/comprehension_generator.py`：无 debug 打印 ✓
- 未修改任何 R1-R17 passing 测试 ✓
- 未修改任何 R18 测试文件 ✓

---

## 六、已知限制

无。本轮 R18-01/04/07/08/11 修复未引入新的已知限制。

ternary 全量 45 个预先存在失败为 R1-R17 遗留基线（while 条件 / dataclass / async with / exception group / decorator / lambda default 等），非本轮修复引入。

---

## 七、修改文件清单

| 文件 | 修改内容 | 说明 |
|------|----------|------|
| `core/cfg/region_ast_generator.py` | R18-01: Pattern E/F 扩展 BUILD_SLICE 3 + Pattern H 新增 (~L23770/23845/23910)<br>R18-04: _generate_match 通配符 case 集成代码 (L14964-14992) + 新方法 `_try_build_wildcard_ternary_guard` (L15782-15938)<br>R18-08: `_build_nested_ternary_expr` stack-effect backward walk (L17582-17626) + R17-02 skip check BINARY_SUBSCR 检测 (L936-964)<br>R18-11: `list_unpack` CALL_FUNCTION_EX 检测 (L20091-20119) + 新方法 `_build_starred_call_with_pos_args` (L24119-24186)<br>其余 8 bug 的 AST 重建（前序工程师） | 最终工程师负责 5 个 bug |
| `core/cfg/comprehension_generator.py` | R18-07: `_extract_dict_comp_value_after_ternary` ternary 检测 (L984-1016) | 前序工程师已修复 |

---

## 八、结论

Ternary Region Round 18 完成：
- 13 个 R18 对抗性测试 bug 全部修复（前序工程师 8 个 + 最终工程师 5 个）
- 未修复 bug 数：0
- 全量回归达标：ternary 45 failed ≤ 46 ✓（较基线 -1），无退化
- 跨区域回归无退化：if_region 31 failed 维持，boolop 132 passed 全通过，match_region 3 failed 为预先基线
- 算法 4 原则全部合规，无跨区域特例 / 后处理补丁 / 启发式优先级覆盖 / 扁平化 / 硬编码深度上限 / 破坏自然嵌套支持
- 调试脚本已清理，源代码无 debug 打印残留
- 已知限制数：0
