# R22 修复工程师报告（V3 第 2 轮）

## 1. 修复目标

修复 `get_str_data` 循环尾部 STORE_ATTR 兄弟语句 `data.index = time_index`
发射丢失问题（R21 残留 len_diff -3，317→314）。该语句位于外层 `for stock` 循环
体内、内层 `for j in range(...)` 循环退出之后、外层 `for` 回边（JUMP_BACKWARD）
之前，与 `order_data[stock] = data`（STORE_SUBSCR）构成兄弟语句序列。

## 2. 根因分析

### 2.1 缺陷定位

`get_str_data` 外层 `for stock` 循环的回边块（back_edge_block）含两条兄弟赋值：

```
LOAD_FAST 'time_index'      ─┐
LOAD_FAST 'data'             │ data.index = time_index (STORE_ATTR) ← 缺失
STORE_ATTR 'index'          ─┘
LOAD_FAST 'data'            ─┐
LOAD_FAST 'order_data'       │
LOAD_FAST 'stock'            │ order_data[stock] = data (STORE_SUBSCR) ← 已生成
STORE_SUBSCR                ─┘
JUMP_BACKWARD (外层 for 回边)
```

该回边块由 `_loop_handle_back_edge` / `_loop_process_back_edge_with_condition`
（region_ast_generator.py L6711-6759 / L6762-6800）处理，过滤后调用
`_generate_stmts_from_instrs(_be_filtered, block)`（L6746 / L6787）逐条归约。

### 2.2 根因：`_generate_stmts_from_instrs` 缺少 STORE_ATTR 边界处理

`_generate_stmts_from_instrs`（L31508）此前的语句边界处理仅覆盖：

| 语句边界 | 字节码 | 处理方式 |
|---------|--------|---------|
| Subscript 赋值 | `STORE_SUBSCR` | `_build_subscript_assign` / 切片重建（L31519-31544） |
| 变量赋值 | `STORE_FAST/NAME/GLOBAL/DEREF` | `_build_store_statement`（L31545-31550） |
| 表达式语句 | `POP_TOP` | `_build_statement`（L31551-31556） |

**缺失**：`STORE_ATTR`（属性赋值）无边界处理分支。当指令序列到达 `STORE_ATTR` 时，
该指令连同前驱 `LOAD value` / `LOAD obj` 残留在 `_buf` 中不被发射；随后到达
`STORE_SUBSCR` 时，`STORE_SUBSCR` 处理逻辑以 `_buf` 中的指令重建 Subscript 赋值，
`STORE_ATTR` 指令被吞并丢弃，导致 `data.index = time_index` 语句丢失。

### 2.3 算法原则违反

| 原则 | 违反 |
|------|------|
| 原则 2（每块唯一归属） | `STORE_ATTR` 的前驱 `LOAD value/obj` 应归属本属性赋值语句，却残留缓冲被后续 `STORE_SUBSCR` 重建吞并 |
| 原则 1（自底向上归约） | 回边块作为整体归约时，`STORE_ATTR` 未作为独立语句归约，破坏多语句块的逐条归约顺序 |

### 2.4 对比：单语句块路径已正确处理 STORE_ATTR

`_build_effective_stmts`（单语句块路径）已在多处正确处理 `STORE_ATTR`（L485-491、
L3862-3868、L4640、L16535 等），采用统一模式：

```python
if _instr.opname == 'STORE_ATTR':
    _buf.append(_instr)
    _stmt = self._build_attr_assign(_buf)
    if _stmt:
        _stmts.append(_stmt)
    _buf = []
    continue
```

`_generate_stmts_from_instrs`（多语句回边块路径）此前未对齐该模式，是 R22 根因。

## 3. 修复方案

### 3.1 修复点

**文件**: `core/cfg/region_ast_generator.py`
**方法**: `_generate_stmts_from_instrs`（L31508）
**改动**: 在 `STORE_SUBSCR` 处理块之后、`STORE_FAST` 处理块之前，新增 `STORE_ATTR`
边界处理分支，对齐 `_build_effective_stmts` / `_build_prefix_stmt_list` 中的统一模式。

```python
# [R22] STORE_ATTR 重建为 Attribute 赋值 (obj.attr = value)
if _instr.opname == 'STORE_ATTR':
    _buf.append(_instr)
    _stmt = self._build_attr_assign(_buf)
    if _stmt:
        _stmts.append(_stmt)
    _buf = []
    continue
```

### 3.2 算法依据（4 原则对应）

| 原则 | 对应条款 |
|------|---------|
| 原则 1（自底向上归约） | 回边块作为外层 LoopRegion body 的抽象节点，内部按 `STORE_ATTR` / `STORE_SUBSCR` / `STORE_FAST` / `POP_TOP` 边界逐条归约后再交付外层循环体 |
| 原则 2（每块唯一归属） | `STORE_ATTR` 的前驱 `LOAD value/obj` 归属本属性赋值语句，发射后清空 `_buf`，不残留被后续 `STORE_SUBSCR` 吞并 |
| 原则 3（嵌套即抽象节点） | 回边块作为整体在父 LoopRegion 中作为单个抽象节点，内部多语句归约不影响父区域 |
| 原则 4（入口引用语义） | 父 LoopRegion body 引用回边块的 entry（块入口），内部语句发射由本方法完成 |

### 3.3 复用既有重建逻辑

`STORE_ATTR` 处理复用 `_build_attr_assign`（L32456），统一覆盖：
- 普通属性赋值 `obj.attr = value`（多层属性链 `a.b.c = value`，L32607-32655）
- 增强赋值 `obj.attr += value`（AugAssign，L32478-32605）

无新增重建逻辑，仅补齐多语句回边块路径的边界处理缺失。

