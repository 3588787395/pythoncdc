# R23 测试工程师报告（V3 第 3 轮，重点攻克 get_str_data 残留 instr_diff@179）

## 1. 基线统计

| 指标 | V3-R22 基线 | V3-R23 基线 |
|------|------------|------------|
| 总函数数 | 150 | **150** |
| 一致函数数 | 147 | **147** |
| 不一致函数数 | 3 | 3 |
| 成功率 | 98.00% | **98.00%** |
| compile_ok | True | True |
| `<module>` | match (delegated_embeds=133) | match (delegated_embeds=133) |

R23 基线与 R22 完全一致（147/150=98.00%），**无退化**。继承 R22 全部归一化逻辑：跳转
目标归一化（R14 elif 链跟随 + R15 循环块旁路）、常量编码归一化（R15 set/tuple 等价）、
co_filename 元数据归一化（R16）、`<module>` 传递性不一致委托（R17 方案 A 两阶段比较）。

## 2. 残留 3 个不一致函数

| 函数名 | 状态 | 详细 | 根因 |
|--------|------|------|------|
| `get_str_data` | instr_diff @idx179 | @idx179 `POP_JUMP_FORWARD_IF_FALSE` 跳转目标 orig=182(→JUMP_BACKWARD 回边=continue) vs new=183(→LOAD_FAST post-loop=break) | **P0** — continue 作为 if 兄弟语句（两分支均→回边）未被发射，父 IfRegion 条件合并逻辑将外层+内层 if 合并为 `if A and B:`，改变内层 if false 分支跳转目标 |
| `change_his_to_backward` | instr_diff@296 | @idx296 `POP_JUMP_FORWARD_IF_NOT_NONE` 跳转目标 orig=330 vs new=342；@idx329 起指令完全重排 | **P2** — code_generator if/else 分支布局未对齐（defer） |
| `get_date_and_count` | len_diff -27 (714→687) | 字节码指令数 orig=714 new=687，反编译缺失 27 条指令 | **P1** — Loop 反向链 fall-through 吸收外层条件块 + loop_else（defer） |

## 3. get_str_data instr_diff@179 缺陷定位（本轮重点）

### 3.1 缺陷现象

`get_str_data` 指令数已对齐（317=317，R22 修复），但 @idx179 存在 1 处跳转目标偏移
（`/tmp/r23_out/diff_detail.txt` get_str_data 节，idx 170-185）：

```
170    O: 786 POP_JUMP_FORWARD_IF_FALSE    ->[183]   # 外层 if: false → 183 (break)
179 !! O: 830 POP_JUMP_FORWARD_IF_FALSE    ->[182]   # ORIG: 内层 if false → 182 (回边=continue)
       !! N: 830 POP_JUMP_FORWARD_IF_FALSE    ->[183]   # NEW:  内层 if false → 183 (post-loop=break)
180    O: 832 LOAD_CONST                   1
181    O: 834 STORE_FAST                   'data_is_nan'
182    O: 836 JUMP_BACKWARD                ->[163]       # 回边（continue）
183    O: 838 LOAD_FAST                    'j'           # not_nan_icount = j（break 路径）
```

### 3.2 原始源码结构

```python
for j in range(len(is_all_nan)):
    if is_all_nan[j] == True:          # idx 170 外层 if（false → 183 break）
        if j == len(is_all_nan) - 1:   # idx 179 内层 if（false → 182 回边=continue）
            data_is_nan = 1            # idx 180-181
        continue                       # idx 182 JUMP_BACKWARD（两分支均→回边=无条件兄弟）
    not_nan_icount = j                 # idx 183-184（else 分支）
    break                              # idx 185 POP_TOP
```

内层 if 的 true 分支（180-181）fallthrough 到 182（回边），false 分支（POP_JUMP_FORWARD_IF_FALSE）
也跳到 182（回边）。**两分支均→回边**，continue 为无条件兄弟语句（在 if 之后）。

### 3.3 反编译输出（缺陷）

