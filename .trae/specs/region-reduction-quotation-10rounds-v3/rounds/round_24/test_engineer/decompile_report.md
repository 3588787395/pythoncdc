# R24 测试工程师反编译报告 — quotation.pyc

> 反编译器：`/workspace/pydc.py`（pycdc） ｜ 目标：`/workspace/quotation.pyc`（Python 3.11）
> 归一化口径：`exact_match_stats.py`（跳转目标归一化 + 循环块旁路 + 常量等价 + 传递性委托）
> 基线成绩：**148 / 150 = 98.67%**，`compile_ok=True`，残留 2 个不一致函数。

## 0. 成功率统计

```
[stats] orig code objects: 150
[stats] new code objects: 150
[stats] compile_ok=True
[stats] total=150 matched=148 mismatched=2 missing=0 success_rate=98.67%
[stats] mismatched functions (2):
  - change_his_to_backward: instr_diff @idx296
  - get_date_and_count: len_diff orig=714 new=687 (diff=-27)
```

反编译命令：`cd /workspace && timeout 120 python pycdc.py /workspace/quotation.pyc > /tmp/r24_decompiled.py 2>/tmp/r24_err.txt`（exit 0，产物 3666 行，stderr 为空）。

---

## 1. 缺陷 A — `change_his_to_backward`：IF then 分支吸收循环末尾的兄弟语句

### 1.1 orig vs new 字节码关键差异段（标注偏移）

函数位于反编译产物 `/tmp/r24_decompiled.py` 第 753 行。问题集中在 `for n in indexlist:` 循环体内的 `if preindex is None: ... elif ...: break ... elif ...: ... else: ...` 链。

**ORIG（正确）— offset 1532~1592：**
```
1286  >> 1532 LOAD_FAST  16 (preindex)
      1534 POP_JUMP_FORWARD_IF_NOT_NONE   96 (to 1728)   # if preindex is None: then 分支入口
1288     1536 ...                                   # then: t=datetime.strptime(...)
1291     1668 ... tmpdata = data[:preday].copy()
         1724 EXTENDED_ARG 1
         1726 JUMP_FORWARD  415 (to 2558)            # then 末尾跳到循环末尾的【兄弟 if】
1294  >> 1728 ...                                   # elif: data[predataindex:curdataindex].empty
         1756 POP_JUMP_FORWARD_IF_FALSE 3 (to 1764)
1295     1758 POP_TOP
         1762 JUMP_FORWARD 415 (to 2594)             # break → 循环出口
1297  >> 1764 ... elif curdataindex in data.index
         ...   (各分支均 JUMP_FORWARD to 2558)
1327  >> 2558 LOAD_FAST 16 (preindex)               # 【兄弟 if #1】 if preindex != n: preindex = n
         2562 COMPARE_OP != ; 2568 POP_JUMP_FORWARD_IF_FALSE 2 (to 2574)
         2570 STORE_FAST 16 (preindex)
1331  >> 2574 ... if predataindex != curdataindex:  # 【兄弟 if #2】
         2584 POP_JUMP_FORWARD_IF_FALSE 2 (to 2590)
         2586 STORE_FAST 18 (predataindex)
      2590 EXTENDED_ARG 2
      2592 JUMP_BACKWARD 578 (to 1438)              # 循环回边
```
关键：then 分支（1536-1726）只含 `tmpdata` 设置，末尾 `JUMP_FORWARD to 2558`；两个 `if preindex != n` / `if predataindex != curdataindex` 是 **if/elif/else 链之后的兄弟语句**，所有非 break 分支都汇聚到 2558 执行它们，再走 2592 回边。

