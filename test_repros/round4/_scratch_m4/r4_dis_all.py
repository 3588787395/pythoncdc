import sys, marshal, dis
path = sys.argv[1]
f = open(path, 'rb')
f.read(16)
code = marshal.load(f)

def walk(co, prefix=''):
    print('=' * 20, prefix + co.co_name, '=' * 20)
    dis.dis(co)
    for c in co.co_consts:
        if hasattr(c, 'co_name'):
            walk(c, prefix + co.co_name + '.')

walk(code)