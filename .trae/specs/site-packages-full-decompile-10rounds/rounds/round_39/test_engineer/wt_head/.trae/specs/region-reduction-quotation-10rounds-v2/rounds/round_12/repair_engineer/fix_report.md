# R12 修复工程师：修复报告

## 1. R12 基线统计

| 指标 | 值 |
|------|-----|
| 总函数数 | 150 |
| 一致函数数 | 144 |
| 不一致函数数 | 6 |
| 成功率 | 96.00% |
| compile_ok | True |
| R11 基线 | 144/150 (96.00%) |
| get_str_data | len_diff orig=317 new=269 (diff=-48) |

R12 基线与 R11 一致（144/150），无退化。

## 2. get_str_data -48 指令的具体丢失内容

`get_str_data` 原始字节码 317 条，反编译产物 269 条，缺失 48 条。核心丢失区域
为内层 `for datas in datass_list[-count:]` 循环体内的 dict 构造语句。

### 2.1 原始结构（offset 844-1434）

原始字节码构造一个 7 键 dict 并赋值给 `data.loc[i]`：

```python
data.loc[i] = {
    'open':   stock_df.ix[datas][not_nan_icount]['open'],
    'close':  stock_df.ix[datas[-1]]['close'],
    'high':   stock_df.ix[datas]['high'].max(),
    'low':    stock_df.ix[datas]['low'].min(),
    'volume': numpy.nan if data_is_nan == 1 else stock_df.ix[datas[0]:datas[-1]+1]['volume'].sum(),
    'price':  stock_df.ix[datas[-1]]['price'],
    'money':  numpy.nan if data_is_nan == 1 else stock_df.ix[datas[0]:datas[-1]+1]['money'].sum(),
}
```

字节码布局：7 个值表达式顺序压栈（含 2 个 TernaryRegion + 1 个普通 LOAD），
随后 `BUILD_CONST_KEY_MAP 7`（offset 1418）+ `STORE_SUBSCR`（offset 1434）。

- TernaryRegion@844：`volume` 三元（merge_context='compare', merge_block=1226）
- 1226-1270：`price` 普通载入（`stock_df.ix[datas[-1]]['price']`）
- TernaryRegion@1226：`money` 三元（merge_context='store', merge_block=1416）

### 2.2 反编译产物（基线 -48）

```python
numpy.nan if data_is_nan == 1 else stock_df.ix[datas[0]:datas[-1] + 1]['volume'].sum()  # bare expr
numpy.nan                                                                                # 误发
stock_df.ix[datas[0]:datas[-1] + 1]['money'].sum()                                       # bare expr
data.loc[i] = {}                                                                         # 空 dict
```

丢失内容：
- `open`/`close`/`high`/`low` 4 个值表达式（offset 844-1074）
- `price` 普通载入（offset 1226-1270）
- `BUILD_CONST_KEY_MAP 7` dict 构造（offset 1418）
- 2 个三元被分解为 bare expression（结果被 POP_TOP 丢弃），未作为 dict value 嵌入

## 3. 根因分析结论

### 根因 A（区域识别层）：dict 构造消费模式未建模

`data.loc[i] = {...}` 的 RHS 是 `BUILD_CONST_KEY_MAP 7`，消费 7 个栈上值
（含 2 个三元结果 + 4 个普通载入 + 1 个 price 载入）。当前区域归约算法将 2 个
三元识别为独立 TernaryRegion（结构上正确），但其**消费方**是 dict 构造，而非
简单变量赋值（STORE_FAST）或表达式语句丢弃（POP_TOP）。

- TernaryRegion@1226 被误赋 `value_target='i'`：`STORE_SUBSCR`（offset 1434，
  `data.loc[i] = ...`）的下标 `i` 被误识别为三元的消费目标，导致生成
  `i = i + 1` 而非 money 三元。
- TernaryRegion@1226 的 entry=1226 错误包含了前驱 `price` 载入块（1226-1270），
  区域边界与 dict value 边界不对齐。

### 根因 B（生成层）：IfRegion else 分支不分发兄弟表达式子区域

IfRegion@614（`if not datas: continue`）的 else_blocks 包含兄弟 TernaryRegion@844
/@1226 的 entry（其 parent 是外层 LoopRegion@610，非 IfRegion@614）。
`_process_if_blocks` 仅从 `region.children` 收集表达式子区域，遗漏兄弟表达式
子区域，导致其 entry 被平坦化为顺序块并标记 generated，后续父循环遍历跳过。

违反原则 3（嵌套即抽象节点）+ 原则 4（入口引用语义）。

### 根因 C（生成层）：链式共享 merge_block

TernaryRegion@844.merge_block=1226 == TernaryRegion@1226.entry。前驱标记
`region.blocks`（含共享 merge_block 1226）为 generated，导致后继 entry 已
generated 被跳过。违反原则 2（每块唯一归属）。

## 4. 修复点（尝试 + 回退）

### 4.1 尝试的修复（_process_if_blocks）

在 `_process_if_blocks` 中扩展 `child_expr_regions` 收集逻辑：

1. **兄弟表达式子区域收集**：当 IfRegion 的 then/else blocks 包含兄弟表达式
   子区域（parent 非当前 IfRegion 但 entry 落在 blocks 中），通过
   `get_entry_region_for_block` 补充扫描加入 `child_expr_regions`（镜像
   `_loop_handle_child_region_entry`）。守卫：若 parent 是嵌套 IfRegion 且
   其 entry 也在 blocks 中，跳过（交由嵌套 IfRegion 统一生成）。
2. **链式共享 merge_block 处理**：TernaryRegion 链式共享 merge_block
   （前驱 merge == 后继 entry）时，前驱不标记 merge_block 为 generated
   （原则 2），后继仍需以该块为 entry 归约。