```python
for j in range(len(is_all_nan)):
    if is_all_nan[j] == True and j == len(is_all_nan) - 1:   # ← 条件合并
        data_is_nan = 1
    else:
        not_nan_icount = j
        break
```

反编译器将外层+内层 if 条件合并为 `if A and B:`，`continue` 兄弟语句丢失。
合并后内层条件 false 分支跳到 else（183=break），而非回边（182=continue），
**语义错误**（A=true B=false 时原应 continue，合并后变 break）。

### 3.4 缺陷性质

区域结构（region_analyzer 分析结果）：

```
LoopRegion entry=760 header=760 back_edge=836
  body_blocks=[760, 762, 788, 832, 836]
  break_blocks=[838]

IfRegion entry=788 cond=788 merge=836     # 内层 if
  then_blocks=[832]  else_blocks=[]       # merge=836=回边，无 else
  → 两分支均→merge(回边)，continue 无条件

IfRegion entry=762 cond=762 merge=844     # 外层 if
  then_blocks=[788, 832]  else_blocks=[838]
```

内层 IfRegion（entry=788）的 merge=836=循环回边，else_blocks 为空。
反编译器将 merge（回边）视为循环隐式 continue（不生成显式 Continue 节点），
导致内层 if 的 then_stmts=[inner_if]（单元素）。父 IfRegion 的条件合并逻辑
（region_ast_generator.py L10612）将单元素 then_stmts 中的嵌套 if 条件合并
为 `if A and B:`，改变内层 if false 分支跳转目标。

## 4. 缺陷分类（按区域类型 + 违反的算法原则）

| 缺陷 | 区域类型 | 算法原则违反 | 说明 |
|------|---------|------------|------|
| get_str_data if-continue 兄弟语句丢失 | IfRegion（生成层） | **原则 2（每块唯一归属）**：回边块（merge=836）作为内层 if 的 merge 应归属该 if 的 continue 兄弟语句，却被循环体当作隐式回边跳过；**原则 4（入口引用语义）**：内层 if 的 continue 兄弟应作为 if 之后的显式节点引用回边 entry | `_if_generate_normal` 未检测 merge=回边且无 else 的 if-continue 兄弟模式，未生成显式 Continue 节点 |
| get_date_and_count 反向链 + loop_else | LoopRegion（识别层） | **原则 1 + 原则 2** | defer（R24-R26） |
| change_his_to_backward 指令重排 | code_generator（生成层 if/else 布局） | **原则 4 生成层对偶** | defer（R27） |

### 4.1 修复优先级

修复优先级：**P0（get_str_data if-continue 兄弟语句发射）→ P1（get_date_and_count）→ P2（change_his_to_backward）**

本轮聚焦 P0：在 `_if_generate_normal` 中检测 merge=回边且无 else 的 if-continue 兄弟
模式，生成显式 Continue 节点作为 if 的兄弟语句。属生成层补全范畴，风险可控。

## 5. 详细 diff 参考

逐指令 diff（3 个残留不一致函数，含 offset / opcode / argval 对比，标记 `!!` 为差异行）
输出至：

**`/tmp/r23_out/diff_detail.txt`**

由 `rounds/round_23/test_engineer/diff_detail.py` 生成，复用 R23 `exact_match_stats.py`
的 `get_instr_list` / `walk_code` / `load_orig` 归一化逻辑（跳转目标归一化 + 常量编码归一化
+ `<module>` 传递性委托）。

diff 文件头摘要：
```
# R23 diff_detail — 3 个残留不一致函数逐指令 diff
# summary: total=150 matched=147 mismatched=3 success_rate=98.0% compile_ok=True
# orig PYC=/workspace/quotation.pyc
# new  SRC=/tmp/r23_decompiled.py
```

## 6. 最小复现实例（10 个，聚焦 if-continue 兄弟语句发射）

R23 重点针对 get_str_data instr_diff@179 的 if-continue 兄弟语句发射问题，提取 10 个
最小复现实例，覆盖该缺陷的不同侧面：

