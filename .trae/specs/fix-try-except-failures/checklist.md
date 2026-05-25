# 修复 try_except 11个测试失败验证清单

## Task 1: te047/te083 — continue→break 误识别
- [ ] te047: `try:\n    for i in range(3):\n        if i == 1:\n            continue\n        x = i\nexcept:\n    x = 0` 反编译结果包含 `continue` 而非 `break`
- [ ] te083: `try:\n    for i in range(3):\n        if i < 1:\n            continue\nexcept:\n    y = 1` 反编译结果包含 `continue` 而非 `break`
- [ ] Task 1 回归测试: try_except 无回归

## Task 2: try20 — for-else 多余 return None
- [ ] try20: `def f():\n    try:\n        for k, v in items:\n            process(k, v)\n    except (TypeError, ValueError):\n        handle_error()` for 循环不包含 `else: return None`
- [ ] Task 2 回归测试: try_except + basic + for_loop 无回归

## Task 3: try15 — try-return except handler body
- [ ] try15: `def safe_get(d, key):\n    try:\n        return d[key]\n    except KeyError:\n        return default` try body 不含多余 `return None`，handler body 包含 `return default`
- [ ] Task 3 回归测试: try_except 无回归

## Task 4: te104 — finally copy 块泄漏
- [ ] te104: `def f():\n    try:\n        x = 1\n    except ValueError:\n        return 'val'\n    finally:\n        cleanup()` try body 不含 `cleanup(); return 'val'`，handler body 包含 `return 'val'`
- [ ] Task 4 回归测试: try_except 无回归

## Task 5: try11 — if-else→IfExp 误识别
- [ ] try11: `try:\n    if condition:\n        risky()\n    else:\n        safe()\nexcept Error:\n    handle()` try body 包含 If 语句而非 IfExp
- [ ] Task 5 回归测试: try_except 无回归

## Task 6: te050 — 内层 try-except 在 for 循环中
- [ ] te050: `try:\n    for i in range(3):\n        try:\n            x = 1 / i\n        except ZeroDivisionError:\n            x = 0\nexcept:\n    x = -1` 循环体包含嵌套 try-except，`x = 0` 仅出现在 except handler 中
- [ ] Task 6 回归测试: try_except 无回归

## Task 7: te080/te100/try16 — 多层嵌套 try 结构
- [ ] te080: `try:\n    x = 1\nexcept:\n    try:\n        y = 2\n    except:\n        z = 3` 外层 handler body 包含内层 try-except
- [ ] te100: 三层嵌套 try 每层 body 包含正确语句
- [ ] try16: `try:\n    try:\n        level2()\n    except Error2:\n        try:\n            level3_recover()\n        except Error3:\n            deep_fix()\nexcept Error1:\n    top_fix()` 无语法错误
- [ ] Task 7 回归测试: try_except 无回归

## Task 8: te081 — try-finally 内嵌套 try-except
- [ ] te081: `try:\n    x = 1\nfinally:\n    try:\n        y = 2\n    except:\n        z = 3` finalbody 包含 `try: y = 2 except: z = 3`
- [ ] Task 8 回归测试: try_except 无回归

## Task 9: 最终验证
- [ ] 完整 try_except 回归测试通过
- [ ] basic + for_loop + while_loop + if_region 回归测试通过
- [ ] 总体零回归确认