**NEW（错误）— offset 1532~1758：**
```
802  >> 1532 LOAD_FAST  16 (preindex)
      1534 POP_JUMP_FORWARD_IF_NOT_NONE  111 (to 1758)   # 跳转目标由 1728 → 1758（then 体多 30 字节）
803     1536 ...                                   # then: tmpdata 设置
806     1668 ... tmpdata = data[:preday].copy()
807     1724 LOAD_FAST 16 (preindex)               # 【兄弟 if #1 被错误并入 then】
         1728 COMPARE_OP != ; 1734 POP_JUMP_FORWARD_IF_FALSE 2 (to 1740)
808     1736 STORE_FAST 16 (preindex)
809  >> 1740 ... if predataindex != curdataindex:  # 【兄弟 if #2 被错误并入 then】
         1750 POP_JUMP_FORWARD_IF_FALSE 2 (to 1756)
810     1752 STORE_FAST 18 (predataindex)
      1756 JUMP_BACKWARD 160 (to 1438)             # then 末尾直接回边，跳过 elif/else 与兄弟 if
811  >> 1758 ... elif data[predataindex:curdataindex].empty
         ...   (elif/else 各分支 2292/2592 处直接 JUMP_BACKWARD to 1438，【丢失兄弟 if】)
```
归一化比较首个差异点 idx 296 即此 `POP_JUMP_FORWARD_IF_NOT_NONE`：orig 目标→330，new 目标→342（then 体多 12 条指令 = 两个兄弟 if）。

### 1.2 反编译源码中的结构错误位置

`/tmp/r24_decompiled.py` 第 802-810 行：

```python
802  if preindex is None:
803      t = datetime.strptime(curdataindex, '%Y-%m-%d %H:%M:%S')
804      pret = t + qdt.timedelta(days=-1)
805      preday = datetime.strftime(pret, '%Y-%m-%d %H:%M:%S')
806      tmpdata = data[:preday].copy()
807      if preindex != n:            # ← 错误：应为 if/elif/else 链之后的兄弟语句
808          preindex = n
809      if predataindex != curdataindex:   # ← 错误：应为兄弟语句
810          predataindex = curdataindex
811  elif data[predataindex:curdataindex].empty:
812      break
     ... elif/else 分支在此处丢失了上述两个兄弟 if（直接回边到循环头）
```

错误描述：第 807-810 行的两个 `if` 本应是 `if/elif/else` 链结束后的循环体兄弟语句（每轮执行，break 除外），被错误嵌套进 `if preindex is None:` 的 then 分支。导致 then 分支多 12 条指令、`POP_JUMP_FORWARD_IF_NOT_NONE` 跳转目标变大，且 elif/else 两个分支完全丢失这两个兄弟 if。

### 1.3 根因初判

- **区域类型**：IF（IfRegion）—— `if preindex is None: ... elif ...: break ... elif/else` 链。
- **字节码模式**：then/elif/else 各分支末尾 `JUMP_FORWARD` 汇聚到循环末尾的兄弟语句块（而非直接 `JUMP_BACKWARD` 到循环头）；兄弟语句块紧跟在 `JUMP_BACKWARD` 回边之前。反编译器把"循环末尾汇聚点之后的兄弟语句"误判为 then 分支的延续。
- **涉及方法方向**：`core/cfg/region_analyzer.py::_identify_conditional_regions`（行 10905）在确定 then-region 边界时，把循环体内 if/elif/else 链的"汇聚后继块"错误归入 then 分支；配合 `core/cfg/region_ast_generator.py::_generate_if` / `_process_if_blocks`（行 7190 / 12780）把 then_blocks 范围过度扩张。修复方向：then-region 边界应止于 then 分支末尾的 `JUMP_FORWARD` 跳转点，循环体内 if/elif/else 链的公共汇聚后继块应保留为循环体的兄弟语句，而非 then 的子节点。

---

## 2. 缺陷 B — `get_date_and_count`：LOOP 反向链吸收外层条件块 + loop_else

### 2.1 orig vs new 字节码关键差异段（标注偏移）

函数位于反编译产物第 985 行。问题集中在 `candle_period == 8`（第 1000-1032 行）和 `candle_period == 15`（第 1045-1089 行）两个分支的 else 子分支。两者同构，下面以 `candle_period == 8` 为例。

