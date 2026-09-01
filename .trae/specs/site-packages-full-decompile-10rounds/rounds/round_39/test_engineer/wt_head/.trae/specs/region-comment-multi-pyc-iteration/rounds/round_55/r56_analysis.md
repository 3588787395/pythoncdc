# R55-R56 分析报告

## R55 修复 (已提交: cfbd405d)

### 根因
rcm-r30 (56fc7e15) 修改了 `_generate_slice` 方法，使独立的 ASTSlice 生成 `slice()` 函数调用。
但 ASTSlice 在 Subscript 的元组 slice 内（如 `data.loc[a:b, fields]`）也被当作独立表达式处理，
因为 `_generate_subscript` 的元组分支对所有元素统一调用 `_generate_expression`，
ASTSlice 走 `_generate_slice` → `slice()` 调用路径。

### 修复
在 `_generate_subscript` 的元组分支中，对 ASTSlice 元素使用 `_generate_slice_in_subscript`
生成 `a:b` 格式，而非 `slice(a, b)` 调用。

### 效果
- quotation.pyc: 132/143 → 134/143 (92.31% → 93.71%)
- 修复函数: change_his_to_backward, change_his_to_forward
- 批量: 5872/6617 → 5892/6617 (88.74% → 89.04%, +20 matched, +1 OK, 0 failed)

## R56 分析 (进行中)

### 剩余 9 个 mismatch 根因分类

#### 1. LOAD_METHOD 误识别 (3 个函数)
- `_is_same_type_date`: `day1.isocalendar()` 方法调用丢失
- `change_future_real_date`: `strftime()` 方法调用丢失
- `get_date_and_count`: `isocalendar()` 方法调用丢失

**根因**: rcm-r07 的 `block_to_region` 守卫导致 if-elif 分支体块被错误跳过。
例如 `_is_same_type_date` 中 `if typet == 7:` 的分支体（isocalendar 调用）变为 `pass`，
实际代码被外推到 if-elif 链之后。

#### 2. 表达式顺序错乱 (4 个函数)
- `build_future_fill_time`: jump_diffs=110, true_diffs=469
- `load_bars_from_hundsun`: 大规模指令顺序错乱
- `valuation_new`: 字典构建顺序错误
- `valuation`: BUILD_MAP 顺序错误 + jump_diffs

**根因**: ast_generator 的语句排序逻辑在 rcm-r07+ 后发生变化，部分语句被错误重排。

#### 3. 变量名/常量混淆 (2 个函数)
- `load_get_price`: LOAD_CONST(1) vs LOAD_FAST(typet)
- `get_str_data`: stock_df vs j 变量名混淆

**根因**: 表达式重建时变量引用错误。

### 回归时间线 (R54 analyzer + R26 code + 各 commit ast)
- R26 ast: 150/150 (100%) ✅
- rcm-r07: 146/150 (+4 regressions) ← block_to_region 守卫
- rcm-r12: 145/150 (+1 regression) ← get_str_data
- rcm-r13: 145/150 (no change) ← COMPARE_OP subexpr
- rcm-r14: 141/150 (+4 regressions)
- rcm-r21: 140/150 (+1 regression)
- 当前: 141/150 (R55 修复了 2 个 slice 问题)

### 下一步
1. 修复 rcm-r07 的 block_to_region 守卫——在 if-elif 分支体中不跳过属于当前区域的块
2. 分析 rcm-r14 引入的 4 个新回归
3. 修复 LOAD_METHOD 识别问题
