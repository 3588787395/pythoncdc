# R12 测试工程师：反编译报告

## 1. 总体统计

- 总函数数: 150
- 一致函数数: 144
- 不一致函数数: 6
- 成功率: 96.00%
- compile_ok: True
- V2-R11 基线: 144/150 (96.00%) — R12 不得退化

## 2. 残留不一致函数清单（6 个）

| 函数 | 状态 | orig_len | new_len | diff |
|------|------|----------|---------|------|
| `<module>` | instr_diff@394 | - | - | - |
| `one_prod_to_dataframe` | instr_diff@131 | - | - | - |
| `build_future_fill_time` | instr_diff@226 | - | - | - |
| `get_str_data` | len_diff | 317 | 269 | -48 |
| `change_his_to_backward` | instr_diff@296 | - | - | - |
| `get_date_and_count` | len_diff | 714 | 687 | -27 |

## 3. 缺陷分类（按区域类型 + 算法原则）

### P0 Loop 区域缺陷（2 个，真算法缺陷）

- **get_str_data** (len_diff -48)：Loop 嵌套 for/while 循环体语句丢失。`_generate_loop` 在 LoopRegion@610 的子区域分发中，IfRegion@614 (if datas: continue) 的 else_blocks 包含兄弟 TernaryRegion@844/@1226 的 entry，`_if_generate_else_branch` 不分发 TernaryRegion/BoolOpRegion（不同于 then 分支），导致 TernaryRegion 块被平坦化为顺序块并标记 generated，后续父循环遍历跳过。违反原则 3（嵌套即抽象节点）+ 原则 4（入口引用语义）。R12 重点。
- **get_date_and_count** (len_diff -27)：Loop+Conditional while 循环 if/elif 链语句丢失。while 体内 if/elif 链未完整生成。违反原则 1（自底向上归约）+ 原则 3。待后续迭代。

### P1 跳转目标归一化差异（3 个，语义等价）

- **one_prod_to_dataframe** (instr_diff@131)：首个 `i==0` 提取为外层 if，原始跳到下一 elif，跳转目标偏移。归一化已对齐指令索引，残留偏移差异。违反原则 4。
- **build_future_fill_time** (instr_diff@226)：listcomp 内部 code 对象布局 + 后续跳转目标偏移。违反原则 4。
- **change_his_to_backward** (instr_diff@296)：for 循环内嵌套 if 的 else 体已恢复，残留跳转目标偏移。违反原则 4。

### P2 元数据差异（1 个，非算法缺陷）

- **`<module>`** (instr_diff@394)：嵌套 code 对象 co_filename 原始为 `./fly_docker_py311/fly/data/quotation.py`，反编译产物为 `<decompiled>`。违反原则 4（入口引用语义，co_filename 引用语义）。

## 4. 详细 diff

见 `diff_detail.txt`（/tmp/r12_out/diff_detail.txt），含 6 个残留函数 orig vs new 指令逐行对比。

## 5. get_str_data -48 指令详细分析（R12 重点）

`get_str_data` orig_len=317 / new_len=269 / diff=-48，first_diff_idx=9。

### 5.1 区域结构（_diag_regions.py 输出）

```
LoopRegion@610 (for datas in datass_list[count:]) parent=LoopRegion@54
  body_blocks=[610, 614, 620, 622, 760, 762, 788, 832, 836, 838, 844, 1096, 1120, 1226, 1286, 1310, 1416]
  children=['IfRegion@614', 'LoopRegion@760', 'TernaryRegion@844', 'TernaryRegion@1226']

IfRegion@614 (if datas: continue) merge=610 (loop header)
  then_blocks=[620]  # JUMP_BACKWARD (continue)
  else_blocks=[622, 760, 762, 844, 788, 838, 1096, 1120, 832, 836, 1226, 1286, 1310]
  children=[]  # ← 空子区域列表！

TernaryRegion@844 blocks=[844, 1096, 1120, 1226] merge=1226 merge_context=compare
TernaryRegion@1226 blocks=[1226, 1286, 1310, 1416] merge=1416 merge_context=store
```

### 5.2 根因（两层）

**根因 A（生成层，主因）**：`_if_generate_else_branch` 不分发 TernaryRegion/BoolOpRegion 子区域。

- IfRegion@614 的 else_blocks 包含兄弟 TernaryRegion@844 (entry=844) 和 TernaryRegion@1226 (entry=1226) 的 entry。
- `_if_generate_else_branch` 现有两阶段收集：
  - phase 1: TryExcept/With/Loop children → 收集 LoopRegion@760 ✓
  - phase 2: IfRegion children → 无 ✓
  - **缺失 phase 3: TernaryRegion/BoolOpRegion → 不收集** ✗
