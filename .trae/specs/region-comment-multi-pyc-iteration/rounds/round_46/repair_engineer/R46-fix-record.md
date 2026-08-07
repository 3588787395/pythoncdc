# R46 修复记录

## 问题：工具限制导致修复失败

**修复目标**: `core/cfg/region_ast_generator.py` line 22893-22904

**需要添加的代码**:
```python
elif op_chain:
    first_chain_block = op_chain[0][0]
    # [R46] 区域归约算法原则 2（每块唯一归属）：当 first_chain_block
    # 已被 generate() 入口处理提取过前置语句（标记为 generated），
    # 不应在此重复提取。典型场景：a = None; a = a or x.close 中
    # 入口块同时是 BoolOpRegion 的首个 chain block，generate() 的
    # BoolOpRegion 入口分支已通过 _if_extract_cond_instructions
    # 提取 a = None，若此处再次提取会导致重复输出。
    if first_chain_block in self.generated_blocks:
        pre_stmts = []
    else:
        # 原有的前置语句提取逻辑
        ...
```

## 当前状态

- R46 测试工程师工作已完成：创建了 12 个最小复现实例，其中 3 个有缺陷
- 分析了 3 个缺陷的根因
- 工具限制：`string_replace` 和 `MultiEdit` 均因网络问题失败

## 建议

由于本轮迭代时间已用完（6 个待办），建议在下一轮迭代中：
1. 手动应用修复到 `core/cfg/region_ast_generator.py` line 22893-22904
2. 验证 repro_14 的修复效果
3. 优先修复 repro_14，因为它影响最广泛（LOAD_FAST->LOAD_CONST 模式）

## 批量验证结果

修复前: 87.08% (5762/6617 函数匹配)
目标: 修复后应提升至接近 100%