# r4_01 attack: match value patterns (literal cases, int/str mixed multi-case)


def match_value_single(x):
    """Attack 1: single int value case."""
    match x:
        case 1:
            return "one"
        case _:
            return "other"


def match_value_mixed_types(x):
    """Attack 2: int/str mixed multi-case values."""
    match x:
        case 1:
            return "int-one"
        case "hello":
            return "str-hello"
        case 3.5:
            return "float"
        case None:
            return "none-val"
        case _:
            return "miss"


def match_value_int_str_mixed(x):
    """Attack 3: interleaved int/str cases with a capture tail."""
    match x:
        case "a":
            return 1
        case 10:
            return 2
        case "b":
            return 3
        case other:
            return (other, 0)


def match_value_expr_body(x):
    """Attack 4: value cases with non-trivial bodies (loop + assignment)."""
    acc = []
    match x:
        case 1:
            for i in range(3):
                acc.append(i * 2)
        case 2:
            acc = [x, x + 1]
        case _:
            acc.append(-1)
    return acc


def match_value_subject_tuple(x, y):
    """Attack 5: match on tuple subject with value cases."""
    match (x, y):
        case (0, 0):
            return "origin"
        case (0, _):
            return "y-axis"
        case (_, 0):
            return "x-axis"
        case _:
            return "plane"
