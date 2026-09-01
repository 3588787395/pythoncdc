# R51 修复工程师报告

## 修复概述
修复 `_find_try_else_blocks` 中 TE 模式检查的 false positive：当所有 handler 以终止指令退出时，try_end 的 JUMP_FORWARD 目标是 try-except 后的顺序代码，不是 else 子句。

## 根因
R21 (b915121b) 引入的 TE 模式检查用于检测 try-else（Pattern TE）。该检查在 `merge_point` 为 None 或 `<= precise_handler_end` 时，检测 try_end_block 的 JUMP_FORWARD 目标是否 `> precise_handler_end`。如果是，则从该目标收集 else 块。

R47 (c5c9f9ee) 添加了 `_handler_also_jumps_to_target` 检查，防止 handler 也跳转到同一目标时的 false positive。但该检查只看 handler 块内的直接 JUMP_FORWARD 指令，不看异常清理路径（POP_EXCEPT + RERAISE 等）。

**剩余 false positive 场景**：当所有 handler 以 RETURN_VALUE/RERAISE 终止时：
1. try_end JUMP_FORWARD 目标 > precise_handler_end ✓
2. `_handler_also_jumps_to_target = False`（handler 无 JUMP_FORWARD 到目标）✓
3. 但 JUMP_FORWARD 目标实际是 try-except 后的顺序代码（merge point），不是 else 子句

## 修复方案
**原则**：区域归约算法原则 2（每块唯一归属）+ 原则 3（嵌套即抽象节点）

**判据**：从所有 handler 块出发 BFS，检查是否可达 JUMP_FORWARD 目标块。
- **可达** → 目标是 merge point（handler fall-through 到达），可能是 else 子句
- **不可达** → 所有 handler 终止，目标是 post-try 顺序代码，不是 else 子句

**正确性论证**：当所有 handler 终止时，try-else 与 try-without-else 语义等价、字节码相同。decompiler 应取更简单的无 else 形式（符合最小实现原则）。

## 修改文件
- `core/cfg/region_analyzer.py` L7832: `_find_try_else_blocks` 添加 handler 可达性 BFS 检查

## 验证结果
- quotation.pyc: 88.67% → 89.33%（修复 api_get_financial，1/17）
- 批量验证: 88.50% → 88.64%，0 failed，无回归
- 区域测试矩阵: IF/LOOP/TRY/TERNARY 无退化

## 残留问题
- 16 mismatches 残留，分属 3 个文件：
  - region_ast_generator.py: 5 个（_is_same_type_date, load_get_price, change_future_real_date, get_date_and_count, valuation）
  - code_generator.py: 2 个（get_str_data, change_his_to_backward）
  - region_analyzer.py: 6 个（balance_statement, income_statement, cashflow_statement, get_cb_calender_info, get_cb_time_info, build_future_fill_time）
  - 交互效应: 3 个（load_bars_from_hundsun, change_his_to_forward, get_option_info）
- region_analyzer.py 残留主因：IfRegion 过度膨胀（BFS 越过循环边界吸收 loop body 块）
