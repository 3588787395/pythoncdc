# R08 修复工程师报告

## 修复概述

| 字段 | 值 |
|---|---|
| 轮次 | R08 (dtc-r08) |
| 修复目标 | repro_r2_07 finally_implicit_return (return None 丢失) |
| 修复文件 | core/cfg/region_ast_generator.py, core/cfg/code_generator.py |
| 修复前 | 9/12 repros pass, 50% on r2_07 |
| 修复后 | 10/12 repros pass, 100% on r2_07 |

## 根因

CPython 3.11 编译 try-except-else-finally 时，当 else 分支含 return 时：
1. else 块只含返回值表达式加载指令（如 LOAD_FAST results）
2. RETURN_VALUE 指令放在 finally 正常路径副本块中
3. finally 正常路径副本的 JUMP_FORWARD 目标是 try-except-else-finally 之后的代码（如 return None）

反编译器有三个问题：
1. **finally_copy_blocks 后继检测条件反转**: `_succ not in _region_block_set` 排除了在 region.blocks 中但不属于任何已知结构部分的块（如 return None 块）
2. **post-try 块生成时被跳过**: block 148 在 try body/handler 生成过程中被标记为 generated，但 post-try 循环仅清除 `_post_try_pre_generated_r19n2` 中的块
3. **_generate_region 对 BASIC Region 返回空**: block 148 有自己的 BASIC Region，_generate_region 返回空列表，但未回退到 _generate_block_statements
4. **_filter_trailing_return_none 过滤了显式 return None**: code_generator 的 _filter_trailing_return_none 把 Try 之后的 return None 当作隐式返回过滤掉

## 修复方案

### 1. region_ast_generator.py - finally_copy_blocks 后继检测
用 `_known_struct`（try/else/finally/handler/copy_keys 的 offset 集合）替代 `_region_block_set`，允许在 region.blocks 中但不属于任何已知结构部分的块被收集为 post-try 块。

### 2. region_ast_generator.py - post-try 块生成循环
无条件清除 generated 标记（不仅清除 `_post_try_pre_generated_r19n2` 中的块）。

### 3. region_ast_generator.py - _generate_region 回退
当 _generate_region 对 post-try 块的 Region 返回空时，回退到 _generate_block_statements。

### 4. code_generator.py - _filter_trailing_return_none
当 return None 紧跟在 Try 节点之后时，不过滤（它是显式返回，不是隐式）。

## 算法依据
- 原则 2（每块唯一归属）：post-try 块的结构归属是 try-except 之后的顺序代码
- 原则 3（嵌套即抽象节点）：finally 正常路径副本作为抽象节点，不暴露其内部结构
