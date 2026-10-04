# Source Generated with Decompyle++ (Python version)
# File: r10_14_nonlocal_deep.pyc (Python 3.11)

__doc__ = 'r10_14: nonlocal 四层闭包链 + 多名声明（深度 ≥3）'
def nl_level4(start):
    l1 = start
    def s2():
        nonlocal l1
        l1 += 1
        def s3():
            if l1 % 3 == 0:
                l1 *= 2
            def s4():
                l1 -= 5
                return l1
            return s4()
        return s3()
    return s2()
def nl_multi_names():
    x = 0
    y = 10
    z = 100
    def worker(n):
        nonlocal x, y, z
        for i in range(n):
            if i % 2:
                x += i
                continue
            if i % 3:
                y += i
                continue
            z += i
            continue
        return (x, y, z)
    return worker
