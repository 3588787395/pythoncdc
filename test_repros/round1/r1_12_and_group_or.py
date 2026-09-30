# r1_12 and 组内嵌 or（if a and (b or c)）
# 焦点：B1a 嫁接路径的 ck==1 链首续接分支（组首 and + 内层 or）


def f(a, b, c):
    total = 0
    if a and (b or c):
        total += 4
    return total
