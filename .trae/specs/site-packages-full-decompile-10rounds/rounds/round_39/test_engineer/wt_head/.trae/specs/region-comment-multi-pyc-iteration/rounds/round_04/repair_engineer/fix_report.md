# R04 修复工程师报告 — klinedata.pyc

## 1. 修复概览

| 字段 | 值 |
|---|---|
| 目标 pyc | `site-packages/IQCommon/api/klinedata.pyc` |
| 修复前 match_rate | 53.33% (24/45) |
| 修复后 match_rate | **53.33%** (24/45) — 持平 |
| 新增一致函数 | 0（实际 pyc 层；最小复现实例层 +4） |
| 残留不一致 | 21（与 R03 一致） |
| 修复模式数 | Pattern A 子模式 A1（BoolOp-in-try-body-if 坍缩） |
| 回归测试 | 1 failed, 112 passed, 14 errors（与基线一致，无退化） |
| 算法合规 | FULLY COMPLIANT（0 反模式新增） |

## 2. 修复点

### Fix-01: Pattern A 子模式 A1 — BoolOp 条件 + try-body if 坍缩（结构边界回退解析器）

**文件**: `core/cfg/region_analyzer.py`

**新增方法**: `_get_enclosing_structural_boundary_stop` (L18512-18561)

**修改方法**: `_identify_conditional_regions` (L11742-11743) — boundary_stop 计算回退

**根因分析**:

Pattern A 子模式 A1 的触发条件：`try:` 体内含 `if <BoolOp>:` / `elif ...:` + trailing return。

区域归约顺序：BoolOpRegion（表达式区域）先于 IfRegion 识别，占用 if 入口块（如 `if x is None or y is None:` 的第一个条件块）。但该块同时属于外层 TryExceptRegion.try_blocks（`try: if ...:` 的 try 体）。

**问题**：
- `block_to_region[if_entry_block]` = BoolOpRegion（表达式区域先识别）
- BoolOpRegion 继承 base Region.get_if_branch_boundary_stop 返回空集（表达式区域不提供结构边界）
- `boundary_stop = block_region.get_if_branch_boundary_stop(block)` → 空集
- `_collect_branch_blocks` 越过 try 体边界，把体外块（如 try 后的 trailing return、except handler entry）误收集进 elif_final_else / then_blocks
- IfRegion 跨越 try 边界 → try/except 整体丢失（坍缩为 `if ...: pass / elif ...: pass / else: return y`）

**字节码模式（最小复现 repro_01）**:

```python
# 源码
def f(x, y, z, d):
    try:
        if x is None or y is None:  # BoolOp 条件
            return z
        elif x == 0:
            return z + 1
    except BaseException:
        return d
    return y

# 修复前反编译（坍缩）
def f(x, y, z, d):
    if x is None or y is None:
        pass                        # if body 丢失
    elif x == 0:
        pass                        # elif body 丢失
    else:
        return y                    # trailing return 误入 else（try/except 整体丢失）
```

**修复方案**:

新增 `_get_enclosing_structural_boundary_stop(block)` 方法：当 `boundary_stop` 为空时，遍历 `self.regions` 查找 block 所属的外层 TryExceptRegion（`block in region.try_blocks`）或 LoopRegion（`block in region.blocks`），调用其 `get_if_branch_boundary_stop(block)` 获取结构边界。优先返回 TryExceptRegion（try 体边界更严格）。

```python
# region_analyzer.py L11742-11743 (_identify_conditional_regions 内)
if not boundary_stop:
    boundary_stop = self._get_enclosing_structural_boundary_stop(block)

# region_analyzer.py L18512-18561 (新增方法)
def _get_enclosing_structural_boundary_stop(self, block) -> set:
    _try_boundary = None
    _loop_boundary = None
    for region in self.regions:
        if isinstance(region, TryExceptRegion):
            if block in region.try_blocks:
                _try_boundary = region.get_if_branch_boundary_stop(block)
                if _try_boundary:
                    return _try_boundary
        elif isinstance(region, LoopRegion):
            if block in region.blocks:
                _loop_boundary = region.get_if_branch_boundary_stop(block)
    if _try_boundary:
        return _try_boundary
    return _loop_boundary or set()
```

