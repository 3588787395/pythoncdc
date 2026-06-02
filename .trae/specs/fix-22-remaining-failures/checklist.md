# 修复22个反编译测试失败 - 验证清单

## Phase 1: Match Region修复

### Task 1.1: M054/M061/M069 try在match case body中
- [ ] M054: `match x: case 1: try: y=1 except: z=2` 反编译try body不为pass
- [ ] M061: `match x: case 1: try: y=risky() except: y=0` 反编译try body不为pass
- [ ] M069: `match x: case 1: try: x=risky() except ValueError: x=0 except TypeError: x=-1` 反编译try body不为pass
- [ ] match_region回归测试无回归

### Task 1.2: M106 match guard with BoolOp
- [ ] M106: `case n if n > 0 and n < 100: return "small"` case body包含return语句
- [ ] match_region回归测试无回归

### Task 1.3: M083 guard表达式不泄漏
- [ ] M083: `case list() as lst if len(lst) > 0:` body中不出现`len(lst) > 0`独立语句
- [ ] match_region回归测试无回归

### Task 1.4: M107 mapping pattern with guard
- [ ] M107: `case {"type": "user", "name": name} if len(name) > 0:` 结构正确
- [ ] match_region回归测试无回归

### Task 1.5: M075 BoolOp在case body中
- [ ] M075: `case 1: if a and b: y=1` 不被拆为嵌套if
- [ ] match_region回归测试无回归

## Phase 2: Try-except修复

### Task 2.1: TRY15 handler return
- [ ] TRY15: `except KeyError: return default` 输出`return default`而非`default; return`
- [ ] try_except回归测试无回归

### Task 2.2: TE046 try with nested with
- [ ] TE046: `with open('a') as fa: with open('b') as fb: x = fa.read() + fb.read()` as变量fb不丢失
- [ ] try_except回归测试无回归

### Task 2.3: TE080/TRY16 嵌套try-except
- [ ] TE080: `try: x=1 except: try: y=2 except: z=3` 输出完整嵌套结构
- [ ] TRY16: 多层嵌套try-except输出完整结构
- [ ] try_except回归测试无回归

### Task 2.4: TE081 try-finally嵌套try-except
- [ ] TE081: `try: x=1 finally: try: y=2 except: z=3` finally块包含try-except
- [ ] try_except回归测试无回归

### Task 2.5: TE100 三层嵌套try
- [ ] TE100: 三层嵌套try每层handler body正确，不重复
- [ ] try_except回归测试无回归

### Task 2.6: TE104 try-except-finally
- [ ] TE104: try body不含cleanup()和return 'val'，handler body包含return 'val'
- [ ] try_except回归测试无回归

### Task 2.7: TRY20 复杂try模式
- [ ] TRY20: 条件不反转，continue正确，for-else无多余return
- [ ] try_except回归测试无回归

## Phase 3: Ternary修复

### Task 3.1: TE04 ternary作为函数参数
- [ ] TE04_a: `print("max" if a > b else "min", a if a > 0 else b)` ternary嵌入Call参数
- [ ] TE04_n: 同上（不同变量名版本）
- [ ] ternary回归测试无回归

### Task 3.2: ternary11 ternary在if条件中
- [ ] ternary11: `if (a if c else b) > threshold: process()` ternary嵌入if条件
- [ ] ternary回归测试无回归

### Task 3.3: ternary12 ternary在while条件中
- [ ] ternary12: `while (next_item() if has_more() else None): pass` ternary嵌入while条件
- [ ] ternary回归测试无回归

### Task 3.4: ternary13 ternary在for迭代器中
- [ ] ternary13: `for x in (list_a if use_a else list_b): pass` ternary嵌入for iter
- [ ] ternary回归测试无回归

### Task 3.5: ternary17 ternary在lambda中
- [ ] ternary17: `f = lambda x: (process(x) if valid(x) else None)` lambda体为ternary
- [ ] ternary回归测试无回归

### Task 3.6: ternary20 复杂ternary嵌套
- [ ] ternary20: elif分支中ternary嵌入return语句
- [ ] ternary回归测试无回归

## Phase 4: 全量验证

- [ ] for_loop回归测试: 失败数不超过基线(3f)
- [ ] 全量10区域回归测试: 总失败数不超过基线+5
- [ ] try_except: 0f (从8f修复)
- [ ] ternary: 0f (从7f修复)
- [ ] match_region: 0f (从7f修复)
