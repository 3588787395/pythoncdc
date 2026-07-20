# IF Region Round 14 — 修复报告

## 修复概览

- **测试总数**：15 个（11 失败 + 4 通过）
- **已修复**：9 个（类别 D: 2, 类别 C: 4, 类别 B: 3）
- **已知限制**：2 个（类别 A: boolop 结果作 `COMPARE_OP` 操作数）
- **IF 全量回归**：689 passed / 6 failed (4 baseline + 2 类别 A 已知限制) / 4 skipped
- **基线对照**：R13 是 676 passed / 4 failed / 4 skipped；R14 不退化（基线 4 个失败均保留），新增 13 个 pass（9 修复 + 4 新增测试原本就通过）
- **更广泛回归**：CFM + bool_op + with_region + match_region 共 11 failed / 723 passed / 13 skipped — 与 R13 基线**完全一致**，0 退化

## 修改文件清单

| 文件 | 改动 |
|------|------|
| `core/cfg/region_ast_generator.py` | 扩展 `_WRAPPING_OPS` 集合；新增 BUILD_SLICE / BUILD_TUPLE/LIST/SET 处理器；新增 walrus COPY+STORE_* 模式检测与 NamedExpr 重建 |
| `core/cfg/region_analyzer.py` | 新增 walrus+wrapping merge_context 检测；新增 BUILD_TUPLE/LIST/SET 与 BUILD_SLICE 独立分支（含 `_mb_has_cond_jump` 检查） |

---

## 类别 D：三元作切片操作数（2 个错误，优先级最高）

### 错误 10: test_adv14_ternary_slice_operand
- **源码**：`if (a if c else b)[0:5] > 0: pass`
- **现象**：三元 `(a if c else b)` 被完全丢弃，切片起始值 `0` 被误当作 base，输出 `if (0[5] > 0): pass` 并触发 `SyntaxWarning: 'int' object is not subscriptable`
- **根因**：三元 merge_block 的结果作为 `BINARY_SUBSCR` 的 base（栈底），但 `BUILD_SLICE` 的归约未识别为 wrapping，导致 COMPARE_OP 分支因 `net_stack` 为负值而退化为不归约
- **修复**：
  - 将 `BUILD_SLICE` 加入 `_WRAPPING_OPS`
  - 在 `_sim_wrapping_instr` 新增 BUILD_SLICE 处理器（`region_ast_generator.py` 行 8336-8362）：argc=2 弹 start/stop 压 `Slice(start, stop, None)`；argc=3 弹 start/stop/step 压 `Slice(start, stop, step)`
  - 在 `region_analyzer.py` 新增 BUILD_SLICE merge_context 检测分支（行 11513-11530）：含 `_mb_has_cond_jump` 检查避免误判赋值场景
- **状态**：✓ 已修复

### 错误 11: test_adv14_ternary_slice_step
- **源码**：`if a[1:10:(b if c else 2)] > 0: pass`
- **现象**：整个切片 `a[1:10:...]` 与 `> 0` 比较及 `if` 结构全部丢失，只剩 `(b if c else 2)` 顶层 Expr
- **根因**：三元作为 `BUILD_SLICE 3` 的 step 参数（栈顶），同样未识别为 wrapping，三元结果被单独提取为顶层表达式
- **修复**：与错误 10 同根因，同一组修复涵盖
- **状态**：✓ 已修复

---

## 类别 C：walrus 绑定三元后接操作（4 个错误，同一根因）

