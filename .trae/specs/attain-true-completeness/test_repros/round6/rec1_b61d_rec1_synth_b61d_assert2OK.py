# Source Generated with Decompyle++ (Python version)
# File: rec1_b61d_rec1_synth_b61d_assert2.pyc (Python 3.11)

__doc__ = 'R5 synth family 3b: assert dispatch inside match case bodies (B61d AssertRegion dispatch).'
def a2_first(x):
    match x:
        case 1:
            assert x == 1
            return 'one'
        case _:
            assert x is not None, 'null'
            return 'other'
def a2_after_capture(x):
    match x:
        case str() as s if s:
            assert len(s) < 10
            return s
        case _:
            pass
