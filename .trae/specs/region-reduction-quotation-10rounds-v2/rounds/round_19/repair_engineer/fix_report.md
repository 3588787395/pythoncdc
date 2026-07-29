# R19 修复工程师报告

## 1. 修复目标

- **目标**: 在 R18 修复根因 A（TernaryRegion `value_target` 对 STORE_SUBSCR 误识别）的基础上，修复根因 B/C，完成 `get_str_data` 的完整修复（-48 → 0 或收窄）。
- **R18 基线**: 147/150 (98.00%)，get_str_data len_diff -48 (317→269)，残留 3 个不一致函数。
- **R19 策略**: R18 已修复根因 A（`value_target` 从 `'i'` 纠正为 `None`，`container_type='dict'`，`dict_const_keys` 7 键完整捕获）。R19 在此基础上修复根因 B（`_process_if_blocks` 遗漏兄弟表达式子区域）+ 根因 C（链式共享 merge_block 独占标记）。

## 2. 根因分析（R19 聚焦根因 B+C）

### 2.1 三层根因回顾

| 根因 | 描述 | R12 处置 | R18 处置 | R19 处置 |
|------|------|---------|---------|---------|
| A | BUILD_CONST_KEY_MAP+STORE_SUBSCR dict 构造消费模式未建模。TernaryRegion@1226 被误赋 `value_target='i'` | 未修复（B+C 暴露 A 导致 -48→-69 退化，回退） | **已修复**（`value_target=None`，`container_type='dict'`） | 继承 R18 |
| B | `_process_if_blocks` 仅从 region.children 收集表达式子区域，遗漏 IfRegion@614 else_blocks 中的兄弟 TernaryRegion@844/@1226 | 尝试修复导致退化，回退 | deferred | **R19 重点** |
| C | TernaryRegion@844.merge_block=1226 == TernaryRegion@1226.entry 链式共享，前驱独占标记 merge_block 为 generated | 尝试修复导致退化，回退 | deferred | **R19 重点** |

### 2.2 根因 B 精确定位

**位置**: `core/cfg/region_ast_generator.py` `_process_if_blocks`（L12783 区域）

**问题**: `_process_if_blocks` 仅从 `region.children` 收集表达式子区域（BoolOpRegion/TernaryRegion）。但 TernaryRegion@844/@1226 的 parent 是外层 LoopRegion@610（非当前 IfRegion@614），因此不出现在 IfRegion@614.children 中（`children: []`）。它们的 entry（844/1226）落在 IfRegion@614.else_blocks 中，但 `_process_if_blocks` 不收集它们，导致 entry 被平坦化为顺序块处理并标记 generated，后续父循环遍历跳过。

**违反原则**: 3（嵌套即抽象节点）+ 4（入口引用语义）。

### 2.3 根因 C 精确定位

**位置**: `core/cfg/region_ast_generator.py` 子区域生成循环（L13074 区域）

**问题**: TernaryRegion@844.merge_block=1226 == TernaryRegion@1226.entry。当 TernaryRegion@844 被生成时，`region.blocks`（含共享 merge_block 1226）被标记为 generated。导致 TernaryRegion@1226 的 entry（1226）已在 generated_blocks 中，后续子区域循环检测到 `child.entry in self.generated_blocks` 而跳过整个 TernaryRegion@1226。

**违反原则**: 2（每块唯一归属）—— merge_block 1226 同时是前驱的 merge 和后继的 entry，前驱不应独占标记。

## 3. 修复方案（尝试）

### 3.1 根因 B 修复（兄弟表达式子区域收集）

**文件**: `core/cfg/region_ast_generator.py` `_process_if_blocks`
**改动**: 在 `_block_set = set(blocks)` 之后，扫描 blocks 通过 `get_entry_region_for_block` 收集兄弟表达式子区域（BoolOpRegion/TernaryRegion），补充加入 `child_expr_regions`。守卫：跳过 parent 是嵌套 IfRegion 且其 entry 也在 blocks 中的（交由嵌套 IfRegion 统一生成）。

### 3.2 根因 C 修复（链式共享 merge_block 处理）

**文件**: `core/cfg/region_ast_generator.py` 子区域生成循环
**改动**: 在标记 `child.blocks` 为 generated 之后，检测当前 TernaryRegion 的 merge_block 是否同时是另一个 TernaryRegion 的 entry（链式共享）。若是，且后继 TernaryRegion 尚未生成，则从 generated_blocks 中 discard 共享 merge_block，使后继 TernaryRegion 能以该块为 entry 正常归约。

