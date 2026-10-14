def f(fq, div, fields):
    if fq is None or not div or isinstance(fields, str) and 'x' in fields:
        need = 0
    else:
        need = 1
    return need
