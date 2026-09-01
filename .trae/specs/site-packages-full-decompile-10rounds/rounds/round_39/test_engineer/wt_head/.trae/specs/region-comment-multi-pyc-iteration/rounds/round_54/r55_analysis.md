# R54-R55 分析报告

## R54 修复 (已提交: 39055189)

### 根因
R27 (aa00bbf7) 的 R4-08 BFS 扩展在 `_find_loop_else` 中对所有 WHILE_LOOP 执行 BFS 收集 else_blocks，
无论循环是否有 break。无 break 时，else 子句与顺序代码在字节码层面不可区分，BFS 会越过循环边界
吸收循环体后的所有顺序代码（try-except、嵌套循环等），导致 else_blocks 过度膨胀。

### 修复
将 break target 检测提前到 BFS 之前，仅在有 break 时运行 BFS。

### 效果
- quotation.pyc: 136/150 → 139/150 (90.67% → 92.67%)
- 修复函数: get_option_info, get_cb_calender_info, get_cb_time_info
- 批量: 5872/6617 = 88.74% (无回归)

## R55 分析 (未提交)

### 二分结果

#### region_analyzer.py 回归
- R26 analyzer + R26 ast + R26 code = 150/150 (100%)
- R27 analyzer + R26 ast + R26 code = 142/150 (8 mismatches)
- R54 analyzer (当前) + R26 ast + R26 code = 150/150 (100%) ← R54 已修复所有 analyzer 回归

#### region_ast_generator.py 回归
- R26 analyzer + R26 code + 各 commit 的 ast:
  - LOOP round_02 (2c418eef): 150/150 ✅
  - LOOP round_03 (4d8e8581): 150/150 ✅
  - rcm-r07 (36ec4ea3): 149/150 ← 引入第 1 个回归
  - rcm-r13 (b92522dd): 142/150 ← 引入 7 个回归（最严重）
  - rcm-r21 (b915121b): 144/150
  - R27 (aa00bbf7): 144/150 (6 mismatches)
  - R35 (d826d7fa): 143/150 (修复 1 个，引入 2 个)
  - R35b (ec1f510f): 142/150
  - R47 (c5c9f9ee): 142/150

#### code_generator.py 回归
- R26 analyzer + R26 ast + R27 code = 150/150 ✅ (无回归)

### 关键发现
1. **R54 analyzer 修复了所有 region_analyzer.py 回归**（R54 + R26 ast + R26 code = 100%）
2. **region_ast_generator.py 有 6 个基础回归**（从 rcm-r07 开始）
3. **直接回退 R26 ast/code 不可行**——R26 对其他 pyc 有严重回归（FAILED, exception）
4. 需要逐个分析 rcm-r07 和 rcm-r13 的修改，仅回退对 quotation.pyc 有回归的部分

### 剩余 11 个 mismatch 分类
1. `build_future_fill_time`: 大规模指令顺序错乱（jump_diffs=110, true_diffs=469）
2. `change_future_real_date`: LOAD_METHOD(strftime) 误识别 + jump_diffs
3. `load_bars_from_hundsun`: 大规模指令顺序错乱
4. `load_get_price`: LOAD_CONST(1) vs LOAD_FAST(typet) + 大量 jump_diffs
5. `get_str_data`: 变量名错误(stock_df vs j) + 大量 jump_diffs
6. `_is_same_type_date`: LOAD_METHOD(isocalendar) 误识别
7. `change_his_to_forward`: LOAD_GLOBAL(slice) 代替 BUILD_SLICE
8. `change_his_to_backward`: LOAD_GLOBAL(slice) 代替 BUILD_SLICE
9. `get_date_and_count`: LOAD_METHOD(isocalendar) 误识别 + 大量 jump_diffs
10. `valuation_new`: 字典构建顺序错误
11. `valuation`: BUILD_MAP 顺序错误 + 大量 jump_diffs
