def generate(round_num):
    patterns = []
    vals = ['x', 'y', 'z', 'a', 'b', 'n']

    for v in vals:
        patterns.append(f'for {v} in items:\n    r = 1')
        patterns.append(f'for {v} in items:\n    r = 1\nelse:\n    r = 2')
        patterns.append(f'for {v} in items:\n    r = 1\n    if r > 0:\n        break')
        patterns.append(f'for {v} in items:\n    r = 1\n    if r > 0:\n        break\nelse:\n    r = 2')
        patterns.append(f'for {v} in items:\n    r = 1\n    if r > 0:\n        continue')
        patterns.append(f'for {v} in items:\n    r = 1\n    if r > 0:\n        continue\nelse:\n    r = 2')

    for v1 in vals[:3]:
        for v2 in vals[:3]:
            if v1 != v2:
                patterns.append(f'for {v1} in items:\n    for {v2} in items:\n        r = 1')

    patterns.append('for i in range(10):\n    r = i')
    patterns.append('for i in range(10):\n    r = i\nelse:\n    r = -1')
    patterns.append('for i in range(10):\n    if i > 5:\n        break\n    r = i')
    patterns.append('for i in range(10):\n    if i > 5:\n        break\nelse:\n    r = -1')
    patterns.append('for i in range(10):\n    if i > 5:\n        continue\n    r = i')
    patterns.append('for i in range(10):\n    if i > 5:\n        continue\nelse:\n    r = -1')

    for v in vals[:3]:
        patterns.append(f'for {v} in items:\n    try:\n        r = 1\n    except:\n        r = 2')
        patterns.append(f'for {v} in items:\n    if a:\n        r = 1\n    elif b:\n        r = 2')

    patterns.append('for x in items:\n    match x:\n        case 1:\n            r = 1\n        case _:\n            r = 2')
    patterns.append('for x in items:\n    if a:\n        break\n    elif b:\n        continue\n    r = 1')
    patterns.append('for x in items:\n    if a:\n        break\n    elif b:\n        break\nelse:\n    r = 2')
    patterns.append('for x in items:\n    with open("f") as f:\n        r = 1')
    patterns.append('for x in items:\n    if a and b:\n        r = 1\n    elif c or d:\n        r = 2')

    seen = set()
    unique = []
    for p in patterns:
        if p not in seen:
            seen.add(p)
            unique.append(p)
    return unique
