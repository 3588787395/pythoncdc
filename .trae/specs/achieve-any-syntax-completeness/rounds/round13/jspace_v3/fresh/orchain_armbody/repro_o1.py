def f(sig, pred):
    if sig == 'a' or sig == 'b' or ((sig == 'c' or sig == 'd') and not pred.isdigit()):
        tag = pred[0]
        return tag
    if sig == 'e':
        return 'E'
    else:
        raise ValueError('bad')
