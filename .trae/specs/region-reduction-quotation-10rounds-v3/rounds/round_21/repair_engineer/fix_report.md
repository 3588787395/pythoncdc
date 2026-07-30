# R21 修复工程师报告（V3 首轮，重点攻克 get_str_data 根因 A）

## 1. 修复目标

建模 `BUILD_CONST_KEY_MAP`+`STORE_SUBSCR` dict 构造消费模式，修复 `get_str_data`（V2-R20 基线 len_diff -48，317→269）。

修复顺序严格遵守 spec：**A 消费模式建模 → 边界对齐 → B 兄弟表达式子区域收集 → C 链式共享 merge_block discard**（禁止跳过 A 直接修复 B/C，R12/R19 教训）。

本轮聚焦根因 A（消费模式建模），未触碰 B/C。

## 2. 根因分析

### 2.1 缺陷现象

`get_str_data` 反编译缺失 48 条指令（orig=317 new=269）。原始字节码中存在如下消费模式：

```python
data.loc[i] = {
    'open': stock_df.ix[datas[not_nan_icount]]['open'],
    'close': stock_df.ix[datas[-1]]['close'],
    'high': stock_df.ix[datas]['high'].max(),
    'low': stock_df.ix[datas]['low'].min(),
    'volume': numpy.nan if data_is_nan == 1 else stock_df.ix[datas[0]:datas[-1] + 1]['volume'].sum(),
    'price': stock_df.ix[datas[-1]]['price'],
    'money': numpy.nan if data_is_nan == 1 else stock_df.ix[datas[0]:datas[-1] + 1]['money'].sum(),
}
```

CPython 3.11+ 将该 dict 字面量编译为：键作为单个 `LOAD_CONST tuple` + `BUILD_CONST_KEY_MAP 7`，值表达式中混合纯 LOAD（open/close/high/low/price）与三元表达式（volume/money）。

### 2.2 三层根因

| 根因层 | 描述 | 本轮处置 |
|--------|------|---------|
| A | `BUILD_CONST_KEY_MAP`+`STORE_SUBSCR` dict 构造消费模式未建模。值表达式被拆为独立 TernaryRegion + bare expr，未作为整体 dict 构造语句归约 | **本轮修复** |
| B | `_process_if_blocks` 仅从 region.children 收集表达式子区域，遗漏 IfRegion else_blocks 中的兄弟 TernaryRegion | defer（R23） |
| C | TernaryRegion@844.merge_block=1226 == TernaryRegion@1226.entry 链式共享，前驱独占标记 merge_block 为 generated | defer（R23） |

### 2.3 根因 A 细节

`_try_build_ternary_chained_container` 的 dict 分支原逻辑：当 `len(_const_keys) == len(ternary_chain)` 时一一对应（每个 ternary 一个 key）。但 `get_str_data` 的 dict 有 7 键，其中只有 2 个（volume/money）是三元表达式，其余 5 个是纯 LOAD 值——`len(_const_keys)=7 != len(ternary_chain)=2`，原逻辑直接 bail，导致整个 dict 构造语句丢失。

纯 LOAD 值表达式被编译为 ternary condition_block 中条件测试之前的**前缀指令序列**（每条值表达式净压栈 +1），未被识别为 dict value。

## 3. 修复描述

所有改动集中在 `core/cfg/region_ast_generator.py`，未引入反模式前缀（`_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_`），未新增硬编码深度上限。

### 3.1 修复点 1：栈效应切分前缀值表达式

新增 `_extract_dict_prefix_values(condition_block)`（行 27004）+ `_ternary_prefix_stack_effect(instr)`（行 27095）：

- 基于栈效应的向后扫描：每个值表达式净压栈 +1。从条件测试起点向前反向扫描，每找到一段净效应 +1 的指令序列即为一个值表达式。
- 覆盖 dict 值表达式中常见操作码（LOAD/BINARY_SUBSCR/CALL/BUILD_SLICE 等），其中 `BINARY_SUBSCR` 显式处理（push=1, pop=2），`BUILD_SLICE` 处理切片表达式。
- 与 `_generate_ternary` 中 `cond_val_start` 检测使用相同的栈效应模型，保证一致性。

### 3.2 修复点 2：混合模式 dict 构造

修改 `_try_build_ternary_chained_container` dict 分支（行 ~27540）：当 `len(_const_keys) != len(ternary_chain)` 时，提取各 ternary condition_block 前缀的纯值表达式 + ternary 表达式，组合为 `all_values`，校验 `len(all_values) == len(_const_keys)` 后作为 dict values。

