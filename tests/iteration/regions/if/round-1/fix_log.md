# IF Region Round 1

13 bugs found (13 fixable). Awaiting fixes.

- [if-r1-0] ast_mismatch: def f(found):
    if not found:
        return None
    result = 1
    return re
- [if-r1-1] ast_mismatch: def f(x):
    if x > 10:
        return 1
    elif x > 5:
        return 2
    r
- [if-r1-2] ast_mismatch: def f(x):
    if x:
        return 1
    return 0
- [if-r1-3] ast_mismatch: def f():
    if a:
        return 1
    b = 2
    return b
- [if-r1-4] ast_mismatch: def f():
    if not ok:
        return -1
    return 0
- [if-r1-5] ast_mismatch: for i in range(10):
    if i > 5:
        pass
    else:
        continue
- [if-r1-6] ast_mismatch: for i in range(10):
    if i > 5:
        continue
    else:
        x = 1
- [if-r1-7] ast_mismatch: for i in range(10):
    if i > 5:
        x = 1
    else:
        continue
- [if-r1-8] ast_mismatch: for i in range(5):
    if i > 2:
        x = 1
    else:
        y = 2
- [if-r1-10] ast_mismatch: if 0 < a < 10 or x > 100:
    y = 1
- [if-r1-11] ast_mismatch: if a != 0 and 0 < b < 10:
    y = 1
- [if-r1-12] ast_mismatch: if not (x or y):
    z = 1
- [if-r1-13] ast_mismatch: def f(x):
    if x > 0:
        return 1
    elif x == 0:
        return 0
    r
