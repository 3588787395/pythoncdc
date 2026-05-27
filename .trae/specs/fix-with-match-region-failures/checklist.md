# 修复 with_region 和 match_region 测试失败 - 验证清单

## Phase 0: 回退与基线确认
- [ ] 0.1: region_ast_generator.py 已回退到已提交基线
- [ ] 0.2: with_region 基线确认为 9f
- [ ] 0.3: match_region 基线确认为 4f
- [ ] 0.4: 其他区域基线记录完成

## Phase 1: w035/w043/w099/w100 修复
- [ ] 1.1: for_iter_setup 块跳过 prefix 指令逻辑已实现
- [ ] 1.2: w035 测试通过
- [ ] 1.3: w043 测试通过
- [ ] 1.4: w099 测试通过
- [ ] 1.5: w100 测试通过
- [ ] 1.6: match_region 仍为 4f（无回归）
- [ ] 1.7: 其他区域无回归

## Phase 2: m083 修复
- [ ] 2.1: _collect_guard_pattern_blocks allowed 集合已扩展
- [ ] 2.2: m083 测试通过
- [ ] 2.3: with_region 仍为 5f（无回归）
- [ ] 2.4: match_region 其他 3f 无回归

## Phase 3: m107 修复
- [ ] 3.1: m107 多余 POP_TOP 已修复
- [ ] 3.2: m107 测试通过
- [ ] 3.3: 无回归

## Phase 4: m106 修复
- [ ] 4.1: m106 guard BoolOp 表达式重建已修复
- [ ] 4.2: m106 测试通过
- [ ] 4.3: 无回归

## Phase 5: w079/w080 修复
- [ ] 5.1: with __exit__ + break/continue 检测逻辑已实现
- [ ] 5.2: w079 测试通过（`for i in range(3): with ctx: if i > 1: break`）
- [ ] 5.3: w080 测试通过（`for i in range(3): with ctx: if i < 1: continue`）
- [ ] 5.4: match_region 无回归（关键检查点！）
- [ ] 5.5: 其他区域无回归

## Phase 6: w058 修复
- [ ] 6.1: async with 嵌套代码对象已修复
- [ ] 6.2: w058 测试通过
- [ ] 6.3: 无回归

## Phase 7: w102 修复
- [ ] 7.1: with+try/except/finally 重复生成已修复
- [ ] 7.2: w102 测试通过
- [ ] 7.3: 无回归

## Phase 8: w30withcustomctx 修复
- [ ] 8.1: 自定义上下文管理器指令顺序已修复
- [ ] 8.2: w30withcustomctx 测试通过
- [ ] 8.3: 无回归

## Phase 9: m075 修复
- [ ] 9.1: match case body BoolOp/If 嵌套已修复
- [ ] 9.2: m075 测试通过
- [ ] 9.3: 无回归

## Phase 10: 全量验证
- [ ] 10.1: with_region 0f ✅
- [ ] 10.2: match_region 0f ✅
- [ ] 10.3: basic 无回归
- [ ] 10.4: if_region 无回归
- [ ] 10.5: while_loop 无回归
- [ ] 10.6: for_loop 无回归
- [ ] 10.7: try_except 无回归
- [ ] 10.8: boolop 无回归
- [ ] 10.9: ternary 无回归
- [ ] 10.10: nested 无回归
