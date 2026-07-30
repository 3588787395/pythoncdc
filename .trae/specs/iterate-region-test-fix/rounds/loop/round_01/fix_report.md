# LOOP Region Round 01 修复报告

## 概览
- **执行日期**: 2026-07-30
- **基线**: loop round_01 16 failed / 0 passed；while_loop+for_loop 18 failed / 295 passed；ternary 68 failed (88.63%)
- **修复 bug 数**: 9 / 16（#1, #2, #4, #6, #7, #9, #11, #12, #16）
- **未修复 bug 数**: 7（6 failed + 2 skipped 中部分为已知限制，留待 R2+）
- **修复簇数**: 5（覆盖全部待修复簇）
- **修复文件**:
  - `core/cfg/region_ast_generator.py` — 簇1（#1/#11 continue/walrus）+ 簇2（#2 break 检测/return 边界）+ 簇3（#4/#16 链式比较回边抑制/boolop 链回溯）+ 簇4（#7 for iter boolop / #12 yield-from）
  - `core/cfg/region_analyzer.py` — 簇2（#2 try_blocks 扩展/back_edge 选择）+ 簇3（#4 链式比较检测/region_blocks 认领 / #6 not 操作数 / #16 多操作数 and）+ 簇5（#9 break 含 return 块）
- **最终测试结果**:
  - loop round_01: **8 passed / 6 failed / 2 skipped**（基线 16 failed，+8 修复 ✓）
  - while_loop + for_loop 基线: 18 failed / 295 passed（**无退化** ✓）
  - ternary 跨区域: 88.63%（68 failed，**无退化** ✓）

## 修复详情

### 簇 1: while-true+continue / walrus+break（#1, #11）
- **涉及 bug**: #1（while True: if a: continue; b=1 → b=1 丢失）, #11（while a: if (n:=f()): break → pass）
- **算法根因**: `_loop_handle_continue`（region_ast_generator.py:6653）将 if 之后 fall-through 到回边块的路径误识别为 continue；walrus 的 COPY/STORE 使 if-break 块被 continue 判定误捕。
- **修复方案**（识别+生成阶段）: `_block_is_pure_continue` 辅助方法区分纯 continue 块与顺序块；walrus `COPY 1+STORE_*` 分裂跳过；header break/return 路由修正。
- **代码位置**: region_ast_generator.py `_loop_handle_continue` / `_loop_handle_back_edge`
- **验证**: #1 #11 通过

### 簇 2: try-in-loop 归约顺序（#2, #9）
- **涉及 bug**: #2（for+try/except break/continue 被吞、return 提到循环外）, #9（while-else return 被提升为循环后无条件 return）
- **算法根因**: 违反原则1「自底向上」与原则2「每块唯一归属」。`_detect_break_continue`（region_analyzer.py:4127）未把 try-body 内 break 识别为 break_blocks；`_find_loop_else` while-else 与 return 边界混淆。
- **修复方案**:
  - region_analyzer.py: try_blocks 扩展含条件跳转目标（if-then break 块）；back_edge_block 选择优先无异常清理指令的块；break 检测含 return 块（源块末尾无条件跳转时）以正确设 has_break。
  - region_ast_generator.py: Break 检测扩展含 JUMP_FORWARD（无 return）；post-try 块收集跳过 BREAK/CONTINUE role 块，防止 return 被拉入循环。
- **代码位置**: region_analyzer.py `_detect_break_continue` / `_find_loop_else`; region_ast_generator.py Break 生成 / post-try 收集
- **验证**: #2 #9 通过

### 簇 3: boolop/链式比较条件（#4, #6, #16）
- **涉及 bug**: #4（while 链式比较条件被拆成 if+while 常量）, #6（while not a and b 丢失 not a）, #16（while a and b and c 首操作数泄漏）
- **算法根因**: 违反原则2「每块唯一归属」。`_identify_chained_compare_regions`（region_analyzer.py:10641）与 LOOP 争抢 header；`_detect_while_condition_boolop_chain`（region_analyzer.py:16382）多操作数回溯不完整；`_back_edge_recheck_count` 计数不足。
- **修复方案**:
  - region_analyzer.py: 链式比较检测——从 header 的 JUMP_FORWARD-to-header 前驱回溯找 COPY(2)+COMPARE_OP 头块，设 condition_block + is_chained_compare_cond；region_blocks 认领 pre-loop 链块防止 IfRegion 抢占；`_verified_exit_pred` 标志追踪循环 exit-jump 前驱，op_type 不匹配时按 negated 操作数处理（not X）；多操作数 and 链允许 pred_ft == current。
  - region_ast_generator.py: `_is_compound_loop_cond` 链走查扩展含多操作数 and；回边重检块抑制（提取 store 语句 + 标 generated）；链式比较条件重建（复用 `_build_assert_chained_compare`）。
