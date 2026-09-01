# IF Region Round 13 — 修复报告

## 修复概览

- **测试总数**：15 个（11 失败 + 4 通过）
- **已修复**：8 个（类别 1: 2, 类别 2: 1, 类别 3: 5）
- **已知限制**：3 个（类别 4: 多三元 boolop 归并错乱）
- **IF 全量回归**：676 passed / 4 failed (1 legacy + 3 cat4 已知限制) / 4 skipped
- **CFM 全量回归**：4 failed / 323 passed / 11 skipped（与基线一致，无退化）

## 修改文件清单

| 文件 | 改动 |
|------|------|
| `core/cfg/region_ast_generator.py` | +278 行：扩展 `_WRAPPING_OPS`、FORMAT_VALUE/BINARY_OP 处理器、新增 `_try_build_nested_ternary_as_if_cond` |
| `core/cfg/ast_generator_v2.py` | +63 行：重写 `_parse_comprehension_from_code` 委托给 ComprehensionGenerator |
| `core/cfg/comprehension_generator.py` | +7 行：`_detect_comp_ternary` 添加 BACKWARD 检查 |

## 类别 1: _WRAPPING_OPS 集合扩展（2 个错误）

### Error 5: 三元 in f-string 丢失 FORMAT_VALUE
- **测试**：test_adv13_ternary_in_fstring_cond.py
- **源码**：`if f"{a if c else b}" == "x": pass`
- **现象**：FORMAT_VALUE 被跳过，输出 `(a if c else b) == 'x'`
- **修复**：将 FORMAT_VALUE 加入 `_WRAPPING_OPS`；在 `_sim_wrapping_instr` 添加 FORMAT_VALUE 处理器，构造 FormattedValue 节点
- **状态**：✓ 已修复

### Error 10: 三元 + BINARY_OP 丢失 BINARY_OP
- **测试**：test_adv13_ternary_binary_op_cond.py
- **源码**：`if (a if c else b) + 1 > 0: pass`
- **现象**：BINARY_OP 被跳过，输出 `(a if c else b) > 0`
- **修复**：将 BINARY_OP 加入 `_WRAPPING_OPS`；在 `_sim_wrapping_instr` 添加 BINARY_OP 处理器，弹出两操作数构造 BinOp 节点
- **状态**：✓ 已修复

## 类别 2: 嵌套三元 else 分支形式（1 个错误）

### Error 11: 嵌套三元（else 分支含内层）作 if 条件退化为 Expr
- **测试**：test_adv13_nested_ternary_bare_cond.py
- **源码**：`if a if b else c if d else e: pass` (Python 解析为 `if (a if b else (c if d else e)): pass`)
- **现象**：if 关键字与条件分支完全丢失，只剩孤立的 `(a if b else c if d else e)` Expr 语句
- **修复**：新增 `_try_build_nested_ternary_as_if_cond` 方法（行 16692-16841），检测嵌套三元 orelse 形式作 if 条件的模式；在 `_generate_ternary` 中调用该方法（行 15865-15873）
- **状态**：✓ 已修复

## 类别 3: 推导式 code object 重建缺陷（5 个错误）

### Error 1: walrus + listcomp filter 丢失
- **测试**：test_adv13_walrus_listcomp_cond.py
- **源码**：`if (x := [i for i in range(10) if i > 5]): pass`
- **现象**：listcomp filter `if i > 5` 完全丢失
- **状态**：✓ 已修复

### Error 4: setcomp 直接作 if 条件 filter 丢失
- **测试**：test_adv13_setcomp_direct_cond.py
- **源码**：`if {x for x in y if x > 0}: pass`
- **现象**：setcomp filter `if x > 0` 完全丢失
- **状态**：✓ 已修复

### Error 2: dictcomp 直接作 if 条件产生 `<>` 占位符
- **测试**：test_adv13_dictcomp_direct_cond.py
- **源码**：`if {k: v for k, v in items}: pass`
- **现象**：key/value 变 `<>` 占位符
- **状态**：✓ 已修复

### Error 3: walrus + dictcomp 产生 `<>` 占位符
- **测试**：test_adv13_walrus_dictcomp_cond.py
- **源码**：`if (x := {k: v for k, v in items}): pass`
- **状态**：✓ 已修复

### Error 6: listcomp 三元元素退化为 false 分支常量
- **测试**：test_adv13_ternary_in_listcomp_cond.py
- **源码**：`if [a if c else b for x in y]: pass`
- **现象**：三元退化为 false 分支常量 b
- **状态**：✓ 已修复

