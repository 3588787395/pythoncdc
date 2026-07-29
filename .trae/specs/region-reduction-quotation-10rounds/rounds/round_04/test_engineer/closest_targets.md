# Round 4 最接近修复的函数分析（closest_targets.md）

> 区域归约算法驱动的 quotation.pyc 反编译迭代 — 第 4 轮测试工程师
> 基线：141/150 = 94.00%，9 个不一致函数
> 工作目录：`/workspace/.trae/specs/region-reduction-quotation-10rounds/rounds/round_04/test_engineer/`
> 本文件对 9 个不一致函数按"接近匹配"程度排序，给出每个函数的指令差异、根因定位、修复可行性评估。

## 0. 9 个不一致函数总览（按接近匹配程度排序）

| 排名 | 函数 | 状态 | orig_len | new_len | diff | 接近度 | 可修复性 |
|---|---|---|---|---|---|---|---|
| 1 | `one_prod_to_dataframe` | len_diff | 444 | 455 | +11 | ★★★★（指令数最接近） | 中（if/elif 链分裂，高风险） |
| 2 | `build_future_fill_time` | instr_diff | 671 | 671 | 0 | ★★★★（指令数完全相同） | **不可修**（frozenset 版本差异） |
| 3 | `get_date_and_count` | len_diff | 714 | 687 | -27 | ★★（尾部 elif 体丢失） | 低（tail body lost） |
| 4 | `load_get_price` | len_diff | 226 | 201 | -25 | ★★（长 or 链分支体折叠） | 低（R3 未触达） |
| 5 | `fill_minute_or_day_blank` | len_diff | 241 | 199 | -42 | ★（else 分支丢失） | 低 |
| 6 | `get_str_data` | len_diff | 317 | 269 | -48 | ★（循环后构造丢失） | 低 |
| 7 | `change_his_to_backward` | len_diff | 578 | 522 | -56 | ★（FOR_ITER 边界） | 低 |
| 8 | `<module>` | len_diff | 1082 | 1023 | -59 | ★（模块级 NOP 占位） | 低 |
| 9 | `load_bars_from_hundsun` | len_diff | 501 | 327 | -174 | ☆（最大亏损） | 低 |

## 1. `one_prod_to_dataframe`（+11，最易 +1 候选）

### 1.1 指令差异

- `orig_len=444, new_len=455, diff=+11`
- 首处差异：idx=97，`FOR_ITER 1650` → `FOR_ITER 1682`（跳转目标偏移 +32 字节，由循环体内 11 条多余指令导致）
- 末尾结构一致：`BUILD_LIST 0, STORE_FAST 'columns', if data_type is None: ... else: columns=[...], return pandas.DataFrame(...)`

### 1.2 根因定位

反编译器将原始的 `if i == 0 and len(v) == N:` elif 链**拆分为两个独立的 if 结构**，导致指令冗余：

**原始结构（orig 字节码推断）：**
```python
elif i == 0 and len(v) == 8:
    index.append(f"{v[0:4]}-{v[4:6]}-{v[6:8]} 00:00:00")
elif i == 0 and len(v) == 10:
    index.append(f"{v[0:4]}-{v[4:6]}-{v[6:8]} {v[8:10]}:00:00")
elif i == 0 and len(v) == 11:
    index.append(f"{v[0:4]}-{v[4:6]}-{v[6:8]} 0{v[8:9]}:{v[9:11]}:00")
elif i == 0 and len(v) == 12:
    index.append(f"{v[0:4]}-{v[4:6]}-{v[6:8]} {v[8:10]}:{v[10:12]}:00")
elif i == 0 and len(v) == 14:
    index.append(f"{v[0:4]}-{v[4:6]}-{v[6:8]} {v[8:10]}:{v[10:12]}:{v[12:14]}")
```

**反编译产物（new 字节码对应的源码）：**
```python
if i == 0:                                      # 拆分点 1：外层 if
    if len(v) == 8:                              # 内层 if
        index.append(...)
    elif i == 0 and len(v) == 10:                # 冗余 `i == 0 and`（已在外层 if 中）
        index.append(...)
    elif i == 0:                                  # 丢失 `len(v) == 11` 条件
        index.append(...)
    elif i == 0:                                  # 丢失 `len(v) == 12` 条件
        index.append(...)
    elif i == 0:                                  # 丢失 `len(v) == 14` 条件
        index.append(...)
if len(v) == 11:                                  # 拆分点 2：第二个 if 链
    pass                                          # body 丢失
elif i == 0 and len(v) == 12:
    pass                                          # body 丢失
elif i == 0 and len(v) == 14:
    pass                                          # body 丢失
```

