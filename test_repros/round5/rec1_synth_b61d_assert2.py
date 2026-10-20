"""R5 synth family 3b: assert dispatch inside match case bodies (B61d AssertRegion dispatch)."""


def a2_first(x):
    match x:
        case 1:
            assert x == 1
            return 'one'
        case _:
            assert x is not None, "null"
            return 'other'


def a2_after_capture(x):
    match x:
        case str() as s if s:
            assert len(s) < 10
            return s
        case _:
            return None
