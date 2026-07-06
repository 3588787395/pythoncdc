# Tasks

## Phase 1: Match Region修复 (7f)

- [ ] Task 1.1: 修复M054/M061/M069 — try在match case body中try body变pass
  - [ ] 1.1.1: 在`_generate_try_body`中添加`if region.entry in r.blocks: continue`跳过父MatchRegion
  - [ ] 1.1.2: 验证M054/M061/M069测试通过
  - [ ] 1.1.3: 运行match_region回归测试确认无回归

- [ ] Task 1.2: 修复M106 — match guard with BoolOp case body变pass
  - [ ] 1.2.1: 在`region_analyzer.py`的`_mr_collect_case_body`中添加or-guard分支（POP_JUMP_*_IF_TRUE检测）
  - [ ] 1.2.2: 在`region_analyzer.py`的`pattern_jump_targets`中排除TRUE跳转目标
  - [ ] 1.2.3: 在`region_ast_generator.py`的`_generate_match`中修复body_start>0的noise filter（LOAD_CONST argval非None时不跳过）
  - [ ] 1.2.4: 验证M106测试通过
  - [ ] 1.2.5: 运行match_region回归测试确认无回归

- [ ] Task 1.3: 修复M083 — guard表达式泄漏到case body
  - [ ] 1.3.1: 在`_collect_guard_pattern_blocks`的allowed集合中添加CALL/BINARY_OP/BUILD_*/MAKE_FUNCTION等操作码
  - [ ] 1.3.2: 验证M083测试通过
  - [ ] 1.3.3: 运行match_region回归测试确认无回归

- [ ] Task 1.4: 修复M107 — match mapping pattern with guard结构错误
  - [ ] 1.4.1: 分析M107字节码差异（74 vs 76，多2条POP_TOP）
  - [ ] 1.4.2: 在`_generate_match`中检测并过滤mapping pattern guard多余的POP_TOP
  - [ ] 1.4.3: 验证M107测试通过
  - [ ] 1.4.4: 运行match_region回归测试确认无回归

- [ ] Task 1.5: 修复M075 — match case body中BoolOp展开错误
  - [ ] 1.5.1: 分析M075字节码差异（24 vs 28，多4条指令）
  - [ ] 1.5.2: 修复case body中`if a and b:`不被拆分为嵌套if
  - [ ] 1.5.3: 验证M075测试通过
  - [ ] 1.5.4: 运行match_region回归测试确认无回归

## Phase 2: Try-except修复 (8f)

- [ ] Task 2.1: 修复TRY15 — handler body return语句错误
  - [ ] 2.1.1: 在`_generate_handler_body_statements`中添加SWAP指令异常清理检测（后继含POP_EXCEPT时跳过SWAP）
  - [ ] 2.1.2: 在POP_EXCEPT处理的has_return_after continue前过滤stmt_instrs中的SWAP
  - [ ] 2.1.3: 添加`_merge_handler_expr_return`方法合并Expr+bare Return为Return with value
  - [ ] 2.1.4: 验证TRY15测试通过
  - [ ] 2.1.5: 运行try_except回归测试确认无回归

- [ ] Task 2.2: 修复TE046 — try with nested with, as变量丢失
  - [ ] 2.2.1: 分析TE046字节码差异（STORE_NAME vs POP_TOP，with as变量fb丢失）
  - [ ] 2.2.2: 修复嵌套with在try body中的as变量赋值
  - [ ] 2.2.3: 验证TE046测试通过
  - [ ] 2.2.4: 运行try_except回归测试确认无回归

- [ ] Task 2.3: 修复TE080/TRY16 — 嵌套try-except输出pass
  - [ ] 2.3.1: 分析TE080/TRY16的region结构和异常表
  - [ ] 2.3.2: 修复嵌套TryExceptRegion在handler body中的识别和生成
  - [ ] 2.3.3: 验证TE080和TRY16测试通过
  - [ ] 2.3.4: 运行try_except回归测试确认无回归

- [ ] Task 2.4: 修复TE081 — try-finally中嵌套try-except结构错误
  - [ ] 2.4.1: 分析TE081字节码差异（33 vs 28）
  - [ ] 2.4.2: 修复finally块中嵌套TryExceptRegion的生成
  - [ ] 2.4.3: 验证TE081测试通过
  - [ ] 2.4.4: 运行try_except回归测试确认无回归

