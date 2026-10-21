# Source Generated with Decompyle++ (Python version)
# File: l0_b2_for_else_in_match.pyc (Python 3.11)

__doc__ = 'AT-04: for-else 位于 match case 体内'
def b2(v):
    match v:
        case [x]:
            for i in range(x):
                print(i)
            print('else')
            return None
        case _:
            pass
