# r2_16 handler 类型为复杂表达式（属性链/调用/下标）
# 焦点：except <complex-expr> 的类型表达式重建


def f(exc, mod, table):
    out = []
    try:
        out.append(mod.value[0])
    except mod.errors.MyError(table["code"]):
        out.append("custom")
    except mod.registry[(1, 2)]:
        out.append("sub")
    return out


def g(mod, name):
    try:
        return mod.handlers[name[0]]()
    except mod.registry.make(name[1]):
        return None
    except mod.base.TestErr:
        return "direct"