**指令级根因（idx 231 处首次结构分歧）：**
- ORIG idx 231: `POP_JUMP_FORWARD_IF_FALSE 1202`（`i==0` 失败 → 跳向下一个 elif 的 `len(v)==11` 检查，1202）
- NEW idx 231: `POP_JUMP_FORWARD_IF_FALSE 1166`（`i==0` 失败 → 跳向 1166，跳过当前 elif 链进入第二个 if 链）
- ORIG idx 232: `LOAD_GLOBAL len`（开始 `len(v) == 11` 条件求值）
- NEW idx 232: `LOAD_FAST index`（直接进入 body，`len(v)==11` 条件丢失）

### 1.3 算法根因

`_identify_conditional_regions` 在处理 `A and B` 复合条件的 elif 链时，将 `A`（`i == 0`）提取为外层 if 条件，将 `B`（`len(v) == N`）作为内层 if 条件，破坏了 elif 链的连续性。具体表现为：
1. 第一个 `if i == 0 and len(v) == 8:` 被归约为 `if i == 0:` 外层 + `if len(v) == 8:` 内层
2. 后续 `elif i == 0 and len(v) == N:` 被归约到外层 if 的 elif 链，但 `i == 0` 条件冗余、`len(v) == N` 条件丢失
3. 原始 elif 链的后半部分（`len(v) == 11/12/14`）被拆分为独立的第二个 if 链，body 丢失为 pass

### 1.4 修复可行性

- **风险**：高。修改 `_identify_conditional_regions` 的 elif 链识别逻辑可能影响 141 个已匹配函数。
- **方向**：在 elif 链识别时，当当前 elif 条件是 `A and B` 复合条件且前一个 elif 也是 `A and B'` 时，应保持 `A and B` 作为整体条件，不拆分 A 为外层 if。
- **算法依据**：原则 4（入口引用语义）—— elif 链的每个分支条件块应共享同一 exit 入口；原则 2（每块唯一归属）—— 条件块不应被拆分到不同 if 区域。
- **结论**：本轮尝试修复，需严格回归测试确保 0 退化。

## 2. `build_future_fill_time`（instr_diff，不可修）

### 2.1 指令差异

- `orig_len=671, new_len=671, diff=0`（指令数完全相同）
- 13 处差异：
  - 5 处 `LOAD_CONST tuple` → `LOAD_CONST frozenset`（idx 522, 531, 536, 569, 583）
  - 5 处 `JUMP_FORWARD 2660` → `JUMP_FORWARD 2586`（idx 226, 369, 512, 559, 606，偏移 -74 字节）
  - 3 处 listcomp code object 地址差异（idx 201, 344, 487，仅对象 id 不同，字节码等价）

### 2.2 根因定位

**frozenset 版本差异（不可修复）：**
- 原始 pyc（编译自旧版 Python）将集合字面量 `{'14:30:00', '15:15:00', ...}` 的常量存储为 **tuple** 类型
  - 字节码：`BUILD_SET 0, LOAD_CONST ('14:30:00', ...), SET_UPDATE 1`
- 反编译产物重新用 Python 3.11.15 编译时，同样的集合字面量常量被存储为 **frozenset** 类型
  - 字节码：`BUILD_SET 0, LOAD_CONST frozenset({...}), SET_UPDATE 1`
- 这是 Python 编译器版本差异：旧版将 set literal 常量存为 tuple，3.11+ 存为 frozenset

**JUMP_FORWARD 偏移（frozenset 差异的连锁后果）：**
- 5 处 JUMP_FORWARD 目标偏移 74 字节（2660→2586）
- 根因：frozenset 常量与 tuple 常量在 `co_consts` 中的存储方式不同，导致后续常量索引变化，触发不同的 EXTENDED_ARG 前缀，累积 74 字节偏移
- 这是 frozenset 差异的**派生后果**，非独立缺陷

### 2.3 修复可行性

