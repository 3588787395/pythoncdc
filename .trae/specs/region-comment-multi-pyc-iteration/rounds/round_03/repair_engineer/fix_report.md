# R03 修复工程师报告 — klinedata.pyc

## 1. 修复概览

| 字段 | 值 |
|---|---|
| 目标 pyc | `site-packages/IQCommon/api/klinedata.pyc` |
| 修复前 match_rate | 51.11% (23/45) |
| 修复后 match_rate | **53.33%** (24/45) |
| 新增一致函数 | 1 (`<dictcomp>`) |
| 残留不一致 | 21 (原 22) |
| 修复模式数 | 1/5 (Pattern D) |
| 回归测试 | IF 46 failures（与基线一致，无退化） |
| 算法合规 | FULLY COMPLIANT（0 反模式新增） |

## 2. 修复点

### Fix-01: Pattern D — 推导式 key/value 互换（`<dictcomp>`）

**文件**: `core/cfg/comprehension_generator.py`

**方法**: `_find_dict_kv_split_point` (L738)

**根因分析**:

字典推导式 `{key: value for ...}` 的 key/value 分割逻辑存在缺陷。原代码使用两个循环查找深度从 1 到 >1 的转换点，但两个循环都要求 `i > 0`，导致简单单指令 key（如 `{date: idx for ...}`）无法正确分割。

**字节码模式**:
```
# {date: idx for idx, date in pairs}
LOAD_FAST 'date'    # depth: 0 → 1 (key)
LOAD_FAST 'idx'     # depth: 1 → 2 (value)
MAP_ADD             # depth: 2 → 0
```

**原逻辑（缺陷）**:
```python
# 第一个循环：查找 depth==1 → next_depth>1 的转换，要求 i>0
for i in range(len(depth_history) - 1):
    if depth == 1 and next_depth > 1 and i > 0:  # i>0 阻止了简单 key 的分割
        return i + 1
# 第二个循环：查找 depth==1，要求 i>0
for i in range(len(depth_history) - 1):
    if depth == 1 and i > 0:  # 同样阻止了简单 key 的分割
        return i + 1
```

对于 `{date: idx}`:
- depth_history = `[(0, 1), (1, 2)]`
- 第一个循环：i=0, depth=1, next_depth=2, 但 i>0=False → 跳过
- 第二个循环：i=0, depth=1, 但 i>0=False → 跳过
- 回退到 reconstruct-based 分割，但 `len(value_part) >= 2` 条件也不满足（value_part 只有 1 条指令）
- 最终 key_instrs=[], value_instrs=[LOAD_FAST 'date', LOAD_FAST 'idx']
- key_expr 回退为 target_name（'idx'），value_expr 取两个 LOAD_FAST 的重建结果
- 输出 `{idx: idx ...}` 而非 `{date: idx ...}`

**修复方案**:

替换两个循环为单一逻辑：查找**最后一个**从 depth==1 到 depth>1 的转换点。

```python
# [R03 fix] Find the LAST transition from depth==1 to depth>1.
last_transition_idx = None
for i in range(len(depth_history) - 1):
    idx, depth = depth_history[i]
    next_idx, next_depth = depth_history[i + 1]
    if depth == 1 and next_depth > 1:
        last_transition_idx = i

if last_transition_idx is not None:
    return last_transition_idx + 1
```

**算法依据**:

- **区域归约原则 3（嵌套即抽象节点）**：key_expr 和 value_expr 是推导式元素的两个兄弟子节点，分割点是父节点（MAP_ADD）引用子入口的边界。
- **算法驱动**：用栈深度转换的数学性质（最后从 1→2 的转换点）替代启发式条件（`i > 0`）。
- 正确处理：
  - 简单 key `{a: b}`: depth `[(0,1),(1,2)]` → 最后转换 i=0 → split at 1 ✓
  - 复合 key `{a+b: c}`: depth `[(0,1),(1,2),(2,1),(3,2)]` → 最后转换 i=2 → split at 3 ✓
  - 简单 value `{a: b+c}`: depth `[(0,1),(1,2),(2,3),(3,2)]` → 最后转换 i=0 → split at 1 ✓

