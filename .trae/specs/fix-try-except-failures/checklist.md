# 修复 try_except 测试失败验证清单

## Task 0: 回滚有回归的变更
- [ ] region_analyzer.py 中 inner_handler_indices 的 PUSH_EXC_INFO 检查已回滚
- [ ] region_analyzer.py 中 known_handler_starts 过滤逻辑已回滚
- [ ] region_analyzer.py 中 _collect_body 跳过 TryExceptRegion 块的逻辑已回滚
- [ ] region_ast_generator.py 中 _generate_try 嵌套 TryExceptRegion 检测逻辑已回滚
- [ ] 回滚后 try_except 恢复到 8f（基线状态 + te046 通过 = 7f）
- [ ] for_loop 保持 3f
- [ ] if_region 保持 0f

## Task 1: te080 — except handler 内嵌套 try-except
- [ ] te080: `try:\n    x = 1\nexcept:\n    try:\n        y = 2\n    except:\n        z = 3` 外层 handler body 包含内层 try-except
- [ ] te10/te25 无回归
- [ ] for_loop 保持 3f
- [ ] if_region 保持 0f

## Task 2: te100 — 三层嵌套 try
- [ ] te100: `try:\n    try:\n        try:\n            x = 1\n        except:\n            y = 2\n    except:\n        z = 3\nexcept:\n    w = 4` 每层 handler body 包含正确语句
- [ ] te10/te25 无回归
- [ ] for_loop 保持 3f
- [ ] if_region 保持 0f

## Task 3: try16 — 多层嵌套 try
- [ ] try16: 多层嵌套 try-except 无语法错误
- [ ] 无回归

## Task 4: te081 — try-finally 内嵌套 try-except
- [ ] te081: `try:\n    x = 1\nfinally:\n    try:\n        y = 2\n    except:\n        z = 3` finalbody 包含 `try: y = 2 except: z = 3`
- [ ] 无回归

## Task 5: te104 — finally copy 块泄漏
- [ ] te104: try body 不含 `cleanup(); return 'val'`，handler body 包含 `return 'val'`
- [ ] 无回归

## Task 6: try15 — except handler return 语句
- [ ] try15: handler body 包含 `return default` 而非 `default; return None`
- [ ] 无回归

## Task 7: try20 — 复杂 try 模式
- [ ] try20: 复杂 for-try-except-continue 模式反编译结果正确
- [ ] 无回归

## Task 8: 最终验证
- [ ] 完整 try_except 回归测试通过（0f）
- [ ] for_loop 回归测试保持 3f
- [ ] if_region 回归测试保持 0f
- [ ] basic + while_loop 无回归
