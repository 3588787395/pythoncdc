# rv_01 修复一 A 臂（or 裸尾续接）嵌套变体 1：
# 混合链 if 嵌在 while 内层 for 体内（双层嵌套：while > for > if）
# 验收：深层产物与浅层 r1_01 同为 MATCH


def f(a, b, c, x):
    total = 0
    while x:
        for i in range(3):
            if a and b or c:
                total += 1
        total += 2
    return total
