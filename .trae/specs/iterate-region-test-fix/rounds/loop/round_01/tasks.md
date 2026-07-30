# Tasks — LOOP 区域 Round 01

> 父 spec：`/workspace/.trae/specs/iterate-region-test-fix/spec.md`（Phase 2 / Task 2.1）
> 输入：`test_findings.md`（16 个 LOOP 区域反编译错误）
> 修复必须严格依「区域归约算法 4 原则」：自底向上归约 / 每块唯一归属 / 嵌套即抽象节点 / 父引用子入口。
> 禁止：跨区域启发式特例 / 后处理补丁 / 启发式优先级覆盖 / 破坏嵌套的扁平化 / 硬编码深度上限 / `_fix_`/`_merge_`/`_patch_`/`_fallback_`/`_hack_`/`_workaround_`/`_temp_` 前缀命名。
> 每批修复 3-5 个相关 bug（按根因聚类），每批后运行回归；若某修复导致退化，回滚该修复换方案。
> 所有命令用 `timeout 240` 包裹。本轮不 git commit（由父代理决定提交时机）。

## 基线（不可退化）

- 现有 `while_loop` + `for_loop`：313 测试 | 295 passed | **18 failed**（已知失败：`l15whiletruebreak`×3、`wl30whilebreakintry`×2、`wl32whilemultibreak`×2、`for-else+break` 系列 11 个）
- 跨区域 `ternary`：598 测试 | 530 passed | **68 failed** | 0 skipped
- 本轮新测试 `loop/round_01/`：16 测试 | **2 passed**（#1、#11）| **14 failed**

## 起点状态（已完成的修复）

- `core/cfg/region_ast_generator.py` 已含 #1、#11 修复（80 行新增，未提交）：
  - `_block_is_pure_continue`：区分纯 continue 块（无 body 语句）与含 body 语句的 fall-through 块（原则 2 每块唯一归属）。
  - `_loop_handle_no_exit_successors`：then 为纯 continue 而 else 含 body 时生成 `if cond: continue`，else 后继留作循环体顺序归约（原则 4 父引用子入口）。
  - `_loop_handle_exit_successors` / `_loop_handle_no_exit_successors`：跳过 walrus `COPY 1 + STORE_*` 切分点，让 expr_reconstructor 重建 NamedExpr（原则 2）。
  - header 一后继 break/return、另一后继即回边块时调用 `_loop_process_header_instructions` 指令级重建 `if <expr>: break/return`（原则 1 自底向上 + 原则 4）。
- `core/cfg/region_analyzer.py` 未改动（与 HEAD 一致）。

---

## Task 2.1.0: 基线确认
- [x] 确认 `while_loop`+`for_loop` = 18 failed / 295 passed（无退化）
- [x] 确认 `ternary` = 68 failed / 530 passed
- [x] 确认 `loop/round_01/` = 2 passed（#1、#11）/ 14 failed

## Task 2.1.1 (P0): Cluster 1 — while-true continue + walrus break（#1、#11）✅ 已完成
- [x] #1 `while True: if a: continue; b=1` — body 不丢失、不被替换为 `else: continue`
- [x] #11 `while a: if (n := f()): break` — walrus + if-break 不退化为 `pass`
- [x] 回归：while_loop 7 failed / for_loop 11 failed 不增加；ternary 68 不增加

## Task 2.1.2 (P0): Cluster 2 — try-in-loop 归约顺序（#2、#3、#10、#13）
- [ ] #2 `for+try/except`：try-body 内 break（跳循环外）被异常块过滤逻辑误排除；`continue` 丢失；`return i` 被拉进循环体
  - 根因方向：`_detect_break_continue`（region_analyzer.py:4127）对 PUSH_EXC_INFO 异常块的 break 识别；`_loop_handle_back_edge`（region_ast_generator.py:6668）不应把循环后语句并入
- [ ] #3 `for+try/finally+break`：try-finally 先于 loop 归约，吞含 break 的循环体，LoopRegion 不再识别 → for 循环完全消失
  - 根因方向：违反原则 1（自底向上）—— try-finally 不应跨越 for header；`_identify_try_except_regions` 与 `_identify_loop_regions` 的归约顺序 / 边界
- [ ] #10 `while+try/except/else/finally+break`：finally 块被同时归入 except handler 与外层 finally（违反原则 2）；except 内 break 与 finally 清理块耦合
  - 根因方向：`_detect_break_continue` 把 except 内 break 与 finally 清理块耦合；finally 块唯一归属
- [ ] #13 `for+try` 嵌套 if 的 continue 守卫丢失：`if a: if b: continue` 双层守卫被吞，continue 变无条件，`x=1` 变死代码
  - 根因方向：`_loop_handle_continue`（region_ast_generator.py:6653）与 try 区域归约交互；内层 continue 条件块被吞为 continue 入口
- [ ] 回归：本批 4 测试通过；while_loop+for_loop ≤ 18 failed；ternary ≤ 68 failed

## Task 2.1.3 (P0): Cluster 3 — boolop / chained compare 循环条件（#4、#6、#8、#14、#16）
- [ ] #4 `while 0 < x < 10`：链式比较中间块被识别为独立 IfRegion，while 条件块被拆退化为 `while 10`
  - 根因方向：`_identify_chained_compare_regions`（region_analyzer.py:10641）与 LOOP 争抢 header；原则 2 每块唯一归属
- [ ] #6 `while not a and b`：复合 `and` 首操作数 `not a` 丢失
  - 根因方向：`_detect_while_condition_boolop_chain`（region_analyzer.py:16382）回溯 `not` 前缀块不足；`_back_edge_recheck_count` 计数