| 复现实例 | 测试的 aspect | 对应根因 |
|---------|--------------|---------|
| repro_01 | for 循环内 if-continue 兄弟语句（核心模式：外层 if + 内层 if + continue 兄弟 + break） | continue 兄弟语句收集 |
| repro_02 | while 循环内 if-continue 兄弟语句（循环类型无关性） | while 循环回边同样适用 |
| repro_03 | 内层 if 无 else，false 分支→回边（纯 continue 回边模式） | false 分支跳转目标=回边检测 |
| repro_04 | 内层 if true 分支含多条语句（赋值 + 方法调用），continue 仍为兄弟 | 多语句 true 分支不影响兄弟发射 |
| repro_05 | 外层 if 有 else（break 路径）+ 内层 if-continue 兄弟（最接近 get_str_data） | if-else + if-continue 兄弟共存 |
| repro_06 | 内层 if 条件为复合比较（j == len(x) - 1，与 get_str_data 一致） | 复合比较条件不影响兄弟发射 |
| repro_07 | if-continue 兄弟无 break 路径（循环体只有 if + continue） | 最简 if-continue 兄弟模式 |
| repro_08 | STORE_FAST 赋值作为 true 分支（data_is_nan = 1，与 get_str_data 一致） | STORE_FAST + continue 兄弟顺序 |
| repro_09 | 内层 if true 分支含方法调用（POP_TOP），continue 仍为兄弟 | POP_TOP 语句边界不吞并 continue 兄弟 |
| repro_10 | 综合：for + if + if + continue 兄弟 + break（get_str_data 完整形态） | 完整复现 instr_diff@179 缺陷 |

全部 10 个 repro 位于 `rounds/round_23/test_engineer/minimal_repros/repro_01.py` ..
`repro_10.py`，每个文件顶部含注释说明所测试的 if-continue 兄弟语句 aspect。
**全部 10 个 repro py_compile 通过**。

## 7. 反编译产物

| 检查项 | 结果 |
|--------|------|
| `/tmp/r23_decompiled.py` | 已生成（继承 R22 反编译流程，未修改产物） |
| `compile(src, '<decompiled>', 'exec')` | OK (compile_ok=True) |
| `/tmp/r23_out/bc_results.json` | 已生成（summary + per-function results） |
| `/tmp/r23_out/diff_detail.txt` | 已生成（3 节） |

## 8. 退出条件检查

| 退出条件 | 状态 | 说明 |
|---------|------|------|
| V3-E1 不一致函数数 = 0（100%） | ✗ 未达成 | 残留 3 个（R23 修复后 2 个） |
| V3-E2 可提取新增最小复现实例 < 10 | ✗ 未达成 | 本轮提取 10 个 repro（聚焦 if-continue 兄弟语句），残留不一致函数 3 个但 repro 需求 ≥10 |

## 9. 对修复工程师的建议

### 9.1 get_str_data（P0，本轮重点）

在 `_if_generate_normal`（region_ast_generator.py）中，当满足以下条件时，生成显式
Continue 作为 if 的兄弟语句（在 if 之后）：

1. 当前在循环上下文中（`_current_loop is not None`）
2. `region.merge_block == _current_loop.back_edge_block`（merge = 回边）
3. 回边块仅含 `JUMP_BACKWARD`（无有意义指令 = 纯 continue 回边）
4. 无 else_blocks（`else_stmts` 为空 = 两分支均指向回边 = continue 无条件）

满足时追加 `{'type': 'Continue'}` 作为 if 的兄弟语句，并标记回边块为已生成
（避免循环体 `_loop_handle_back_edge` 重复处理）。

- **WHEN** 循环内 if 的 merge=回边且无 else（两分支均→回边）
- **THEN** SHALL 生成显式 Continue 兄弟语句，不可将 if 条件与外层条件合并
- 同步更新相关方法 docstring（6 节模板）

### 9.2 change_his_to_backward（P2，defer）

code_generator if/else 分支布局对齐，属生成层重构，影响面广。本轮 defer。

### 9.3 get_date_and_count（P1，defer）

Loop 反向链 fall-through + loop_else 守卫。本轮 defer。