**验证**:
- repro_01 (DEFECT-REPRO → OK): `{date: idx for idx, date in pairs}` 字节码 100% 一致
- klinedata.pyc `<dictcomp>` 函数从 mismatch → match

## 3. 残留不一致清单（21 个，按模式归类）

### Pattern A — 控制流区域坍缩（9 函数，最高发，未修复）

if/elif 条件跳转被替换为 EXTENDED_ARG/LOAD_FAST/LOAD_CONST/NOP，伴随大量 true_diffs 与 jump_diffs。

| 函数名 | orig | decomp | true_diffs | 首个差异 |
|---|---|---|---|---|
| get_price_common | 594 | 605 | 472 | 28: POP_JUMP_FORWARD_IF_NONE → LOAD_FAST |
| get_kline_by_count | 478 | 478 | 392 | 2: POP_JUMP_FORWARD_IF_NONE → EXTENDED_ARG |
| get_history_common | 536 | 543 | 367 | 111: POP_JUMP_FORWARD_IF_NOT_NONE → EXTENDED_ARG |
| get_multiminute_his_data | 535 | 439 | 248 | 18: EXTENDED_ARG arg=5 → 3 |
| get_history_new | 352 | 262 | 132 | 65: EXTENDED_ARG arg=2 → 1 |
| `<module>` | 545 | 541 | 189 | 344: NOP → LOAD_CONST |
| get_kline_by_date_new | 332 | 322 | 43 | 38: POP_JUMP_FORWARD_IF_NONE arg=386 → 216 |
| to_pd_result | 215 | 219 | 161 | 35: POP_JUMP_FORWARD_IF_NOT_NONE → EXTENDED_ARG |
| _all_bars_of_range | 17 | 16 | 3 | 14: NOP → LOAD_FAST |

**可疑根因方法**:
- `region_analyzer.py:_identify_conditional_regions` — try/except 上下文下 if/elif 区域识别
- `region_ast_generator.py:_generate_elif_else_chain` / `_generate_if` — elif 链生成阶段跳转指令丢失

### Pattern B — 变量作用域/名字解析错误（6 函数，未修复）

| 函数名 | true_diffs | 首个差异 |
|---|---|---|
| get_multiminute_his_data_by_date | 492 | 48: LOAD_FAST → LOAD_GLOBAL |
| get_history_date_and_count_ifalse | 313 | 99: LOAD_GLOBAL 'datetime' → LOAD_FAST |
| _all_bars_of_cache | 187 | 29: LOAD_CONST '20050101' → LOAD_FAST |
| get_all_real_minute_kline | 191 | 82: LOAD_GLOBAL 'range' → 'system_log' |
| get_all_real_daily_kline | 137 | 51: LOAD_GLOBAL 'len' → LOAD_FAST |
| get_pre_date | 117 | 34: LOAD_GLOBAL 'len' → LOAD_FAST |

### Pattern C — 值/赋值丢失（5 函数，含 R01 残留，未修复）

| 函数名 | true_diffs | 首个差异 |
|---|---|---|
| get_kline_by_count_new | 507 | 14: UNPACK_SEQUENCE → STORE_FAST |
| kline_datetime_list | 208 | 148: SWAP → COMPARE_OP |
| klineCacheData_to_dict | 166 | 30: STORE_FAST → NOP |
| get_kline_by_date_one | 126 | 44: RETURN_VALUE → POP_TOP (**R01 残留**) |
| np_tp_pd | 111 | 56: SWAP → POP_TOP |

### Pattern E — 跳转目标重编号（1 函数，未修复）

| 函数名 | jump_diffs | 首个差异 |
|---|---|---|
| get_kline_by_date_ndarray | 3 | 47: POP_JUMP arg=656 → 308 |

## 4. 回归测试结果

### IF 区域测试矩阵

```
tests/exhaustive/if_region/: 46 failed, 805 passed, 13 skipped (27.60s)
```

- 基线（Phase 1）: IF 96.60%（46 failures / 1355 total）
- 修复后: if_region 46 failures（与基线一致，无新增失败）
- 13 skipped 为测试发现机制差异，非失败

### 推导式相关测试

```
tests/nook/test_comprehensions.py + test_unpacking_003.py + test_unpack_assign_003.py: 6 passed (0.58s)
```

### 模块编译检查

