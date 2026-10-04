# Source Generated with Decompyle++ (Python version)
# File: r10_13_nonlocal_basic.pyc (Python 3.11)

__doc__ = 'r10_13: nonlocal 基础（双层闭包计数器/交换）'
def nl_counter():
    count = 0
    def bump(step):
        nonlocal count
        if step > 0:
            count += step
        else:
            count -= 1
        return count
    return bump
def nl_swap():
    a = 1
    b = 2
    def flip(do):
        nonlocal a, b
        if do:
            a, b = (b, a)
        return (a, b)
    return flip