**算法依据**:

- **区域归约原则 3（嵌套即抽象节点）**：BoolOpRegion 嵌套于 IfRegion 嵌套于 TryExceptRegion；IfRegion 的分支收集受外层 TryExceptRegion 边界约束。
- **区域归约原则 4（入口引用语义）**：边界从父（TryExceptRegion）传播到子（IfRegion）的分支收集——父区域通过 boundary_stop 向子区域传递结构边界。
- **区域归约原则 2（每块唯一归属）**：本方法不改变 block_to_region 直接归属（BoolOpRegion 仍是 if 入口块的直接归属），仅查找外层结构区域以获取边界。
- **区域归约原则 1（自底向上归约）**：不改变归约顺序，仅在边界计算时回溯外层结构区域。
- 该查找是**结构性的**（基于区域嵌套归属 `block in region.try_blocks`），非实例特征启发式，不违反反模式禁令。

**验证（最小复现实例层）**:

| repro | 子模式 | 修复前 | 修复后 |
|---|---|---|---|
| repro_01 | `or` BoolOp + try + elif + trailing return (FULL COLLAPSE) | DEFECT-REPRO (true_diffs=29) | **NO-DEFECT** ✓ |
| repro_02 | `and` BoolOp + try | DEFECT-REPRO | **NO-DEFECT** ✓ |
| repro_03 | BoolOp 条件误编 | DEFECT-REPRO | **NO-DEFECT** ✓ |
| repro_04 | None 检查 `or` + 多 elif + try | DEFECT-REPRO | **NO-DEFECT** ✓ |

4/5 Pattern A repro 修复为 NO-DEFECT。

**为何实际 pyc 未提升**:

实际 klinedata.pyc 函数的 Pattern A 子模式与最小 repro 不同：

- **子模式 A1（本轮已修复）**：BoolOp 条件 + try-body if 坍缩。最小 repro 触发，修复有效。
- **子模式 A2（本轮未修复，残留）**：简单条件 + try-body if + 多分支 + return 触发的区域坍缩，**无 BoolOp 条件**。最小 repro_05 触发（DEFECT-REPRO 残留）。

对 `get_kline_by_count` 直接 dis 分析证实：
- 原 pyc offset 2-4：`LOAD_FAST 'asset'; POP_JUMP_FORWARD_IF_NONE 18`（**单条件，非 BoolOp**）
- 反编译 offset 2-6：`LOAD_FAST 'asset'; EXTENDED_ARG 4; POP_JUMP_FORWARD_IF_NONE 2438`（跳转目标从 18 漂移至 2438，函数末尾）
- try 块覆盖 offset 704-2310，首个失败 offset 2 在 try 块**之外**

A2 的根因（待下一轮定位）：初步排查——`_collect_branch_blocks` 在 try 体内收集 if 分支时，merge 计算或 boundary_stop 仍存在边界穿透；可能与 `_find_nearest_common_post_dominator` 在 try-body return + trailing return 场景下返回 try 外块作为 merge 有关。

## 3. 残留不一致清单（21 个，与 R03 完全一致）

### Pattern A — 控制流区域坍缩（9 函数，本轮修复 A1 子模式但实际 pyc 触发 A2 子模式）

