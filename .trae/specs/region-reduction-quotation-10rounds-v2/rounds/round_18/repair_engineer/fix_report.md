# R18 修复工程师报告

## 1. 修复目标

- **目标函数**: `get_str_data`（len_diff -48，BUILD_CONST_KEY_MAP+STORE_SUBSCR dict 构造消费模式未建模）
- **R17 基线**: 147/150 (98.00%)，残留 3 个不一致函数
- **修复方向**: 优先修复根因 A（TernaryRegion 的 value_target 对 STORE_SUBSCR 的误识别），这是 R12 退化的根本原因。按 R18 策略："只有修复根因 A 后，根因 B/C 的修复才不会退化"。

## 2. 根因分析

### 2.1 三层根因回顾（R12 已定位）

| 根因 | 描述 | R12 处置 |
|------|------|---------|
| A（主因）| BUILD_CONST_KEY_MAP+STORE_SUBSCR dict 构造消费模式未建模。TernaryRegion@1226 被误赋 `value_target='i'`（STORE_SUBSCR 的下标 `i` 被误识别为三元消费目标），导致生成 `i = i + 1` 而非 money 三元 | 未修复（R12 修复 B+C 暴露 A 导致 -48→-69 退化，回退） |
| B | `_process_if_blocks` 仅从 region.children 收集表达式子区域，遗漏兄弟 TernaryRegion | R12 尝试修复导致退化，回退 |
| C | TernaryRegion@844.merge_block=1226 == TernaryRegion@1226.entry 链式共享 | R12 尝试修复导致退化，回退 |

### 2.2 根因 A 精确定位

在 `core/cfg/region_analyzer.py` 的 `_identify_ternary_regions` 调用链中，merge_block 扫描循环（约 L14525）负责检测 TernaryRegion 的 `value_target` 与 `merge_context`。

**历史问题**：扫描循环仅检查 `STORE_FAST/STORE_NAME/STORE_GLOBAL/STORE_DEREF`（简单变量赋值目标），未处理 `STORE_SUBSCR`（下标赋值目标）。当 merge_block 含 `BUILD_CONST_KEY_MAP 7 + STORE_SUBSCR`（即 `data.loc[i] = {...}`）时：
1. 扫描跳过 STORE_SUBSCR（不在检测列表）
2. 继续扫描到后续 `STORE_FAST 'i'`（属于下一条语句 `i += 1`）
3. 误赋 `value_target='i'`、`merge_context='store'`
4. AST 生成 `i = (ternary)` 而非 dict 构造 `data.loc[i] = {...}`

### 2.3 诊断确认（`_diag_ternary.py`）

修复前（R12 记录）：TernaryRegion@1226 `value_target='i'`（误识别）
修复后（R18 诊断）：

```
TernaryRegion[0]: entry=1226 merge_block=1416
  value_target=None              ← 修复前为 'i'，现已正确
  merge_context='store'          ← 正确识别 STORE_SUBSCR 消费
  container_type='dict'          ← BUILD_CONST_KEY_MAP 已识别
  dict_const_keys=('open', 'close', 'high', 'low', 'volume', 'price', 'money')  ← 7 键完整
  merge_block instructions:
    1416 LOAD_CONST (7 keys)
    1418 BUILD_CONST_KEY_MAP 7
    1420 LOAD_FAST 'data'
    1422 LOAD_ATTR 'loc'
    1432 LOAD_FAST 'i'
    1434 STORE_SUBSCR            ← 下标赋值消费点
```

## 3. 修复方案

### 3.1 修复点

**文件**: `core/cfg/region_analyzer.py`
**位置**: merge_block 扫描循环（L14525 区域），在 `STORE_FAST/STORE_NAME/...` 检测之前
**改动**: 新增 `STORE_SUBSCR` 检测分支

