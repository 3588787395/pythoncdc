# Source Generated with Decompyle++ (Python version)
# File: l0_e11_proj_for_match_plain.pyc (Python 3.11)

__doc__ = 'AT-02 for x match 变量分离 1/3: case 体无 continue'
def e11(v):
    for x in v:
        match x:
            case 0 if x == 0:
                print('zero')
                continue
            case _:
                print('other')
