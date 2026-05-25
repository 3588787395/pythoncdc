# Tasks

## Phase 0: 回退与基线确认
- [ ] Task 0.1: 回退 region_ast_generator.py 到已提交基线
  - [ ] 0.1.1: `git checkout core/cfg/region_ast_generator.py`
  - [ ] 0.1.2: 确认 with_region 9f, match_region 4f
- [ ] Task 0.2: 运行全量基线测试，记录各区域失败数

## Phase 1: with_region 安全修复（w035/w043/w099/w100）
- [ ] Task 1.1: 修复 with body 中 LoopRegion for_iter_setup 块的重复 prefix 指令
  - [ ] 1.1.1: 在 `_generate_with` 方法中，当嵌套区域是 LoopRegion 且当前块是其 `for_iter_setup` 块时，跳过 prefix 指令生成
  - [ ] 1.1.2: 验证 w035/w043/w099/w100 通过
  - [ ] 1.1.3: 验证 match_region 无回归（仍为 4f）
  - [ ] 1.1.4: 验证其他区域无回归

## Phase 2: match_region 安全修复（m083）
- [ ] Task 2.1: 修复 _collect_guard_pattern_blocks 的 allowed 集合
  - [ ] 2.1.1: 在 allowed 集合中添加 PUSH_NULL、PRECALL、CALL、LOAD_METHOD、BINARY_OP、CONTAINS_OP
  - [ ] 2.1.2: 验证 m083 通过
  - [ ] 2.1.3: 验证 with_region 无回归（仍为 5f，Phase 1 修复后）
  - [ ] 2.1.4: 验证 match_region 其他 3f 无回归

## Phase 3: match_region 修复（m107）
- [ ] Task 3.1: 修复 match in func return 的 POP_TOP 多余指令
  - [ ] 3.1.1: 分析 m107 的字节码差异（76 vs 74，多 2 条 POP_TOP）
  - [ ] 3.1.2: 在 `_generate_match` 中检测并过滤多余的 POP_TOP
  - [ ] 3.1.3: 验证 m107 通过
  - [ ] 3.1.4: 验证无回归

## Phase 4: match_region 修复（m106）
- [ ] Task 4.1: 修复 match guard BoolOp 的 LOAD_CONST 参数不匹配
  - [ ] 4.1.1: 分析 m106 的字节码差异（LOAD_CONST small vs None）
  - [ ] 4.1.2: 修复 guard BoolOp 表达式重建逻辑
  - [ ] 4.1.3: 验证 m106 通过
  - [ ] 4.1.4: 验证无回归

## Phase 5: with_region 修复（w079/w080）
- [ ] Task 5.1: 修复 with+if+break/continue 模式
  - [ ] 5.1.1: 在 `_if_generate_then_branch` 中检测 with __exit__ + break/continue 模式
  - [ ] 5.1.2: 当 then_stmts 为空或只有 Pass 时，检查条件块后继块中的 PRECALL+CALL+RETURN_VALUE/JUMP 模式
  - [ ] 5.1.3: 直接生成 Break/Continue AST 节点替代 __exit__ 调用
  - [ ] 5.1.4: 验证 w079/w080 通过
  - [ ] 5.1.5: 验证 match_region 无回归（关键！之前的修复导致 40f 回归）
  - [ ] 5.1.6: 验证其他区域无回归

## Phase 6: with_region 修复（w058）
- [ ] Task 6.1: 修复 async with 嵌套代码对象
  - [ ] 6.1.1: 分析 w058 字节码差异（43 vs 37，差 6 条指令）
  - [ ] 6.1.2: 修复 async with 的 as 变量赋值和后续使用
  - [ ] 6.1.3: 验证 w058 通过
  - [ ] 6.1.4: 验证无回归

## Phase 7: with_region 修复（w102）
- [ ] Task 7.1: 修复 with+try/except/finally
  - [ ] 7.1.1: 分析 w102 字节码差异（54 vs 59，多 5 条指令）
  - [ ] 7.1.2: 修复 finally 块重复生成问题
  - [ ] 7.1.3: 验证 w102 通过
  - [ ] 7.1.4: 验证无回归

## Phase 8: with_region 修复（w30withcustomctx）
- [ ] Task 8.1: 修复自定义上下文管理器
  - [ ] 8.1.1: 分析 w30withcustomctx 字节码差异（35 vs 38，多 3 条指令）
  - [ ] 8.1.2: 修复 class 定义块生成顺序
  - [ ] 8.1.3: 验证 w30withcustomctx 通过
  - [ ] 8.1.4: 验证无回归

## Phase 9: match_region 修复（m075）
- [ ] Task 9.1: 修复 match case body 中 BoolOp/If 嵌套
  - [ ] 9.1.1: 分析 m075 字节码差异（24 vs 28，多 4 条指令）
  - [ ] 9.1.2: 修复 case body 中 if 语句的展开逻辑
  - [ ] 9.1.3: 验证 m075 通过
  - [ ] 9.1.4: 验证无回归

## Phase 10: 全量验证
- [ ] Task 10.1: 运行全部 10 个区域测试
  - [ ] 10.1.1: 确认 with_region 0f
  - [ ] 10.1.2: 确认 match_region 0f
  - [ ] 10.1.3: 确认其他 8 个区域无回归
- [ ] Task 10.2: 更新 tasks.md/checklist.md

# Task Dependencies
- Phase 0 必须首先完成（回退 + 基线确认）
- Phase 1 和 Phase 2 可并行（修复不同区域，互不影响）
- Phase 3-4 依赖 Phase 2（match_region 修复需要在前一修复基础上进行）
- Phase 5 依赖 Phase 1（w079/w080 修复需要在 w035 等修复后验证）
- Phase 6-8 可并行（不同 with_region 测试）
- Phase 9 依赖 Phase 3-4（m075 修复需要在其他 match 修复后验证）
- Phase 10 依赖所有其他 Phase
