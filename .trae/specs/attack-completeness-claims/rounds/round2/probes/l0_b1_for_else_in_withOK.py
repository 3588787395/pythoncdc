# Source Generated with Decompyle++ (Python version)
# File: l0_b1_for_else_in_with.pyc (Python 3.11)

__doc__ = 'AT-04: for-else 位于 with 体内（守卫只列 TryExceptRegion 的子集检验）'
def b1(xs):
    with open('f') as fh:
        for x in xs:
            print(x)
        print('for-else')
    return fh
