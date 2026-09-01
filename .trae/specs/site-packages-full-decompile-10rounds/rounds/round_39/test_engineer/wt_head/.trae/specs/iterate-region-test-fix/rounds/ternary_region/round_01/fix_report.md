# Ternary Region Round 01 — 修复报告

## 修复概览

- **测试总数**: 17 个（R1 测试工程师发现，全部 FAILED）
- **已修复**: 5 个 bug（Bug 1, 2, 7, 8, 9）
- **已知限制**: 12 个 bug 未修复（其中 Bug 3, 4 经验证属字节码根本歧义，不可修复）
- **回归状态**: Ternary 区域 60 failed → 55 failed（减 5），72 passed → 77 passed（增 5），无退化
- **跨区域回归**: ternary + if_region + control_flow_matrix 107 failed → 102 failed（减 5），1169 passed → 1174 passed（增 5），无退化

## 修改文件清单

| 文件 | 改动 |
|------|------|
| `core/cfg/region_analyzer.py` | `_is_single_expression_block`: 新增 walrus `COPY N / STORE_*` 副作用剥离；`_detect_ternary_pattern`: COMPARE_OP `_net_stack == 1` 分支新增 STORE_* 检测；`_detect_ternary_context`: 新增 LOAD_METHOD 调用模式识别 |
| `core/cfg/region_ast_generator.py` | `_generate_ternary` preload: 新增 BUILD_LIST/TUPLE/SET/MAP/CONST_KEY_MAP 容器字面量处理；`has_ops`: 新增 LIST_EXTEND/DICT_UPDATE/SET_UPDATE/LIST_APPEND/MAP_ADD |
| `core/cfg/ast_generator_v2.py` | `ExpressionReconstructor.reconstruct` LIST_EXTEND: 新增对 IfExp/BoolOp/BinOp 等复合表达式的 Starred 包装 |
| `core/cfg/code_generator.py` | `_generate_expression` Starred 分支: 当 value 是低优先级复合表达式时加括号 |

## Bug 详细修复

### Bug 1: walrus 在 ternary body 中 — 已修复

- **测试**: `test_r1_walrus_in_body.py`
- **源码**: `x = (y := a) if a > 0 else 0`
- **根因**: walrus 表达式 `(y := a)` 使 ternary true_value_block 含 `COPY 1 / STORE_NAME y` 序列。`_is_single_expression_block` 检测到 STORE_NAME 后拒绝该块为单表达式，TernaryRegion 未识别，整体退化为 IfRegion + 独立 walrus 赋值，外层 x 赋值丢失。
- **修复**: 在 `_is_single_expression_block` 中新增 walrus 副作用剥离逻辑。检测 `COPY N (N>=1) / STORE_*` 对（walrus 字节码模式），将其视为值表达式内的子节点副作用，剥离后再判定单表达式性。
- **算法依据**: 「嵌套即抽象节点」— walrus 是值表达式内的子节点（NamedExpr），不破坏外层单表达式性。「每块唯一归属」— 整块归属 TernaryRegion。
- **字节码验证**: walrus 的 `COPY 1` 复制栈顶值，`STORE_*` 消耗复制体给 walrus 目标，原值留在栈上作为 ternary 值块的求值结果流向 merge_block。

### Bug 2: walrus 在 ternary orelse 中 — 已修复

- **测试**: `test_r1_walrus_in_orelse.py`
- **源码**: `x = a if cond else (y := b)`
- **根因**: 同 Bug 1，walrus 在 orelse 中使 false_value_block 含 `COPY 1 / STORE_NAME y`，被 `_is_single_expression_block` 拒绝。
- **修复**: 同 Bug 1（共用 walrus `COPY N / STORE_*` 剥离逻辑）。

### Bug 7: ternary 作为 compare 左操作数 — 已修复

- **测试**: `test_r1_ternary_in_compare.py`
- **源码**: `x = (a if a > 0 else 0) == b`
- **根因**: `_detect_ternary_pattern` 的 COMPARE_OP `_net_stack == 1` 分支无条件设 `merge_context='compare'`，即使 COMPARE_OP 后有 STORE_*（赋值上下文）。导致 ternary 被视为 compare 的左操作数，外层赋值 `== b / STORE_NAME x` 丢失。
- **修复**: 在 `_net_stack == 1` 分支新增 `_has_store_after_cmp` 检测——若 merge_block 中 COMPARE_OP 之后有 STORE_*，说明比对结果被赋值（如 `x = (ternary) == b`），而非用作 if/while 条件测试。此时不设 `merge_context='compare'`，让流程继续扫描 merge_block 找到 STORE_* 并设为 value_target。
- **算法依据**: 「父引用子入口」— 父表达式（Compare）通过 merge_block 引用 ternary 的入口；merge_block 的消费指令归属到 ternary 父区域。

