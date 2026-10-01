# rv_02 修复一 A 臂（or 裸尾续接）嵌套变体 2：
# 混合链 if 位于两层 if 深处的 elif 臂（if > if > elif）
# 同时覆盖修复一 C 臂（elif 纯条件块判据）的深层交互


def f(a, b, c, x):
    r = 0
    if x:
        if a:
            r = 1
        elif a and b or c:
            r = 2
        else:
            r = 3
    return r
