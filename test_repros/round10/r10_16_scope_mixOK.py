# Source Generated with Decompyle++ (Python version)
# File: r10_16_scope_mix.pyc (Python 3.11)

global MOD_TOTAL
__doc__ = 'r10_16: global + nonlocal 混合作用域（三层嵌套 + 推导式捕获自由变量）'
MOD_TOTAL = 0
def mix_global_nonlocal(base):
    acc = base
    def layer2():
        def layer3():
            global MOD_TOTAL
            if acc > 0:
                MOD_TOTAL += acc
                acc -= 1
            return (acc, MOD_TOTAL)
        return layer3()
    return layer2()
def nl_comp_over_free(limit):
    free = [limit]
    def worker():
        nonlocal free
        if limit > 0:
            free = [x * 2 for x in free if x > 1]
        return free
    return worker()
