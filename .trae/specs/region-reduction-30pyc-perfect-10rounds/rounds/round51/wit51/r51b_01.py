
def f(exchange_type, code):
    if exchange_type:
        if exchange_type == '1':
            code += '.SS'
        elif exchange_type == '2':
            code += '.SZ'
    else:
        if code[0] == '6':
            code += '.SS'
        elif code[0] == '3':
            code += '.SZ'
        else:
            pass
    code += '!'
    return code