- [ ] Task 2.5: 修复TE100 — 三层嵌套try重复输出
  - [ ] 2.5.1: 分析TE100字节码差异（35 vs 41）
  - [ ] 2.5.2: 修复嵌套try handler body重复生成
  - [ ] 2.5.3: 验证TE100测试通过
  - [ ] 2.5.4: 运行try_except回归测试确认无回归

- [ ] Task 2.6: 修复TE104 — try-except-finally finally内容错位
  - [ ] 2.6.1: 分析TE104字节码差异（33 vs 37）
  - [ ] 2.6.2: 修复finally copy块泄漏到try body
  - [ ] 2.6.3: 验证TE104测试通过
  - [ ] 2.6.4: 运行try_except回归测试确认无回归

- [ ] Task 2.7: 修复TRY20 — 复杂try-except-for模式错误
  - [ ] 2.7.1: 分析TRY20字节码差异（81 vs 80）
  - [ ] 2.7.2: 修复条件反转、continue变pass、for-else多余return等问题
  - [ ] 2.7.3: 验证TRY20测试通过
  - [ ] 2.7.4: 运行try_except回归测试确认无回归

## Phase 3: Ternary修复 (7f)

- [ ] Task 3.1: 修复TE04 — ternary作为函数参数
  - [ ] 3.1.1: 在`_generate_ternary`或Call参数处理中检测TernaryRegion并嵌入
  - [ ] 3.1.2: 验证TE04两个测试通过
  - [ ] 3.1.3: 运行ternary回归测试确认无回归

- [ ] Task 3.2: 修复ternary11 — ternary在if条件中
  - [ ] 3.2.1: 在`_if_extract_condition_from_instructions`中添加TernaryRegion merge_ctx='compare'检测
  - [ ] 3.2.2: 提取ternary表达式并与后续COMPARE_OP组合为Compare节点
  - [ ] 3.2.3: 验证ternary11测试通过
  - [ ] 3.2.4: 运行ternary回归测试确认无回归

- [ ] Task 3.3: 修复ternary12 — ternary在while条件中
  - [ ] 3.3.1: 在while条件提取中检测TernaryRegion并嵌入
  - [ ] 3.3.2: 验证ternary12测试通过
  - [ ] 3.3.3: 运行ternary回归测试确认无回归

- [ ] Task 3.4: 修复ternary13 — ternary在for迭代器中
  - [ ] 3.4.1: 在`_loop_generate_for`中改进TernaryRegion merge_ctx='iter'查找逻辑
  - [ ] 3.4.2: 验证ternary13测试通过
  - [ ] 3.4.3: 运行ternary回归测试确认无回归

- [ ] Task 3.5: 修复ternary17 — ternary在lambda中
  - [ ] 3.5.1: 在lambda体生成中检测TernaryRegion并嵌入
  - [ ] 3.5.2: 验证ternary17测试通过
  - [ ] 3.5.3: 运行ternary回归测试确认无回归

- [ ] Task 3.6: 修复ternary20 — 复杂ternary嵌套
  - [ ] 3.6.1: 修复elif分支中ternary表达式的嵌入
  - [ ] 3.6.2: 修复`<JoinedStr>`语法错误
  - [ ] 3.6.3: 验证ternary20测试通过
  - [ ] 3.6.4: 运行ternary回归测试确认无回归

## Phase 4: 全量验证

- [ ] Task 4.1: 运行for_loop回归测试确认无回归
- [ ] Task 4.2: 运行全量10区域回归测试
- [ ] Task 4.3: 更新tasks.md/checklist.md

# Task Dependencies
- Phase 1 (Match) 和 Phase 2 (Try) 可部分并行
- Phase 3 (Ternary) 独立于 Phase 1/2，可并行
- Task 1.1 (M054/M061/M069) 和 Task 1.2 (M106) 独立
- Task 2.1 (TRY15) 独立，优先级高
- Task 2.3 (TE080/TRY16) 和 Task 2.4 (TE081) 可能共享根因
- Task 2.5 (TE100) 可能依赖 Task 2.3 的嵌套try修复
- Phase 4 依赖 Phase 1-3 全部完成
