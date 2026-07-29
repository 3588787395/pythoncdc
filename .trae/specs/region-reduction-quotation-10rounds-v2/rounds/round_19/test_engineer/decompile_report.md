# R19 测试工程师报告

## 1. 基线统计

| 指标 | R18 修复后 | R19 基线 |
|------|-----------|---------|
| 总函数数 | 150 | 150 |
| 一致函数数 | 147 | **147** |
| 不一致函数数 | 3 | 3 |
| 成功率 | 98.00% | **98.00%** |
| compile_ok | True | True |

R19 基线与 R18 修复后完全一致（147/150），无退化。继承 R18 全部归一化逻辑（含传递性不一致委托、STORE_SUBSCR 消费模式检测）。

## 2. 残留 3 个不一致函数

| 函数名 | 状态 | 说明 |
|--------|------|------|
| `get_str_data` | len_diff -48 (317→269) | **R19 重点**：R18 已修复根因 A（value_target=None），R19 修复根因 B/C |
| `change_his_to_backward` | instr_diff@296 | R14 defer（指令重排） |
| `get_date_and_count` | len_diff -27 (714→687) | R13 遗留 |

## 3. R18 修复根因 A 后 get_str_data 的状态变化

### 3.1 R18 修复内容回顾

R18 修复了根因 A：`core/cfg/region_analyzer.py` merge_block 扫描循环新增 STORE_SUBSCR 检测分支。修复后 TernaryRegion@1226 的 `value_target` 从 `'i'` 纠正为 `None`，`merge_context='store'`，`container_type='dict'`，`dict_const_keys` 7 键完整捕获。

### 3.2 R19 诊断确认（get_str_data 区域结构）

运行 `_diag_ternary_detail.py` 确认 R18 修复后的状态：

```
Total TernaryRegions: 3

LoopRegion@610 children:
  IfRegion@614
  LoopRegion@760
  TernaryRegion@844
  TernaryRegion@1226

IfRegion@614:
  then_blocks: [620]
  else_blocks: [622, 760, 762, 844, 788, 838, 1096, 1120, 832, 836, 1226, 1286, 1310]
  children: []
  TernaryRegion@1226: in_then=False in_else=True
  TernaryRegion@844:  in_then=False in_else=True

TernaryRegion[0]@1226:  (R18 修复后)
  entry=1226, merge_block=1416
  value_target=None              ← R18 修复（原为 'i'）
  merge_context='store'
  container_type='dict'
  dict_const_keys=('open','close','high','low','volume','price','money')  ← 7 键

TernaryRegion[1]@844:
  entry=844, merge_block=1226
  value_target='__compare_target__'
  merge_context='compare'
  container_type=None
```

### 3.3 链式共享确认（根因 C）

```
=== Chain analysis (following merge_block -> entry) ===
  Chain from TernaryRegion[1]:
    [0] entry=844  merge=1226  container_type=None         value_target='__compare_target__'
    [1] entry=1226 merge=1416  container_type='dict'       value_target=None
    innermost.dict_const_keys=('open','close','high','low','volume','price','money')
    chain length=2, const_keys length=7
    ** MISMATCH: chain has 2 ternaries but dict has 7 keys **
```

**关键发现**：TernaryRegion@844.merge_block=1226 == TernaryRegion@1226.entry。链式共享确认存在。dict 有 7 键但链中仅 2 个三元（volume@844 + money@1226），其余 5 个值为普通 LOAD 表达式（open/close/high/low/price）。

## 4. 根因 B/C 精确定位

### 4.1 根因 B：_process_if_blocks 遗漏兄弟表达式子区域

**位置**：`core/cfg/region_ast_generator.py` `_process_if_blocks`（L12743）

**问题**：`_process_if_blocks` 在 L12774-12784 仅从 `region.children` 收集表达式子区域（BoolOpRegion/TernaryRegion）：

```python
if region and hasattr(region, 'children'):
    for child in getattr(region, 'children', []):
        ...
        elif isinstance(child, (BoolOpRegion, TernaryRegion)):
            child_region_blocks.update(child.blocks)
            if child.entry:
                child_entries.add(child.entry)
                child_expr_regions[child.entry] = child
```

但 TernaryRegion@844/@1226 的 parent 是外层 LoopRegion@610（非 IfRegion@614），因此不出现在 IfRegion@614.children 中（`children: []`）。它们的 entry（844/1226）落在 IfRegion@614.else_blocks 中，但 _process_if_blocks 不收集它们，导致 entry 被平坦化为顺序块处理并标记 generated，后续父循环遍历跳过。

