# r4_07 attack: capture patterns (case x) and wildcard (_)


def match_capture_bare(x):
    """Attack 1: bare capture pattern catches everything."""
    match x:
        case val:
            return ("captured", val)


def match_capture_after_cases(x):
    """Attack 2: capture as tail case after value cases."""
    match x:
        case 0:
            return "zero"
        case 1:
            return "one"
        case other:
            return ("fallback", other)


def match_wildcard_tail(x):
    """Attack 3: wildcard _ as tail default."""
    match x:
        case 10:
            return "ten"
        case 20:
            return "twenty"
        case _:
            return "many"


def match_wildcard_inside(seq):
    """Attack 4: wildcard inside sequence pattern."""
    match seq:
        case [_, second]:
            return ("second", second)
        case [only]:
            return ("only", only)
        case _:
            return "len-other"


def match_capture_in_mapping(d):
    """Attack 5: capture inside mapping + bare capture tail."""
    match d:
        case {"k": v}:
            return ("k", v)
        case {}:
            return "empty-map"
        case whatever:
            return ("notmap", whatever)