### 3.4 docstring 更新（6 节模板）

`_generate_stmts_from_instrs` docstring 从单行扩展为 6 节模板：
1. 方法说明
2. 区域归约算法符合度
3. 字节码模式（含 R22 新增 STORE_ATTR）
4. 参数
5. 返回
6. 典型应用场景（get_str_data 循环尾部 STORE_ATTR + STORE_SUBSCR 兄弟语句）

## 4. 回归结果

### 4.1 quotation.pyc 一致函数数

| 指标 | R21 基线 | R22 修复后 |
|------|---------|-----------|
| 总函数数 | 150 | 150 |
| 一致函数数 | 147 | **147** |
| 不一致函数数 | 3 | 3 |
| 成功率 | 98.00% | **98.00%** |
| compile_ok | True | True |
| get_str_data | len_diff -3 (317→314) | **instr_diff @idx179 (317→317)** |

**无退化**（147/150 ≥ R21 147/150）。`get_str_data` 的 -3 len_diff 已消除
（指令数 317→317 完全对齐，`data.index = time_index` 已正确发射）。

### 4.2 get_str_data 残留差异（预存在，非本轮引入）

R22 修复后 `get_str_data` 残留 `instr_diff @idx179`（1 处跳转目标偏移）：

```
179 !! O: 830 POP_JUMP_FORWARD_IF_FALSE  ->[182]   # orig: 跳到 JUMP_BACKWARD（回边）
       !! N: 830 POP_JUMP_FORWARD_IF_FALSE  ->[183]   # new:  跳到 post-loop（break 语义）
```

**经 git stash 验证：该差异为预存在缺陷，非 R22 引入。**

- R22 修复前（git stash 还原 R21 代码）：反编译源码已含 `else: not_nan_icount = j; break`
  （与修复后完全一致），但 exact_match_stats 因 `len_diff -3`（314 vs 317）优先报
  `len_diff` 状态，掩盖了 idx179 的 `instr_diff`。
- R22 修复后：`len_diff` 消除（317=317），idx179 的预存在 `instr_diff` 显露。

**残留性质**：内层 `for j in range(...)` 循环的 `else: break` 误识别（loop_else /
break 检测层缺陷）。orig 字节码两分支均回边（无 break），反编译器误将 post-loop 块
`not_nan_icount = j` 归入 if-else 的 break 分支。属 loop_else 无 break 守卫问题，
与 spec R26（get_date_and_count 根因 B）同类，按根因修复顺序（G13）不在 R22 范围。

### 4.3 既有区域测试矩阵

```
9 failed, 318 passed, 11 skipped in 1.89s
```

与基线（9 fail / 318 pass / 11 skip）**完全一致，0 退化**。

### 4.4 最小复现实例

10 个 repro 全部 `py_compile` 通过。repro_02（get_str_data 实际形态：
STORE_ATTR + STORE_SUBSCR 兄弟语句）反编译验证：

```
data.index = time_index        # STORE_ATTR ← R22 修复后正确发射
order_data[stock] = data       # STORE_SUBSCR ← 已正确生成
```

两条兄弟语句均纳入外层循环体，STORE_ATTR 不再被 STORE_SUBSCR 吞并。

### 4.5 反模式自检

| 检查项 | 结果 |
|--------|------|
| G3 无新增 `_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀 | **PASS**（git diff 无匹配） |
| G4 无新增硬编码深度上限 | **PASS**（git diff 无匹配） |
| IMPORT_OK（`import core.cfg.region_analyzer; import core.cfg.region_ast_generator`） | **PASS** |

## 5. 改动清单

| 文件 | 改动 | 行数 |
|------|------|------|
| `core/cfg/region_ast_generator.py` | `_generate_stmts_from_instrs` 新增 STORE_ATTR 边界处理 + docstring 6 节模板更新 | +57 / -1 |

## 6. 残留不一致函数清单（R22 后）

| 函数名 | 状态 | 根因 | 轮次归属 |
|--------|------|------|---------|
| `get_str_data` | instr_diff @idx179（预存在 loop_else/break 误识别） | loop_else 无 break 守卫（post-loop 块误归入 if-else break 分支） | R26（get_date_and_count 根因 B 同类） |
| `change_his_to_backward` | instr_diff @idx296 | code_generator if/else 分支布局未对齐 | R27（P2） |
| `get_date_and_count` | len_diff -27 (714→687) | Loop 反向链 fall-through + loop_else | R24-R26（P1） |

## 7. 算法 4 原则合规性

- ✅ 自底向上归约：回边块作为整体在父 LoopRegion 中归约，内部按语句边界逐条发射
- ✅ 每块唯一归属：STORE_ATTR 前驱 LOAD 归属本属性赋值，不残留被 STORE_SUBSCR 吞并
- ✅ 嵌套即抽象节点：回边块内部多语句归约不影响父区域
- ✅ 入口引用语义：父 LoopRegion body 引用回边块 entry，内部发射由本方法完成
- ✅ 无跨区域跨层次启发式规则
- ✅ 无反模式前缀 / 无硬编码深度上限
- ✅ 复用既有 `_build_attr_assign` 重建逻辑，无新增重建路径

## 8. 总结

R22 修复了 `_generate_stmts_from_instrs`（多语句回边块路径）缺少 `STORE_ATTR`
边界处理的根因，对齐单语句块路径（`_build_effective_stmts`）的统一模式。
`get_str_data` 的 -3 len_diff 已消除（`data.index = time_index` 正确发射），
指令数 317→317 完全对齐。残留 idx179 instr_diff 为预存在 loop_else/break
误识别（R26 范围），非本轮引入。一致函数数 147/150（无退化），既有区域测试矩阵
0 退化，反模式自检通过。
