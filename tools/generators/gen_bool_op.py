def generate(round_num):
    patterns = []
    ops = ['and', 'or']
    cmp_ops = ['<', '>', '<=', '>=', '==', '!=']
    vals = ['x', 'y', 'z', 'a', 'b', 'c', '0', '1', '10', 'True', 'False', 'None']

    for op in ops:
        for v1 in vals[:6]:
            for v2 in vals[:6]:
                if v1 != v2:
                    patterns.append(f'if {v1} {op} {v2}:\n    r = 1')
                    patterns.append(f'if {v1} {op} {v2}:\n    r = 1\nelse:\n    r = 2')
                    patterns.append(f'if {v1} {op} {v2}:\n    r = 1\nelif z:\n    r = 2')
                    patterns.append(f'if {v1} {op} {v2}:\n    r = 1\nelif z:\n    r = 2\nelse:\n    r = 3')
                    patterns.append(f'r = 1 if {v1} {op} {v2} else 2')

    for c1 in cmp_ops[:4]:
        for c2 in cmp_ops[:4]:
            for v in vals[:4]:
                patterns.append(f'if 0 {c1} {v} {c2} 10:\n    r = 1')
                patterns.append(f'if 0 {c1} {v} {c2} 10:\n    r = 1\nelse:\n    r = 2')
                patterns.append(f'if 0 {c1} {v} {c2} 10:\n    r = 1\nelif z:\n    r = 2')
                for op in ops:
                    for v2 in vals[:4]:
                        patterns.append(f'if 0 {c1} {v} {c2} 10 {op} {v2} > 0:\n    r = 1')
                        patterns.append(f'if 0 {c1} {v} {c2} 10 {op} {v2} > 0:\n    r = 1\nelif z:\n    r = 2')

    patterns.append('if a and b and c:\n    r = 1')
    patterns.append('if a or b or c:\n    r = 1')
    patterns.append('if a and b or c:\n    r = 1')
    patterns.append('if a or b and c:\n    r = 1')
    patterns.append('if (a and b) or c:\n    r = 1')
    patterns.append('if a and (b or c):\n    r = 1')

    for op in ops:
        patterns.append(f'while a {op} b:\n    r = 1')
        patterns.append(f'while a {op} b:\n    r = 1\nelse:\n    r = 2')
        patterns.append(f'r = a if b {op} c else d')
        patterns.append(f'if a {op} b:\n    r = 1\nelse:\n    r = a if c else d')

    patterns.append('if a and b:\n    r = 1\nelif c and d:\n    r = 2\nelse:\n    r = 3')
    patterns.append('if a or b:\n    r = 1\nelif c or d:\n    r = 2\nelse:\n    r = 3')
    patterns.append('if a and b:\n    r = 1\nelif c or d:\n    r = 2')
    patterns.append('if a or b:\n    r = 1\nelif c and d:\n    r = 2')

    patterns.append('if not (a and b):\n    r = 1')
    patterns.append('if not (a or b):\n    r = 1')
    patterns.append('if not a and b:\n    r = 1')
    patterns.append('if not a or b:\n    r = 1')

    seen = set()
    unique = []
    for p in patterns:
        if p not in seen:
            seen.add(p)
            unique.append(p)
    return unique
