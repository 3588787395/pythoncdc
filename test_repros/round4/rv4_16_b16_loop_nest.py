# rv4 (REVIEW2 variant): B16 - while x match x match three layers + for containing match containing while


def while_match_match(n, xs):
    """V1: while > match > match (three layers) with break/continue bodies."""
    out = []
    i = 0
    while i < n:
        match i % 3:
            case 0:
                match xs[i % len(xs)]:
                    case "a":
                        out.append("A")
                    case _:
                        out.append("a?")
            case 1:
                out.append("B")
            case _:
                break
        i += 1
    return out


def for_match_while(n):
    """V2: for > match > while (match body contains a while loop)."""
    total = 0
    for k in range(n):
        match k % 2:
            case 0:
                j = 0
                while j < 2:
                    total += k
                    j += 1
            case _:
                continue
    return total


def while_match_continue(m):
    """V3: while > match with continue targeting the outer loop."""
    seen = []
    k = 0
    while k < m:
        k += 1
        match k % 4:
            case 1:
                continue
            case 2:
                seen.append("two")
            case 3:
                seen.append("three")
            case _:
                break
    return seen
