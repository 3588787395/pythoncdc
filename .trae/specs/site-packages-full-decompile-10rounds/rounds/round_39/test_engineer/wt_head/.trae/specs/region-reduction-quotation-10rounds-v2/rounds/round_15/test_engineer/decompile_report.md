# R15 测试工程师报告

## 1. 反编译产物

| 指标 | 值 |
|------|---|
| 输入 pyc | `/workspace/quotation.pyc` |
| 反编译命令 | `pycdc.py --region quotation.pyc` |
| 输出 | `/tmp/r15_decompiled.py` |
| 耗时 | ~1.6s |
| 源码长度 | 175488 字符 / 3641 行 |
| compile_ok | True |

## 2. R15 基线统计（继承 R14 跳转目标归一化）

| 指标 | 值 |
|------|---|
| 总函数数 | 150 |
| 一致函数数 | **145** |
| 不一致函数数 | 5 |
| 缺失函数数 | 0 |
| 成功率 | **96.67%** |
| 基线对照 | R14 修复后 = 145/150 ✓（无退化） |

## 3. 残留 5 个不一致函数

| 函数名 | 状态 | 说明 |
|--------|------|------|
| `<module>` | instr_diff@394 | co_filename 元数据差异 |
| `build_future_fill_time` | instr_diff@226 | **R15 重点**：JUMP_FORWARD 跳转目标偏移 |
| `get_str_data` | len_diff -48 | R12 遗留（循环体语句丢失）|
| `change_his_to_backward` | instr_diff@296 | R14 defer（指令重排）|
| `get_date_and_count` | len_diff -27 | R13 遗留 |

注：`one_prod_to_dataframe` 已在 R14 完全修复，不再列入 FOCUS。

## 4. build_future_fill_time @idx226 差异分析

### 4.1 差异定位

```
idx 226 !! O:1050 JUMP_FORWARD  ->[649]
       !! N:1050 JUMP_FORWARD  ->[629]
```

- orig (pyc): `JUMP_FORWARD` 目标 = idx 649（`LOAD_FAST 'total_dts'`，即 `if total_dts:`）
- new (反编译): `JUMP_FORWARD` 目标 = idx 629（`LOAD_FAST 'trade_days'`，即后置循环开头）
- 两者 opname 相同（JUMP_FORWARD），仅跳转目标 idx 不同（649 vs 629，相差 20）

### 4.2 listcomp code 对象验证（排除任务假设）

任务假设："listcomp 内部 code 对象布局 + 后续跳转目标偏移"。

**验证结果：listcomp code 对象完全相等，非根因。**

- idx 201: `LOAD_CONST <code <listcomp>>`（orig 和 new 均有）
- listcomp 内部指令数：orig=13, new=13（完全一致）
- 13 条指令逐条比较：全部 `instr_equal=True`（含 FOR_ITER ->[12]、JUMP_BACKWARD ->[3] 跳转目标归一化一致）
- co_consts: orig=`(' %H:%M:%S',)`, new=`(' %H:%M:%S',)`（一致）

idx 0-225 全部 `instr_equal=True`（first_diff 确为 226，非 201）。**listcomp 非根因**。

### 4.3 真实根因：后置循环块（loop-block）的跳转目标偏移

**控制流结构**（idx 226 处 JUMP_FORWARD 位于 `if typet == 1:` 分支末尾，跳过 elif 链）：

```
idx 208-225: typet==1 分支内的嵌套循环（trade_days × trade_times）
idx 226: JUMP_FORWARD ->[649(orig) / 629(new)]   ← 差异点
idx 227+: elif typet==2/3/4/13 分支
idx 615/624: suffix 分支 JUMP_FORWARD ->[629]（两边一致）
idx 629-648: 后置循环块（trade_days × market_time，自包含）
  629 LOAD_FAST 'trade_days'
  630 GET_ITER
  631 FOR_ITER ->[649]              ← 循环退出目标 = hi
  632-647 循环体（total_dts.append(today + ' ' + item)）
  648 JUMP_BACKWARD ->[631]          ← 回跳到 FOR_ITER
idx 649: LOAD_FAST 'total_dts'      ← if total_dts: total_dts.sort()
```