### 共性根因
`ast_generator_v2.py` 的 `_parse_comprehension_from_code` 方法硬编码 `'ifs': []`，从不调用 `ComprehensionGenerator.parse_comprehension_inner` 的完整重建逻辑（含 filter / key-value / 三元元素）。完整反编译流程走的是 ast_generator_v2.py 的路径，导致推导式作为 if 条件（直接或经 walrus 包裹）时 filter 与 key/value/element 全部丢失。

### 修复策略
将 `_parse_comprehension_from_code` 委托给 `ComprehensionGenerator.parse_comprehension_inner`：
- 解开 Iter 包装（parse_comprehension_inner 期望直接是迭代对象表达式）
- **保存/恢复栈状态**：parse_comprehension_inner 内部调用 reconstruct -> reset 会清空栈。需要恢复以保留外层调用链（如 `any(...)` 中的 any），否则 GeneratorExp 的 elt 会被误用作外层 Call 的 func（导致 test_adv10_genexp_in_cond 退化）
- ComprehensionGenerator 失败时回退到原简化逻辑

## 类别 4: 多个独立三元在 boolop 中归并错乱（3 个错误，已知限制）

### Error 7: 两个三元作 and 产生额外 and 子句与额外 if
- **测试**：test_adv13_ternary_and_ternary_boolop.py
- **源码**：`if (a if c else b) and (d if e else f): pass`
- **现象**：额外 `and d` 子句 + 额外的 `if (d if e else f): pass` 语句

### Error 8: 三元 + 普通变量 + 三元 作 and
- **测试**：test_adv13_ternary_plain_ternary_and.py
- **源码**：`if (a if c else b) and d and (e if f else g): pass`

### Error 9: 三个三元作 or 产生完全错误的嵌套 if 结构
- **测试**：test_adv13_ternary_three_or_cond.py
- **源码**：`if (a if c else b) or (d if e else f) or (g if h else i): pass`

### 共性根因
第二个（及后续）三元的 merge_block 被误识别为新 if 的 cond_block。boolop 短路连接多个三元时，每个三元的 merge_block 在 boolop 链中是后续操作数的求值点，不应被识别为独立 if 的入口。R12 修复了"嵌套三元选最外层"（一个三元作另一个三元的子表达式），但未处理多个独立三元作 boolop 并列操作数的场景。

### 风险评估
- **修复风险**：高 — 需深度修改 IfRegion/BoolOpRegion 检测逻辑
- **退化风险**：易导致现有测试退化
- **决定**：标记为已知限制，R14 优先修复

## 回归验证

### R13 新测试
```
12 passed, 3 failed (类别 4 已知限制)
```

### IF 区域全量回归
```
676 passed, 4 failed (1 legacy: test_adv03_nested_ternary_chain + 3 cat4 已知限制), 4 skipped
```

### CFM 全量回归
```
4 failed (与基线一致), 323 passed, 11 skipped
```

### 更广泛回归（bool_op + with_region + match_region + if_region）
- 修复前：19 failed
- 修复后：11 failed
- **8 个改善，0 退化**

## 修复统计

| 类别 | 错误数 | 已修复 | 已知限制 |
|------|--------|--------|----------|
| 类别 1: _WRAPPING_OPS | 2 | 2 | 0 |
| 类别 2: 嵌套三元 else 形式 | 1 | 1 | 0 |
| 类别 3: 推导式 code object | 5 | 5 | 0 |
| 类别 4: 多三元 boolop 归并 | 3 | 0 | 3 |
| **合计** | **11** | **8** | **3** |

## 关键技术发现

1. **两条推导式解析路径**：
   - `ComprehensionGenerator.parse_comprehension_inner`（完整，含 filter/key-value/三元）
   - `ast_generator_v2.py._parse_comprehension_from_code`（简化，硬编码 `ifs: []`）
   - 完整反编译流程走路径 2，绕过了路径 1 的完整逻辑
   - 修复：让路径 2 委托给路径 1，并保存/恢复栈状态

2. **栈状态保存/恢复**：
   - `parse_comprehension_inner` 内部调用 `reconstruct` -> `reset()` 会清空栈
   - 必须保存 `self.stack` / `self.temp_vars` / `self._jump_since_last_compare`，否则外层 CALL 链丢失
   - 这是 test_adv10_genexp_in_cond 退化的根因（GeneratorExp 的 elt 被误用作外层 Call 的 func）

## 下一轮计划

R14 优先修复类别 4（多三元 boolop 归并错乱），需深度修改 IfRegion/BoolOpRegion 检测逻辑。
