import itertools
import textwrap
import random

EXPR_VARS = ['x', 'y', 'z', 'w', 'a', 'b', 'c', 'n', 'm', 'flag']
EXPR_VALS = ['0', '1', '2', '3', '10', '42', '-1', "'a'", "'b'", "True", "False", "None"]
SIMPLE_STMTS = [
    'pass',
    'x = 1',
    'y = 2',
    'z = x + 1',
    'w = 0',
    'result = True',
    'count = 0',
    'value = None',
    'print(x)',
    'print(y)',
]
STMT_VARS = ['x', 'y', 'z', 'w', 'result', 'count', 'value', 'total', 'flag', 'n']


def _pick(lst, rng=None):
    if rng is None:
        rng = random.Random()
    return rng.choice(lst)


def _pick_n(lst, n, rng=None):
    if rng is None:
        rng = random.Random()
    return rng.choices(lst, k=n)


def _indent(text, levels=1):
    prefix = '    ' * levels
    return '\n'.join(prefix + line for line in text.split('\n'))


def _simple_expr(rng):
    t = rng.randint(0, 3)
    if t == 0:
        return _pick(EXPR_VARS, rng)
    elif t == 1:
        return _pick(EXPR_VALS, rng)
    elif t == 2:
        return f'{_pick(EXPR_VARS, rng)} > {_pick(EXPR_VALS, rng)}'
    else:
        return f'{_pick(EXPR_VARS, rng)} == {_pick(EXPR_VALS, rng)}'


def _simple_stmt(rng):
    return _pick(SIMPLE_STMTS, rng)


def _stmt_seq(rng, n=None):
    if n is None:
        n = rng.randint(1, 3)
    stmts = []
    used_vars = set()
    for _ in range(n):
        s = _simple_stmt(rng)
        stmts.append(s)
    return '\n'.join(stmts)


# ============================================================
# Pattern generators per region type
# ============================================================

def gen_if_patterns(rng=None, count=50):
    if rng is None:
        rng = random.Random(42)
    patterns = []

    # Basic if-then
    for var in EXPR_VARS[:5]:
        for val in EXPR_VALS[:5]:
            patterns.append(f'if {var}:\n    y = {val}')

    # if-else
    for var in EXPR_VARS[:5]:
        patterns.append(f'if {var}:\n    y = 1\nelse:\n    y = 2')

    # if-elif
    patterns.append('if x > 0:\n    y = 1\nelif x < 0:\n    y = -1')
    patterns.append('if x == 1:\n    y = 1\nelif x == 2:\n    y = 2')

    # if-elif-else
    patterns.append('if x > 0:\n    y = 1\nelif x < 0:\n    y = -1\nelse:\n    y = 0')
    patterns.append('if x == 1:\n    y = 1\nelif x == 2:\n    y = 2\nelse:\n    y = 0')

    # Multi-elif
    patterns.append('if x == 1:\n    y = 1\nelif x == 2:\n    y = 2\nelif x == 3:\n    y = 3\nelse:\n    y = 0')

    # Nested if
    patterns.append('if x:\n    if y:\n        z = 1')
    patterns.append('if x:\n    if y:\n        z = 1\n    else:\n        z = 2')
    patterns.append('if x:\n    if y:\n        z = 1\n    else:\n        z = 2\nelse:\n    z = 3')

    # if with multi-statement body
    patterns.append('if x:\n    y = 1\n    z = 2')
    patterns.append('if x:\n    y = 1\n    z = 2\nelse:\n    y = 3\n    z = 4')

    # if with return (in function)
    patterns.append('def f():\n    if x:\n        return 1\n    return 0')
    patterns.append('def f():\n    if x:\n        return 1\n    else:\n        return 2')

    # if with complex conditions
    patterns.append('if x > 0 and y > 0:\n    z = 1')
    patterns.append('if x > 0 or y > 0:\n    z = 1')
    patterns.append('if not x:\n    y = 1')

    # Randomized
    for _ in range(count - len(patterns)):
        cond = _simple_expr(rng)
        body = _stmt_seq(rng)
        has_else = rng.choice([True, False])
        if has_else:
            else_body = _stmt_seq(rng)
            src = f'if {cond}:\n{_indent(body)}\nelse:\n{_indent(else_body)}'
        else:
            src = f'if {cond}:\n{_indent(body)}'
        patterns.append(src)

    return patterns


