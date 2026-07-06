def generate(round_num):
    patterns = []

    patterns.append('match x:\n    case 1:\n        r = 1')
    patterns.append('match x:\n    case 1:\n        r = 1\n    case 2:\n        r = 2')
    patterns.append('match x:\n    case 1:\n        r = 1\n    case _:\n        r = 2')
    patterns.append('match x:\n    case 1:\n        r = 1\n    case 2:\n        r = 2\n    case _:\n        r = 3')
    patterns.append('match x:\n    case 1 | 2:\n        r = 1')
    patterns.append('match x:\n    case 1 | 2:\n        r = 1\n    case _:\n        r = 2')

    patterns.append('match x:\n    case n if n > 0:\n        r = 1\n    case _:\n        r = 2')
    patterns.append('match x:\n    case n if n > 0:\n        r = 1\n    case n if n < 0:\n        r = 2\n    case _:\n        r = 3')
    patterns.append('match x:\n    case n if a and b:\n        r = 1\n    case _:\n        r = 2')
    patterns.append('match x:\n    case n if a or b:\n        r = 1\n    case _:\n        r = 2')

    patterns.append('match x:\n    case [1, 2]:\n        r = 1\n    case _:\n        r = 2')
    patterns.append('match x:\n    case [a, b]:\n        r = 1\n    case _:\n        r = 2')
    patterns.append('match x:\n    case [a, *rest]:\n        r = 1\n    case _:\n        r = 2')
    patterns.append('match x:\n    case [a, b, *rest]:\n        r = 1\n    case _:\n        r = 2')
    patterns.append('match x:\n    case []:\n        r = 1\n    case [a]:\n        r = 2\n    case _:\n        r = 3')

    patterns.append('match x:\n    case {"key": v}:\n        r = 1\n    case _:\n        r = 2')
    patterns.append('match x:\n    case {"a": v1, "b": v2}:\n        r = 1\n    case _:\n        r = 2')
    patterns.append('match x:\n    case {"key": v, **rest}:\n        r = 1\n    case _:\n        r = 2')

    patterns.append('match x:\n    case int():\n        r = 1\n    case str():\n        r = 2\n    case _:\n        r = 3')
    patterns.append('match x:\n    case int(n):\n        r = 1\n    case str(s):\n        r = 2\n    case _:\n        r = 3')

    patterns.append('match x:\n    case Point(x=1):\n        r = 1\n    case _:\n        r = 2')
    patterns.append('match x:\n    case Point(x=a, y=b):\n        r = 1\n    case _:\n        r = 2')

    patterns.append('for v in items:\n    match v:\n        case 1:\n            r = 1\n        case _:\n            r = 2')
    patterns.append('while a:\n    match x:\n        case 1:\n            r = 1\n        case _:\n            r = 2')
    patterns.append('try:\n    match x:\n        case 1:\n            r = 1\n        case _:\n            r = 2\nexcept:\n    r = 3')
    patterns.append('with open("f") as f:\n    match x:\n        case 1:\n            r = 1\n        case _:\n            r = 2')

    patterns.append('match x:\n    case 1:\n        if a:\n            r = 1\n        else:\n            r = 2\n    case _:\n        r = 3')
    patterns.append('match x:\n    case 1:\n        if a and b:\n            r = 1\n        elif c:\n            r = 2\n    case _:\n        r = 3')

    seen = set()
    unique = []
    for p in patterns:
        if p not in seen:
            seen.add(p)
            unique.append(p)
    return unique