**违反原则**：3（嵌套即抽象节点）+ 4（入口引用语义）。

### 4.2 根因 C：链式共享 merge_block 独占标记

**位置**：`core/cfg/region_ast_generator.py` `_generate_ternary` 及子区域循环（L9195-9235）

**问题**：TernaryRegion@844.merge_block=1226 == TernaryRegion@1226.entry。当 TernaryRegion@844 被生成时，`region.blocks`（含共享 merge_block 1226）被标记为 generated（L9233-9234）：

```python
for b in child.blocks:
    self.generated_blocks.add(b)
```

导致 TernaryRegion@1226 的 entry（1226）已在 generated_blocks 中，后续子区域循环检测到 `child.entry in self.generated_blocks`（L9256）而跳过整个 TernaryRegion@1226。

**违反原则**：2（每块唯一归属）—— merge_block 1226 同时是前驱的 merge 和后继的 entry，前驱不应独占标记。

### 4.3 R12 回退原因回顾（为何 R19 可安全修复）

R12 尝试修复 B/C 时导致 -48→-69 退化，根因是 A 未修复：
- 兄弟区域收集将 TernaryRegion@1226 的 blocks 标记为 generated，导致 numpy.nan（1286）和 money.sum()（1310-1406）被跳过
- TernaryRegion@1226 的 value_target='i' 导致 _generate_ternary 生成 `i = i + 1`（错误赋值）

R18 已修复根因 A（value_target=None, container_type='dict'），R19 可安全修复 B/C。

## 5. 最小复现实例（10 个）

10 个复现实例演示根因 B/C 的各个侧面：

| 复现实例 | 演示要点 | 根因 |
|---------|---------|------|
| repro_01_sibling_ternary_in_if_else | IfRegion else 中的兄弟三元 | B |
| repro_02_chain_shared_merge_block | 三元链式共享 merge_block | C |
| repro_03_combined_b_c_loop_if_ternary | 循环内 IfRegion else + 链式三元 | B+C |
| repro_04_dict_with_ternary_and_load | 7 键 dict 含三元 + 普通载入 | B+C+A |
| repro_05_loop_dict_assign_ternary | 循环中 dict 赋值 + 三元值 | B+C |
| repro_06_ternary_merge_is_next_entry | 三元 merge == 后继 entry | C |
| repro_07_if_else_expr_subregion_not_child | 表达式子区域不在 children | B |
| repro_08_loop_if_else_ternary_siblings | 循环内 IfRegion + 兄弟三元 | B |
| repro_09_chained_ternary_dict_store_subscr | 链式三元 + STORE_SUBSCR | C+A |
| repro_10_get_str_data_full_pattern | get_str_data 完整模式 | B+C+A |

全部 10 个 repro `py_compile` 通过。

## 6. 反编译产物

| 检查项 | 结果 |
|--------|------|
| /tmp/r19_decompiled.py | 生成成功（src_len=175488, src_lines=3641） |
| compile(src, '<decompiled>', 'exec') | OK |
| 反编译耗时 | ~1.8s |

## 7. 对修复工程师的建议

### 7.1 根因 B 修复方向

在 `_process_if_blocks` 中，扩展 `child_expr_regions` 收集逻辑：不仅从 `region.children` 收集，还要从 `then_blocks/else_blocks` 中的块所属区域收集兄弟表达式子区域（通过 `get_entry_region_for_block` 查找以该块为 entry 的 BoolOpRegion/TernaryRegion，即使其 parent 不是当前 IfRegion）。

守卫：若兄弟表达式子区域的 parent 是嵌套 IfRegion 且其 entry 也在 blocks 中，跳过（交由嵌套 IfRegion 统一生成）。

### 7.2 根因 C 修复方向

在子区域循环（L9195-9235）标记 TernaryRegion.blocks 为 generated 时，检查 merge_block 是否同时是另一个 TernaryRegion 的 entry。若是，不标记该共享 merge_block 为 generated（或允许后继三元正常生成）。

### 7.3 修复约束

- 必须符合区域归约算法 4 原则
- 禁止跨区域跨层次启发式规则、后处理修正
- 禁止新增 `_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀方法
- 禁止新增硬编码深度上限
- 禁止修改反编译产物文件
- **若修复导致退化，必须回退**
