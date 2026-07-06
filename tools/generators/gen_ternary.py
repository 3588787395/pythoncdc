def generate(round_num):
    patterns = []
    vals = ['x', 'y', 'z', 'a', 'b', 'c', '0', '1', '10', 'True', 'False', 'None']

    for v1 in vals[:6]:
        for v2 in vals[:6]:
            for v3 in vals[:6]:
                if v1 != v2 and v2 != v3:
                    patterns.append(f'r = {v1} if {v2} else {v3}')

    patterns.append('r = a if b else c if d else e')
    patterns.append('r = a if b else (c if d else e)')
    patterns.append('r = (a if b else c) if d else e')

    for v in vals[:4]:
        patterns.append(f'if a:\n    r = {v} if b else c')
        patterns.append(f'r = a if {v} else b\nif r:\n    r = 1')
        patterns.append(f'if {v} if a else b:\n    r = 1')

    patterns.append('r = 1 if a and b else 2')
    patterns.append('r = 1 if a or b else 2')
    patterns.append('r = 1 if 0 < a < 10 else 2')
    patterns.append('r = 1 if (a and b) or c else 2')
    patterns.append('r = 1 if a and (b or c) else 2')
    patterns.append('r = a if b else c if d else e if f else g')

    for v in vals[:3]:
        patterns.append(f'r = {v} if a else b\nr2 = {v} if c else d')
        patterns.append(f'if a:\n    r = {v} if b else c\nelif d:\n    r = {v} if e else f')
        patterns.append(f'if a and b:\n    r = {v} if c else d\nelif e:\n    r = {v} if f else g')

    patterns.append('while a:\n    r = x if b else y')
    patterns.append('for v in items:\n    r = x if a else y')
    patterns.append('try:\n    r = x if a else y\nexcept:\n    r = 2')
    patterns.append('with open("f") as f:\n    r = x if a else y')

    patterns.append('match x:\n    case 1:\n        r = a if b else c\n    case _:\n        r = 2')
    patterns.append('r = a if b > 0 else c')
    patterns.append('r = a if b == 0 else c')
    patterns.append('r = a if not b else c')
    patterns.append('r = a if b is None else c')
    patterns.append('r = a if b is not None else c')
    patterns.append('r = a if b in items else c')
    patterns.append('r = a if b not in items else c')

    seen = set()
    unique = []
    for p in patterns:
        if p not in seen:
            seen.add(p)
            unique.append(p)
    return unique
