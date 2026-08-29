import dis, types

def f():
    a = (lambda ws: system_log.info('#### close ####'))
    b = (lambda ws: system_log.info('#### open ####'))
    return a, b

src = (
    "def f():\n"
    "    a = (lambda ws: system_log.info('#### close ####'))\n"
    "    b = (lambda ws: system_log.info('#### open ####'))\n"
    "    return a, b\n"
)
co = compile(src, '<t>', 'exec')
for c in co.co_consts:
    if isinstance(c, types.CodeType):
        for cc in c.co_consts:
            if isinstance(cc, types.CodeType):
                print('  LAMBDA name=%s consts=%s' % (cc.co_name, cc.co_consts))
                for i in dis.get_instructions(cc):
                    if i.opname == 'LOAD_CONST':
                        print('    LOAD_CONST', repr(i.argval))
