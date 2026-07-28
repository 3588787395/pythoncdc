# R30-5 Fix Report

## 成功率变化
- 修复前: 90.91% (130/143)
- 修复后: 91.61% (131/143)

## 修复函数
- `get_option_info`: diff=1 → diff=0 (完全匹配)

## 根因分析

`get_option_info` 函数中 `if key == 'price_change_ratio' or key == 'trading_time_desc': continue` 编译为共享 continue 块模式：
```
A; POP_JUMP_FORWARD_IF_TRUE to <shared_continue>
B; POP_JUMP_FORWARD_IF_FALSE to <after>
<shared_continue>: JUMP_BACKWARD to loop_header
<after>: ...
```

区域分析器将其建模为两个 IfRegion：
- IfRegion@602 (IF_THEN, merge=loop_header, then=[fall-through blocks])
  - TRUE 路径跳转到 shared_continue → loop_header (continue)
  - FALSE 路径 fall-through 到 then_blocks
- IfRegion@622 (IF_ELIF_CHAIN, merge=loop_header, then=[shared_continue], else=[...])

反编译器对 IfRegion@602 的条件取反（因为跳转目标不在 then_blocks 中），生成：
```python
if not key == 'price_change_ratio':
    if key == 'trading_time_desc':
        continue
    elif isinstance(value, dict):
        ...
```

当 `key == 'price_change_ratio'` 为真时，`not` 使条件为假，跳过 if body 到循环体末尾，编译器生成额外的 JUMP_BACKWARD（隐式 continue），导致字节码 diff=+1。

## 修复方案

在 `region_ast_generator.py` 的 `_if_generate_normal` 函数中，在结果组装前添加模式检测：

**判据：**
1. `condition` 是 `UnaryOp(Not, ...)` （条件被取反）
2. `then_stmts[0]` 是 `If`，`body == [Continue]`，且有 `orelse`
3. 无 `elif_conditions`、无 `else_stmts`

**重组逻辑：**
- 外层条件 un-negate（取 operand）
- 与内层 if 的条件合并为 `BoolOp(or, [outer_cond, inner_cond])`
- body 设为 `[Continue]`
- orelse 设为内层 if 的 orelse（elif/else 链）
- 内层 if 之后的语句作为 post-if 额外语句

生成结果：
```python
if key == 'price_change_ratio' or key == 'trading_time_desc':
    continue
elif isinstance(value, dict):
    dict1.update(value)
    continue
else:
    dict1[key] = value
    continue
```

## 验证
- minimal_repros/repro_02_or_continue_elif.py 确认 buggy 版本有 1 个额外 JUMP_BACKWARD
- get_option_info 字节码完全匹配 (diff=0)
- 整体成功率从 90.91% 提升至 91.61%

## 修改文件
- `core/cfg/region_ast_generator.py`: 在 `_if_generate_normal` 中添加 R30-5 fix（约 40 行）
