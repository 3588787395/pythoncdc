# -*- coding: utf-8 -*-
"""fix1 jq probe: landed product text for the two failing units + candidate
condition expression recompiled and compared against orig block 564..594."""
import dis
import io
import marshal
import sys

REPO = r'F:\Downloads\pythoncdc-main'
sys.path.insert(0, REPO)
sys.stdout.reconfigure(encoding='utf-8')

PYC = REPO + r'\site-packages\IQCommon\strategy\jq_trans_module.pyc'

import pycdc  # noqa: E402

text = pycdc.decompile_pyc(PYC)
lines = text.splitlines()
print('=== landed product lines mentioning stock_tmp ===')
for i, l in enumerate(lines, 1):
    if 'stock_tmp' in l:
        print('%4d: %s' % (i, l))

code = marshal.loads(io.open(PYC, 'rb').read()[16:])


def walk(c):
    yield c
    for k in c.co_consts:
        if hasattr(k, 'co_code'):
            for x in walk(k):
                yield x


u = [c for c in walk(code) if c.co_name == 'replace_args'
     and 'func_attribute_history_convert_code' in c.co_qualname][0]


def sig(co, lo=None, hi=None):
    out = []
    for i in dis.get_instructions(co):
        if lo is not None and not (lo <= i.offset <= hi):
            continue
        if i.opname in ('RESUME', 'CACHE', 'NOP', 'PRECALL', 'CALL', 'PUSH_NULL'):
            continue
        if i.opname in ('POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_FORWARD_IF_TRUE',
                        'POP_JUMP_BACKWARD_IF_FALSE', 'POP_JUMP_BACKWARD_IF_TRUE',
                        'JUMP_FORWARD', 'JUMP_BACKWARD'):
            a = 'J->%s' % i.argval
        elif i.opname in ('LOAD_CONST', 'LOAD_GLOBAL', 'LOAD_ATTR', 'LOAD_METHOD'):
            a = repr(i.argval)
        else:
            a = i.argrepr or ''
        out.append('%s %s' % (i.opname, a))
    return out


orig_cond = sig(u, 564, 594)
print('\norig condition block (564..594):')
for s in orig_cond:
    print('   ' + s)

exprs = [
    ("A and B or C and D", "'(' in stock_tmp and ')' in stock_tmp or '[' in stock_tmp and ']' in stock_tmp"),
    ("A and B or (C and D)", "'(' in stock_tmp and ')' in stock_tmp or ('[' in stock_tmp and ']' in stock_tmp)"),
    ("prod-as-is", "')' not in stock_tmp or '[' in stock_tmp and ']' not in stock_tmp"),
    ("B or C and D", "')' in stock_tmp or '[' in stock_tmp and ']' in stock_tmp"),
    ("noA", "')' in stock_tmp or '[' in stock_tmp and ']' in stock_tmp"),
]


def first_diff(a, b):
    n = min(len(a), len(b))
    for i in range(n):
        if a[i] != b[i]:
            return i, a[i], b[i]
    if len(a) != len(b):
        return n, a[n:] and a[n] or '<eof>', b[n:] and b[n] or '<eof>'
    return None


for name, e in exprs:
    co = compile('if %s:\n    pass\n' % e, '<c>', 'exec')
    body = co.co_consts[0]
    s = sig(body)
    # drop leading block-ish noise: keep from first LOAD/COMPARE
    fd = first_diff(orig_cond, s)
    print('\n-- %-20s len=%d  first_diff=%s' % (name, len(s), fd))
    if fd:
        print('   orig: %s' % orig_cond[fd[0]])
        print('   cand: %s' % s[fd[0]])
