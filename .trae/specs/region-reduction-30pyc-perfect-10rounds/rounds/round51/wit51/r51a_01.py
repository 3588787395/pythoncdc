
def f(kind, code):
    if kind:
        if kind == '1':
            code += '.SS'
        elif kind == '2':
            code += '.SZ'
    else:
        if code[0] == '6':
            code += '.SS'
        elif code[0] == '3':
            code += '.SZ'
        else:
            pass
    return code