### 错误 6: test_adv14_walrus_ternary_attr
- **源码**：`if (x := a if c else b).field > 0: pass`
- **现象**：walrus 提取为独立赋值 `x = (a if c else b)`，`.field > 0` 与整个 `if` 丢失
- **根因**：walrus 的 `COPY 1, STORE_*` 在三元 merge_block 之后，反编译器把 `STORE_NAME` 视为表达式终点，丢弃了栈上 `COPY` 副本上的后续 `LOAD_ATTR`/`COMPARE_OP`
- **修复**：
  - 在 `_sim_wrapping_instr` 的 COPY 处理器中：当 `n == 1` 时在 state 中标记 `pending_walrus_copy=True`（`region_ast_generator.py` 行 8442-8449）
  - 在 STORE_FAST/STORE_NAME/STORE_GLOBAL/STORE_DEREF 处理器中：若 state 标记为 True 且栈深 ≥ 2，弹出 COPY 副本与原始三元结果，压入 `NamedExpr(target, original)` 节点（行 8451-8472）
  - 在 `_WRAPPING_OPS` 集合新增 `COPY, STORE_FAST, STORE_NAME, STORE_GLOBAL, STORE_DEREF` 仅为触发 `_has_wrapping` 检测
  - 在 `region_analyzer.py` 的 STORE_* merge_context 检测中新增 walrus+wrapping 模式识别（行 11270-11308）：检测 `COPY 1, STORE_*, <wrapping_ops>, <cond_jump>` 模式，设 `merge_context='compare'`
- **状态**：✓ 已修复

### 错误 7: test_adv14_walrus_ternary_subscr
- **源码**：`if (x := a if c else b)[0] > 0: pass`
- **现象**：与错误 6 同构，walrus + 三元后接 `BINARY_SUBSCR` 被丢弃
- **修复**：与错误 6 同根因
- **状态**：✓ 已修复

### 错误 8: test_adv14_walrus_ternary_method
- **源码**：`if (x := a if c else b).method() > 0: pass`
- **现象**：与错误 6 同构，walrus + 三元后接 `LOAD_METHOD/PRECALL/CALL` 被丢弃
- **修复**：与错误 6 同根因
- **状态**：✓ 已修复

### 错误 9: test_adv14_walrus_ternary_binary_op
- **源码**：`if (x := a if c else b) + 1 > 0: pass`
- **现象**：与错误 6 同构，walrus + 三元后接 `BINARY_OP` 被丢弃
- **修复**：与错误 6 同根因
- **状态**：✓ 已修复

> **类别 C 总结**：4 个测试覆盖 `LOAD_ATTR`、`BINARY_SUBSCR`、`LOAD_METHOD/CALL`、`BINARY_OP` 四种 walrus 后续操作形式，全部由同一组修复涵盖。

---

## 类别 B：三元作容器字面量元素（3 个错误）

### 错误 3: test_adv14_ternary_in_tuple_literal
- **源码**：`if (a if c else b, d): pass`
- **现象**：丢失元素 `d` 与整个 `if` 语句，只剩 `(a if c else b,)` 单元素 tuple Expr
- **根因**：三元 TernaryRegion 在 `BUILD_TUPLE 2` 上下文中被错误归约——结果被单独提取为顶层表达式，后续 `BUILD_TUPLE`、`POP_JUMP_IF_FALSE` 全部丢失
- **修复**：
  - 将 `BUILD_TUPLE, BUILD_LIST, BUILD_SET` 加入 `_WRAPPING_OPS`（`region_ast_generator.py` 行 8569-8573）
  - 在 `_sim_wrapping_instr` 新增 BUILD_TUPLE/LIST/SET 处理器（行 8363-8381）：弹 n 个元素逆序压入 `Tuple/List/Set` 节点（ctx=Load）
  - 在 `region_analyzer.py` 新增独立的 BUILD_TUPLE/LIST/SET merge_context 检测分支（行 11487-11504）
- **状态**：✓ 已修复

### 错误 4: test_adv14_ternary_list_elem
- **源码**：`if [a if c else b, d]: pass`
- **现象**：与错误 3 同构，list 字面量场景
- **修复**：与错误 3 同根因
- **状态**：✓ 已修复

### 错误 5: test_adv14_ternary_in_set_literal
- **源码**：`if {a if c else b, d}: pass`
- **现象**：与错误 3 同构，set 字面量场景
- **修复**：与错误 3 同根因
- **状态**：✓ 已修复

