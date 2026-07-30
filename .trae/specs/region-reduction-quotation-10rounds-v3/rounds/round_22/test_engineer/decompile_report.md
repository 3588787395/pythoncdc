# R22 测试工程师报告（V3 第 2 轮，重点攻克 get_str_data 残留 -3）

## 1. 基线统计

| 指标 | V3-R21 基线 | V3-R22 基线 |
|------|------------|------------|
| 总函数数 | 150 | **150** |
| 一致函数数 | 147 | **147** |
| 不一致函数数 | 3 | 3 |
| 成功率 | 98.00% | **98.00%** |
| compile_ok | True | True |
| `<module>` | match (delegated_embeds=133) | match (delegated_embeds=133) |

R22 基线与 R21 完全一致（147/150=98.00%），**无退化**。继承 R21 全部归一化逻辑：跳转目标归一化（R14 elif 链跟随 + R15 循环块旁路）、常量编码归一化（R15 set/tuple 等价）、co_filename 元数据归一化（R16）、`<module>` 传递性不一致委托（R17 方案 A 两阶段比较）。

## 2. 残留 3 个不一致函数

| 函数名 | 状态 | 详细 | 根因 |
|--------|------|------|------|
| `get_str_data` | len_diff -3 (317→314) | 字节码指令数 orig=317 new=314，反编译缺失 3 条指令 | **P0** — 循环尾部 STORE_ATTR 兄弟语句 `data.index = time_index` 在内层 while 循环退出后、外层 for 循环回边前未被纳入外层循环体生成 |
| `change_his_to_backward` | instr_diff@296 | @idx296 `POP_JUMP_FORWARD_IF_NOT_NONE` 跳转目标 orig=330 vs new=342；@idx329 起指令完全重排 | **P2** — code_generator if/else 分支布局未对齐（defer） |
| `get_date_and_count` | len_diff -27 (714→687) | 字节码指令数 orig=714 new=687，反编译缺失 27 条指令 | **P1** — Loop 反向链 fall-through 吸收外层条件块 + loop_else（defer） |

## 3. get_str_data 残留 -3 缺陷定位（本轮重点）

### 3.1 缺陷现象

`get_str_data` 反编译缺失 3 条指令（orig=317 new=314）。逐指令 diff（`/tmp/r22_out/diff_detail.txt` get_str_data 节，idx 296-304）：

```
296    O:1516 JUMP_BACKWARD                ->[-1]     # 内层 while 循环回边
       N:1516 JUMP_BACKWARD                ->[-1]
297 !! O:1518 LOAD_FAST                    'time_index'   # ← 缺失起点
       N:1518 LOAD_FAST                    'data'         # ← new 直接跳到 data
298 !! O:1520 LOAD_FAST                    'data'
       N:1520 LOAD_FAST                    'order_data'
299 !! O:1522 STORE_ATTR                   'index'        # data.index = time_index ← 缺失
       N:1522 LOAD_FAST                    'stock'
300 !! O:1532 LOAD_FAST                    'data'         # order_data[stock] = data 起点
       N:1524 STORE_SUBSCR                 None
301 !! O:1534 LOAD_FAST                    'order_data'
       N:1530 JUMP_BACKWARD                ->[-1]         # ← new 外层回边已到这里
302 !! O:1536 LOAD_FAST                    'stock'
       N:1532 LOAD_GLOBAL                  'pandas'       # 后续指令对齐错位
303 !! O:1538 STORE_SUBSCR                 None           # order_data[stock] = data
       N:1544 LOAD_ATTR                    'Panel'
304 !! O:1544 JUMP_BACKWARD                ->[-1]         # 外层 for 循环回边
       N:1554 LOAD_FAST                    'order_data'
```

### 3.2 缺失语句

外层 `for stock` 循环体尾部原序（orig idx 297-304）：

```
data.index = time_index        # orig 1518-1522 (LOAD_FAST 'time_index', LOAD_FAST 'data', STORE_ATTR 'index')  ← 缺失（3 条指令）
order_data[stock] = data       # orig 1532-1538 (LOAD_FAST 'data', LOAD_FAST 'order_data', LOAD_FAST 'stock', STORE_SUBSCR)  ← 已正确生成
JUMP_BACKWARD                  # orig 1544 外层 for 循环回边
```

