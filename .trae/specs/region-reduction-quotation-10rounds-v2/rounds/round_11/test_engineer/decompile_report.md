# R11 测试工程师：反编译报告

## 1. 总体统计

- 总函数数: 150
- 一致函数数: 143
- 不一致函数数: 7
- 成功率: 95.33%
- compile_ok: True
- V1-R10 基线: 143/150 (95.33%) — R11 不得退化

## 2. 残留不一致函数清单（7 个）

| 函数 | 状态 | orig_len | new_len | diff |
|------|------|----------|---------|------|
| <module> | instr_diff@394 | - | - | - |
| one_prod_to_dataframe | instr_diff@131 | - | - | - |
| build_future_fill_time | instr_diff@226 | - | - | - |
| load_get_price | len_diff | 226 | 224 | -2 |
| get_str_data | len_diff | 317 | 269 | -48 |
| change_his_to_backward | instr_diff@296 | - | - | - |
| get_date_and_count | len_diff | 714 | 687 | -27 |

## 3. 缺陷分类（按区域类型 + 算法原则）

### P0 Loop 区域缺陷（3 个，真算法缺陷）

- **load_get_price** (len_diff -2)：Conditional+BoolOp 嵌套分支残留 2 指令。`if is_utc=='0'` 与 `elif typet==1 or typet==2 or ...` BoolOp 链分支语句部分丢失。违反原则 3（嵌套即抽象节点）+ 原则 4（入口引用语义）。
- **get_str_data** (len_diff -48)：Loop 嵌套 for/while 循环体语句丢失。`_generate_loop` 在嵌套循环体块遍历漏掉 merge/follow 块。违反原则 2（每块唯一归属）。
- **get_date_and_count** (len_diff -27)：Loop+Conditional while 循环 if/elif 链语句丢失。while 体内 if/elif 链未完整生成。违反原则 1（自底向上归约）+ 原则 3。

### P1 跳转目标归一化差异（3 个，语义等价）

- **one_prod_to_dataframe** (instr_diff@131)：首个 `i==0` 提取为外层 if，原始跳到下一 elif，跳转目标偏移。归一化已对齐指令索引，残留偏移差异。违反原则 4（入口引用语义）。
- **build_future_fill_time** (instr_diff@226)：listcomp 内部 code 对象布局 + 后续跳转目标偏移。违反原则 4。
- **change_his_to_backward** (instr_diff@296)：for 循环内嵌套 if 的 else 体已恢复，残留跳转目标偏移。违反原则 4。

### P2 元数据差异（1 个，非算法缺陷）

- **<module>** (instr_diff)：嵌套 code 对象 co_filename 原始为 `./fly_docker_py311/fly/data/quotation.py`，反编译产物为 `<decompiled>`。违反原则 4（入口引用语义，co_filename 引用语义）。

## 4. 详细 diff

见 `diff_detail.txt`（/tmp/r11_out/diff_detail.txt），含 7 个残留函数 orig vs new 指令逐行对比。

## 5. load_get_price -2 指令详细分析（R11 重点）

`load_get_price` orig_len=226 / new_len=224 / diff=-2，first_diff_idx=164。逐指令 diff 显示：

- **缺失的 2 条指令 = orig idx 198 `LOAD_FAST 'panel'` + idx 199 `STORE_FAST 'panel'`** —— 即 for 循环退出后、`if _typet in (7,8,9,15):` 条件前的冗余自赋值 `panel = panel`，反编译器在 loop-exit → conditional 衔接处丢弃。
- idx 164 `JUMP_FORWARD`：orig `->[200]` vs new `->[198]`（因前述 2 指令缺失，目标整体前移 2）。
- idx 168 `POP_JUMP_FORWARD_IF_FALSE`：orig `->[198]` vs new `->[-1]`（new 跳转目标 offset 不在过滤后指令表，BoolOp `_typet in (7,8,9,15)` 条件 then 入口语义未对齐）。
- idx 197 起后续指令整体偏移 2，orig 在末尾多出 2 条（new idx 223 `RETURN_VALUE` 即结束）。

根因：Loop-exit merge 块与后续 Conditional 区域的衔接未遵循原则 4（入口引用语义）—— 冗余自赋值块作为 loop-exit 的 follow 块未被保留，且 BoolOp 条件入口跳转目标归一化失败。

## 6. 最小复现实例清单

见 `minimal_repros/`，共 10 个 repro（repro_01..repro_10），全部 `py_compile` 通过：

| 文件 | 区域类型 | 违反原则 | 对应函数 |
|------|----------|----------|----------|
| repro_01.py | Conditional + BoolOp | 3 + 4 | load_get_price |
| repro_02.py | Loop + Conditional | 2 + 4 | load_get_price (-2 指令: panel=panel) |
| repro_03.py | BoolOp + Conditional | 4 | load_get_price (in tuple 跳转 -1) |
| repro_04.py | Loop | 2 | get_str_data (-48) |
| repro_05.py | Loop + Conditional | 1 + 3 | get_date_and_count (-27) |
| repro_06.py | Conditional | 4 | one_prod_to_dataframe |
| repro_07.py | Sequence + Conditional | 4 | build_future_fill_time |
| repro_08.py | Loop + Conditional | 4 | change_his_to_backward |
| repro_09.py | Module | 4 | <module> (co_filename) |
| repro_10.py | Conditional + BoolOp | 3 + 4 | load_get_price (多层嵌套综合) |

重点 repro_02 直接复现 -2 指令根因（循环退出后 `panel = panel` 自赋值被丢弃）。