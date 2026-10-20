"""R5 synth family 2a: with/match alternation depth 3 + match-in-with (B93 cross-body ancestor)."""


def alt3(v):
    match v:
        case 1:
            with _B() as a:
                match a:
                    case 2:
                        with _B() as b:
                            R = (a, b)
    return 1


def miw(v):
    with _B() as a:
        match v:
            case 1:
                R = a
            case 2 if a:
                R = 2
    return 2
