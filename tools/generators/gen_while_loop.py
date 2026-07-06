def generate(round_num):
    patterns = []
    ops = ['and', 'or']
    cmp_ops = ['<', '>', '<=', '>=', '==', '!=']
    vals = ['x', 'y', 'z', 'a', 'b', 'n', '0', '1', '10', 'True', 'False']

    for v in vals[:7]:
        patterns.append(f'while {v}:\n    r = 1')
        patterns.append(f'while {v}:\n    r = 1\nelse:\n    r = 2')

    for v1 in vals[:5]:
        for v2 in vals[:5]:
            if v1 != v2:
                patterns.append(f'while {v1} {v2}:\n    r = 1')

    for v in vals[:5]:
        patterns.append(f'while {v}:\n    r = 1\n    if r > 0:\n        break')
        patterns.append(f'while {v}:\n    r = 1\n    if r > 0:\n        continue')
        patterns.append(f'while {v}:\n    r = 1\n    if r > 0:\n        break\nelse:\n    r = 2')
        patterns.append(f'while {v}:\n    r = 1\n    if r > 0:\n        continue\nelse:\n    r = 2')

    for op in ops:
        for v in vals[:4]:
            patterns.append(f'while a {op} b:\n    r = 1\n    if {v}:\n        break')
            patterns.append(f'while a {op} b:\n    r = 1\n    if {v}:\n        continue')

    for c1 in cmp_ops[:3]:
        for c2 in cmp_ops[:3]:
            patterns.append(f'while 0 {c1} x {c2} 10:\n    r = 1')
            patterns.append(f'while 0 {c1} x {c2} 10:\n    r = 1\nelse:\n    r = 2')

    patterns.append('while True:\n    r = 1\n    if r > 0:\n        break')
    patterns.append('while True:\n    r = 1\n    if r > 0:\n        break\n    r = 2')
    patterns.append('while True:\n    r = 1\n    if r > 0:\n        continue\n    r = 2')
    patterns.append('while True:\n    if a:\n        break\n    if b:\n        continue\n    r = 1')

    for v in vals[:4]:
        patterns.append(f'while {v}:\n    try:\n        r = 1\n    except:\n        r = 2')
        patterns.append(f'while {v}:\n    with open("f") as f:\n        r = 1')

    patterns.append('while a:\n    r = 1\n    while b:\n        r = 2')
    patterns.append('while a:\n    r = 1\n    while b:\n        r = 2\n        if r > 0:\n            break')
    patterns.append('while a:\n    if b:\n        break\n    if c:\n        continue\n    r = 1')
    patterns.append('while a:\n    if b:\n        break\nelse:\n    r = 2')
    patterns.append('while a:\n    if b:\n        continue\nelse:\n    r = 3')
    patterns.append('while a and b:\n    r = 1\nelse:\n    r = 2')
    patterns.append('while a or b:\n    r = 1\nelse:\n    r = 2')
    patterns.append('while 0 < x < 10:\n    r = 1\nelse:\n    r = 2')

    for v in vals[:3]:
        patterns.append(f'while {v}:\n    if a:\n        r = 1\n    elif b:\n        r = 2')
        patterns.append(f'while {v}:\n    if a:\n        r = 1\n    elif b:\n        r = 2\n    else:\n        r = 3')

    seen = set()
    unique = []
    for p in patterns:
        if p not in seen:
            seen.add(p)
            unique.append(p)
    return unique