### 3.3 算法依据（4 原则对应）

| 原则 | 对应条款 |
|------|---------|
| 1. 自底向上归约 | 修复在 AST 生成阶段（`_process_if_blocks` / 子区域循环），不跨层引用，不后处理 |
| 2. 每块唯一归属 | **核心（根因 C）**：链式共享 merge_block 不被前驱独占，discard 后允许后继以该块为 entry 归约 |
| 3. 嵌套即抽象节点 | **核心（根因 B）**：兄弟表达式子区域作为抽象节点被收集，不被平坦化为顺序块 |
| 4. 入口引用语义 | 兄弟三元通过 entry 引用加入 `child_expr_regions`，符合入口引用语义 |

## 4. 回退原因：引入退化（-48 → -84）

### 4.1 修复后回归结果

| 指标 | R18 基线 | R19 修复后 | 变化 |
|------|---------|-----------|------|
| 总函数数 | 150 | 150 | — |
| 一致函数数 | 147 | **147** | — (无整体退化) |
| 不一致函数数 | 3 | 3 | — |
| 成功率 | 98.00% | **98.00%** | — |
| compile_ok | True | True | — |
| **get_str_data diff** | **-48 (317→269)** | **-84 (317→233)** | **退化 ✗** |

**关键退化**：`get_str_data` 的 len_diff 从 -48 恶化到 -84（new_len 269→233，多丢失 36 条指令）。这比 R12 的 -48→-69 退化更严重。

### 4.2 退化机制分析

R18 修复根因 A 后，TernaryRegion@1226 的 `value_target` 已为 None（不再误生成 `i = i + 1`）。但根因 B 的兄弟区域收集将更多 TernaryRegion 的 blocks（含 1226-1416）标记为 generated，导致：

1. **兄弟三元 blocks 被标记 generated 后跳过**：兄弟表达式子区域收集（B）将 TernaryRegion@844/@1226 的 blocks 加入 `child_region_blocks`，生成后标记为 generated。但这些 blocks 中的 `numpy.nan`（1286）、`money.sum()`（1310-1406）等表达式本应作为 dict value 或 bare expr 发射，被"已生成"标记跳过。
2. **dict 构造消费模式仍未完整建模**：根因 A 仅修复了 `value_target` 检测（STORE_SUBSCR 时 break），但 `BUILD_CONST_KEY_MAP` 消费模式（7 个值表达式作为整体 dict 构造语句归约）仍未建模。兄弟区域收集暴露了这一深层缺陷：7 个值表达式（含 2 三元 + 5 普通载入）应作为 dict value 整体归约，而非独立 TernaryRegion/bare expr。
3. **链式共享 merge_block discard 副作用**：根因 C 的 discard 使后继三元能以共享 merge_block 为 entry 归约，但后继三元的 blocks 仍被标记 generated，进一步扩大"已生成"范围。

### 4.3 与 R12 退化对比

| 项 | R12 退化（-48→-69） | R19 退化（-48→-84） |
|----|---------------------|---------------------|
| 根因 A 状态 | 未修复（`value_target='i'`） | 已修复（`value_target=None`） |
| 退化量 | -21（269→248） | -36（269→233） |
| 退化机制 | 兄弟区域收集 + `value_target='i'` 误生成 `i = i + 1` | 兄弟区域收集 + dict 构造消费模式未建模 |
| 根本原因 | 根因 A 未修复 | **dict 构造消费模式（BUILD_CONST_KEY_MAP）未完整建模** |

**关键结论**：R18 修复根因 A（`value_target` 检测）是必要但不充分的。完整修复 `get_str_data` 需建模 `BUILD_CONST_KEY_MAP` 消费模式——当三元/载入的 merge_block 直接进入 `BUILD_CONST_KEY_MAP n` + `STORE_SUBSCR` 时，这些值表达式应作为整体 dict 构造语句归约，而非独立 TernaryRegion/bare expr。在此深层缺陷未解决前，根因 B/C 的修复（兄弟区域收集）会暴露并放大该缺陷，造成净退化。

### 4.4 回退决策

依据 spec 硬约束"若修复导致退化，必须回退"及用户验证标准"get_str_data diff 改善（-48 → 0 或收窄）"，**回退此修复**，恢复 -48 基线。

```bash
git checkout core/cfg/region_ast_generator.py
```

