# rv3_07: B89 trim 守卫的过度修剪风险攻击——三元赋值后跟完整 if/比较语句
# 完整用户语句（赋值/if/return）必须全部存活，条件链归属下一区域不得吞并合法语句
def ternary_then_if(c, d):
    r = 1 if c else 2
    if d:
        r = r + 10
    else:
        r = r - 10
    return r


def ternary_then_cmp(c, d):
    r = 'big' if c else 'small'
    flag = d > 3
    return r, flag


def ternary_chain_then_while(c, d):
    a = 1 if c else (2 and 3)
    b = (4 or 5) and 6 if d else 7
    n = 0
    while n < b:
        n = n + 1
    return a, n