- 对比 `_if_generate_then_branch`（line 9118-9235）有显式 BoolOpRegion/TernaryRegion 收集，else 分支不对称。
- 后果：TernaryRegion@844/@1226 的 entry（844, 1226）被 `_process_if_blocks` 当作普通顺序块平坦化，标记 generated，后续父循环 LoopRegion@610 遍历跳过。
- **违反原则 3（嵌套即抽象节点）**：TernaryRegion 应作为抽象节点，不被平坦化。
- **违反原则 4（入口引用语义）**：else_blocks 应引用子区域 entry，由 _generate_region 分发。

**根因 B（生成层，链式）**：TernaryRegion@844.merge_block=1226 = TernaryRegion@1226.entry（共享 merge_block）。

- TernaryRegion@844 (merge_context='compare') 的 merge_block (1226) 同时是 TernaryRegion@1226 (merge_context='store') 的 entry。
- `_generate_ternary` 已检测 `_shared_with_next_ternary` 并不发射 extra 语句（正确）。
- 但 CALLER 标记 `region.blocks`（含共享 merge_block 1226）为 generated，导致 TernaryRegion@1226 entry 已 generated 被跳过。
- **违反原则 2（每块唯一归属）**：共享块不应被前驱独占标记，后继仍需以该块为 entry 归约。

### 5.3 first_diff 发散点

- first_diff_idx=9 (offset 56, FOR_ITER)：orig `->[305]` vs new `->[257]` —— 外层 for 循环退出目标偏移，源于内层循环体 -48 指令丢失。
- 真正语句发散起始于 idx 186 (offset 844)：
  - orig: `844 LOAD_FAST 'stock_df'`（TernaryRegion@844 entry，`stock_df.ix[datas[not_nan_icount]]['open']`）
  - new: `844 LOAD_FAST 'data_is_nan'`（TernaryRegion 块被平坦化为错误语句）

## 6. 最小复现实例清单

见 `minimal_repros/`，共 10 个 repro（repro_01..repro_10），全部 `py_compile` 通过：

| 文件 | 区域类型 | 违反原则 | 对应函数 |
|------|----------|----------|----------|
| repro_01.py | Loop + IfRegion(continue) + TernaryRegion | 3 + 4 | get_str_data (-48 完整镜像) |
| repro_02.py | Loop + IfRegion(continue) + TernaryRegion | 3 + 4 | get_str_data (TernaryRegion 被误吞) |
| repro_03.py | TernaryRegion chain (共享 merge_block) | 2 + 3 | get_str_data (@844/@1226 链) |
| repro_04.py | Loop + IfRegion(continue) + LoopRegion + TernaryRegion | 3 + 4 | get_str_data (兄弟 Loop+Ternary) |
| repro_05.py | Loop + IfRegion(continue) + BoolOpRegion | 3 + 4 | get_str_data (BoolOp 兄弟) |
| repro_06.py | Loop + IfRegion(continue) + IfRegion | 4 | get_str_data (sibling IfRegion) |
| repro_07.py | Loop + TernaryRegion(store) | 3 + 4 | get_str_data ('price' 字段) |
| repro_08.py | Loop + IfRegion(continue) | 4 | get_str_data (merge=loop header) |
| repro_09.py | Loop (outer for items) | 4 | get_str_data (first_diff@9) |
| repro_10.py | Loop + IfRegion + Loop + Ternary chain | 2 + 3 + 4 | get_str_data (综合镜像) |

重点 repro_01/repro_02/repro_03 直接复现 -48 指令根因（IfRegion else 不分发 TernaryRegion + 共享 merge_block 链）。

## 7. 修复建议（供修复工程师）

1. **修复点 A**：`_if_generate_else_branch` 新增 phase 3，收集 else_blocks 中的 TernaryRegion/BoolOpRegion entry（通过 `get_entry_region_for_block` 查询，镜像 then 分支 L9118-9235 + `_loop_handle_child_region_entry` L7088-7117）。
2. **修复点 B**：CALLER 标记 `region.blocks` 为 generated 时，跳过共享 merge_block（前驱 merge 是后继 TernaryRegion entry 时），镜像 `_generate_ternary` L23793-23800 的 `_shared_with_next_ternary` 检测。
3. **docstring**：`_if_generate_else_branch` 同步更新 6 节模板，说明 R12 修复依据（原则 3 + 4 + 2）。