### Bug 8: ternary 作为方法调用参数 — 已修复

- **测试**: `test_r1_ternary_in_method_call.py`
- **源码**: `obj.method(a if a > 0 else 0)`
- **根因**: `_detect_ternary_context` 仅检测 `PUSH_NULL + LOAD_*` 调用模式，未检测 `LOAD_NAME obj; LOAD_METHOD method` 模式（无 PUSH_NULL，LOAD_METHOD 自带 self 绑定）。导致 ternary 被视为独立表达式语句，方法调用结构丢失。
- **修复**: 在 `_detect_ternary_context` 新增 `else` 分支检测 LOAD_METHOD 模式。仅当 merge_block 含 PRECALL/CALL 时才识别为 call 上下文，避免误把其他场景的 LOAD_METHOD 当 call。识别后重建 `Attribute(value=Name(obj), attr=method)` 作为 func，返回 `('call', {func: ...}, None)`。
- **算法依据**: 「父引用子入口」— 父表达式（Call）通过 merge_block 引用 ternary 的入口；LOAD_METHOD/PRECALL/CALL 序列归属到 ternary 父区域。

### Bug 9: ternary 在 starred 表达式中 — 已修复（4 处协同）

- **测试**: `test_r1_ternary_in_starred.py`
- **源码**: `x = [*(items if cond else [])]`
- **根因**: `[*(ternary)]` 的字节码是 `BUILD_LIST 0` (建外层 list) + ternary 求值 + `BUILD_LIST` (包装 iter) + `LIST_EXTEND 1` (展开)。反编译器丢失外层 BUILD_LIST 与 LIST_EXTEND，直接赋值 ternary 结果。
- **修复**（4 处协同）:
  1. `region_ast_generator.py` `_generate_ternary` preload 循环：新增 BUILD_LIST/TUPLE/SET/MAP/CONST_KEY_MAP 处理，把 `BUILD_LIST 0` 重建为 `List([])` 加入 preload_stack。
  2. `region_ast_generator.py` `has_ops`：新增 LIST_EXTEND/DICT_UPDATE/SET_UPDATE/LIST_APPEND/MAP_ADD，触发 full_expr 重建。
  3. `ast_generator_v2.py` `ExpressionReconstructor.reconstruct` LIST_EXTEND 处理：新增 elif 分支，当 extend_values 是 IfExp/BoolOp/BinOp 等复合表达式时，包装为 `Starred(value=extend_values)` 以保留 `*expr` 语义。
  4. `code_generator.py` `_generate_expression` Starred 分支：当 value 是低优先级复合表达式（IfExp/BoolOp/NamedExpr/Lambda/Yield/BinOp/UnaryOp/Compare/Starred）时，渲染为 `*({value_code})` 而非 `*{value_code}`，避免 `*items if cond else []` 这种语法错误。
- **算法依据**: 「父引用子入口」— 父表达式（List with Starred）通过 BUILD_LIST + LIST_EXTEND 引用 ternary 的入口；「嵌套即抽象节点」— Starred(IfExp) 是 List 内的抽象节点。

## 未修复 bug（已知限制）

