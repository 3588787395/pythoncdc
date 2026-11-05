def p(next, token, signature):
    while 1:
        try:
            token = next()
        except StopIteration:
            return
        if token[0] == ']':
            break
        if token == ('', ''):
            continue
        signature.append(token[0] or '-')
    signature = ''.join(signature)
    return signature
