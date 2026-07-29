# Round 10 修复工程师：修复报告（最终轮）

## 1. 修复点

### 1.1 load_bars_from_hundsun BoolOp 子表达式赋值提升错位（-88 len_diff → 0，完全修复）

**缺陷**：load_bars_from_hundsun 的 `source_start = qdt.datetime.strptime(start[:8] + (len(start[8:]) == 4 and start[8:] or '0000'), '%Y%m%d%H%M')` 含 BoolOp/ternary 子表达式。该赋值块被错误归属到外层 IfRegion（os.path.exists）的 then_blocks，而非内层 IfRegion（typet==6）的 then_blocks，导致赋值被提升到 `if typet == 6:` 之前。这使整个后续嵌套结构错位，引发 -88 指令差异。

**根因**（`core/cfg/region_ast_generator.py` `_if_generate_then_branch`）：外层 IfRegion 的 then 分支生成时，跨层提前生成了归属于内层 IfRegion 的 BoolOp 子表达式，吞并了内层 IfRegion 的入口块。

- **违反原则 1（自底向上归约）**：内层 IfRegion 应先归约，其块不应被外层 IfRegion 跨层吞并
- **违反原则 2（每块唯一归属）**：BoolOp 子表达式块被外层与内层 IfRegion 双重归属

**修复方案**（3 处，均在 region_ast_generator.py）：
1. **修复点 1（L9278-9294）归属父区域守卫**：`_if_generate_then_branch` 第二循环添加 `find_enclosing_parent` 守卫，防止外层 IfRegion 跨层提前生成归属于内层 IfRegion 的 BoolOp 子表达式。依据原则 1+2。
2. **修复点 2（L9121-9154）双角色块检测**：`_if_generate_then_branch` children 循环添加双角色块检测——当前驱 BoolOp 的 merge_block 同时是当前 BoolOp 的 entry 时，允许继续处理（否则 source_end 赋值会丢失）。约束：仅当 child.merge_block 不是任何其它区域的 entry 时适用。依据原则 1+4。
3. **修复点 3（L20869-20909）post-STORE 语句直接重建**：`_generate_boolop` 的 post-STORE 提取逻辑重构——将原来调用 `_generate_block_statements(merge_block)`（因 generated 检查返回 []，且块首 BINARY_OP 无法重构）改为直接从 value_target STORE 之后的指令切片用 `_generate_stmts_from_instrs` 重建独立语句（恢复 `panel = panel.ix[:, source_start:source_end]`）。约束：若 merge_block 是另一区域的 entry（双角色块），跳过提取。依据原则 2（BoolOpRegion 归属仅到 value_target STORE 为止）。

## 2. 算法 4 原则对应条款

| 原则 | 本轮对应 |
|------|---------|
| 1. 自底向上归约 | 修复点 1 守卫：内层 IfRegion 的 BoolOp 子表达式不被外层 IfRegion 跨层提前生成 |
| 2. 每块唯一归属 | 修复点 1 守卫 + 修复点 3：BoolOpRegion 归属仅到 value_target STORE 为止，post-STORE 语句独立重建 |
| 3. 嵌套即抽象节点 | 双角色块约束：merge_block 是另一区域 entry 时不提取，保持嵌套抽象 |
| 4. 入口引用语义 | 修复点 2 双角色块检测：前驱 BoolOp merge_block 同时是当前 BoolOp entry 时按入口引用语义继续处理 |

## 3. 回归结果

| 检查项 | 结果 |
|--------|------|
| `import core.cfg.region_analyzer; region_ast_generator` | IMPORT_OK |
| quotation.pyc 反编译 | 成功（1.62s，3641 行，compile_ok=True）|
| 一致函数数 | **143/150 = 95.33%**（142→143，+1，单调递增）|
| load_bars_from_hundsun | **-88 len_diff → 0（完全修复，从不一致列表移除）**|
| load_get_price | -26 → -2（部分改善，连带修复）|
| 既有区域测试矩阵（control_flow_matrix） | 基线 9 fail/318 pass/11 skip == R10 后 9 fail/318 pass/11 skip，**0 退化** |
| 反模式自检（G3） | 0 新增 `_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀 |
| 硬编码深度上限（G4） | 0 新增 |

## 4. 残留不一致函数（7 个）

| 函数 | 状态 | 说明 |
|------|------|------|
| `<module>` | instr_diff@394 | code 对象 co_filename 元数据差异（非语句丢失，非算法缺陷）|
| `one_prod_to_dataframe` | instr_diff@131 | R8 已修复 len，残留跳转目标归一化差异（语义等价）|
| `build_future_fill_time` | instr_diff@226 | listcomp code 对象 + 跳转目标归一化差异（语义等价）|
| `load_get_price` | len_diff -2 | R10 部分修复（-26→-2），残留 2 指令 |
| `get_str_data` | len_diff -48 | Loop 嵌套 for/while 语句丢失（待后续迭代）|
| `change_his_to_backward` | instr_diff@296 | R9 已修复 len，残留跳转目标归一化差异（语义等价）|
| `get_date_and_count` | len_diff -27 | Loop+Conditional if/elif 链丢失（待后续迭代）|

R10 一致函数数 142→143（+1，单调递增），成功率 94.67%→95.33%。load_bars_from_hundsun 完全修复（-88→0）。残留 7 个不一致函数中：3 个为跳转目标/元数据差异（源码结构正确，语义等价），3 个为 Loop 区域语句丢失（get_str_data/get_date_and_count/load_get_price），属后续迭代输入。

## 5. 修改文件

- `core/cfg/region_ast_generator.py` — `_if_generate_then_branch` 归属父区域守卫 + 双角色块检测（L9121-9294）；`_generate_boolop` post-STORE 语句直接重建（L20869-20909）