回退后 `region_ast_generator.py` 与 HEAD（R18 commit 855b96b）字节一致（`git diff` 为空）。

## 5. 回退后回归结果

### 5.1 一致性统计

| 指标 | R18 基线 | R19 回退后 | 变化 |
|------|---------|-----------|------|
| 总函数数 | 150 | 150 | — |
| 一致函数数 | 147 | **147** | — (无退化) ✓ |
| 不一致函数数 | 3 | 3 | — |
| 成功率 | 98.00% | **98.00%** | — |
| compile_ok | True | True | — |
| get_str_data diff | -48 | **-48** | — (回退至基线) ✓ |

### 5.2 残留不一致函数（3 个，均 deferred）

| 函数名 | 状态 | 说明 |
|--------|------|------|
| `get_str_data` | len_diff -48 (317→269) | R19 尝试修复 B/C 导致 -48→-84 退化已回退；完整修复需建模 BUILD_CONST_KEY_MAP 消费模式 |
| `change_his_to_backward` | instr_diff@296 | R14 defer（指令重排） |
| `get_date_and_count` | len_diff -27 (714→687) | R13 遗留（deferred） |

### 5.3 既有区域测试矩阵（0 退化）

回退后 `region_ast_generator.py` == HEAD，矩阵结果 == R18 基线：

| 区域 | pass | fail | 说明 |
|------|------|------|------|
| IF | 73 | 4 | 既有基线失败 |
| LOOP | 77 | 3 | 既有基线失败 |
| TRY | 71 | 9 | 既有基线失败 |
| WITH | 78 | 2 | 既有基线失败 |
| MATCH | 78 | 0 | — |
| ASSERT | 16 | 10 | 既有基线失败 |
| BOOLOP | 79 | 0 | — |
| TERNARY | 64 | 5 | 既有基线失败 |
| CC | 37 | 3 | 既有基线失败 |
| SEQ | 80 | 0 | — |
| **总计** | **653** | **36** | **0 退化** ✓ |

**退化验证**：通过 `git stash` 暂存修复运行矩阵 → `git stash pop` 恢复 → 再次运行矩阵，两次结果完全一致（IF/LOOP/TRY/TERNARY/BOOLOP 均通过 stash 对比验证 0 退化）。

### 5.4 编译与导入

| 检查项 | 结果 |
|--------|------|
| `compile /tmp/r19_decompiled.py` | COMPILE_OK ✓ |
| `import core.cfg.region_analyzer; import core.cfg.region_ast_generator` | IMPORT_OK ✓ |
| 反编译产物 src_len | 175488 (3641 lines) ✓ |
| 反编译耗时 | ~1.8s ✓ |

### 5.5 最小复现实例（G5）

10 个 repro 全部 `py_compile` 通过（R19 重点针对根因 B/C）：
repro_01_sibling_ternary_in_if_else / repro_02_chain_shared_merge_block / repro_03_combined_b_c_loop_if_ternary / repro_04_dict_with_ternary_and_load / repro_05_loop_dict_assign_ternary / repro_06_ternary_merge_is_next_entry / repro_07_if_else_expr_subregion_not_child / repro_08_loop_if_else_ternary_siblings / repro_09_chained_ternary_dict_store_subscr / repro_10_get_str_data_full_pattern

## 6. 反模式自检

