# LOOP 区域 Round 01 验证清单

## 基线确认
- [x] `while_loop`+`for_loop` = 18 failed / 295 passed（无退化，#1/#11 修复未影响基线）
- [x] `ternary` = 68 failed / 530 passed / 0 skipped
- [x] `loop/round_01/` 起点 = 2 passed（#1、#11）/ 14 failed

## Cluster 1（已完成）
- [x] #1 `while True: if a: continue; b=1` — `_block_is_pure_continue` + `_loop_handle_no_exit_successors` then-pure-continue 分支，body 不丢失
- [x] #11 `while a: if (n := f()): break` — walrus `COPY 1+STORE_*` 跳过切分 + header break/return 路由 `_loop_process_header_instructions`，body 不退化为 pass
- [x] 修复依 4 原则：原则 2（每块唯一归属，body 语句块不被回边角色吞并）+ 原则 4（父引用子入口，else 后继留作顺序归约）+ 原则 1（自底向上，header 指令级重建）

## Cluster 2 — try-in-loop（#2、#3、#10、#13）
- [ ] #2 `for+try/except`：try-body 内 break 被识别为 break_blocks（不被 PUSH_EXC_INFO 过滤误排除），`continue` 保留，`return i` 不被拉进循环体
- [ ] #3 `for+try/finally+break`：for 循环不消失，try-finally 不跨越 for header（原则 1 自底向上归约顺序）
- [ ] #10 `while+try/except/else/finally+break`：finally 块唯一归属（不被同时归入 except 与外层 finally），except 内 break 与 finally 清理块解耦（原则 2）
- [ ] #13 `for+try` 嵌套 `if a: if b: continue`：双层守卫保留，continue 不变无条件，`x=1` 不变死代码
- [ ] 修复依 4 原则论证（无跨区域特例）
- [ ] while_loop+for_loop 回归 ≤ 18 failed
- [ ] ternary 回归 ≤ 68 failed

## Cluster 3 — boolop / chained compare 条件（#4、#6、#8、#14、#16）
- [ ] #4 `while 0 < x < 10`：条件块不被 chained_compare IfRegion 抢占拆分，`while 0 < x < 10` 完整（原则 2）
- [ ] #6 `while not a and b`：复合 `and` 首操作数 `not a` 不丢失
- [ ] #8 `while 0 <= x < 10 + break`：循环与 break 不合并为单 if，循环体与回边保留（原则 1 + 原则 2）
- [ ] #14 `while 0 < x < y < 100`：三段链式比较无 `<copy_placeholder_*>` 占位符泄漏，可重编译
- [ ] #16 `while a and b and c`：首操作数 `a` 不泄漏为循环体末尾 `if a: pass else: break`
- [ ] 修复依 4 原则论证
- [ ] while_loop+for_loop 回归 ≤ 18 failed
- [ ] ternary 回归 ≤ 68 failed

## Cluster 4 — ternary / yield-from / for iter（#5、#7、#12）
- [ ] #5 `while (a if c else b)`：fused ternary-loop 条件识别不抑制循环体，body `x=1` 不丢失
- [ ] #7 `for x in (a or b)`：iter boolop 短路链不泄漏为独立语句，iter 目标不回退为 `None`
- [ ] #12 `while a: yield from inner()`：yield-from 隐式循环正确识别为 yield-from 表达式，`GET_YIELD_FROM_ITER` 链不丢失为 `None`
- [ ] 修复依 4 原则论证
- [ ] while_loop+for_loop 回归 ≤ 18 failed
- [ ] ternary 回归 ≤ 68 failed

## Cluster 5 — loop-else / 嵌套（#9、#15）
- [ ] #9 `while-else: return 1; return 2`：else 的 `return 1` 不降级为循环后无条件 return，`return 2` 不丢失
- [ ] #15 嵌套 for + 内层 else + 外层 break：内层 `else: continue` 不降级为内层循环体顺序 continue，外层 break 与 else 边界保留（原则 3 嵌套即抽象节点）
- [ ] 修复依 4 原则论证
- [ ] while_loop+for_loop 回归 ≤ 18 failed
- [ ] ternary 回归 ≤ 68 failed

## Docstring 更新
- [ ] `_identify_loop_regions` docstring 已更新（6 节模板，含本轮已知失败模式与算法根因）
- [ ] `_generate_loop` docstring 已更新（4 节模板，含本轮生成阶段修复纪要）

## 修复报告
- [ ] `fix_report.md` 已写入 `/workspace/.trae/specs/iterate-region-test-fix/rounds/loop/round_01/fix_report.md`
- [ ] 报告含基线 / 已修复错误（源码+根因+方案+4 原则论证+验证）/ 已知限制 / 回归结果 / 合规自检 / 清理确认

## 清理与合规
- [ ] 根级 `_debug_r1_*.py` / `_debug_r*_*.py` 已删除
- [ ] 源代码无 debug 打印残留（grep `print(`/`pdb`/`breakpoint()` 仅匹配注释）
- [ ] 未修改任何测试文件
- [ ] 未 git commit（由父代理决定提交时机）
- [ ] 所有修复均通过 4 原则论证，无跨区域启发式特例 / 后处理补丁 / 启发式优先级覆盖 / 扁平化 / 硬编码深度上限 / `_fix_`/`_merge_`/`_patch_`/`_fallback_`/`_hack_`/`_workaround_`/`_temp_` 前缀命名
