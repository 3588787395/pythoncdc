"""R9 repro_02: 空 then + else 体模式（else_stmts_check 探针副作用核心）。
缺陷: `if cond: pass else: <body>` 的 else body 丢失，因 then 为空时探针调用预标记 else 块。
区域类型: Conditional  违反原则: 2(每块唯一归属)
"""
def f(items):
    result = []
    for x in items:
        if x == 0:
            pass
        else:
            result.append(x * 2)
            result.append(x + 1)
    return result
