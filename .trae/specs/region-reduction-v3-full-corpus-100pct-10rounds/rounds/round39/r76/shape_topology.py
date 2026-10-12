"""Jump-topology comparison in INSTRUCTION-INDEX space (immune to the sandbox's
LOAD_GLOBAL/LOAD_DEREF width differences): does the hypothesised shape reproduce the
original unit's jump structure at the @7164 site?

usage: python -X utf8 work/shape_topology.py
"""
import dis
import marshal

import importlib.util

spec = importlib.util.spec_from_file_location('ss', 'D:/Temp/r76/work/shape_site1.py')
PYC = (r"D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main/site-packages/"
       r"IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc")
DROP = ('NOP', 'CACHE', 'EXTENDED_ARG')
src = open('D:/Temp/r76/work/shape_site1.py', encoding='utf-8').read()
ns = {}
exec(src.split('SHAPE = ')[0], ns)
S = {'S1': ns['S1'], 'S2': ns['S2'], 'S3': ns['S3']}


def rows(co):
    out = []
    for i in dis.get_instructions(co):
        if i.opname in DROP:
            continue
        out.append((i.offset, i.opname, i.argrepr or ''))
    return out


def jumps(lst):
    off2idx = {r[0]: k for k, r in enumerate(lst)}
    out = []
    for k, (off, nm, ar) in enumerate(lst):
        if nm.startswith('POP_JUMP') or nm in ('JUMP_FORWARD', 'JUMP_BACKWARD'):
            t = int(ar.split()[-1]) if ar and ar.split()[-1].isdigit() else None
            out.append((k, nm, off2idx.get(t) - k if t in off2idx else None))
    return out


orig = marshal.loads(open(PYC, 'rb').read()[16:])
CO = type(orig)
acc = []


def gather(c):
    acc.append(c)
    for k in c.co_consts:
        if isinstance(k, CO):
            gather(k)


gather(orig)
o = max([c for c in acc if c.co_name == 'clock_worker'], key=lambda c: len(c.co_code))
oi = [r for r in rows(o) if 7164 <= r[0] < 7582]
ji = jumps(oi)
print('orig window instructions=%d conditional/uncond jumps=%d' % (len(oi), len(ji)))
print('orig topology:', [(nm, rel) for _, nm, rel in ji])
for k in ('S1', 'S2', 'S3'):
    comp = compile(S[k], '<p>', 'exec')
    pco = [x for x in comp.co_consts if isinstance(x, CO) and x.co_name == 'f'][0]
    pr = rows(pco)
    st = next(i for i, r in enumerate(pr) if r[1] == 'LOAD_FAST' and r[2] == 'now_date')
    pr = pr[st:]
    e = next(i for i, r in enumerate(pr) if r[2] == 'z')
    pr = pr[:e]
    jj = jumps(pr)
    same = [(a[1], a[2]) for a in ji] == [(b[1], b[2]) for b in jj]
    print('%s: instructions=%d jumps=%d topology_equal_to_orig=%s' % (k, len(pr), len(jj), same))
    if not same:
        for a, b in zip(ji, jj):
            if (a[1], a[2]) != (b[1], b[2]):
                print('    %-28s orig_rel=%s prod_rel=%s' % (a[1], a[2], b[2]))
