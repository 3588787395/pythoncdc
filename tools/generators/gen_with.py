def generate(round_num):
    patterns = []

    patterns.append('with open("f") as f:\n    r = 1')
    patterns.append('with open("f") as f:\n    r = f.read()')
    patterns.append('with open("a") as a, open("b") as b:\n    r = 1')
    patterns.append('with open("f") as f:\n    r = 1\n    r = 2')
    patterns.append('with open("f"):\n    r = 1')

    patterns.append('with open("f") as f:\n    if a:\n        r = 1\n    else:\n        r = 2')
    patterns.append('with open("f") as f:\n    if a:\n        r = 1\n    elif b:\n        r = 2')
    patterns.append('with open("f") as f:\n    if a and b:\n        r = 1\n    elif c:\n        r = 2')

    patterns.append('try:\n    with open("f") as f:\n        r = 1\nexcept:\n    r = 2')
    patterns.append('with open("f") as f:\n    try:\n        r = 1\n    except:\n        r = 2')

    patterns.append('for x in items:\n    with open("f") as f:\n        r = 1')
    patterns.append('with open("f") as f:\n    for x in items:\n        r = 1')

    patterns.append('while a:\n    with open("f") as f:\n        r = 1')
    patterns.append('with open("f") as f:\n    while a:\n        r = 1')

    patterns.append('with open("f") as f:\n    match x:\n        case 1:\n            r = 1\n        case _:\n            r = 2')

    patterns.append('with open("a") as a:\n    with open("b") as b:\n        r = 1')

    patterns.append('with open("f") as f:\n    r = 1 if a else 2')
    patterns.append('with open("f") as f:\n    r = a if b else c\n    if r:\n        r = 2')

    seen = set()
    unique = []
    for p in patterns:
        if p not in seen:
            seen.add(p)
            unique.append(p)
    return unique
