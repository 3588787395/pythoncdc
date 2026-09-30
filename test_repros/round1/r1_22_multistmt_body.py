# r1_22 or 尾臂后接多语句 if 体
# 焦点：混合链 if 体多条语句（or 尾块丢失的可见性放大）


def f(a, b, c):
    total = 0
    if a and b or c:
        total += 4
        total += 5
    return total