- **不可修复**。即使反编译器输出与原始源码完全一致的 `{'14:30:00', ...}` 集合字面量，Python 3.11.15 编译器仍会生成 `LOAD_CONST frozenset(...)`，无法复现原始 pyc 的 `LOAD_CONST tuple(...)`。
- **结论**：接受该差异，build_future_fill_time 不作为 +1 目标。

## 3. `get_date_and_count`（-27，尾部 elif 体丢失）

### 3.1 指令差异

- `orig_len=714, new_len=687, diff=-27`
- 首处差异：idx=140，`JUMP_FORWARD 3046` → `JUMP_FORWARD 2946`（偏移 -100 字节）
- 415 处差异（大部分为跳转目标偏移，由 27 条缺失指令累积导致）
- 尾部分歧：orig 有 `LOAD_GLOBAL str, LOAD_FAST year, PRECALL 1, CALL 1, LOAD_GLOBAL str, LOAD_FAST month, ..., BINARY_OP 0, LOAD_CONST '01', BINARY_OP 0, STORE_FAST 'start_date'`（即 `start_date = str(year) + str(month) + '01'`），new 缺失

### 3.2 根因定位

尾部 elif 分支体（`start_date = str(year) + str(month) + '01'`）丢失。该 elif 分支含字符串拼接 + 赋值，反编译器未能归约该分支体，导致整个 elif 分支被丢弃。

### 3.3 修复可行性

- 低。需修复 elif 分支体的归约逻辑，但该逻辑影响面广，风险高。
- **结论**：留待后续轮次。

## 4. `load_get_price`（-25，长 or 链分支体折叠）

### 4.1 指令差异

- `orig_len=226, new_len=201, diff=-25`
- 首处差异：idx=50，`POP_JUMP_FORWARD_IF_FALSE 500` → `POP_JUMP_FORWARD_IF_FALSE 428`

### 4.2 根因定位

R3 修复（`_detect_boolop_conditional_chain` 的 and(or-chain) 入口引用语义判定）在精简 repro 上有效，但 `load_get_price` 的原始 CFG 更复杂（含 `if len(panel.major_axis) != 0:` 前导嵌套 if + try/except 上下文），未触发与精简 repro 相同的代码路径。长 or 链 `is_utc == '0' and (typet == 1 or ... or typet == 13)` 分支体仍被折叠为 pass。

### 4.3 修复可行性

- 低。需扩展 `_detect_boolop_conditional_chain` 对原始 CFG 路径的覆盖，但 R3 修复尝试已表明精简 repro 与原始 CFG 之间存在结构差异。
- **结论**：留待后续轮次，需用 `debug_regions.py` 对原始函数的 CFG 块结构与 claimed 集合做精细追踪。

## 5. 其余 5 个函数（简述）

| 函数 | diff | 根因 | 修复可行性 |
|---|---|---|---|
| `fill_minute_or_day_blank` | -42 | else 分支（numpy.array + pandas.concat）丢失 | 低 |
| `get_str_data` | -48 | 循环后 `pandas.Panel(...)` 构造边界（repro_02） | 低 |
| `change_his_to_backward` | -56 | for `FOR_ITER` 目标提前收敛 + 循环后 if/None 丢失（repro_01） | 低 |
| `<module>` | -59 | 模块级 NOP 占位区段后 10 个函数定义丢失 | 低 |
| `load_bars_from_hundsun` | -174 | 长 or 链 `is_utc=='0' and (typet==1 or ...)` 分支体仍 pass（repro_03 部分改善，diff 仍 -174） | 低 |

## 6. 本轮修复策略

基于以上分析，本轮修复策略为：

1. **主攻 `one_prod_to_dataframe`（+11 → 0）**：修复 `_identify_conditional_regions` 的 elif 链识别逻辑，使 `A and B` 复合条件的 elif 链保持整体归约，不拆分 A 为外层 if。若成功，一致函数数 141 → 142。
2. **接受 `build_future_fill_time` 不可修**：frozenset 版本差异无法通过算法修复。
3. **确保无退化**：任何修复必须通过既有区域测试矩阵（IF/LOOP/TRY/WITH/MATCH/BOOLOP/TERNARY/CC/SEQ/ASSERT）0 退化 + quotation.pyc 一致数 ≥ 141。
4. **若 one_prod 修复导致退化**：立即回滚，保持 141 无退化，留待 R5。
