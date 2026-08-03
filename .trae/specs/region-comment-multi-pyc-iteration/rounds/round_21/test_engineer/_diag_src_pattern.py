"""R21 diag: determine source that reproduces orig _target 592-630 pattern.
orig: item[0] computed, item[1:] computed, STORE data, STORE command"""
import dis
import sys
sys.path.insert(0, r'f:/Downloads/pythoncdc-main')


def dump(src, name):
    print(f'--- {name} ---')
    co = compile(src, f'<{name}>', 'exec')
    for c in co.co_consts:
        if hasattr(c, 'co_code') and c.co_name == '<lambda>':
            pass
    # find the function
    def walk(c):
        yield c
        for k in c.co_consts:
            if hasattr(k, 'co_code'):
                yield from walk(k)
    for c in walk(co):
        if c.co_name == 'f':
            for i in dis.get_instructions(c):
                print(f'{i.offset:5d} {i.opname:30s} {str(i.argval):25s}')
            print()


dump('''
def f(item):
    data = item[1:]
    command = item[0]
    return data, command
''', 'two-stmts')

dump('''
def f(item):
    data, command = item[1:], item[0]
    return data, command
''', 'tuple-assign')

dump('''
def f(item):
    command = item[0]
    data = item[1:]
    return data, command
''', 'reversed-stmts')

dump('''
def f(item):
    command, data = item[0], item[1:]
    return data, command
''', 'tuple-assign2')