```python
for instr in merge_block.instructions:
    if instr.opname in NOISE_OPS:
        continue
    # [R18 根因 A] STORE_SUBSCR (如 `data.loc[i] = ...`) 是下标
    # 赋值目标，不是简单变量赋值。value_target 保持 None（表示
    # 非简单变量目标），由 container_type / 后续 AST 生成路径处理。
    # 依「每块唯一归属」: STORE_SUBSCR 是 ternary 值的消费者
    # （经 BUILD_CONST_KEY_MAP 等容器构造），其后续指令属于下一
    # 条语句，不应继续扫描到后续 STORE_FAST 而误识别 value_target。
    if instr.opname == 'STORE_SUBSCR':
        merge_context = 'store'
        break
    if instr.opname in ('STORE_FAST', 'STORE_NAME',
                        'STORE_GLOBAL', 'STORE_DEREF'):
        ...
```

### 3.2 算法依据（4 原则对应）

| 原则 | 对应条款 |
|------|---------|
| 1. 自底向上归约 | 修复发生在 `_identify_ternary_regions`（Phase 2 区域识别阶段），不跨层引用，不后处理 |
| 2. 每块唯一归属 | **核心**：STORE_SUBSCR 是 ternary 值的消费者（经 BUILD_CONST_KEY_MAP 容器构造）。其后续指令（如 `STORE_FAST 'i'` 即 `i += 1`）属于下一条语句，不应被本 ternary 扫描吸收。`break` 守卫确保 merge_block 的 POST-STORE_SUBSCR 部分归属下一条语句 |
| 3. 嵌套即抽象节点 | 不引入跨区域启发式；STORE_SUBSCR 的容器构造（dict）作为抽象节点由 container_type 标记 |
| 4. 入口引用语义 | value_target=None 表示非简单变量目标，由 container_type / 后续 AST 生成路径按入口引用语义处理 |

### 3.3 修改范围

仅修改 `core/cfg/region_analyzer.py` 一个文件，新增 13 行（含注释），无方法签名变更，无新增方法。

### 3.4 为何 get_str_data diff 未收窄（-48 未变）

根因 A 修复后，TernaryRegion[0] 的 `value_target` 已正确为 None，`container_type='dict'`、`dict_const_keys` 7 键完整捕获。但 get_str_data 的 -48 diff 未收窄，原因：

1. **根因 B/C 仍 deferred**：`_process_if_blocks` 遗漏兄弟 TernaryRegion（B）+ 链式共享 merge_block（C）未修复。R12 已验证：在根因 A 未修复时尝试 B/C 会导致 -48→-69 退化。
2. **仅 3/7 三元被识别**：get_str_data 有 7 个三元表达式作为 dict 值（open/close/high/low/volume/price/money），当前仅识别 3 个 TernaryRegion。完整修复需 B/C 配合。
3. **R18 策略符合**：本轮优先安全修复根因 A（foundation），为后续轮次修复 B/C 铺路。根因 A 是 R12 退化的根本原因，必须先修复且不退化。

**关键**：根因 A 修复无退化（147/150 维持），符合"若修复导致退化，必须回退"的硬约束。get_str_data 的完整修复（-48→0）需后续轮次在 A 的基础上修复 B/C。

## 4. 回归结果

### 4.1 一致性统计

| 指标 | R17 基线 | R18 修复后 | 变化 |
|------|---------|-----------|------|
| 总函数数 | 150 | 150 | — |
| 一致函数数 | 147 | **147** | — (无退化) ✓ |
| 不一致函数数 | 3 | 3 | — |
| 成功率 | 98.00% | **98.00%** | — |
| compile_ok | True | True | — |

### 4.2 残留不一致函数（3 个，均 deferred）

| 函数名 | 状态 | 说明 |
|--------|------|------|
| `get_str_data` | len_diff -48 | R18 修复根因 A（value_target 已纠正），B/C deferred |
| `change_his_to_backward` | instr_diff@296 | R14 defer（指令重排） |
| `get_date_and_count` | len_diff -27 | R13 遗留（deferred） |

### 4.3 既有区域测试矩阵（0 退化）

| 指标 | R17 基线（stash 验证） | R18 修复后 | 变化 |
|------|----------------------|-----------|------|
| passed | 318 | 318 | — ✓ |
| failed | 9 | 9 | — ✓ |
| skipped | 11 | 11 | — ✓ |

