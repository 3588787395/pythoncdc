def f(p, obj):
    with open(p, 'r', encoding='utf-8') as fh:
        content = fh.read()
    if obj.flag is not None:
        x = content + '_' + obj.flag
    return x
