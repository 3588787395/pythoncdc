# R18 测试工程师报告

## 1. 基线统计

| 指标 | R17 修复后 | R18 基线 |
|------|-----------|---------|
| 总函数数 | 150 | 150 |
| 一致函数数 | 147 | **147** |
| 不一致函数数 | 3 | 3 |
| 成功率 | 98.00% | **98.00%** |
| compile_ok | True | True |

R18 基线与 R17 修复后完全一致（147/150），无退化。继承 R14/R15/R16/R17 全部归一化逻辑（含传递性不一致委托）。

## 2. 残留 3 个不一致函数

| 函数名 | 状态 | 说明 |
|--------|------|------|
| `get_str_data` | len_diff -48 (317→269) | **R18 重点** |
| `change_his_to_backward` | instr_diff@296 | R14 defer（指令重排） |
| `get_date_and_count` | len_diff -27 (714→687) | R13 遗留 |

`<module>` 在 R17 已修复（传递性不一致委托，delegated_embeds=133），不再列入残留。

## 3. get_str_data 差异分析（R18 重点）

### 3.1 差异概况

- orig_len=317, new_len=269, diff=-48
- first_diff_idx=9（FOR_ITER 目标差异：orig→[305] vs new→[257]）
- 实质差异从 idx 179 开始（POP_JUMP_FORWARD_IF_FALSE 目标：orig→[182] vs new→[183]）
- idx 186 起完全错位

### 3.2 反编译产物中的错误（/tmp/r18_decompiled.py 第 650-653 行）

```python
numpy.nan if data_is_nan == 1 else stock_df.ix[datas[0]:datas[-1] + 1]['volume'].sum()
numpy.nan
stock_df.ix[datas[0]:datas[-1] + 1]['money'].sum()
data.loc[i] = {}
```

**三处明显错误**：
1. 三元表达式被拆解为孤立的表达式语句（应为 dict 值）
2. `numpy.nan` 孤立出现（应为三元表达式的 if 分支）
3. `data.loc[i] = {}` 空字典（BUILD_CONST_KEY_MAP 7 完全丢失）

### 3.3 根因 A 确认：TernaryRegion value_target 误识别 STORE_SUBSCR

**orig 字节码**（idx 276-281，正确）：
```
276: LOAD_CONST ('open','close','high','low','volume','price','money')  # offset 1416
277: BUILD_CONST_KEY_MAP 7                                               # offset 1418
278: LOAD_FAST 'data'                                                    # offset 1420
279: LOAD_ATTR 'loc'                                                     # offset 1422
280: LOAD_FAST 'i'                                                       # offset 1432
281: STORE_SUBSCR                                                        # offset 1434
```

**new 字节码**（反编译，错误）：
- idx 232: `BUILD_MAP 0`（空字典，BUILD_CONST_KEY_MAP 7 丢失）
- idx 236: `STORE_SUBSCR`（offset 1136）
- idx 247-251: `LOAD_FAST 'i'; LOAD_CONST 1; BINARY_OP 13; STORE_FAST 'i'; JUMP_BACKWARD`
  → 生成 `i = i - 1`（错误！value_target 误识别为 'i'）

### 3.4 TernaryRegion@1226 链式共享

orig 在 offset 1226（idx 244）是 `LOAD_FAST 'stock_df'`，开始一个新的三元表达式区域（money 键的 else 分支）。
new 在 offset 1226（idx 255）是 `STORE_SUBSCR`，被误当作三元表达式的赋值目标。

这正是 R12 根因分析所述：
- TernaryRegion@1226 被误赋 value_target='i'（STORE_SUBSCR 的下标 i 被误识别为三元消费目标）
- 导致生成 `i = i + 1`（实为 `i = i - 1`，BINARY_OP 13）而非 money 三元

### 3.5 根因 A 定位

在 `core/cfg/region_analyzer.py` 的 `_identify_ternary_regions`（或相关方法）中：
- 当检测到 STORE_SUBSCR（如 `data.loc[i] = ...`）时
- value_target 不应是下标变量 `i`
- 而应是整个 `data.loc[i]` 表达式（或 None/特殊标记）
- 需区分 STORE_FAST（简单赋值目标）和 STORE_SUBSCR（下标赋值目标）

## 4. 最小复现实例（10 个）

10 个复现实例演示 BUILD_CONST_KEY_MAP+STORE_SUBSCR dict 构造消费模式未建模的各个侧面：

| 复现实例 | 演示要点 |
|---------|---------|
| repro_01_const_key_map_store_subscr_basic | BUILD_CONST_KEY_MAP + STORE_SUBSCR 基本模式 |
| repro_02_ternary_in_dict_value | 三元表达式作为 dict 值 |
| repro_03_multi_key_ternary_dict | 多键三元 dict（get_str_data 7 键缩影） |
| repro_04_value_target_store_fast_ok | value_target 对 STORE_FAST 正常（对照） |
| repro_05_value_target_store_subscr_misid | value_target 对 STORE_SUBSCR 误识别（根因 A 核心） |
| repro_06_dict_loc_assign_pattern | data.loc[i] = {...} 完整模式 |
| repro_07_ternary_then_dict_construction | 三元后跟 dict 构造（链式共享） |
| repro_08_loop_with_dict_assign | 循环中 dict 赋值 + 索引递增 |
| repro_09_chained_ternary_dict_values | 链式三元 dict 值 + numpy.nan 分支 |
| repro_10_get_str_data_pattern | get_str_data 完整模式缩影 |

## 5. 反编译产物

| 检查项 | 结果 |
|--------|------|
| /tmp/r18_decompiled.py | 生成成功（src_len=175488, src_lines=3641） |
| compile(src, '<decompiled>', 'exec') | OK |
| 反编译耗时 | 1.81s |

## 6. 对修复工程师的建议

### 6.1 修复方向：根因 A（TernaryRegion value_target 对 STORE_SUBSCR 的检测）

在 `core/cfg/region_analyzer.py` 的 `_identify_ternary_regions`（或相关方法）中：
- 当遇到 STORE_SUBSCR（如 `data.loc[i] = ...`）时
- value_target 不应取下标变量名 `i`
- 应区分 STORE_FAST（简单赋值目标，value_target = 变量名）和 STORE_SUBSCR（下标赋值目标，value_target 应为 None 或特殊标记）

### 6.2 修复约束

- 必须符合区域归约算法 4 原则
- 禁止跨区域跨层次启发式规则、后处理修正
- 禁止新增 `_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀方法
- 禁止新增硬编码深度上限
- 禁止修改反编译产物文件
- **若修复导致退化，必须回退**

### 6.3 安全保证

- 修复后必须确认不引入退化
- quotation.pyc 一致函数数 ≥ 147
- get_str_data diff 改善（-48 → 0 或收窄）
- 既有矩阵 0 退化
- 编译通过