### 3.3 修复点 3：链式容器优先检查

在 `_generate_ternary` 中 merge_context 派发之前增加链式容器优先检查（行 22407-22420）：当 region.merge_block 是另一个带 `container_type` 的 TernaryRegion 的 entry 时，优先调用 `_try_build_ternary_chained_container`，避免进入 `merge_context='compare'` 分支提前消费。

### 3.4 修复点 4：STORE_SUBSCR/STORE_ATTR 消费目标重建

在 `_try_build_ternary_chained_container` 末尾增加 STORE_SUBSCR/STORE_ATTR 消费处理（行 27621-27703）：

- 扫描 innermost_merge 找到首个 STORE_SUBSCR/STORE_ATTR 及其前导 BUILD_* 指令。
- 用 expr_reconstructor 重建目标表达式：STORE_SUBSCR → `Subscript(value=obj, slice=key, ctx=Store)`；STORE_ATTR → `Attribute(value=obj, attr=name, ctx=Store)`。
- 生成 `Assign(targets=[_target_expr], value=container_info)`，使 dict 字面量被包装为 `data.loc[i] = {...}` 赋值语句。
- 提取 store 之后的指令作为 `post_consumer_extra_stmts`（如 `time_index.append(...)`、`i += 1`）。

### 3.5 修复点 5：POP_TOP 语句边界

在 `_build_statements_from_instructions` 中增加 POP_TOP 作为语句边界：检测到 POP_TOP 时将累积的表达式指令重建为 `Expr(value=...)` 语句，恢复 `time_index.append(...)` 等表达式语句。

## 4. 算法 4 原则合规性（FULLY COMPLIANT）

| 原则 | 合规条款 |
|------|---------|
| 1. 自底向上归约 | `_extract_dict_prefix_values` 从最内层（最后压栈的值）向前逐段归约；链式 ternary 从 innermost 向外逐层构建。识别阶段不跨层引用 |
| 2. 每块唯一归属 | 链式 ternary 的所有块归属单个容器赋值语句（`_has_chained_container_inner` 守卫确保 merge_block==entry 时不被重复消费）；condition_block 前缀指令归属父 Dict 节点，条件测试指令归属 IfExp test |
| 3. 嵌套即抽象节点 | 每个 ternary 作为 Dict 的一个 value 子节点；dict 字面量作为单个 Assign value 抽象节点，不展开所有值表达式子块 |
| 4. 入口引用语义 | 父 Dict 通过各值表达式在 condition_block 中的压栈顺序引用它们；父容器通过 merge_block → entry 链引用 chained ternaries；`post_consumer_extra_stmts` 通过 region 属性传递，不跨层展开 |

无跨区域跨层次启发式规则；无后处理修正（一次正确原则）。

## 5. 回归结果

### 5.1 编译检查

```
$ python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"
IMPORT_OK
```

### 5.2 既有区域测试矩阵（基线 9 fail/318 pass/11 skip）

```
$ python -m pytest tests/control_flow_matrix/ -q
9 failed, 318 passed, 11 skipped in 2.11s
```

**0 退化**：与基线完全一致（9 fail/318 pass/11 skip）。

### 5.3 10 个最小复现实例

```
repro_01.py .. repro_10.py: 全部 py_compile OK
```

### 5.4 quotation.pyc 字节码一致性

```
[stats] total=150 matched=147 mismatched=3 missing=0 success_rate=98.00%
[stats] compile_ok=True
[stats] mismatched functions (3):
  - get_str_data: len_diff orig=317 new=314 (diff=-3)    ← -48 → -3（显著减少）
  - change_his_to_backward: instr_diff @idx296            ← P2 deferred
  - get_date_and_count: len_diff orig=714 new=687 (diff=-27)  ← P1 deferred
```

| 指标 | V2-R20 基线 | V3-R21 修复后 |
|------|------------|--------------|
| 一致函数数 | 147 | **147**（≥ 基线，0 退化） |
| 成功率 | 98.00% | 98.00% |
| compile_ok | True | True |
| get_str_data len_diff | -48 (317→269) | **-3 (317→314)**（显著减少） |

R21-5c（一致函数数 ≥ 147）✓；R21-7（get_str_data -48→显著减少）✓。

### 5.5 反编译产物验证

`get_str_data` 反编译输出已正确重建 7 键 dict 字面量，含两个三元表达式（volume/money），并包装为 `data.loc[i] = {...}` 赋值：