反编译输出已正确生成 `order_data[stock] = data`，但**缺失前导 `data.index = time_index` 赋值**（STORE_ATTR，3 条指令）。new 输出从内层 while 回边直接跳到 `order_data[stock] = data` 的 LOAD_FAST 'data'，跳过了中间的 STORE_ATTR 兄弟赋值。

### 3.3 缺陷性质

该语句位于**外层 for 循环体内、内层 while 循环退出之后、外层 for 循环回边 (JUMP_BACKWARD) 之前**的中间块。属循环尾部兄弟语句发射问题——内层循环退出后到外层循环回边之间的语句块未被纳入外层循环体生成。R21 的 `post_consumer_extra_stmts` 仅提取 store 之后的指令，未覆盖 store 之前的兄弟赋值（如 `data.index = time_index` 在 `order_data[stock] = data` 之前）。

## 4. 缺陷分类（按区域类型 + 违反的算法原则）

| 缺陷 | 区域类型 | 算法原则违反 | 说明 |
|------|---------|------------|------|
| get_str_data 循环尾部 STORE_ATTR 兄弟语句丢失 | LoopRegion（循环区域生成） | **原则 2（每块唯一归属）**：内层 while 循环退出后、外层 for 回边前的中间块（含 `data.index = time_index` STORE_ATTR）未被任何循环体归属，成为孤儿块被跳过；**原则 1（自底向上归约）**：外层 LoopRegion body 块遍历未覆盖嵌套 LoopRegion 之后的兄弟语句块 | `_generate_loop` 生成外层循环体时，遍历 body 块序列到嵌套 LoopRegion 后停止，未继续收集嵌套循环退出后的剩余兄弟块；或 `post_consumer_extra_stmts` 仅提取 store 之后指令，未覆盖 store 之前的兄弟赋值 |
| get_date_and_count 反向链 + loop_else | LoopRegion（循环区域识别） | **原则 1 + 原则 2** | defer（R24-R26） |
| change_his_to_backward 指令重排 | code_generator（生成层 if/else 布局） | **原则 4 生成层对偶** | defer（R27） |

### 4.1 修复优先级

修复优先级：**P0（get_str_data 循环尾部 STORE_ATTR 兄弟语句发射）→ P1（get_date_and_count）→ P2（change_his_to_backward）**

本轮聚焦 P0：调查循环尾部块（inner loop 退出 → outer loop back-edge 之间）的语句收集，将该 STORE_ATTR 兄弟赋值纳入外层循环体生成。属边界对齐 / 语句收集范畴，风险可控。

## 5. 详细 diff 参考

逐指令 diff（3 个残留不一致函数，含 offset / opcode / argval 对比，标记 `!!` 为差异行）输出至：

**`/tmp/r22_out/diff_detail.txt`**

由 `rounds/round_22/test_engineer/diff_detail.py` 生成，复用 R22 `exact_match_stats.py` 的 `get_instr_list` / `walk_code` / `load_orig` 归一化逻辑（跳转目标归一化 + 常量编码归一化 + `<module>` 传递性委托）。

diff 文件头摘要：
```
# R22 diff_detail — 3 个残留不一致函数逐指令 diff
# summary: total=150 matched=147 mismatched=3 success_rate=98.0% compile_ok=True
# orig PYC=/workspace/quotation.pyc
# new  SRC=/tmp/r22_decompiled.py
```

## 6. 最小复现实例（10 个，聚焦循环尾部 STORE_ATTR 兄弟语句发射）

R22 重点针对 get_str_data 残留 -3 的循环尾部 STORE_ATTR 兄弟语句发射问题，提取 10 个最小复现实例，覆盖该缺陷的不同侧面：