| 检查项 | 结果 |
|--------|------|
| `_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀方法 | 0 新增 ✓（代码 diff 为空，已回退） |
| 硬编码深度上限 | 0 新增 ✓ |
| 跨区域跨层次启发式规则 | 0 新增 ✓ |
| 后处理修正 | 0 新增 ✓ |
| 修改反编译产物文件 | 无 ✓ |

## 7. docstring 合规（G8）

本次修复尝试已回退，`region_ast_generator.py` == HEAD（R18 commit 855b96b），`_process_if_blocks` docstring 维持 V1 R8 的 6 节统一模板，**无变更**。

## 8. 算法 4 原则符合度

| 原则 | 状态 | 说明 |
|------|------|------|
| 1. 自底向上归约 | ✓ | 修复尝试在 AST 生成阶段，不跨层，不后处理（已回退） |
| 2. 每块唯一归属 | ✓ | 修复尝试遵循原则 2（链式共享 merge_block 不独占），但因深层缺陷退化已回退 |
| 3. 嵌套即抽象节点 | ✓ | 修复尝试遵循原则 3（兄弟区域作为抽象节点），但因深层缺陷退化已回退 |
| 4. 入口引用语义 | ✓ | 修复尝试遵循原则 4（entry 引用），但因深层缺陷退化已回退 |

当前代码 == HEAD，4 原则合规状态 == R18（PASS）。

## 9. 正确修复路径（deferred，需后续轮次）

完整修复 `get_str_data` 需同时解决三层：

1. **区域识别层（根因 A 已修复，但 BUILD_CONST_KEY_MAP 消费模式未完整建模）**：
   - R18 已修复 `value_target` 检测（STORE_SUBSCR 时 break，`value_target=None`）。
   - **待修复**：建模 `BUILD_CONST_KEY_MAP n` 消费模式——当三元/载入的 merge_block 直接进入 `BUILD_CONST_KEY_MAP n` + `STORE_SUBSCR` 时，这些值表达式是 dict value，应作为整体 dict 构造语句归约，而非独立 TernaryRegion/bare expr。
   - 涉及 `_identify_ternary_regions` 的区域边界：TernaryRegion@1226 的 entry 不应包含前驱 `price` 载入块（1226-1270），应从条件测试点（1274）开始。

2. **生成层（根因 B/C）**：
   - 在 BUILD_CONST_KEY_MAP 消费模式建模稳定后，重新应用 R19 的兄弟表达式子区域收集（根因 B）+ 链式共享 merge_block 处理（根因 C）。
   - R19 已验证：BUILD_CONST_KEY_MAP 消费模式未建模时，B/C 修复会导致 -48→-84 退化。

3. **dict value 表达式整体归约**：
   - 7 个值表达式（含 2 三元 + 5 普通载入）应作为 dict value 整体归约，由 `container_type='dict'` + `dict_const_keys` 标记的 TernaryRegion 统一生成 `data.loc[i] = {...}` 语句。

此修复涉及区域识别核心逻辑（`_identify_ternary_regions` 的 BUILD_CONST_KEY_MAP 消费模式建模 + 区域边界对齐），影响面广，需配套最小复现实例回归，**不在 R19 单轮内完成**，避免 destabilize 147 基线。

## 10. R19 产出

### 测试工程师阶段（完成）：
- `test_engineer/decompile_report.md`（含 R18 修复根因 A 后 get_str_data 状态变化 + 根因 B/C 精确定位 + 10 个最小复现实例）
- `test_engineer/decompile_quotation.py` / `exact_match_stats.py` / `diff_detail.py`
- `test_engineer/_diag_ternary.py` / `_diag_bytecode.py` / `_diag_ternary_detail.py`（诊断工具）
- `test_engineer/minimal_repros/repro_01..repro_10.py`（10 个最小复现实例，重点根因 B/C）

### 修复工程师阶段（根因已定位，修复因退化已回退）：
- `repair_engineer/fix_report.md`（本报告）

## 11. 异常说明

R19 未实现 `get_str_data` 的净改善（-48 未变）。原因：R18 修复根因 A（`value_target` 检测）是必要但不充分的。`get_str_data` 的 -48 根因涉及 **dict 构造消费模式建模**（`BUILD_CONST_KEY_MAP` + `STORE_SUBSCR`），属于区域识别层的功能扩展（非局部 bug 修复），影响面广、风险高。

R19 尝试的局部修复（根因 B 兄弟表达式子区域收集 + 根因 C 链式共享 merge_block 处理）因暴露 `BUILD_CONST_KEY_MAP` 消费模式未建模的深层缺陷，引入 -48→-84 退化（比 R12 的 -48→-69 更严重），按"0 退化"硬约束回退。

**关键教训**：R12 退化的根本原因不仅是根因 A（`value_target` 误识别），还包括更深的 `BUILD_CONST_KEY_MAP` 消费模式未建模。R18 修复根因 A 消除了 `value_target='i'` 的误识别，但 `BUILD_CONST_KEY_MAP` 消费模式仍未建模，因此 B/C 修复仍会退化。完整修复需先建模 `BUILD_CONST_KEY_MAP` 消费模式（区域识别层），再应用 B/C 修复（生成层）。

建议后续轮次（R20+）优先攻克：
1. `_identify_ternary_regions` 的 `BUILD_CONST_KEY_MAP` 消费模式建模（dict value 表达式作为整体语句归约）
2. TernaryRegion@1226 的区域边界对齐（entry 不应包含前驱 price 载入块）
3. 在上述 2 项稳定后，重新应用 R19 的兄弟表达式子区域收集（根因 B）+ 链式共享 merge_block 处理（根因 C）
