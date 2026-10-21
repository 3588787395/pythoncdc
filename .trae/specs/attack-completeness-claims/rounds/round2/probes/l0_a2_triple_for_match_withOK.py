# Source Generated with Decompyle++ (Python version)
# File: l0_a2_triple_for_match_with.pyc (Python 3.11)

__doc__ = 'AT-02: for x match x with —— 三元嵌套，case 体含 with + continue'
def a2(v):
    for x in v:
        match x:
            case 0 if x == 0:
                with open('f') as fh:
                    print(fh)
                pass
                continue
            case _:
                continue
    print('else')
