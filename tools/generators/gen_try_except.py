def generate(round_num):
    patterns = []
    exc_types = ['ValueError', 'TypeError', 'KeyError', 'Exception', 'RuntimeError', 'IOError']

    patterns.append('try:\n    r = 1\nexcept:\n    r = 2')
    patterns.append('try:\n    r = 1\nexcept ValueError:\n    r = 2')
    for e in exc_types[:4]:
        patterns.append(f'try:\n    r = 1\nexcept {e}:\n    r = 2')
    patterns.append('try:\n    r = 1\nexcept ValueError:\n    r = 2\nexcept TypeError:\n    r = 3')
    patterns.append('try:\n    r = 1\nexcept ValueError:\n    r = 2\nexcept:\n    r = 3')
    patterns.append('try:\n    r = 1\nexcept (ValueError, TypeError):\n    r = 2')
    patterns.append('try:\n    r = 1\nexcept ValueError as e:\n    r = 2')
    patterns.append('try:\n    r = 1\nexcept ValueError as e:\n    r = str(e)')
    patterns.append('try:\n    r = 1\nexcept:\n    r = 2\nelse:\n    r = 3')
    patterns.append('try:\n    r = 1\nexcept ValueError:\n    r = 2\nelse:\n    r = 3')
    patterns.append('try:\n    r = 1\nfinally:\n    r = 2')
    patterns.append('try:\n    r = 1\nexcept:\n    r = 2\nfinally:\n    r = 3')
    patterns.append('try:\n    r = 1\nexcept ValueError:\n    r = 2\nelse:\n    r = 3\nfinally:\n    r = 4')

    patterns.append('try:\n    try:\n        r = 1\n    except:\n        r = 2\nexcept:\n    r = 3')
    patterns.append('try:\n    r = 1\nexcept ValueError:\n    try:\n        r = 2\n    except:\n        r = 3')

    for v in ['a', 'b', 'c']:
        patterns.append(f'try:\n    r = 1\nexcept ValueError:\n    r = 2\nelse:\n    if {v}:\n        r = 3')
        patterns.append(f'try:\n    r = 1\nexcept ValueError:\n    r = 2\nelse:\n    if {v}:\n        r = 3\n    elif {v} > 0:\n        r = 4')

    patterns.append('for x in items:\n    try:\n        r = 1\n    except ValueError:\n        r = 2')
    patterns.append('while a:\n    try:\n        r = 1\n    except ValueError:\n        r = 2')
    patterns.append('try:\n    for x in items:\n        r = 1\nexcept ValueError:\n    r = 2')
    patterns.append('try:\n    while a:\n        r = 1\nexcept ValueError:\n    r = 2')

    patterns.append('try:\n    r = 1\nexcept ValueError:\n    r = 2\n    if a:\n        r = 3')
    patterns.append('try:\n    r = 1\nexcept ValueError as e:\n    if str(e):\n        r = 2\n    else:\n        r = 3')

    seen = set()
    unique = []
    for p in patterns:
        if p not in seen:
            seen.add(p)
            unique.append(p)
    return unique
