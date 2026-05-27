# Tasks

## Phase 0: 基线确认与当前状态评估
- [ ] Task 0.1: 运行 with_region 全量测试，确认当前基线失败数和失败列表
  - [ ] 0.1.1: `pytest tests/exhaustive/with_region/ -v --tb=no 2>&1 | tail -30`
  - [ ] 0.1.2: 记录 10 个失败测试名称和错误类型
- [ ] Task 0.2: 运行其他 9 个区域测试，记录基线数据
  - [ ] 0.2.1: `pytest tests/exhaustive/basic/ -q --tb=no 2>&1 | tail -5`
  - [ ] 0.2.2: `pytest tests/exhaustive/if_region/ -q --tb=no 2>&1 | tail -5`
  - [ ] 0.2.3: `pytest tests/exhaustive/for_loop/ -q --tb=no 2>&1 | tail -5`
  - [ ] 0.2.4: `pytest tests/exhaustive/while_loop/ -q --tb=no 2>&1 | tail -5`
  - [ ] 0.2.5: `pytest tests/exhaustive/try_except/ -q --tb=no 2>&1 | tail -5`
  - [ ] 0.2.6: `pytest tests/exhaustive/match_region/ -q --tb=no 2>&1 | tail -5`
  - [ ] 0.2.7: `pytest tests/exhaustive/boolop/ -q --tb=no 2>&1 | tail -5`
  - [ ] 0.2.8: `pytest tests/exhaustive/ternary/ -q --tb=no 2>&1 | tail -5`
  - [ ] 0.2.9: `pytest tests/exhaustive/nested/ -q --tb=no 2>&1 | tail -5`
- [ ] Task 0.3: 评估当前工作区修改状态
  - [ ] 0.3.1: `git diff --stat core/cfg/region_ast_generator.py`
  - [ ] 0.3.2: 确认已有修改（_fix_try_else_in_with、TryExceptRegion 跳过逻辑等）

## Phase 1: 修复 generate() 顶层 With 异常处理 TryExceptRegion 跳过（解决当前回归）
- [ ] Task 1.1: 在 generate() 方法的 top_level_regions 循环中添加 With 异常处理 TryExceptRegion 跳过逻辑
  - [ ] 1.1.1: 分析 generate() 方法中 top_level_regions 的处理逻辑（约 L564）
  - [ ] 1.1.2: 添加检查：如果 TryExceptRegion 的所有 handler_entry_blocks 都在某个 WithRegion 的 cleanup_blocks 或 exception_blocks 中，则跳过
  - [ ] 1.1.3: 验证 w035/w043/w099/w100 不再产生 `try:...except:pass except:pass` 无效语法
- [ ] Task 1.2: 运行 with_region 全量测试验证
  - [ ] 1.2.1: 确认 w045 仍然通过
  - [ ] 1.2.2: 确认 w035/w043/w099/w100 不再回归
- [ ] Task 1.3: 运行全量回归测试
  - [ ] 1.3.1: 其他 9 个区域回归 ≤5f

## Phase 2: 修复 Pattern A — with+boolop/loop 重复 prefix 指令（w035/w043/w099/w100）
- [ ] Task 2.1: 在 _generate_with 中跳过 LoopRegion 块的重复 prefix 指令生成
  - [ ] 2.1.1: 分析 _generate_with 中 identify_block_prefix_instructions 的调用点
  - [ ] 2.1.2: 当嵌套区域是 LoopRegion 且当前块是其 blocks 成员时，跳过 prefix 指令生成（替换为 pass 或条件跳过）
  - [ ] 2.1.3: 验证 w035/w043 通过（指令数匹配）
  - [ ] 2.1.4: 验证 w099/w100 通过（指令数匹配）
- [ ] Task 2.2: 运行 with_region 全量测试验证
- [ ] Task 2.3: 运行全量回归测试（其他 9 个区域）

## Phase 3: 修复 Pattern B — with+try/except/else else 块错误（w045）
- [ ] Task 3.1: 确认 _fix_try_else_in_with 方法正确工作
  - [ ] 3.1.1: 验证 w045 在 Phase 1+2 修改后仍然通过
  - [ ] 3.1.2: 如果 w045 未通过，调试 _fix_try_else_in_with 逻辑
- [ ] Task 3.2: 运行 with_region 全量测试验证
- [ ] Task 3.3: 运行全量回归测试

## Phase 4: 修复 Pattern C — with+try 嵌套异常处理冲突（w058/w079/w080）
- [ ] Task 4.1: 分析 w058 async with 嵌套代码对象
  - [ ] 4.1.1: 运行 w058 单独测试查看错误详情
  - [ ] 4.1.2: 分析字节码差异（43 vs 37，-6 条指令）
  - [ ] 4.1.3: 设计修复方案
- [ ] Task 4.2: 分析 w079 for+with+if+break
  - [ ] 4.2.1: 运行 w079 单独测试查看错误详情
  - [ ] 4.2.2: 分析字节码差异（41 vs 32，-9 条指令）
  - [ ] 4.2.3: 设计修复方案
- [ ] Task 4.3: 分析 w080 for+with+if+continue
  - [ ] 4.3.1: 运行 w080 单独测试查看错误详情
  - [ ] 4.3.2: 分析字节码差异（38 vs 47，+9 条指令）
  - [ ] 4.3.3: 设计修复方案
- [ ] Task 4.4: 实施修复并验证
  - [ ] 4.4.1: 逐个实施修复
  - [ ] 4.4.2: 每次修复后运行 with_region + 全量回归测试

## Phase 5: 修复 Pattern D — with+loop 嵌套指令不匹配（w102）
- [ ] Task 5.1: 分析 w102 with+try/except/finally
  - [ ] 5.1.1: 运行 w102 单独测试查看错误详情
  - [ ] 5.1.2: 分析字节码差异（54 vs 59，+5 条指令）
  - [ ] 5.1.3: 确认是否为 finally 块重复生成
- [ ] Task 5.2: 实施修复并验证
  - [ ] 5.2.1: 修复 finally 块重复生成
  - [ ] 5.2.2: 运行 with_region + 全量回归测试

## Phase 6: 修复 Pattern E — with+custom context（w30withcustomctx）
- [ ] Task 6.1: 分析 w30withcustomctx
  - [ ] 6.1.1: 运行 w30withcustomctx 单独测试查看错误详情
  - [ ] 6.1.2: 分析字节码差异（35 vs 38，+3 条指令）
  - [ ] 6.1.3: 分析 class 定义块生成顺序
- [ ] Task 6.2: 实施修复并验证
  - [ ] 6.2.1: 修复 class 定义块生成顺序
  - [ ] 6.2.2: 运行 with_region + 全量回归测试

## Phase 7: 全量验证与结果汇总
- [ ] Task 7.1: 运行 with_region 全量测试确认 0f
- [ ] Task 7.2: 运行全量 10 区域回归测试
- [ ] Task 7.3: 汇总修复描述、前后测试结果、回归结果、剩余失败

# Task Dependencies
- Phase 0 必须首先完成（基线确认）
- Phase 1 依赖 Phase 0（解决当前回归是最高优先级）
- Phase 2 依赖 Phase 1（在回归解决后修复 Pattern A）
- Phase 3 依赖 Phase 1+2（确认 w045 在其他修复后仍通过）
- Phase 4-6 可部分并行（不同 with_region 测试，但共享核心文件，建议串行）
- Phase 7 依赖所有其他 Phase
