# R30 修复工程师报告

## 本轮修复

### Fix 1: elif chain merge_block 误标记为 generated_blocks 导致后续顶级 IfRegion 被跳过

**问题**: 在 `_if_generate_elif_chain` 和 `_if_generate_full_elif_chain` 中，最后一个 elif 的 BoolOp 的 `merge_block` 被无条件添加到 `generated_blocks`。当该 `merge_block` 恰好是后续顶级区域（如另一个 IfRegion）的入口时，顶级循环中的 `all(b in self.generated_blocks)` 检查会通过，导致该区域被跳过，代码块丢失。

**影响函数**: `share_change` (diff=-17 → 0)

**修复**: 在标记 `merge_block` 为已生成之前，检查它是否是任何顶级区域的入口。如果是，则不标记，让后续区域正常处理。

**修改位置**: `region_ast_generator.py` 两处：
1. `_if_generate_elif_chain` 中 `elif_boolop.merge_block` 的标记（约 line 9621）
2. `_if_generate_full_elif_chain` 中 `_last_elif_boolop.merge_block` 的标记（约 line 9832）

**算法依据**: 区域归约算法原则 1（自底向上归约）+ 原则 3（嵌套即抽象节点）。merge_block 作为后续区域的入口，不应被前驱区域的 elif 链处理消费。

## 成功率变化

- 修复前: 128/143 (89.51%)
- 修复后: 129/143 (90.21%)

## 最小复现

创建了 12 个最小复现实例（`minimal_repros/repro_01_elif_merge_block_skips_next_if.py`），覆盖以下模式：
1. elif chain merge_block 是后续 IfRegion 入口
2. if-elif 链后跟 if 语句
3. BoolOp elif merge 跳过后续 if
4. 多 elif 链后跟 if
5. BoolOp 条件 elif 后跟 if
6. 简单 if 后跟 if（对照组）
7. 复杂 BoolOp elif 后跟 if
8. 嵌套 if 在 elif 中后跟 if
9. elif 带 return 后跟 if
10. elif 后跟带赋值的 if
11. elif merge 是 for 循环入口
12. elif 后跟 while 循环

验证结果: 8/12 通过。4 个失败案例涉及更复杂的区域检测问题（BoolOp 分解、while 循环区域检测等），需后续迭代修复。

## 剩余失败函数

| 函数 | diff | 类型 |
|------|------|------|
| get_valuation_new | -243 | 大量代码丢失 |
| load_bars_from_hundsun | -184 | 大量代码丢失 |
| fill_minute_or_day_blank | -81 | 结构错误 |
| <module> | -59 | 模块级代码丢失 |
| change_his_to_backward | -58 | 结构错误 |
| get_str_data | -56 | 结构错误 |
| valuation_new | -53 | 结构错误 |
| one_prod_to_dataframe | +39 | 额外指令 |
| get_stock_exrights | -32 | 结构错误 |
| get_date_and_count | -21 | 结构错误 |
| load_get_price | -19 | 结构错误 |
| build_future_fill_time | -11 | 结构错误 |
| change_his_to_forward | +2 | 跳转目标偏移 |
| get_option_info | +1 | 额外指令 |
