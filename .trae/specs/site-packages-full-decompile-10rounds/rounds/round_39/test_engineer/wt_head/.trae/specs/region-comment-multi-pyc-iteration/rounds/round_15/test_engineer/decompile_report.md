# R15 测试工程师报告 — trade_schedule.pyc

## 1. 目标 pyc

- **路径**: `site-packages/IQCommon/trade_schedule.pyc`
- **decompile_status（R15 前）**: pending（last_tested_round=0，诊断阶段 partial 50%）
- **本轮重点**: get_trading_schedule「if-then=continue 内层 for 循环误并入 else 分支」缺陷 + is_stock/future_trade_time_now「BoolOp-in-return（chained-compare + OR 短路）误分解为 if+pass」残留

## 2. 反编译 + 字节码 diff 结果

| 指标 | R15 前（诊断 partial） | R15（post-fix） |
|------|------------------------|-----------------|
| total_functions | 6 | 6 |
| matched_functions | 3 | 4 |
| match_rate | 50.00% | **66.67%** |
| mismatches | 3 | 2 |

- **match_rate 改善**: 50.00% → 66.67%（+1 函数匹配，-1 mismatch）
- **decompile_status**: partial（未达 100%，残留 is_stock/future_trade_time_now 2 个 mismatch）

## 3. 不一致函数清单（2 mismatch）

| 模式 | 数量 | 代表函数 | 说明 |
|------|------|----------|------|
| BOOLOP_IN_RETURN | 2 | is_stock_trade_time_now / is_future_trade_time_now | orig=36 decomp=57，jump_diffs=9 true_diffs=28，first_diff: index 24 orig=LOAD_GLOBAL STOCK_PM_OPEN decomp=NOP |

### is_stock / is_future_trade_time_now 残留分析

- **源码结构**: `return STOCK_AM_OPEN < now < STOCK_AM_CLOSE or STOCK_PM_OPEN < now < STOCK_PM_CLOSE`
- **字节码**: chained compare（`A < x < B`）发射 `JUMP_IF_FALSE_OR_POP`；BoolOp OR 发射 `JUMP_IF_TRUE_OR_POP`。两类短路跳转在 return-expression 上下文中交错。
- **缺陷**: `JUMP_IF_TRUE_OR_POP`（BoolOp OR 短路）被误识别为 if-branch 控制流，将单一 return 表达式分解为多个 `if ...: pass` 语句。decomp 产物（57 条指令 vs orig 36 条）含 4 个独立 `if` + 多个 `return None`，结构语义已偏离原 `return <boolop>` 表达式。
- **性质判定**: BOOLOP-in-return 模式（chained-compare × BoolOp OR 交错于值上下文）。该模式涉及 BoolOpRegion / ChainedCompareRegion 与 return-expression 上下文的交互，根因较深（区域归约将值上下文的短路跳转误作控制流分支），本轮 R15 修复（continue-sink 检测）未触及该路径，作为残留留待后续轮次。

## 4. 最小复现实例（12 个）

归档于 `minimal_repros/`，覆盖以下场景：

| 实例 | 场景 | 类型 | 结果 |
|------|------|------|------|
| repro_01 | is_stock_trade_time_now 镜像（chained-compare + OR in return） | DEFECT-REPRO | 1/2 matched, 37 diffs (is_stock_trade_time_now) |
| repro_02 | is_future_trade_time_now 镜像（chained-compare + OR in return） | DEFECT-REPRO | 1/2 matched, 37 diffs (is_future_trade_time_now) |
| repro_03 | 最小 chained-compare + OR in return（int 常量） | DEFECT-REPRO | 1/2 matched, 37 diffs (f) |
| repro_04 | 三路 chained-compare + OR in return | DEFECT-REPRO | 1/2 matched, 37 diffs (f) |
| repro_05 | chained-compare + AND in return | DEFECT-REPRO | 1/2 matched, 41 diffs (f) |
| repro_06 | chained-compare + OR in return（双变量） | DEFECT-REPRO | 1/2 matched, 37 diffs (f) |
| repro_07 | chained-compare + OR 赋值后 return | DEFECT-REPRO | 1/2 matched, 19 diffs (f) |
| repro_08 | get_trading_schedule 镜像（continue + 内层 for，验证 R15 修复） | CTRL (NO-DEFECT) | 2/2 matched |
| repro_09 | continue + 简单赋值 post-if（验证 R15 修复） | CTRL (NO-DEFECT) | 2/2 matched |
| repro_10 | while 循环 continue + 赋值 post-if（验证 R15 修复） | CTRL (NO-DEFECT) | 2/2 matched |
| repro_11 | break + 赋值 post-if（R2-C 既有处理，回归控制） | CTRL (NO-DEFECT) | 2/2 matched |
| repro_12 | 简单 if-in-for 无 continue（纯控制组） | CTRL (NO-DEFECT) | 2/2 matched |

### 验证方法

`verify_repros.py` 对每个 repro 执行：编译 → 反编译 → 重编译 → 字节码 diff（含 code-object 身份噪声归一化）。

- **7 DEFECT-REPRO**（repro_01-07）：隔离 is_stock/future_trade_time_now 的 BOOLOP-in-return（chained-compare + BoolOp OR/AND 短路在 return 上下文）模式。该模式为 R15 残留，反编译器将 `JUMP_IF_TRUE_OR_POP` 误作 if-branch，把单一 return 表达式分解为多 if+pass。
- **5 CTRL NO-DEFECT**（repro_08-12）：repro_08-10 验证 R15 修复（continue-sink 检测使内层 for / 赋值正确归为 post-if 语句）；repro_11 验证 R2-C 既有 break 处理无回归；repro_12 为简单 if-in-for 纯控制组。

## 5. 累计成功率

- R14 committed: 66.36%（31 verified pyc, 290/437 matched）
- R15: trade_schedule.pyc pending → 66.67%（+1 matched / +6 total），累计 **66.37%**（32 verified pyc, 294/443 matched）
- **注**: 累计成功率随 verified 集合扩张重算。R15 前 290/437=66.36%，R15 后 294/443=66.37%，本 pyc 贡献 +1 matched（get_trading_schedule 修复）使累计微升。

## 6. 残留不一致

- **is_stock_trade_time_now / is_future_trade_time_now**: 2 mismatch（BOOLOP-in-return 模式：chained-compare + BoolOp OR 短路在 return 上下文被误分解为 if+pass。根因较深，留待后续轮次）
- **跨轮残留**（不变）: T3/T2/A2/B/C/E/F/M2/G3/R 等模式见各轮报告
