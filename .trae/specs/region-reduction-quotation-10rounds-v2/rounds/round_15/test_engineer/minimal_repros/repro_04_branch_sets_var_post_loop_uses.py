"""复现 04：分支内设置变量 + 后置循环使用该变量。

模式：if 分支设置 market_time 变量，后置循环遍历 market_time。
orig 中 typet 分支跳过后置循环（market_time 仅对 typet==5 有意义），
new 中所有分支都进入后置循环。
"""
def f(typet, days, mt):
    total = []
    if not typet == 5:
        if typet == 1:
            mt = {'a': 1, 'b': 2}
            for d in days:
                total.append(d)
        elif typet == 2:
            mt = ['x', 'y']
            for d in days:
                total.append(d)
    for d in days:
        for k in mt:
            total.append(d + ' ' + str(k))
    return total
