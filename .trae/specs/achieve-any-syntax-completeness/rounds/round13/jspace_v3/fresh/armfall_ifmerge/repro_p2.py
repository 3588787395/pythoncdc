def p2(next, token, signature, predicate):
    while 1:
        try:
            token = next()
        except StopIteration:
            return
        if token[0] == ']':
            break
        if token == ('', ''):
            continue
        if token[0] and token[0][:1] in '\'':
            token = ("'", token[0][1:-1])
        signature.append(token[0] or '-')
        predicate.append(token[1])
    return ''.join(signature)
