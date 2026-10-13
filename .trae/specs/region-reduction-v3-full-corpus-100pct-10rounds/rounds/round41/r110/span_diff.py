"""span_diff.py — align original vs product opcode sequences and print the dropped spans.

usage: python -X utf8 span_diff.py <product.py>
Prints SequenceMatcher tags over the opcode-name sequences of clock_worker, mapping each
non-equal original span to its bytecode offsets and original source lines.
"""
import dis
import marshal
import sys
import types
from difflib import SequenceMatcher

PYC = 'D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main/site-packages/IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc'


def find(c, name):
    for k in c.co_consts:
        if isinstance(k, types.CodeType):
            if k.co_name == name:
                return k
            r = find(k, name)
            if r is not None:
                return r
    return None


def main():
    prod = sys.argv[1]
    src = open(prod, encoding='utf-8-sig').read()
    pc = find(compile(src, prod, 'exec'), 'clock_worker')
    o = find(marshal.loads(open(PYC, 'rb').read()[16:]), 'clock_worker')
    oi = [i for i in dis.get_instructions(o)]
    pi = [i for i in dis.get_instructions(pc)]
    os_ = [i.opname for i in oi]
    ps_ = [i.opname for i in pi]
    print('[span-diff] %s orig=%d prod=%d delta=%+d' % (prod, len(os_), len(ps_), len(ps_) - len(os_)))
    sm = SequenceMatcher(None, os_, ps_, autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            continue
        lines = sorted({x.starts_line for x in oi[i1:i2] if x.starts_line})
        ops = sorted({x.opname for x in oi[i1:i2]})
        print('  %-8s orig[%d:%d]=%d prod[%d:%d]=%d offs=%s..%s src_lines=%s ops=%s' % (
            tag, i1, i2, i2 - i1, j1, j2, j2 - j1,
            oi[i1].offset if i1 < len(oi) else '-', oi[min(i2, len(oi)) - 1].offset if i2 else '-',
            lines[:14], ops[:8]))
    return 0


sys.exit(main())