- [ ] #8 `while 0 <= x < 10 + break`：循环与 break 合并为单 if，循环体与回边全丢失
  - 根因方向：chained_compare 把条件块与 break 守卫块合并为 IfRegion，LoopRegion header 被吞（原则 1 + 原则 2）
- [ ] #14 `while 0 < x < y < 100`：三段链式比较 COPY 占位符泄漏 `<copy_placeholder_2>`，语法错误
  - 根因方向：`_identify_chained_compare_regions` 对 3 段以上中间值 COPY 未物化为临时变量
- [ ] #16 `while a and b and c`：首操作数 `a` 泄漏为循环体末尾 `if a: pass else: break`
  - 根因方向：`_detect_while_condition_boolop_chain` 对 3 操作数 `and` 回溯不完整；`_back_edge_recheck_count` 等价出口计数
- [ ] 回归：本批 5 测试通过；while_loop+for_loop ≤ 18 failed；ternary ≤ 68 failed

## Task 2.1.4 (P1): Cluster 4 — ternary / yield-from / for iter 复合表达式（#5、#7、#12）
- [ ] #5 `while (a if c else b)`：fused ternary-loop 识别使 `condition_block=None`，循环体被当三元 merge 抑制 → body 丢失降级为 if
  - 根因方向：`_is_fused_ternary_false_value_block`（region_analyzer.py:16546）+ `_loop_generate_while` 三元消费（region_ast_generator.py:3535）
- [ ] #7 `for x in (a or b)`：iter 表达式 boolop 短路链被当独立语句泄漏，iter 回退为 `None`
  - 根因方向：`_loop_generate_for`（region_ast_generator.py:3130）取 iter 时未识别 preheader `GET_ITER` 前的 `JUMP_IF_TRUE_OR_POP` 短路链
- [ ] #12 `while a: yield from inner()`：yield-from 隐式循环（SEND+YIELD_VALUE 自循环）未识别为 yield-from 表达式，循环体被当普通块，`GET_YIELD_FROM_ITER` 链丢失为 `None`
  - 根因方向：`_identify_loop_regions` 模式 E（region_analyzer.py:2911 `is_yield_from`）
- [ ] 回归：本批 3 测试通过；while_loop+for_loop ≤ 18 failed；ternary ≤ 68 failed

## Task 2.1.5 (P1): Cluster 5 — loop-else / 嵌套循环边界（#9、#15）
- [ ] #9 `while-else: return 1; return 2`：else 的 `return 1` 被降级为循环后无条件 return，`return 2` 丢失
  - 根因方向：`_find_loop_else` while 分支（region_analyzer.py:3864-3867）；else 块是 return 时 natural_exit 与 post-dominator 边界混淆
- [ ] #15 嵌套 for + 内层 else + 外层 break：内层 `else: continue` 降级为内层循环体顺序 continue，外层 break 与 else 边界丢失
  - 根因方向：`_find_loop_else`（region_analyzer.py:3847）内层 for-else 的 else 块与外层 break 目标 post-dominator 混淆（原则 3 嵌套即抽象节点）
- [ ] 回归：本批 2 测试通过；while_loop+for_loop ≤ 18 failed；ternary ≤ 68 failed

## Task 2.1.6: 更新 docstring
- [ ] 更新 `_identify_loop_regions` docstring（6 节模板：职责 / 算法概览 / 已知失败模式 / 算法根因 / 修复纪要 / 约束），写入本轮修复后的反编译逻辑（continue 角色分发 / walrus 条件 / try-in-loop 归约顺序 / boolop 与 chained_compare 条件回溯 / loop-else 边界）
- [ ] 更新 `_generate_loop` docstring（4 节模板：职责 / AST 映射 / 已知失败模式 / 修复纪要），写入本轮生成阶段修复逻辑
- [ ] 若某簇标记为已知限制，在 docstring「已知失败模式」节明确记录

## Task 2.1.7: 写修复报告
- [ ] 将修复报告写入 `/workspace/.trae/specs/iterate-region-test-fix/rounds/loop/round_01/fix_report.md`
- [ ] 报告含：基线 / 已修复错误（按簇列源码、根因、修复方案、4 原则论证、验证）/ 已知限制 / 回归结果 / 算法合规性自检 / 清理确认

## Task 2.1.8: 清理
- [ ] 删除根级临时调试脚本：`_debug_r1_e1.py`、`_debug_r1_e1b.py`、`_debug_r1_cluster1.py` 及任何 `_debug_r*_*.py`
- [ ] 源代码无 debug 打印残留（grep `print(`/`pdb`/`breakpoint()` 仅匹配注释）
- [ ] 未修改任何测试文件
- [ ] 未 git commit（由父代理决定提交时机）

## Task 2.1.9: 最终回归 + 合规自检
- [ ] `timeout 240 python -m pytest tests/exhaustive/loop/round_01/ -q`：≤（14 - 已修复数）failed
- [ ] `timeout 240 python tests/exhaustive/run_test_matrix.py --category for_loop --category while_loop`：≤ 18 failed
- [ ] `timeout 240 python tests/exhaustive/run_test_matrix.py --category ternary`：≤ 68 failed
- [ ] 算法合规性自检：归约顺序 / 每块唯一归属 / 嵌套即抽象节点 / 父引用子入口；无跨区域特例 / 后处理补丁 / 启发式优先级覆盖 / 扁平化 / 硬编码深度上限 / 禁用前缀命名

# Task Dependencies
- Task 2.1.2 / 2.1.3 / 2.1.4 / 2.1.5 互相独立，可并行（不同根因簇，但都改 region_analyzer.py / region_ast_generator.py，建议串行以避免合并冲突）
- Task 2.1.6 依赖 2.1.2-2.1.5 完成（汇总修复逻辑）
- Task 2.1.7 依赖 2.1.2-2.1.6 完成
- Task 2.1.8 / 2.1.9 在最后执行