**ORIG（正确）— `candle_period==8` 分支 else 子分支（offset 1222~1470）：**
```
1755  >> 1202 ... elif count == 1:                # elif 分支
         1214 STORE_FAST 6 (start_date)
         1220 JUMP_FORWARD 912 (to 3046)          # → return
1758  >> 1222 LOAD_FAST 1 (count)                 # else 分支入口
         1224 LOAD_CONST 1; 1226 BINARY_OP -= ; 1230 STORE_FAST 1   # count -= 1
1760     1232 LOAD_FAST 1 (count); 1236 COMPARE_OP >; 1242 POP_JUMP_FORWARD_IF_FALSE 35 (to 1314)  # while count>0:
1761  >> 1244 ... if month-count<=0: ... else: ... # 循环体
1760  >> 1302 ... count > 0
         1312 POP_JUMP_BACKWARD_IF_TRUE 35 (to 1244)   # ← while 回边
1768  >> 1314 LOAD_FAST 8 (month)                 # if month in (10,11,12): ...
         1320 POP_JUMP_FORWARD_IF_FALSE 36 (to 1394)
         ...   (if/else 各分支 JUMP_FORWARD to 3046 → return)
```
ORIG 全函数共有 **4 个 `POP_JUMP_BACKWARD_IF_TRUE` 回边**（`candle_period==8` 与 `==15` 各 2 个：then/else 各一个 while）。每个 if/elif/else 分支末尾都 `JUMP_FORWARD to 3046`（return），**无任何兄弟语句**。

**NEW（错误）— `candle_period==8` 分支（offset 1198~1440）：**
```
1020  >> 1198 LOAD_FAST 1 (count); 1202 COMPARE_OP == ; 1208 POP_JUMP_FORWARD_IF_FALSE 35 (to 1280)  # elif count==1
         1210 LOAD_FAST 1 (count); 1214 COMPARE_OP >; 1220 POP_JUMP_FORWARD_IF_FALSE 29 (to 1280)   # ← while 条件被并入 elif 守卫
1021     1222 LOAD_FAST 8 (month) ... if month-count<=0: ... else: ...   # ← 裸 if/else（while 包装丢失）
1026  >> 1266 ... else: month = month - count; count = 0
1028  >> 1280 LOAD_FAST 9 (this_month_start_date); 1282 STORE_FAST 6 (start_date)   # ← 多余兄弟赋值
1029     1284 LOAD_FAST 8 (month); 1288 CONTAINS_OP; 1290 POP_JUMP_FORWARD_IF_FALSE 36 (to 1364)    # ← 多余兄弟 if month in...
         ...   (if/else 末尾 JUMP_FORWARD to 2946 → return)
```
NEW 全函数只有 **2 个 `POP_JUMP_BACKWARD_IF_TRUE` 回边**（then 子分支的 while 保留，else 子分支的 while 回边丢失）。else 子分支的 `count -= 1`、`while count>0:` 包装、回边 `POP_JUMP_BACKWARD_IF_TRUE` 全部丢失，循环体降级为裸 `if/else`，`while` 条件被并入 elif 守卫（`elif count == 1 and count > 0`），并多出兄弟 `start_date = this_month_start_date; if month in (10,11,12): ...`。

归一化比较：`len_diff orig=714 new=687 (diff=-27)`。丢失的 27 条 ≈ else 子分支的 `count -= 1`(4) + while 头部条件检测(6) + 回边 `POP_JUMP_BACKWARD_IF_TRUE`(1) + while 末尾二次条件检测(6) + 原本应跳到 return 的跳转调整 等（两个 candle_period 分支合计）。

### 2.2 反编译源码中的结构错误位置

`/tmp/r24_decompiled.py` 第 1000-1032 行（`candle_period == 8` 分支）：

