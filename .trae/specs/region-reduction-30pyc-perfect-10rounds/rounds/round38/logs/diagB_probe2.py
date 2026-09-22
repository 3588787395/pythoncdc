# -*- coding: utf-8 -*-
"""r38diagB probe 2: enumerate the LANDED core's basic blocks for the two corpus rows and for
synthetic controls, printing EVERY instruction of each block, so a block that carries two
terminators (原则-1 violation) is visible.

usage:  D:/Python/python.exe -X utf8 D:/Temp/r38diagB/probe2.py
"""
import io
import os
import sys

REPO = r'F:\Downloads\pythoncdc-main'
ROOT = r'D:/Temp/r38diagB'
sys.path.insert(0, REPO)

import pycdc  # noqa: E402
from core.cfg import region_ast_generator as rag  # noqa: E402

OUT = []
TARGETS = set(['wizard_quant_check_limit', 'get_all_real_daily_kline',
               'ctl_plain_elif', 'ctl_two_cont', 'ctl_single_cont', 'ctl_elif_more_body'])
seen = set()


def _is_term(op):
    return (op.startswith('POP_JUMP') or op.startswith('JUMP') or op.startswith('RETURN')
            or op.startswith('RAISE') or op in ('BREAK', 'CONTINUE', 'RERAISE'))


def scan(self, where):
    try:
        nm = self.cfg.code.co_name
        blocks = list(self.cfg.blocks.values())
    except Exception:
        return
    if nm not in TARGETS:
        return
    bad = []
    for b in blocks:
        inner = [i.offset for i, o in zip(b.instructions, [x.opname for x in b.instructions][:-1])
                 if _is_term(o)]
        if inner:
            bad.append((b.start_offset, b.end_offset, len(b.instructions), inner,
                        ' '.join('%s@%d' % (i.opname, i.offset) for i in b.instructions),
                        sorted(x.start_offset for x in b.conditional_successors)))
    if not bad:
        return
    OUT.append('  !! %s [%s] %d block(s) with INTERNAL terminator (原则1 violation):' % (
        nm, where, len(bad)))
    for s, e, n, inner, o, su in sorted(bad):
        OUT.append('     @%d..%d n=%d inner-terminator-offsets=%s succs=%s' % (s, e, n, inner, su))
        OUT.append('        %s' % o)


def full_dump(gen, nm, lo, hi):
    OUT.append('---- ALL blocks of %s in [@%d..@%d] ----' % (nm, lo, hi))
    own = getattr(gen.region_analyzer, 'block_to_region', {})
    for b in sorted(gen.cfg.blocks.values(), key=lambda x: x.start_offset):
        if not (lo <= b.start_offset <= hi):
            continue
        r = own.get(b)
        OUT.append('  @%-4d..%-4d succs=%-16s owner=%-22s %s' % (
            b.start_offset, b.end_offset,
            str(sorted(x.start_offset for x in b.conditional_successors)),
            (type(r).__name__ + '@' + str(r.entry.start_offset)) if r is not None else '-',
            ' '.join('%s@%d' % (i.opname, i.offset) for i in b.instructions)))
    OUT.append('  whole-function block starts: %s' % sorted(
        b.start_offset for b in gen.cfg.blocks.values()))


def window_for(name, region):
    return {'wizard_quant_check_limit': (270, 360),
            'get_all_real_daily_kline': (820, 910)}.get(name)


INSTALLED = []


def install():
    G = rag.RegionASTGenerator
    for name in ('_generate_region', '_process_if_blocks', '_if_generate_normal',
                 '_if_generate_then_branch', '_if_generate_else_branch',
                 '_if_generate_full_elif_chain', '_if_generate_elif_chain', '_generate_loop'):
        orig = getattr(G, name)

        def w(self, *a, orig=orig, name=name, **k):
            scan(self, name)
            try:
                nm = self.cfg.code.co_name
                wd = window_for(nm, a[0] if a else None)
                if wd and (nm, 'fd') not in seen:
                    seen.add((nm, 'fd'))
                    full_dump(self, nm, wd[0], wd[1])
            except Exception as e:
                OUT.append('  PROBE-FAIL %r' % (e,))
            return orig(self, *a, **k)
        setattr(G, name, w)
        INSTALLED.append(name)


install()
OUT.append('probe installed on %d methods: %s' % (len(INSTALLED), INSTALLED))

for p in ['IQCommon/strategy/wizard_quant_api.pyc', 'IQCommon/api/klinedata.pyc']:
    OUT.append('######## %s' % p)
    pycdc.decompile_pyc(os.path.join(REPO, 'site-packages', p.replace('/', os.sep)))

CTL = (
    'def ctl_plain_elif(x):\n'
    '    for i in x:\n'
    '        if i > 3:\n'
    '            a = 1\n'
    '        elif i < 0:\n'
    '            a = 2\n'
    '        print(a)\n'
    '    return 0\n'
    'def ctl_single_cont(d, ks):\n'
    '    for k in ks:\n'
    '        if k > 3:\n'
    '            d[k] = 1\n'
    '            continue\n'
    '    return d\n'
    'def ctl_two_cont(d, ks):\n'
    '    for k in ks:\n'
    '        try:\n'
    '            if k > 3:\n'
    '                d[k] = 1\n'
    '                continue\n'
    '            if k < 0:\n'
    '                d[k] = -1\n'
    '                continue\n'
    '        except Exception:\n'
    '            pass\n'
    '    return d\n'
    'def ctl_elif_more_body(d, ks):\n'
    '    for k in ks:\n'
    '        if k > 3:\n'
    '            d[k] = 1\n'
    '        elif k < 0:\n'
    '            d[k] = -1\n'
    '        d[k + 1] = 2\n'
    '    return d\n'
)
io.open(os.path.join(ROOT, 'ctl_src.py'), 'w', encoding='utf-8').write(CTL)
import py_compile  # noqa: E402
pyc = os.path.join(ROOT, 'ctl_src.pyc')
py_compile.compile(os.path.join(ROOT, 'ctl_src.py'), cfile=pyc, doraise=True)
OUT.append('######## synthetic controls (probe must walk these too)')
ctl_out = pycdc.decompile_pyc(pyc)
io.open(os.path.join(ROOT, 'ctl_src_landed.py'), 'w', encoding='utf-8').write(ctl_out)
OUT.append(ctl_out)
OUT.append('controls scanned; blocks-with-internal-terminator report lines = %d'
           % sum(1 for l in OUT if l.startswith('  !! ')))

io.open(os.path.join(ROOT, 'probe2.log.txt'), 'w', encoding='utf-8').write('\n'.join(OUT) + '\n')
sys.stdout.write('\n'.join(OUT) + '\n')
print('TOTAL %d lines' % len(OUT))