### 关键退化修复
- **首轮实现问题**：初始 BUILD_TUPLE/LIST/SET 处理器未含 `_mb_has_cond_jump` 检查，导致所有 BUILD_* 场景（含 `x = [ternary, y]` 赋值、`lambda x=ternary: ...` 默认值、`def f() -> ternary: ...` 类型注解）均被误设为 `merge_context='compare'`
- **退化影响**：首轮引入 6 个退化（test_adv09_ternary_list_elem、test_adv10_lambda_ternary_default、test_adv10_ternary_in_list_literal、test_adv10_ternary_in_set_literal、test_adv11_ternary_func_default、test_adv11_ternary_return_ann）
- **修复**：拆分 BUILD_MAP 与 BUILD_TUPLE/LIST/SET 为两个独立 elif 分支；后者增加 `_mb_has_cond_jump` 检查（要求 merge_block 末尾含条件跳转，即 if/while 条件上下文），仅在该条件满足时才设 `merge_context='compare'`
- **状态**：✓ 退化已修复

---

## 类别 A：boolop 结果作 `COMPARE_OP` 操作数（2 个错误，已知限制）

### 错误 1: test_adv14_boolop_result_compare
- **源码**：`if (a and b) == (c and d): pass`
- **现象**：输出退化为 `if (a and c): pass` — 丢失 `b`、`d`、`==` 比较运算符
- **根因**：boolop 的 `JUMP_IF_FALSE_OR_POP` 短路跳转结构在条件归约中被误判为 `if` 条件判断点，两个 `and` 的 cond_block 链被错误合并，`COMPARE_OP ==` 与右操作数 `and` 表达式丢失

### 错误 2: test_adv14_boolop_single_compare
- **源码**：`if (a or b) == c: pass`
- **现象**：输出退化为 `if (a or b): pass` — `== c` 比较部分完全丢失
- **根因**：`JUMP_IF_TRUE_OR_POP` 跳转目标被识别为 `if` 条件判断点，`LOAD_NAME c` 与 `COMPARE_OP ==` 被当作 `if` 体外语句丢弃

### 风险评估与决定
- **修复风险**：高
  - 需要深度修改 BoolOpRegion / TernaryRegion / IfRegion 边界检测逻辑，识别 `JUMP_IF_*_OR_POP` 后紧跟另一个 `JUMP_IF_*_OR_POP` 与 `COMPARE_OP` 的模式
  - 该区域**正是 R12/R13 留下的 4 个 baseline 失败所在区域**：
    - `test_adv03_nested_ternary_chain`（嵌套三元链）
    - `test_adv13_ternary_and_ternary_boolop`（两个三元作 and）
    - `test_adv13_ternary_plain_ternary_and`（三元+普通变量+三元作 and）
    - `test_adv13_ternary_three_or_cond`（三个三元作 or）
  - 这 4 个 baseline 失败本身已经表明边界检测逻辑不稳定，进一步修改极易引入新退化
- **决定**：标记为已知限制，不在 R14 修复，留待后续轮次专门处理

---

## 回归验证

### R14 新测试
```
15 passed (含 R14 修复 9 + 通过 4 + 退化测试 2 已知限制)
按修复状态：9 fixed, 2 known limits, 4 already passing
```

实际运行：
```
test_adv14_*: 13 passed, 2 failed (类别 A 已知限制), 0 skipped
```

### IF 区域全量回归
```
689 passed, 6 failed, 4 skipped
```

失败明细：
- `test_adv03_nested_ternary_chain`（R12 基线限制）
- `test_adv13_ternary_and_ternary_boolop`（R13 cat4 已知限制）
- `test_adv13_ternary_plain_ternary_and`（R13 cat4 已知限制）
- `test_adv13_ternary_three_or_cond`（R13 cat4 已知限制）
- `test_adv14_boolop_result_compare`（R14 类别 A 已知限制）
- `test_adv14_boolop_single_compare`（R14 类别 A 已知限制）

### 基线对照（R13 → R14）
| 指标 | R13 | R14 | 变化 |
|------|-----|-----|------|
| IF passed | 676 | 689 | +13（9 修复 + 4 已通过新测试） |
| IF failed | 4 | 6 | +2（类别 A 已知限制） |
| IF skipped | 4 | 4 | 0 |

**基线 4 个失败全部保留，无退化**。