def gen_loop_patterns(rng=None, count=50):
    if rng is None:
        rng = random.Random(43)
    patterns = []

    # For loops
    for target in ['i', 'j', 'x', 'item', 'elem']:
        for iterable in ['range(10)', 'range(3)', 'items', 'data', 'seq']:
            patterns.append(f'for {target} in {iterable}:\n    pass')

    patterns.append('for i in range(10):\n    print(i)')
    patterns.append('for i in range(10):\n    x = i\n    y = i * 2')
    patterns.append('for i in range(10):\n    if i == 5:\n        break')
    patterns.append('for i in range(10):\n    if i == 5:\n        continue')
    patterns.append('for i in range(10):\n    if i == 3:\n        continue\n    if i == 7:\n        break\n    print(i)')

    # While loops
    patterns.append('while x > 0:\n    x -= 1')
    patterns.append('while True:\n    x -= 1\n    if x == 0:\n        break')
    patterns.append('while x > 0:\n    if x == 1:\n        break\n    x -= 1')
    patterns.append('while x > 0:\n    if x == 5:\n        continue\n    x -= 1')

    # For/while else
    patterns.append('for i in range(10):\n    x = i\nelse:\n    x = -1')
    patterns.append('while x > 0:\n    x -= 1\nelse:\n    x = 0')
    patterns.append('for i in range(10):\n    if i == 5:\n        break\nelse:\n    x = -1')

    # Nested loops
    patterns.append('for i in range(3):\n    for j in range(3):\n        print(i, j)')
    patterns.append('while x > 0:\n    while y > 0:\n        y -= 1\n    x -= 1')
    patterns.append('for i in range(3):\n    for j in range(3):\n        if j == 1:\n            break\n    print(i)')

    # Loop in function with return
    patterns.append('def f():\n    for i in range(10):\n        if i == 5:\n            return i\n    return -1')
    patterns.append('def f():\n    while x > 0:\n        if x == 1:\n            return x\n        x -= 1')

    # Randomized
    for _ in range(count - len(patterns)):
        kind = rng.choice(['for', 'while'])
        if kind == 'for':
            target = _pick(['i', 'j', 'x', 'item'], rng)
            iterable = _pick(['range(10)', 'range(3)', 'items', 'data'], rng)
            body = _stmt_seq(rng)
            src = f'for {target} in {iterable}:\n{_indent(body)}'
        else:
            cond = _simple_expr(rng)
            body = _stmt_seq(rng)
            src = f'while {cond}:\n{_indent(body)}'
        patterns.append(src)

    return patterns


def gen_tryexcept_patterns(rng=None, count=50):
    if rng is None:
        rng = random.Random(44)
    patterns = []

    # Basic try-except
    patterns.append('try:\n    x = 1\nexcept TypeError:\n    x = 0')
    patterns.append('try:\n    x = 1\nexcept:\n    x = 0')
    patterns.append('try:\n    x = 1\nexcept TypeError as e:\n    print(e)')

    # Multi-except
    patterns.append('try:\n    x = 1\nexcept TypeError:\n    x = 0\nexcept ValueError:\n    x = -1')

    # Try-else
    patterns.append('try:\n    x = 1\nexcept TypeError:\n    x = 0\nelse:\n    y = 2')

    # Try-finally
    patterns.append('try:\n    x = 1\nfinally:\n    x = 0')
    patterns.append('try:\n    x = 1\nexcept TypeError:\n    x = 0\nfinally:\n    y = 2')
    patterns.append('try:\n    x = 1\nexcept TypeError:\n    x = 0\nelse:\n    y = 2\nfinally:\n    z = 3')

    # Nested try
    patterns.append('try:\n    try:\n        x = 1\n    except TypeError:\n        x = 0\nexcept ValueError:\n    x = -1')

    # Try in loop
    patterns.append('for i in range(3):\n    try:\n        x = i\n    except TypeError:\n        x = 0')
    patterns.append('while x > 0:\n    try:\n        x -= 1\n    except TypeError:\n        x = 0')

    # Try with multi-statement bodies
    patterns.append('try:\n    x = 1\n    y = 2\nexcept TypeError:\n    x = 0\n    y = 0')

    # Randomized
    exc_types = ['TypeError', 'ValueError', 'KeyError', 'IndexError', 'OSError', 'RuntimeError', 'Exception']
    for _ in range(count - len(patterns)):
        has_else = rng.choice([True, False])
        has_finally = rng.choice([True, False])
        n_handlers = rng.randint(1, 3)
        try_body = _stmt_seq(rng)
        src = f'try:\n{_indent(try_body)}'
        for h in range(n_handlers):
            exc = _pick(exc_types, rng)
            has_as = rng.choice([True, False])
            handler_body = _stmt_seq(rng)
            if has_as:
                src += f'\nexcept {exc} as e:\n{_indent(handler_body)}'
            else:
                src += f'\nexcept {exc}:\n{_indent(handler_body)}'
        if has_else:
            else_body = _stmt_seq(rng)
            src += f'\nelse:\n{_indent(else_body)}'
        if has_finally:
            fin_body = _stmt_seq(rng)
            src += f'\nfinally:\n{_indent(fin_body)}'
        patterns.append(src)

    return patterns


