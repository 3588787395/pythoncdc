
def f(rows):
    out = {}
    for r in rows:
        code = r.get('code')
        kind = r.get('kind')
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
        out[code] = r
    return out