**退化验证方法**：`git stash` 暂存修复 → 运行矩阵（9 fail/318 pass/11 skip）→ `git stash pop` 恢复修复 → 运行矩阵（9 fail/318 pass/11 skip）。两次结果完全一致，9 个失败用例相同（TestL03ForElse / TestL04WhileElse / TestE03TryExceptElse / TestN11TryWhileContinue / TestXP04BoolOpInIf / TestXP07NestedTernary / TestCO09WhileIfWhileBreak / TestDEEP12 / TestDEEP16 均为既有基线失败，非 R18 引入）。

### 4.4 编译与导入

| 检查项 | 结果 |
|--------|------|
| `compile /tmp/r18_decompiled.py` | COMPILE_OK ✓ |
| `import core.cfg.region_analyzer; import core.cfg.region_ast_generator` | IMPORT_OK ✓ |
| 反编译产物 src_len | 175488 (3641 lines) ✓ |
| 反编译耗时 | 1.73s ✓ |

### 4.5 最小复现实例（G5）

10 个 repro 全部 `py_compile` 通过：
repro_01_const_key_map_store_subscr_basic / repro_02_ternary_in_dict_value / repro_03_multi_key_ternary_dict / repro_04_value_target_store_fast_ok / repro_05_value_target_store_subscr_misid / repro_06_dict_loc_assign_pattern / repro_07_ternary_then_dict_construction / repro_08_loop_with_dict_assign / repro_09_chained_ternary_dict_values / repro_10_get_str_data_pattern

## 5. 算法 4 原则符合度

| 原则 | 状态 | 说明 |
|------|------|------|
| 1. 自底向上归约 | ✓ | 修复在 Phase 2 区域识别阶段（_identify_ternary_regions），不跨层，不后处理 |
| 2. 每块唯一归属 | ✓ | STORE_SUBSCR 是 ternary 值消费者；break 守卫确保后续指令（i += 1）归属下一条语句，不被误吸收 |
| 3. 嵌套即抽象节点 | ✓ | dict 容器构造作为抽象节点由 container_type='dict' 标记，不跨区域启发式 |
| 4. 入口引用语义 | ✓ | value_target=None 表示非简单变量目标，由 container_type / AST 生成路径按入口引用处理 |

## 6. 反模式自检

| 检查项 | 结果 |
|--------|------|
| `_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀方法 | 0 新增 ✓ |
| 硬编码深度上限 | 0 新增 ✓ |
| 跨区域跨层次启发式规则 | 0 新增 ✓ |
| 后处理修正 | 0 新增（修复在识别阶段，非后处理）✓ |
| 修改反编译产物文件 | 无 ✓ |

## 7. docstring 合规（G8）

`_identify_ternary_regions` 方法已具备 6 节统一模板（算法依据 / 归约顺序 / 唯一归属判定 / ...），继承 V1 R8。本次修复为 merge_block 扫描循环内新增 STORE_SUBSCR 分支，属 merge_context 检测细化（docstring 已覆盖 merge_context 赋值/返回/容器等变体）。修复点以详尽内联注释文档化（含根因、算法依据、历史问题、4 原则对应），无需改动方法级 docstring。

## 8. 总结

R18 优先修复根因 A（TernaryRegion value_target 对 STORE_SUBSCR 的误识别），这是 R12 退化的根本原因：

1. **修复点**：`core/cfg/region_analyzer.py` merge_block 扫描循环新增 STORE_SUBSCR 检测分支，遇 STORE_SUBSCR 时设 `merge_context='store'` 并 `break`，防止继续扫描到后续 STORE_FAST 'i' 而误赋 value_target。
2. **修复效果**：TernaryRegion[0] `value_target` 从 `'i'` 纠正为 `None`，`merge_context='store'`，`container_type='dict'`，`dict_const_keys` 7 键完整捕获。
3. **无退化**：147/150 维持；既有矩阵 9 fail/318 pass/11 skip 与基线完全一致（stash 验证）；IMPORT_OK；10 repros compile OK；0 新增反模式。
4. **get_str_data diff 未收窄（-48）**：根因 A 是 foundation 修复，完整闭合需后续轮次在 A 基础上修复 B/C（R12 已验证 A 未修复时 B/C 导致 -48→-69 退化）。
5. **算法合规**：4 原则 FULLY COMPLIANT，核心依据"每块唯一归属"——STORE_SUBSCR 是消费者，后续指令归属下一条语句。