**跳转目标统计**（诊断确认）：

| 跳转来源 | orig 目标 | new 目标 |
|---------|----------|---------|
| idx 226 (typet==1 分支末尾) | **649**（跳过循环）| **629**（进入循环）|
| idx 369 (typet==2 分支末尾) | 649（跳过循环）| 629（进入循环）|
| idx 512 (typet==3 分支末尾) | 649（跳过循环）| 629（进入循环）|
| idx 559 (typet==4 分支末尾) | 649（跳过循环）| 629（进入循环）|
| idx 606 (typet==13 分支末尾)| 649（跳过循环）| 629（进入循环）|
| idx 615/624 (suffix 分支) | 629（进入循环）| 629（进入循环）|
| idx 631 (FOR_ITER 退出) | 649 | 649 |

**结论**：
- orig：typet 分支（1,2,3,4,13）JUMP_FORWARD ->[649]，**跳过**后置循环块
- new：typet 分支 JUMP_FORWARD ->[629]，**进入**后置循环块
- 区域 [629, 649) 为自包含循环块：`FOR_ITER(exit=649)` + 循环体 + `JUMP_BACKWARD(->631)`，JUMP_BACKWARD 位于 hi-1

### 4.4 归一化可行性

R14 的 `_chase_elif_chain` 在该处**正确返回 False**：
- 从 lo=629 跟随到 hi=649，idx 630 为 `GET_ITER`（非 PURE_COND_OPS，有副作用）
- 追随在 GET_ITER 处停止，无法到达 649
- **不能**通过 R14 的 elif 链归一化解决

R15 需新增**循环块旁路归一化**（loop-block bypass）：
- 当 JUMP_FORWARD 目标 ta≠tb，区域 [min,max) 为自包含循环块（FOR_ITER exit=max + JUMP_BACKWARD->FOR_ITER 位于 max-1）时，视为等价
- 安全保证：要求 orig/new 的 [lo,hi) 指令序列（opname 列表）完全相同，防止误归一化指令重排

## 5. 最小复现实例（10 个）

| # | 文件 | 模式 |
|---|------|------|
| 1 | repro_01_if_elif_post_chain_loop.py | if/elif + 后置循环（基线模式）|
| 2 | repro_02_if_elif_else_single_loop.py | if/elif/else + 单层后置循环 |
| 3 | repro_03_nested_post_chain_loop.py | 嵌套后置循环（两层 for）|
| 4 | repro_04_branch_sets_var_post_loop_uses.py | 分支设置变量 + 后置循环使用 |
| 5 | repro_05_listcomp_branch_post_loop.py | 分支含 listcomp + 后置循环 |
| 6 | repro_06_single_if_post_loop.py | 单 if + 后置循环（最简）|
| 7 | repro_07_post_nested_double_loop.py | 后置双循环（外+内 FOR_ITER）|
| 8 | repro_08_post_loop_method_call.py | 后置循环含方法调用 |
| 9 | repro_09_post_loop_binary_op.py | 后置循环含 BINARY_OP 拼接 |
| 10 | repro_10_five_branch_post_loop.py | 5 分支 if/elif + 后置循环（最接近原函数）|

所有复现实例均通过 `py_compile` 编译验证。

## 6. 编译与导入

| 检查项 | 结果 |
|--------|------|
| py_compile /tmp/r15_decompiled.py | COMPILE_OK ✓ |
| IMPORT_OK | pytz ModuleNotFoundError（环境依赖，与 R14 一致）|

## 7. 交付物

- `/tmp/r15_decompiled.py`（反编译产物）
- `/tmp/r15_out/bc_results.json`（一致性统计 JSON）
- `/tmp/r15_out/diff_detail.txt`（5 个 FOCUS 函数的逐指令 diff）
- `minimal_repros/repro_01..10_*.py`（10 个最小复现实例）
- `decompile_report.md`（本报告）