| 函数名 | orig | decomp | true_diffs | 首个差异 | 子模式 |
|---|---|---|---|---|---|
| get_price_common | 594 | 605 | 472 | 28: POP_JUMP_FORWARD_IF_NONE → LOAD_FAST 'start_date' | A2 |
| get_kline_by_count | 478 | 478 | 392 | 2: POP_JUMP_FORWARD_IF_NONE → EXTENDED_ARG | A2 |
| get_history_common | 536 | 543 | 367 | 111: POP_JUMP_FORWARD_IF_NOT_NONE → EXTENDED_ARG | A2 |
| get_multiminute_his_data | 535 | 439 | 248 | 18: EXTENDED_ARG arg=5 → arg=3 (96 instr lost) | A2 |
| get_history_new | 352 | 262 | 132 | 65: EXTENDED_ARG arg=2 → arg=1 (90 instr lost) | A2 |
| `<module>` | 545 | 541 | 189 | 344: NOP → LOAD_CONST tuple | A2 |
| get_kline_by_date_new | 332 | 322 | 43 | 38: POP_JUMP_FORWARD_IF_NONE arg=386 → arg=216 | A2 |
| to_pd_result | 215 | 219 | 161 | 35: POP_JUMP_FORWARD_IF_NOT_NONE → EXTENDED_ARG | A2 |
| _all_bars_of_range | 17 | 16 | 3 | 14: NOP → LOAD_FAST 'data_array' | A2 |

### Pattern B — 变量作用域/名字解析错误（6 函数，未修复）

| 函数名 | true_diffs | 首个差异 |
|---|---|---|
| get_multiminute_his_data_by_date | 492 | 48: LOAD_FAST '_1m_df_nan_data' → LOAD_GLOBAL 'get_kline_time_by_asset' |
| get_history_date_and_count_ifalse | 313 | 99: LOAD_GLOBAL 'datetime' → LOAD_FAST 'query_date' |
| _all_bars_of_cache | 187 | 29: LOAD_CONST '20050101' → LOAD_FAST 'start_date' |
| get_all_real_minute_kline | 191 | 82: LOAD_GLOBAL 'range' → LOAD_GLOBAL 'system_log' |
| get_all_real_daily_kline | 137 | 51: LOAD_GLOBAL 'len' → LOAD_FAST 'list_data' |
| get_pre_date | 117 | 34: LOAD_GLOBAL 'len' → LOAD_FAST 'frequency' |

### Pattern C — 值/赋值丢失（5 函数，未修复）

| 函数名 | true_diffs | 首个差异 |
|---|---|---|
| get_kline_by_count_new | 507 | 14: UNPACK_SEQUENCE 2 → STORE_FAST 'start_000300' |
| kline_datetime_list | 208 | 148: SWAP 2 → COMPARE_OP '>' |
| klineCacheData_to_dict | 166 | 30: STORE_FAST 'symbol' → NOP |
| get_kline_by_date_one | 126 | 44: RETURN_VALUE → POP_TOP (R01 残留) |
| np_tp_pd | 111 | 56: SWAP 2 → POP_TOP |

### Pattern E — 跳转目标重编号（1 函数，未修复）

| 函数名 | jump_diffs | 首个差异 |
|---|---|---|
| get_kline_by_date_ndarray | 3 | 47: POP_JUMP_FORWARD_IF_TRUE arg=656 → arg=308 |

## 4. 回归测试结果

### testqouter/round1/ 测试矩阵

```
Pre-R04 (git stash):  1 failed, 112 passed, 105 warnings, 14 errors in 49.70s
Post-R04 (with fix):  1 failed, 112 passed, 105 warnings, 14 errors in 92.24s
```

- **1 failed**: `test_r2q_10_with_open_read.py` — FileNotFoundError: 'nonexistent.txt'（运行时文件缺失，非反编译缺陷，pre-existing）
- **14 errors**: `test_r2q_03/04/05/06/07/08/17/18/21/25/27/28/30/34` — 反编译产物含语法错误（pre-existing，与 R03 一致）
- **112 passed**: 与 R03 一致

**结论**：无回归（pre == post），R04 修复未引入新失败。

### 模块编译检查

```
python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"
imports OK
```

### 最小复现实例验证