```
python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator; import core.cfg.comprehension_generator"
→ imports OK
```

## 5. 复现实例验证结果

| # | 实例 | 修复前 | 修复后 |
|---|---|---|---|
| 01 | repro_01_dictcomp_keyval_swap | DEFECT-REPRO | **OK** ✓ |
| 02 | repro_02_module_ifelif_collapse | NO-DEFECT | OK |
| 03 | repro_03_default_const_to_local | DEFECT-REPRO | DEFECT-REPRO（Pattern A 残留） |
| 04 | repro_04_global_builtin_to_local | NO-DEFECT | OK |
| 05 | repro_05_wrong_global_name | NO-DEFECT | OK |
| 06 | repro_06_popjump_none_to_extended_arg | DEFECT-REPRO | DEFECT-REPRO（Pattern A 残留） |
| 07 | repro_07_return_value_lost_in_conditional | DEFECT-REPRO | DEFECT-REPRO（Pattern C 残留） |
| 08 | repro_08_tuple_unpack_collapse | DEFECT-REPRO | DEFECT-REPRO（Pattern C 残留） |
| 09 | repro_09_store_to_nop_assign_lost | NO-DEFECT | OK |
| 10 | repro_10_swap_to_pop_value_dropped | DEFECT-REPRO | DEFECT-REPRO（Pattern C 残留） |
| 11 | repro_11_chained_compare_collapse | DEFECT-REPRO | DEFECT-REPRO（Pattern C 残留） |
| 12 | repro_12_major_region_loss_extended_arg | DEFECT-REPRO | DEFECT-REPRO（Pattern A 残留） |
| 13 | repro_13_loadfast_to_loadglobal_scope | DEFECT-REPRO | DEFECT-REPRO（Pattern B 残留） |
| 14 | repro_14_jump_target_renumber | DEFECT-REPRO | DEFECT-REPRO（Pattern E 残留） |

**汇总**: 5 OK / 9 DEFECT-REPRO（原 10 DEFECT-REPRO，修复 1 个）

## 6. 算法 4 原则合规

- **自底向上归约**: ✓ 未改变归约顺序
- **每块唯一归属**: ✓ 未改变块归属逻辑
- **嵌套即抽象节点**: ✓ key/value 分割点为父节点引用子入口边界
- **入口引用语义**: ✓ MAP_ADD 引用 key/value 入口

## 7. 反模式自检

- `_fix_` / `_merge_` / `_patch_` / `_fallback_` / `_hack_` / `_workaround_` / `_temp_` 前缀: **0 新增**
- 硬编码深度上限: **0 新增**
- 跨区域启发式: **0 新增**
- 后处理补丁: **0 新增**

## 8. 注释更新清单

本轮修复涉及的方法 `_find_dict_kv_split_point` 不是 `_identify_*_regions` 或 `_generate_*` 方法，无需 6/4 节模板。修复内注释已标注 `[R03 fix]` + 算法依据（区域归约原则 3）。

## 9. pyc_index.json 更新

`scripts/pyc_batch_verify.py single` 已自动回写：
- `decompile_status`: partial（未变，未达 100%）
- `bytecode_match_rate`: 0.5333（从 0.5111 提升）
- `ok_py_generated`: true
- `last_tested_round`: 3

## 10. 后续轮次输入

残留 21 个不一致函数（5 类模式），建议后续轮次按以下优先级修复：

1. **Pattern A（9 函数，最高发）**: try/except 上下文下 if/elif 区域坍缩。需深入 `region_analyzer.py:_identify_conditional_regions` 与 `region_ast_generator.py:_generate_elif_else_chain`，分析 try-region pass 与 conditional-region pass 的块归属冲突。
2. **Pattern C（5 函数）**: 含 R01 残留（return 值丢失）。需修复 `region_ast_generator.py:_generate_return_ast` 在 try/except if/elif 内 return 值未正确发射的问题。
3. **Pattern B（6 函数）**: 变量作用域/名字解析。需修复 `code_generator.py` 在 elif 链 + try/except 复合上下文中 LOAD_GLOBAL vs LOAD_FAST 误分类。
4. **Pattern E（1 函数）**: 跳转目标重编号，可能是 Pattern A 修复后的副作用。