def gen_with_patterns(rng=None, count=50):
    if rng is None:
        rng = random.Random(45)
    patterns = []

    patterns.append("with open('f') as f:\n    data = f.read()")
    patterns.append('with ctx:\n    pass')
    patterns.append("with open('a') as a, open('b') as b:\n    data = a.read() + b.read()")
    patterns.append("with open('a') as a:\n    with open('b') as b:\n        data = a.read() + b.read()")

    # With in try
    patterns.append("try:\n    with open('f') as f:\n        data = f.read()\nexcept OSError:\n    data = ''")

    # Try in with
    patterns.append("with open('f') as f:\n    try:\n        data = f.read()\n    except OSError:\n        data = ''")

    # With in loop
    patterns.append("for i in range(3):\n    with open('f') as f:\n        data = f.read()")
    patterns.append("with open('f') as f:\n    for line in f:\n        print(line)")

    # With with return
    patterns.append("def f():\n    with open('f') as fh:\n        return fh.read()")

    # With + if
    patterns.append("if flag:\n    with open('f') as f:\n        data = f.read()")

    # Randomized
    ctx_names = ['open', 'lock', 'ctx', 'resource', 'connection']
    var_names = ['f', 'fh', 'conn', 'lk', 'res', 'fp']
    for _ in range(count - len(patterns)):
        n_ctx = rng.randint(1, 2)
        body = _stmt_seq(rng)
        if n_ctx == 1:
            ctx = _pick(ctx_names, rng)
            var = _pick(var_names, rng)
            src = f'with {ctx}() as {var}:\n{_indent(body)}'
        else:
            c1 = _pick(ctx_names, rng)
            v1 = _pick(var_names, rng)
            c2 = _pick(ctx_names, rng)
            v2 = _pick(var_names, rng)
            src = f'with {c1}() as {v1}, {c2}() as {v2}:\n{_indent(body)}'
        patterns.append(src)

    return patterns


def gen_match_patterns(rng=None, count=50):
    if rng is None:
        rng = random.Random(46)
    patterns = []

    # Basic match
    patterns.append("match x:\n    case 1:\n        y = 'one'\n    case 2:\n        y = 'two'\n    case _:\n        y = 'other'")
    patterns.append("match x:\n    case [a, b]:\n        y = a + b\n    case _:\n        y = 0")
    patterns.append("match x:\n    case {'key': v}:\n        y = v\n    case _:\n        y = None")

    # Match with guard
    patterns.append("match x:\n    case n if n > 0:\n        y = n\n    case _:\n        y = 0")

    # Match in function
    patterns.append("def f(x):\n    match x:\n        case 1:\n            return 'one'\n        case _:\n            return 'other'")

    # Match in loop
    patterns.append("for item in items:\n    match item:\n        case 1:\n            print('one')\n        case _:\n            print('other')")
    patterns.append("for x in items:\n    match x:\n        case 1:\n            break\n        case 2:\n            continue\n        case _:\n            print(x)")

    # Match with multiple cases
    patterns.append("match x:\n    case 1:\n        y = 1\n    case 2:\n        y = 2\n    case 3:\n        y = 3\n    case _:\n        y = 0")

    # Match with tuple pattern
    patterns.append("match point:\n    case (0, 0):\n        y = 'origin'\n    case (x, 0):\n        y = 'x-axis'\n    case _:\n        y = 'other'")

    # Match with class pattern
    patterns.append("match obj:\n    case int():\n        y = 'int'\n    case str():\n        y = 'str'\n    case _:\n        y = 'other'")

    # Randomized
    for _ in range(count - len(patterns)):
        n_cases = rng.randint(2, 5)
        subject = _pick(EXPR_VARS, rng)
        src = f'match {subject}:\n'
        for ci in range(n_cases):
            is_default = (ci == n_cases - 1) and rng.choice([True, False])
            if is_default:
                body = _stmt_seq(rng)
                src += f'    case _:\n{_indent(body, 2)}\n'
            else:
                val = _pick(EXPR_VALS, rng)
                body = _stmt_seq(rng)
                src += f'    case {val}:\n{_indent(body, 2)}\n'
        patterns.append(src.rstrip())

    return patterns


