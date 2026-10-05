# Source Generated with Decompyle++ (Python version)
# File: rv3_04_b91_class_match.pyc (Python 3.11)

_TH = 1
class MatchTrueGuard:
    val = _TH
    picked = 0
    if val == 1:
        picked = 11
    elif val:
        picked = 12
class MatchFakeGuard:
    match __name__:
        case 1 as val:
            pass
        case _:
            pass
    picked = 22
def use_both():
    return (MatchTrueGuard.picked, MatchFakeGuard.picked)
