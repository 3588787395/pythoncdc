# Round 11 修复工程师：修复报告

## 1. 根因分析

### 1.1 load_get_price 循环退出后冗余自赋值 `panel = panel` 被丢弃（-2 → 0，完全修复）

**缺陷**：`load_get_price` orig_len=226 / new_len=224 / diff=-2。for 循环退出后、`if _typet in (7, 8, 9, 15):` 条件之前的冗余自赋值 `panel = panel`（orig idx 198 `LOAD_FAST 'panel'` + idx 199 `STORE_FAST 'panel'`）被丢弃，连带 idx 164 `JUMP_FORWARD` 跳转目标偏移、idx 168 `POP_JUMP_FORWARD_IF_FALSE` 跳转目标归一化失败（-1）。

**根因**（两处，分别位于 `region_ast_generator.py` 与 `code_generator.py`）：

1. **AST 生成层 peephole 误删**（`core/cfg/region_ast_generator.py` `_generate_block_statements`）：原实现包含一段 peephole 优化，将 `LOAD_FAST x + STORE_FAST x`（自赋值）模式匹配识别为「无意义操作」并替换为 `Pass`，导致块 818（else 分支的 `panel = panel`）语句丢失。
   - **违反原则 4（入口引用语义）**：自赋值块是 loop-exit → conditional 衔接处的真实指令，归约后父区域应通过入口引用语义保留其语句，不得由 peephole 跨层丢弃。
   - **违反「禁止用模式匹配替代算法」**：该 LOAD/STORE 同名检测属于跨层启发式规则，替代了区域归约算法本身的语句生成路径。
   - **违反「后处理修正（一次正确原则）」**：peephole 在正常语句生成之前介入，属于后处理修正。

2. **代码生成层 `_if_depth` 过早递减**（`core/cfg/code_generator.py` `_generate_if`）：`_if_depth -= 1` 在 elif body 生成后立即执行，导致后续 elif/else 分支处理期间 `_if_depth=0`，触发 else 分支中自赋值语句的跳过逻辑。
   - **违反原则 4（入口引用语义）**：elif/else 分支作为 IfRegion 的子入口，其语句生成应在 `_if_depth > 0` 上下文中完整执行，过早递减破坏了入口引用语义。

## 2. 修复点

### 修复点 1：移除自赋值 peephole（`core/cfg/region_ast_generator.py` `_generate_block_statements`）

移除原实现在 `_generate_block_statements` 中的 peephole 优化代码块：

```python
# 移除的代码（跨层启发式，违反原则 4 + 禁止模式匹配替代算法）
meaningful = [i for i in block.instructions
             if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
if len(meaningful) == 2:
    load_instr = meaningful[0]
    store_instr = meaningful[1]
    load_ops = ('LOAD_FAST', 'LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_DEREF')
    store_ops = ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF')
    if (load_instr.opname in load_ops and store_instr.opname in store_ops
        and load_instr.argval == store_instr.argval):
        self.generated_blocks.add(block)
        return [{'type': 'Pass'}]
```

移除后，自赋值块走正常语句生成路径，产出 `ast.Assign` 节点（如 `panel = panel`），恢复 orig idx 198-199 的 2 条指令。同时添加 6 节模板 docstring 说明方法契约与 R11 修复依据。

### 修复点 2：调整 `_if_depth` 递减时机（`core/cfg/code_generator.py` `_generate_if`）

将 `_if_depth -= 1` 从 elif body 生成后立即递减，调整为在整个 elif/else 链处理完成后再递减：

```python
# 修改前（过早递减，else 分支 _if_depth=0）
self._if_depth += 1
self._increase_indent()
self._generate_block(first_node.body)
self._decrease_indent()
self._if_depth -= 1  # ← 过早递减
if first_node.orelse and first_node.orelse.nodes:
    self._generate_elif_or_else(first_node.orelse)  # ← 此处 _if_depth=0

# 修改后（整个 elif/else 处理期间保持 _if_depth > 0）
self._if_depth += 1
self._increase_indent()
self._generate_block(first_node.body)
self._decrease_indent()
if first_node.orelse and first_node.orelse.nodes:
    self._generate_elif_or_else(first_node.orelse)  # ← 此处 _if_depth > 0
# 处理剩余节点...
self._if_depth -= 1  # ← 在所有 elif/else 处理完成后递减
```

## 3. 算法 4 原则对应条款

| 原则 | 本轮对应 |
|------|---------|
| 1. 自底向上归约 | 修复点 1：自赋值块作为基本块内的真实指令，由最底层的语句生成路径处理，不被跨层 peephole 提前吞并 |
| 2. 每块唯一归属 | 修复点 1：自赋值块归属其所在 IfRegion 的 else 分支（块 818），由该区域唯一生成 |
| 3. 嵌套即抽象节点 | 未直接涉及（本修复不改变嵌套区域结构）|
| 4. 入口引用语义 | 修复点 1 + 修复点 2：自赋值块作为 loop-exit → conditional 衔接处的入口块，其语句必须完整保留；elif/else 子入口在 `_if_depth > 0` 上下文中完整生成 |

## 4. 回归结果

| 检查项 | 结果 |
|--------|------|
| quotation.pyc 反编译 | 成功（1.86s，3641 行，compile_ok=True）|
| 一致函数数 | **144/150 = 96.00%**（143→144，+1，单调递增）|
| load_get_price | **-2 → 0（完全修复，从不一致列表移除，status=match）**|
| 既有区域测试矩阵（control_flow_matrix） | 修复前 4 fail/85 pass == 修复后 4 fail/85 pass（stash 对比验证），**0 退化** |
| 控制流完整性矩阵（test_control_flow_completeness_matrix） | 94 passed，0 failed |
| 编译检查（py_compile） | COMPILE_OK |
| 反模式自检（G3） | 0 新增 `_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀 |
| 硬编码深度上限（G4） | 0 新增 |

## 5. 残留不一致函数（6 个）

| 函数 | 状态 | 说明 |
|------|------|------|
| `<module>` | instr_diff@394 | code 对象 co_filename 元数据差异（非语句丢失，非算法缺陷）|
| `one_prod_to_dataframe` | instr_diff@131 | R8 已修复 len，残留跳转目标归一化差异（语义等价）|
| `build_future_fill_time` | instr_diff@226 | listcomp code 对象 + 跳转目标归一化差异（语义等价）|
| `get_str_data` | len_diff -48 | Loop 嵌套 for/while 语句丢失（待后续迭代）|
| `change_his_to_backward` | instr_diff@296 | R9 已修复 len，残留跳转目标归一化差异（语义等价）|
| `get_date_and_count` | len_diff -27 | Loop+Conditional if/elif 链丢失（待后续迭代）|

R11 一致函数数 143→144（+1，单调递增），成功率 95.33%→96.00%。load_get_price 完全修复（-2→0，从不一致列表移除）。残留 6 个不一致函数中：3 个为跳转目标/元数据差异（源码结构正确，语义等价），2 个为 Loop 区域语句丢失（get_str_data/get_date_and_count），属后续迭代输入。

## 6. 修改文件

- `core/cfg/region_ast_generator.py` — `_generate_block_statements`：移除自赋值 peephole（LOAD_FAST x + STORE_FAST x → Pass），添加 6 节模板 docstring
- `core/cfg/code_generator.py` — `_generate_if`：调整 `_if_depth -= 1` 递减时机，确保整个 elif/else 处理期间 `_if_depth > 0`