| Bug | 测试 | 优先级 | 说明 |
|-----|------|--------|------|
| 3 | test_r1_assert_simple | P1 | **根本性歧义**: Python 3.11.15 中 `assert (a if a > 0 else 0)` 与 `assert (a > 0 and a)` 字节码完全等价（已验证），不可修复 |
| 4 | test_r1_assert_with_message | P1 | 同 Bug 3，带 message 的 assert 字节码也等价 |
| 5 | test_r1_chained_compare_in_cond | P2 | chained_compare IfRegion 优先级高于 TernaryRegion，需边界调整 |
| 6 | test_r1_ternary_in_slice | P0 | 双 ternary 喂 BUILD_SLICE 2 / BINARY_SUBSCR，merge_block 含第二个 ternary 的 setup |
| 10 | test_r1_return_tuple_with_ternary | P1 | 嵌套 code object 内 ternary + BUILD_TUPLE 2 重组错误 |
| 11 | test_r1_ternary_in_dict_value | P0 | 双 ternary 喂 BUILD_CONST_KEY_MAP 2，退化为 BUILD_MAP |
| 12 | test_r1_ternary_in_lambda_complex | P2 | lambda body 含 `(ternary) + 1` 复合表达式时 body 被替换为 None |
| 13 | test_r1_while_with_ternary_body | P1 | while 循环体含 ternary 赋值，back_edge_block 的条件 reload 被误输出为表达式语句 `cond` |
| 14 | test_r1_async_for_ternary | P2 | async for 字节码（GET_AITER/GET_ANEXT/SEND）干扰 ternary 识别 |
| 15 | test_r1_ternary_in_with | P1 | with 上下文管理器位置使用 ternary，BEFORE_WITH 与 __exit__ 调用顺序错乱 |
| 16 | test_r1_class_body_multi_ternary | P1 | class body 多 ternary，第二个 ternary 的 condition_block 未能被 TernaryRegion 归约 |
| 17 | test_r1_return_two_ternary | P1 | return 双 ternary 元组，嵌套 code object 内重组错误 |

## 回归验证

### R1 新测试
```
17 failed → 12 failed（5 修复：Bug 1, 2, 7, 8, 9）
```

### Ternary 区域全量回归
```
60 failed, 72 passed, 1 skipped → 55 failed, 77 passed, 1 skipped
```

### 跨区域回归（ternary + if_region + control_flow_matrix）
```
107 failed, 1169 passed, 22 skipped → 102 failed, 1174 passed, 22 skipped
```

### 退化分析
- Ternary 区域：减 5 failed，增 5 passed，无退化
- 跨区域：减 5 failed，增 5 passed，无退化
- 已验证 `test_l1_expression.py::TestXP04BoolOpInIf` 等预存在失败非本次修复引入

## 修复统计

| 类别 | 错误数 | 已修复 | 已知限制 |
|------|--------|--------|----------|
| R1: walrus 在 ternary body/orelse | 2 | 2 | 0 |
| R4: ternary 作为外层表达式操作数 | 5 | 3 (Bug 7, 8, 9) | 2 (Bug 6, 11) |
| R2: assert(ternary) 折叠为 BoolOp | 2 | 0 | 2 (根本性歧义) |
| R3: chained compare 在 ternary 条件 | 1 | 0 | 1 |
| R5: 嵌套 code object 内 ternary | 5 | 0 | 5 |
| R6: lambda body 含复合 ternary | 1 | 0 | 1 |
| R7: async for 体 ternary | 1 | 0 | 1 |
| **合计** | **17** | **5** | **12** |

## 算法原则遵循性

所有 5 个修复均严格遵循区域归约算法 4 原则：

1. **自底向上归约**: walrus 作为子表达式先被识别（Bug 1, 2）；ternary 作为子表达式先被识别（Bug 7, 8, 9），再由父表达式（Compare/Call/List）消费。
2. **每块唯一归属**: walrus 的 COPY+STORE 对归属 ternary 值块（不归属独立赋值）；ternary merge_block 的消费指令归属 ternary 父区域（不归属独立表达式语句）。
3. **嵌套即抽象节点**: walrus 是值表达式内的 NamedExpr 子节点（Bug 1, 2）；Starred(IfExp) 是 List 内的抽象节点（Bug 9）。
4. **父引用子入口**: 父表达式（Compare/Call/List）通过 merge_block 引用 ternary 的入口块；不展平嵌套，不跨区域特例。

**禁止项核查**: 无跨区域启发式特例、无后处理补丁、无启发式优先级覆盖、无展平嵌套。

## 下一阶段计划

1. **P0 R4 剩余**: Bug 6 (slice) + Bug 11 (dict value) — 需处理双 ternary 喂同一消费指令（BUILD_SLICE 2 / BUILD_CONST_KEY_MAP 2）的模式，第一个 ternary 的 merge_block 含第二个 ternary 的 setup。
2. **P1 R5**: Bug 10, 13, 15, 16, 17 — 嵌套 code object 内 ternary 重组错误，每个 bug 可能需要单独修复。
3. **P1 R2**: Bug 3, 4 已验证为根本性歧义，建议从测试套件中移除或标记为已知限制。
4. **P2 R3/R6/R7**: Bug 5, 12, 14 — 单个 bug，优先级较低。