### 4.2 回退原因：引入退化（-48 → -69）

修复后 `get_str_data` diff 从 -48 恶化到 -69（new=248），丢失更多指令：

| 项 | 基线 (-48) | 修复后 (-69) |
|----|-----------|-------------|
| volume 三元 | bare expr ✓ | bare expr ✓ |
| `numpy.nan` | bare expr ✓ | **丢失** ✗ |
| `money.sum()` | bare expr ✓ | **丢失** ✗ |
| `data.loc[i] = {}` | ✓ | ✓ |
| TernaryRegion@1226 生成 | (未作为区域生成) | `i = i + 1` **错误** ✗ |

退化机制：
- 兄弟表达式子区域收集将 TernaryRegion@1226 的 blocks（含 1226-1416）标记为
  generated，导致 `numpy.nan`（1286）和 `money.sum()`（1310-1406）作为
  "已生成"块被跳过——但这 2 个表达式本应作为 bare expr 发射（基线行为）。
- TernaryRegion@1226 的 `value_target='i'`（根因 A）导致 `_generate_ternary`
  生成 `i = i + 1`（错误赋值），而非 money 三元。

**结论**：根因 A（dict 构造消费模式 + value_target='i' 误识别）未解决前，
根因 B/C 的修复（兄弟区域收集）会暴露并放大根因 A 的缺陷，造成净退化。
按"0 退化"硬约束，**回退此修复**，恢复 -48 基线。

### 4.3 正确修复路径（deferred，需后续轮次）

完整修复需同时解决三层：

1. **区域识别层**：建模 `BUILD_CONST_KEY_MAP` 消费模式——当三元/载入的
   merge_block 直接进入 `BUILD_CONST_KEY_MAP n` + `STORE_SUBSCR` 时，这些
   值表达式是 dict value，应作为整体 dict 构造语句归约，而非独立
   TernaryRegion/bare expr。
2. **value_target 检测**：`STORE_SUBSCR`（`data.loc[i] = ...`）的 value_target
   不应是下标 `i`，而应是 dict 构造本身（或标记为 `__dict_value__` 语义）。
3. **区域边界**：TernaryRegion@1226 的 entry 不应包含前驱 `price` 载入块
   （1226-1270），应从条件测试点（1274）开始。

此修复涉及区域识别核心逻辑（`_identify_ternary_regions` 的 value_target
检测 + `BUILD_CONST_KEY_MAP` 消费模式），影响面广，需配套最小复现实例
回归，**不在 R12 单轮内完成**，避免 destabilize 144 基线。

## 5. 回归结果

### 5.1 一致函数数

```
[stats] total=150 matched=144 mismatched=6 missing=0 success_rate=96.00%
[stats] compile_ok=True
```

一致函数数 144/150 == R11 基线，**无退化**（满足 ≥ 144）。

### 5.2 既有区域测试矩阵

```
L1:      52 pass / 0 fail
L1_EXP:  10 pass / 2 fail
L1_CF:   12 pass / 0 fail
L2:      30 pass / 0 fail
L2_EX:   49 pass / 0 fail
L3:      16 pass / 2 fail
L3_CO:   15 pass / 1 fail
总计:   184 pass / 5 fail (97.35%)
```

`region_ast_generator.py` 与 `region_analyzer.py` 均与 HEAD（R11 commit a4feb6b）
字节一致（`git diff` 为空），矩阵结果 == R11 基线，**0 退化**。

### 5.3 编译检查

```
$ python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"
IMPORT_OK
```

### 5.4 get_str_data

- 基线：len_diff -48（未改善，未退化）
- 修复尝试：-69（退化，已回退）
- 回退后：-48（== R11 基线）

## 6. 反模式自检

- G3 反模式前缀（`_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_`）：
  代码 diff 为空，**0 新增**（PASS）
- G4 硬编码深度上限：代码 diff 为空，**0 新增**（PASS）
- G11 反编译产物未修改（PASS）
- G12 算法 4 原则：修复尝试遵循原则 2/3/4，但因根因 A 未解导致退化已回退；
  当前代码 == HEAD，4 原则合规状态 == R11（PASS）

## 7. R12 产出

- 测试工程师阶段（完成）：
  - `test_engineer/decompile_report.md`（含 get_str_data -48 详细分析 + 区域结构）
  - `test_engineer/exact_match_stats.py` / `decompile_quotation.py` / `diff_detail.py`
  - `test_engineer/minimal_repros/repro_01..repro_10.py`（10 个最小复现实例）
  - `test_engineer/_diag_regions.py` / `_diag_regions2.py`（区域诊断工具）
- 修复工程师阶段（根因已定位，修复因退化已回退）：
  - `repair_engineer/fix_report.md`（本报告）

## 8. 异常说明

R12 未实现 get_str_data 的净改善（-48 未变）。原因：get_str_data 的 -48 根因
涉及 **dict 构造消费模式建模**（`BUILD_CONST_KEY_MAP` + `STORE_SUBSCR`），
属于区域识别层的功能扩展（非局部 bug 修复），影响面广、风险高。尝试的局部
修复（兄弟表达式子区域收集）因暴露 `value_target='i'` 误识别而引入 -69 退化，
按"0 退化"硬约束回退。

建议后续轮次（R13+）优先攻克：
1. `_identify_ternary_regions` 的 `value_target` 检测对 `STORE_SUBSCR` 的处理
   （下标 vs 赋值目标）
2. `BUILD_CONST_KEY_MAP` 消费模式归约（dict value 表达式作为整体语句）
3. 在上述 2 项稳定后，重新应用 R12 的兄弟表达式子区域收集（根因 B/C 修复）