```python
data.loc[i] = {'open': stock_df.ix[datas[not_nan_icount]]['open'],
               'close': stock_df.ix[datas[-1]]['close'],
               'high': stock_df.ix[datas]['high'].max(),
               'low': stock_df.ix[datas]['low'].min(),
               'volume': numpy.nan if data_is_nan == 1 else stock_df.ix[datas[0]:datas[-1] + 1]['volume'].sum(),
               'price': stock_df.ix[datas[-1]]['price'],
               'money': numpy.nan if data_is_nan == 1 else stock_df.ix[datas[0]:datas[-1] + 1]['money'].sum()}
time_index.append(datetime_index[datas[-1]])
i += 1
order_data[stock] = data
```

## 6. 反模式自检

| 检查项 | 结果 |
|--------|------|
| `core/cfg/` 无新增 `_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀方法 | ✓ 0 新增 |
| 无新增硬编码深度上限 | ✓ 0 新增 |
| 无跨区域跨层次启发式规则 | ✓ |
| 修改方法 docstring 按 6 节模板更新 | ✓（`_extract_dict_prefix_values` / `_ternary_prefix_stack_effect` 均含算法角色/算法依据/归约顺序/唯一归属判定/嵌套处理/入口引用语义） |

## 7. 残留不一致函数（3 个）

### 7.1 get_str_data（P0，残留 -3，本轮显著推进）

**残留**：len_diff -3（orig=317 new=314）。

**定位**（`/tmp/r21_out/diff_detail.txt` get_str_data 节，idx 297-304）：

```
297 !! O:1518 LOAD_FAST 'time_index'    N:1518 LOAD_FAST 'data'
298 !! O:1520 LOAD_FAST 'data'           N:1520 LOAD_FAST 'order_data'
299 !! O:1522 STORE_ATTR 'index'         N:1522 LOAD_FAST 'stock'
300 !! O:1532 LOAD_FAST 'data'           N:1524 STORE_SUBSCR None
301 !! O:1534 LOAD_FAST 'order_data'     N:1530 JUMP_BACKWARD ->[-1]
302 !! O:1536 LOAD_FAST 'stock'          N:1532 LOAD_GLOBAL 'pandas'
303 !! O:1538 STORE_SUBSCR None          ...
304 !! O:1544 JUMP_BACKWARD ->[-1]       ...
```

外层 `for stock` 循环体尾部原序：
```
data.index = time_index        # orig 1518-1522 (STORE_ATTR)  ← 缺失（3 条指令）
order_data[stock] = data       # orig 1532-1538 (STORE_SUBSCR) ← 已正确生成
JUMP_BACKWARD                  # 外层循环回边
```

反编译输出已正确生成 `order_data[stock] = data`，但**缺失前导 `data.index = time_index` 赋值**（STORE_ATTR，3 条指令）。

**根因性质**：非 BUILD_CONST_KEY_MAP 消费模式（已修复），属**循环尾部 STORE_ATTR 语句发射**问题——内层循环结束后、外层循环回边前的中间块语句未被纳入循环体生成。`post_consumer_extra_stmts` 仅提取 store 之后的指令，未覆盖 store 之前的兄弟赋值。

**建议 R22 处置**：调查循环尾部块（inner loop 退出 → outer loop back-edge 之间）的语句收集，将该 STORE_ATTR 兄弟赋值纳入外层循环体生成。属边界对齐 / 语句收集范畴，风险可控。

### 7.2 change_his_to_backward（P2，defer）

instr_diff@296，code_generator if/else 分支布局未对齐（真实指令重排）。本轮 defer，R27 处理。

### 7.3 get_date_and_count（P1，defer）

len_diff -27（714→687），Loop 反向链 fall-through + loop_else 误识别。本轮 defer，R24-R26 处理。

## 8. 退出条件检查

| 退出条件 | 状态 |
|---------|------|
| V3-E1 不一致函数数 = 0（100%） | ✗ 残留 3 个 |
| V3-E2 可提取新增最小复现实例 < 10 | ✗ 本轮提取 10 个 repro |

## 9. 结论

- R21 根因 A（BUILD_CONST_KEY_MAP+STORE_SUBSCR 消费模式建模）**已修复**，get_str_data len_diff **-48 → -3**（显著减少 94%）。
- 一致函数数 **147/150**（≥ 基线，**0 退化**）。
- 既有区域测试矩阵 **9 fail/318 pass/11 skip**（与基线完全一致，**0 退化**）。
- 10 个 repro 全部 py_compile 通过；IMPORT_OK。
- 算法 4 原则 FULLY COMPLIANT；0 反模式新增。
- 残留 get_str_data -3（循环尾部 STORE_ATTR 兄弟赋值缺失），建议 R22 推进。
