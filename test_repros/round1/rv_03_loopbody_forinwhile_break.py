# rv_03 修复一 B/B2 臂（循环体内层 if 链装配豁免）嵌套变体 1：
# 内层 if 混合链带 break，位于 while 内层 for 体内（for > while > if）
# 豁免判据与循环体 body_blocks 认领的深层交互


def f(items, a, b, c):
    out = []
    for it in items:
        while it:
            if a and b or c:
                break
            it -= 1
        out.append(it)
    return out
