# 最终残留不一致清单（10 轮迭代后）

> 10 轮区域归约算法双工程师迭代完成。quotation.pyc 反编译字节码一致函数数从基线 141/150 (94.00%) 提升至 143/150 (95.33%)，compile_ok=True。残留 7 个不一致函数如下，作为后续迭代输入。

## 残留不一致函数（7 个）

### 1. 跳转目标归一化差异（3 个，源码结构正确，语义等价）

| 函数 | 状态 | 根因 | 修复轮次 |
|------|------|------|---------|
| `one_prod_to_dataframe` | instr_diff@131 | 反编译器将首个 `i==0` 提取为外层 if，原始跳到下一 elif，跳转目标偏移（语义等价）| R8 修复 len_diff，残留跳转目标 |
| `build_future_fill_time` | instr_diff@226 | listcomp 内部 code 对象布局 + 后续跳转目标偏移（语义等价）| 未修复（listcomp code 对象 + 跳转目标归一化）|
| `change_his_to_backward` | instr_diff@296 | for 循环内嵌套 if 的 else 体已恢复，残留跳转目标偏移（语义等价）| R9 修复 len_diff，残留跳转目标 |

### 2. 元数据差异（1 个，非算法缺陷）

| 函数 | 状态 | 根因 |
|------|------|------|
| `<module>` | instr_diff@394 | 嵌套 code 对象的 co_filename 在原始为 `./fly_docker_py311/fly/data/quotation.py`，反编译产物为 `<decompiled>`，LOAD_CONST code 对象比较不等（非语句丢失）|

### 3. Loop 区域语句丢失（3 个，待后续迭代）

| 函数 | 状态 | 根因 | 修复轮次 |
|------|------|------|---------|
| `load_get_price` | len_diff -2 | Conditional+BoolOp 嵌套分支残留 2 指令 | R10 部分修复（-26→-2）|
| `get_str_data` | len_diff -48 | Loop 嵌套 for/while 循环体语句丢失 | 未修复 |
| `get_date_and_count` | len_diff -27 | Loop+Conditional while 循环 if/elif 链语句丢失 | 未修复 |

## 10 轮迭代一致性进展

| 轮次 | 一致函数数 | 成功率 | 关键修复 |
|------|-----------|--------|---------|
| 基线 | 141/150 | 94.00% | — |
| R1 | 141/150 | 94.00% | BoolOp 链首边界 + _nested_if_skip |
| R2 | 141/150 | 94.00% | STORE_SUBSCR 切分 + 三元前序赋值 |
| R3 | 141/150 | 94.00% | 长 or 链入口引用语义 |
| R4 | 141/150 | 94.00% | 修复尝试回退（无退化）|
| R5 | 141/150 | 94.00% | _cond_block_is_ternary_merge 标志生命周期 |
| R6 | 141/150 | 94.00% | 双角色块检测（BoolOp merge_block 同时作为新链起始）|
| R7 | 142/150 | 94.67% | 一元运算符优先级 + 嵌套 IfRegion 主动生成 + NOP 过滤 |
| R8 | 142/150 | 94.67% | 全区域 docstring 审查 + elif 链 ibc 传播 |
| R9 | 142/150 | 94.67% | _if_generate_then_branch 探针副作用（else 体丢失）|
| R10 | 143/150 | 95.33% | BoolOp 子表达式赋值提升错位（load_bars -88→0）|

## 后续迭代建议

1. **Loop 区域语句丢失**（get_str_data -48 / get_date_and_count -27 / load_get_price -2）：重点分析 `_generate_loop` 循环体块遍历是否漏掉 merge/follow 块，以及嵌套 IfRegion 在循环体内的 then/else_blocks 完整生成。
2. **跳转目标归一化**（one_prod_to_dataframe / build_future_fill_time / change_his_to_backward）：源码结构已正确，残留为跳转目标偏移。可考虑在 exact_match_stats 中进一步归一化语义等价的跳转目标，或在 code_generator 中对齐跳转目标布局。
3. **元数据差异**（`<module>`）：非算法缺陷，可在反编译产物中设置 co_filename 为原始文件名以消除。

## 算法合规性

10 轮迭代所有修复均符合区域归约算法 4 原则（自底向上归约 / 每块唯一归属 / 嵌套即抽象节点 / 入口引用语义），0 新增反模式（`_fix_/_hack_/_workaround_` 等前缀），0 新增硬编码深度上限。既有区域测试矩阵 control_flow_matrix 全程 0 退化（基线 9 fail/318 pass == R10 后 9 fail/318 pass）。全部 11 类 `_identify_*_regions` 识别方法 docstring 按 6 节统一模板补全（11/11，R8）。