```python
1005  if len(get_trade_days(this_month_start_date, query_date)) == 0:
1006      query_date = datetime.strptime(...) - timedelta(1)
1007      query_date = datetime.strftime(...)
1008      while count > 0:                    # then 子分支的 while（正确保留）
1009          if month - count <= 0: ...
1014          else: ...
1016      if month in (10, 11, 12):           # then 子分支的 if/else（正确）
1017          start_date = ...
1019      else: ...
1020  elif count == 1 and count > 0:          # ← 错误1：elif 守卫多了 "and count > 0"（原为 elif count == 1）
1021      if month - count <= 0:              # ← 错误2：else 子分支的 while 循环体降级为裸 if/else
1022          year -= 1; count -= month; month = 12
1025      else: month = month - count; count = 0
1028  start_date = this_month_start_date      # ← 错误3：多余的兄弟赋值（orig 各分支直接跳 return，无兄弟）
1029  if month in (10, 11, 12):               # ← 错误4：多余的兄弟 if/else
1030      start_date = str(year) + str(month) + '01'
1031  else: start_date = str(year) + '0' + str(month) + '01'
```

错误描述：
1. 第 1020 行 `elif count == 1 and count > 0` —— `and count > 0` 是 else 子分支 `while count > 0:` 的循环条件，被错误并入 elif 守卫。
2. 第 1021-1027 行 —— else 子分支的 `while count > 0:` 循环包装丢失，循环体降级为裸 `if/else`，且丢失了 else 子分支首部的 `count -= 1`。
3. 第 1028-1032 行 —— 多出兄弟 `start_date = this_month_start_date; if month in (10,11,12): ... else: ...`，orig 中每个分支末尾直接 `JUMP_FORWARD to 3046`（return），不存在该兄弟语句。

`candle_period == 15` 分支（第 1045-1089 行）存在完全同构的 4 处错误。

### 2.3 根因初判

- **区域类型**：LOOP（LoopRegion）—— 嵌套在 if/elif/else 的 then/else 子分支内的 `while count > 0:` 循环。
- **字节码模式**：while 循环回边 `POP_JUMP_BACKWARD_IF_TRUE → header`；循环正常退出后紧跟一个 `if month in (10,11,12): ... else: ...` 块，该块末尾 `JUMP_FORWARD` 跳到函数 return；外层 if/elif/else 的每个分支也都 `JUMP_FORWARD` 跳到同一 return 点。反编译器把 while 的回边链 + 循环后的条件块误判为"循环的 loop_else / 循环后的顺序语句"，把 else 子分支的 while 包装拆解。
- **涉及方法方向**：
  - `core/cfg/region_analyzer.py::_identify_loop_regions`（行 2801）+ `_find_loop_else`（行 3717）：在判定 while 循环的 `else_blocks` / `natural_exit` 时，把循环后继的 `if month in ...` 条件块错误归入 loop_else 或循环的自然出口顺序语句，导致 else 子分支的 while 区域被拆散、回边块（`POP_JUMP_BACKWARD_IF_TRUE`）被丢弃。
  - `core/cfg/region_ast_generator.py::_generate_loop`（行 2852）及行 3408/4301 的 "[R5 Fix 1] 无 break 时 else_stmts 不作为 orelse, 而作为 for/while 之后的顺序语句" 逻辑：在 if/elif/else 嵌套 while + 循环后 if/else 且各分支同跳 return 的场景下，把循环后的条件块当作 while 之后的顺序语句外提为兄弟，并把 while 条件并入外层 elif 守卫。
  - 修复方向：while 循环的 region 边界应包含其回边块；循环正常退出后、且该后继块仍位于外层 if/elif/else 同一子分支内（未被外层分支的 `JUMP_FORWARD to return` 截断）时，后继条件块应作为循环后的子分支内顺序语句保留在原分支内，不得外提为兄弟，也不得把 while 条件并入外层 elif。

---

## 3. 最小复现实例清单

所有 repro 位于 `/workspace/.trae/specs/region-reduction-quotation-10rounds-v3/rounds/round_24/test_engineer/minimal_repros/`，均 `py_compile` 通过，再用 `pycdc.py` 反编译后用归一化口径对比 dis。验证脚本：`_run_repros.py`，结果：`_repro_results.json`。

