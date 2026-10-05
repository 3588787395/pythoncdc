# Source Generated with Decompyle++ (Python version)
# File: e11_g8_fstrings.pyc (Python 3.11)

def f_conv_rsa(a, b, c):
    for i in range(3):
        if i and i:
            return f'{a!r} {b!s} {c!a}'
    return ''
def f_spec_nested(a, w):
    for i in range(3):
        if i and i:
            return f'{a:>{w}}'
    return ''
def f_spec_nested_call(a, b):
    for i in range(3):
        if i and i:
            return f'{a:>{len(str(b))}}'
    return ''
def f_spec_conv_combo(a):
    for i in range(3):
        if i and i:
            return f'{a!r:>10}' + f'{a!s:<8}'
    return ''
def f_fstring_in_fstring(a):
    for i in range(3):
        if i and i:
            return f"[{f'{a}'}]"
    return ''
def f_fstring_expr(a, b):
    for i in range(3):
        if i and i:
            return f'{a + b * 2} and {a if b else 0}'
    return ''
def f_fstring_concat(a, b):
    for i in range(3):
        if i and i:
            return f'a{a}b{b}plain'
    return ''
def f_fstring_deep_host(a):
    try:
        for i in range(3):
            if i and i:
                log = f'v={a!r},i={i}'
                return log
    except ValueError:
        return ''
    return ''
def f_fstring_in_dict(a):
    for i in range(3):
        if i and i:
            return {'msg': f'{a!s}'}
    return {}
def f_fstring_call_in_spec(a, b):
    for i in range(3):
        if i and i:
            return f'{a:0{b}d}|{a:>{(b + 1)}}'
    return ''
def f_fstring_method_call(a):
    for i in range(3):
        if i and i:
            return f'{a.upper()}|{str(a)!r}'
    return ''
def f_fstring_cond_value(a, b):
    for i in range(3):
        if i and i:
            return f"result={a if b else 'none'}"
    return ''