def gen_assert_patterns(rng=None, count=50):
    if rng is None:
        rng = random.Random(47)
    patterns = []

    patterns.append('assert x > 0')
    patterns.append("assert x > 0, 'x must be positive'")
    patterns.append('assert x == y')
    patterns.append('assert x')
    patterns.append('assert not x')
    patterns.append('assert x and y')
    patterns.append('assert x or y')
    patterns.append('assert 0 < x < 100')

    # Assert in function
    patterns.append('def f(x):\n    assert x > 0\n    return x')
    patterns.append('def f(x):\n    assert isinstance(x, int)\n    return x')

    # Assert in loop
    patterns.append('for i in range(10):\n    assert i >= 0')
    patterns.append('while x > 0:\n    assert x > 0\n    x -= 1')

    # Assert in if
    patterns.append('if flag:\n    assert x > 0')

    # Randomized
    for _ in range(count - len(patterns)):
        cond = _simple_expr(rng)
        has_msg = rng.choice([True, False])
        if has_msg:
            msg = _pick(["'error'", "'invalid'", "'bad value'", "'check failed'"], rng)
            src = f'assert {cond}, {msg}'
        else:
            src = f'assert {cond}'
        patterns.append(src)

    return patterns


def gen_boolop_patterns(rng=None, count=50):
    if rng is None:
        rng = random.Random(48)
    patterns = []

    # Basic and/or
    patterns.append('if x and y:\n    z = 1')
    patterns.append('if x or y:\n    z = 1')
    patterns.append('if x and y and z:\n    w = 1')
    patterns.append('if x or y or z:\n    w = 1')
    patterns.append('if (x and y) or z:\n    w = 1')
    patterns.append('if x and (y or z):\n    w = 1')

    # BoolOp assignment
    patterns.append('z = x and y')
    patterns.append('z = x or y')
    patterns.append('z = x and y and z')
    patterns.append('z = a or b or c')
    patterns.append('z = x and (y if w else z)')

    # BoolOp in function return
    patterns.append('def f():\n    return x and y')
    patterns.append('def f():\n    return x or y')

    # BoolOp with ternary
    patterns.append('z = a and (b if c else d)')
    patterns.append('z = a or (b if c else d)')
    patterns.append('if a and (b if c else d):\n    pass')

    # Randomized
    for _ in range(count - len(patterns)):
        op = rng.choice(['and', 'or'])
        n_terms = rng.randint(2, 4)
        terms = [_simple_expr(rng) for _ in range(n_terms)]
        expr = f' {op} '.join(terms)
        is_if = rng.choice([True, False])
        if is_if:
            body = _simple_stmt(rng)
            src = f'if {expr}:\n{_indent(body)}'
        else:
            src = f'z = {expr}'
        patterns.append(src)

    return patterns


def gen_ternary_patterns(rng=None, count=50):
    if rng is None:
        rng = random.Random(49)
    patterns = []

    patterns.append('y = 10 if x > 3 else 0')
    patterns.append("z = 'yes' if flag else 'no'")
    patterns.append('y = x if x > 0 else -x')
    patterns.append('y = 1 if a and b else 0')
    patterns.append('y = 1 if a or b else 0')
    patterns.append('y = 1 if not x else 0')
    patterns.append("y = 'a' if x == 1 else 'b' if x == 2 else 'c'")

    # Ternary in function
    patterns.append('def f():\n    return 1 if x else 0')
    patterns.append('def f(x):\n    return x if x > 0 else -x')

    # Ternary in loop
    patterns.append('for i in range(10):\n    y = i if i > 5 else 0')

    # Ternary in if
    patterns.append('if (1 if x else 0):\n    y = 1')

    # Ternary + BoolOp
    patterns.append('z = a and (b if c else d)')
    patterns.append('z = a or (b if c else d)')

    # Randomized
    for _ in range(count - len(patterns)):
        true_val = _pick(EXPR_VALS + EXPR_VARS, rng)
        false_val = _pick(EXPR_VALS + EXPR_VARS, rng)
        cond = _simple_expr(rng)
        src = f'y = {true_val} if {cond} else {false_val}'
        patterns.append(src)

    return patterns


GEN_FUNCS = {
    'if': gen_if_patterns,
    'loop': gen_loop_patterns,
    'tryexcept': gen_tryexcept_patterns,
    'with': gen_with_patterns,
    'match': gen_match_patterns,
    'assert': gen_assert_patterns,
    'boolop': gen_boolop_patterns,
    'ternary': gen_ternary_patterns,
}