```
15 repros: 8 NO-DEFECT, 7 DEFECT-REPRO
  - Pattern A: 4/5 NO-DEFECT (repro_01/02/03/04 fixed), 1/5 DEFECT-REPRO (repro_05 A2 残留)
  - Pattern D: 1/1 NO-DEFECT (R03 修复)
  - Pattern C: 0/4 NO-DEFECT (4 残留)
  - Pattern B: 0/1 NO-DEFECT (1 残留)
  - Pattern E: 0/1 NO-DEFECT (1 残留)
  - Controls: 3/3 NO-DEFECT (repro_13/14/15)
```

## 5. 算法 4 原则合规

- **自底向上归约**: ✓ 未改变归约顺序，仅在边界计算时回溯外层结构区域
- **每块唯一归属**: ✓ block_to_region 直接归属不变（BoolOpRegion 仍是 if 入口块的直接归属），本方法仅查找外层结构区域以获取边界
- **嵌套即抽象节点**: ✓ BoolOpRegion 嵌套于 IfRegion 嵌套于 TryExceptRegion；IfRegion 的分支收集受外层 TryExceptRegion 边界约束
- **入口引用语义**: ✓ 边界从父（TryExceptRegion）传播到子（IfRegion）的分支收集

## 6. 反模式自检

- `_fix_` / `_merge_` / `_patch_` / `_fallback_` / `_hack_` / `_workaround_` / `_temp_` 前缀: **0 新增**
  - 新方法名 `_get_enclosing_structural_boundary_stop` 不含禁止前缀（`_get_` 前缀为查询类方法命名约定）
- 硬编码深度上限: **0 新增**
- 跨区域启发式: **0 新增**（查找基于 `block in region.try_blocks` 结构归属，非实例特征）
- 后处理补丁: **0 新增**（在识别阶段 boundary_stop 计算时回溯，非后处理）
- 针对特定 pyc 的硬编码绕过: **0 新增**

## 7. 注释更新清单

### `_identify_conditional_regions` (L11035) — 6 节模板更新

在 **嵌套处理** 节追加 `[R04 fix] 边界传播` 段落（L11130-11139），文档化：
- 触发条件：if 入口块被表达式区域占用但嵌套于外层 TryExceptRegion/LoopRegion
- 回退机制：`_get_enclosing_structural_boundary_stop` 查找外层结构区域边界
- 算法依据：原则 2（不变 block_to_region）+ 原则 4（父→子边界传播）
- 关联缺陷：Pattern A1（BoolOp 条件 + try-body if 坍缩）

### `_get_enclosing_structural_boundary_stop` (L18512) — 新增方法 docstring

新增方法已包含完整 docstring（背景/问题/修复/4 原则合规），不属 `_identify_*_regions` / `_generate_*` 模板范畴（辅助方法）。

## 8. pyc_index.json 更新

`scripts/pyc_batch_verify.py single` 已自动回写 klinedata.pyc 条目：
- `decompile_status`: partial（未变，未达 100%）
- `bytecode_match_rate`: 0.5333（未变）
- `ok_py_generated`: true
- `last_tested_round`: 4

## 9. 后续轮次输入

残留 21 个不一致函数（5 类模式），建议后续轮次按以下优先级修复：

1. **Pattern A 子模式 A2（9 函数，最高发，本轮残留）**：简单条件 + try-body if + 多分支 + return 触发的区域坍缩。需深入 `region_analyzer.py:_identify_conditional_regions` 的 merge 计算与 try-body boundary_stop 交互，特别关注 `_find_nearest_common_post_dominator` 在 try-body return + trailing return 场景下返回 try 外块的问题。repro_05 为最小复现。
2. **Pattern C（5 函数）**：含 R01 残留（return 值丢失）。需修复 `region_ast_generator.py:_generate_return_ast` 在 try/except if/elif 内 return 值未正确发射。
3. **Pattern B（6 函数）**：变量作用域/名字解析。
4. **Pattern E（1 函数）**：跳转目标重编号。
