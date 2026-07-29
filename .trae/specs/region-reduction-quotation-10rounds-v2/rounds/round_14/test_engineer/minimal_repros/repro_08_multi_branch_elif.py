"""复现 08：多分支 elif 链的级联短路跳转。

模式：5 个分支的 elif 链，第一个条件短路跳转目标在归一化后应跟随到链末尾。
验证 _chase_elif_chain 能跨越多个分支到达 ceiling。
"""
def f(i, v):
    out = []
    if i == 0 and len(v) == 1:
        out.append('a')
    elif i == 0 and len(v) == 2:
        out.append('b')
    elif i == 0 and len(v) == 3:
        out.append('c')
    elif i == 0 and len(v) == 4:
        out.append('d')
    elif i == 0 and len(v) == 5:
        out.append('e')
    return out
