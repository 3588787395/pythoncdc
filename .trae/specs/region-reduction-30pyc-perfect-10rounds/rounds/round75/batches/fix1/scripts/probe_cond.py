# -*- coding: utf-8 -*-
"""fix1 jq: compile candidate conditions, print bytecode, diff vs orig 564..594."""
import dis
import io
import marshal
import sys

sys.stdout.reconfigure(encoding='utf-8')
REPO = r'F:\Downloads\pythoncdc-main'


def sig(co):
    out = []
    for i in dis.get_instructions(co):
        if i.opname in ('RESUME', 'CACHE', 'NOP', 'PRECALL', 'CALL', 'PUSH_NULL'):
            continue
        if i.opname.startswith(('POP_JUMP', 'JUMP')) and i.arg is not None:
            a = 'J->%s' % i.argval
        elif i.opname in ('LOAD_CONST', 'LOAD_GLOBAL', 'LOAD_ATTR', 'LOAD_METHOD'):
            a = repr(i.argval)
        else:
            a = i.argrepr or ''
        out.append('%s %s' % (i.opname, a))
    return out


def body_of(e):
    return compile('if ' + e + ':\n    pass\n', '<c>', 'exec')


code = marshal.loads(io.open(REPO + r'\site-packages\IQCommon\strategy\jq_trans_module.pyc', 'rb').read()[16:])


def walk(c):
    yield c
    for k in c.co_consts:
        if hasattr(k, 'co_code'):
            for x in walk(k):
                yield x


u = [c for c in walk(code) if c.co_name == 'replace_args'
     and 'func_attribute_history_convert_code' in c.co_qualname][0]

orig = []
for i in dis.get_instructions(u):
    if 564 <= i.offset <= 594:
        if i.opname.startswith(('POP_JUMP', 'JUMP')) and i.arg is not None:
            a = 'J->%s' % i.argval
        elif i.opname == 'LOAD_CONST':
            a = repr(i.argval)
        else:
            a = i.argrepr or ''
        orig.append('%s %s' % (i.opname, a))
print('ORIG 564..594:')
for x in orig:
    print('   ' + x)

cands = {
    'A and B or C and D': "'(' in stock_tmp and ')' in stock_tmp or '[' in stock_tmp and ']' in stock_tmp",
    'A and B or (C and D)': "'(' in stock_tmp and ')' in stock_tmp or ('[' in stock_tmp and ']' in stock_tmp)",
    'prod-as-is': "')' not in stock_tmp or '[' in stock_tmp and ']' not in stock_tmp",
    'B or C and D': "')' in stock_tmp or '[' in stock_tmp and ']' in stock_tmp",
}
for n, e in cands.items():
    s = sig(body_of(e))
    print('\n== %-22s len=%d' % (n, len(s)))
    for x in s:
        print('   ' + x)
    m = min(len(s), len(orig))
    d = None
    for i in range(m):
        if s[i] != orig[i]:
            d = i
            break
    print('   first_diff idx=%s' % d)
    if d is not None:
        print('     orig: %s' % orig[d])
        print('     cand: %s' % s[d])