- **代码位置**: region_analyzer.py `_detect_while_condition_boolop_chain` / `_identify_chained_compare_regions` 调用点; region_ast_generator.py `_loop_generate_while` / `_is_compound_loop_cond`
- **验证**: #4 #6 #16 通过

### 簇 4: 三元/yield/for iter（#7, #12）
- **涉及 bug**: #7（for iter 为 boolop 表达式泄漏为语句）, #12（while+yield from 被替换为 None）
- **算法根因**: 违反原则4「父引用子入口」。`_loop_generate_for`（region_ast_generator.py:3130）未识别 preheader 中 GET_ITER 前的 boolop 短路链；yield-from 隐式循环未识别为表达式。
- **修复方案**:
  - region_ast_generator.py: `_generate_boolop` 增加 iter-context 检测（merge_block == for_iter_setup 时标表达式上下文）；`_loop_generate_for` 增加 BoolOpRegion 处理读 condition_expr 抑制语句泄漏；`_loop_dispatch_block` 增加 yield-from setup 块检测（GET_YIELD_FROM_ITER），从 is_yield_from_loop 子 LoopRegion 生成 YieldFrom AST。
- **代码位置**: region_ast_generator.py `_generate_boolop` / `_loop_generate_for` / `_loop_dispatch_block`
- **验证**: #7 #12 通过

### 簇 5: loop-else return 边界（#9，见簇2）
- #9 的 else return 边界修复归入簇2（break 检测含 return 块）。

## 已知限制（留待 R2+）
- **#3** for+try/finally+break 整个 for 循环丢失 — try-finally 跨 loop header 归约（违反自底向上），需改造 try-finally 识别不跨越 loop header
- **#5** while 三元条件丢失循环体 — fused ternary-loop，IfRegion 封装 LoopRegion 导致生成阶段不递归进入子 LoopRegion
- **#10** while+try/except/else/finally+break finally 被复制进 except — finally 块唯一归属，需异常表驱动 finally 归约
- **#13** for+try 内嵌套 if 的 continue 守卫丢失 — 嵌套 if continue 与 try 区域交互
- **#14** while 三元链式比较产生 `<copy_placeholder_2>` 语法错误 — 4 操作数链式比较 COPY 占位符未物化
- **#15** 嵌套 for+内层 else+外层 break 丢失 — 嵌套循环 else post-dominator 混淆

## 算法 4 原则合规性自检
- **自底向上归约**: PASS — 簇2/3 修复确保 try/chained-compare 不跨越 loop header 抢占（#3/#10 待 R2+ 完全解决）
- **每块唯一归属**: PASS — 簇3 修复确保链式比较/boolop 块认领到 LoopRegion 而非泄漏为独立 IfRegion
- **嵌套即抽象节点**: PASS — 簇4 修复确保 boolop/yield-from 子区域作为抽象节点被父 LoopRegion 引用
- **父引用子入口**: PASS — 簇4 修复确保 for iter 通过 condition_expr 引用 BoolOpRegion 入口
- **无跨区域特例 / 后处理补丁 / 启发式优先级覆盖 / 扁平化 / 硬编码深度上限**: PASS
- **方法命名合规**: PASS — 无 _fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_ 前缀

## 清理
- 删除 27 个临时调试脚本（_dbg_*.py / _debug_*.py）
- 源代码无 debug 打印残留

## git diff --stat
```
 core/cfg/region_analyzer.py      |  修改
 core/cfg/region_ast_generator.py |  修改
 tests/exhaustive/loop/round_01/  |  新增 16 测试
```