### 缺陷 A（IF then 吸收循环末尾兄弟语句）— 4/4 复现

| 文件 | 体现模式 | 复现结果 |
|---|---|---|
| `repro_01_if_absorb_sibling_in_loop.py` | for 循环 + if/elif(break)/else + 2 个兄弟 if（最贴近 change_his_to_backward） | `instr_diff @idx10`：`POP_JUMP_FORWARD_IF_NOT_NONE` orig→18 vs new→31（与原 bug 同型） |
| `repro_02_if_absorb_sibling_while.py` | while 循环 + if/elif(break)/else + 兄弟赋值 + 兄弟 if | `instr_diff @idx26`：`JUMP_FORWARD` vs `LOAD_FAST` |
| `repro_03_if_absorb_sibling_elif_chain.py` | for 循环 + if/elif/elif(break)/else + 2 个兄弟 if（elif 链变体） | `instr_diff @idx10`：`POP_JUMP_FORWARD_IF_NOT_NONE` orig→18 vs new→31 |
| `repro_04_if_absorb_sibling_minimal.py` | for 循环 + if/elif(break)/else + 1 个兄弟 if（最简，需 break 分支触发） | `instr_diff @idx17`：`JUMP_FORWARD` vs `LOAD_FAST` |

反编译产物验证（以 repro_01 为例）：兄弟 `if pre != n: pre = n` 与 `if len(out) != 0: pass` 被嵌套进 `if pre is None:` then 分支，else 分支丢失兄弟 if（与 change_his_to_backward 完全同型）。

### 缺陷 B（LOOP 反向链吸收外层条件块 + loop_else）— 4/4 复现

| 文件 | 体现模式 | 复现结果 |
|---|---|---|
| `repro_05_loop_absorb_outer_cond_full.py` | if/elif/else，then 与 else 均含 while+if/else，elif 简单（最贴近 get_date_and_count） | `len_diff orig=141 new=71 diff=-70`（整块坍塌为 `while count==1 and count>0`） |
| `repro_06_loop_absorb_outer_cond_else_only.py` | if/elif/else，仅 else 含 while+if/else | `len_diff orig=81 new=67 diff=-14` |
| `repro_07_loop_absorb_outer_cond_if_else.py` | if/elif/else，then 与 else 均含 while+if/else，elif 简单（变体） | `len_diff orig=141 new=71 diff=-70` |
| `repro_08_loop_absorb_outer_cond_simple_body.py` | while 循环体为单语句赋值（无内层 if/else） | `len_diff orig=89 new=46 diff=-43` |

反编译产物验证（以 repro_05 / repro_06 为例）：整个 `if flag==0: ... elif count==1: ... else: ...` 坍塌为 `while count == 1 and count > 0:`（elif 条件 + while 条件合并），`count -= 1` 与 while 包装丢失，多出兄弟 `if month in (10,11,12): ...`（与 get_date_and_count 完全同型）。

---

## 4. 总结

- **当前基线**：148/150 = 98.67%，COMPILE_OK，与 R23 持平，无回归。
- **残留 2 个不一致函数**：
  1. `change_his_to_backward`（instr_diff@296）—— IF then 分支吸收循环末尾兄弟 if，根因在 `_identify_conditional_regions` 的 then-region 边界判定 + `_generate_if` 的 then_blocks 范围。
  2. `get_date_and_count`（len_diff -27）—— LOOP 反向链吸收外层条件块 + loop_else，根因在 `_identify_loop_regions` / `_find_loop_else` 的 else_blocks 边界 + `_generate_loop` 的 R5-Fix1 顺序语句外提逻辑。
- **复现**：两类缺陷各构造 4 个最小 repro（共 8 个），全部复现，字节码模式与原 bug 完全一致。
- **未修改任何反编译器源码或 quotation.pyc**；本轮仅做研究分析与复现实例构造。