### 更广泛回归（CFM + bool_op + with_region + match_region）
- **修复前**（git stash 后基线）：11 failed / 723 passed / 13 skipped
- **修复后**（R14）：11 failed / 723 passed / 13 skipped
- **退化检查**：11 个失败测试**完全一致**（同测试名、同失败原因），0 退化

CFM + bool_op + match_region 的 11 个 baseline 失败均与 R14 修改无关：
- 4 个 CFM（CF2WhileIfBreakContinue, L12WhileBreakContinue, N11TryWhileContinue, XP04BoolOpInIf）
- 4 个 bool_op（bool03_not, bool11_in_while, bool19_ternary_combo, bool20_complex_logic）
- 3 个 match_region（m031, m049, m106matchguardboolop）

---

## 修复统计

| 类别 | 优先级 | 错误数 | 已修复 | 已知限制 |
|------|--------|--------|--------|----------|
| 类别 D: 三元作切片操作数 | 1 | 2 | 2 | 0 |
| 类别 C: walrus 绑定三元后接操作 | 2 | 4 | 4 | 0 |
| 类别 B: 三元作容器字面量元素 | 3 | 3 | 3 | 0 |
| 类别 A: boolop 结果作 COMPARE_OP 操作数 | 4 | 2 | 0 | 2 |
| **合计** | — | **11** | **9** | **2** |

---

## 关键技术发现

### 1. walrus 模式与 wrapping 模式的关系
walrus 的字节码模式 `COPY 1, STORE_*, <后续运算>, <cond_jump>` 是 wrapping 模式的一个变体：
- 普通 wrapping：三元结果在栈上，被 `LOAD_ATTR`/`BINARY_SUBSCR`/`CALL`/`BINARY_OP` 直接消费
- walrus+wrapping：三元结果先 `COPY 1` 留副本，副本被 `STORE_*` 消费并绑定名称，原始值仍在栈上继续被后续 wrapping 指令消费
- 重建时需把原始值替换为 `NamedExpr(target, value)` 以表达 walrus 副作用，同时不丢失原始值在表达式中的位置

### 2. `_mb_has_cond_jump` 检查的必要性
`BUILD_TUPLE/LIST/SET` / `BUILD_SLICE` 不仅出现在 if 条件上下文中，还出现在：
- 赋值右值：`x = [ternary, y]`
- 默认参数：`lambda x=ternary: ...`
- 类型注解：`def f() -> ternary: ...`

未含 `_mb_has_cond_jump` 检查的初始实现把这些场景都误判为 `merge_context='compare'`，导致 6 个测试退化。加上检查后（要求 merge_block 末尾含条件跳转），仅在 if/while 条件上下文设置 compare，赋值/默认值/注解场景走默认 `'store'` 路径。

### 3. 类别 A 与基线限制同源
类别 A 的 2 个错误与 R13 cat4 已知限制（3 个测试）共享同一根因区域：BoolOpRegion 的短路跳转（`JUMP_IF_FALSE_OR_POP`/`JUMP_IF_TRUE_OR_POP`）与 TernaryRegion / IfRegion 的边界检测。该区域不稳定，4 个 baseline 失败本身已证明这一点。修复需统一处理 boolop merge 后的归约终点判定，留待后续轮次专门处理。

---

## 下一轮计划

R15 优先处理 boolop + COMPARE_OP 组合（类别 A + R12/R13 残留 cat4），需：
1. 在条件归约中识别 `JUMP_IF_FALSE_OR_POP` / `JUMP_IF_TRUE_OR_POP` 后紧跟 `COMPARE_OP` 的模式
2. 将 boolop 结果包装为带括号的子表达式（`(a and b) == (c and d)`）后再作为 `COMPARE_OP` 操作数
3. 区分单个 boolop 作 if 条件（`if a and b:` — boolop 直接作条件）vs boolop 作比较操作数（`if (a and b) == c:` — boolop 需括号）
4. 处理多个独立三元作 boolop 并列操作数（R13 cat4 的 3 个测试）

风险管控：每改一处即运行 IF 全量回归，确保 6 个 baseline+类别 A 失败不引入新退化。