| 复现实例 | 测试的 aspect | 对应根因 |
|---------|--------------|---------|
| repro_01 | 外层 for + 内层 while + 循环尾部单条 STORE_ATTR 兄弟语句（核心模式） | 循环尾部兄弟语句收集 |
| repro_02 | 循环尾部 STORE_ATTR + STORE_SUBSCR 兄弟语句序列（get_str_data 实际形态） | STORE_ATTR 在 STORE_SUBSCR 之前易丢失 |
| repro_03 | 循环尾部多条 STORE_ATTR 兄弟语句（3 条连续属性赋值） | 多条 STORE_ATTR 逐条纳入 |
| repro_04 | 内层 for（而非 while）退出后的循环尾部 STORE_ATTR 兄弟语句 | 内层循环类型无关性 |
| repro_05 | STORE_ATTR 目标为循环内构造对象 (data.index = time_index) | STORE_ATTR 目标/值表达式重建 |
| repro_06 | 内层循环与外层回边间多条异构兄弟语句（STORE_ATTR + STORE_FAST + POP_TOP + STORE_SUBSCR） | 异构兄弟语句按序纳入 |
| repro_07 | 循环尾部 STORE_ATTR 后跟方法调用表达式语句 (POP_TOP) | POP_TOP 语句边界不吞并前导 STORE_ATTR |
| repro_08 | 嵌套 dict 构造 + 内层循环 + 循环尾部 STORE_ATTR（接近 get_str_data） | dict 消费模式不吸收后续 STORE_ATTR |
| repro_09 | 内层 while 含 break + 循环尾部 STORE_ATTR 兄弟语句 | break 退出路径下循环尾部块收集 |
| repro_10 | 综合：外层 for + dict + 内层 while + STORE_ATTR + STORE_SUBSCR（get_str_data 完整形态） | 完整复现 -3 缺陷 |

全部 10 个 repro 位于 `rounds/round_22/test_engineer/minimal_repros/repro_01.py` .. `repro_10.py`，每个文件顶部含注释说明所测试的循环尾部 STORE_ATTR 兄弟语句 aspect。**全部 10 个 repro py_compile 通过**。

## 7. 反编译产物

| 检查项 | 结果 |
|--------|------|
| `/tmp/r22_decompiled.py` | 已生成（继承 R21 反编译流程，未修改产物） |
| `compile(src, '<decompiled>', 'exec')` | OK (compile_ok=True) |
| `/tmp/r22_out/bc_results.json` | 已生成（summary + per-function results） |
| `/tmp/r22_out/diff_detail.txt` | 已生成（3 节） |

## 8. 退出条件检查

| 退出条件 | 状态 | 说明 |
|---------|------|------|
| V3-E1 不一致函数数 = 0（100%） | ✗ 未达成 | 残留 3 个 |
| V3-E2 可提取新增最小复现实例 < 10 | ✗ 未达成 | 本轮提取 10 个 repro（聚焦循环尾部 STORE_ATTR 兄弟语句），残留不一致函数 3 个但 repro 需求 ≥10 |

## 9. 对修复工程师的建议

### 9.1 get_str_data（P0，本轮重点）

调查循环尾部块（inner loop 退出 → outer loop back-edge 之间）的语句收集：

1. **`region_ast_generator.py` `_generate_loop`**：检查外层 LoopRegion body 块遍历——遍历到嵌套 LoopRegion（内层 while）后是否继续收集嵌套循环退出后的剩余兄弟块（含 `data.index = time_index` STORE_ATTR）。
2. **`post_consumer_extra_stmts`（R21 新增）**：当前仅提取 store 之后的指令（如 `time_index.append(...)`、`i += 1`），未覆盖 store 之前的兄弟赋值。检查是否需要扩展为同时收集 store 前的兄弟语句，或改由外层循环体遍历统一收集。
3. **`region_analyzer.py` `_identify_loop_regions`**：检查外层 LoopRegion 的 body 块集合是否包含内层 while 循环退出后到外层回边之间的中间块——若该块被吸收进错误的 region 或成为孤儿块，则生成层无法发射。

- **WHEN** 外层 for 循环体内嵌套内层 while 循环，且内层循环退出后到外层回边前存在兄弟语句块
- **THEN** 这些兄弟语句 SHALL 纳入外层 for 循环体生成，不可丢失
- 同步更新相关方法 docstring（6 节模板）

### 9.2 change_his_to_backward（P2，defer）

code_generator if/else 分支布局对齐，属生成层重构，影响面广。本轮 defer。

### 9.3 get_date_and_count（P1，defer）

Loop 反向链 fall-through + loop_else 守卫。本轮 defer。
