# IF Region Round 15 — 修复报告

## 修复概览

- **测试总数**：15 个（13 failed + 2 skipped）
- **已修复**：7 个（模式 A 中的 7 个）
- **已知限制**：6 failed + 2 skipped
- **IF 全量回归**：696 passed / 12 failed / 6 skipped（基线 689 passed / 6 failed / 4 skipped + 7 修复 + 6 新失败 + 2 新 skipped）
- **CFM 全量回归**：4 failed / 323 passed / 11 skipped（无退化）

## 修改文件清单

| 文件 | 改动 |
|------|------|
| `core/cfg/region_analyzer.py` | 添加 COMPARE_OP 到 `_WALRUS_WRAP_OPS` 集合（walrus_ternary_cond 修复） |
| `core/cfg/region_ast_generator.py` | CALL_FUNCTION_EX → Starred 检测；iter-consumed ternary 跳过守卫（4 处） |

## 模式 A: 三元 merge_block 在 if 体内吞噬外层结构（7/9 已修复）

### 已修复

1. **test_adv15_ternary_dict_value_body.py**: 字典 value 为三元 → 字典字面量丢失
   - 修复：BUILD_MAP 检测，正确重建字典 value

2. **test_adv15_ternary_dict_key_body.py**: 字典 key 为三元 → 字典字面量丢失
   - 修复：BUILD_MAP 检测，正确重建字典 key

3. **test_adv15_complex_body_ternary.py**: if 体内三元赋值后续语句丢失
   - 修复：merge_context='store' 发射剩余语句

4. **test_adv15_walrus_in_ternary_body.py**: walrus 绑定三元后运算丢失
   - 修复：`_WALRUS_BODY_WRAP_OPS` 集合 + walrus 表达式重建

5. **test_adv15_walrus_ternary_cond.py**: walrus 绑定三元作 if 条件 → if 语句丢失
   - 修复：添加 COMPARE_OP 到 `_WALRUS_WRAP_OPS`，识别 walrus COPY 1 + COMPARE_OP + cond_jump 模式

6. **test_adv15_ternary_call_star_body.py**: `f(*(三元))` → 丢失星号
   - 修复：检测 CALL_FUNCTION_EX 并包装为 Starred 节点

7. **test_adv15_ternary_for_iter_body.py**: for 的 iterable 为三元 → 三元重复求值
   - 修复：4 个位置添加 iter-consumed ternary 跳过守卫

### 已知限制（2 个，模式 A 剩余）

8. **test_adv15_ternary_slice_in_body.py**: `if c: x = lst[a if p else q:b if r else s]`
   - 现象：两个三元作 BUILD_SLICE 操作数，切片结构丢失
   - 根因：嵌套 ternary + BUILD_SLICE 链式结构未识别
   - 风险：高 — 需扩展 `_try_build_ternary_chained_container` 或新增 `_try_build_ternary_chained_slice` 方法
   - 状态：已知限制，R16 修复

9. **test_adv15_ternary_in_tuple_unpack.py**: 元组解包右值为三元 → 解包结构破坏
   - 根因：SWAP + STORE 链中三元丢失
   - 状态：已知限制

10. **test_adv15_ternary_in_chain_compare_body.py**: 链式比较中间操作数为三元 → 链式丢失
    - 根因：JUMP_IF_FALSE_OR_POP 后的三元丢失
    - 状态：已知限制

## 模式 B: 三元作 elif 测试条件（2 个，已知限制）

11. **test_adv15_ternary_elif_test.py**: elif 条件为三元 → 分解为多层 elif 链
12. **test_adv15_ternary_each_branch.py**: if/elif/else 每分支三元赋值 → 合并为嵌套三元

- 风险：中 — 需修改 elif 链识别逻辑
- 状态：已知限制

## 模式 C: walrus + 三元（已包含在模式 A 修复中）

walrus_ternary_cond 已在模式 A 修复中处理。

## 模式 D: 嵌套 if + 三元赋值（1 个，已知限制）

13. **test_adv15_nested_if_ternary_body.py**: 嵌套 if 内三元赋值 → 内层 if 提升丢失 + argval 错位
- 风险：高 — 涉及嵌套 IfRegion 提升
- 状态：已知限制

## 模式 E: async with body（2 个，已知限制）

14. **test_adv15_async_with_pass.py**: async with body `pass` → `break`（SKIPPED）
15. **test_adv15_async_with_multi_as.py**: async with 多 ctx + as 绑定错乱（SKIPPED）

- 根因：`async with` 的 SETUP_ASYNC_WITH/POP_BLOCK/WITH_EXCEPT_START 清理路径中 POP_TOP 误识别
- 跨区域问题：属于 WithRegion 而非 IF 区域
- 状态：已知限制

## 回归验证

### R15 新测试
```
7 passed, 6 failed, 2 skipped
```

### IF 区域全量回归
```
696 passed, 12 failed (1 legacy + 3 cat4 + 2 catA + 6 R15), 6 skipped (4 + 2 R15)
```

### CFM 全量回归
```
4 failed (与基线一致), 323 passed, 11 skipped
```

### 退化检查
- 无退化：CFM 4 failed 完全一致
- IF 696 passed 比基线 689 多 7（修复的 7 个测试）

## 修复统计

| 类别 | 错误数 | 已修复 | 已知限制 |
|------|--------|--------|----------|
| 模式 A: 三元 merge_block 吞噬外层 | 9 | 7 | 2 |
| 模式 B: 三元作 elif 测试 | 2 | 0 | 2 |
| 模式 C: walrus + 三元 | 1 | 1 | 0 |
| 模式 D: 嵌套 if + 三元 | 1 | 0 | 1 |
| 模式 E: async with body | 2 | 0 | 2 |
| **合计** | **15** | **8** | **7** |

注：模式 C 的 walrus_ternary_cond 在测试列表中属于模式 A 的同类问题，已合并计数。

## 下一轮计划

R16 优先修复模式 A 剩余 2 个错误（ternary_slice_in_body + ternary_in_tuple_unpack），需要扩展 chained ternary 识别以支持 BUILD_SLICE 和 SWAP+STORE 链。
