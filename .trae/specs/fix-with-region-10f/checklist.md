# 修复 with_region 10 个测试失败 - 验证清单

## Phase 0: 基线确认与当前状态评估
- [ ] 0.1: with_region 当前失败数和失败列表已记录
- [ ] 0.2: 其他 9 个区域基线数据已记录
- [ ] 0.3: 当前工作区修改状态已评估

## Phase 1: generate() 顶层 With 异常处理 TryExceptRegion 跳过
- [ ] 1.1: generate() 中 top_level_regions 循环已添加 With 异常处理 TryExceptRegion 跳过逻辑
- [ ] 1.2: w035/w043/w099/w100 不再产生 `try:...except:pass except:pass` 无效语法
- [ ] 1.3: w045 仍然通过
- [ ] 1.4: 全量回归测试 ≤5f

## Phase 2: Pattern A — with+boolop/loop 重复 prefix 指令（w035/w043/w099/w100）
- [ ] 2.1: _generate_with 中 LoopRegion 块的 prefix 指令跳过逻辑已实现
- [ ] 2.2: w035 测试通过（42vs42 指令匹配）
- [ ] 2.3: w043 测试通过（42vs42 指令匹配）
- [ ] 2.4: w099 测试通过（37vs37 指令匹配）
- [ ] 2.5: w100 测试通过（39vs39 指令匹配）
- [ ] 2.6: with_region 全量测试通过
- [ ] 2.7: 全量回归测试 ≤5f

## Phase 3: Pattern B — with+try/except/else else 块错误（w045）
- [ ] 3.1: _fix_try_else_in_with 方法正确工作
- [ ] 3.2: w045 测试通过（PUSH_NULL vs PUSH_EXC_INFO 已解决）
- [ ] 3.3: with_region 全量测试通过
- [ ] 3.4: 全量回归测试 ≤5f

## Phase 4: Pattern C — with+try 嵌套异常处理冲突（w058/w079/w080）
- [ ] 4.1: w058 字节码差异分析完成（43vs37, -6 指令）
- [ ] 4.2: w079 字节码差异分析完成（41vs32, -9 指令）
- [ ] 4.3: w080 字节码差异分析完成（38vs47, +9 指令）
- [ ] 4.4: w058 修复已实施并验证通过
- [ ] 4.5: w079 修复已实施并验证通过
- [ ] 4.6: w080 修复已实施并验证通过
- [ ] 4.7: with_region 全量测试通过
- [ ] 4.8: 全量回归测试 ≤5f

## Phase 5: Pattern D — with+loop 嵌套指令不匹配（w102）
- [ ] 5.1: w102 字节码差异分析完成（54vs59, +5 指令）
- [ ] 5.2: w102 finally 块重复生成问题已修复
- [ ] 5.3: w102 测试通过
- [ ] 5.4: with_region 全量测试通过
- [ ] 5.5: 全量回归测试 ≤5f

## Phase 6: Pattern E — with+custom context（w30withcustomctx）
- [ ] 6.1: w30withcustomctx 字节码差异分析完成（35vs38, +3 指令）
- [ ] 6.2: class 定义块生成顺序已修复
- [ ] 6.3: w30withcustomctx 测试通过
- [ ] 6.4: with_region 全量测试通过
- [ ] 6.5: 全量回归测试 ≤5f

## Phase 7: 全量验证与结果汇总
- [ ] 7.1: with_region 0f ✅
- [ ] 7.2: 全量 10 区域回归测试完成
- [ ] 7.3: 修复描述、前后测试结果、回归结果、剩余失败已汇总
