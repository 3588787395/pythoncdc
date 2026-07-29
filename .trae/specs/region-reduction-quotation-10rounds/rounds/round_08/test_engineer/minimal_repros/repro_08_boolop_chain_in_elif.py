"""R8 repro_08: BoolOp 链在 elif 上下文条件丢失。
缺陷: `elif a == 1 or a == 2 or a == 3:` 形式的 BoolOp 链在 elif 上下文中部分条件丢失。
区域类型: BoolOp  违反原则: 4(入口引用语义)
"""
def f(a, b):
    if a == 0:
        return b
    elif a == 1 or a == 2 or a == 3 or a == 4 or a == 5 or a == 13:
        b = b + 1
        return b
    elif a == 6:
        b = b + 2
        return b
    return b
