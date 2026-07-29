# Round 9 修复工程师：修复报告

## 1. 修复点

### 1.1 change_his_to_backward for 循环内嵌套 if 的 else 分支体丢失（-57 len_diff）

**缺陷**：change_his_to_backward 的 for 循环体内嵌套 `if len(data[predataindex:y_curdataindex]) == 0:` 的 **else 分支体整段丢失**（变 `pass`），导致 -57 指令差异。

**根因**（`core/cfg/region_ast_generator.py` `_if_generate_then_branch` L9038）：
原实现在"空 then + 循环上下文"中调用 `_if_generate_else_branch(region)` 作为"是否存在 else 体"的探针检查。该调用有**副作用**——将 else_blocks 标记为 `generated_blocks`。探针结果仅作布尔判定（无论真假 then 均为 Pass），else 体语句被丢弃。随后 `_if_generate_normal`（L10499）第二次调用 `_if_generate_else_branch` 时，else 块已标记为已生成，返回空，导致 else 体整段丢失。

- **违反原则 2（每块唯一归属）**：else 块被探针预标记 + 正规调用跳过（双重归属冲突）
- **违反原则 4（入口引用语义）**：then 分支生成触发 else 分支的块标记（跨分支副作用）

**修复方案**（算法依据）：移除 `_if_generate_then_branch` 中的 `else_stmts_check` 探针调用（4 行）。then 空 + 非循环出口时直接 Pass，else 体由 `_if_generate_normal` 的正规 `_if_generate_else_branch` 调用生成（无副作用冲突）。修复为纯删除，无新增启发式规则。两个调用方（L7818 elif 链 / L10496 普通 if-else）均安全。

**docstring**：为 `_if_generate_then_branch` 补全 6 节模板（算法依据/归约顺序/唯一归属判定/嵌套处理/入口引用语义/反编译流程）。

## 2. 算法 4 原则对应条款

| 原则 | 本轮对应 |
|------|---------|
| 1. 自底向上归约 | else 体由正规调用生成，识别阶段不跨分支预标记 |
| 2. 每块唯一归属 | 移除探针预标记，else 块仅由正规 `_if_generate_else_branch` 唯一归属 |
| 3. 嵌套即抽象节点 | docstring 6 节"嵌套处理"明确嵌套 IfRegion 作为单个抽象节点 |
| 4. 入口引用语义 | 移除 then 分支生成对 else 分支块标记的跨分支副作用 |

## 3. 回归结果

| 检查项 | 结果 |
|--------|------|
| `import core.cfg.region_analyzer; region_ast_generator` | IMPORT_OK |
| quotation.pyc 反编译 | 成功（1.93s，3636 行，compile_ok=True）|
| 一致函数数 | **142/150 = 94.67%**（≥142，无退化）|
| change_his_to_backward | **-57 len_diff → instr_diff@296**（578=578 指令数完全恢复，残留跳转目标归一化差异）|
| 既有区域测试矩阵（control_flow_matrix） | 基线 9 fail/318 pass/11 skip == R9 后 9 fail/318 pass/11 skip，**0 退化** |
| 反模式自检（G3） | 0 新增 `_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀 |
| 硬编码深度上限（G4） | 0 新增 |

## 4. 残留不一致函数（8 个）

| 函数 | 状态 | 说明 |
|------|------|------|
| `<module>` | instr_diff@394 | code 对象 filename 元数据差异（非语句丢失）|
| `one_prod_to_dataframe` | instr_diff@131 | R8 已修复 len，残留跳转目标 |
| `build_future_fill_time` | instr_diff@226 | listcomp code 对象 + 跳转目标 |
| `load_bars_from_hundsun` | len_diff -88 | Conditional 嵌套赋值链丢失（待后续轮次）|
| `load_get_price` | len_diff -26 | Conditional+BoolOp 嵌套分支丢失（待后续轮次）|
| `get_str_data` | len_diff -48 | Loop 嵌套 for/while 语句丢失（待后续轮次）|
| `change_his_to_backward` | instr_diff@296 | **R9 修复 len_diff，残留跳转目标** |
| `get_date_and_count` | len_diff -27 | Loop+Conditional if/elif 链丢失（待后续轮次）|

R9 一致函数数 142→142（无退化），change_his_to_backward 语句丢失缺陷已修复（-57 len_diff 归零，指令数 578=578 完全匹配）。后续 R10 将继续处理残留 4 个 len_diff 函数（load_bars_from_hundsun / get_str_data / get_date_and_count / load_get_price）。

## 5. 修改文件

- `core/cfg/region_ast_generator.py` — `_if_generate_then_branch` 移除 else_stmts_check 探针调用（-4 行）+ docstring 6 节模板（+25 行）
