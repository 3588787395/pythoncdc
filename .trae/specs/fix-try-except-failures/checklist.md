# 修复 try_except 测试失败验证清单

## Task 5: te104 — finally copy 块泄漏
- [ ] te104 反编译输出为 `def f():\n    try:\n        x = 1\n    except ValueError:\n        return 'val'\n    finally:\n        cleanup()`
- [ ] try body 不含 `cleanup()` 和 `return 'val'`
- [ ] 全量回归测试总失败数不超过25f
- [ ] try_except 失败数不超过2f

## Task 6: try20 — 复杂 try 模式
- [ ] try body 包含 `if not result: continue`（条件不反转，continue 不丢失）
- [ ] except TypeError handler 包含 `continue`
- [ ] except ValueError handler 包含 `raise`
- [ ] for-else 包含 `return 'all processed'`
- [ ] 字节码指令数匹配（81 vs 81）
- [ ] 全量回归测试总失败数不超过25f
- [ ] try_except 失败数不超过2f

## Task 7: 最终验证
- [ ] 完整 try_except 回归测试通过（0f）
- [ ] 全量回归测试总失败数不超过25f
- [ ] try_except 失败数从原始8f减少到0f
