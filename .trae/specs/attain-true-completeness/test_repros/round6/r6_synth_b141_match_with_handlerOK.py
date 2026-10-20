# Source Generated with Decompyle++ (Python version)
# File: r6_synth_b141_match_with_handler.pyc (Python 3.11)

class _Ctx:
    def __enter__(self):
        return self
    def __exit__(self, *a):
        return False
def s_b141_match_in_with_handler(e):
    try:
        X = 1
    except (TypeError, KeyError) as e:
        with _Ctx():
            match e:
                case TypeError():
                    R = 't'
                case _:
                    R = 'o'
    return R
def s_b141_match_in_with_plain(e):
    with _Ctx():
        match e:
            case TypeError():
                R = 't'
            case _:
                R = 'o'
    return R
def s_b141_match_in_with_nested(e):
    try:
        X = 1
    except ValueError as e:
        with _Ctx():
            match e:
                case int():
                    R = 1
                case str():
                    R = 2
                case _:
                    R = 3
    return R
