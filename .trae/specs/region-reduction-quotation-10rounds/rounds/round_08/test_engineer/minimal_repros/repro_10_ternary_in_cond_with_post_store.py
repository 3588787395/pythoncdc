"""R8 repro_10: 三元表达式在条件上下文 + 后续 STORE 赋值丢失。
缺陷: `x = a if cond else b` 三元表达式后的独立 `y = ...` 赋值被错误并入三元归约范围而丢失。
区域类型: Ternary + Conditional  违反原则: 2(每块唯一归属)
"""
def f(start, end):
    if len(start) > 8:
        source_start = start[:8] + (start[8:] if len(start[8:]) == 4 else '0000')
        source_end = end[:8] + (end[8:] if len(end[8:]) == 4 else '1530')
        diff = set(start).difference(set(end))
        if len(diff) == 0:
            return source_start
    return source_end if 'source_end' in dir() else None
