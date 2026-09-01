"""复现 10：多分支 if/elif 链 + 后置循环（5 分支，最接近 build_future_fill_time 结构）。

模式：if/elif 链含 typet==1/2/3/4/13 五个分支，每个分支有自有循环，
链末尾有后置循环。orig 中 typet 分支 JUMP_FORWARD 跳到后置循环之后，
new 中跳到后置循环开头。
对应 build_future_fill_time 完整结构的最小复现。
"""
def f(typet, days, t1, t2, mt):
    total = []
    if not typet == 5:
        if typet == 1:
            for d in days:
                for it in t1:
                    total.append(d + it)
        elif typet == 2:
            for d in days:
                for it in t2:
                    total.append(d + it)
        elif typet == 3:
            for d in days:
                for it in t1:
                    total.append(d + it)
        elif typet == 4:
            for d in days:
                for it in mt:
                    total.append(d + it)
        elif typet == 13:
            for d in days:
                for it in mt:
                    total.append(d + it)
    elif typet == 5:
        mt = ['a', 'b']
    for d in days:
        for it in mt:
            total.append(d + ' ' + it)
    return total
