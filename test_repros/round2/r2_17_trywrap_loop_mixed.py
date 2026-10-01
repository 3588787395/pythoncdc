# r2_17 try 包裹外层循环 + 内层混合链（B7 交互在 try 新语料下的延伸）
# 焦点：B7（外层循环包裹混合链装配降级）× try 所有权交叠


def f(a, b, c, out):
    for i in range(3):
        try:
            if a and b or c:
                out.append(i)
                break
            while a or b and c:
                out.append(i * 2)
                break
        except TypeError:
            out.append("e")
    return out


def g(a, b, c, out):
    while a:
        try:
            if a and b or c:
                out.append(1)
                break
        except TypeError:
            out.append("e")
        a = False
    return out
